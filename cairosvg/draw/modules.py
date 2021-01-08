attrib = [
	'Core':['id','xml:base','xml:lang','xml:space'],
	'Container':['enable-background'],
	'Conditional':['requiredFeatures','requiredExtensions','systemLanguage'],
	'Style':['style','class'],
	'Viewport':['clip','overflow'],
	'Text':['writing-mode'],
	'TextContent':['alignment-baseline','baseline-shift','direction','dominant-baseline','glyph-orientation-horizontal','glyph-orientation-vertical','kerning','letter-spacing','text-anchor','text-decoration','unicode-bidi','word-spacing'],
	'Font':['font-family','font-size','font-size-adjust','font-stretch','font-style','font-variant','font-weight'],
	'Paint':['color','fill','fill-rule','stroke','stroke-dasharray','stroke-dashoffset','stroke-linecap','stroke-linejoin','stroke-miterlimit','stroke-width','color-interpolation','color-rendering'],
	'Opacity':['opacity','stroke-opacity','fill-opacity'],
	'Graphics':['display','image-rendering','pointer-events','shape-rendering','text-rendering','visibility'],
	'Marker':['marker-start','marker-mid','marker-end'],
	'Gradient':['stop-color','stop-opacity'],
	'Clip':['clip-path','clip-rule'],
	'Mask':['mask'],
	'Filter':['filter'],
	'FilterColor':['color-interpolation-filters'],
	'FilterPrimitive':['x','y','width','height','result'],
	'DocumentEvents':['onunload','onabort','onerror','onresize','onscroll','onzoom'],
	'GraphicalEvents':['onfocusin','onfocusout','onactivate','onclick','onmousedown','onmouseup','onmouseover','onmousemove','onmouseout','onload'],
	'AnimationEvents':['onbegin','onend','onrepeat','onload'],
	'Cursor':['cursor'],
	'XLink':['xlink:type','xlink:href','xlink:role','xlink:arcrole','xlink:title','xlink:show','xlink:actuate'],
	'External':['externalResourcesRequired'],
	'AnimationAttribute':['attributeName','attributeType'],
	'AnimationTiming':['begin','dur','end','min','max','restart','repeatCount','repeatDur','fill'],
	'AnimationValue':['calcMode','values','keyTimes','keySplines','from','to','by'],
	'AnimationAddition':['additive','accumulate']
]
attrib['FilterPrimitiveWithin'] = attrib['FilterPrimitive'] + ['in']
attrib['XLinkRequired'] = attrib['XLink']
attrib['XLinkEmbed'] = attrib['XLink']
attrib['XLinkReplace'] = attrib['XLink']
attrib['Animation'] = attrib['XLink']

content = [
	'Description':['desc','title','metadata'],
	'Use':['use'],
	'Structure':['svg','g','defs','symbol','use'],
	'Conditional':['switch'],
	'Image':['image'],
	'Style':['style'],
	'Shape':['rect','circle','line','polyline','polygon','ellipse','path'],
	'Text':['text','altGlyphDef'],
	'TextContent':['tspan','tref','textPath','altGlyph'],
	'Marker':['marker'],
	'ColorProfileElements':['color-profile'],
	'Gradient':['linearGradient','radialGradient'],
	'Pattern':['pattern'],
	'Clip':['clipPath'],
	'Mask':['mask'],
	'Filter':['filter'],
	'FilterPrimitive':['feBlend','feFlood','feColorMatrix','feComponentTransfer','feComposite','feConvolveMatrix','feDiffuseLighting','feDisplacementMap','feGaussianBlur','feImage','feMerge','feMorphology','feOffset','feSpecularLighting','feTile','feTurbulence'],
	'Cursor':['cursor'],
	'Hyperlink':['a'],
	'View':['view'],
	'Script':['script'],
	'Animation':['animate','animateColor','animateTransform','animateMotion','set'],
	'Font':['font']
]