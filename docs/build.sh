#!/bin/sh

export LC_ALL=en_US

make html

make latex
cd _build/latex
xelatex *.tex
cp django-cdshanyou.pdf ../.

