
from PIL import ImageColor

import re


BIGBOXMAXDEPTH = 7
BIGBOXMAXSCALE = 10
BIGBOXMAXUNDO = 15

BOXVIEWRESIZETRIGGER = 0.001
BOXVIEWRESIZETOLLOW = 0.025
BOXVIEWRESIZETOLHIGH = 0.075
BOXVIEWRESIZETOLMED = ( BOXVIEWRESIZETOLLOW + BOXVIEWRESIZETOLHIGH ) / 2
BOXVIEWRESIZEAVAIL = 1-BOXVIEWRESIZETOLMED


BOXVIEWGRIDCOLOR = ImageColor.getrgb( "Black" )
BOXVIEWGRIDTHICKNESS = 1

BOXVIEWPOINTCOLOR = ImageColor.getrgb( "Blue" )
BOXVIEWPOINTRADIUS = 2

#BOXVIEWBACKGROUNDCOLOR = ImageColor.getrgb( "AntiqueWhite" )
#BOXVIEWBACKGROUNDCOLOR = ImageColor.getrgb( "Beige" )
#BOXVIEWBACKGROUNDCOLOR = ImageColor.getrgb( "BlanchedAlmond" )
#BOXVIEWBACKGROUNDCOLOR = ImageColor.getrgb( "Cornsilk" )
#BOXVIEWBACKGROUNDCOLOR = ImageColor.getrgb( "LemonChiffon" )
BOXVIEWBACKGROUNDCOLOR = ImageColor.getrgb( "LightGoldenRodYellow" )
#BOXVIEWBACKGROUNDCOLOR = ImageColor.getrgb( "PapayaWhip" )

#BOXVIEWHIGHLIGHTCOLOR = ImageColor.getrgb( "DeepPink" )
BOXVIEWHIGHLIGHTCOLOR = ImageColor.getrgb( "BurlyWood" )
#BOXVIEWHIGHLIGHTCOLOR = ImageColor.getrgb( "Khaki" )
#BOXVIEWHIGHLIGHTCOLOR = ImageColor.getrgb( "Red" )


pr_std = { "XY":( lambda P : ( P[0], P[1] ) ), "YZ":( lambda P : ( P[1], P[2] ) ), "XZ":( lambda P : ( P[0], P[2] ) ) } # projections of 3-space onto standard planes


def extract_floats( ptstr ):
	floats = []
	fpstrs = re.split( "[^\-+.0-9eE]", ptstr ) # consider as a delimiter anything other than characters used for standard floating-point numbers
	for fpstr in filter( bool, fpstrs ): # strings are True unless empty
		floats.append( float(fpstr) ) # note that float(_) handles exponential notation intelligently
	return floats


