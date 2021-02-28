import os
import sys
sys.path.insert(0, os.path.abspath('..'))
import cairosvg

svg = cairosvg.SVG(600, 600)
svg.rect(600, 600, fill='#ffe')

g = svg.g(transform='translate(300,300)')
g.addChild('circle', r=180, fill='#05a')

svg.export('test_export.png')
svg.export('test_export.pdf')
svg.export('test_export_oneline.svg', {'newline':False})
svg.export('test_export_cairo.svg', {'useCairo':True})
svg.export('test_export_indent.svg', {'indent':'  '})
