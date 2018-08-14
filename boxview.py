
from PIL import Image, ImageDraw

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib

from CONFIG import BOXVIEWBACKGROUNDCOLOR, BOXVIEWGRIDCOLOR, BOXVIEWGRIDTHICKNESS, BOXVIEWPOINTCOLOR, BOXVIEWPOINTRADIUS, BOXVIEWHIGHLIGHTCOLOR


# TO DO? Consider caching gdkpixbuf for each page. If the user 
# does a lot of page-flipping, something like this could save 
# a lot of calculation. On the other hand, if the user typically 
# edits and pages in a vaguely alternating way then the constant 
# purging and recreating of the cache could actually hurt performance. 
# It's all about what the user actually does...


class BoxView:

	def __init__( self, w, h ):
		self.AspectRatio = float(w)/float(h) # see note inside .resize_to, below
		self.Img = Image.new( "RGB", (int(w),int(h)), color = BOXVIEWBACKGROUNDCOLOR ) # not yet exploiting the possibility of "alpha"
		self.Drw = ImageDraw.Draw( self.Img, "RGB" )
		self.glibbytes = None
		self.gdkpixbuf = None
##		self.CachedPages = {} # stores some previously drawn pages


	def __del__( self ):
		self.Img.close()


	def resize_to( self, W, H ):
		"""closes existing PIL.Image and creates a new one with dimensions w x h such that 
			(1) aspect ratio w/h is the same as before, 
			(2) w x h is the largest that will fit inside W x H"""
# Note: It is very important to store the original aspect ratio in .__init__ and reuse it here. 
#	The alternative is to recalculate it via self.Img.width/self.Img.height here, but accumulation 
#	of floating-point errors from the arithmetic here causes the aspect ratio to become corrupted 
#	after each resize, eventually resulting in an image that is visibly wrong to even a casual observer.
		w = None
		h = None
		if self.AspectRatio > float(W)/float(H):
			w = W
			h = float(W)/self.AspectRatio
		else:
			h = H
			w = float(H)*self.AspectRatio
		self.Img.close()
		self.Img = Image.new( "RGB", (int(w),int(h)), color = BOXVIEWBACKGROUNDCOLOR )
		self.Drw = ImageDraw.Draw( self.Img, "RGB" ) # recreate a PIL.ImageDraw for the new PIL.Image
		# will be responsibility of resize-handler to redraw the image and show, seems best not to do it here


	def screen2offsets( self, P, numstrips ):
		"""Given screen coordinates (X,Y), return the xy-offsets (x,y) of the SmallBox which would contain (X,Y) graphically."""
		return { "x":int(P[0]/(self.Img.width/numstrips)), "y":int((self.Img.height-P[1])/(self.Img.height/numstrips)) }


	def offsets2screen( self, xyoffset, numstrips ):
		"""Given the xy-offsets (x,y) of a SmallBox B, return the screen coordinates (X,Y) of the lower-left corner the square that B would occupy if displayed graphically."""
		return { "X":xyoffset["x"]*self.Img.width/numstrips, "Y":self.Img.height-(xyoffset["y"]*self.Img.height/numstrips) }


	def reset( self ): # often want to add points to an existing canvas, but sometimes need to restart
		self.Drw.rectangle( xy = [ (0,0), (self.Img.width-1,self.Img.height-1) ], fill = BOXVIEWBACKGROUNDCOLOR, outline = BOXVIEWGRIDCOLOR )


	def draw_grid( self, numstrips ):
		for i in range( 1, numstrips ): # does not draw the border of the image (that's done already by .reset)
			self.Drw.line( [ (i*self.Img.width/numstrips,0), (i*self.Img.width/numstrips,self.Img.height-1) ], fill = BOXVIEWGRIDCOLOR, width = BOXVIEWGRIDTHICKNESS )
			self.Drw.line( [ (0,i*self.Img.height/numstrips), (self.Img.width-1,i*self.Img.height/numstrips) ], fill = BOXVIEWGRIDCOLOR, width = BOXVIEWGRIDTHICKNESS )


	def draw( self, pts, O, L ): # will get pts from SmallBox, so important to access members by integer
		"""this is the only place in the entire program where points are drawn to an image"""
		Xscl = self.Img.width / L[0] # possibly pts is very long and this quantity is independent of P, save one operation per P by precalculating
		Yscl = self.Img.height / L[1] # ditto
		O1plusL1 = O[1] + L[1] # ditto
		for P in pts:
			X = Xscl * ( P[0] - O[0] )
			Y = Yscl * ( O1plusL1 - P[1] ) # reflect, because screen's origin is upper-left but origin of desired model of xy-plane is lower-left
			self.Drw.ellipse( xy = [ (X-BOXVIEWPOINTRADIUS,Y-BOXVIEWPOINTRADIUS), (X+BOXVIEWPOINTRADIUS,Y+BOXVIEWPOINTRADIUS) ], fill = BOXVIEWPOINTCOLOR ) # a thick dot


	def highlight( self, bbox ):
		LX = int(bbox["min"]["X"])
		RX = min( int(bbox["max"]["X"]), self.Img.width-1 )
		BY = min( int(bbox["min"]["Y"]), self.Img.height-1 )
		TY = int(bbox["max"]["Y"])
		self.Drw.rectangle( xy = [ (LX+1,TY+1), (RX-1,BY-1) ], fill = BOXVIEWHIGHLIGHTCOLOR )
		##self.Drw.line( [ (LX,BY), (LX,TY) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # left edge of square
		##self.Drw.line( [ (LX+1,BY), (LX+1,TY) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # thicken towards center
		##self.Drw.line( [ (LX,BY), (RX,BY) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # bottom edge of square
		##self.Drw.line( [ (LX,BY-1), (RX,BY-1) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # thicken towards center (don't forget that screen's Y increases downwards)
		##self.Drw.line( [ (LX,TY), (RX,TY) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # top edge of square
		##self.Drw.line( [ (LX,TY+1), (RX,TY+1) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # thicken towards center (don't forget that screen's Y increases downwards)
		##self.Drw.line( [ (RX,BY), (RX,TY) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # right edge of square
		##self.Drw.line( [ (RX-1,BY), (RX-1,TY) ], fill = BOXVIEWHIGHLIGHTCOLOR, width = BOXVIEWGRIDTHICKNESS ) # thicken towards center


	def show( self, gtkimage ):
		self.glibbytes = GLib.Bytes.new( self.Img.tobytes() )
		self.gdkpixbuf = GdkPixbuf.Pixbuf.new_from_bytes( self.glibbytes, GdkPixbuf.Colorspace.RGB, False, 8, self.Img.width, self.Img.height, len(self.Img.getbands())*self.Img.width )
		gtkimage.set_from_pixbuf( self.gdkpixbuf.copy() )


##	def is_cached( self, pagenum ):
##		return pagenum in self.CachedPages # check if dictionary has value for key=pagenum


##	def cache_current( self, pagenum ):
##		self.CachedPages[pagenum] = self.gdkpixbuf.copy()


##	def show_cache( self, gtkimage, pagenum ):
##		gtkimage.set_from_pixbuf( self.CachedPages[pagenum].copy() )


##	def invalidate_cache( self ):
##		self.CachedPages.clear()

