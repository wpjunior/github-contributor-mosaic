import argparse
import math
import json
from io import BytesIO

import pycurl
from PIL import Image
from octopus import TornadoOctopus


def get_avatars(urls):
    avatars = []

    otto = TornadoOctopus(
        concurrency=50, auto_start=True, cache=True, expiration_in_seconds=60
    )

    def handle_url_response(url, response):
        if 'Not found' == response.text:
            print 'URL Not Found: %s' % url
        else:
            avatars.append(response.text)

    for url in urls:
        otto.enqueue(url, handle_url_response)

    otto.wait()

    return avatars


def find_avatars(github_project):
    c = pycurl.Curl()
    data = BytesIO()

    url = 'https://api.github.com/repos/%s/stats/contributors' % github_project
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, data.write)
    c.perform()

    json_data = json.loads(data.getvalue())

    return map(lambda x: x['author']['avatar_url'], json_data)


class GitHubMozaic(object):
    MIN_X = 230

    def __init__(self, github_project):
        self.avatars = find_avatars(github_project)
        self.x = int(math.ceil(math.sqrt(len(self.avatars))))
        self.y = int(math.ceil(len(self.avatars) / float(self.x)))

    def write(self, writer):
        main_image = Image.new("RGB", (
            self.MIN_X * self.x,
            self.MIN_X * self.y), "white")

        avatars = get_avatars(self.avatars)

        for pos, avatar in enumerate(avatars):
            io = BytesIO(avatar)
            img = Image.open(io)

            line = pos // self.x
            column = pos % self.x

            if img.size[0] > self.MIN_X or img.size[1] > self.MIN_X:
                img.thumbnail((self.MIN_X, self.MIN_X), Image.ANTIALIAS)
            else:
                img = img.resize((self.MIN_X, self.MIN_X))

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
