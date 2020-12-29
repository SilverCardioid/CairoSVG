import os
import sys
import _show_node_vertices

if len(sys.argv) > 1:
	csvg_path = sys.argv[1]
	images = sys.argv[2]
	img_suffix = sys.argv[3]
	vertices_suffix = sys.argv[4]

	sys.path.insert(0, csvg_path)
	import cairosvg
	print('CairoSVG path: ', cairosvg.__path__)

	for image in images.split('|'):
		cairosvg.svg2png(url=image, write_to=os.path.splitext(image)[0] + '-' + img_suffix + '.png')
		if vertices_suffix:
			_show_node_vertices.main(image, os.path.splitext(image)[0] + '-' + vertices_suffix + '.png', cairosvg)