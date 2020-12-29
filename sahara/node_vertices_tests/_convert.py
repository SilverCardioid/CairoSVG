import glob
import os

image = input('Input image(s): ')
scripts = input('Scripts [ikmsv]: ').lower() or 'ikmsv'
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
		os.system('inkscape --export-png="{}" "{}"'.format(os.path.splitext(image)[0] + '-ink.png', image))

## Kozea/CairoSVG current version
if 'k' in scripts:
	csvg_path = os.path.abspath(repo_base + '../CairoSVG-current/').replace('\\','\\\\')
	img_suffix = 'kozea'
	vertices_suffix = 'kozea-vertices' if 'v' in scripts else ''
	os.system('python _run_test.py "{}" "{}" "{}" "{}"'.format(csvg_path, '|'.join(images), img_suffix, vertices_suffix))

## AgC/CairoSVG master branch
if 'm' in scripts:
	csvg_path = os.path.abspath(repo_base + '../CairoSVG-master/').replace('\\','\\\\')
	img_suffix = 'agc-master'
	vertices_suffix = 'agc-master-vertices' if 'v' in scripts else ''
	os.system('python _run_test.py "{}" "{}" "{}" "{}"'.format(csvg_path, '|'.join(images), img_suffix, vertices_suffix))

## AgC/CairoSVG main branch
if 's' in scripts:
	csvg_path = os.path.abspath(repo_base).replace('\\','\\\\')
	img_suffix = 'agc-main'
	vertices_suffix = ''
	os.system('python _run_test.py "{}" "{}" "{}" "{}"'.format(csvg_path, '|'.join(images), img_suffix, vertices_suffix))
