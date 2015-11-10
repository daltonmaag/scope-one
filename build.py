from __future__ import print_function, unicode_literals
import sys
import os
from io import open
from ufo2fdk import OTFCompiler
from defcon import Font

try:
    from plistlib import load
except ImportError:
    from plistlib import readPlist as load


def groups_to_features(ufo_path):
    """
    Translate and copy UFO groups.list file to FEA features groups.
    For example:
    <dict>
        <key>figDef</key>
        <array>
            <string>zero</string>
            <string>one</string>
            <string>two</string>
            <string>three</string>
            <string>four</string>
            <string>five</string>
            <string>six</string>
            <string>seven</string>
            <string>eight</string>
            <string>nine</string>
        </array>
    </dict>
    becomes
    @figDef = [zero one two three four five six seven eight nine];
    """
    path = os.path.join(ufo_path, "groups.plist")
    with open(path, "rb") as f:
        groups = load(f)

    output = []
    for group, lst in groups.items():
        if group.startswith("@"):
            output.append("{} = [{}]".format(group, " ".join(lst)) + ";\n")
        else:
            output.append("@{} = [{}]".format(group, " ".join(lst)) + ";\n")

    path = os.path.join(ufo_path, "features.fea")
    with open(path, "r") as f:
        features = f.readlines()

    newFeatures = output + [""] + features

    with open(path + ".bak", "w") as f:
        f.writelines(features)
    with open(path, "w") as f:
        f.writelines(newFeatures)


def clean_up_features(ufo_path):
    path = os.path.join(ufo_path, "features.fea")
    if os.path.exists(path + ".bak"):
        if os.path.exists(path):
            os.remove(path)
        os.rename(path + ".bak", path)


def build(family, styles):
    family = family.replace(" ", "_")
    for w in styles:
        if w == "Regular":
            ufo_path = "source/{}.ufo".format(family)
        else:
            ufo_path = "source/{}-{}.ufo".format(family, w)

        groups_to_features(ufo_path)

        font = Font(ufo_path)
        compiler = OTFCompiler(
            savePartsNextToUFO=len(sys.argv) > 1 and sys.argv[1] == "debug")
        reports = compiler.compile(font, family + "-" + w + ".otf",
                                   checkOutlines=False, autohint=False,
                                   releaseMode=True)

        print(reports["autohint"])
        print(reports["makeotf"])
        clean_up_features(ufo_path)


if __name__ == "__main__":
    family = "Deck Slab"
    styles = ["Regular"]
    build(family, styles)
