"""
Shapes drawers.

"""

from math import pi

from ..draw import shapes
from ..helpers import normalize, point, point_angle, size


def circle(surface, node):
    """Draw a circle ``node`` on ``surface``."""
    r = size(surface, node.get('r'))
    if not r:
        return
    cx = size(surface, node.get('cx'), 'x')
    cy = size(surface, node.get('cy'), 'y')

    shape = shapes.Circle(r, cx, cy, fill='none')
    shape._paint = lambda surface: None # hack to bypass painting by .draw
    shape.draw(surface)


def ellipse(surface, node):
    """Draw an ellipse ``node`` on ``surface``."""
    rx = size(surface, node.get('rx'), 'x')
    ry = size(surface, node.get('ry'), 'y')
    if not rx or not ry:
        return
    cx = size(surface, node.get('cx'), 'x')
    cy = size(surface, node.get('cy'), 'y')

    shape = shapes.Ellipse(rx, ry, cx, cy, fill='none')
    shape._paint = lambda surface: None # hack to bypass painting by .draw
    shape.draw(surface)


def line(surface, node):
    """Draw a line ``node``."""
    x1, y1, x2, y2 = tuple(
        size(surface, node.get(position), position[0])
        for position in ('x1', 'y1', 'x2', 'y2'))

    node.path = shapes.Line(x1, y1, x2, y2, fill='none')
    node.path._paint = lambda surface: None # hack to bypass painting by .draw
    node.path.draw(surface)


def polygon(surface, node):
    """Draw a polygon ``node`` on ``surface``."""
    string = normalize(node.get('points', ''))
    points = []
    while string:
        x, y, string = point(surface, string)
        points.append([x, y])

    node.path = shapes.Polygon(points, fill='none')
    node.path._paint = lambda surface: None # hack to bypass painting by .draw
    node.path.draw(surface)


def polyline(surface, node):
    """Draw a polyline ``node``."""
    string = normalize(node.get('points', ''))
    points = []
    while string:
        x, y, string = point(surface, string)
        points.append([x, y])

    node.path = shapes.Polyline(points, fill='none')
    node.path._paint = lambda surface: None # hack to bypass painting by .draw
    node.path.draw(surface)


def rect(surface, node):
    """Draw a rect ``node`` on ``surface``."""
    x, y = size(surface, node.get('x'), 'x'), size(surface, node.get('y'), 'y')
    width = size(surface, node.get('width'), 'x')
    height = size(surface, node.get('height'), 'y')
    rx = node.get('rx')
    ry = node.get('ry')

    shape = shapes.Rect(width, height, x, y, rx, ry, fill='none')
    shape._paint = lambda surface: None # hack to bypass painting by .draw
    shape.draw(surface)
