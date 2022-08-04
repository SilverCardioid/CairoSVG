from csvg_import import cairosvg

svg = cairosvg.SVG(600, 600, viewBox='0 0 300 100', fill='grey', stroke='red', strokeWidth=5)
svg.rect(300, 100, fill='#f8f8f8')
svg.circle(id='c1', r=40, cx=50, cy=50)
svg.circle(id='c2', r=40, cx=100, cy=50, fill='blue')
svg.use(href='#c1', x=100)

svg2 = svg.svg(100, 50, x=200, viewBox='0,0,300,100', preserveAspectRatio='xMidYMid slice', stroke='green')
svg2.rect(300, 100, fill='#efe')
svg2.use(href='#c1')
svg2.circle(id='c3', r=40, cx=150, cy=50, fill='blue')
svg2.use(href='#c1', x=200)

svg3 = svg.svg(100, 50, x=200, y=50, viewBox='0 0 300 100', preserveAspectRatio='none', stroke='black')
svg3.rect(300, 100, fill='#eee')
svg3.circle(id='c4', r=40, cx=50, cy=50, fill='blue')
svg3.use(href='#c1', x=100)
svg3.use(href='#c4', x=200)

svg.export('output/test_nested_svgs.png')
svg.export('output/test_nested_svgs.svg')
