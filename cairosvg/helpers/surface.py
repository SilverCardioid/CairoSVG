import cairocffi as cairo
from cairocffi import Surface, ImageSurface, PDFSurface, PSSurface, RecordingSurface, SVGSurface
import cv2
import numpy as np

def createSurface(surfaceType, width, height, filename=None, *, x=0, y=0):
	surfaceType = surfaceType.lower()
	if surfaceType in ['image', 'png']:
		surface = ImageSurface(cairo.FORMAT_ARGB32, width, height)
	elif surfaceType == 'pdf':
		surface = PDFSurface(filename, width, height)
	elif surfaceType in ['ps', 'postscript']:
		surface = PSSurface(filename, width, height)
	elif surfaceType == 'recording':
		surface = RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (x, y, width, height))
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

def pixels(surface, alpha=False, bgr=False):
	# based on github.com/Zulko/gizeh
	im = 0 + np.frombuffer(surface.get_data(), np.uint8)
	im.shape = (surface.get_height(), surface.get_width(), 4)
	if not bgr:
		im = im[:,:,[2,1,0,3]]
	if alpha:
		return im
	else:
		return im[:,:,:3]

def show(image, windowName='svg', *, wait=0):
	if isinstance(image, cairo.Surface):
		# Convert surface contents to image
		image = pixels(image, bgr=True)
	cv2.imshow(windowName, image)
	close = False
	waitTime = wait if wait > 0 else 100 # ms
	try:
		while not close:
			key = cv2.waitKey(waitTime)
			if key >= 0 and (key & 0xFF) in [ord('q'), 27] \
			or cv2.getWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN) < 0:
				# Q or Esc key pressed or window manually closed (cv2.WND_PROP_VISIBLE doesn't work correctly)
				close = True
			elif wait > 0:
				# Specified time elapsed
				close = True
		if close:
			cv2.destroyWindow(windowName)
	except cv2.error as e:
		# ignore null pointer exception for already-closed window
		if not (e.code == -27):
			raise
