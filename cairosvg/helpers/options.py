import re
import typing as ty

class SVGOutputOptions:
	"""
	A container class for options for SVG code output.
	* `xml_declaration` (bool): include the declaration of the XML version
	    and encoding at the top of the SVG code
	* `namespace_declaration` (bool): include `xmlns:` attributes for
	    namespaces used in the tree on the root element
	* `indent` (str|None): whitespace string used for indentation
	* `newline` (str|None): whitespace string used between tags
	* `precision` (int|None): number of decimal places to round coordinates and
	    sizes to (if None, keep numeric values unchanged)
	"""
	def __init__(self, *,
	             xml_declaration:bool = True,
	             namespace_declaration:bool = True,
	             indent:ty.Optional[str] = '',
	             newline:ty.Optional[str] = '\n',
	             precision:ty.Optional[int] = None):
		self.xml_declaration = xml_declaration
		self.namespace_declaration = namespace_declaration
		self.indent = indent or ''
		self.newline = newline or ''
		self.precision = precision

	def _roundString(self, value:str) -> str:
		return _float_regex.sub(lambda m: self._roundNumber(float(m[0])), value)

	def _roundNumber(self, value:ty.Union[int, float]) -> str:
		return str(round(value, self.precision)).removesuffix('.0')

_float_regex = re.compile(r'(?<![\d.\-])\-?\d*\.\d+(?![\d.])')
_repr_format = SVGOutputOptions(namespace_declaration=False)