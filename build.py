#!/usr/bin/env python

from __future__ import print_function, unicode_literals
import sys
import os
import errno
from ufo2fdk import OTFCompiler
from defcon import Font
import argparse
import tempfile
import shutil
import logging
from ufo2ft.outlineOTF import OutlineTTFCompiler
from fontTools.ttLib import TTFont

CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TOOLS_DIR = os.path.join(CURR_DIR, 'tools')
sys.path.insert(0, TOOLS_DIR)
from convert import font_to_quadratic
from mark import MarkFeatureWriter
from rename import GoadbManager


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


def compile_otf(font, release_mode=False, debug=False):
    """Compile UFO into a CFF TTFont instance."""
    compiler = OTFCompiler(savePartsNextToUFO=debug)

    fd, tmpfile = tempfile.mkstemp()
    try:
        os.close(fd)
        report = compiler.compile(
            font, tmpfile, releaseMode=release_mode,
            glyphOrder=font.glyphOrder)
        ttFont = TTFont(tmpfile)
    finally:
        os.remove(tmpfile)

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


def build(ufopath, output_dir=None, formats=['cff'], goadb=None, debug=False,
          verbose=True):
    if ufopath.endswith(os.sep):
        # strip any trailing forward or backslash
        ufopath = ufopath[:-1]

    font = Font(ufopath)

    mark_feature = MarkFeatureWriter(font).write()
    font.features.text += "\n\n" + mark_feature

    otf = compile_otf(
        font, release_mode=(True if 'cff' in formats else False),
        debug=debug)

    for fmt in formats:
        outfile = make_output_name(ufopath, fmt, output_dir)

        if fmt == 'ttf':
            logging.info('Converting UFO to TrueType...')
            font_to_quadratic(font, max_err=1.0)
            if debug:
                # save quadratic UFO (and overwrite existing)
                quadpath = os.path.splitext(ufopath)[0] + '_quad.ufo'
                if os.path.isdir(quadpath):
                    shutil.rmtree(quadpath)
                font.save(quadpath, formatVersion=font.ufoFormatVersion)

            ttf = compile_ttf(font)

            # copy OpenType layout tables compiled by makeotf
            for tag in ('GDEF', 'GSUB', 'GPOS'):
                ttf[tag] = otf[tag]

            # copy makeotf-generated Mac Roman cmap subtable
            cmap6_1_0 = otf['cmap'].getcmap(1, 0)
            ttf['cmap'].tables.append(cmap6_1_0)

            ttf.save(outfile)

            if goadb:
                logging.info('Rename glyphs using "%s"...' % goadb)
                rename_glyphs(goadb, outfile)
        else:
            otf.save(outfile)
            # XXX rename glyphs in CFF fonts?

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
              options.debug, options.verbose)


if __name__ == "__main__":
    main()
