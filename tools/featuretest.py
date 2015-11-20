# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# import re
import json
import sys
import os
import argparse
from io import open
from subprocess import Popen, PIPE

CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TOOLS_DIR = os.path.join(CURR_DIR, 'tools')
sys.path.insert(0, TOOLS_DIR)
from rename import GoadbManager


__version__ = '0.1'


def run_hb_shape(font_file_name, test):
    '''Get hb-shape output give a font and a text'''
    hb_parameters = [
        'hb-shape',
        "--output-format=json"
    ]
    if 'f' in test.keys():
        feat = test['f']
        hb_parameters.append('--features={}'.format(feat))
    if 'l' in test.keys():
        lang = test['l']
        hb_parameters.append('--language={}'.format(lang))
    if not ('p' in test.keys()):
        hb_parameters.append('--no-positions')
    if not ('c' in test.keys()):
        hb_parameters.append('--no-clusters')
    hb_parameters.append('--font-file={}'.format(font_file_name))
    text = test['t']

    # run hb-shape
    process = Popen(hb_parameters, stdin=PIPE, stdout=PIPE)
    output_data, err_data = process.communicate(text.encode('utf-8'))
    output_text = output_data.decode('utf-8')
    data = json.loads(output_text)

    return data


def run_tests(font_file_name, test_definition, goadb_file_name):
    """Run a series of given tests on a font file with Harbfuzz"""
    failed = []
    passed = []
    glyph_dict = get_glyphs_names(goadb_file_name)

    for test in test_definition:
        expect = test['e']
        output = run_hb_shape(font_file_name, test)
        test['result'] = '|'.join(glyph_dict[glyph['g']] for glyph in output)
        if test['result'] != expect:
            failed.append(test)
        else:
            passed.append(test)
    for test in passed:
        test_desc = test['d']
        print('pass - ' + test_desc)
    for test in failed:
        test_desc = test['d']
        print('')
        print('FAIL * ' + test_desc + ':')
        print('- ' + str(test['e']))
        print('+ ' + str(test['result']))
        print('')
    print('Passed ' + str(len(passed)) + ' test(s)')
    print('Failed ' + str(len(failed)) + ' test(s)')

    if len(failed) > 0:
        return True
    else:
        return False


def get_glyphs_names(goadb_file_name):
    name_dict, _ = GoadbManager.parse_goadb(goadb_file_name)
    inv_name_dict = {v: k for k, v in name_dict.items()}
    return inv_name_dict


def parse_options(args):
    parser = argparse.ArgumentParser(
        description="Runs substition features tests on a font.",
        usage=usage)
    parser.add_argument('testjsonfile', metavar='TESTJSON',
                        help='Input font file.')
    parser.add_argument('fontfile', metavar='FONTFILE',
                        help='Font file being tested')
    parser.add_argument('-g', '--goadb', metavar='GOADB.txt',
                        help='Use GlyphOrderAndAliasDB to rename glyphs.')
    parser.add_argument('--version', action='version', version=__version__)
    options = parser.parse_args(args)
    return options


def main(args):
    options = parse_options(args)

    with open(options.testjsonfile, 'r', encoding='utf-8') as f:
        test_definition = json.load(f)
    failed = run_tests(options.fontfile, test_definition,
                       options.goadb)
    if failed:
        exit(1)


usage = '''\
Usage:
  featuretest.py [-g <GOADB file>] <test definition file> <font...>

Runs substition features tests on a font.
Use a test definition JSON file with an array of test objects,
with an optional GlyphOrderAndAliasDB file if glyphs have been renamed.
Harfbuzz's hb-shape must be installed and in the PATH.
Each test object must have:
  't'  : Unicode input text
  'e'  : expected hb-shape glyph output
  'd'  : test description
Optional:
  'l'  : language code
  'f'  : features (see hb-shape for format)
  'p'  : enables positions in expected hb-shape output
  'c'  : enables clusters info in expected hb-shape output
'''

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(usage)
        exit(1)
    main(sys.argv[1:])
