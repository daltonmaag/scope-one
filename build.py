from __future__ import print_function, unicode_literals
import os
from ufo2fdk import OTFCompiler
from defcon import Font
from collections import defaultdict
import argparse


STYLE_MAP = {
    "Regular": "Rg",
    "Italic": "It",
    "Bold": "Bd",
    "Bold Italic": "BdIt",
}


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


def make_output_name(font, ext="otf"):
    # strip spaces from family name
    family = font.info.familyName.replace(" ", "")
    # try to shorten the style name using default mapping
    style = font.info.styleName
    shortstyle = STYLE_MAP[style] if style in STYLE_MAP else style
    return family + "_" + shortstyle + "." + ext


def build(ufopath, flavor='otf', debug=False, verbose=True):
    font = Font(ufopath)

    dirname = os.path.dirname(ufopath)
    outfile = os.path.join(dirname, make_output_name(font, flavor))

    mark_feature = MarkFeatureWriter(font).write()
    font.features.text += "\n\n" + mark_feature

    compiler = OTFCompiler(savePartsNextToUFO=debug)
    reports = compiler.compile(font, outfile,
                               checkOutlines=False, autohint=False,
                               releaseMode=True,
                               glyphOrder=font.glyphOrder)
    if verbose:
        print(reports["makeotf"])


def parse_options(args):
    parser = argparse.ArgumentParser(
        description="Compile UFO to OpenType font.")
    parser.add_argument('infiles', metavar='INPUT', nargs="+",
                        help='input UFO font files.')
    parser.add_argument('-f', '--flavor', default='otf',
                        choices=['otf', 'ttf'],
                        help='output font flavor ("otf" or "ttf").')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='keep temporary FDK files.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print makeotf output to console.')
    return parser.parse_args(args)


def main(args=None):
    options = parse_options(args)
    for ufopath in options.infiles:
        build(ufopath, options.flavor, options.debug, options.verbose)


if __name__ == "__main__":
    main()
