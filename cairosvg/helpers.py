"""
Surface helpers.

"""

import re
from math import atan2, cos, radians, sin, tan

import cairocffi as cairo
#from .parse.url import parse_url

UNITS = {
    'mm': 1 / 25.4,
    'cm': 1 / 2.54,
    'in': 1,
    'pt': 1 / 72.,
    'pc': 1 / 6.,
    'px': None,
}

PAINT_URL = re.compile(r'(url\(.+\)) *(.*)')
PATH_LETTERS = 'achlmqstvzACHLMQSTVZ'
RECT = re.compile(r'rect\( ?(.+?) ?\)')

FILL_RULES = {
	'nonzero': cairo.FILL_RULE_WINDING,
	'evenodd': cairo.FILL_RULE_EVEN_ODD
}
LINE_CAPS = {
	'butt':   cairo.LINE_CAP_BUTT,
	'round':  cairo.LINE_CAP_ROUND,
	'square': cairo.LINE_CAP_SQUARE
}
LINE_JOINS = {
	'miter': cairo.LINE_JOIN_MITER,
	'round': cairo.LINE_JOIN_ROUND,
	'bevel': cairo.LINE_JOIN_BEVEL
}


class PointError(Exception):
    """Exception raised when parsing a point fails."""


def createSurface(surfaceType, width, height, filename=None):
	surfaceType = surfaceType.lower()
	if surfaceType in ['image', 'png']:
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
	elif surfaceType == 'pdf':
		surface = cairo.PDFSurface(filename, width, height)
	elif surfaceType in ['ps', 'postscript']:
		surface = cairo.PSSurface(filename, width, height)
	elif surfaceType == 'recording':
		surface = cairo.RecordingSurface(filename, (0, 0, width, height))
	elif surfaceType == 'svg':
		surface = cairo.SVGSurface(filename, width, height)
	else:
		raise ValueError('Unsupported surface type: {}'.format(surfaceType))
	surface.context = cairo.Context(surface)
	return surface



def distance(x1, y1, x2, y2):
    """Get the distance between two points."""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


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


def node_format(surface, node, reference=True):
    """Return ``(width, height, viewbox)`` of ``node``.

    If ``reference`` is ``True``, we can rely on surface size to resolve
    percentages.

    """
    reference_size = 'xy' if reference else (0, 0)
    width = size(surface, node.get('width', '100%'), reference_size[0])
    height = size(surface, node.get('height', '100%'), reference_size[1])
    viewbox = node.get('viewBox')
    if viewbox:
        viewbox = re.sub('[ \n\r\t,]+', ' ', viewbox)
        viewbox = tuple(float(position) for position in viewbox.split())
        width = width or viewbox[2]
        height = height or viewbox[3]
    return width, height, viewbox


def normalize(string):
    """Normalize a string corresponding to an array of various values."""
    string = string.replace('E', 'e')
    string = re.sub('(?<!e)-', ' -', string)
    string = re.sub('[ \n\r\t,]+', ' ', string)
    string = re.sub(r'(\.[0-9-]+)(?=\.)', r'\1 ', string)
    return string.strip()


camelCaseAttribs = set(['allowReorder','attributeName','attributeType','autoReverse','baseFrequency','baseProfile','calcMode','clipPathUnits','contentScriptType','contentStyleType','diffuseConstant','edgeMode','externalResourcesRequired','filterRes','filterUnits','glyphRef','gradientTransform','gradientUnits','kernelMatrix','kernelUnitLength','keyPoints','keySplines','keyTimes','lengthAdjust','limitingConeAngle','markerHeight','markerUnits','markerWidth','maskContentUnits','maskUnits','numOctaves','pathLength','patternContentUnits','patternTransform','patternUnits','pointsAtX','pointsAtY','pointsAtZ','preserveAlpha','preserveAspectRatio','primitiveUnits','refX','refY','referrerPolicy','repeatCount','repeatDur','requiredExtensions','requiredFeatures','specularConstant','specularExponent','spreadMethod','startOffset','stdDeviation','stitchTiles','surfaceScale','systemLanguage','tableValues','targetX','targetY','textLength','viewBox','viewTarget','xChannelSelector','yChannelSelector','zoomAndPan'])
def parseAttribute(key):
	"""Convert a snake_case or camelCase function argument to a hyphenated SVG attribute"""
	key = key.replace('_','-')
	if key not in camelCaseAttribs:
		key = re.sub('(?<!^)(?=[A-Z])', '-', key).lower()
	return key


def point(surface, string):
    """Return ``(x, y, trailing_text)`` from ``string``."""
    match = re.match('(.*?) (.*?)(?: |$)', string)
    if match:
        x, y = match.group(1, 2)
        string = string[match.end():]
        return (size(surface, x, 'x'), size(surface, y, 'y'), string)
    else:
        raise PointError


def point_angle(cx, cy, px, py):
    """Return angle between x axis and point knowing given center."""
    return atan2(py - cy, px - cx)


