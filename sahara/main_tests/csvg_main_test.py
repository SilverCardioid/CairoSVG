from csvg_import import cairosvg

svg = cairosvg.SVG(600, 600)
svg.rect(600, 600, fill='#ffe')
svg.circle(180, 300, 300, fill='#05a')
svg.show()