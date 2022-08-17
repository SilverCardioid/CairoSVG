import re

from . import attribs # transform dynamically imported to avoid mutual imports

UNITS = {
    'mm': 1 / 25.4,
    'cm': 1 / 2.54,
    'in': 1,
    'pt': 1 / 72.,
    'pc': 1 / 6.,
    'px': None,
}

class Viewport:
	def __init__(self, width='auto', height='auto', *, viewBox='none',
	             preserveAspectRatio='xMidYMid meet', parent=None):
		self.parent = parent
		self._attribs = {
			'width':               width,
			'height':              height,
			'viewBox':             viewBox,
			'preserveAspectRatio': preserveAspectRatio
		}

	@property
	def width(self):
		return size2(self._attribs['width'], self.parent._getViewport(), 'x', autoValue='100%')

	@property
	def height(self):
		return size2(self._attribs['height'], self.parent._getViewport(), 'y', autoValue='100%')

	@property
	def viewBox(self):
		vb = self._attribs['viewBox']
		if vb in (None, 'none'):
			return None
		elif isinstance(vb, str):
			# vb = re.sub('[ \n\r\t,]+', ' ', vb)
			vb = attribs.normalize(vb)
			vb = tuple(size2(position, units=False) for position in vb.split())
			assert len(vb) == 4
			return vb
		# unknown type
		return None

	@property
	def viewBoxSize(self):
		vb = self.viewBox
		if vb:
			return vb[2:]
		else:
			return (self.width, self.height)

	def getTransform(self):
		"""Return a Transform object based on the viewport's viewBox and preserveAspectRatio values."""
		from . import transform
		tr = transform.Transform()
		vb = self.viewBox
		if vb:
			# Manage the ratio preservation
			width, height = self.width, self.height
			vbWidth, vbHeight = vb[2:]

			translateX = 0
			translateY = 0
			scaleX = width / vbWidth if vbWidth > 0 else 1
			scaleY = height / vbHeight if vbHeight > 0 else 1

			aspectRatio = self._attribs.get('preserveAspectRatio', 'xMidYMid').split()
			align = aspectRatio[0]
			if align == 'none':
				# Non-uniform scale
				xPosition = 'min'
				yPosition = 'min'
			else:
				# Uniform scale
				meetOrSlice = aspectRatio[1] if len(aspectRatio) > 1 else None
				if meetOrSlice == 'slice':
					scaleValue = max(scaleX, scaleY)
				else:
					scaleValue = min(scaleX, scaleY)
				scaleX = scaleY = scaleValue
				xPosition = align[1:4].lower()
				yPosition = align[5:].lower()
			tr._scale(scaleX, scaleY)

			translateX = 0
			if xPosition == 'mid':
				translateX = (width / scaleX - vbWidth) / 2
			elif xPosition == 'max':
				translateX = width / scaleX - vbWidth
			translateY = 0
			if yPosition == 'mid':
				translateY += (height / scaleY - vbHeight) / 2
			elif yPosition == 'max':
				translateY += height / scaleY - vbHeight
			tr._translate(translateX, translateY)

		return tr

def size2(string, viewport=None, reference='xy', *, units=True, autoValue=0, fontSize=None, dpi=96):
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
		# Not a float, try parsing units or reraise error
		if units:
			pass
		else:
			raise ValueError(f'invalid number: {string}')

	if fontSize is None: # default 12pt
		fontSize = 12 * UNITS['pt'] * dpi

	if string.split() == 'auto':
		string = str(autoValue)

	string = attribs.normalize(string).split(' ', 1)[0]
	if string.endswith('%'):
		if isinstance(reference, str):
			# reference in ('x', 'y', 'xy'): use viewport size
			if not viewport:
				return 0
			refWidth, refHeight = viewport.viewBoxSize
			if reference == 'x':
				reference = refWidth
			elif reference == 'y':
				reference = refHeight
			elif reference == 'xy':
				reference = ((refWidth**2 + refHeight**2) / 2) ** .5
			else:
				# invalid string value
				reference = 0
		return float(string[:-1]) * reference / 100

	elif string.endswith('em'):
		return fontSize * float(string[:-2])

	elif string.endswith('ex'):
		# Assume that 1em == 2ex
		return fontSize * float(string[:-2]) / 2

	for unit, coefficient in UNITS.items():
		if string.endswith(unit):
			number = float(string[:-len(unit)])
			return number * (dpi * coefficient if coefficient else 1)

	# Unknown size
	return 0

def point2(string, viewport=None, *, units=True):
	"""Return ``(x, y, trailing_text)`` from ``string``."""
	match = re.match('(.*?) (.*?)(?: |$)', string)
	if match:
		x, y = match.group(1, 2)
		string = string[match.end():]
		return (size2(x, viewport, 'x', units=units),
		        size2(y, viewport, 'y', units=units),
		        string)
	else:
		raise PointError


## Original functions

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


def point(surface, string):
    """Return ``(x, y, trailing_text)`` from ``string``."""
    match = re.match('(.*?) (.*?)(?: |$)', string)
    if match:
        x, y = match.group(1, 2)
        string = string[match.end():]
        return (size(surface, x, 'x'), size(surface, y, 'y'), string)
    else:
        raise PointError


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

    string = attribs.normalize(string).split(' ', 1)[0]
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

