import math

from .element import _ShapeElement
from .. import helpers
from ..helpers.modules import attrib as _attrib

class Path(_ShapeElement):
	attribs = _ShapeElement.attribs + _attrib['Marker'] + ['d','pathLength','transform']

	def __init__(self, d=helpers._strdef(''), **attribs):
		self.tag = 'path'
		super().__init__(d=d, **attribs)
		self._clear()
		if d is not None:
			self._d(d)

	def __setitem__(self, key, value):
		super().__setitem__(key, value)
		if key == 'd':
			self._clear()
			self._d(self['d'])

	def __delitem__(self, key):
		super().__delitem__(key)
		if key == 'd':
			self._clear()

	def _add(self, letter, coords=None):
		self._data.append([letter, coords])
		if letter == 'M':
			self._startPoint = coords[-2:]
		elif self._startPoint is None:
			raise ValueError('Path has not been started with \'M\' or \'m\'')
		self._currentPoint = coords[-2:] if letter != 'Z' else self._startPoint
		self._lastBezier = (letter, *coords[-4:-2]) if letter in 'QC' else None

	def _addToAttr(self, string):
		val = self._attribs.get('d', None) or ''
		val += string
		self['d'] = val

	def _clear(self):
		self._data = []
		self._currentPoint = None
		self._startPoint = None
		self._lastBezier = None

	def _rel2abs(self, x, y):
		return self._currentPoint[0] + x, self._currentPoint[1] + y

	# The public version of each method changes the 'd' attribute;
	# the private version (with '_') doesn't
	def M(self, x, y):
		"""Moveto: start a new sub-path at (x, y)"""
		self._M(x, y)
		self._addToAttr(f'M{x},{y}')
		return self
	def _M(self, x, y):
		self._add('M', [x, y])

	def m(self, x, y):
		"""Relative moveto: start a new sub-path at (x, y)"""
		self._m(x, y)
		self._addToAttr(f'm{x},{y}')
		return self
	def _m(self, x, y):
		if self._startPoint is not None:
			x, y = self._rel2abs(x, y)
		self._M(x, y)

	def L(self, x, y):
		"""Lineto: draw a straight line to (x, y)"""
		self._L(x, y)
		self._addToAttr(f'L{x},{y}')
		return self
	def _L(self, x, y):
		self._add('L', [x, y])

	def l(self, x, y):
		"""Relative lineto: draw a straight line to (x, y)"""
		self._l(x, y)
		self._addToAttr(f'l{x},{y}')
		return self
	def _l(self, x, y):
		self._L(*self._rel2abs(x, y))

	def H(self, x):
		"""Horizontal lineto: draw a horizontal line to x"""
		self._H(x)
		self._addToAttr(f'H{x}')
		return self
	def _H(self, x):
		self._L(x, self._currentPoint[1])

	def h(self, x):
		"""Relative horizontal lineto: draw a horizontal line to x"""
		self._h(x)
		self._addToAttr(f'h{x}')
		return self
	def _h(self, x):
		self._l(x, 0)

	def V(self, y):
		"""Vertical lineto: draw a vertical line to y"""
		self._V(y)
		self._addToAttr(f'V{y}')
		return self
	def _V(self, y):
		self._L(self._currentPoint[0], y)

	def v(self, y):
		"""Relative vertical lineto: draw a vertical line to y"""
		self._v(y)
		self._addToAttr(f'v{y}')
		return self
	def _v(self, y):
		self._l(0, y)

	def A(self, rx, ry, rot, large, sweep, x, y):
		"""Elliptical arc"""
		self._A(rx, ry, rot, large, sweep, x, y)
		self._addToAttr(f'A{rx},{ry} {rot} {large},{sweep} {x},{y}')
		return self
	def _A(self, rx, ry, rot, large, sweep, x, y):
		self._add('A', [rx, ry, rot, large, sweep, x, y])

	def a(self, rx, ry, rot, large, sweep, x, y):
		"""Relative elliptical arc"""
		self._a(rx, ry, rot, large, sweep, x, y)
		self._addToAttr(f'a{rx},{ry} {rot} {large},{sweep} {x},{y}')
		return self
	def _a(self, rx, ry, rot, large, sweep, x, y):
		self._A(rx, ry, rot, large, sweep, *self._rel2abs(x, y))

	def C(self, x1, y1, x2, y2, x, y):
		"""Curveto: cubic Bezier curve"""
		self._C(x1, y1, x2, y2, x, y)
		self._addToAttr(f'C{x1},{y1} {x2},{y2} {x},{y}')
		return self
	def _C(self, x1, y1, x2, y2, x, y):
		self._add('C', [x1, y1, x2, y2, x, y])

	def c(self, x1, y1, x2, y2, x, y):
		"""Relative curveto: cubic Bezier curve"""
		self._c(x1, y1, x2, y2, x, y)
		self._addToAttr(f'c{x1},{y1} {x2},{y2} {x},{y}')
		return self
	def _c(self, x1, y1, x2, y2, x, y):
		self._C(*self._rel2abs(x1, y1), *self._rel2abs(x2, y2), *self._rel2abs(x, y))

	def Q(self, x1, y1, x, y):
		"""Quadratic Bezier curveto"""
		self._Q(x1, y1, x, y)
		self._addToAttr(f'Q{x1},{y1} {x},{y}')
		return self
	def _Q(self, x1, y1, x, y):
		self._add('Q', [x1, y1, x, y])

	def q(self, x1, y1, x, y):
		"""Relative quadratic Bezier curveto"""
		self._q(x1, y1, x, y)
		self._addToAttr(f'q{x1},{y1} {x},{y}')
		return self
	def _q(self, x1, y1, x, y):
		self._Q(*self._rel2abs(x1, y1), *self._rel2abs(x, y))

	def S(self, x2, y2, x, y):
		"""Smooth curveto: smooth cubic Bezier curve"""
		self._S(x2, y2, x, y)
		self._addToAttr(f'S{x2},{y2} {x},{y}')
		return self
	def _S(self, x2, y2, x, y):
		x1, y1 = self._currentPoint
		if self._lastBezier and self._lastBezier[0]=='C':
			xp, yp = self._lastBezier[1:]
			x1, y1 = x1 - (xp - x1), y1 - (yp - y1)
		self._C(x1, y1, x2, y2, x, y)

	def s(self, x2, y2, x, y):
		"""Relative smooth curveto: smooth cubic Bezier curve"""
		self._s(x2, y2, x, y)
		self._addToAttr(f's{x2},{y2} {x},{y}')
		return self
	def _s(self, x2, y2, x, y):
		self._S(*self._rel2abs(x2, y2), *self._rel2abs(x, y))

	def T(self, x, y):
		"Smooth quadratic Bezier curveto"
		self._T(x, y)
		self._addToAttr(f'T{x},{y}')
		return self
	def _T(self, x, y):
		x1, y1 = self._currentPoint
		if self._lastBezier and self._lastBezier[0]=='Q':
			xp, yp = self._lastBezier[1:]
			x1, y1 = x1 - (xp - x1), y1 - (yp - y1)
		self._Q(x1, y1, x, y)

	def t(self, x, y):
		"Relative smooth quadratic Bezier curveto"
		self._t(x, y)
		self._addToAttr(f't{x},{y}')
		return self
	def _t(self, x, y):
		self._T(*self._rel2abs(x, y))

	def Z(self):
		"Closepath: draw a straight line to the sub-path's initial point"
		self._Z()
		self._addToAttr('z')
		return self
	def _Z(self):
		self._add('Z')
	z = Z

	def polyline(self, points, closed=False):
		"""Add a series of straight lines from an array of [x,y] points"""
		if len(points) > 0:
			self.M(*points[0])
			for p in points[1:]:
				self.L(*p)
			if closed:
				self.z()

	def draw(self, surface=None):
		surface = surface or self._getSurface()
		with self.transform.applyContext(surface):
			startPoint = None
			lastPoint = None
			for command in self._data:
				letter, coords = command
				if letter == 'M':
					surface.context.move_to(*coords)
					startPoint = coords[-2:]
				elif letter == 'L':
					surface.context.line_to(*coords)
				elif letter == 'A':
					self._drawArc(surface, *lastPoint, *coords)
				elif letter == 'C':
					surface.context.curve_to(*coords)
				elif letter == 'Q':
					cubicCoords = helpers.quadratic_points(*lastPoint, *coords)
					surface.context.curve_to(*cubicCoords)
				elif letter == 'Z':
					surface.context.close_path()
				else:
					raise ValueError('Unknown letter: ' + letter)
				lastPoint = coords[-2:] if letter != 'Z' else startPoint

			self._paint(surface)

	def _drawArc(self, surface, x1, y1, rx, ry, rotation, large, sweep, x3, y3):
		surface.context.set_tolerance(0.00001)
		rotation = helpers.radians(float(rotation))
		# rx=0 or ry=0 means straight line
		if not rx or not ry:
			surface.context.line_to(x3, y3)
			return
		# Absolute x3 and y3, convert to relative
		x3 -= x1
		y3 -= y1
		radii_ratio = ry / rx
		# Cancel the rotation of the second point
		xe, ye = helpers.rotate(x3, y3, -rotation)
		ye /= radii_ratio
		# Find the angle between the second point and the x axis
		angle = helpers.point_angle(0, 0, xe, ye)
		# Put the second point onto the x axis
		xe = (xe ** 2 + ye ** 2) ** .5
		ye = 0
		# Update the x radius if it is too small
		rx = max(rx, xe / 2)
		# Find one circle centre
		xc = xe / 2
		yc = (rx ** 2 - xc ** 2) ** .5
		# Choose between the two circles according to flags
		if not (large ^ sweep):
				yc = -yc
		# Define the arc sweep
		arc = (surface.context.arc if sweep else surface.context.arc_negative)
		# Put the second point and the center back to their positions
		xe, ye = helpers.rotate(xe, 0, angle)
		xc, yc = helpers.rotate(xc, yc, angle)
		# Find the drawing angles
		angle1 = helpers.point_angle(xc, yc, 0, 0)
		angle2 = helpers.point_angle(xc, yc, xe, ye)
		# Draw the arc
		surface.context.save()
		surface.context.translate(x1, y1)
		surface.context.rotate(rotation)
		surface.context.scale(1, radii_ratio)
		arc(xc, yc, rx, angle1, angle2)
		surface.context.restore()

	def vertices(self, include_z=True):
		"""Get the vertices of the path as a list of [x,y] arrays"""
		v = []
		lastM = None
		for letter, coords in self._data:
			if letter != 'Z':
				# M, L, A, C, Q: add coordinate
				v.append(coords[-2:])
				if letter == 'M':
					lastM = coords[-2:]
			elif include_z:
				v.append(lastM)
		return v

	def vertexAngles(self):
		"""Get the marker angles at every vertex"""
		segmentAngles = []
		#index = 0
		vertex = None
		lastVertex = (0, 0) # in case of no M
		lastM = None
		#lastMIndex = None
		lastLetter = None

		for command in self._data: #index, command in enumerate(self._data):
			letter, coords = command

			if letter == 'M':
				if segmentAngles and lastLetter != 'Z': # Mark last path unclosed
					segmentAngles[-1].append(None)
				vertex = coords[-2:]
				lastM = vertex
				#lastMIndex = index
				segmentAngles.append([])

			elif letter == 'L':
				vertex = coords[-2:]
				angle = helpers.point_angle(*lastVertex, *vertex)
				segmentAngles[-1].append((angle, angle))

			elif letter == 'A':
				vertex = coords[-2:]
				rx, ry, rotation, large, sweep, xe, ye = coords
				xe -= lastVertex[0]
				ye -= lastVertex[1]
				rotation = math.radians(rotation)
				if not rx or not ry:
					# rx=0 or ry=0 means straight line
					angle = helpers.point_angle(*lastVertex, *vertex)
					segmentAngles[-1].append((angle, angle))
				else:
					# Cancel the rotation of the second point
					radii_ratio = ry / rx
					xe, ye = helpers.rotate(xe, ye, -rotation)
					ye /= radii_ratio
					# Put the second point onto the x axis
					angle = helpers.point_angle(0, 0, xe, ye)
					xe, ye = (xe ** 2 + ye ** 2) ** .5, 0
					rx = max(rx, xe / 2)
					# Find circle centre
					xc = xe / 2
					yc = (rx ** 2 - xc ** 2) ** .5
					if not (large ^ sweep): yc = -yc
					# Put the second point and the center back to their positions
					xe, ye = helpers.rotate(xe, 0, angle)
					xc, yc = helpers.rotate(xc, yc, angle)
					# Find the drawing angles
					angle1 = helpers.point_angle(xc, yc, 0, 0)
					angle2 = helpers.point_angle(xc, yc, xe, ye)
					tangent1 = angle1 + (math.pi/2 if sweep else -math.pi/2)
					tangent2 = angle2 + (math.pi/2 if sweep else -math.pi/2)
					if radii_ratio != 1:
						tangent1 = math.atan2(radii_ratio*math.sin(tangent1), math.cos(tangent1))
						tangent2 = math.atan2(radii_ratio*math.sin(tangent2), math.cos(tangent2))
					segmentAngles[-1].append((tangent1 + rotation, tangent2 + rotation))

			elif letter == 'C':
				vertex = coords[-2:]
				segmentAngles[-1].append(helpers.bezier_angles(lastVertex, coords[0:2], coords[2:4], vertex))

			elif letter == 'Q':
				vertex = coords[-2:]
				segmentAngles[-1].append(helpers.bezier_angles(lastVertex, coords[0:2], vertex))

			elif letter == 'Z':
				vertex = lastM
				angle = helpers.point_angle(*lastVertex, *vertex)
				segmentAngles[-1].append((angle, angle))

			lastVertex = vertex
			lastLetter = letter

		if lastLetter != 'Z': # Mark last path unclosed
			segmentAngles[-1].append(None)

		# Calculate vertex angles from adjoining segments
		vertexAngles = []
		for subpath in segmentAngles:
			angleOut, angleIn = None, None

			if subpath and subpath[-1] is not None:
				# Closed subpath: assign final angle to average with initial angle &
				# append copy of first angle at the end
				angleIn = subpath[-1][1]
				subpath += [subpath[0]]

			for angles in subpath:
				if angles:
					angleOut = angles[0]
					if angleIn is None:
						# Start of unclosed subpath
						vertexAngles.append(angleOut)
					else:
						# Two adjoining segments: bisect the angle difference
						# by summing the corresponding unit vectors
						vertexAngles.append(math.atan2(math.sin(angleOut) + math.sin(angleIn), math.cos(angleOut) + math.cos(angleIn)))
					angleIn = angles[1]
				else: # End of unclosed subpath
					vertexAngles.append(angleIn)
		return vertexAngles

	def d(self, d):
		"""Append path data from a string"""
		self._d(d)
		self._addToAttr(d)
		return self

	def _d(self, d):
		string = d
		surface = self._getSurface() # is a surface necessary for unit conversion?
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
				rx, ry, string = helpers.coordinates.point(surface, string)
				rotation, string = string.split(' ', 1)

				# The large and sweep values are not always separated from the
				# following values. These flags can only be 0 or 1, so reading a
				# single digit suffices.
				large, string = string[0], string[1:].strip()
				sweep, string = string[0], string[1:].strip()

				# Retrieve end point and set remainder (before checking flags)
				x3, y3, string = helpers.coordinates.point(surface, string)

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
				x1, y1, string = helpers.coordinates.point(surface, string)
				x2, y2, string = helpers.coordinates.point(surface, string)
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._c(x1, y1, x2, y2, x3, y3)

			elif letter == 'C':
				# Curve
				x1, y1, string = helpers.coordinates.point(surface, string)
				x2, y2, string = helpers.coordinates.point(surface, string)
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._C(x1, y1, x2, y2, x3, y3)

			elif letter == 'h':
				# Relative horizontal line
				x, string = (string + ' ').split(' ', 1)
				x = helpers.coordinates.size(surface, x, 'x')
				self._h(x)

			elif letter == 'H':
				# Horizontal line
				x, string = (string + ' ').split(' ', 1)
				x = helpers.coordinates.size(surface, x, 'x')
				self._H(x)

			elif letter == 'l':
				# Relative straight line
				x, y, string = helpers.coordinates.point(surface, string)
				self._l(x, y)

			elif letter == 'L':
				# Straight line
				x, y, string = helpers.coordinates.point(surface, string)
				self._L(x, y)

			elif letter == 'm':
				# Current point relative move
				x, y, string = helpers.coordinates.point(surface, string)
				self._m(x, y)

			elif letter == 'M':
				# Current point move
				x, y, string = helpers.coordinates.point(surface, string)
				self._M(x, y)

			elif letter == 'q':
				# Relative quadratic curve
				x1, y1 = 0, 0
				x2, y2, string = helpers.coordinates.point(surface, string)
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._q(x2, y2, x3, y3)

			elif letter == 'Q':
				# Quadratic curve
				x2, y2, string = helpers.coordinates.point(surface, string)
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._Q(x2, y2, x3, y3)

			elif letter == 's':
				# Relative smooth curve
				x2, y2, string = helpers.coordinates.point(surface, string)
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._s(x2, y2, x3, y3)

			elif letter == 'S':
				# Smooth curve
				x2, y2, string = helpers.coordinates.point(surface, string)
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._S(x2, y2, x3, y3)

			elif letter == 't':
				# Relative quadratic curve end
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._t(x3, y3)

			elif letter == 'T':
				# Quadratic curve end
				x3, y3, string = helpers.coordinates.point(surface, string)
				self._T(x3, y3)

			elif letter == 'v':
				# Relative vertical line
				y, string = (string + ' ').split(' ', 1)
				y = helpers.coordinates.size(surface, y, 'y')
				self._v(y)

			elif letter == 'V':
				# Vertical line
				y, string = (string + ' ').split(' ', 1)
				y = helpers.coordinates.size(surface, y, 'y')
				self._V(y)

			elif letter in 'zZ':
				# End of path
				self._Z()

			string = string.strip()
