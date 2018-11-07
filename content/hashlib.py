# Instruction library to define models and the necessary internal functions #

import sys, os, re, __main__

class HashModel:

	def __init__(self):

		self.inputFileNames = []
		self.outputFileNames = []
		self.scriptFolder = sys.path[0] + '/'
		self.outputFolder = './'
		self.toParseHashFileNames = []
		self.toGenerateOutputFileNames = []

		self.currentFileName = ''
		self.currentFileNumber = 0
		self.currentRowNumber = 0

		self.parsedHashFiles = []
		self.processedPredicates = []
		self.predicateModels = []
		self.predicateModelIdByName = {}
		self.predicateSeriesStopNames = []

		self.openingText = ''
		self.closingText = ''
		self.currentValueAsTextRows = []
		self.currentValue = ''
		self.dotPredicateCounter = 0
		self.startedDotSubstringFlags = []


	class DotPredicate:

		def __init__(self):
			self.name = ''
			self.substringIds = []


	class SubstringsAndThemPredicates:

		def __init__(self):
			self.substrings = []
			self.dotPredicates = []


	class PredicateModel:

		def __init__(self):
			self.name = ''
			self.inSeries = False
			self.beforeSeries = ''
			self.afterSeries = ''
			self.valueComposition = []


	class Predicate:

		def __init__(self):
			self.name = ''
			self.value = ''


	## INTERNAL FUNCTIONS ##

	def isPredicateSeriesStopName(self, predicateName):
		for i in range(0, len(self.predicateSeriesStopNames)):
			# If the predicate name ends with - (dash), it can match the predicate without - or up to -
			if self.predicateSeriesStopNames[i][-1] == '-':
				if predicateName == self.predicateSeriesStopNames[i][1:-1] or \
					predicateName.startswith(self.predicateSeriesStopNames[i][1:]):
					return True
			else:
				if predicateName == self.predicateSeriesStopNames[i][1:]:
					return True

		return False


	def valueOfNextPredicate(self, predicateName, fromPredicateIndex):
		for i in range(fromPredicateIndex + 1, len(self.parsedHashFiles[self.currentFileNumber])):

			# Double hash ## forces the use of the next predicate that is encountered (here only another # can remain)
			if predicateName[0] == '#':
				if self.parsedHashFiles[self.currentFileNumber][i].name == predicateName[1:]:
					return self.parsedHashFiles[self.currentFileNumber][i].value

			else:
				if self.processedPredicates[i] == 0 and self.parsedHashFiles[self.currentFileNumber][i].name == predicateName:
					self.processedPredicates[i] = 1
					return self.parsedHashFiles[self.currentFileNumber][i].value

		return ''


	def manageDotSubstrings(self, predicateIndex):
		value = self.parsedHashFiles[self.currentFileNumber][predicateIndex].value
		outputSubstrings = value.substrings

		for i in range(0, len(value.dotPredicates)):
			try:
				predicateModel = self.predicateModels[self.predicateModelIdByName[value.dotPredicates[i].name]]
			except:
				continue

			reachedPredicateValue = False
			stringBeforePredicateValue = ''
			firstSubstringId = value.dotPredicates[i].substringIds[0]
			lastSubstringId = value.dotPredicates[i].substringIds[-1]

			if predicateModel.inSeries == False:
				for valueItem in predicateModel.valueComposition:
					if valueItem == '':
						continue

					elif valueItem == '#':
						# The value of dot predicate is the relative dot substring itself
						# The position of the predicate value has been reached, further item strings of the model are placed
						# at the end of the last dot substring to which the predicate is applied
						reachedPredicateValue = True

					elif valueItem[0] == '#':
						predicateName = valueItem[1:]
						# The next predicate is not searched among the dot predicates
						# But the use of dot predicates must remain limited to specifications for substrings
						if reachedPredicateValue:
							outputSubstrings[lastSubstringId] += self.valueOfNextPredicate(predicateName, predicateIndex)
						else:
							stringBeforePredicateValue += self.valueOfNextPredicate(predicateName, predicateIndex)

					elif valueItem[0:2] == '\#': # the only valid combination is \#
						# It's possibile to have a normal string that starts with # via the escape character \
						if reachedPredicateValue:
							outputSubstrings[lastSubstringId] += valueItem[1:]
						else:
							stringBeforePredicateValue += valueItem[1:]

					else:
						if reachedPredicateValue:
							outputSubstrings[lastSubstringId] += valueItem
						else:
							stringBeforePredicateValue += valueItem

				if reachedPredicateValue:
					outputSubstrings[firstSubstringId] = stringBeforePredicateValue + outputSubstrings[firstSubstringId]
				else:
					# BUG A fixed predicate value composition replaces the substrings to which the predicate applies.
					# However, only the first substring and not all ones are substituted. This bug is really marginal,
					# because if you want to completely replace a substring, you would not break it down into further
					# substrings by associating them some dot predicates. The bug should never rise up.
					outputSubstrings[firstSubstringId] = stringBeforePredicateValue

			else:
				sys.exit('Error. File: %s, row %i. A predicate series in the position of dot predicate is not allowed.'
					% (self.currentFileName, self.currentRowNumber))

		return ''.join(outputSubstrings)


	def collectValueAfterPredicateName(self, predicateNameEndPosition, textRow):
		string = textRow[predicateNameEndPosition:].strip()
		if string != '':
			self.currentValueAsTextRows.append(string)


	def removeFlagFromLastDotPredicate(self):
		for i in range(0, len(self.startedDotSubstringFlags)):
			if self.startedDotSubstringFlags[-i-1] == 1:
				self.startedDotSubstringFlags[-i-1] = 0
				return

		# To end more dot substrings than those that have been started is not allowed
		sys.exit('Error. File: %s. There is a closing substring symbol too many in the row %i or earlier.'
			% (self.currentFileName, self.currentRowNumber))


	def addCurrentSubstringIdToFlaggedDotPredicates(self):
		currentTechSubstringId = len(self.currentValue.substrings) - 1
		for i in range(0, len(self.startedDotSubstringFlags)):
			if self.startedDotSubstringFlags[i] == 1:
				self.currentValue.dotPredicates[i].substringIds.append(currentTechSubstringId)


	def addTechSubstringToCurrentValue(self, string, newTechSubstringToStart):
		if newTechSubstringToStart:
			self.currentValue.substrings.append(string)
		else:
			self.currentValue.substrings[-1] += string


	def getDotSubstringsOfCurrentValue(self):
		# It starts from the current value which is a collection of text rows
		# The delimiters ==( )== can nest and they define the dot substrings
		# A dot substring is a substring to which a dot predicate is applied
		# The delimiters generate tech(nical) substrings that compose the dot substrings
		# It may happen that a simple string is returned, if there are no dot substrings

		self.currentValue = self.SubstringsAndThemPredicates()
		self.startedDotSubstringFlags = []
		newTechSubstringToStart = True

		for textRow in self.currentValueAsTextRows:

			# Remove initial escape char \, but in case of \==( or \)== sequences
			if textRow[0:4] != '\\==(' and textRow[0:4] != '\\)==' and textRow[0] == '\\': textRow = textRow[1:]

			initialDotSubstringPosition = finalDotSubstringPosition = -1
			p = pp = 0 # p: parsing position, pp: previous parsing position

			while True:
				# Search possible combinations of special chars (the delimiters)
				initialDotSubstringPosition = textRow.find('==(', p)
				finalDotSubstringPosition = textRow.find(')==', p)

				# Evaluate if ==( comes first or comes alone
				if (initialDotSubstringPosition != -1 and finalDotSubstringPosition != -1 and \
					initialDotSubstringPosition < finalDotSubstringPosition) or \
					(initialDotSubstringPosition != -1 and finalDotSubstringPosition == -1):

					# Check if there is an escape char \ before
					if initialDotSubstringPosition > 0 and \
						textRow[initialDotSubstringPosition-1:initialDotSubstringPosition] == '\\':

						textRow = textRow[0:initialDotSubstringPosition-1] + textRow[initialDotSubstringPosition:]
						p = initialDotSubstringPosition + 3
						self.addTechSubstringToCurrentValue(textRow[pp:p], newTechSubstringToStart)
						newTechSubstringToStart = False

					# Manage the delimiter ==(
					else:
						p = initialDotSubstringPosition + 3
						self.addTechSubstringToCurrentValue(textRow[pp:p-3], newTechSubstringToStart)

						dotPredicate = self.DotPredicate()
						self.currentValue.dotPredicates.append(dotPredicate)
						self.addCurrentSubstringIdToFlaggedDotPredicates()
						self.startedDotSubstringFlags.append(1)
						newTechSubstringToStart = True

				# Evaluate if )== comes first or comes alone
				elif (initialDotSubstringPosition != -1 and finalDotSubstringPosition != -1 and \
					finalDotSubstringPosition < initialDotSubstringPosition) or \
					(finalDotSubstringPosition != -1 and initialDotSubstringPosition == -1):

					# Check if there is an escape char \ before
					if finalDotSubstringPosition > 0 and \
						textRow[finalDotSubstringPosition-1:finalDotSubstringPosition] == '\\':

						textRow = textRow[0:finalDotSubstringPosition-1] + textRow[finalDotSubstringPosition:]
						p = finalDotSubstringPosition + 3
						self.addTechSubstringToCurrentValue(textRow[pp:p], newTechSubstringToStart)
						newTechSubstringToStart = False

					# Manage the delimiter )==
					else:
						p = finalDotSubstringPosition + 3
						self.addTechSubstringToCurrentValue(textRow[pp:p-3], newTechSubstringToStart)
						self.addCurrentSubstringIdToFlaggedDotPredicates()
						self.removeFlagFromLastDotPredicate()
						newTechSubstringToStart = True

				# If no special chars found, manage the final tech substring
				elif initialDotSubstringPosition == -1 and finalDotSubstringPosition == -1:
					self.addTechSubstringToCurrentValue(textRow[pp:], newTechSubstringToStart)
					newTechSubstringToStart = False
					break

				pp = p

		if len(self.currentValue.dotPredicates) == 0:
			# No predicate means that the value is a simple string
			return self.currentValue.substrings[0]
		else:
			# Set the default predicate name with the first word of its relative substring
			for i in range(0, len(self.currentValue.dotPredicates)):
				name = self.currentValue.substrings[self.currentValue.dotPredicates[i].substringIds[0]]
				pattern = re.compile('[A-Za-z_][0-9A-Za-z_-]*')
				predicateName = pattern.match(name)
				if predicateName:
					name = predicateName.group(0)
				else:
					name = ''
				self.currentValue.dotPredicates[i].name = name
			return self.currentValue


	def setLastPredicateValueWithCurrentValue(self):
		if len(self.currentValueAsTextRows) > 0:
			self.parsedHashFiles[-1][-1].value = self.getDotSubstringsOfCurrentValue()


	def parseInputFiles(self):
		for self.currentFileName in self.toParseHashFileNames:

			# Read all text rows in the file and close it
			f = open(os.path.join(self.scriptFolder, self.currentFileName), 'r')
			textRows = f.readlines()
			f.close()

			# A list of parsed elements for each file
			self.parsedHashFiles.append([])

			# Number that indicates if you inside in a multiline comment (type 1 or 2) or not (0)
			insideMultilineComment = 0
			self.currentValueAsTextRows = [] # to collect strings that will become the predicate value
			parentPredicateNameStack = []
			previousDashNumber = 0

			# Parse the text rows
			for self.currentRowNumber, textRow in enumerate(textRows):

				# Remove beginning and end spaces
				textRow = textRow.strip()

				# Jump empty textRows
				if len(textRow) == 0:
					continue

				# Detect end of multiline comment (type 1)
				if insideMultilineComment == 1:
					if textRow[-2:] == '*/':
						insideMultilineComment = 0
						continue
					continue

				# Detect end of multiline comment (type 2)
				if insideMultilineComment == 2:
					pattern = re.compile('^#+$')
					if pattern.match(textRow):
						insideMultilineComment = 0
						continue
					continue

				# Detect single line comment (type 1)
				if textRow[0:2] == '//':
					continue

				# Detect single line comment (type 2)
				pattern = re.compile('^#+[^#0-9A-Za-z\_]')
				if pattern.match(textRow):
					continue

				# Detect start of multiline comment (type 1)
				if textRow[0:2] == '/*':
					insideMultilineComment = 1
					continue

				# Detect start of multiline comment (type 2)
				pattern = re.compile('^#+$')
				if pattern.match(textRow):
					insideMultilineComment = 2
					continue

				# Detect hash predicate
				if textRow[0:1] == '#':
					pattern = re.compile('[A-Za-z_][0-9A-Za-z_-]*')
					predicateName = pattern.match(textRow, 1)

					if predicateName:
						self.setLastPredicateValueWithCurrentValue()
						self.currentValueAsTextRows = []

						predicate = self.Predicate()
						predicate.name = predicateName.group(0)
						self.parsedHashFiles[-1].append(predicate)
						parentPredicateNameStack = [predicateName.group(0)]

						self.collectValueAfterPredicateName(predicateName.end(0), textRow)
						previousDashNumber = 0
						self.dotPredicateCounter = 0
						continue

				# Detect dash predicate
				pattern = re.compile('-+')
				dashes = pattern.match(textRow)

				if dashes:
					pattern = re.compile('[A-Za-z_][0-9A-Za-z_-]*')
					predicateName = pattern.match(textRow, dashes.end(0))

					if predicateName:
						if len(parentPredicateNameStack) == 0:
							# Dash predicate without hash predicate before is not allowed
							sys.exit('Error. File %s. The dash predicate on line %i has not '
								'an hash predicate before.' % (self.currentFileName, self.currentRowNumber + 1))

						dashNumber = len(dashes.group(0))

						if dashNumber > previousDashNumber + 1:
							sys.exit('Error. File %s. The dashes on line %i are too many compared to '
								'the previous indentation.' % (self.currentFileName, self.currentRowNumber + 1))

						if dashNumber > 1 and dashNumber > previousDashNumber:
							parentPredicateNameStack.append(previousPredicateName)

						elif dashNumber < previousDashNumber:
							parentPredicateNameStack = parentPredicateNameStack[0 : dashNumber-previousDashNumber]

						previousDashNumber = dashNumber
						previousPredicateName = predicateName.group(0)
						parentPredicateName = '-'.join(parentPredicateNameStack)

						self.setLastPredicateValueWithCurrentValue()
						self.currentValueAsTextRows = []

						predicate = self.Predicate()
						predicate.name = parentPredicateName + '-' + predicateName.group(0)
						self.parsedHashFiles[-1].append(predicate)

						self.collectValueAfterPredicateName(predicateName.end(0), textRow)
						self.dotPredicateCounter = 0
						continue

				# Detect dot predicate
				if textRow[0:1] == '.':
					pattern = re.compile('[A-Za-z_][0-9A-Za-z_-]*')
					predicateName = pattern.match(textRow, 1)

					if predicateName:
						self.setLastPredicateValueWithCurrentValue()
						self.currentValueAsTextRows = []

						# Set the previous substring predicate name to this dot predicate name
						try:
							self.parsedHashFiles[-1][-1].value.dotPredicates[self.dotPredicateCounter].name = predicateName.group(0)
						except:
							sys.exit('Error. File %s. The dot predicate at line %i is in excess.' \
								% (self.currentFileName, self.currentRowNumber + 1))

						self.dotPredicateCounter += 1
						continue

				# Any other string will result in a value for the previous predicate, it collects them
				self.currentValueAsTextRows.append(textRow)

				self.dotPredicateCounter = 0

			# When it finished parsing text, manage last value found
			self.setLastPredicateValueWithCurrentValue()
			self.currentValueAsTextRows = []


	def determineFilesToGenerate(self):
		# If the number of output files is not the same as the number of input files, then exit
		if not len(self.outputFileNames) == len(self.inputFileNames):
			sys.exit('In this model script the number of output files is not the same as the number of input files.'
				' Please, fix this inconsistency.')

		self.toParseHashFileNames = []
		self.toGenerateOutputFileNames = []

		modelScriptFilePath = os.path.join(self.scriptFolder, os.path.basename(__main__.__file__))

		# Collect file names to generate (if they don't exist or must to update)
		for n in range(0, len(self.outputFileNames)):
			if not os.path.isfile(self.outputFolder + self.outputFileNames[n]) or \
				os.stat(os.path.join(self.outputFolder + self.outputFileNames[n])).st_mtime < \
				os.stat(os.path.join(self.scriptFolder + self.inputFileNames[n])).st_mtime or \
				os.stat(os.path.join(self.outputFolder + self.outputFileNames[n])).st_mtime < \
				os.stat(modelScriptFilePath).st_mtime:
				self.toParseHashFileNames.append(self.inputFileNames[n])
				self.toGenerateOutputFileNames.append(self.outputFileNames[n])

		notToGenerateOutputFileNames = \
			[name for name in self.outputFileNames if name not in self.toGenerateOutputFileNames]

		if len(notToGenerateOutputFileNames) == 1:
			print(notToGenerateOutputFileNames[0] + ' skipped.\n'
				'It is more recent than its source file and its model script.')
		elif len(notToGenerateOutputFileNames) > 1:
			print(', '.join(notToGenerateOutputFileNames) + ' skipped.\n'
				'They are more recent than their source files and their model script.')
		if len(self.toGenerateOutputFileNames) > 0:
			print(', '.join(self.toGenerateOutputFileNames) + ' must be created or updated.')


	## PUBLIC FUNCTIONS ##

	def setInputFiles(self, *fileNames):
		self.inputFileNames = []
		for name in fileNames:
			if not name.endswith('.hsh'): name += '.hsh'
			self.inputFileNames.append(name)


	def setOutputFiles(self, *fileNames):
		self.outputFileNames = list(fileNames)


	def setOutputFolder(self, path):
		self.outputFolder = os.path.join(self.scriptFolder, path)


	def setOpeningText(self, text):
		self.openingText = text


	def setClosingText(self, text):
		self.closingText = text


	def addPredicate(self, name, valueComposition):
		if name[0] != '#' and name[0] != '.':
			sys.exit("The predicate name '%s' must start with '#' or '.'" % name)

		predicateModel = self.PredicateModel()
		predicateModel.name = name[1:]
		predicateModel.valueComposition = valueComposition
		self.predicateModels.append(predicateModel)


	def addPredicateSeries(self, name, beforeSeries, valueComposition, afterSeries):
		if name[0] != '#':
			sys.exit("The predicate name '%s' must start with '#' when it is used in a series." % name)

		predicate = self.PredicateModel()
		predicate.name = name[1:]
		predicate.inSeries = True
		predicate.beforeSeries = beforeSeries
		predicate.afterSeries = afterSeries
		predicate.valueComposition = valueComposition
		self.predicateModels.append(predicate)


	def setPredicateSeriesStopNames(self, *stops):
		self.predicateSeriesStopNames = stops


	def generateOutputFiles(self):
		self.determineFilesToGenerate()
		self.parseInputFiles()

		# Only predicates specified in the model will be managed and will produce some output text
		# Predicates must be in an ordered list, but it is also necessary to retrieve them through the name
		# So it needs a dictionary that associates the name of a predicate with its id in the ordered list
		for i in range(0, len(self.predicateModels)):
			self.predicateModelIdByName[self.predicateModels[i].name] = i

		for n in range(0, len(self.toParseHashFileNames)):
			self.currentFileNumber = n

			# Mark all predicates as unprocessed with a 0
			self.processedPredicates = [0] * len(self.parsedHashFiles[n])
			outputFileText = self.openingText

			# Perform all the encountered predicates
			for i in range(0, len(self.parsedHashFiles[n])):

				# If the predicate is already processed, skip it
				if self.processedPredicates[i] == 1:
					continue

				try:
					predicate = self.predicateModels[self.predicateModelIdByName[self.parsedHashFiles[n][i].name]]
				except:
					# When the predicate name in the hash file is not in the model, skip it
					continue

				# This predicate will be processed
				self.processedPredicates[i] = 1
				outputPredicateText = ''

				if predicate.inSeries == False:
					outputPredicateText += predicate.beforeSeries
					for valueString in predicate.valueComposition:
						if valueString == '#':
							value = self.parsedHashFiles[n][i].value
							if type(value) is self.SubstringsAndThemPredicates:
								value = self.manageDotSubstrings(i)
							outputPredicateText += value
						elif valueString[0] == '#':
							predicateName = valueString[1:]
							outputPredicateText += self.valueOfNextPredicate(predicateName, i)
						else:
							# It's possibile to have a string that starts with # via the escape character \
							if valueString[0:2] == '\#': # the only valid combination is \#
								outputPredicateText += valueString[1:]
							else:
								outputPredicateText += valueString
					outputPredicateText += predicate.afterSeries

				elif predicate.inSeries == True:
					outputPredicateText += predicate.beforeSeries
					predicateSeriesEnd = False
					j = 0 # predicate series index
					while True:
						for valueString in predicate.valueComposition:
							if valueString == '#':
								# j grows and allows to catch the subsequent predicate values
								value = self.parsedHashFiles[n][i+j].value
								if type(value) is self.SubstringsAndThemPredicates:
									value = self.manageDotSubstrings(i+j)
								outputPredicateText += value
							elif valueString[0] == '#':
								predicateName = valueString[1:]
								outputPredicateText += self.valueOfNextPredicate(predicateName, i)
							else:
								# It's possibile to have a string that starts with # via the escape character \
								if valueString[0:2] == '\#': # the only valid combination is \#
									outputPredicateText += valueString[1:]
								else:
									outputPredicateText += valueString

						while True:
							j += 1
							# If the predicates are finished, break the loop
							# If next predicate is a series stop, break the loop
							if i+j == len(self.parsedHashFiles[n]) or \
								self.isPredicateSeriesStopName(self.parsedHashFiles[n][i+j].name):
								predicateSeriesEnd = True
								break

							if self.processedPredicates[i+j] == 0 and \
								self.parsedHashFiles[n][i+j].name == predicate.name:
								self.processedPredicates[i+j] = 1
								outputPredicateText += "\n"
								break

						if predicateSeriesEnd:
							break

					outputPredicateText += predicate.afterSeries

				outputFileText += outputPredicateText + "\n"

			outputFileText += self.closingText

			# Write an output file
			f = open(self.outputFolder + self.outputFileNames[n], 'w')
			f.write(outputFileText)
			f.close()
			print(self.outputFileNames[n] + ' was generated.')

		print('Operation terminated.')
