from . import namespaces as ns

class Root:
	def __init__(self, element, namespaces=None):
		self.element = element
		self._ids = {}
		if namespaces is not None:
			self.namespaces = ns.Namespaces(namespaces)
		else:
			self.namespaces = ns.DEFAULTS.copy()

	def _updateIDs(self):
		self._ids = {}
		for e in self.element.descendants():
			eid = e.id
			if eid:
				self._ids[eid] = e