def preserve_ratio(surface, node, width=None, height=None):
    """Manage the ratio preservation."""
    if node.tag == 'marker':
        width = width or size(surface, node.get('markerWidth', '3'), 'x')
        height = height or size(surface, node.get('markerHeight', '3'), 'y')
        _, _, viewbox = node_format(surface, node)
        viewbox_width, viewbox_height = viewbox[2:]
    elif node.tag in ('svg', 'image', 'g'):
        node_width, node_height, _ = node_format(surface, node)
        width = width or node_width
        height = height or node_height
        viewbox_width, viewbox_height = node.image_width, node.image_height
    else:
        raise TypeError(
            ('Root node is {}. Should be one of '
             'marker, svg, image, or g.').format(node.tag))

    translate_x = 0
    translate_y = 0
    scale_x = width / viewbox_width if viewbox_width > 0 else 1
    scale_y = height / viewbox_height if viewbox_height > 0 else 1

    aspect_ratio = node.get('preserveAspectRatio', 'xMidYMid').split()
    align = aspect_ratio[0]
    if align == 'none':
        x_position = 'min'
        y_position = 'min'
    else:
        meet_or_slice = aspect_ratio[1] if len(aspect_ratio) > 1 else None
        if meet_or_slice == 'slice':
            scale_value = max(scale_x, scale_y)
        else:
            scale_value = min(scale_x, scale_y)
        scale_x = scale_y = scale_value
        x_position = align[1:4].lower()
        y_position = align[5:].lower()

    if node.tag == 'marker':
        translate_x = -size(surface, node.get('refX', '0'), 'x')
        translate_y = -size(surface, node.get('refY', '0'), 'y')
    else:
        translate_x = 0
        if x_position == 'mid':
            translate_x = (width / scale_x - viewbox_width) / 2
        elif x_position == 'max':
            translate_x = width / scale_x - viewbox_width

        translate_y = 0
        if y_position == 'mid':
            translate_y += (height / scale_y - viewbox_height) / 2
        elif y_position == 'max':
            translate_y += height / scale_y - viewbox_height

    return scale_x, scale_y, translate_x, translate_y


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


def clip_marker_box(surface, node, scale_x, scale_y):
    """Get the clip ``(x, y, width, height)`` of the marker box."""
    width = size(surface, node.get('markerWidth', '3'), 'x')
    height = size(surface, node.get('markerHeight', '3'), 'y')
    _, _, viewbox = node_format(surface, node)
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


def quadratic_points(x1, y1, x2, y2, x3, y3):
    """Return the quadratic points to create quadratic curves."""
    xq1 = x2 * 2 / 3 + x1 / 3
    yq1 = y2 * 2 / 3 + y1 / 3
    xq2 = x2 * 2 / 3 + x3 / 3
    yq2 = y2 * 2 / 3 + y3 / 3
    return xq1, yq1, xq2, yq2, x3, y3


def rotate(x, y, angle):
    """Rotate a point of an angle around the origin point."""
    return x * cos(angle) - y * sin(angle), y * cos(angle) + x * sin(angle)


def transform(surface, transform_string, gradient=None, transform_origin=None):
    """Transform ``surface`` or ``gradient`` if supplied using ``string``.

    See http://www.w3.org/TR/SVG/coords.html#TransformAttribute

    """
    if not transform_string:
        return

    transformations = re.findall(
        r'(\w+) ?\( ?(.*?) ?\)', normalize(transform_string))
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
            origin_x = size(surface, origin_x, 'x')

        if origin_y == 'center':
            origin_y = surface.height / 2
        elif origin_y == 'top':
            origin_y = 0
        elif origin_y == 'bottom':
            origin_y = surface.height
        else:
            origin_y = size(surface, origin_y, 'y')

        matrix.translate(float(origin_x), float(origin_y))

    for transformation_type, transformation in transformations:
        values = [size(surface, value) for value in transformation.split(' ')]
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
    match = RECT.search(normalize(string or ''))
    return match.group(1).split(' ') if match else []


def rotations(node):
    """Retrieves the original rotations of a `text` or `tspan` node."""
    if 'rotate' in node:
        original_rotate = [
            float(i) for i in normalize(node['rotate']).strip().split(' ')]
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


def size(surface, string, reference='xy'):
    """Replace a ``string`` with units by a float value.

    If ``reference`` is a float, it is used as reference for percentages. If it
    is ``'x'``, we use the viewport width as reference. If it is ``'y'``, we
    use the viewport height as reference. If it is ``'xy'``, we use
    ``(viewport_width ** 2 + viewport_height ** 2) ** .5 / 2 ** .5`` as
    reference.

    """
    if not string:
        return 0

    try:
        return float(string)
    except ValueError:
        # Not a float, try something else
        pass

    # No surface (for parsing only)
    if surface is None:
        return 0

    string = normalize(string).split(' ', 1)[0]
    if string.endswith('%'):
        if reference == 'x':
            reference = surface.context_width or 0
        elif reference == 'y':
            reference = surface.context_height or 0
        elif reference == 'xy':
            reference = (
                (surface.context_width ** 2 +
                 surface.context_height ** 2) ** .5 /
                2 ** .5)
        return float(string[:-1]) * reference / 100
    elif string.endswith('em'):
        return surface.font_size * float(string[:-2])
    elif string.endswith('ex'):
        # Assume that 1em == 2ex
        return surface.font_size * float(string[:-2]) / 2

    for unit, coefficient in UNITS.items():
        if string.endswith(unit):
            number = float(string[:-len(unit)])
            return number * (surface.dpi * coefficient if coefficient else 1)

    # Unknown size
    return 0
