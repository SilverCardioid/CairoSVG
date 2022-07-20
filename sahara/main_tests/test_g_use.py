from csvg_import import cairosvg

svg = cairosvg.SVG(600, 600)
svg.rect(600, 600, fill='#ffe')

# blue, blue, green, green (top left 2x2)
g1 = svg.g(id='g1', fill='#05a')
path1 = g1.addChild('path', id='path1', d='M75,15 135,75 75,135 15,75z')
g1.addChild('use', href='#path1', transform='translate(150,0)')
g1.addChild('use', href='path1',  transform='translate(0,150)',   fill='#084')
g1.addChild('use', href=path1,    transform='translate(150,150)', fill='#084')

# red, red, green, green (top right 2x2)
g2 = svg.g(id='g2', fill='#b11', transform='translate(300,0)')
g2.use(href='#path1')
use1 = g2.use(href='#path1', x=150, id='use1')
g2.use(       href='path1',  y=150, fill='#084')
g2.use(       href=use1,     y=150, fill='#084')

# copies of g1 and g2 (fill should be ignored here)
svg.use('#g1', fill='#000', y=300)
svg.use(g2,    fill='#000', y=300)

svg.export('output/test_g_use.png')
svg.export('output/test_g_use.svg')
