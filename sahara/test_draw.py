import os
import sys
sys.path.insert(0, os.path.abspath('..'))
import cairosvg

svg = cairosvg.SVG(600, 600, fill='#ffe', strokeWidth='5')
path1 = svg.path('M 50,50H250V100H175L250,150 250,200 200,250 150,150 100,250  50,200V150L125,100z', stroke='#f00')
path2 = svg.path(stroke='#00d')
path2.M(350,50).H(550).V(100).H(475).L(550,150).L(550,200).L(500,250).L(450,150).L(400,250).L(350,200).V(150).L(425,100).Z()

svg.export('test_draw.png')