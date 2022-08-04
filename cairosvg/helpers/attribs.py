import re

import cairocffi as cairo

NAMESPACES = {
	'xmlns': 'http://www.w3.org/2000/svg',
	'svg'  : 'http://www.w3.org/2000/svg',
	'xlink': 'http://www.w3.org/1999/xlink',
	'xml'  : None
}

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
nameSpaceAttribs = {'base':'xml', 'lang':'xml', 'space':'xml', 'type':'xlink', 'href':'xlink', 'role':'xlink', 'arcrole':'xlink', 'title':'xlink', 'show':'xlink', 'actuate':'xlink'}
def parseAttribute(key):
	"""Convert a snake_case or camelCase function argument to a hyphenated SVG attribute"""
	key = key.replace('_','-')
	if key in nameSpaceAttribs:
		key = nameSpaceAttribs[key] + ':' + key
	if key not in camelCaseAttribs:
		key = re.sub('(?<!^)(?=[A-Z])', '-', key).lower()
	return key

def getNamespaces(elem):
	ns = set()
	for e in elem.descendants():
		if ':' in e.tag:
			ns.add(e.tag.split(':', 2)[0])
		for attrib in e._attribs.keys():
			if ':' in attrib:
				ns.add(attrib.split(':', 2)[0])
	return sorted(list(ns))
