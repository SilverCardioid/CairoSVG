from csvg_import import cairosvg

def checkElem(elem, root=None, notRoot=None, eid=None):
	if root:
		assert elem.root is root
		assert elem._root is root._root
	if notRoot:
		assert elem not in notRoot.descendants()
		if elem.id:
			assert elem.id not in notRoot._root._ids

	if eid is not None:
		assert elem.id == eid
	if elem.id:
		assert elem.id in elem._root._ids

	if elem.parent:
		assert elem in elem.parent.children
		assert elem._root is elem.parent._root
	else:
		assert elem.root is elem

def checkChildren(elem, assertedNames):
	assert [(e.id or e.tag) for e in elem.children] == assertedNames

def checkTarget(elem, target=None, notTarget=None):
	assert elem.target is target
	if target:
		refs = target.get_references()
		assert any(ref[0] is elem for ref in refs)
	if notTarget:
		refs = notTarget.get_references()
		assert not any(ref[0] is elem for ref in refs)

svg = cairosvg.SVG(600, 600)

rect = svg.rect(600, 600, fill='#ffe', id='rect')
checkElem(rect, root=svg)
path = svg.add_child('path', 'M0,0 600,600M0,600 600,0', stroke='#000', id='path')
checkElem(path, root=svg)

circle = cairosvg.elements.Circle(180, 300, 300, fill='#05a', id='circle', parent=svg, child_index=1)
checkElem(circle, root=svg)
checkChildren(svg, ['rect', 'circle', 'path'])

# Add g, move path to it, add use

g = cairosvg.elements.G(id='g')
checkElem(g, root=None, notRoot=svg)

g.add_child(path)
checkElem(path, root=g, notRoot=svg)
checkChildren(g, ['path'])

svg.add_child(g)
checkElem(g, root=svg)
checkElem(path, root=svg)
checkChildren(svg, ['rect', 'circle', 'g'])

use = g.use(href='#path', id='use')
checkElem(use, root=svg)
checkTarget(use, target=path)

# Create new set of g, path and use with the same ids, and add it to svg

g1 = cairosvg.elements.G(id='g')
checkElem(g1, root=None)

path1 = g1.add_child('path', 'M0,300H600M300,0V600', stroke='#000', id='path')
checkElem(path1, root=g1)

use1 = g1.use(href='#path', id='use')
checkElem(use1, root=g1)
checkTarget(use1, target=path1)
checkChildren(g1, ['path', 'use'])

svg.add_child(g1) # renames the duplicate IDs
checkElem(g1, root=svg, eid='g1')
checkElem(path1, root=svg, eid='path1')
checkElem(use1, root=svg, eid='use1')
checkTarget(use1, target=path1)
checkChildren(svg, ['rect', 'circle', 'g', 'g1'])

# Rename path, and detach it by deleting g

path.change_id('path2')
checkTarget(use, target=path)

path.change_id('path3', update_references=False)
checkTarget(use, target=None, notTarget=path)

g.delete(recursive=False)
checkElem(path, root=None, notRoot=svg)
checkElem(use, root=None, notRoot=svg)
checkChildren(svg, ['rect', 'circle', 'g1'])
