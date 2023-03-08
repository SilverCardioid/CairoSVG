import re
import typing as ty

import cairocffi as cairo

from . import namespaces as ns

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

def normalize(string:str) -> str:
	"""Normalize a string corresponding to an array of various values."""
	string = string.replace('E', 'e')
	string = re.sub('(?<!e)-', ' -', string)
	string = re.sub('[ \n\r\t,]+', ' ', string)
	string = re.sub(r'(\.[0-9-]+)(?=\.)', r'\1 ', string)
	return string.strip()

def merge(kwargs:dict, **posargs) -> dict:
	"""Return a copy of a dict of attributes with positional arguments inserted at the start"""
	attribs = {}
	for attrib, value in posargs.items():
		if value is not None:
			attribs[attrib] = value
	attribs.update(kwargs)
	return attribs

camelCaseAttribs = set(['allowReorder','attributeName','attributeType','autoReverse','baseFrequency','baseProfile','calcMode','clipPathUnits','contentScriptType','contentStyleType','diffuseConstant','edgeMode','externalResourcesRequired','filterRes','filterUnits','glyphRef','gradientTransform','gradientUnits','kernelMatrix','kernelUnitLength','keyPoints','keySplines','keyTimes','lengthAdjust','limitingConeAngle','markerHeight','markerUnits','markerWidth','maskContentUnits','maskUnits','numOctaves','pathLength','patternContentUnits','patternTransform','patternUnits','pointsAtX','pointsAtY','pointsAtZ','preserveAlpha','preserveAspectRatio','primitiveUnits','refX','refY','referrerPolicy','repeatCount','repeatDur','requiredExtensions','requiredFeatures','specularConstant','specularExponent','spreadMethod','startOffset','stdDeviation','stitchTiles','surfaceScale','systemLanguage','tableValues','targetX','targetY','textLength','viewBox','viewTarget','xChannelSelector','yChannelSelector','zoomAndPan'])
nameSpaceAttribs = {'base':ns.NS_XML, 'lang':ns.NS_XML, 'space':ns.NS_XML, 'type':ns.NS_XLINK, 'href':ns.NS_XLINK, 'role':ns.NS_XLINK, 'arcrole':ns.NS_XLINK, 'title':ns.NS_XLINK, 'show':ns.NS_XLINK, 'actuate':ns.NS_XLINK}
def parseAttribute(key:str, *, namespaces:ty.Optional[ns.Namespaces] = None,
                   defaultName:ty.Optional[str] = None) -> str:
	"""Convert a snake_case or camelCase function argument to a hyphenated SVG attribute, and expand namespaces"""
	nsName = ''
	if key in nameSpaceAttribs:
		nsName = nameSpaceAttribs[key]
	elif namespaces:
		nsName, key = namespaces.expandName(key, defaultName=defaultName)
		if nsName == ns.NS_SVG:
			# Omit {name} for SVG namespace
			nsName = ''

	key = key.replace('_','-')
	if key not in camelCaseAttribs:
		key = re.sub('(?<!^)(?=[A-Z])', '-', key).lower()
	return f'{{{nsName}}}{key}' if nsName else key

def getFloat(elem, attrName:str, defaultValue:ty.Optional[float] = None, *,
             range:ty.List[ty.Optional[float]] = [None, None], cascade:bool=False) -> ty.Optional[float]:
	"""Get an attribute value and parse it as a float, and check if it's in the allowed range if one is given"""
	if defaultValue is None:
		defaultValue = elem._defaults.get(attrName, None)
	val = elem.getAttribute(attrName, defaultValue, cascade=cascade)
	try:
		val = float(val)
		assert (range[0] is None or val >= range[0]) and \
		       (range[1] is None or val <= range[1])
		return val
	except (ValueError, AssertionError) as _:
		print(f'warning: invalid value "{val}" for {attrName}')
		return defaultValue

def getEnum(elem, attrName:str, valueDict:ty.Mapping[str, ty.Any],
            defaultValue:ty.Optional[str] = None, *, cascade:bool = True) -> ty.Any:
	"""Get an attribute value and check if is in a dict of allowed values, returning the corresponding value from the dict"""
	if defaultValue is None:
		defaultValue = elem._defaults[attrName]
	val = elem.getAttribute(attrName, defaultValue, cascade=cascade)
	try:
		return valueDict[val]
	except KeyError:
		print(f'warning: invalid value "{val}" for {attrName}')
		return valueDict[defaultValue]
