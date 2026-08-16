import os
import shutil
import signal
import subprocess
import sys

import util

DEFAULT_MAX_HEIGHT = 1080
LOCK_ROOT = ".locks"


def build_command(url, referer, max_height, output_template):
    return [
        "yt-dlp",
        "-S", "res:" + str(max_height),
        "--referer", referer,
        "--force-generic-extractor",
        url,
        "-o", output_template
    ]


def is_downloaded(directory, title):
    prefix = title + "."
    for entry in os.listdir(directory):
        if entry.startswith(prefix) and not entry.endswith((".part", ".ytdl")):
            return True

    return False


# mkdir is atomic: exactly one instance can create a given lock, so it is the
# claim. Locks are released after each attempt - finished videos are protected
# by is_downloaded, and a failed one should be retryable by the next run.
def claim(lock_root, video_id):
    lock = os.path.join(lock_root, video_id)
    try:
        os.mkdir(lock)
    except FileExistsError:
        return False

    with open(os.path.join(lock, "pid"), "w") as pid_file:
        pid_file.write(str(os.getpid()))

    return True


def release(lock_root, video_id):
    shutil.rmtree(os.path.join(lock_root, video_id), ignore_errors=True)


def download(url, referer, max_height, directory, lock_root, video_id, title):
    if is_downloaded(directory, title):
        print("skipping (already downloaded): " + title)
        return

    if not claim(lock_root, video_id):
        print("skipping (being downloaded by another run): " + title)
        return

    try:
        # another instance may have finished this one between the check and the claim
        if is_downloaded(directory, title):
            print("skipping (already downloaded): " + title)
            return

        output_template = os.path.join(directory, title + ".%(ext)s")
        command = build_command(url, referer, max_height, output_template)

        print(" ".join(command))
        result = subprocess.run(command)
        if result.returncode != 0:
            print("failed (exit %d): %s" % (result.returncode, title))
    finally:
        release(lock_root, video_id)


if __name__ == '__main__':
    conf = util.read_conf()

    titles = conf["titles"]
    url_template = conf["url_template"]
    referer = conf["referer"]
    name = conf["name"]
    max_height = conf.get("max_height", DEFAULT_MAX_HEIGHT)

    os.makedirs(name, exist_ok=True)

    lock_root = os.path.join(name, LOCK_ROOT)
    if "--clear-locks" in sys.argv:
        shutil.rmtree(lock_root, ignore_errors=True)
        print("cleared stale locks in " + lock_root)

    os.makedirs(lock_root, exist_ok=True)

    # SIGTERM would kill us without running the finally that releases the lock
    signal.signal(signal.SIGTERM, lambda number, frame: sys.exit(130))

    for video_id, title in titles.items():
        print(video_id + ": " + title)

        url = url_template.format(index=video_id)
        try:
            download(url, referer, max_height, name, lock_root, video_id, title)
        except Exception as ex:
            print("skipping: " + video_id + ": " + title + " because: " + str(ex))

    try:
        os.rmdir(lock_root)
    except OSError:
        pass
