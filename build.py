from __future__ import print_function, unicode_literals
import os
import errno
from ufo2fdk import OTFCompiler
from defcon import Font
from collections import defaultdict
import argparse


class MarkFeatureWriter(object):

    tag = "mark"

    def __init__(self, font):
        self.font = font
        self._setupAnchorGroups()

    def _setupAnchorGroups(self):
        anchorGroups = defaultdict(list)
        anchorNames = set()
        for glyph in self.font:
            for anchor in glyph.anchors:
                anchorNames.add(anchor.name)
        for anchorName in sorted(anchorNames):
            if not anchorName.startswith("_"):
                break
            baseName = anchorName[1:]
            if baseName in anchorNames:
                anchorGroupName = baseName.split(".", 1)[0]
                anchorGroups[anchorGroupName].append(baseName)
        self.anchorGroups = anchorGroups

    def _createAccentAndBaseGlyphLists(self, anchorName):
        """Return two lists of <glyphName, x, y> tuples: one for accent glyphs, and
        one for base glyphs containing an anchor with the given name.
        """
        accentAnchorName = "_" + anchorName
        accentGlyphs = []
        for glyph in self.font:
            for anchor in glyph.anchors:
                if accentAnchorName == anchor.name:
                    accentGlyphs.append((glyph.name, anchor.x, anchor.y))
                    break
        accentGlyphNames = set(glyphName for glyphName, _, _ in accentGlyphs)
        baseGlyphs = []
        for glyph in self.font:
            # XXX handle mkmk?
            if glyph.name in accentGlyphNames:
                continue
            for anchor in glyph.anchors:
                if anchorName == anchor.name:
                    baseGlyphs.append((glyph.name, anchor.x, anchor.y))
                    break
        return accentGlyphs, baseGlyphs

    def _addMarkLookup(self, lines, lookupName, anchorGroup):
        """Add a mark lookup for one group of anchors having the same name."""
        anchorGroupName = anchorGroup[0].split(".", 1)[0]

        lines.append("  lookup %s {" % lookupName)

        className = "@MC_%s_%s" % (self.tag, anchorGroupName)

        groupAccentGlyphs = []
        groupBaseGlyphs = []
        for anchorName in anchorGroup:
            accents, bases = self._createAccentAndBaseGlyphLists(anchorName)
            groupAccentGlyphs.extend(accents)
            groupBaseGlyphs.extend(bases)

        for accentName, x, y in sorted(groupAccentGlyphs):
            lines.append(
                "    markClass %s <anchor %d %d> %s;" %
                (accentName, x, y, className))

        for accentName, x, y in sorted(groupBaseGlyphs):
            lines.append(
                "    pos base %s <anchor %d %d> mark %s;" %
                (accentName, x, y, className))

        lines.append("  } %s;" % lookupName)

    def write(self):
        """Write the feature."""
        lines = ["feature %s {" % self.tag]

        for i, (name, group) in enumerate(sorted(self.anchorGroups.items())):
            lookupName = "%s%d" % (self.tag, i + 1)
            self._addMarkLookup(lines, lookupName, group)

        lines.append("} %s;" % self.tag)
        return "" if len([ln for ln in lines if ln]) == 2 else "\n".join(lines)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def make_output_name(ufopath, output_format, output_dir=None):
    if output_format not in ('ttf', 'cff'):
        raise RuntimeError('invalid format: %s' % output_format)
    dirname, basename = os.path.split(ufopath)
    ufoname = os.path.splitext(basename)[0]
    if output_dir is None:
        # use same folder as ufopath
        output_dir = dirname
    else:
        # create output_dir if it doesn't exist
        mkdir_p(output_dir)
    ext = ".otf" if output_format == 'cff' else '.ttf'
    return os.path.join(output_dir, ufoname + ext)


def build(ufopath, output_dir=None, formats=['cff'], debug=False, verbose=True):
    if ufopath.endswith(os.sep):
        # strip any trailing forward or backslash
        ufopath = ufopath[:-1]

    font = Font(ufopath)

    mark_feature = MarkFeatureWriter(font).write()
    font.features.text += "\n\n" + mark_feature

    for fmt in formats:
        outfile = make_output_name(ufopath, fmt, output_dir)

        compiler = OTFCompiler(savePartsNextToUFO=debug)
        reports = compiler.compile(font, outfile,
                                   checkOutlines=False, autohint=False,
                                   releaseMode=True,
                                   glyphOrder=font.glyphOrder)
        if verbose:
            print(reports["makeotf"])


def parse_options(args):
    parser = argparse.ArgumentParser(
        description="Compile UFOs to OpenType fonts.")
    parser.add_argument('infiles', metavar='INPUT', nargs="+",
                        help='input UFO source files.')
    parser.add_argument('-d', '--output-dir', metavar='DIR', nargs="?",
                        help="output directory. If it doesn't exist, it will "
                        "be created (default: same as input UFO).")
    parser.add_argument('--ttf', dest='formats', action='append_const',
                        const='ttf', help='save output as TTF/OTF.')
    parser.add_argument('--cff', dest='formats', action='append_const',
                        const='cff', help='save output as CFF/OTF (default)')
    parser.add_argument('--debug', action='store_true',
                        help='keep temporary FDK files.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print makeotf output to console.')
    options = parser.parse_args(args)
    for ufopath in options.infiles:
        # make sure inputs are valid UFO directories
        if (not os.path.isdir(ufopath) or
                not os.path.exists(os.path.join(ufopath, 'metainfo.plist'))):
            parser.error('Invalid UFO font: "%s"' % ufopath)
    if not options.formats:
        # default to CFF/OTF output
        options.formats = ['cff']
    else:
        # prune duplicate format entries
        options.formats = list(set(options.formats))
    return options


def main(args=None):
    options = parse_options(args)
    for ufopath in options.infiles:
        build(ufopath, options.output_dir, options.formats, options.debug,
              options.verbose)


if __name__ == "__main__":
    main()
