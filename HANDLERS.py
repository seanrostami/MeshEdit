
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from bigbox import SMALLBOXINFOFMT

from CONFIG import BIGBOXMAXUNDO, extract_floats, pr_std
from CONFIG import BOXVIEWRESIZETRIGGER, BOXVIEWRESIZETOLLOW, BOXVIEWRESIZETOLHIGH, BOXVIEWRESIZETOLMED, BOXVIEWRESIZEAVAIL

import time


SMALLBOXFRAMEDEFAULT = "SmallBox"
SMALLBOXFRAMEFMT = SMALLBOXFRAMEDEFAULT + " (cursor is at offset (%d,%d,%d))"
UNDOBUTTONDEFAULT = "UNDO"
UNDOBUTTONFMT = UNDOBUTTONDEFAULT + " (%s)"


def on_top_delete_event( target, gdkevent, hIDs ):
	for hID in hIDs: # discontinue any "indefinitely running" timeouts
		GLib.source_remove( hID )
	return False # allow Event to propagate further


# The obvious way to handle resizes is to connect to the 'configure-event' signal. However, I found this event 
#	to be unreliable. It seemed to me that during initialization the window manager resized the main GtkWindow 
#	several times but did not emit the signal, so the image was comically small because my handler was never 
#	called to resize it. The alternative, which is done here, is to have a timeout running that checks whether 
#	the window's size changed and resizes if so. For it to work smoothly, modifications were necessary -- see 
#	below. Another possibility, whose complexity would probably not be justified by the gains, is to have the 
#	timeout operate with one of two frequencies: slow and fast. Usually, the timeout is operating on the slow 
#	frequency, so as to leave minimal footprint on the program's operation. Upon noticing that the window's size 
#	changed, it changes to fast frequency. When it decides that the resizing is finished (how?), it returns to 
#	the slow frequency.
def image_resize_timeout( bb, bv, gtkimage, bbframe, svs, sbframes ):
	bfW = bbframe.get_allocated_width()
	bfH = bbframe.get_allocated_height()

	if abs( image_resize_timeout.W - bfW ) < BOXVIEWRESIZETRIGGER and abs( image_resize_timeout.H - bfH ) < BOXVIEWRESIZETRIGGER: # window didn't "really" change (most common situation), do nothing
		return True # tells GTK+ to continue running this timeout (this particular timeout should run indefinitely)

	bfHadj = bfH - bbframe.get_label_widget().get_allocated_height()

	errW = abs(bfW - bv.Img.width) / bfW # gap between the GtkFrame's right edge and the GtkImage's right edge, as a percentage of the former
	errH = abs(bfHadj - bv.Img.height) / bfHadj # the GtkFrame's embedded GtkLabel occupies some of the height, adjust for that!

	# This conditional decides, again, whether to resize or do nothing. In brief, 
	# 	1) if EITHER edge of the GtkFrame is sufficiently NEAR the corresponding edge of the GtkImage, resize (to be smaller), 
	#	2) if BOTH edges of the GtkFrame are sufficiently FAR from the corresponding edges of the GtkImage, resize (to be larger), and 
	#	3) otherwise, do nothing.
	#	What exactly "sufficiently" means is specified by the constants BOXVIEWRESIZETOLLOW, BOXVIEWRESIZETOLHIGH (CONFIG.py)
	if errW > BOXVIEWRESIZETOLLOW and errH > BOXVIEWRESIZETOLLOW and ( errW < BOXVIEWRESIZETOLHIGH or errH < BOXVIEWRESIZETOLHIGH ):
		return True # tells GTK+ to continue running this timeout (this particular timeout should run indefinitely)

	# I believe these should be here, rather than above the preceding 'if' statement.
	image_resize_timeout.W = bfW # update stored dimensions with which to compare next dimensions
	image_resize_timeout.H = bfH

	# The constant BOXVIEWRESIZEAVAIL, which is close to but less than 1, is used to prevent the GtkImage from occupying the full space of its GtkFrame.
	# Why? Because if things are too tight, the window manager will enlarge the GtkFrame a bit, which will trigger this function to resize the image, 
	#	which will cause the window manager to enlarge the GtkFrame a bit, which will trigger this function to resize the image, which will...
	#	Note that setting bv.Img.width, bv.Img.height to these values causes errW, errH (if they were to be recalculated immediately afterward) to 
	#	be precisely 1-BOXVIEWRESIZEAVAIL, halfway between BOXVIEWRESIZETOLLOW and BOXVIEWRESIZETOLHIGH, which is the most straightforward way to 
	#	avoid "runaway resizing".
	bv.resize_to( BOXVIEWRESIZEAVAIL*bfW, BOXVIEWRESIZEAVAIL*bfHadj )
	bb.draw( bv )
	bv.show( gtkimage )

	for plane in svs: # resize all the projections
		W = sbframes[plane].get_allocated_width() # ACTUAL width of GtkFrames around SmallBoxes' projections' GtkImages, which are set to expand automatically as the user resizes the main GtkWindow
		Hadj = sbframes[plane].get_allocated_height() - sbframes[plane].get_label_widget().get_allocated_height() # the GtkFrame's height, adjusted for the embedded GtkLabel's height
		svs[plane].resize_to( BOXVIEWRESIZEAVAIL*W, BOXVIEWRESIZEAVAIL*Hadj )

	reset_projections()

	# In case it ever happens (it shouldn't) that the new dimensions have an appreciably different aspect ratio than the original, notify
	if round( float(bv.Img.width)/float(bv.Img.height), 2 ) != round( float(bv.AspectRatio.numerator)/float(bv.AspectRatio.denominator), 2 ):
		print( "\n[sent @ %.2f] image_resize_timeout : resized large image to be %dx%d (aspect %.2f)" % ( time.clock(), bv.Img.width, bv.Img.height, float(bv.Img.width)/float(bv.Img.height) ) )
		smallsizes = ()
		for plane in ( "XY", "YZ", "XZ" ): # dictionaries have arbitrary order and I don't want to guess which plane is which, so force the order
			smallsizes += ( svs[plane].Img.width, svs[plane].Img.height, float(svs[plane].Img.width) / float(svs[plane].Img.height) )
		print( "image_resize_timeout : resized small images to be to be %dx%d (%.2f), %dx%d (%.2f), %dx%d (%.2f)" % smallsizes )
	
	return True # tells GTK+ to continue running this timeout (this particular timeout should run indefinitely)


