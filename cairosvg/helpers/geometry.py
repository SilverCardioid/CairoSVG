import math

def distance(x1, y1, x2, y2):
	"""Get the distance between two points."""
	return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def point_angle(cx, cy, px, py):
	"""Return angle between x axis and point knowing given center."""
	return math.atan2(py - cy, px - cx)


def rotate(x, y, angle):
	"""Rotate a point of an angle around the origin point."""
	return x * math.cos(angle) - y * math.sin(angle), y * math.cos(angle) + x * math.sin(angle)


def quadratic_points(x1, y1, x2, y2, x3, y3):
	"""Return the quadratic points to create quadratic curves."""
	xq1 = x2 * 2 / 3 + x1 / 3
	yq1 = y2 * 2 / 3 + y1 / 3
	xq2 = x2 * 2 / 3 + x3 / 3
	yq2 = y2 * 2 / 3 + y3 / 3
	return xq1, yq1, xq2, yq2, x3, y3


def bezier_angles(*points):
	"""Return the tangent angles of a Bezier curve of any degree."""
	if len(points) < 2:
		# zero-length segment
		return (0, 0)
	# Control points that coincide with vertices can be removed
	elif points[0] == points[1]:
		return bezier_angles(*points[1:])
	elif points[-2] == points[-1]:
		return bezier_angles(*points[:-1])
	else:
		return (point_angle(*points[0], *points[1]), point_angle(*points[-2], *points[-1]))


def evaluate_quadratic(t, p0, p1, p2):
	"""Get the value of either coordinate of a quadratic Bezier at parameter value t"""
	return p0*(1-t)*(1-t) + 2*p1*t*(1-t) + p2*t*t

def evaluate_cubic(t, p0, p1, p2, p3):
	"""Get the value of either coordinate of a cubic Bezier at parameter value t"""
	return p0*(1-t)*(1-t)*(1-t) + 3*p1*t*(1-t)*(1-t) + 3*p2*t*t*(1-t) + p3*t*t*t


def quadratic_extrema(p0, p1, p2):
	"""Find points on a quadratic Bezier with zero derivative (horizontal or vertical tangent)"""
	solns = []
	# solution of dp/dt = 0
	try:
		t = (p0 - p1)/(p0 - 2*p1 + p2)
		if 0 < t < 1:
			solns.append((t, evaluate_quadratic(t, p0, p1, p2)))
	except ZeroDivisionError:
		# p1 must be halfway between p0 and p2, so no extremum
		pass
	return solns

def cubic_extrema(p0, p1, p2, p3):
	"""Find points on a cubic Bezier with zero derivative (horizontal or vertical tangent)"""
	solns = []
	# coefficients of dp/dt (a quadratic function)
	a = 3*(-p0 + 3*p1 - 3*p2 + p3)
	b = 6*(p0 - 2*p1 + p2)
	c = 3*(-p0 + p1)
	det = b*b - 4*a*c
	if a == 0:
		# linear equation bt+c = 0; one solution unless b == 0
		if b != 0:
			t = -c/b
			if 0 < t < 1:
				solns.append((t, evaluate_cubic(t, p0, p1, p2, p3)))

	elif det > 0:
		# two roots
		t1 = (-b - det**0.5) / (2*a)
		t2 = (-b + det**0.5) / (2*a)
		if 0 < t1 < 1:
			solns.append((t1, evaluate_cubic(t1, p0, p1, p2, p3)))
		if 0 < t2 < 1:
			solns.append((t2, evaluate_cubic(t2, p0, p1, p2, p3)))

	elif det == 0:
		# one root
		t = -b / (2*a)
		if 0 < t < 1:
			solns.append((t, evaluate_cubic(t, p0, p1, p2, p3)))

	return solns


