# Scope One

Scope One is a design optimised for titling and display sizes, ideally used at 14 point and above. The vertical proportions of the typeface allow for all-caps setting that is more akin to using small caps, giving a more refined typographic impression. Scope One is a light slab serif typeface with an elegant expression for a wide range of usages. The font features four sets of numerals, lining and old style, proportional and tabular. The proportional lining numerals are placed on the default keyboard positions with the alternatives accessible via OpenType feature.

Scope One supports a broad range of languages using the Latin alphabet and contains a large set of currencies including the recent Unicode addition of the Bitcoin symbol. The font has been enhanced for good quality display on screen, and has been tested extensively in a variety of on-screen and print environments.

Scope One is a Dalton Maag original design, commissioned by Google.

For a live font specimen you can go to [http://daltonmaag.github.io/scope-one/](http://daltonmaag.github.io/scope-one/)

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
- ttfautohint
- Harfbuzz (for testing only)

Make sure all the requirements are in your PATH.

### Setting up Python virtual environment

- create a new virtual environment by running the `pyvenv` script

  `$ pyvenv /path/to/new/virtual/environment`

- if you don't have `pyvenv` in your PATH, you can invoke it as follows

  `python -m venv /path/to/new/virtual/environment`

- activate virtual environment on OS X or Linux

  `$ source <venv>/bin/activate`

- activate virtual environment on Win

  `$ <venv>\Scripts\activate.bat`

More info on setting up virtual environments can be found at [Python docs](https://docs.python.org/3/library/venv.html).

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

  `$ python tools/featuretest.py -g source/GlyphOrderAndAliasDB.txt test/test.json build/ScopeOne_Rg.ttf`

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
