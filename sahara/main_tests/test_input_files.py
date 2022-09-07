import os

from csvg_import import cairosvg

for file in os.listdir('input'):
	filename, ext = os.path.splitext(file)
	if ext != '.svg':
		continue

	print(file)
	inputPath = os.path.join('input', file)
	outputPNG = os.path.join('output', 'read_' + filename + '.png')
	outputSVG = os.path.join('output', 'read_' + filename + '.svg')

	svg = cairosvg.SVG.read(inputPath)
	svg.export(outputPNG)
	svg.export(outputSVG)
