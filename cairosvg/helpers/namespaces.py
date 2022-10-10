import re

NS_SVG = 'http://www.w3.org/2000/svg'
NS_XLINK = 'http://www.w3.org/1999/xlink'
NS_XML = 'http://www.w3.org/XML/1998/namespace'

_RGX_ATTRIB = re.compile(r'^(?:\{([^\{\}]+)\}|([^\{\}:]+):)?(.*?)$')
def _split(attrib):
	m = _RGX_ATTRIB.match(attrib)
	# nsName, nsPrefix, localName (first two are mutually exclusive)
	# (https://www.w3.org/TR/xml-names/ for terminology)
	return m[1], m[2], m[3]

# https://stackoverflow.com/questions/3318625/how-to-implement-an-efficient-bidirectional-hash-table
class Namespaces(dict):
	def __init__(self, nsMapping=None, *, default=NS_SVG):
		super().__init__()
		self.default = default
		self._names = {}
		if nsMapping:
			for key in nsMapping:
				self[key] = nsMapping[key]

	def __setitem__(self, key, value):
		if key in self:
			oldValue = self[key]
			self._names[oldValue].remove(key) 
			if not self._names[oldValue]: 
				del self._names[oldValue]
		super().__setitem__(key, value)
		self._names.setdefault(value, []).append(key)        

	def __delitem__(self, key):
		value = self[key]
		if value in self._names:
			self._names[value].remove(key)
			if not self._names[value]: 
				del self._names[value]
		super().__delitem__(key)

	def copy(self):
		return Namespaces(self)

	def fromPrefix(self, prefix):
		""" Get the namespace name (a URI) bound to a namespace prefix """
		return self.get(prefix, None)

	def fromName(self, name):
		""" Get the namespace prefixes bound to a namespace name """
		return self._names.get(name, [])

	def changePrefix(self, old, new):
		self[new] = self[old]
		del self[old]

	def _getPrefix(self, name, *, defaultName=None, defPrefix='ns'):
		# Get the last-declared prefix for a name, or
		# add one if the name is missing
		if (defaultName or self.default) == name:
			return ''
		prefixes = self.fromName(name)
		if len(prefixes) > 0:
			return prefixes[-1]

		defCount = 0
		if defPrefix[-1].isnumeric():
			# Add a separator if the prefix ends in a number
			defPrefix += '_'
		prefix = defPrefix + str(defCount)
		while prefix in self:
			defCount += 1
			prefix = defPrefix + str(defCount)
		self[prefix] = name
		return prefix

	def expandName(self, attrib, *, defaultName=None):
		""" Get a tuple (nsName, localName) from the qualified name "nsPrefix:localName" """
		nsName, nsPrefix, localName = _split(attrib)
		if nsName:
			# Already explanded name
			return nsName, localName
		if not nsPrefix:
			# Local name only: default namespace
			nsName = defaultName or self.default
			return nsName, localName

		# Qualified name
		nsName = self.fromPrefix(nsPrefix)
		if nsName is None:
			if nsPrefix in DEFAULTS:
				# Undeclared standard namespace (e.g. xlink); silently add
				nsName = DEFAULTS[nsPrefix]
				self[nsPrefix] = nsName
			else:
				print(f'warning: undeclared namespace "{ns}:" not expanded')
				localName = nsPrefix + ':' + localName
				nsPrefix = ''
		return nsName, localName

	def qualifyName(self, attrib, *, defaultName=None):
		""" Get a qualified name "nsPrefix:localName" from the expanded name "{nsName}localName" """
		nsName, nsPrefix, localName = _split(attrib)
		if nsPrefix:
			# Already qualified name
			return attrib
		prefix = self._getPrefix(nsName or NS_SVG, defaultName=defaultName)
		if prefix: prefix += ':'
		return prefix + localName


DEFAULTS = Namespaces({
	'svg'  : NS_SVG,
	'xlink': NS_XLINK,
	'xml'  : NS_XML
})


def getNamespaces(elem):
	# Find the namespaces actually used by elem's descendants
	nsNames = set()
	for e in elem.descendants():
		if e.namespace:
			nsNames.add(e.namespace)
		for attrib in e._attribs.keys():
			nsName, nsPrefix, localName = _split(attrib)
			if nsName:
				nsNames.add(nsName)
			elif not nsPrefix:
				# Attribs without {nsName} default to SVG
				nsNames.add(NS_SVG)

	return sorted(list(nsNames))
