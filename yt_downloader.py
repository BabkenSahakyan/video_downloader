import os
import subprocess

import util

DEFAULT_MAX_HEIGHT = 1080


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
        if entry.startswith(prefix) and not entry.endswith(".part"):
            return True

    return False


def download(url, referer, max_height, directory, title):
    if is_downloaded(directory, title):
        print("skipping (already downloaded): " + title)
        return

    output_template = os.path.join(directory, title + ".%(ext)s")
    command = build_command(url, referer, max_height, output_template)

    print(" ".join(command))
    result = subprocess.run(command)
    if result.returncode != 0:
        print("failed (exit %d): %s" % (result.returncode, title))


if __name__ == '__main__':
    conf = util.read_conf()

    titles = conf["titles"]
    url_template = conf["url_template"]
    referer = conf["referer"]
    name = conf["name"]
    max_height = conf.get("max_height", DEFAULT_MAX_HEIGHT)

    os.makedirs(name, exist_ok=True)

    for video_id, title in titles.items():
        print(video_id + ": " + title)

        url = url_template.format(index=video_id)
        try:
            download(url, referer, max_height, name, title)
        except Exception as ex:
            print("skipping: " + video_id + ": " + title + " because: " + str(ex))
