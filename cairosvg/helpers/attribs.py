import re

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

def normalize(string):
    """Normalize a string corresponding to an array of various values."""
    string = string.replace('E', 'e')
    string = re.sub('(?<!e)-', ' -', string)
    string = re.sub('[ \n\r\t,]+', ' ', string)
    string = re.sub(r'(\.[0-9-]+)(?=\.)', r'\1 ', string)
    return string.strip()

camelCaseAttribs = set(['allowReorder','attributeName','attributeType','autoReverse','baseFrequency','baseProfile','calcMode','clipPathUnits','contentScriptType','contentStyleType','diffuseConstant','edgeMode','externalResourcesRequired','filterRes','filterUnits','glyphRef','gradientTransform','gradientUnits','kernelMatrix','kernelUnitLength','keyPoints','keySplines','keyTimes','lengthAdjust','limitingConeAngle','markerHeight','markerUnits','markerWidth','maskContentUnits','maskUnits','numOctaves','pathLength','patternContentUnits','patternTransform','patternUnits','pointsAtX','pointsAtY','pointsAtZ','preserveAlpha','preserveAspectRatio','primitiveUnits','refX','refY','referrerPolicy','repeatCount','repeatDur','requiredExtensions','requiredFeatures','specularConstant','specularExponent','spreadMethod','startOffset','stdDeviation','stitchTiles','surfaceScale','systemLanguage','tableValues','targetX','targetY','textLength','viewBox','viewTarget','xChannelSelector','yChannelSelector','zoomAndPan'])
nameSpaceAttribs = {'base':ns.NS_XML, 'lang':ns.NS_XML, 'space':ns.NS_XML, 'type':ns.NS_XLINK, 'href':ns.NS_XLINK, 'role':ns.NS_XLINK, 'arcrole':ns.NS_XLINK, 'title':ns.NS_XLINK, 'show':ns.NS_XLINK, 'actuate':ns.NS_XLINK}
def parseAttribute(key, *, namespaces=None, defaultName=None):
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
