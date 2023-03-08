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
	_defaults = {
		'width': 'auto',
		'height': 'auto',
		'viewBox': 'none',
		'preserveAspectRatio': 'xMidYMid meet'
	}

	def __init__(self, width=None, height=None, *, viewBox=None,
	             preserveAspectRatio=None, parent=None):
		self.parent = parent
		defs = parent._defaults if parent else {}
		self._attribs = {
			'width': width, 'height': height, 'viewBox': viewBox,
			'preserveAspectRatio': preserveAspectRatio
		}
		for attrib in self._attribs.keys():
			if self._attribs[attrib] is None:
				if self.parent:
					self._attribs[attrib] = self.parent.getAttribute(
						attrib, self._defaults[attrib], getDefault=True)
				else:
					self._attribs[attrib] = self._defaults[attrib]

	@property
	def width(self):
		return size(self._attribs['width'], self.parent and self.parent._getViewport(), 'x', autoValue='100%')

	@property
	def height(self):
		return size(self._attribs['height'], self.parent and self.parent._getViewport(), 'y', autoValue='100%')

	@property
	def viewBox(self):
		vb = self._attribs['viewBox']
		if vb in (None, 'none'):
			return None
		elif isinstance(vb, str):
			# vb = re.sub('[ \n\r\t,]+', ' ', vb)
			vb = attribs.normalize(vb)
			vb = tuple(size(position, units=False) for position in vb.split())
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

def size(string, viewport=None, reference='xy', *, units=True, autoValue=0, fontSize=None, dpi=96):
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

def point(string, viewport=None, *, units=True):
	"""Return ``(x, y, trailing_text)`` from ``string``."""
	match = re.match('(.*?) (.*?)(?: |$)', string)
	if match:
		x, y = match.group(1, 2)
		string = string[match.end():]
		return (size(x, viewport, 'x', units=units),
		        size(y, viewport, 'y', units=units),
		        string)
	else:
		raise PointError


def node_format(node, viewport=None, reference=True):
    """Return ``(width, height, viewbox)`` of ``node``.

    If ``reference`` is ``True``, we can rely on surface size to resolve
    percentages.

    """
    reference_size = 'xy' if reference else (0, 0)
    width = size(node.get('width', '100%'), viewport, reference_size[0])
    height = size(node.get('height', '100%'), viewport, reference_size[1])
    viewbox = node.get('viewBox')
    if viewbox:
        viewbox = re.sub('[ \n\r\t,]+', ' ', viewbox)
        viewbox = tuple(float(position) for position in viewbox.split())
        width = width or viewbox[2]
        height = height or viewbox[3]
    return width, height, viewbox
