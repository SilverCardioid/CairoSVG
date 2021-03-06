import math
import os
import sys
import xml.etree.ElementTree as ET
import cairocffi as cairo

bgColour = [1, 1, 1]
dotColour = [0, 0, 0]
angleInColour = [0.6, 0, 1]
angleOutColour = [0, 0.7, 0]

def main(image, outName=None, cairosvg=None):
	if not cairosvg:
		import cairosvg
	if not outName:
		outName = os.path.splitext(image)[0] + '-vertices.png'

	## Parse SVG
	svg = ET.parse(image).getroot()
	paths = svg.findall('{http://www.w3.org/2000/svg}path')

	## Create cairo surface & run cairosvg.path
	width = int(svg.attrib.get('width', 600))
	height = int(svg.attrib.get('height', 600))
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
	context = cairo.Context(surface)
	with context: # white background
		context.set_source_rgb(*bgColour)
		context.paint()

	for path in paths:
		node = NodeSurface(cairosvg, surface, context, path.attrib['d'])
		lineColour = list(cairosvg.colors.color(path.attrib.get('stroke', '#000')))
		lineColour[3] /= 2 # reduce opacity
		context.set_source_rgba(*lineColour)
		strokeWidth = float(path.attrib.get('stroke-width', 1))
		context.set_line_width(strokeWidth)
		cairosvg.path.path(node, node)
		context.stroke()

		## Display node.vertices
		subpaths = node.vertices
		if type(subpaths[0][0]) not in [list, tuple]:
			subpaths = [subpaths]
		for subpath in subpaths:
			vertices = subpath.copy()
			prev_angles = vertices[-1] if len(vertices) % 2 == 0 else None
			while len(vertices) > 0:
				point = vertices.pop(0)
				angles = vertices.pop(0) if len(vertices) > 0 else None
				angleIn = prev_angles[1] if prev_angles is not None else None
				angleOut = angles[0] if angles is not None else None
				showVertex(context, point, angleIn, angleOut, strokeWidth)
				prev_angles = angles

	surface.write_to_png(outName)


class NodeSurface: # imitates cairosvg.Node and cairosvg.Surface
	def __init__(self, cairosvg, surface, context, string):
		self.context = context
		self.context_width = surface.get_width()
		self.context_height = surface.get_height()
		self.dpi = 96
		self.font_size = cairosvg.helpers.size(self, '12pt')
		self.d = string
	def get(self,key,default=None):
		return getattr(self,key,default)


def showVertex(ctx, point, angleIn, angleOut, relSize=1, radius=0.8):
	ctx.save()
	ctx.translate(*point)
	ctx.set_line_width(1)
	## Angle indicators
	if angleIn is not None:
		drawArrow(ctx, angleIn, relSize)
		ctx.set_source_rgb(*angleInColour); ctx.fill_preserve()
		ctx.set_source_rgb(*bgColour); ctx.stroke()
	if angleOut is not None:
		drawArrow(ctx, angleOut, relSize)
		ctx.set_source_rgb(*angleOutColour); ctx.fill_preserve()
		ctx.set_source_rgb(*bgColour); ctx.stroke()
		# Redraw 'in' at half opacity to blend the two arrows if they overlap
		if angleIn is not None:
			drawArrow(ctx, angleIn, relSize)
			ctx.set_source_rgba(*angleInColour, 0.5); ctx.fill_preserve()
			ctx.set_source_rgb(*bgColour); ctx.stroke()
	## Vertex
	ctx.move_to(relSize*radius, 0)
	ctx.arc(0, 0, relSize*radius, 0, 2*math.pi)
	ctx.set_source_rgb(*dotColour); ctx.fill_preserve()
	ctx.set_source_rgb(*bgColour); ctx.stroke()
	
	ctx.restore()


def drawArrow(ctx, angle, relSize=1, xApex=4, xBase=2, xEnd=0, headWidth=3, stemWidth=1):
	ctx.save()
	ctx.rotate(angle)
	ctx.move_to(relSize*xApex, 0)
	ctx.line_to(relSize*xBase, relSize*headWidth/2)
	ctx.line_to(relSize*xBase, relSize*stemWidth/2)
	ctx.line_to(relSize*xEnd, relSize*stemWidth/2)
	ctx.line_to(relSize*xEnd, -relSize*stemWidth/2)
	ctx.line_to(relSize*xBase, -relSize*stemWidth/2)
	ctx.line_to(relSize*xBase, -relSize*headWidth/2)
	ctx.close_path()
	ctx.restore()


if __name__ == '__main__':
	image = input('Input image: ')
	if image[-4:] != '.svg': image += '.svg'
	main(image)