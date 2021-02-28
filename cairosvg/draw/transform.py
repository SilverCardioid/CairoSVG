import cairocffi as cairo
from contextlib import contextmanager
import math
import re

from .. import helpers

class Transform:
	def __init__(self, string=None, *, parent=None):
		self._matrix = cairo.Matrix()
		self._transformed = False
		self.parent = parent
		self.root = parent.root if parent is not None else self
		if string is not None: self(string)

	def __enter__(self):
		if self._transformed:
			self.push()

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self._transformed:
			self.pull()

	def __call__(self, string, *params, transform_origin=None, surface=None):
		surface = surface or self.parent._getSurface()
		if transform_origin:
			if type(transform_origin) is str:
				origin = transform_origin.split(' ')
			if len(origin) == 1:
				origin_x = origin[0]
				if origin_x in ('top', 'bottom'):
					origin_x, origin_y = surface.width/2, origin_x
				else:
					origin_y = surface.height/2
			elif len(origin) > 1:
				origin_x, origin_y = origin[:2]
				if origin_x in ('top', 'bottom'):
					origin_x, origin_y = origin_y, origin_x

			if origin_x == 'center':   origin_x = surface.width/2
			elif origin_x == 'left':   origin_x = 0
			elif origin_x == 'right':  origin_x = surface.width
			else:                      origin_x = helpers.size(surface, origin_x, 'x')

			if origin_y == 'center':   origin_y = surface.height/2
			elif origin_y == 'top':    origin_y = 0
			elif origin_y == 'bottom': origin_y = surface.height
			else:                      origin_y = helpers.size(surface, origin_y, 'y')

			self._matrix.translate(float(origin_x), float(origin_y))

		if len(params):
			# transform('type',values)
			transformations = [(string, params)]
		else:
			# transform('type(values)')
			transformations = re.findall(r'(\w+) ?\( ?(.*?) ?\)', helpers.normalize(string))

		for transformation_type, values in transformations:
			if type(values) is str:
				values = [helpers.size(surface, value) for value in values.split(' ')]

			if transformation_type == 'matrix':      self.matrix(*values)
			elif transformation_type == 'rotate':    self.rotate(*values)
			elif transformation_type == 'skewX':     self.skewX(*values)
			elif transformation_type == 'skewY':     self.skewY(*values)
			elif transformation_type == 'translate': self.translate(*values)
			elif transformation_type == 'scale':     self.scale(*values)

		if transform_origin:
			self._matrix.translate(-float(origin_x), -float(origin_y))

		return self.parent or self

		#try:
		#	self._matrix.invert()
		#except cairo.Error:
		#	# Matrix not invertible, clip the surface to an empty path
		#	active_path = surface.context.copy_path()
		#	surface.context.new_path()
		#	surface.context.clip()
		#	surface.context.append_path(active_path)
		#else:
		#	if gradient:
		#		# When applied on gradient use already inverted matrix (mapping
		#		# from user space to gradient space)
		#		matrix_now = gradient.get_matrix()
		#		gradient.set_matrix(matrix_now.multiply(self._matrix))
		#	else:
		#		self._matrix.invert()
		#		surface.context.transform(self._matrix)

	def apply(self, surface=None):
		surface = surface or self.parent._getSurface()
		surface.context.transform(self._matrix)

	@contextmanager
	def applyContext(self, surface=None):
		surface = surface or self.parent._getSurface()
		if self._transformed:
			self.push(surface)
		try:
			yield self
		finally:
			if self._transformed:
				self.pull(surface)

	def save(self, surface=None):
		surface = surface or self.parent._getSurface()
		surface.context.save()
		self.apply(surface)
	push = save

	def restore(self, surface=None):
		surface = surface or self.parent._getSurface()
		surface.context.restore()
	pull = restore

	def transformPoint(self, x, y):
		return self._matrix.transform_point(x, y)

	def translate(self, tx, ty=0):
		self._matrix.translate(tx, ty)
		self._transformed = True
		return self

	def scale(self, sx, sy=None):
		self._matrix.scale(sx, sy)
		self._transformed = True
		return self

	def rotate(self, angle, cx=0, cy=0):
		self._matrix.translate(cx, cy)
		self._matrix.rotate(math.radians(angle))
		self._matrix.translate(-cx, -cy)
		self._transformed = True
		return self

	def skewX(self, angle):
		self._matrix = cairo.Matrix(1, 0, math.tan(math.radians(angle)), 1, 0, 0) * self._matrix
		self._transformed = True
		return self

	def skewY(self, angle):
		self._matrix = cairo.Matrix(1, math.tan(math.radians(angle)), 0, 1, 0, 0) * self._matrix
		self._transformed = True
		return self

	def matrix(self, xx, yx, xy, yy, x0, y0):
		self._matrix = cairo.Matrix(xx, yx, xy, yy, x0, y0) * self._matrix
		self._transformed = True
		return self
