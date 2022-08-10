class Root:
	def __init__(self, element):
		self.element = element
		self._ids = {}

	def _updateIDs(self):
		self._ids = {}
		for e in self.element.descendants():
			eid = e.id
			if eid:
				self._ids[eid] = e
