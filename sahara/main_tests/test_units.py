from csvg_import import cairosvg

svg = cairosvg.SVG('10in', '10in', viewBox='0 0 600 600') # 960px
svg.rect('100%' , '100%',          fill='#fff')
svg.rect('5in'  , '10%' ,          fill='#b00') # 480px
svg.rect('10cm' , '10%' , y='10%', fill='#fc0') # ~378px
svg.rect('200pt', '10%' , y='20%', fill='#b00') # ~267px
svg.rect('10em' , '10%' , y='30%', fill='#fc0') # 160px
svg.rect('10ex' , '10%' , y='40%', fill='#b00') # 80px
svg.circle('10%', cx='80%', cy='35%', fill='#b00') # 60px

svg2 = svg.svg('80%', '50%', y='50%') # 480x300px
svg2.rect('100%' , '100%',         fill='#ddd')
svg2.rect('1e1ex', '20%',          fill='#fc0')
svg2.rect('1e1em', '20%', y='20%', fill='#b00')
svg2.rect('2e2pt', '20%', y='40%', fill='#fc0')
svg2.rect('1e1cm', '20%', y='60%', fill='#b00')
svg2.rect('5e0in', '20%', y='80%', fill='#fc0')
svg2.circle('15%', cx='100%', cy='30%', fill='#b00') # ~60.04px (15% of RMS(480,300))

svg.export('output/test_units.png')
svg.export('output/test_units.svg')