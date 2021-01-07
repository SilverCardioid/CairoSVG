from .element import Element
from .. import helpers

class Path(Element):
	def __init__(self, d=None, **attribs):
		Element.__init__(self, d=d, **attribs)
		self.parent = parent
		self.surface = parent.surface if hasattr(parent, 'surface') else None
		self._data = []
		self._currentPoint = None
		self._startPoint = None
		self._lastBezier = None
		if d is not None:
			self.d(d)

	def _add(self, type, coords=None):
		self._data.append([type, coords])
		if type == 'M':
			self._startPoint = coords[-2:]
		elif self._startPoint is None:
			raise ValueError('Path has not been started with \'M\' or \'m\'')
		self._currentPoint = coords[-2:] if type != 'Z' else self._startPoint
		self._lastBezier = (type, *coords[-4:-2]) if type in 'QC' else None

	def _rel2abs(self, x, y):
		return self._currentPoint[0] + x, self._currentPoint[1] + y

	def M(self, x, y):
		"""Moveto: start a new sub-path at (x, y)"""
		self._add('M', [x, y])
		return self

	def m(self, x, y):
		"""Relative moveto: start a new sub-path at (x, y)"""
		return self.M(*self._rel2abs(x, y)) if self._startPoint is not None else self.M(x, y)

	# Lineto
	def L(self, x, y):
		"""Lineto: draw a straight line to (x, y)"""
		self._add('L', [x, y])
		return self

	def l(self, x, y):
		"""Relative lineto: draw a straight line to (x, y)"""
		return self.L(*self._rel2abs(x, y))

	def H(self, x):
		"""Horizontal lineto: draw a horizontal line to a new X coordinate"""
		return self.L(x, self._currentPoint[1])

	def h(self, x):
		"""Relative horizontal lineto: draw a horizontal line to a new X coordinate"""
		return self.l(x, 0)

	def V(self, y):
		"""Vertical lineto: draw a vertical line to a new Y coordinate"""
		return self.L(self._currentPoint[0], y)

	def v(self, y):
		"""Relative vertical lineto: draw a vertical line to a new Y coordinate"""
		return self.l(0, y)

	def A(self, rx, ry, rot, large, sweep, x, y):
		"""Elliptical arc"""
		self._add('A', [rx, ry, rot, large, sweep, x, y])
		return self

	def a(self, rx, ry, rot, large, sweep, x, y):
		"""Relative elliptical arc"""
		return self.A(rx, ry, rot, large, sweep, *self._rel2abs(x, y))

	def C(self, x1, y1, x2, y2, x, y):
		"""Curveto: cubic Bezier curve"""
		self._add('C', [x1, y1, x2, y2, x, y])
		return self

	def c(self, x1, y1, x2, y2, x, y):
		"""Relative curveto: cubic Bezier curve"""
		return self.C(*self._rel2abs(x1, y1), *self._rel2abs(x2, y2), *self._rel2abs(x, y))

	def Q(self, x1, y1, x, y):
		"""Quadratic Bezier curveto"""
		self._add('Q', [x1, y1, x, y])
		return self

	def q(self, x1, y1, x, y):
		"""Relative quadratic Bezier curveto"""
		return self.Q(*self._rel2abs(x1, y1), *self._rel2abs(x, y))

	def S(self, x2, y2, x, y):
		"""Smooth curveto: smooth cubic Bezier curve"""
		x1, y1 = self._currentPoint
		if self._lastBezier and self._lastBezier[0]=='C':
			xp, yp = self._lastBezier[1:]
			x1, y1 = x1 - (xp - x1), y1 - (yp - y1)
		return self.C(x1, y1, x2, y2, x, y)

	def s(self, x2, y2, x, y):
		"""Relative smooth curveto: smooth cubic Bezier curve"""
		return self.S(*self._rel2abs(x2, y2), *self._rel2abs(x, y))

	def T(self, x, y):
		"Smooth quadratic Bezier curveto"
		x1, y1 = self._currentPoint
		if self._lastBezier and self._lastBezier[0]=='Q':
			xp, yp = self._lastBezier[1:]
			x1, y1 = x1 - (xp - x1), y1 - (yp - y1)
		return self.Q(x1, y1, x, y)

	def t(self, x, y):
		"Relative smooth quadratic Bezier curveto"
		return self.T(*self._rel2abs(x, y))

	def Z(self):
		"Closepath: draw a straight line to the sub-path's initial point"
		self._add('Z')
		return self
	z = Z

	def draw(self):
		if self.surface is None:
			raise Exception('surface needed for drawing')
		startPoint = None
		lastPoint = None
		for command in self._data:
			letter, coords = command
			if letter == 'M':
				self.surface.context.move_to(*coords)
				startPoint = coords[-2:]
			elif letter == 'L':
				self.surface.context.line_to(*coords)
			elif letter == 'A':
				self._drawArc(*lastPoint, *coords)
			elif letter == 'C':
				self.surface.context.curve_to(*coords)
			elif letter == 'Q':
				cubicCoords = helpers.quadratic_points(*lastPoint, *coords)
				self.surface.context.curve_to(*cubicCoords)
			elif letter == 'Z':
				self.surface.context.close_path()
			else:
				raise ValueError('Unknown letter: ' + letter)
			lastPoint = coords[-2:] if letter != 'Z' else startPoint

	def _drawArc(self, x1, y1, rx, ry, rotation, large, sweep, x3, y3):
		self.surface.context.set_tolerance(0.00001)
		rotation = helpers.radians(float(rotation))
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
		arc = (self.surface.context.arc if sweep else self.surface.context.arc_negative)
		# Put the second point and the center back to their positions
		xe, ye = helpers.rotate(xe, 0, angle)
		xc, yc = helpers.rotate(xc, yc, angle)
		# Find the drawing angles
		angle1 = helpers.point_angle(xc, yc, 0, 0)
		angle2 = helpers.point_angle(xc, yc, xe, ye)
		# Draw the arc
		self.surface.context.save()
		self.surface.context.translate(x1, y1)
		self.surface.context.rotate(rotation)
		self.surface.context.scale(1, radii_ratio)
		arc(xc, yc, rx, angle1, angle2)
		self.surface.context.restore()

	def d(self, d):
		"""Load path data from a string"""
		for letter in helpers.PATH_LETTERS:
				string = string.replace(letter, ' {} '.format(letter))
		string = normalize(string)

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
						rx, ry, string = helpers.point(self.surface, string)
						rotation, string = string.split(' ', 1)

						# The large and sweep values are not always separated from the
						# following values. These flags can only be 0 or 1, so reading a
						# single digit suffices.
						large, string = string[0], string[1:].strip()
						sweep, string = string[0], string[1:].strip()

						# Retrieve end point and set remainder (before checking flags)
						x3, y3, string = helpers.point(self.surface, string)

						# Only allow 0 or 1 for flags
						large, sweep = int(large), int(sweep)
						if large not in (0, 1) or sweep not in (0, 1):
								continue
						large, sweep = bool(large), bool(sweep)

						if letter == 'A':
								# Absolute x3 and y3, convert to relative
								x3 -= x1
								y3 -= y1

						# rx=0 or ry=0 means straight line
						if not rx or not ry:
								self.l(x3, y3)
								continue
						else:
								self.a(rx, ry, rotation, large, sweep, x3, y3)

				elif letter == 'c':
						# Relative curve
						x1, y1, string = helpers.point(self.surface, string)
						x2, y2, string = helpers.point(self.surface, string)
						x3, y3, string = helpers.point(self.surface, string)
						self.c(x1, y1, x2, y2, x3, y3)

				elif letter == 'C':
						# Curve
						x1, y1, string = helpers.point(self.surface, string)
						x2, y2, string = helpers.point(self.surface, string)
						x3, y3, string = helpers.point(self.surface, string)
						self.C(x1, y1, x2, y2, x3, y3)

				elif letter == 'h':
						# Relative horizontal line
						x, string = (string + ' ').split(' ', 1)
						x = helpers.size(self.surface, x, 'x')
						self.h(x)

				elif letter == 'H':
						# Horizontal line
						x, string = (string + ' ').split(' ', 1)
						x = helpers.size(self.surface, x, 'x')
						self.H(x)

				elif letter == 'l':
						# Relative straight line
						x, y, string = helpers.point(self.surface, string)
						self.l(x, y)

				elif letter == 'L':
						# Straight line
						x, y, string = helpers.point(self.surface, string)
						self.L(x, y)

				elif letter == 'm':
						# Current point relative move
						x, y, string = helpers.point(self.surface, string)
						self.m(x, y)

				elif letter == 'M':
						# Current point move
						x, y, string = helpers.point(self.surface, string)
						self.M(x, y)

				elif letter == 'q':
						# Relative quadratic curve
						x1, y1 = 0, 0
						x2, y2, string = helpers.point(self.surface, string)
						x3, y3, string = helpers.point(self.surface, string)
						self.q(x2, y2, x3, y3)

				elif letter == 'Q':
						# Quadratic curve
						x2, y2, string = helpers.point(self.surface, string)
						x3, y3, string = helpers.point(self.surface, string)
						self.Q(x2, y2, x3, y3)

				elif letter == 's':
						# Relative smooth curve
						x2, y2, string = helpers.point(self.surface, string)
						x3, y3, string = helpers.point(self.surface, string)
						self.s(x2, y2, x3, y3)

				elif letter == 'S':
						# Smooth curve
						x2, y2, string = helpers.point(self.surface, string)
						x3, y3, string = helpers.point(self.surface, string)
						self.S(x2, y2, x3, y3)

				elif letter == 't':
						# Relative quadratic curve end
						x3, y3, string = helpers.point(self.surface, string)
						self.t(x3, y3)

				elif letter == 'T':
						# Quadratic curve end
						x3, y3, string = helpers.point(self.surface, string)
						self.T(x3, y3)

				elif letter == 'v':
						# Relative vertical line
						y, string = (string + ' ').split(' ', 1)
						y = helpers.size(self.surface, y, 'y')
						self.v(y)

				elif letter == 'V':
						# Vertical line
						y, string = (string + ' ').split(' ', 1)
						y = helpers.size(self.surface, y, 'y')
						self.V(y)

				elif letter in 'zZ':
						# End of path
						self.z()

				string = string.strip()

		return self
