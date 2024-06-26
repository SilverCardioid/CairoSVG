from __future__ import annotations
import math
import typing as ty

def distance(x1:float, y1:float, x2:float, y2:float) -> float:
	"""Get the distance between two points."""
	return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def point_angle(cx:float, cy:float, px:float, py:float) -> float:
	"""Return angle between x axis and point knowing given center."""
	return math.atan2(py - cy, px - cx)


def rotate(x:float, y:float, angle:float) -> ty.Tuple[float, float]:
	"""Rotate a point of an angle around the origin point."""
	return (x * math.cos(angle) - y * math.sin(angle),
	        y * math.cos(angle) + x * math.sin(angle))


def quadratic_points(x1:float, y1:float, x2:float, y2:float, x3:float, y3:float
                     )-> ty.Tuple[float, float, float, float, float, float]:
	"""Convert a quadratic to a cubic Bezier.
	Return the cubic curve (control points and end point) that is equivalent
	to the given quadratic curve (start point, control point and end point).
	"""
	xq1 = x2 * 2 / 3 + x1 / 3
	yq1 = y2 * 2 / 3 + y1 / 3
	xq2 = x2 * 2 / 3 + x3 / 3
	yq2 = y2 * 2 / 3 + y3 / 3
	return xq1, yq1, xq2, yq2, x3, y3


def bezier_angles(*points:float) -> ty.Tuple[float, float]:
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
		return (point_angle(*points[0], *points[1]),
		        point_angle(*points[-2], *points[-1]))


def evaluate_quadratic(t:float, p0:float, p1:float, p2:float) -> float:
	"""Evaluate a quadratic Bezier curve.
	Given the coordinates for the start point, control point and end point
	along one axis, get the coordinate of a point on the curve at the
	parametric value `t` for that axis.
	"""
	return p0*(1-t)*(1-t) + 2*p1*t*(1-t) + p2*t*t

def evaluate_cubic(t:float, p0:float, p1:float, p2:float, p3:float) -> float:
	"""Evaluate a cubic Bezier curve.
	Given the coordinates for the start point, two control points and end
	point along one axis, get the coordinate of a point on the curve at the
	parametric value `t` for that axis.
	"""
	return p0*(1-t)*(1-t)*(1-t) + 3*p1*t*(1-t)*(1-t) + 3*p2*t*t*(1-t) + p3*t*t*t


def quadratic_extrema(p0:float, p1:float, p2:float
                      ) -> ty.List[ty.Tuple[float, float]]:
	"""Find the extrema of a quadratic Bezier curve.
	Given the coordinates for the start point, control point and end point
	along one axis, get the parametric value `t` at which the curve has a
	zero derivative (if any), and return a list of solutions as tuples of
	`t` values and corresponding point coordinates.
	"""
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

