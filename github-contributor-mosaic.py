import argparse
import math
import requests
import sys

from PIL import Image
from StringIO import StringIO


def find_avatars(github_project):
    req = requests.get(
        'https://github.com/%s/graphs/contributors-data' % github_project)

    return map(lambda x: x['author']['avatar'], req.json())


def print_in_line(text):
    sys.stdout.write(text)
    sys.stdout.write('\r')
    sys.stdout.flush()


class GitHubMozaic(object):
    MIN_X = 60

    def __init__(self, github_project):
        self.avatars = find_avatars(github_project)
        self.x = int(math.ceil(math.sqrt(len(self.avatars))))

    def write(self, writer):
        main_image = Image.new("RGB", (
            self.MIN_X * self.x,
            self.MIN_X * self.x), "white")

        for pos, avatar in enumerate(self.avatars):
            req = requests.get(avatar)
            io = StringIO(req.content)
            img = Image.open(io)

            column = pos // self.x
            line = pos % self.x
            img.thumbnail((self.MIN_X, self.MIN_X), Image.ANTIALIAS)
            main_image.paste(img, (self.MIN_X * column, self.MIN_X * line))

            print_in_line('%d / %d Downloading' % (pos + 1, len(self.avatars)))

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
