#!/usr/bin/python
# Script to detect all model scripts and run them #

from os import listdir
from os.path import isfile
from sys import path as pyPath
import subprocess

class ModelScripts:
	folder = pyPath[0] + '/'
	fileNames = []

	def detect(self):
		self.fileNames = [fileName for fileName in listdir(self.folder) \
			if (fileName.endswith('.model.py') and isfile(self.folder + fileName))]

		scriptCount = len(self.fileNames)

		if scriptCount == 1:
			print('Found 1 model script.')
		else:
			print('Found ' + str(scriptCount) + ' model scripts.')


	def run(self):
		someExecution = False

		for fileName in self.fileNames:
			print(fileName + " launched.")
			subprocess.call([self.folder + fileName])
			someExecution = True

		if someExecution == False:
			print('Nothing to perform.')


modelScripts = ModelScripts()
modelScripts.detect()
modelScripts.run()
