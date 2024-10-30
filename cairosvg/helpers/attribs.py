import re
import typing as ty

import cairocffi as cairo

from . import namespaces as ns

if ty.TYPE_CHECKING:
	from ..elements.element import _Element

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

camelcase_attribs = set(['allowReorder','attributeName','attributeType','autoReverse','baseFrequency','baseProfile','calcMode','clipPathUnits','contentScriptType','contentStyleType','diffuseConstant','edgeMode','externalResourcesRequired','filterRes','filterUnits','glyphRef','gradientTransform','gradientUnits','kernelMatrix','kernelUnitLength','keyPoints','keySplines','keyTimes','lengthAdjust','limitingConeAngle','markerHeight','markerUnits','markerWidth','maskContentUnits','maskUnits','numOctaves','pathLength','patternContentUnits','patternTransform','patternUnits','pointsAtX','pointsAtY','pointsAtZ','preserveAlpha','preserveAspectRatio','primitiveUnits','refX','refY','referrerPolicy','repeatCount','repeatDur','requiredExtensions','requiredFeatures','specularConstant','specularExponent','spreadMethod','startOffset','stdDeviation','stitchTiles','surfaceScale','systemLanguage','tableValues','targetX','targetY','textLength','viewBox','viewTarget','xChannelSelector','yChannelSelector','zoomAndPan'])
namespaced_attribs = {'base':ns.NS_XML, 'lang':ns.NS_XML, 'space':ns.NS_XML, 'type':ns.NS_XLINK, 'href':ns.NS_XLINK, 'role':ns.NS_XLINK, 'arcrole':ns.NS_XLINK, 'title':ns.NS_XLINK, 'show':ns.NS_XLINK, 'actuate':ns.NS_XLINK}
url_attribs = set(['clip-path', 'mask'])

def normalize(string:str) -> str:
	"""Normalize a string corresponding to an array of various values."""
	string = string.replace('E', 'e')
	string = re.sub('(?<!e)-', ' -', string)
	string = re.sub('[ \n\r\t,]+', ' ', string)
	string = re.sub(r'(\.[0-9-]+)(?=\.)', r'\1 ', string)
	return string.strip()

def merge(kwargs:dict, **posargs) -> dict:
	"""Merge an element's keyword and positional attributes.
	Return a dict containing all items with non-None values from
	`posargs`, followed by all items from `kwargs`.
	"""
	attribs = {}
	for attrib, value in posargs.items():
		if value is not None:
			attribs[attrib] = value
	attribs.update(kwargs)
	return attribs

def parse_attribute(key:str, *, namespaces:ty.Optional[ns.Namespaces] = None,
                    default_name:ty.Optional[str] = None) -> str:
	"""Parse an attribute name.
	Convert camelCase and snake_case to hyphens (unless the attribute is
	normally camelCase, e.g. "viewBox"), and add missing xlink or xml
	namespaces to attributes like "href". If `namespaces` is provided,
	use it to expand namespace prefixes, using the given `default_name`
	(or `namespaces.default` if None) for attributes without a prefix.
	"""
	ns_name = ''
	if key in namespaced_attribs:
		ns_name = namespaced_attribs[key]
	elif namespaces:
		ns_name, key = namespaces.expand_name(key, default_name=default_name)
		if ns_name == ns.NS_SVG:
			# Omit {name} for SVG namespace
			ns_name = ''

	key = key.replace('_','-')
	if key not in camelcase_attribs:
		key = re.sub('(?<!^)(?=[A-Z])', '-', key).lower()
	return f'{{{ns_name}}}{key}' if ns_name else key

def get_float(elem:'_Element', attrib:str, default:ty.Optional[float] = None, *,
              range:ty.List[ty.Optional[float]] = [None, None],
              cascade:bool=False) -> ty.Optional[float]:
	"""Get an attribute value and parse it as a float.
	Check if it's in the allowed range if one is given."""
	if default is None:
		default = elem.__class__._defaults.get(attrib, None)
	val = elem.get_attribute(attrib, default, cascade=cascade)
	try:
		val = float(val)
		assert (range[0] is None or val >= range[0]) and \
		       (range[1] is None or val <= range[1])
		return val
	except (ValueError, AssertionError) as _:
		print(f'warning: invalid value "{val}" for {attrib}')
		return default

def get_enum(elem:'_Element', attrib:str, values:ty.Mapping[str, ty.Any],
            default:ty.Optional[str] = None, *, cascade:bool = True) -> ty.Any:
	"""Get an attribute value and check if is in a dict of allowed values.
	Return the corresponding value from the dict."""
	if default is None:
		default = elem.__class__._defaults[attrib]
	val = elem.get_attribute(attrib, default, cascade=cascade)
	try:
		return values[val]
	except KeyError:
		print(f'warning: invalid value "{val}" for {attrib}')
		return values[default]
