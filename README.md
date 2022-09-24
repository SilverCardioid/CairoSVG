A work-in-progress fork of the vector graphics converter [CairoSVG](https://github.com/Kozea/CairoSVG/). It is intended to be a more modular version of the library, allowing its drawing functionality to be used directly from a script in addition to its original purpose of parsing and converting SVG files.

Other branches and related repositories:
* [CairoSVG/master](https://github.com/SilverCardioid/CairoSVG/tree/master/): for proposed changes to the original library
* [Cairopath](https://github.com/SilverCardioid/cairopath): my previous attempt at a vector graphics module

# Requirements
See `requirements.txt` for the necessary Python libraries. In addition, [cairocffi](https://github.com/Kozea/cairocffi) needs a separate DLL file for [Cairo](https://en.wikipedia.org/wiki/Cairo_(graphics)) itself, which must be named `libcairo-2.dll` and placed in a folder that is in the system's [`PATH`](https://en.wikipedia.org/wiki/PATH_(variable)).

Getting a working Cairo DLL turns out to be quite a challenge, especially on Windows. The [cairocffi documentation](https://cairocffi.readthedocs.io/en/stable/overview.html#installing-cairo-on-windows) recommends installing GTK+, which includes Cairo. This worked for me when I first started working with it in 2018, but loading the DLL fails in a new Anaconda environment on another device. I eventually found the [cairo-windows](https://preshing.com/20170529/heres-a-standalone-cairo-dll-for-windows/) repository, which has [ZIP files](https://github.com/preshing/cairo-windows/releases) with prebuilt 32- and 64-bit DLLs, and moved and renamed the DLL from the newest version (1.17.2) so cairocffi could find it.

# Example
```python
import math
from cairosvg import SVG

# Create an SVG object
svg = SVG(width=600, height=600)

# ...or load a file using
# svg = SVG.read('filename.svg')

# Add elements
svg.rect(width=600, height=600, fill='#fff')

g = svg.g()
g.transform.translate(300, 300)
g.circle(r=120, fill='#000')

path = g.path(fill='#fc0')
path.M(0, -100)
for i in range(1, 5):
	path.L(100*math.sin(i*4*math.pi/5), -100*math.cos(i*4*math.pi/5))
path.z()

# Display and save the image
svg.show()
svg.export('filename.svg')
svg.export('filename.png')

```