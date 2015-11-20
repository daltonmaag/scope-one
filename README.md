# Scope One

Light weight, upright slab serif.

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
- Python 3.x
- pip
- virtualenv
- Harfbuzz (for testing only)

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

  `$ build.sh`

- Build on Windows

  `$ build.bat`

The fonts can be found on the `build` folder.

### Testing the font

- Run test script on OS X and Linux

  `$ python tools/featuretest.py test/test.json build/ScopeOne_Rg.ttf`

- Run test script on Windows

  `$ python tools\featuretest.py test\test.json build\ScopeOne_Rg.ttf`

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