def cubic_extrema(p0:float, p1:float, p2:float, p3:float
                  ) -> ty.List[ty.Tuple[float, float]]:
	"""Find the extrema of a cubic Bezier curve.
	Given the coordinates for the start point, two control points and end
	point along one axis, get the parametric values `t` at which the curve
	has a zero derivative (if any), and return a list of solutions as tuples
	of `t` values and corresponding point coordinates.
	"""
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
	def __init__(self, rx:float, ry:float, rotation:float,
	             large:bool, sweep:bool, dx:float, dy:float):
		self.rx = rx; self.ry = ry
		self.rotation = math.radians(float(rotation))
		self.large = large; self.sweep = sweep
		self.dx = dx; self.dy = dy
		self.calculate()

	def calculate(self):
		# Cancel the rotation & eccentricity
		self.radii_ratio = self.ry / self.rx
		dx, dy = rotate(self.dx, self.dy, -self.rotation)
		dy /= self.radii_ratio
		# Put the second point onto the x axis
		angle = point_angle(0, 0, dx, dy)
		dx, dy = (dx ** 2 + dy ** 2) ** .5, 0
		# Update the x radius if it is too small
		self.rx = max(self.rx, dx / 2)
		self.ry = self.rx * self.radii_ratio
		# Find circle centre
		xc = dx / 2
		yc = (self.rx ** 2 - xc ** 2) ** .5
		if not (self.large ^ self.sweep):
			yc = -yc
		# Put the second point and the center back to their positions
		dx, dy = rotate(dx, 0, angle)
		self.draw_center = rotate(xc, yc, angle)
		self.draw_angles = (point_angle(*self.draw_center, 0, 0),
		                    point_angle(*self.draw_center, dx, dy))
		self.center = rotate(self.draw_center[0],
		                     self.draw_center[1]*self.radii_ratio, self.rotation)

	def evaluate(self, t:float) -> ty.Tuple[float, float]:
		return (self.center[0] + self.rx*math.cos(self.rotation)*math.cos(t)
		                       - self.ry*math.sin(self.rotation)*math.sin(t),
		        self.center[1] + self.rx*math.sin(self.rotation)*math.cos(t)
		                       + self.ry*math.cos(self.rotation)*math.sin(t))

	def extrema(self) -> ty.List[ty.Tuple[float, ty.Tuple[float, float]]]:
		# Get parametric angles for the extrema of the full circle or ellipse, in [0, 2pi)
		if self.rotation == 0:
			# No rotation: extrema must be at multiples of pi/2
			ex_angles = [0, math.pi/2, math.pi, 3*math.pi/2]
		elif self.radii_ratio == 1:
			# Rotated circular arc: account for rotation
			ex_angles = sorted([(-self.rotation              ) % (2*math.pi),
			                    (-self.rotation +   math.pi/2) % (2*math.pi),
			                    (-self.rotation +   math.pi  ) % (2*math.pi),
			                    (-self.rotation + 3*math.pi/2) % (2*math.pi)])
		else:
			# Rotated elliptical arc: get solutions for dx/dt = 0 and dy/dt = 0
			tx = math.atan2(-self.ry * math.sin(self.rotation),
			                 self.rx * math.cos(self.rotation))
			ty = math.atan2( self.ry * math.cos(self.rotation),
			                 self.rx * math.sin(self.rotation))
			ex_angles = sorted([(tx          ) % (2*math.pi),
			                    (tx + math.pi) % (2*math.pi),
			                    (ty          ) % (2*math.pi),
			                    (ty + math.pi) % (2*math.pi)])

		# Normalise angles to make sure 0 <= a1 <= a2
		a1 = self.draw_angles[0] % (2*math.pi)
		a2 = self.draw_angles[1] % (2*math.pi)
		if not self.sweep:
			a1, a2 = a2, a1
		if a1 > a2:
			a2 += 2*math.pi

		# Check which possible angles are between a1 and a2
		solns = []
		for angle in ex_angles:
			# check angle+2pi too since a2 may be up to 4pi
			if a1 < angle < a2 or a1 < (angle + 2*math.pi) < a2:
				x, y = self.evaluate(angle)
				solns.append((angle, (x, y)))

		return solns


def arc_extrema(rx:float, ry:float, rotation:float,
                large:bool, sweep:bool, dx:float, dy:float
                ) -> ty.List[ty.Tuple[float, ty.Tuple[float, float]]]:
	"""Find the extrema of an elliptical arc.
	Given an arc (using the syntax of a path's 'a' command), get the input
	angles at which the arc has a horizontal or vertical tangent, and return
	a list of solutions as tuples of angles and (x, y) tuples.
	"""
	return Arc(rx, ry, rotation, large, sweep, dx, dy).extrema()


class Box:
	# Helper class for bounding rectangles, to distinguish
	# single-point boxes at the origin from null boxes without defined location
	def __init__(self, x:ty.Optional[float] = None, y:ty.Optional[float] = None,
	             width:float = 0, height:float = 0):
		self.defined = x is not None and y is not None
		if self.defined:
			self.x0 = x
			self.y0 = y
			self.x1 = self.x + width
			self.y1 = self.y + height
		else:
			self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0

	@property
	def x(self) -> float: return self.x0
	@property
	def y(self) -> float: return self.y0
	@property
	def width(self) -> float: return self.x1 - self.x0
	@property
	def height(self) -> float: return self.y1 - self.y0
	@property
	def xywh(self) -> ty.Tuple[float, float, float, float]:
		return (self.x, self.y, self.width, self.height)

	def copy(self) -> Box:
		if self.defined:
			return Box(self.x, self.y, self.width, self.height)
		else:
			return Box()

	def add_point(self, x:float, y:float):
		if self.defined:
			self.x0, self.x1 = min(self.x0, x), max(self.x1, x)
			self.y0, self.y1 = min(self.y0, y), max(self.y1, y)
		else:
			# Initial point
			self.x0, self.x1 = x, x
			self.y0, self.y1 = y, y
			self.defined = True

	def add_box(self, other:Box):
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

	def vertices(self) -> ty.List[ty.Tuple[float, float]]:
		if self.defined:
			return [(self.x0, self.y0), (self.x1, self.y0), (self.x1, self.y1), (self.x0, self.y1)]
		else:
			return []

	def __add__(self, other:Box) -> Box:
		return self.copy().add_box(other)

	def __iadd__(self, other:Box) -> Box:
		self.add_box(other)
		return self

	def __and__(self, other:Box) -> Box:
		if self.defined and other.defined:
			x0, x1 = max(self.x0, other.x0), min(self.x1, other.x1)
			y0, y1 = max(self.y0, other.y0), min(self.y1, other.y1)
			if x0 <= x1 and y0 <= y1:
				return Box(x0, y0, x1 - x0, y1 - y0)
		# either box not defined, or no intersection
		return Box()
