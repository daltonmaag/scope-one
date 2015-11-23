#!/usr/bin/env python

from __future__ import print_function, unicode_literals
import sys
import os
import errno
import argparse
import tempfile
import shutil
import logging
import subprocess
import shlex

from ufo2fdk import OTFCompiler
from defcon import Font
from ufo2ft.outlineOTF import OutlineTTFCompiler
from ufo2ft.markFeatureWriter import MarkFeatureWriter
from fontTools.ttLib import TTFont


CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TOOLS_DIR = os.path.join(CURR_DIR, 'tools')
sys.path.insert(0, TOOLS_DIR)
from convert import font_to_quadratic
from rename import GoadbManager


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def make_output_name(ufopath, extension, output_dir=None):
    dirname, basename = os.path.split(ufopath)
    ufoname = os.path.splitext(basename)[0]
    if output_dir is None:
        # use same folder as ufopath
        output_dir = dirname
    else:
        # create output_dir if it doesn't exist
        mkdir_p(output_dir)
    return os.path.join(output_dir, ufoname + extension)


def compile_otf(font, release_mode=False, autohint=False, debug=False):
    """Compile UFO into a CFF TTFont instance."""
    compiler = OTFCompiler(savePartsNextToUFO=debug)

    fd, tmpfile = tempfile.mkstemp()
    try:
        os.close(fd)
        report = compiler.compile(
            font, tmpfile, releaseMode=release_mode,
            autohint=autohint, glyphOrder=font.glyphOrder)
        ttFont = TTFont(tmpfile)
    finally:
        os.remove(tmpfile)

    if autohint:
        logging.info(report["autohint"])
    logging.info(report["makeotf"])
    return ttFont


def compile_ttf(font, max_err=1.0):
    """Compile UFO into a TrueType TTFont instance."""
    compiler = OutlineTTFCompiler(font, font.glyphOrder)
    return compiler.compile()


def rename_glyphs(goadb, fontfile):
    manager = GoadbManager(goadb, fontfile)
    manager.rename_glyphs()
    manager.save(fontfile)
    manager.close()


def ttfautohint(infile, outfile=None, ctrlfile=None, options=None):
    overwrite = False
    if not outfile:
        fd, outfile = tempfile.mkstemp()
        os.close(fd)
        overwrite = True
    cmdline = ["ttfautohint"]
    if options is not None:
        cmdline += shlex.split(options)
    if ctrlfile is not None:
        cmdline += ["-m", ctrlfile]
    cmdline += [infile, outfile]
    logging.info("Run ttfautohint")
    logging.info("$ " + " ".join(cmdline))
    if not shutil.which('ttfautohint'):
        raise RuntimeError('ttfautohint: command not found')
    try:
        subprocess.check_call(cmdline)
    except:
        raise
    else:
        if overwrite:
            os.remove(infile)
            logging.info("$ mv %s %s" % (outfile, infile))
            shutil.copyfile(outfile, infile)
    finally:
        if overwrite:
            os.remove(outfile)