# TO DO: replace .get_pointer with .get_device_position (GTK+ Manaual says former is deprecated)
def mouse_position_timeout( bb, bv, gtkimage, sbframe ):
	"""Monitors the position of the mouse and, if it is above the region of gtkimage described by bbox, displays to user."""
	P = gtkimage.get_pointer()
	if 0 <= P[0] and P[0] < bv.Img.width and 0 <= P[1] and P[1] < bv.Img.height:
		xyoffsets = bv.screen2offsets( P, len(bb) )
		sbframe.set_label( SMALLBOXFRAMEFMT % ( xyoffsets["x"], xyoffsets["y"], bb.CurPage ) )
	else: # if mouse is outside, best not to say anything about cursor
		sbframe.set_label( SMALLBOXFRAMEDEFAULT )
	return True # tells GTK+ to continue running this timeout (this particular timeout should run indefinitely)


def on_image_mouse_press( target, gdkevent, bb, bv, gtkimage, svs, gtkimages, sblabel ):
	if gdkevent.button != 1 or gdkevent.type != Gdk.EventType.BUTTON_PRESS or int(gdkevent.x) < 0 or int(gdkevent.x) >= bv.Img.width or int(gdkevent.y) < 0 or int(gdkevent.y) >= bv.Img.height: # is there a more canonical way to express "left-click"?
		return False
	xyoffset = bv.screen2offsets( ( int(gdkevent.x), int(gdkevent.y) ), len( bb ) )
	bb.draw( bv, xyoffset ) # highlight selected square in the BigBox (automatically eliminates previous highlighting, if any) 
	bv.show( gtkimage )
	for plane in svs:
		bb.draw_projection( svs[plane], xyoffset, pr_std[plane] )
		svs[plane].show( gtkimages[plane] )
	sblabel.set_label( SMALLBOXINFOFMT % bb.get_SMALLBOXINFO( xyoffset ) )
	return True # no reason to propagate Event further


def on_first_button_click( target, bb, bv, gtkimage ):
	bb.decrement_page( True ) # also refreshes Observers
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()


def on_prev_button_click( target, bb, bv, gtkimage ):
	bb.decrement_page() # also refreshes Observers
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()


def on_next_button_click( target, bb, bv, gtkimage ):
	bb.increment_page() # also refreshes Observers
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()


def on_last_button_click( target, bb, bv, gtkimage ):
	bb.increment_page( True ) # also refreshes Observers
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()


def on_refine_button_click( target, bb, bv, gtkimage ):
	memento = bb.get_memento()
	bb.refine() # also refreshes Observers
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()
	undo_push( memento, 'r' )


def on_coarsen_button_click( target, bb, bv, gtkimage ):
	memento = bb.get_memento()
	bb.coarsen() # also refreshes Observers
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()
	undo_push( memento, 'c' )


