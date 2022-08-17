import cairocffi as cairo
from cairocffi import ImageSurface, PDFSurface, PSSurface, RecordingSurface, SVGSurface

def createSurface(surfaceType, width, height, filename=None):
	surfaceType = surfaceType.lower()
	if surfaceType in ['image', 'png']:
		surface = ImageSurface(cairo.FORMAT_ARGB32, width, height)
	elif surfaceType == 'pdf':
		surface = PDFSurface(filename, width, height)
	elif surfaceType in ['ps', 'postscript']:
		surface = PSSurface(filename, width, height)
	elif surfaceType == 'recording':
		surface = RecordingSurface(filename, (0, 0, width, height))
	elif surfaceType == 'svg':
		surface = SVGSurface(filename, width, height)
	else:
		raise ValueError('Unsupported surface type: {}'.format(surfaceType))
	surface.context = cairo.Context(surface)
	return surface

def clearSurface(surface):
	surface.context.set_operator(cairo.OPERATOR_CLEAR)
	surface.context.paint()
	surface.context.set_operator(cairo.OPERATOR_OVER)
