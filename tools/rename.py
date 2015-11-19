from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from collections import OrderedDict
import argparse
import re


__version__ = '0.1'


uniname_RE = re.compile(r"""((uni)|(u))              # match "uni" or "u"
                            ((?(2)([0-9A-F]{4}))     # if "uni" match 4 digits
                             (?(3)([0-9A-F]{4,6})))  # if "u" match 4-6 digits
                            (?!.)""", re.X)          # don't match anythg else


def codepoint_from_uniname(name):
    m = re.match(uniname_RE, name)
    if m:
        codepoint_hex = m.group(4)
        return int(codepoint_hex, 16)
    else:
        raise ValueError("invalid uniname: '%s'" % name)


def parse_options(args):
    parser = argparse.ArgumentParser(
        description="Use GlyphOrderAndAliasDB to rename glyphs in TTF/OTF")
    parser.add_argument('goadb', metavar='GOADB.txt',
                        type=argparse.FileType('r'), help='input GOADB file.')
    parser.add_argument('infile', metavar='INPUT',
                        help='input font file.')
    parser.add_argument('outfile', metavar='OUTPUT', nargs='?',
                        help='output font file (default: overwrite input '
                        'file).')
    parser.add_argument('--version', action='version', version=__version__)
    options = parser.parse_args(args)
    if not options.outfile:
        # careful: this is going to overwrite the input file!
        options.outfile = options.infile
    return options


def parse_goadb(goadbfile):
    try:
        goadb = goadbfile.read()
    except AttributeError:
        with open(goadbfile, 'r') as f:
            goadb = f.read()
    finalnames = {}
    mapping = {}
    for i, line in enumerate(goadb.splitlines()):
        line = re.sub(r"#.*", "", line).strip()
        if not line:
            continue
        names = line.split()
        n = len(names)
        assert len(names) in (2, 3)
        if n == 2:
            final, friendly = names
        elif n == 3:
            final, friendly, uniname = names
            code = codepoint_from_uniname(uniname)
            if code not in mapping:
                mapping[code] = final
            else:
                raise AssertionError('uniname redefined: %s' % uniname)
        else:
            raise AssertionError(
                "GOADB must have either 2 or 3 items per entry: "
                "line %d: %s" % line)
        finalnames[friendly] = final
    return finalnames, mapping


class GoadbManager(object):

    def __init__(self, goadbpath, fontpath):
        self.parse_goadb(goadbpath)
        self.font = ttLib.TTFont(fontpath, recalcBBoxes=False,
                                 recalcTimestamp=False)

    def parse_goadb(self, goadbfile):
        try:
            goadb = goadbfile.read()
        except AttributeError:
            with open(goadbfile, 'r') as f:
                goadb = f.read()
        self.names = names = OrderedDict()
        self.mapping = mapping = {}
        for i, line in enumerate(goadb.splitlines()):
            line = re.sub(r"#.*", "", line).strip()
            if not line:
                continue
            items = line.split()
            n = len(items)
            assert len(items) in (2, 3)
            if n == 2:
                final, friendly = items
            elif n == 3:
                final, friendly, uniname = items
                code = codepoint_from_uniname(uniname)
                if code not in mapping:
                    mapping[code] = final
                else:
                    raise AssertionError('uniname redefined: %s' % uniname)
            else:
                raise AssertionError(
                    "GOADB must have either 2 or 3 items per entry: "
                    "line %d: %s" % line)
            names[friendly] = final
        self.inv_mapping = {v: k for k, v in mapping.items()}

    def rename_glyphs(self):
        # Do the renaming in newnames
        newnames = []
        for gname in self.font.getGlyphOrder():
            if gname in self.names:
                newnames.append(self.names[gname])
            else:
                newnames.append(gname)
        # must reload TTFont again
        font = ttLib.TTFont(self.font.reader.file.name)
        # set glyph order as newnames then load post table
        font.setGlyphOrder(newnames)
        font['post']
        self.font = font

    def save(self, outpath):
        self.font.save(outpath, reorderTables=False)

    def close(self):
        self.font.close()


def main(args=None):
    options = parse_options(args)
    manager = GoadbManager(options.goadb, options.infile)
    manager.rename_glyphs()
    manager.save(options.outfile)
    manager.close()


if __name__ == '__main__':
    main()
