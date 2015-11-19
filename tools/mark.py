from __future__ import print_function, unicode_literals
import sys
from collections import defaultdict


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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    from defcon import Font
    font = Font(sys.argv[1])
    writer = MarkFeatureWriter(font)
    print(writer.write())
