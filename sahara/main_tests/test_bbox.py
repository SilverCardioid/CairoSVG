from csvg_import import cairosvg

svg = cairosvg.SVG.read('input/bbox.svg')

gShapes = svg.find(lambda e: e.id == 'shapes')[0]
gBoxes = svg.g(id='boxes', fill='none', stroke='#f00', strokeWidth='2')
gVertices = svg.g(id='vertices', fill='#b00')
gExtrema = svg.g(id='extrema', fill='#0a0')
pointR = 4

for e in gShapes.descendants():
	if e.tag == 'g':
		continue
	print(e)

	if e.tag == 'path':
		extr = []
		bx, by, bw, bh = e.boundingBox(extr)
		gBoxes.rect(x=bx, y=by, width=bw, height=bh)
		for vx, vy in e.vertices(include_z=False):
			gVertices.circle(r=pointR, cx=vx, cy=vy)
		for ex, ey in extr:
			gExtrema.circle(r=pointR, cx=ex, cy=ey)

	else:
		bx, by, bw, bh = e.boundingBox()
		gBoxes.rect(x=bx, y=by, width=bw, height=bh)

svg.export('output/test_bbox.svg')
svg.export('output/test_bbox.png')