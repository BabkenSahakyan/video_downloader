import datetime
import urllib.request
import urllib.error
import csv
import os

import util


def read_urls(name):
    result = []
    with open(name + ".csv", "r") as urls_file:
        lines = csv.reader(urls_file, delimiter='|')
        for line in lines:
            result.append(line[3::])

    return result


def download(file_name, url):
    if not os.path.isfile(file_name):
        try:
            with urllib.request.urlopen(url) as response:
                headers = response.info()
                if headers["Content-Type"] == "application/octet-stream":
                    print("%s: %s %s" % (str(datetime.datetime.now()), title, url))
                    with open(file_name, 'wb') as out_file:
                        while block := response.read(1024 * 8):
                            out_file.write(block)
                else:
                    print("Invalid response for %s: %s" % (title, response.read()))
        except urllib.error.URLError:
            print("skipping " + title)
        finally:
            if response is not None:
                print("closing response")
                response.close()


if __name__ == '__main__':
    conf = util.read_conf()

    name = conf["name"]
    os.makedirs(name, exist_ok=True)

    urls = read_urls(name)
    for idx, (title, url) in enumerate(urls):
        download(name + "/" + title, url)
