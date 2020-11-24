from ..helpers import quadratic_points

class Path:
	def __init__(self, d=None):
		self._data = []
		self._currentPoint = None
		self._startPoint = None
		self._lastBezier = None
		if d is not None:
			self.d(d)

	def _add(path, type, coords=None):
		self._data.append([type, coords])
		if type == 'M':
			self._startPoint = coords[-2:]
		elif self._startPoint is None:
			raise ValueError('Path has not been started with \'M\' or \'m\'')
		self._currentPoint = coords[-2:] if type != 'Z' else self._startPoint
		self._lastBezier = (type, *coords[-4:-2]) if type in 'QC' else None

	def _rel2abs(path, x, y):
		return self._currentPoint[0] + x, self._currentPoint[1] + y

	def d(self, d):
		raise NotImplementedError()

	def M(self, x, y):
		"""Moveto: start a new sub-path at (x, y)"""
		self._add('M', [x, y])
		return self

	def m(self, x, y):
		"""Relative moveto: start a new sub-path at (x, y)"""
		return self.M(*self._rel2abs(x, y))

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
		cubicCoords = quadratic_points(*self._currentPoint, x1, y1, x, y)
		self._add('C', cubicCoords)
		return self

	def q(self, x1, y1, x, y):
		"""Relative quadratic Bezier curveto"""
		return self.Q(*self._rel2abs(x1, y1), *self._rel2abs(x, y))

	def S(self, x2, y2, x, y):
		"""Smooth curveto: smooth cubic Bezier curve"""
		x1, y1 = self._currentPoint
		if self._lastBezierPoint and self._lastBezierPoint[0]=='C':
			xp, yp = self._lastBezierPoint[1:]
			x1, y1 = x1 - (xp - x1), y1 - (yp - y1)
		return self.C(x1, y1, x2, y2, x, y)

	def s(self, x2, y2, x, y):
		"""Relative smooth curveto: smooth cubic Bezier curve"""
		return self.S(*self._rel2abs(x2, y2), *self._rel2abs(x, y))

	def T(self, x, y):
		"Smooth quadratic Bezier curveto"
		x1, y1 = self._currentPoint
		if self._lastBezierPoint and self._lastBezierPoint[0]=='Q':
			xp, yp = self._lastBezierPoint[1:]
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

	def draw(self, context):
		for command in self._data:
			letter, coords = command
			if letter == 'M':
				context.move_to(*coords)
			elif letter == 'L':
				context.line_to(*coords)
			elif letter == 'A':
				raise NotImplementedError()
			elif letter == 'C':
				context.curve_to(*coords)
			elif letter == 'Q':
				raise NotImplementedError()
			elif letter == 'Z':
				context.close_path()
			else:
				raise ValueError('Unknown letter: ' + letter)