def build(ufopath, output_dir=None, formats=['cff'], goadb=None, debug=False,
          autohint=False, tta_ctrlfile=None, tta_options=None, verbose=True):
    if ufopath.endswith(os.sep):
        # strip any trailing forward or backslash
        ufopath = ufopath[:-1]

    dirname, ufoname = os.path.split(ufopath)

    if output_dir is None:
        # use the same folder as ufopath
        output_dir = dirname

    # create the output_dir if it doesn't exist
    mkdir_p(output_dir)

    # create a temporary build folder in the output_dir
    build_dir = tempfile.mkdtemp(prefix='build-', dir=output_dir)

    # make a temporary copy of ufo inside build_dir
    tmpufo = os.path.join(build_dir, ufoname)
    shutil.copytree(ufopath, tmpufo)

    font = Font(tmpufo)

    mark_feature = MarkFeatureWriter(font).write()
    font.features.text += "\n\n" + mark_feature

    logging.info('Compile OTF')
    otf = compile_otf(
        font, release_mode=(True if 'cff' in formats else False),
        autohint=(autohint if "cff" in formats else False), debug=debug)

    for fmt in formats:
        ext = ".otf" if fmt == 'cff' else '.ttf'
        outfile = make_output_name(ufopath, ext, output_dir)

        if fmt == 'ttf':
            logging.info('Convert UFO curves to quadratic splines')
            font_to_quadratic(font, max_err=1.0)
            if debug:
                # save quadratic UFO
                quadpath = os.path.splitext(tmpufo)[0] + '_quad.ufo'
                font.save(quadpath, formatVersion=font.ufoFormatVersion)

            logging.info('Compile UFO to TTF')
            ttf = compile_ttf(font)

            logging.info('Copy OpenType layout tables from OTF to TTF')
            for tag in ('GDEF', 'GSUB', 'GPOS'):
                ttf[tag] = otf[tag]

            # copy makeotf-generated Mac Roman cmap subtable
            cmap6_1_0 = otf['cmap'].getcmap(1, 0)
            ttf['cmap'].tables.append(cmap6_1_0)

            logging.info('Save font')
            ttf.save(outfile)

            if autohint:
                ttfautohint(outfile, ctrlfile=tta_ctrlfile,
                            options=tta_options)
            if goadb:
                logging.info('Rename glyphs using "%s"' % goadb)
                rename_glyphs(goadb, outfile)
        else:
            logging.info('Save font')
            otf.save(outfile)
            # XXX rename glyphs in CFF fonts?

    # remove temp ufo copy
    shutil.rmtree(tmpufo)
    if not debug:
        # unless --debug option is passed, also remove temp build_dir
        shutil.rmtree(build_dir)

    logging.info('Done!')


def parse_options(args):
    parser = argparse.ArgumentParser(
        description="Compile UFOs to OpenType fonts.")
    parser.add_argument('infiles', metavar='INPUT', nargs="+",
                        help='input UFO source files.')
    parser.add_argument('-d', '--output-dir', metavar='DIR', nargs="?",
                        help="output directory. If it doesn't exist, it will "
                        "be created (default: same as input UFO).")
    parser.add_argument('--ttf', dest='formats', action='append_const',
                        const='ttf', help='save output as TTF/OTF (default).')
    parser.add_argument('--cff', dest='formats', action='append_const',
                        const='cff', help='save output as CFF/OTF.')
    parser.add_argument('-g', '--goadb', metavar='GOADB.txt',
                        help='Use GlyphOrderAndAliasDB to rename glyphs (TTF '
                        'only).')
    parser.add_argument('--debug', action='store_true',
                        help='keep temporary FDK files.')
    parser.add_argument('--autohint', action='store_true',
                        help="hint font using ttfautohint or Adobe autohint.")
    parser.add_argument('--tta-control-file', metavar='FILE',
                        help="get ttfautohint control instructions from FILE.")
    parser.add_argument('--tta-options', metavar='STRING',
                        help="options for ttfautohint.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print makeotf output to console.')
    options = parser.parse_args(args)
    for ufopath in options.infiles:
        # make sure inputs are valid UFO directories
        if (not os.path.isdir(ufopath) or
                not os.path.exists(os.path.join(ufopath, 'metainfo.plist'))):
            parser.error('Invalid UFO font: "%s"' % ufopath)
    if not options.formats:
        # default to TTF/OTF output
        options.formats = ['ttf']
    else:
        # prune duplicate format entries
        options.formats = list(set(options.formats))
    return options


def main(args=None):
    options = parse_options(args)

    logging.basicConfig(
        format='%(message)s',
        level=logging.DEBUG if options.verbose else logging.WARNING)

    for ufopath in options.infiles:
        build(ufopath, options.output_dir, options.formats, options.goadb,
              options.debug, options.autohint, options.tta_control_file,
              options.tta_options, options.verbose)


if __name__ == "__main__":
    main()
