import cairocffi as cairo
from contextlib import contextmanager
import math
import re
import typing as ty

from ..helpers import attribs, coordinates

class Transform:
	def __init__(self, string:str = None, *, parent:ty.Optional['Element'] = None):
		self.parent = parent
		self._reset()
		if string is not None:
			self._transform(string)

	def _add_to_attr(self, string:str):
		if self.parent:
			val = self.parent._attribs.get('transform', None) or ''
			if val:
				val += ' '
			val += string
			self.parent['transform'] = val

	def _get_origin(self) -> ty.Tuple[float, float]:
		transform_origin = self.parent and self.parent.get_attribute('transform-origin', None) # todo: cascadable or not?
		if transform_origin:
			vp = self.parent and self.parent.get_viewport()
			width, height = vp.inner_size

			if isinstance(transform_origin, str):
				origin = transform_origin.split(' ')
			if len(origin) == 1:
				origin_x = origin[0]
				if origin_x in ('top', 'bottom'):
					origin_x, origin_y = width/2, origin_x
				else:
					origin_y = height/2
			elif len(origin) > 1:
				origin_x, origin_y = origin[:2]
				if origin_x in ('top', 'bottom'):
					origin_x, origin_y = origin_y, origin_x

			if   origin_x == 'center': origin_x = width/2
			elif origin_x == 'left':   origin_x = 0
			elif origin_x == 'right':  origin_x = width
			else:                      origin_x = coordinates.size(origin_x, vp, 'x')

			if   origin_y == 'center': origin_y = height/2
			elif origin_y == 'top':    origin_y = 0
			elif origin_y == 'bottom': origin_y = height
			else:                      origin_y = coordinates.size(origin_y, vp, 'y')

			return (origin_x, origin_y)
		else:
			return (0, 0)

	def __call__(self, string:str, *params:coordinates.Length):
		self._transform(string, *params)
		if self.parent:
			# Append to transform attribute
			trans = string
			if len(params):
				trans += '(' + ','.join(str(v) for v in params) + ')'
			self._add_to_attr(trans)

		return self.parent or self

	def _transform(self, string:str, *params:coordinates.Length):
		if len(params):
			# transform('type',values)
			transformations = [(string, params)]
		else:
			# transform('type(values)')
			transformations = re.findall(r'(\w+) ?\( ?(.*?) ?\)', attribs.normalize(string))

		for transformation_type, values in transformations:
			# Convert string values to numbers
			if isinstance(values, str):
				values = values.split(' ')
			for i, value in enumerate(values):
				if isinstance(value, str):
					values[i] = coordinates.size(value, units=False)

			if transformation_type == 'matrix':      self._matrix(*values)
			elif transformation_type == 'rotate':    self._rotate(*values)
			elif transformation_type == 'skewX':     self._skewX(*values)
			elif transformation_type == 'skewY':     self._skewY(*values)
			elif transformation_type == 'translate': self._translate(*values)
			elif transformation_type == 'scale':     self._scale(*values)

		#try:
		#	self._mat.invert()
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
		#		gradient.set_matrix(matrix_now.multiply(self._mat))
		#	else:
		#		self._mat.invert()
		#		surface.context.transform(self._mat)

	def apply(self, surface:cairo.Surface):
		origin_x, origin_y = self._get_origin()
		surface.context.translate(origin_x, origin_y)
		surface.context.transform(self._mat)
		surface.context.translate(-origin_x, -origin_y)

	@contextmanager
	def apply_context(self, surface:cairo.Surface):
		if self._transformed:
			self.push(surface)
		try:
			yield self
		finally:
			if self._transformed:
				self.pull(surface)

	def save(self, surface:cairo.Surface):
		surface.context.save()
		self.apply(surface)
	push = save

	def restore(self, surface:cairo.Surface):
		surface.context.restore()
	pull = restore

	def transform_point(self, x:float, y:float) -> ty.Tuple[float, float]:
		return self._mat.transform_point(x, y)

	# The public version of each method changes
	# the parent's 'transform' attribute;
	# the private version (with '_') doesn't
	def translate(self, tx:float, ty:float = 0):
		self._translate(tx, ty)
		self._add_to_attr(f'translate({tx},{ty})' if ty != 0 else
		                f'translate({tx})')
		return self
	def _translate(self, tx:float, ty:float = 0):
		self._mat.translate(tx, ty)
		self._transformed = True

	def scale(self, sx:float, sy:ty.Optional[float] = None):
		self._scale(sx, sy)
		self._add_to_attr(f'scale({sx},{sy})' if sy is not None else
		                f'scale({sx})')
		return self
	def _scale(self, sx:float, sy:ty.Optional[float] = None):
		self._mat.scale(sx, sy)
		self._transformed = True

	def rotate(self, angle:float, cx:float = 0, cy:float = 0):
		self._rotate(angle)
		self._add_to_attr(f'rotate({angle},{cx},{cy})' if cx != 0 or cy != 0 else
		                f'rotate({angle})')
		return self
	def _rotate(self, angle:float, cx:float = 0, cy:float = 0):
		self._mat.translate(cx, cy)
		self._mat.rotate(math.radians(angle))
		self._mat.translate(-cx, -cy)
		self._transformed = True

	def skewX(self, angle:float):
		self._skewX(angle)
		self._add_to_attr(f'skewX({angle})')
		return self
	def _skewX(self, angle:float):
		self._mat = cairo.Matrix(1, 0, math.tan(math.radians(angle)),
		                         1, 0, 0) * self._mat
		self._transformed = True

	def skewY(self, angle:float):
		self._skewY(angle)
		self._add_to_attr(f'skewY({angle})')
		return self
	def _skewY(self, angle:float):
		self._mat = cairo.Matrix(1, math.tan(math.radians(angle)), 0,
		                         1, 0, 0) * self._mat
		self._transformed = True

	def matrix(self, xx:float, yx:float, xy:float, yy:float, x0:float, y0:float):
		self._matrix(xx, yx, xy, yy, x0, y0)
		self._add_to_attr(f'matrix({xx},{yx},{xy},{yy},{x0},{y0})')
		return self
	def _matrix(self, xx:float, yx:float, xy:float, yy:float, x0:float, y0:float):
		self._mat = cairo.Matrix(xx, yx, xy, yy, x0, y0) * self._mat
		self._transformed = True

	def reset(self):
		self._reset()
		if self.parent:
			self.parent['transform'] = ''
	def _reset(self):
		self._mat = cairo.Matrix()
		self._transformed = False
