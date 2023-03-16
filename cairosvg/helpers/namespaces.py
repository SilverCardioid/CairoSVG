import re
import typing as ty

NS_SVG = 'http://www.w3.org/2000/svg'
NS_XLINK = 'http://www.w3.org/1999/xlink'
NS_XML = 'http://www.w3.org/XML/1998/namespace'

_RGX_ATTRIB = re.compile(r'^(?:\{([^\{\}]+)\}|([^\{\}:]+):)?(.*?)$')
def _split(attrib):
	m = _RGX_ATTRIB.match(attrib)
	# ns_name, ns_prefix, local_name (first two are mutually exclusive)
	# (https://www.w3.org/TR/xml-names/ for terminology)
	return m[1], m[2], m[3]

# https://stackoverflow.com/questions/3318625/how-to-implement-an-efficient-bidirectional-hash-table
class Namespaces(dict):
	def __init__(self, ns_mapping:ty.Mapping[str, str] = None, *,
	             default:str = NS_SVG):
		super().__init__()
		self.default = default
		self._names = {}
		if ns_mapping:
			for key in ns_mapping:
				self[key] = ns_mapping[key]

	def __setitem__(self, key:str, value:str):
		if key in self:
			old_value = self[key]
			self._names[old_value].remove(key) 
			if not self._names[old_value]: 
				del self._names[old_value]
		super().__setitem__(key, value)
		self._names.setdefault(value, []).append(key)        

	def __delitem__(self:str, key:str):
		value = self[key]
		if value in self._names:
			self._names[value].remove(key)
			if not self._names[value]: 
				del self._names[value]
		super().__delitem__(key)

	def copy(self):
		return Namespaces(self)

	def from_prefix(self, prefix:str) -> ty.Optional[str]:
		""" Get the namespace name (a URI) bound to a namespace prefix """
		return self.get(prefix, None)

	def from_name(self, name:str) -> ty.List[str]:
		""" Get the namespace prefixes bound to a namespace name """
		return self._names.get(name, [])

	def change_prefix(self, old:str, new:str):
		self[new] = self[old]
		del self[old]

	def _get_prefix(self, name:str, *, default_name:ty.Optional[str] = None,
	                default_prefix:ty.Optional[str] = 'ns'):
		# Get the last-declared prefix for a name, or
		# add one if the name is missing
		if (default_name or self.default) == name:
			return ''
		prefixes = self.from_name(name)
		if len(prefixes) > 0:
			return prefixes[-1]

		def_count = 0
		default_prefix = default_prefix or 'ns'
		if default_prefix[-1].isnumeric():
			# Add a separator if the prefix ends in a number
			default_prefix += '_'
		prefix = default_prefix + str(def_count)
		while prefix in self:
			def_count += 1
			prefix = default_prefix + str(def_count)
		self[prefix] = name
		return prefix

	def expand_name(self, attrib:str, *, default_name:ty.Optional[str] = None):
		""" Get a tuple (ns_name, local_name) from the qualified name "prefix:local_name" """
		ns_name, ns_prefix, local_name = _split(attrib)
		if ns_name:
			# Already explanded name
			return ns_name, local_name
		if not ns_prefix:
			# Local name only: default namespace
			ns_name = default_name or self.default
			return ns_name, local_name

		# Qualified name
		ns_name = self.from_prefix(ns_prefix)
		if ns_name is None:
			if ns_prefix in DEFAULTS:
				# Undeclared standard namespace (e.g. xlink); silently add
				ns_name = DEFAULTS[ns_prefix]
				self[ns_prefix] = ns_name
			else:
				print(f'warning: undeclared namespace "{ns}:" not expanded')
				local_name = ns_prefix + ':' + local_name
				ns_prefix = ''
		return ns_name, local_name

	def qualify_name(self, attrib:str, *, default_name:ty.Optional[str] = None):
		""" Get a qualified name "prefix:local_name" from the expanded name "{ns_name}local_name" """
		ns_name, ns_prefix, local_name = _split(attrib)
		if ns_prefix:
			# Already qualified name
			return attrib
		prefix = self._get_prefix(ns_name or NS_SVG, default_name=default_name)
		if prefix: prefix += ':'
		return prefix + local_name


DEFAULTS = Namespaces({
	'svg'  : NS_SVG,
	'xlink': NS_XLINK,
	'xml'  : NS_XML
})


def get_namespaces(elem) -> ty.List[str]:
	# Find the namespaces actually used by elem's descendants
	ns_names = set()
	for e in elem.descendants(True, elements_only=True):
		if e.namespace:
			ns_names.add(e.namespace)
		for attrib in e._attribs.keys():
			ns_name, ns_prefix, local_name = _split(attrib)
			if ns_name:
				ns_names.add(ns_name)
			elif not ns_prefix:
				# Attribs without {ns_name} default to SVG
				ns_names.add(NS_SVG)

	return sorted(list(ns_names))
