import typing as ty

import cairocffi as cairo
from cairocffi import (
	Surface, ImageSurface, PDFSurface, PSSurface,
	RecordingSurface, SVGSurface)
import cv2
import numpy as np

def create_surface(surface_type:str, width:int, height:int,
                   filename:ty.Optional[str] = None, *, x:int = 0, y:int = 0
	               ) -> Surface:
	surface_type = surface_type.lower()
	if surface_type in ['image', 'png']:
		surface = ImageSurface(cairo.FORMAT_ARGB32, width, height)
	elif surface_type == 'pdf':
		surface = PDFSurface(filename, width, height)
	elif surface_type in ['ps', 'postscript']:
		surface = PSSurface(filename, width, height)
	elif surface_type == 'recording':
		surface = RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (x, y, width, height))
	elif surface_type == 'svg':
		surface = SVGSurface(filename, width, height)
	else:
		raise ValueError(f'Unsupported surface type: {surface_type}')
	surface.context = cairo.Context(surface)
	return surface

def copy(surface:Surface, new_type:str) -> Surface:
	new_surface = create_surface(new_type, surface.width, surface.height)
	new_context = cairo.Context(new_surface)
	new_context.set_source_surface(surface, 0, 0)
	new_context.paint()
	return new_surface

def clear_surface(surface:Surface):
	surface.context.set_operator(cairo.OPERATOR_CLEAR)
	surface.context.paint()
	surface.context.set_operator(cairo.OPERATOR_OVER)

def pixels(surface:Surface, alpha:bool = False, bgr:bool = False
           ) -> np.ndarray:
	# based on github.com/Zulko/gizeh
	im = 0 + np.frombuffer(surface.get_data(), np.uint8)
	im.shape = (surface.get_height(), surface.get_width(), 4)
	if not bgr:
		im = im[:,:,[2,1,0,3]]
	if alpha:
		return im
	else:
		return im[:,:,:3]

def show(image:ty.Union[np.ndarray, cairo.Surface], window_name:str = 'svg', *, wait:int = 0):
	if isinstance(image, cairo.Surface):
		# Convert surface contents to image
		if not hasattr(image, 'get_data'):
			image = copy(image, 'image')
		image = pixels(image, bgr=True)

	cv2.imshow(window_name, image)
	close = False
	wait_time = wait if wait > 0 else 100 # ms
	try:
		while not close:
			key = cv2.waitKey(wait_time)
			if key >= 0 and (key & 0xFF) in [ord('q'), 27] \
			or cv2.getWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN) < 0:
				# Q or Esc key pressed or window manually closed (cv2.WND_PROP_VISIBLE doesn't work correctly)
				close = True
			elif wait > 0:
				# Specified time elapsed
				close = True
		if close:
			cv2.destroyWindow(window_name)
	except cv2.error as e:
		# ignore null pointer exception for already-closed window
		if not (e.code == -27):
			raise
