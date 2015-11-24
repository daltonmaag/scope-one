#!/bin/sh

python tools/build.py \
	--output-dir build \
	--autohint --tta-control-file source/ttfautohint.ctrl --tta-options "-D latn -f latn -l 11 -G 50 -n" \
	--goadb source/GlyphOrderAndAliasDB.txt \
	source/ScopeOne_Rg.ufo $*
