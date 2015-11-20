# Scope One

Scope One is a light weight, slab serif font. It is designed to work well on display sizes, 14pt and upwards, for titling purposes. The short ascenders and descenders allowed to create an uppercase that imitates proportions closer to small capitals, ensuring that an all-caps setting works well without any extra refinement. It is optimised to work on screen but has also been tested for text usage both on screen and print.

Display being its primary purpose the default figures are proportional lining, however the font also contains lining tabular and two sets of oldstyle figures (proportional and tabular). Anchors were positioned on the A-Z and a-z glyphs allowing accented characters to be built on the fly. A large set of currencies is provided, including the recent addition of the bitcoin symbol.

## License

Scope One is licensed under the [SIL Open Font License v1.1](http://scripts.sil.org/OFL).
To view the copyright and specific terms and conditions please refer to LICENSE.txt.

## Repository tree

source - UFO (format 2), autohint control file, GOADB

test - font testing files

tools - build and test scripts

## Build instructions

### Requirements

- AFDKO (latest)
- Python 3.3+
- pip
- virtualenv
- ttfautohint
- Harfbuzz (for testing only)

Make sure all the requirements are in your PATH.

### Setting up Python virtual environment

- create virtual environment in new 'venv' folder

  `$ python3 -m virtualenv venv`

- activate venv on OS X or Linux

  `$ source venv/bin/activate`

- activate venv on Win

  `$ venv\Scripts\activate.bat`

### Installing dependencies via requirements.txt

`$ pip install -r requirements.txt`

### Building the font

- Build on OS X or Linux

  `$ ./build.sh`

- Build on Windows

  `$ build.bat`

The fonts can be found in the `build` folder.

### Testing the font

- Run test script

  `$ python tools/featuretest.py test/test.json build/ScopeOne_Rg.ttf`

### Deactivating Python virtual environment

`$ deactivate`

* * *

## Plan

- [x] Concept
- [x] Design
  - [x] ASCII
  - [x] Full glyphset
  - [x] Kerning
  - [x] Design testing
- [x] OT Features
  - [x] OT testing
- [x] Hinting
  - [x] Hinting testing
- [x] Build
  - [x] Font info
  - [x] Scripts
- [x] DONE!
