import typing as ty

from . import namespaces as ns

if ty.TYPE_CHECKING:
	from ..elements.element import _ElemType

class Root:
	def __init__(self, element:'_ElemType', namespaces=None):
		self.element = element
		self._ids = {}
		if namespaces is not None:
			self.namespaces = ns.Namespaces(namespaces)
		else:
			self.namespaces = ns.DEFAULTS.copy()

	def _update_ids(self):
		self._ids = {}
		for e in self.element.descendants(True, elements_only=True):
			eid = e.id
			if eid:
				self._ids[eid] = e
