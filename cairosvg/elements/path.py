import math
import typing as ty

from .element import _ShapeElement
from .. import helpers
from ..helpers import types as ht
from ..helpers.coordinates import size as _size, point as _point
from ..helpers.modules import attrib as _attrib

class Path(_ShapeElement):
	"""<path> element.
	A general shape element that defines a series of lines,
	Bezier curves and elliptical arcs.

	Main attributes:
	* d: path data as a string of single-letter commands and coordinates.
	    These correspond to, and can be set with methods in this class.
	* Presentation attributes (e.g., fill, stroke, transform, clip-path).
	"""
	tag = 'path'
	attribs = _ShapeElement.attribs + _attrib['Marker'] + ['d','pathLength','transform']
	_defaults = {**_ShapeElement._defaults,
		'd': ''
	}

	def __init__(self, d_:ty.Optional[str] = None, /, **attribs):
		attribs = helpers.attribs.merge(attribs, d=d_)
		super().__init__(**attribs)

		d = self._getattrib('d')
		self._clear()
		if d and d != 'none':
			self._d(d)

	def __setitem__(self, key:str, value:ty.Any):
		super().__setitem__(key, value)
		if key == 'd':
			self._clear()
			if value and value != 'none':
				self._d(value)

	def __delitem__(self, key:str):
		super().__delitem__(key)
		if key == 'd':
			self._clear()

	def _add(self, letter:str, coords:ty.List[float] = None):
		self._data.append([letter, coords])
		if letter == 'M':
			self._start_point = coords[-2:]
		elif self._start_point is None:
			raise ValueError('Path has not been started with \'M\' or \'m\'')
		self._current_point = coords[-2:] if letter != 'Z' else self._start_point
		self._last_bezier = (letter, *coords[-4:-2]) if letter in 'QC' else None

	def _add_to_attr(self, string:str):
		val = self._attribs.get('d', None) or ''
		val += string
		self['d'] = val

	def _clear(self):
		self._data = []
		self._current_point = None
		self._start_point = None
		self._last_bezier = None

	def _rel2abs(self, x:float, y:float) -> ty.Tuple[float, float]:
		return self._current_point[0] + x, self._current_point[1] + y

	# The public version of each method changes the 'd' attribute;
	# the private version (with '_') doesn't
	def M(self, x:float, y:float):
		"""Moveto: start a new sub-path at (x, y)"""
		self._M(x, y)
		self._add_to_attr(f'M{x},{y}')
		return self
	def _M(self, x:float, y:float):
		self._add('M', [x, y])

	def m(self, x:float, y:float):
		"""Relative moveto: start a new sub-path at (x, y)"""
		self._m(x, y)
		self._add_to_attr(f'm{x},{y}')
		return self
	def _m(self, x:float, y:float):
		if self._start_point is not None:
			x, y = self._rel2abs(x, y)
		self._M(x, y)

	def L(self, x:float, y:float):
		"""Lineto: draw a straight line to (x, y)"""
		self._L(x, y)
		self._add_to_attr(f'L{x},{y}')
		return self
	def _L(self, x:float, y:float):
		self._add('L', [x, y])

	def l(self, x:float, y:float):
		"""Relative lineto: draw a straight line to (x, y)"""
		self._l(x, y)
		self._add_to_attr(f'l{x},{y}')
		return self
	def _l(self, x:float, y:float):
		self._L(*self._rel2abs(x, y))

	def H(self, x:float):
		"""Horizontal lineto: draw a horizontal line to x"""
		self._H(x)
		self._add_to_attr(f'H{x}')
		return self
	def _H(self, x:float):
		self._L(x, self._current_point[1])

	def h(self, x:float):
		"""Relative horizontal lineto: draw a horizontal line to x"""
		self._h(x)
		self._add_to_attr(f'h{x}')
		return self
	def _h(self, x:float):
		self._l(x, 0)

	def V(self, y:float):
		"""Vertical lineto: draw a vertical line to y"""
		self._V(y)
		self._add_to_attr(f'V{y}')
		return self
	def _V(self, y:float):
		self._L(self._current_point[0], y)

	def v(self, y:float):
		"""Relative vertical lineto: draw a vertical line to y"""
		self._v(y)
		self._add_to_attr(f'v{y}')
		return self
	def _v(self, y:float):
		self._l(0, y)

	def A(self, rx:float, ry:float, rot:float, large:bool, sweep:bool,
	      x:float, y:float):
		"""Elliptical arc"""
		self._A(rx, ry, rot, large, sweep, x, y)
		self._add_to_attr(f'A{rx},{ry} {rot} {large},{sweep} {x},{y}')
		return self
	def _A(self, rx:float, ry:float, rot:float, large:bool, sweep:bool,
	       x:float, y:float):
		self._add('A', [rx, ry, rot, large, sweep, x, y])

	def a(self, rx:float, ry:float, rot:float, large:bool, sweep:bool,
	      x:float, y:float):
		"""Relative elliptical arc"""
		self._a(rx, ry, rot, large, sweep, x, y)
		self._add_to_attr(f'a{rx},{ry} {rot} {large},{sweep} {x},{y}')
		return self
	def _a(self, rx:float, ry:float, rot:float, large:bool, sweep:bool,
	       x:float, y:float):
		self._A(rx, ry, rot, large, sweep, *self._rel2abs(x, y))

	def C(self, x1:float, y1:float, x2:float, y2:float, x:float, y:float):
		"""Curveto: cubic Bezier curve"""
		self._C(x1, y1, x2, y2, x, y)
		self._add_to_attr(f'C{x1},{y1} {x2},{y2} {x},{y}')
		return self
	def _C(self, x1:float, y1:float, x2:float, y2:float, x:float, y:float):
		self._add('C', [x1, y1, x2, y2, x, y])

	def c(self, x1:float, y1:float, x2:float, y2:float, x:float, y:float):
		"""Relative curveto: cubic Bezier curve"""
		self._c(x1, y1, x2, y2, x, y)
		self._add_to_attr(f'c{x1},{y1} {x2},{y2} {x},{y}')
		return self
	def _c(self, x1:float, y1:float, x2:float, y2:float, x:float, y:float):
		self._C(*self._rel2abs(x1, y1), *self._rel2abs(x2, y2), *self._rel2abs(x, y))

	def Q(self, x1:float, y1:float, x:float, y:float):
		"""Quadratic Bezier curveto"""
		self._Q(x1, y1, x, y)
		self._add_to_attr(f'Q{x1},{y1} {x},{y}')
		return self
	def _Q(self, x1:float, y1:float, x:float, y:float):
		self._add('Q', [x1, y1, x, y])

	def q(self, x1:float, y1:float, x:float, y:float):
		"""Relative quadratic Bezier curveto"""
		self._q(x1, y1, x, y)
		self._add_to_attr(f'q{x1},{y1} {x},{y}')
		return self
	def _q(self, x1:float, y1:float, x:float, y:float):
		self._Q(*self._rel2abs(x1, y1), *self._rel2abs(x, y))

	def S(self, x2:float, y2:float, x:float, y:float):
		"""Smooth curveto: smooth cubic Bezier curve"""
		self._S(x2, y2, x, y)
		self._add_to_attr(f'S{x2},{y2} {x},{y}')
		return self
	def _S(self, x2:float, y2:float, x:float, y:float):
		x1, y1 = self._current_point
		if self._last_bezier and self._last_bezier[0]=='C':
			xp, yp = self._last_bezier[1:]
			x1, y1 = x1 - (xp - x1), y1 - (yp - y1)
		self._C(x1, y1, x2, y2, x, y)

	def s(self, x2:float, y2:float, x:float, y:float):
		"""Relative smooth curveto: smooth cubic Bezier curve"""
		self._s(x2, y2, x, y)
		self._add_to_attr(f's{x2},{y2} {x},{y}')
		return self
	def _s(self, x2:float, y2:float, x:float, y:float):
		self._S(*self._rel2abs(x2, y2), *self._rel2abs(x, y))

	def T(self, x:float, y:float):
		"""Smooth quadratic Bezier curveto"""
		self._T(x, y)
		self._add_to_attr(f'T{x},{y}')
		return self
	def _T(self, x:float, y:float):
		x1, y1 = self._current_point
		if self._last_bezier and self._last_bezier[0]=='Q':
			xp, yp = self._last_bezier[1:]
			x1, y1 = x1 - (xp - x1), y1 - (yp - y1)
		self._Q(x1, y1, x, y)

	def t(self, x:float, y:float):
		"""Relative smooth quadratic Bezier curveto"""
		self._t(x, y)
		self._add_to_attr(f't{x},{y}')
		return self
	def _t(self, x:float, y:float):
		self._T(*self._rel2abs(x, y))

	def Z(self):
		"""Closepath: draw a straight line to the sub-path's initial point"""
		self._Z()
		self._add_to_attr('z')
		return self
	def _Z(self):
		self._add('Z')
	z = Z

	def polyline(self, points:ty.Sequence[ty.Tuple[float, float]],
	             closed:bool = False):
		"""Add a series of straight lines from an array of (x,y) points."""
		if len(points) > 0:
			self.M(*points[0])
			for p in points[1:]:
				self.L(*p)
			if closed:
				self.z()

	def draw(self, surface:ht.Surface, *, paint:bool = True,
	         viewport:ty.Optional[ht.Viewport] = None):
		with self._apply_transformations(surface):
			start_point = None
			last_point = None
			for command in self._data:
				letter, coords = command
				if letter == 'M':
					surface.context.move_to(*coords)
					start_point = coords[-2:]
				elif letter == 'L':
					surface.context.line_to(*coords)
				elif letter == 'A':
					self._draw_arc(surface, *last_point, *coords)
				elif letter == 'C':
					surface.context.curve_to(*coords)
				elif letter == 'Q':
					cubic_coords = helpers.geometry.quadratic_points(*last_point, *coords)
					surface.context.curve_to(*cubic_coords)
				elif letter == 'Z':
					surface.context.close_path()
				else:
					raise ValueError('Unknown letter: ' + letter)
				last_point = coords[-2:] if letter != 'Z' else start_point

			if paint:
				self._paint(surface, viewport=viewport)

	def _draw_arc(self, surface:ht.Surface, x1:float, y1:float,
	              rx:float, ry:float, rotation:float,
	              large:bool, sweep:bool, x3:float, y3:float):
		surface.context.set_tolerance(0.00001)
		# rx=0 or ry=0 means straight line
		if not rx or not ry:
			surface.context.line_to(x3, y3)
			return

		arc = helpers.geometry.Arc(
			rx, ry, rotation, large, sweep, x3 - x1, y3 - y1)
		arc_fun = (surface.context.arc if arc.sweep else
		           surface.context.arc_negative)

		surface.context.save()
		surface.context.translate(x1, y1)
		surface.context.rotate(arc.rotation)
		surface.context.scale(1, arc.radii_ratio)
		arc_fun(*arc.draw_center, arc.rx, *arc.draw_angles)
		surface.context.restore()

	def vertices(self, close:bool = True) -> ht.VertexList:
		"""Get the vertices of the path as a list of (x,y) tuples.
		If `close` is True, repeat the initial vertex of closed sub-paths
		at the end.
		"""
		v = []
		last_m = None
		for letter, coords in self._data:
			if letter != 'Z':
				# M, L, A, C, Q: add coordinate
				v.append(tuple(coords[-2:]))
				if letter == 'M':
					last_m = tuple(coords[-2:])
			elif close:
				v.append(last_m)
		return v

	def vertex_angles(self) -> ty.List[float]:
		"""Get the marker angles at every vertex.
		Each angle is in radians, and is the average of the direction of the
		two adjoining line segments at that vertex.
		"""
		segment_angles = []
		#index = 0
		vertex = None
		last_vertex = (0, 0) # in case of no M
		last_m = (0, 0)
		last_letter = None

		for command in self._data:
			letter, coords = command

			if letter == 'M':
				if segment_angles and last_letter != 'Z': # Mark last path unclosed
					segment_angles[-1].append(None)
				vertex = coords[-2:]
				last_m = vertex
				segment_angles.append([])

			elif letter == 'L':
				vertex = coords[-2:]
				angle = helpers.geometry.point_angle(*last_vertex, *vertex)
				segment_angles[-1].append((angle, angle))

			elif letter == 'A':
				vertex = coords[-2:]
				rx, ry, rotation, large, sweep, xe, ye = coords
				xe -= last_vertex[0]
				ye -= last_vertex[1]
				rotation = math.radians(rotation)
				if not rx or not ry:
					# rx=0 or ry=0 means straight line
					angle = helpers.geometry.point_angle(*last_vertex, *vertex)
					segment_angles[-1].append((angle, angle))
				else:
					arc = helpers.geometry.Arc(rx, ry, rotation, large, sweep, xe, ye)
					angle1, angle2 = arc.draw_angles
					tangent1 = angle1 + (math.pi/2 if arc.sweep else -math.pi/2)
					tangent2 = angle2 + (math.pi/2 if arc.sweep else -math.pi/2)
					if arc.radii_ratio != 1:
						tangent1 = math.atan2(arc.radii_ratio*math.sin(tangent1),
						                      math.cos(tangent1))
						tangent2 = math.atan2(arc.radii_ratio*math.sin(tangent2),
						                      math.cos(tangent2))
					segment_angles[-1].append((tangent1 + arc.rotation,
					                           tangent2 + arc.rotation))

			elif letter == 'C':
				vertex = coords[-2:]
				segment_angles[-1].append(helpers.bezier_angles(
					last_vertex, coords[0:2], coords[2:4], vertex))

			elif letter == 'Q':
				vertex = coords[-2:]
				segment_angles[-1].append(helpers.bezier_angles(
					last_vertex, coords[0:2], vertex))

			elif letter == 'Z':
				vertex = last_m
				angle = helpers.geometry.point_angle(*last_vertex, *vertex)
				segment_angles[-1].append((angle, angle))

			last_vertex = vertex
			last_letter = letter

		if last_letter != 'Z': # Mark last path unclosed
			segment_angles[-1].append(None)

		# Calculate vertex angles from adjoining segments
		vertex_angles = []
		for subpath in segment_angles:
			angle_out, angle_in = None, None

			if subpath and subpath[-1] is not None:
				# Closed subpath: assign final angle to average with initial angle &
				# append copy of first angle at the end
				angle_in = subpath[-1][1]
				subpath += [subpath[0]]

			for angles in subpath:
				if angles:
					angle_out = angles[0]
					if angle_in is None:
						# Start of unclosed subpath
						vertex_angles.append(angle_out)
					else:
						# Two adjoining segments: bisect the angle difference
						# by summing the corresponding unit vectors
						vertex_angles.append(math.atan2(
							math.sin(angle_out) + math.sin(angle_in),
							math.cos(angle_out) + math.cos(angle_in)))
					angle_in = angles[1]
				else: # End of unclosed subpath
					vertex_angles.append(angle_in)
		return vertex_angles

	def bounding_box(self, *, with_transform:bool = True,
	                 _ex:ty.Optional[ht.VertexList] = None) -> ht.Box:
		box = helpers.geometry.Box()
		last_vertex = (0, 0) # in case of no M
		last_m = (0, 0)
		for command in self._data:
			letter, coords = command
			x0, y0 = last_vertex

			if letter == 'Z':
				last_vertex = last_m
				continue

			if letter == 'M':
				last_m = coords

			if letter == 'C':
				x1, y1, x2, y2, x3, y3 = coords
				x_extrema = helpers.geometry.cubic_extrema(x0, x1, x2, x3)
				y_extrema = helpers.geometry.cubic_extrema(y0, y1, y2, y3)
				for t, x in x_extrema:
					y = helpers.geometry.evaluate_cubic(t, y0, y1, y2, y3)
					box.add_point(x, y)
					if _ex is not None:
						_ex.append((x, y))
				for t, y in y_extrema:
					x = helpers.geometry.evaluate_cubic(t, x0, x1, x2, x3)
					box.add_point(x, y)
					if _ex is not None:
						_ex.append((x, y))

			if letter == 'Q':
				x1, y1, x2, y2 = coords
				x_extrema = helpers.geometry.quadratic_extrema(x0, x1, x2)
				y_extrema = helpers.geometry.quadratic_extrema(y0, y1, y2)
				for t, x in x_extrema:
					y = helpers.geometry.evaluate_quadratic(t, y0, y1, y2)
					box.add_point(x, y)
					if _ex is not None:
						_ex.append((x, y))
				for t, y in y_extrema:
					x = helpers.geometry.evaluate_quadratic(t, x0, x1, x2)
					box.add_point(x, y)
					if _ex is not None:
						_ex.append((x, y))

			if letter == 'A':
				rx, ry, rotation, large, sweep, x1, y1 = coords
				if rx and ry:
					arc = helpers.geometry.Arc(rx, ry, rotation, large, sweep,
					                           x1 - x0, y1 - y0)
					extrema = arc.extrema()
					for angle, (x, y) in extrema:
						x += x0; y += y0
						box.add_point(x, y)
						if _ex is not None:
							_ex.append((x, y))

			new_x, new_y = coords[-2:]
			box.add_point(new_x, new_y)
			last_vertex = (new_x, new_y)

		if with_transform: box = self._transform_box(box)
		return box

	def d(self, d:str):
		"""Append path data from a string."""
		self._d(d)
		self._add_to_attr(d)
		return self

	def _d(self, d:str):
		string = d
		for letter in helpers.PATH_LETTERS:
			string = string.replace(letter, ' {} '.format(letter))
		string = helpers.attribs.normalize(string)

		while string:
			string = string.strip()
			if string.split(' ', 1)[0] in helpers.PATH_LETTERS:
				letter, string = (string + ' ').split(' ', 1)
			elif letter == 'M':
				letter = 'L'
			elif letter == 'm':
				letter = 'l'

			if letter in 'aA':
				# Elliptic curve
				rx, ry, string = _point(string, units=False)
				rotation, string = string.split(' ', 1)
				rotation = _size(rotation, units=False)

				# The large and sweep values are not always separated from the
				# following values. These flags can only be 0 or 1, so reading a
				# single digit suffices.
				large, string = string[0], string[1:].strip()
				sweep, string = string[0], string[1:].strip()

				# Retrieve end point and set remainder (before checking flags)
				x3, y3, string = _point(string, units=False)

				# Only allow 0 or 1 for flags
				large, sweep = int(large), int(sweep)
				if large not in (0, 1) or sweep not in (0, 1):
						continue
				large, sweep = bool(large), bool(sweep)

				# rx=0 or ry=0 means straight line
				if not rx or not ry:
					self._l(x3, y3)
					continue
				elif letter == 'A':
					self._A(rx, ry, rotation, large, sweep, x3, y3)
				else:
					self._a(rx, ry, rotation, large, sweep, x3, y3)

			elif letter == 'c':
				# Relative curve
				x1, y1, string = _point(string, units=False)
				x2, y2, string = _point(string, units=False)
				x3, y3, string = _point(string, units=False)
				self._c(x1, y1, x2, y2, x3, y3)

			elif letter == 'C':
				# Curve
				x1, y1, string = _point(string, units=False)
				x2, y2, string = _point(string, units=False)
				x3, y3, string = _point(string, units=False)
				self._C(x1, y1, x2, y2, x3, y3)

			elif letter == 'h':
				# Relative horizontal line
				x, string = (string + ' ').split(' ', 1)
				x = _size(x, units=False)
				self._h(x)

			elif letter == 'H':
				# Horizontal line
				x, string = (string + ' ').split(' ', 1)
				x = _size(x, units=False)
				self._H(x)

			elif letter == 'l':
				# Relative straight line
				x, y, string = _point(string, units=False)
				self._l(x, y)

			elif letter == 'L':
				# Straight line
				x, y, string = _point(string, units=False)
				self._L(x, y)

			elif letter == 'm':
				# Current point relative move
				x, y, string = _point(string, units=False)
				self._m(x, y)

			elif letter == 'M':
				# Current point move
				x, y, string = _point(string, units=False)
				self._M(x, y)

			elif letter == 'q':
				# Relative quadratic curve
				x1, y1 = 0, 0
				x2, y2, string = _point(string, units=False)
				x3, y3, string = _point(string, units=False)
				self._q(x2, y2, x3, y3)

			elif letter == 'Q':
				# Quadratic curve
				x2, y2, string = _point(string, units=False)
				x3, y3, string = _point(string, units=False)
				self._Q(x2, y2, x3, y3)

			elif letter == 's':
				# Relative smooth curve
				x2, y2, string = _point(string, units=False)
				x3, y3, string = _point(string, units=False)
				self._s(x2, y2, x3, y3)

			elif letter == 'S':
				# Smooth curve
				x2, y2, string = _point(string, units=False)
				x3, y3, string = _point(string, units=False)
				self._S(x2, y2, x3, y3)

			elif letter == 't':
				# Relative quadratic curve end
				x3, y3, string = _point(string, units=False)
				self._t(x3, y3)

			elif letter == 'T':
				# Quadratic curve end
				x3, y3, string = _point(string, units=False)
				self._T(x3, y3)

			elif letter == 'v':
				# Relative vertical line
				y, string = (string + ' ').split(' ', 1)
				y = _size(y, units=False)
				self._v(y)

			elif letter == 'V':
				# Vertical line
				y, string = (string + ' ').split(' ', 1)
				y = _size(y, units=False)
				self._V(y)

			elif letter in 'zZ':
				# End of path
				self._Z()

			string = string.strip()

