import glob
import os
import importlib.util
import _show_node_vertices

def import_url(name, url):
	# https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
	spec = importlib.util.spec_from_file_location(name, url)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod

image = input('Input image(s): ')
scripts = input('Scripts [iksv]: ').lower() or 'iksv'
if not image:
	images = glob.glob('*.svg')
else:
	images = image.split('|')
	for i,image in enumerate(images):
		if image[-4:] != '.svg':
			images[i] += '.svg'
	
repo_base = '../../'

## Inkscape
if 'i' in scripts:
	for image in images:
		os.system('inkscape --export-png="' + os.path.splitext(image)[0] + '-ink.png" ' + image + '"')

## CairoSVG master branch (synced with Kozea/CairoSVG)
if 'k' in scripts:
	for image in images:
		cairosvg = import_url('cairosvg', repo_base + '../CairoSVG-kozea/cairosvg/__init__.py')
		out = os.path.splitext(image)[0] + '-kozea.png'
		cairosvg.svg2png(url=image, write_to=out)

## CairoSVG main branch
if 's' in scripts:
	for image in images:
		parse = import_url('cairosvg', repo_base + 'cairosvg/parse/__init__.py')
		out = os.path.splitext(image)[0] + '-agc.png'
		parse.svg2png(url=image, write_to=out)

## CairoSVG, visualise node.vertices
if 'v' in scripts:
	for image in images:
		_show_node_vertices.main(image)
