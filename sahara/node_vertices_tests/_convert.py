import os
import importlib.util
import _show_node_vertices

def import_url(name, url):
	# https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
	spec = importlib.util.spec_from_file_location(name, url)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod

image = input('Input image: ')
if image[-4:] != '.svg': image += '.svg'

repo_base = '../../'

## CairoSVG master branch (synced with Kozea/CairoSVG)
cairosvg = import_url('cairosvg', repo_base + '../CairoSVG-kozea/cairosvg/__init__.py')
out = os.path.splitext(image)[0] + '-kozea.png'
cairosvg.svg2png(url=image, write_to=out)

## CairoSVG main branch
parse = import_url('cairosvg', repo_base + 'cairosvg/parse/__init__.py')
out = os.path.splitext(image)[0] + '-agc.png'
parse.svg2png(url=image, write_to=out)

## CairoSVG, visualise node.vertices
_show_node_vertices.main(image)

## Inkscape
os.system('inkscape --export-png="' + os.path.splitext(image)[0] + '-ink.png" ' + image + '"')
