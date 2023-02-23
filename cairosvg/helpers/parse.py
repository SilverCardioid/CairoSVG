from xml.etree import ElementTree as ET

from ..elements import _creators
from . import namespaces

def parse(source):
	events = ET.iterparse(source, events=["start", "end", "comment", "pi", "start-ns", "end-ns"])
	elemStack = []

	nextEv, nextElem = next(events, (None, None))
	while nextEv:
		newNS = {}
		while nextEv == 'start-ns':
			newNS[nextElem[0]] = nextElem[1]
			nextEv, nextElem = next(events, (None, None))
		if newNS:
			assert nextEv == 'start'

		if nextEv == 'start':
			# Create element
			nsName, nsPrefix, tag = namespaces._split(nextElem.tag)
			if nsPrefix:
				# Undefined prefix; keep prefix in tag
				print(f'undefined namespace prefix "{nsPrefix}:"')
				tag = nsPrefix + ':' + tag
			parent = elemStack[-1] if len(elemStack) > 0 else None
			if nsName == namespaces.NS_SVG and tag in _creators:
				elem = _creators[tag](parent, **nextElem.attrib)
			else:
				# Custom element
				print(f'<{nextElem.tag}> node not supported; can be saved but not drawn')
				elem = _creators['custom'](parent, tag, nsName, **nextElem.attrib)
			elemStack.append(elem)

			if newNS:
				# Add declared namespaces
				ns = elem._root.namespaces
				if not elem.isRoot():
					print('namespace declarations moved to root element')
				for nsPrefix, nsName in newNS.items():
					if nsPrefix in ns:
						if ns[nsPrefix] != nsName:
							# Same prefix for different name
							newPrefix = ns._getPrefix(nsName, defPrefix=nsPrefix)
							print(f'duplicate prefix "{nsPrefix}:" changed to "{newPrefix}:"')
						# else, already included with same name
						continue
					# Add new prefix
					ns[nsPrefix] = nsName
			yield ('start', elem)

		elif nextEv == 'end':
			yield ('end', elemStack.pop())

		# todo: comments (nextEv == 'comment'), text nodes (nextElem.text / nextElem.tail)

		nextEv, nextElem = next(events, (None, None))


def read(source):
	elemIt = parse(source)
	# First element = root
	ev, root = next(elemIt, (None, None))
	# Parse the rest of the tree
	while ev:
		ev, elem = next(elemIt, (None, None))
		if ev == 'start' and elem.isRoot():
			print(f'multiple root-level elements')
	return root
