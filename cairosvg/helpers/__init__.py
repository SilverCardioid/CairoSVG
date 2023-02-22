"""
Surface helpers.

"""

import re
from math import radians, tan

import cairocffi as cairo
from . import attribs, coordinates, geometry, parse, root, surface
#from .parse.url import parse_url

PAINT_URL = re.compile(r'(url\(.+\)) *(.*)')
PATH_LETTERS = 'achlmqstvzACHLMQSTVZ'
RECT = re.compile(r'rect\( ?(.+?) ?\)')

# Basic type subclasses to mark arguments that haven't been
# explicitly set, and should be omitted from exported code
class _Default: pass
class _intdef(int, _Default): pass
class _strdef(str, _Default): pass


class PointError(Exception):
    """Exception raised when parsing a point fails."""


def paint(value):
    """Extract from value an uri and a color.

    See http://www.w3.org/TR/SVG/painting.html#SpecifyingPaint

    """
    if not value:
        return None, None

    value = value.strip()
    match = PAINT_URL.search(value)
    if match:
        source = parse_url(match.group(1)).fragment
        color = match.group(2) or None
    else:
        source = None
        color = value or None

    return (source, color)


def clip_marker_box(surface, node, scale_x, scale_y):
    """Get the clip ``(x, y, width, height)`` of the marker box."""
    width = coordinates.size(surface, node.get('markerWidth', '3'), 'x')
    height = coordinates.size(surface, node.get('markerHeight', '3'), 'y')
    _, _, viewbox = coordinates.node_format(surface, node)
    viewbox_width, viewbox_height = viewbox[2:]

    align = node.get('preserveAspectRatio', 'xMidYMid').split(' ')[0]
    x_position = 'min' if align == 'none' else align[1:4].lower()
    y_position = 'min' if align == 'none' else align[5:].lower()

    clip_x = viewbox[0]
    if x_position == 'mid':
        clip_x += (viewbox_width - width / scale_x) / 2.
    elif x_position == 'max':
        clip_x += viewbox_width - width / scale_x

    clip_y = viewbox[1]
    if y_position == 'mid':
        clip_y += (viewbox_height - height / scale_y) / 2.
    elif y_position == 'max':
        clip_y += viewbox_height - height / scale_y

    return clip_x, clip_y, width / scale_x, height / scale_y


def transform2(surface, transform_string, gradient=None, transform_origin=None):
    """Transform ``surface`` or ``gradient`` if supplied using ``string``.

    See http://www.w3.org/TR/SVG/coords.html#TransformAttribute

    """
    if not transform_string:
        return

    transformations = re.findall(
        r'(\w+) ?\( ?(.*?) ?\)', attribs.normalize(transform_string))
    matrix = cairo.Matrix()

    if transform_origin:
        origin = transform_origin.split(' ')
        origin_x = origin[0]
        if len(origin) == 1:
            if origin_x in ('top', 'bottom'):
                origin_y = origin_x
                origin_x = surface.width / 2
            else:
                origin_y = surface.height / 2
        elif len(origin) > 1:
            if origin_x in ('top', 'bottom'):
                origin_y = origin_x
                origin_x = origin[1]
            else:
                origin_y = origin[1]
        else:
            return

        if origin_x == 'center':
            origin_x = surface.width / 2
        elif origin_x == 'left':
            origin_x = 0
        elif origin_x == 'right':
            origin_x = surface.width
        else:
            origin_x = coordinates.size(surface, origin_x, 'x')

        if origin_y == 'center':
            origin_y = surface.height / 2
        elif origin_y == 'top':
            origin_y = 0
        elif origin_y == 'bottom':
            origin_y = surface.height
        else:
            origin_y = coordinates.size(surface, origin_y, 'y')

        matrix.translate(float(origin_x), float(origin_y))

    for transformation_type, transformation in transformations:
        values = [coordinates.size(surface, value) for value in transformation.split(' ')]
        if transformation_type == 'matrix':
            matrix = cairo.Matrix(*values).multiply(matrix)
        elif transformation_type == 'rotate':
            angle = radians(float(values.pop(0)))
            x, y = values or (0, 0)
            matrix.translate(x, y)
            matrix.rotate(angle)
            matrix.translate(-x, -y)
        elif transformation_type == 'skewX':
            tangent = tan(radians(float(values[0])))
            matrix = cairo.Matrix(1, 0, tangent, 1, 0, 0).multiply(matrix)
        elif transformation_type == 'skewY':
            tangent = tan(radians(float(values[0])))
            matrix = cairo.Matrix(1, tangent, 0, 1, 0, 0).multiply(matrix)
        elif transformation_type == 'translate':
            if len(values) == 1:
                values += (0,)
            matrix.translate(*values)
        elif transformation_type == 'scale':
            if len(values) == 1:
                values = 2 * values
            matrix.scale(*values)

    if transform_origin:
        matrix.translate(-float(origin_x), -float(origin_y))

    try:
        matrix.invert()
    except cairo.Error:
        # Matrix not invertible, clip the surface to an empty path
        active_path = surface.context.copy_path()
        surface.context.new_path()
        surface.context.clip()
        surface.context.append_path(active_path)
    else:
        if gradient:
            # When applied on gradient use already inverted matrix (mapping
            # from user space to gradient space)
            matrix_now = gradient.get_matrix()
            gradient.set_matrix(matrix_now.multiply(matrix))
        else:
            matrix.invert()
            surface.context.transform(matrix)


def clip_rect(string):
    """Parse the rect value of a clip."""
    match = RECT.search(attribs.normalize(string or ''))
    return match.group(1).split(' ') if match else []


def rotations(node):
    """Retrieves the original rotations of a `text` or `tspan` node."""
    if 'rotate' in node:
        original_rotate = [
            float(i) for i in attribs.normalize(node['rotate']).strip().split(' ')]
        return original_rotate
    return []


def pop_rotation(node, original_rotate, rotate):
    """Removes the rotations of a node that are already used."""
    node['rotate'] = ' '.join(
        str(rotate.pop(0) if rotate else original_rotate[-1])
        for i in range(len(node.text)))


def zip_letters(xl, yl, dxl, dyl, rl, word):
    """Returns a list with the current letter's positions (x, y and rotation).

    E.g.: for letter 'L' with positions x = 10, y = 20 and rotation = 30:
    >>> [[10, 20, 30], 'L']

    Store the last value of each position and pop the first one in order to
    avoid setting an x,y or rotation value that have already been used.

    """
    return (
        ([pl.pop(0) if pl else None for pl in (xl, yl, dxl, dyl, rl)], char)
        for char in word)


def flatten(node):
    """Flatten the text of a node and its children."""
    flattened_text = [node.text or '']
    for child in list(node):
        flattened_text.append(flatten(child))
        flattened_text.append(child.tail or '')
        node.remove(child)
    return ''.join(flattened_text)


