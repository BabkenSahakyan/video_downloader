import urllib.parse
import re
import requests

import util


def construct_download_url(url_template: str, index: str, downloader_host: str):
    normal_url = url_template.format(index=index)
    ascii_url = urllib.parse.quote_plus(normal_url)

    return downloader_host + "/ajax/getLinks.php?video=" + ascii_url + "&rand=" + get_decoded(normal_url)


def extract_urls(downloader_api_url, title):
    response = get_urls(downloader_api_url)
    response_json = response.json()

    result = []
    for idx, next_entity in enumerate(response_json["data"]["av"]):
        download_url = next_entity["url"].replace("[[_index_]]", str(idx))
        ext = next_entity["ext"]
        quality = next_entity["quality"]
        fps = str(next_entity.get("fps", "_"))

        result.append({
            "quality": quality,
            "ext": ext,
            "fps": fps,
            "title": title + "." + ext,
            "download_url": download_url
        })

    return result


def get_urls(url):
    return requests.get(url, headers={"Content-type": "application/x-www-form-urlencoded",
                                      "User-Agent": "Mozilla/5.0 Firefox/131.0",
                                      "Accept-Encoding": "gzip, deflate, br, zstd"})


def get_decoded(url):
    return normalize(decode(url))


def decode(url, operation="dec", max_chars=3):
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
    url += ''

    for _ in range(max_chars):
        enc_str = ''
        for char in url:
            pos = chars.find(char)
            if pos == -1:
                enc_str += char
            else:
                if operation == "enc":
                    enc_pos = pos + 5 if pos + 5 < len(chars) else (pos + 5) - len(chars)
                else:
                    enc_pos = pos - 5 if pos - 5 >= 0 else len(chars) + (pos - 5)

                enc_char = chars[enc_pos]
                enc_str += enc_char

        url = enc_str[::-1]

    return enc_str[::-1]


def normalize(value):
    return re.sub('[^0-9a-zA-Z]', '', value)[0: 15]


def write_to_file(file, result_list, preferred_quality, preferred_ext, honour_preferences):
    for result in result_list:
        if (not honour_preferences) or (preferred_quality == result['quality'] and preferred_ext == result['ext']):
            file.write(result['quality'] + "|" +
                       result['ext'] + "|" +
                       result['fps'] + "|" +
                       result['title'] + "|" +
                       result['download_url'] +
                       "\n")

    file.flush()


if __name__ == '__main__':
    conf = util.read_conf()

    titles = conf["titles"]
    url_template = conf["url_template"]
    downloader_host = conf["downloader_host"]
    file_name = conf["name"]
    preferred_quality = conf["preferred_quality"]
    preferred_ext = conf["preferred_ext"]
    honour_preferences = conf.get("honour_preferences", True)

    file = open(file_name + ".csv", "a")
    for video_id, title in titles.items():
        print(video_id + ": " + title)

        download_url = construct_download_url(url_template, video_id, downloader_host)
        try:
            result_list = extract_urls(download_url, title)
            write_to_file(file, result_list, preferred_quality, preferred_ext, honour_preferences)
        except Exception as ex:
            print("skipping: " + video_id + ": " + title + "because: " + str(ex))

    file.close()
