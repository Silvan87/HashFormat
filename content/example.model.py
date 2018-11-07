#!/usr/bin/python

from hashlib import HashModel

model = HashModel()

## Input and output specification

model.setInputFiles('example')
model.setOutputFiles('example.html')
model.setOutputFolder('./')

## Lazy model instructions

model.setOpeningText('<!DOCTYPE html><html><head><title>Example</title><meta charset="utf-8" />'
	'<style>body{width:800px;margin:0 auto;}.grey{color:grey;margin-top:0;padding-top:0;}</style>'
	'</head><body>')

# A tip to easily insert text as it is
model.addPredicate('#this', ['#'])

# addPredicate is an instruction, the 1st string is the predicate name
# the 2nd argument is a list, in that list you can put a piece of string
# or the value of predicate itself by a single hash: #
# It's possibile to use #other-predicate-name to put the value of
# corresponding predicate. It will catch the next predicate yet unused.
# If you want the value of the next predicate even if just used, then
# you use double hash before predicate name ##other-predicate-name
model.addPredicate('#bold', ['<b>', '#', '</b>'])

model.addPredicate('#italic', ['<i>', '#', '</i>'])

model.addPredicate('#title', ['<h1>', '#', '</h1>'])

model.addPredicate('#paragraph', ['<p>', '#', '</p>'])

model.addPredicate('#paragraph-italian', ['<p class="grey">', '#', '</p>'])

model.addPredicate('#N', [' <sup>[N]</sup>'])

# The predicates can be treat in series and it needs a name predicate to stop the series
# You can use the ending dash in the stop name to specify the name itself
# without dash and any other name with dash and something after that.
model.setPredicateSeriesStopNames('#title-', '#list', '#paragraph')

# This treat a series of #list-item, its name is in the 1st argument
# 2nd argument is a string to put before the series
# 3rd argument is a list with the same logic of the addPredicate instruction
# 4th argument is a string to put after the series
model.addPredicateSeries('#list-item',
	'<h2>English list</h2><ul>',
	['<li>', '#', '</li>'],
	'</ul>')

model.addPredicateSeries('#list-item-spanish',
	'<h2>Spanish list</h2><ul>',
	['<li>', '#', '</li>'],
	'</ul>')

model.setClosingText('</body></html>')

## Generate output with the model instructions

model.generateOutputFiles()
