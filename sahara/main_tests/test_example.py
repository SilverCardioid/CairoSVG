import math

from csvg_import import cairosvg
SVG = cairosvg.SVG

# Create an SVG object
svg = SVG(width=600, height=600)

# ...or load a file using
# svg = SVG.read('filename.svg')

# Add elements
svg.rect(width=600, height=600, fill='#fff')

g = svg.g()
g.transform.translate(300, 300)
g.circle(r=120, fill='#000')

path = g.path(fill='#fc0')
path.M(0, -100)
for i in range(1, 5):
	path.L(100*math.sin(i*4*math.pi/5), -100*math.cos(i*4*math.pi/5))
path.z()

# Display and save the image
svg.show()
svg.export('output/test_example.svg')
svg.export('output/test_example.png')