class Arc:
	# Helper class for arcs
	def __init__(self, rx, ry, rotation, large, sweep, dx, dy):
		self.rx = rx; self.ry = ry
		self.rotation = math.radians(float(rotation))
		self.large = large; self.sweep = sweep
		self.dx = dx; self.dy = dy
		self.calculate()

	def calculate(self):
		# Cancel the rotation & eccentricity
		self.radiiRatio = self.ry / self.rx
		dx, dy = rotate(self.dx, self.dy, -self.rotation)
		dy /= self.radiiRatio
		# Put the second point onto the x axis
		angle = point_angle(0, 0, dx, dy)
		dx, dy = (dx ** 2 + dy ** 2) ** .5, 0
		# Update the x radius if it is too small
		self.rx = max(self.rx, dx / 2)
		self.ry = self.rx * self.radiiRatio
		# Find circle centre
		xc = dx / 2
		yc = (self.rx ** 2 - xc ** 2) ** .5
		if not (self.large ^ self.sweep):
			yc = -yc
		# Put the second point and the center back to their positions
		dx, dy = rotate(dx, 0, angle)
		self.drawCenter = rotate(xc, yc, angle)
		self.drawAngles = (point_angle(*self.drawCenter, 0, 0),
		                   point_angle(*self.drawCenter, dx, dy))
		self.center = rotate(self.drawCenter[0],
		                     self.drawCenter[1]*self.radiiRatio, self.rotation)

	def evaluate(self, t):
		return (self.center[0] + self.rx*math.cos(self.rotation)*math.cos(t)
		                       - self.ry*math.sin(self.rotation)*math.sin(t),
		        self.center[1] + self.rx*math.sin(self.rotation)*math.cos(t)
		                       + self.ry*math.cos(self.rotation)*math.sin(t))

	def extrema(self):
		# Get parametric angles for the extrema of the full circle or ellipse, in [0, 2pi)
		if self.rotation == 0:
			# No rotation: extrema must be at multiples of pi/2
			exAngles = [0, math.pi/2, math.pi, 3*math.pi/2]
		elif self.radiiRatio == 1:
			# Rotated circular arc: account for rotation
			exAngles = sorted([(-self.rotation              ) % (2*math.pi),
			                   (-self.rotation +   math.pi/2) % (2*math.pi),
			                   (-self.rotation +   math.pi  ) % (2*math.pi),
			                   (-self.rotation + 3*math.pi/2) % (2*math.pi)])
		else:
			# Rotated elliptical arc: get solutions for dx/dt = 0 and dy/dt = 0
			tx = math.atan2(-self.ry * math.sin(self.rotation), self.rx * math.cos(self.rotation))
			ty = math.atan2( self.ry * math.cos(self.rotation), self.rx * math.sin(self.rotation))
			exAngles = sorted([(tx          ) % (2*math.pi),
			                   (tx + math.pi) % (2*math.pi),
			                   (ty          ) % (2*math.pi),
			                   (ty + math.pi) % (2*math.pi)])

		# Normalise angles to make sure 0 <= a1 <= a2
		a1 = self.drawAngles[0] % (2*math.pi)
		a2 = self.drawAngles[1] % (2*math.pi)
		if not self.sweep:
			a1, a2 = a2, a1
		if a1 > a2:
			a2 += 2*math.pi

		# Check which possible angles are between a1 and a2
		solns = []
		for angle in exAngles:
			# check angle+2pi too since a2 may be up to 4pi
			if a1 < angle < a2 or a1 < (angle + 2*math.pi) < a2:
				x, y = self.evaluate(angle)
				solns.append((angle, (x, y)))

		return solns


def arc_extrema(rx, ry, rotation, large, sweep, dx, dy):
	"""Find points on an arc with zero derivative (horizontal or vertical tangent)"""
	return Arc(rx, ry, rotation, large, sweep, dx, dy).extrema()


class Box:
	# Helper class for bounding rectangles, to distinguish
	# single-point boxes at the origin from null boxes without defined location
	def __init__(self, x=None, y=None, width=0, height=0):
		self.defined = x is not None and y is not None
		if self.defined:
			self.x0 = x
			self.y0 = y
			self.x1 = self.x + width
			self.y1 = self.y + height
		else:
			self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0

	@property
	def x(self): return self.x0
	@property
	def y(self): return self.y0
	@property
	def width(self): return self.x1 - self.x0
	@property
	def height(self): return self.y1 - self.y0
	@property
	def xywh(self):
		return (self.x, self.y, self.width, self.height)

	def copy(self):
		if self.defined:
			return Box(self.x, self.y, self.width, self.height)
		else:
			return Box()

	def addPoint(self, x, y):
		if self.defined:
			self.x0, self.x1 = min(self.x0, x), max(self.x1, x)
			self.y0, self.y1 = min(self.y0, y), max(self.y1, y)
		else:
			# Initial point
			self.x0, self.x1 = x, x
			self.y0, self.y1 = y, y
			self.defined = True

	def addBox(self, other):
		if other.defined:
			if self.defined:
				# bounding box of the union of the two
				self.x0, self.x1 = min(self.x0, other.x0), max(self.x1, other.x1)
				self.y0, self.y1 = min(self.y0, other.y0), max(self.y1, other.y1)
			else:
				# copy other
				self.x0, self.x1 = other.x0, other.x1
				self.y0, self.y1 = other.y0, other.y1
				self.defined = True
		# other not defined: no change

	def __add__(self, other):
		return self.copy().addBox(other)

	def __iadd__(self, other):
		self.addBox(other)
		return self

	def __and__(self, other):
		if self.defined and other.defined:
			x0, x1 = max(self.x0, other.x0), min(self.x1, other.x1)
			y0, y1 = max(self.y0, other.y0), min(self.y1, other.y1)
			if x0 <= x1 and y0 <= y1:
				return Box(x0, y0, x1 - x0, y1 - y0)
		# either box not defined, or no intersection
		return Box()
