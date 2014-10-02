import argparse
import math
import json
from io import BytesIO

import pycurl
from PIL import Image
from StringIO import StringIO
from octopus import TornadoOctopus


def get_avatars(urls):
    avatars = []

    otto = TornadoOctopus(
        concurrency=50, auto_start=True, cache=True, expiration_in_seconds=60
    )

    def handle_url_response(url, response):
        if 'Not found' == response.text:
            print url
        else:
            avatars.append(response.text)

    for url in urls:
        otto.enqueue(url, handle_url_response)

    otto.wait()

    return avatars


def find_avatars(github_project):
    c = pycurl.Curl()
    data = BytesIO()

    url = 'https://github.com/%s/graphs/contributors-data' % github_project

    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, data.write)
    c.perform()

    json_data = json.loads(data.getvalue())

    return map(lambda x: x['author']['avatar'], json_data)


class GitHubMozaic(object):
    MIN_X = 60

    def __init__(self, github_project):
        self.avatars = find_avatars(github_project)
        self.x = int(math.ceil(math.sqrt(len(self.avatars))))

    def write(self, writer):
        main_image = Image.new("RGB", (
            self.MIN_X * self.x,
            self.MIN_X * self.x), "white")

        avatars = get_avatars(self.avatars)

        for pos, avatar in enumerate(avatars):
            io = StringIO(avatar)
            img = Image.open(io)

            column = pos // self.x
            line = pos % self.x
            img.thumbnail((self.MIN_X, self.MIN_X), Image.ANTIALIAS)
            main_image.paste(img, (self.MIN_X * column, self.MIN_X * line))

        main_image.save(writer, 'JPEG')

    def save(self, path):
        with open(path, 'wb') as output:
            self.write(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", dest="output", help="write mozaic to FILE",
        metavar="OUTPUT", required=True)
    parser.add_argument(
        "--repository", dest="repository", help="write mozaic to FILE",
        metavar="REPOSITORY",
        required=True)
    args = parser.parse_args()

    mozaic = GitHubMozaic(args.repository)
    mozaic.save(args.output)