def shift( bb, bv, gtkimage, trvec ):
	if not bb.shift( trvec ): # .shift also refreshes Observers if successful (success <=> return True)
		return False # this particular shift was not possible, indicate that user should be notified
	bb.draw( bv )
	bv.show( gtkimage )
	return True


# TO DO: move notifications to a GtkLabel?
def on_shiftX_button_click( target, bb, gtkentry, bv, gtkimage ):
	memento = bb.get_memento()
	shiftby = extract_floats( gtkentry.get_text() )
	if len( shiftby ) != 1: # something is wrong with user input, notify and do nothing else
		print( "on_shiftX_button_click : bad input provided for shift" )
		return
	if not shift( bb, bv, gtkimage, ( shiftby[0], 0, 0 ) ):
		print( "on_shiftX_button_click : can't shift past bounding box" )
		return
	reset_projections()
	undo_push( memento, 'x' )


# TO DO: move notifications to a GtkLabel?
def on_shiftY_button_click( target, bb, gtkentry, bv, gtkimage ): 
	memento = bb.get_memento()
	shiftby = extract_floats( gtkentry.get_text() )
	if len( shiftby ) != 1: # something is wrong with user input, notify and do nothing else
		print( "on_shiftY_button_click : bad input provided for shift" )
		return
	if not shift( bb, bv, gtkimage, ( 0, shiftby[0], 0 ) ):
		print( "on_shiftY_button_click : can't shift past bounding box" )
		return
	reset_projections()
	undo_push( memento, 'y' )


# TO DO: move notifications to a GtkLabel?
def on_shiftZ_button_click( target, bb, gtkentry, bv, gtkimage ):
	memento = bb.get_memento()
	shiftby = extract_floats( gtkentry.get_text() )
	if len( shiftby ) != 1: # something is wrong with user input, notify and do nothing else
		print( "on_shiftZ_button_click : bad input provided for shift" )
		return
	if not shift( bb, bv, gtkimage, ( 0, 0, shiftby[0] ) ):
		print( "on_shiftZ_button_click : can't shift past bounding box" )
		return
	reset_projections()
	undo_push( memento, 'z' )	


# TO DO: move notifications to a GtkLabel?
def on_scaleXYZ_button_click( target, bb, gtkentry, bv, gtkimage ):
	memento = bb.get_memento()
	scaleby = extract_floats( gtkentry.get_text() )
	if len( scaleby ) != 1: # something is wrong with user input, notify and do nothing else
		print( "on_scaleXYZ_button_click : bad input provided for scale" )
		return
	if not bb.scale( scaleby[0] ): # .scale also refreshes Observers if successful (success <=> return True)
		print( "on_scaleXYZ_button_click : can't scale into bounding box" )
		return
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()
	undo_push( memento, 's' )


def reset_projections():
	for plane in reset_projections.svs:
		reset_projections.svs[plane].reset()
		reset_projections.svs[plane].show( reset_projections.gtkimages[plane] )
	reset_projections.sblabel.set_label( "(click on a SmallBox to inspect)" )


def on_undo_button_click( target, bb, bv, gtkimage ):
	bb.undo( undo_pop() )
	bb.draw( bv )
	bv.show( gtkimage )
	reset_projections()


def undo_push( memento, optype ): # possibilities for optype: 'r' (refine), 'c' (coarsen), 'x' (x-shift), 'y' (y-shift), 'z' (z-shift), 's' (xyz-scale)
	assert len( on_undo_button_click.UndoStack ) <= BIGBOXMAXUNDO, "undo_push : stack is full!"
	if len( on_undo_button_click.UndoStack ) == BIGBOXMAXUNDO:
		del on_undo_button_click.UndoStack[0] # stack is full, need to make space
	memento["op"] = optype
	on_undo_button_click.UndoStack.append( memento )
	on_undo_button_click.button.set_sensitive( True )
	on_undo_button_click.button.set_label( UNDOBUTTONFMT % optype )


def undo_peek():
	assert len( on_undo_button_click.UndoStack ) > 0, "undo_peek : stack is empty!"
	return on_undo_button_click.UndoStack[-1]


def undo_pop():
	assert len( on_undo_button_click.UndoStack ) > 0, "undo_pop : stack is empty!"
	memento = on_undo_button_click.UndoStack.pop()
	if len( on_undo_button_click.UndoStack ) > 0:
		on_undo_button_click.button.set_sensitive( True )
		on_undo_button_click.button.set_label( UNDOBUTTONFMT % undo_peek()["op"] )
	else:
		on_undo_button_click.button.set_sensitive( False )
		on_undo_button_click.button.set_label( UNDOBUTTONDEFAULT )
	return memento





#
