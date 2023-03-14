from __future__ import annotations
import re
import typing as ty

from . import attribs
# .transform dynamically imported to avoid mutual imports

Length = ty.Union[str, int, float]

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

	def __init__(self, width:ty.Optional[Length] = None,
	             height:ty.Optional[Length] = None, *,
	             viewBox:ty.Optional[str] = None,
	             preserveAspectRatio:ty.Optional[str] = None,
	             parent:ty.Optional['Element'] = None):
		self.parent = parent
		defs = parent._defaults if parent else {}
		self._attribs = {
			'width': width, 'height': height, 'viewBox': viewBox,
			'preserveAspectRatio': preserveAspectRatio
		}
		for attrib in self._attribs.keys():
			if self._attribs[attrib] is None:
				if self.parent:
					self._attribs[attrib] = self.parent._getattrib(attrib)
				else:
					self._attribs[attrib] = self._defaults[attrib]

	@property
	def width(self) -> float:
		return size(self._attribs['width'],
		            self.parent and self.parent._get_viewport(),
		            'x', auto_value='100%')

	@property
	def height(self) -> float:
		return size(self._attribs['height'],
		            self.parent and self.parent._get_viewport(),
		            'y', auto_value='100%')

	@property
	def viewBox(self) -> ty.Optional[ty.Tuple[float, float, float, float]]:
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
	def inner_size(self) -> ty.Tuple[float, float]:
		vb = self.viewBox
		if vb:
			return vb[2:]
		else:
			return (self.width, self.height)

	def get_absolute_size(self, default_width:float = 1000,
	                      default_height:float = 1000) -> ty.Tuple[float, float]:
		"""Get the viewport's absolute width and height.
		If either is zero, 'auto' or a percentage and there is no
		ancestor viewport with an absolute size, calculate them from the
		viewBox's aspect ratio and the one dimension with an absolute size.
		If both are, calculate them from the viewBox ratio and `default_width`.
		If there is no viewBox, return `(default_width, default_height)`.
		"""
		width, height = self.width, self.height
		if width > 0 and height > 0:
			return (width, height)

		# Calculate aspect ratio from viewBox
		vb = self.viewBox
		if vb is not None and vb[2] != 0 and vb[3] != 0:
			hw_ratio = vb[3] / vb[2]
			if width > 0:
				return (width, hw_ratio*width)
			if height > 0:
				return (height/hw_ratio, height)
			return (default_width, hw_ratio*default_width)

		return (default_width, default_height)

	def get_transform(self) -> transform.Transform:
		"""Return a Transform object based on the viewport's viewBox and preserveAspectRatio values."""
		from . import transform
		tr = transform.Transform()
		vb = self.viewBox
		if vb:
			# Manage the ratio preservation
			width, height = self.get_absolute_size()
			vb_width, vb_height = vb[2:]

			translate_x = 0
			translate_y = 0
			scale_x = width / vb_width if vb_width > 0 else 1
			scale_y = height / vb_height if vb_height > 0 else 1

			aspect_ratio = self._attribs.get('preserveAspectRatio', 'xMidYMid').split()
			align = aspect_ratio[0]
			if align == 'none':
				# Non-uniform scale
				x_position = 'min'
				y_position = 'min'
			else:
				# Uniform scale
				meet_or_slice = aspect_ratio[1] if len(aspect_ratio) > 1 else None
				if meet_or_slice == 'slice':
					scale_value = max(scale_x, scale_y)
				else:
					scale_value = min(scale_x, scale_y)
				scale_x = scale_y = scale_value
				x_position = align[1:4].lower()
				y_position = align[5:].lower()
			tr._scale(scale_x, scale_y)

			translate_x = 0
			if x_position == 'mid':
				translate_x = (width / scale_x - vb_width) / 2
			elif x_position == 'max':
				translate_x = width / scale_x - vb_width
			translate_y = 0
			if y_position == 'mid':
				translate_y += (height / scale_y - vb_height) / 2
			elif y_position == 'max':
				translate_y += height / scale_y - vb_height
			tr._translate(translate_x, translate_y)

		return tr

def size(string:Length, viewport:ty.Optional[Viewport] = None,
         reference:str = 'xy', *, units:bool = True, auto_value:Length = 0,
         font_size:ty.Optional[float] = None, dpi:float = 96) -> float:
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

	if font_size is None: # default 12pt
		font_size = 12 * UNITS['pt'] * dpi

	string = attribs.normalize(string).split(' ', 1)[0]
	if string == 'auto':
		string = str(auto_value)

	if string.endswith('%'):
		if isinstance(reference, str):
			# reference in ('x', 'y', 'xy'): use viewport size
			if not viewport:
				return 0
			ref_width, ref_height = viewport.inner_size
			if reference == 'x':
				reference = ref_width
			elif reference == 'y':
				reference = ref_height
			elif reference == 'xy':
				reference = ((ref_width**2 + ref_height**2) / 2) ** .5
			else:
				# invalid string value
				reference = 0
		return float(string[:-1]) * reference / 100

	elif string.endswith('em'):
		return font_size * float(string[:-2])

	elif string.endswith('ex'):
		# Assume that 1em == 2ex
		return font_size * float(string[:-2]) / 2

	for unit, coefficient in UNITS.items():
		if string.endswith(unit):
			number = float(string[:-len(unit)])
			return number * (dpi * coefficient if coefficient else 1)

	# Unknown size
	return 0

def point(string:str, viewport:ty.Optional[Viewport] = None, *,
          units:bool = True) -> ty.Tuple[float, float, str]:
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
