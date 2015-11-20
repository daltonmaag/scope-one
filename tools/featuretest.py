# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# import re
import json
import sys
from io import open
from subprocess import Popen, PIPE


def run_hb_shape(font_file_name, test):
    """Get hb-shape output give a font and a text"""
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


def run_tests(font_file_name, test_definition):
    """Run a series of given tests on a font file with Harbfuzz"""
    failed = []
    passed = []

    for test in test_definition:
        expect = test['e']
        output = run_hb_shape(font_file_name, test)
        test['result'] = '|'.join(glyph['g'] for glyph in output)
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
        return 1
    else:
        return 0


def main(args):
    import json

    test_definition_file = args[0]
    with open(test_definition_file, 'r', encoding='utf-8') as f:
        test_definition = json.load(f)
    font_files = args[1:]
    failed = False
    for font_file_name in font_files:
        run_tests(font_file_name, test_definition)
    if failed:
        exit(1)


usage = '''\
Usage:
  featuretest.py <test definition file> <font...>

Use a JSON file with an array of test objects.
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
    if len(sys.argv) < 3:
        print(usage)
        exit(1)
    main(sys.argv[1:])
