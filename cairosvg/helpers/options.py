class SVGOutputOptions:
	"""
	A container class for options for SVG code output.
	* `xml_declaration` (bool):, include the declaration of the XML version
	    and encoding at the top of the SVG code
	* `namespace_declaration` (bool) include `xmlns:` attributes for
	    namespaces used in the tree on the root element
	* `indent` (str): whitespace string used for indentation
	* `newline` (str): whitespace string used between tags
	* `precision` (int): number of decimal places for coordinates and sizes
	"""
	def __init__(self,
	             xml_declaration:bool = True,
	             namespace_declaration:bool = True,
	             indent:str = '',
	             newline:str = '\n',
	             precision:int = 6):
		self.xml_declaration = xml_declaration
		self.namespace_declaration = namespace_declaration
		self.indent = indent or ''
		self.newline = newline or ''
		self.precision = precision

_repr_format = SVGOutputOptions(namespace_declaration=False)