import os
import traceback

from csvg_import import cairosvg

input_folder = 'input'
catch = True

for file in os.listdir(input_folder):
	filename, ext = os.path.splitext(file)
	if ext != '.svg':
		continue

	print('\n\n== ' + file + ' ==')
	input_path = os.path.join(input_folder, file)
	output_png = os.path.join('output_png', filename + '.png')
	output_svg = os.path.join('output_svg', filename + '.svg')

	try:
		svg = cairosvg.SVG.read(input_path)
	except:
		if catch:
			print('\nError reading file:')
			traceback.print_exc()
		else:
			raise

	try:
		svg.export(output_png)
	except:
		if catch:
			print('\nError drawing PNG:')
			traceback.print_exc()
		else:
			raise

	try:
		svg.export(output_svg, indent='  ')
	except:
		if catch:
			print('\nError saving SVG:')
			traceback.print_exc()
		else:
			raise
