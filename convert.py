from __future__ import print_function, division, absolute_import
from cu2qu import fonts_to_quadratic
from robofab.world import OpenFont
import sys
import os
import shutil


MAX_ERROR = 1.5


def rmtree(path):
    for root, directories, files in os.walk(path):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in directories:
            shutil.rmtree(os.path.join(root, d))


def convert_to_quadratic(source, dest, max_err=MAX_ERROR):
    font = OpenFont(source)
    report = fonts_to_quadratic(font, max_err=max_err)
    if os.path.isdir(dest):
        rmtree(dest)
    font.save(dest)
    return report


def main():
    if len(sys.argv) < 2:
        print('usage: convert.py Font.ufo [Font_quad.ufo]', file=sys.stderr)
        return 1
    source = sys.argv[1]
    if len(sys.argv) > 3:
        dest = sys.argv[2]
    else:
        source = source[:-1] if source.endswith('/') else source
        dest = os.path.splitext(source)[0] + '_quad.ufo'
    report = convert_to_quadratic(source, dest)
    print(report)


if __name__ == '__main__':
    main()
