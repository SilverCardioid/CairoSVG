import os
import sys
sys.path.insert(0, os.path.abspath('..'))
import cairosvg

svg = cairosvg.SVG(600, 600)
svg.rect(600, 600, fill='#ffe')
svg.rect(100, 100, 40, 40, fill='#f00')
svg.rect(100, 100, 40, 40, fill='#f08', transform='translate(140)')
svg.rect(100, 100, 40, 40, fill='#f0f').transform('translate', 280, 0)
svg.rect(100, 100, 40, 40, fill='#80f').transform.translate(420)
svg.rect(100, 100, 40, 40, fill='#00f', transform='rotate(180, 90, 160)')
svg.rect(100, 100, 40, 40, fill='#08f').transform('translate(120 120) scale(2)')
svg.rect(100, 100, 40, 40, fill='#0ff').transform.rotate(90, 370, 230).translate(280)
svg.rect(100, 100, 40, 40, fill='#0f8').transform('translate', 0, 280).transform('rotate', 45, 90, 90)
svg.rect(100, 100, 40, 40, fill='#0f0').transform('rotate(45,510,370) translate(420,280)')
svg.rect(100, 100, 40, 40, fill='#8f0').transform.translate(-80, 440).skewX(45)
svg.rect(100, 100, 40, 40, fill='#ff0').transform.scale(2,1).translate(70, 420)
svg.rect(100, 100, 40, 40, fill='#f80').transform('skewY(-45) translate(440, 940)')

svg.export('test_transform.png')