
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import sys
import os

from CONFIG import BIGBOXMAXUNDO, extract_floats
from bigbox import BigBox
from boxview import BoxView
from HANDLERS import SMALLBOXFRAMEDEFAULT, UNDOBUTTONDEFAULT
from HANDLERS import on_first_button_click, on_prev_button_click, on_next_button_click, on_last_button_click
from HANDLERS import on_image_mouse_press, reset_projections, mouse_position_timeout, on_top_delete_event, image_resize_timeout
from HANDLERS import on_refine_button_click, on_coarsen_button_click, on_shiftX_button_click, on_shiftY_button_click, on_shiftZ_button_click, on_undo_button_click, on_scaleXYZ_button_click


mainwin = Gtk.Window( title = "MeshEdit < %s" % sys.argv[1] ) # sys.argv[1], as in C, is the first parameter passed by the user (should be filename of file containing points)


# load the icon from whatever directory contains this script (MESHEDIT.py)
GUIICONPATH = os.path.join( sys.path[0], "ICON" + os.extsep + "jpg" ) # sys.path[0] is the directory containing this script (MESHEDIT.py), os.path.join intelligently splices
if os.path.isfile( GUIICONPATH ): # if the icon exists (why wouldn't it?) then make it the program's "official" icon
	mainwin.set_icon_from_file( GUIICONPATH )
else:
	print( "LAUNCH : can't find taskbar icon file %s (not very important)" % GUIICONPATH )


icontheme = Gtk.IconTheme.get_for_screen( mainwin.get_screen() ) # used to verify whether standard icons exist
print( "LAUNCH : found desired standard button icons? %s" % str( icontheme.has_icon( "go-bottom" ) and icontheme.has_icon( "go-down" ) and icontheme.has_icon( "go-up" ) and icontheme.has_icon( "go-top" ) ) )

ICON_STD_INIT = "go-bottom"
ICON_STD_DECR = "go-down"
ICON_STD_INCR = "go-up"
ICON_STD_FINL = "go-top"
firstbutton = ( Gtk.Button.new_from_icon_name( ICON_STD_INIT, Gtk.IconSize.from_name( ICON_STD_INIT ) ) if icontheme.has_icon( ICON_STD_INIT ) else Gtk.Button.new_with_label( "First" ) )
prevbutton = ( Gtk.Button.new_from_icon_name( ICON_STD_DECR, Gtk.IconSize.from_name( ICON_STD_DECR ) ) if icontheme.has_icon( ICON_STD_DECR ) else Gtk.Button.new_with_label( "Previous" ) )
nextbutton = ( Gtk.Button.new_from_icon_name( ICON_STD_INCR, Gtk.IconSize.from_name( ICON_STD_INCR ) ) if icontheme.has_icon( ICON_STD_INCR ) else Gtk.Button.new_with_label( "Next" ) )
lastbutton = ( Gtk.Button.new_from_icon_name( ICON_STD_FINL, Gtk.IconSize.from_name( ICON_STD_FINL ) ) if icontheme.has_icon( ICON_STD_FINL ) else Gtk.Button.new_with_label( "Last" ) )

#firstbutton = Gtk.Button.new_from_icon_name( "go-bottom", Gtk.IconSize.from_name( "go-bottom" ) )
#prevbutton = Gtk.Button.new_from_icon_name( "go-down", Gtk.IconSize.from_name( "go-down" ) )
#nextbutton = Gtk.Button.new_from_icon_name( "go-up", Gtk.IconSize.from_name( "go-up" ) )
#lastbutton = Gtk.Button.new_from_icon_name( "go-top", Gtk.IconSize.from_name( "go-top" ) )

#firstbutton = Gtk.Button.new_from_icon_name( "go-first", Gtk.IconSize.from_name( "go-first" ) )
#prevbutton = Gtk.Button.new_from_icon_name( "go-previous", Gtk.IconSize.from_name( "go-previous" ) )
#nextbutton = Gtk.Button.new_from_icon_name( "go-next", Gtk.IconSize.from_name( "go-next" ) )
#lastbutton = Gtk.Button.new_from_icon_name( "go-last", Gtk.IconSize.from_name( "go-last" ) )

#firstbutton = Gtk.Button.new_from_icon_name( "media-skip-backward", Gtk.IconSize.from_name( "media-skip-backward" ) )
#prevbutton = Gtk.Button.new_from_icon_name( "media-seek-backward", Gtk.IconSize.from_name( "media-seek-backward" ) )
#nextbutton = Gtk.Button.new_from_icon_name( "media-seek-forward", Gtk.IconSize.from_name( "media-seek-forward" ) )
#lastbutton = Gtk.Button.new_from_icon_name( "media-skip-forward", Gtk.IconSize.from_name( "media-skip-forward" ) )

paginggrid = Gtk.Grid()
paginggrid.attach( firstbutton, left = 0, top = 0, width = 1, height = 1 )
paginggrid.attach_next_to( prevbutton, firstbutton, Gtk.PositionType.RIGHT, width = 1, height = 1 )
paginggrid.attach_next_to( nextbutton,prevbutton , Gtk.PositionType.RIGHT, width = 1, height = 1 )
paginggrid.attach_next_to( lastbutton, nextbutton, Gtk.PositionType.RIGHT, width = 1, height = 1 )
paginggridframe = Gtk.Frame( label = "Paging" )
paginggridframe.add( paginggrid )


bigboximage = Gtk.Image()
# Because widgets are sometimes given extra space in the form of margins, 
# need to be sure that origin of this GtkImage widget agrees with what the 
# VIEWER considers to be the actual upper-left corner of the image, 
# otherwise mouse-clicks will mis-identify stuff.
bigboximage.set_halign( Gtk.Align.START )
bigboximage.set_valign( Gtk.Align.START )
# BUG: Nonetheless, there is still a tiny region of misidentification, 
# because the upper-left-corner of the true image starts at some small 
# number of pixels (2 or 3). If you click very very close to the bottom 
# or right edge of a square, it will select the square below or to the 
# right of the intended one.
bigboximageevents = Gtk.EventBox() # allow the image itself to receive events (specifically, mouse-clicks)
bigboximageevents.add( bigboximage )
bigboximageframe = Gtk.Frame()
bigboximageframe.add( bigboximageevents )

bigboxlabel = Gtk.Label( "" )
bigboxlabelframe = Gtk.Frame( label = "BigBox" )
bigboxlabelframe.add( bigboxlabel )


smallboxXYimage = Gtk.Image()
smallboxXYimageframe = Gtk.Frame( label = "XY-projection of selected SmallBox" )
smallboxXYimageframe.add( smallboxXYimage )
smallboxYZimage = Gtk.Image()
smallboxYZimageframe = Gtk.Frame( label = "YZ-projection of selected SmallBox" )
smallboxYZimageframe.add( smallboxYZimage )
smallboxXZimage = Gtk.Image()
smallboxXZimageframe = Gtk.Frame( label = "XZ-projection of selected SmallBox" )
smallboxXZimageframe.add( smallboxXZimage )
smallboxgrid = Gtk.Grid()
smallboxgrid.attach( smallboxXYimageframe, left = 0, top = 0, width = 3, height = 3 )
smallboxgrid.attach_next_to( smallboxYZimageframe, smallboxXYimageframe, Gtk.PositionType.BOTTOM, width = 3, height = 3 )
smallboxgrid.attach_next_to( smallboxXZimageframe, smallboxYZimageframe, Gtk.PositionType.BOTTOM, width = 3, height = 3 )
smallboxlabel = Gtk.Label()
smallboxlabelframe = Gtk.Frame( label = SMALLBOXFRAMEDEFAULT )
smallboxlabelframe.add( smallboxlabel )
smallboximages = { "XY":smallboxXYimage , "YZ":smallboxYZimage , "XZ":smallboxXZimage } # for convenience
smallboximageframes = { "XY":smallboxXYimageframe , "YZ":smallboxYZimageframe , "XZ":smallboxXZimageframe } # for convenience
#for plane in smallboximages:
#	smallboximages[plane].set_halign( Gtk.Align.START )
#	smallboximages[plane].set_valign( Gtk.Align.START )


refinebutton = Gtk.Button.new_with_label( "Refine" ) # use "zoom-in" icon?
coarsenbutton = Gtk.Button.new_with_label( "Coarsen" ) # use "zoom-out" icon?
partitiongrid = Gtk.Grid()
partitiongrid.attach( refinebutton, left = 0, top = 0, width = 1, height = 1 )
partitiongrid.attach_next_to( coarsenbutton, refinebutton, Gtk.PositionType.BOTTOM, width = 1, height = 1 )
partitiongridframe = Gtk.Frame( label = "Partition" )
partitiongridframe.add( partitiongrid )

shiftXbutton = Gtk.Button.new_with_label( "x-shift" )
shiftXentrybox = Gtk.Entry.new()
shiftXentrybox.set_placeholder_text( "x-increment (+ or -)" )
shiftYbutton = Gtk.Button.new_with_label( "y-shift" )
shiftYentrybox = Gtk.Entry.new()
shiftYentrybox.set_placeholder_text( "y-increment (+ or -)" )
shiftZbutton = Gtk.Button.new_with_label( "z-shift" )
shiftZentrybox = Gtk.Entry.new()
shiftZentrybox.set_placeholder_text( "z-increment (+ or -)" )
shiftgrid = Gtk.Grid()
shiftgrid.attach( shiftXbutton, left = 0, top = 0, width = 1, height = 1 )
shiftgrid.attach_next_to( shiftYbutton, shiftXbutton, Gtk.PositionType.BOTTOM, width = 1, height = 1 )
shiftgrid.attach_next_to( shiftZbutton, shiftYbutton, Gtk.PositionType.BOTTOM, width = 1, height = 1 )
shiftgrid.attach_next_to( shiftXentrybox, shiftXbutton, Gtk.PositionType.RIGHT, width = 1, height = 1 )
shiftgrid.attach_next_to( shiftYentrybox, shiftYbutton, Gtk.PositionType.RIGHT, width = 1, height = 1 )
shiftgrid.attach_next_to( shiftZentrybox, shiftZbutton, Gtk.PositionType.RIGHT, width = 1, height = 1 )
shiftgridframe = Gtk.Frame( label = "Location" )
shiftgridframe.add( shiftgrid )

undobutton = Gtk.Button.new_with_label( UNDOBUTTONDEFAULT )
undogrid = Gtk.Grid()
undogrid.attach( undobutton, left = 0, top = 0, width = 1, height = 1 )
undoframe = Gtk.Frame( label = ( "Undo (up to %d previous)" % BIGBOXMAXUNDO ) )
undoframe.add( undogrid )

scaleXYZbutton = Gtk.Button.new_with_label( "xyz-scale" )
scaleXYZentrybox = Gtk.Entry.new()
scaleXYZentrybox.set_placeholder_text( "scale factor (+ or -)" )
scalegrid = Gtk.Grid()
scalegrid.attach( scaleXYZbutton, left = 0, top = 0, width = 1, height = 1 )
scalegrid.attach_next_to( scaleXYZentrybox, scaleXYZbutton, Gtk.PositionType.RIGHT, width = 1, height = 1 )
scalegridframe = Gtk.Frame( label = "Size" )
scalegridframe.add( scalegrid )


maingrid = Gtk.Grid()
maingrid.attach( partitiongridframe, left = 0, top = 0, width = 2, height = 2 )
maingrid.attach_next_to( shiftgridframe, partitiongridframe, Gtk.PositionType.BOTTOM, width = 2, height = 3 )
maingrid.attach_next_to( scalegridframe, shiftgridframe, Gtk.PositionType.BOTTOM, width = 2, height = 1 )
maingrid.attach_next_to( undoframe, scalegridframe, Gtk.PositionType.BOTTOM, width = 2, height = 1 )
maingrid.attach_next_to( paginggridframe, undoframe, Gtk.PositionType.BOTTOM, width = 2, height = 1 )

maingrid.attach( bigboximageframe, left = 2, top = 0, width = 8, height = 8 )
maingrid.attach_next_to( bigboxlabelframe, bigboximageframe, Gtk.PositionType.BOTTOM, width = 8, height = 1 )
maingrid.attach_next_to( smallboxlabelframe, bigboxlabelframe, Gtk.PositionType.BOTTOM, width = 8, height = 1 )
maingrid.attach( smallboxgrid, left = 10, top = 0, width = 3, height = 10 )
# TO DO: attach a GtkLabel for communication with user (want to avoid dependence on terminal)


mainwin.add( maingrid )


# extract points and description of enclosing box from file
bigbox = None
f = open( sys.argv[1], "r" ) # sys.argv[1], as in C, is the first parameter passed by the user (should be filename of file containing points)
O = L = None
for line in f:
	if "%" in line: # allow MATLAB-style remarks in the header
		print( "LAUNCH : ignored line '%s'" % line[:-1] )
		continue
	flts = extract_floats( line )
	if len( flts ) != 3:
		print( "LAUNCH : invalid line in file (probably not bad, usually extra newline)" )
		continue
	if bigbox is None: # inefficient to continue checking nature of line after known to be past "header"
		if "O" in line or "o" in line: # line describes a corner of the box
			O = ( flts[0], flts[1], flts[2] )
			print( "LAUNCH : successfully read 'O' field" )
			continue
		elif "L" in line or "l" in line: # line describes the box's dimensions
			L = ( flts[0], flts[1], flts[2] )
			print( "LAUNCH : successfully read 'L' field" )
			continue
		assert O is not None, "LAUNCH : 'O' field not found?"
		assert L is not None, "LAUNCH : 'L' field not found?"
		bigbox = BigBox( O, L ) # if here, header is completely known and current line (should) contains the first point -- initialize outermost box and fall out of this if-statement
	assert O[0] <= flts[0] and flts[0] < O[0]+L[0] and O[1] <= flts[1] and flts[1] < O[1]+L[1] and O[2] <= flts[2] and flts[2] < O[2]+L[2], "LAUNCH : tried to insert point outside of BigBox!"
	bigbox.insert_point( ( flts[0], flts[1], flts[2] ) )
f.close()

# scale the BigBox to fit exactly within a BOXVIEWMAXPIXELS x BOXVIEWMAXPIXELS x BOXVIEWMAXPIXELS cube (largest of L[0],L[1] becomes BOXVIEWMAXPIXELS, others scale appropriately)
dilation = ( 2 * mainwin.get_screen().height() / 6.0 ) / max( abs(L[0]), abs(L[1]) )
BBW = dilation*L[0]
BBH = dilation*L[1]
BBD = dilation*L[2]
bigboxview = BoxView( BBW, BBH ) # TO DO: be sure the aspect ratio corresponds to the actual dimensions of the box (only matters for non-cubical)
smallboxviewXY = BoxView( BBW/2, BBH/2 ) # when the BigBox is non-cubical, need three different BoxViews for projections (all three could be different sizes)
smallboxviewYZ = BoxView( BBH/2, BBD/2 ) # when the BigBox is non-cubical, need three different BoxViews for projections (all three could be different sizes)
smallboxviewXZ = BoxView( BBW/2, BBD/2 ) # when the BigBox is non-cubical, need three different BoxViews for projections (all three could be different sizes)
smallboxviews = { "XY":smallboxviewXY , "YZ":smallboxviewYZ , "XZ":smallboxviewXZ } # for convenience
##print( "LAUNCH : screen's resolution is %dx%d; " % ( mainwin.get_screen().width(), mainwin.get_screen().height() ) )
##print( "LAUNCH : large image set to %dx%d; " % ( BBW, BBH ) )
##print( "LAUNCH : small images set to %dx%d, %dx%d, %dx%d" % ( smallboxviewXY.Img.width, smallboxviewXY.Img.height, smallboxviewYZ.Img.width, smallboxviewYZ.Img.height, smallboxviewXZ.Img.width, smallboxviewXZ.Img.height ) )


# connect all signals/events
firstbutton.connect( "clicked", on_first_button_click, bigbox, bigboxview, bigboximage )
prevbutton.connect( "clicked", on_prev_button_click, bigbox, bigboxview, bigboximage )
nextbutton.connect( "clicked", on_next_button_click, bigbox, bigboxview, bigboximage )
lastbutton.connect( "clicked", on_last_button_click, bigbox, bigboxview, bigboximage )
refinebutton.connect( "clicked", on_refine_button_click, bigbox, bigboxview, bigboximage )
coarsenbutton.connect( "clicked", on_coarsen_button_click, bigbox, bigboxview, bigboximage )
shiftXbutton.connect( "clicked", on_shiftX_button_click, bigbox, shiftXentrybox, bigboxview, bigboximage )
shiftYbutton.connect( "clicked", on_shiftY_button_click, bigbox, shiftYentrybox, bigboxview, bigboximage )
shiftZbutton.connect( "clicked", on_shiftZ_button_click, bigbox, shiftZentrybox, bigboxview, bigboximage )
scaleXYZbutton.connect( "clicked", on_scaleXYZ_button_click, bigbox, scaleXYZentrybox, bigboxview, bigboximage )
undobutton.connect( "clicked", on_undo_button_click, bigbox, bigboxview, bigboximage )
bigboximageevents.connect( "button-press-event", on_image_mouse_press, bigbox, bigboxview, bigboximage, smallboxviews, smallboximages, smallboxlabel )


# assemble list of widgets that depend exclusively on the BigBox's internal state
bigbox.attach_observer( "bf", bigboximageframe )
bigbox.attach_observer( "bl", bigboxlabel )
bigbox.attach_observer( "Fb", firstbutton )
bigbox.attach_observer( "Pb", prevbutton )
bigbox.attach_observer( "Nb", nextbutton )
bigbox.attach_observer( "Lb", lastbutton )
bigbox.attach_observer( "Rb", refinebutton )
bigbox.attach_observer( "Cb", coarsenbutton )


# set reset_projections's "static" local variables
reset_projections.svs = smallboxviews
reset_projections.gtkimages = smallboximages
reset_projections.sblabel = smallboxlabel

# set on_undo_button_click's "static" local variables
on_undo_button_click.UndoStack = []
on_undo_button_click.button = undobutton

# set image_resize_timeout's "static" local variables
image_resize_timeout.W = 0 # is this really the best initial value?
image_resize_timeout.H = 0 # is this really the best initial value?

# prep various widgets
mainwin.show_all() # fully initializes all GtkWidgets recursively
bigboximageevents.set_visible_window( False )
bigbox.draw( bigboxview )
bigboxview.show( bigboximage )
bigbox.get_number_of_points( True ) # force bigbox to calculate number of points and save result: at present, never changes after this, and is inefficient to recalculate unless changes
bigbox.get_bounding_box( True ) # force bigbox to calculate the bounding box and save result: at present, never changes after this, and is inefficient to recalculate unless changes
bigbox.refresh_statistics() # force bigbox to calculate fullest box and save (will change throughout runtime, but at least need initial value)
bigbox.notify_observers()
bigboxlabel.set_selectable( True ) # user likely wants to copy/paste the information displayed here
reset_projections()
smallboxlabel.set_selectable( True ) # user likely wants to copy/paste the information displayed here
undobutton.set_sensitive( False )

# allow these frames to grow if the user resizes, can then scale the images
bigboximageframe.set_hexpand( True )
smallboxXYimageframe.set_hexpand( True )
smallboxYZimageframe.set_hexpand( True )
smallboxXZimageframe.set_hexpand( True )
bigboximageframe.set_vexpand( True )
smallboxXYimageframe.set_vexpand( True )
smallboxYZimageframe.set_vexpand( True )
smallboxXZimageframe.set_vexpand( True )


hIDresize = GLib.timeout_add( 100, image_resize_timeout, bigbox, bigboxview, bigboximage, bigboximageframe, smallboxviews, smallboximageframes )

hIDmouse = GLib.timeout_add( 100, mouse_position_timeout, bigbox, bigboxview, bigboximage, smallboxlabelframe )


mainwin.connect( "delete-event", on_top_delete_event, ( hIDmouse, hIDresize ) )
mainwin.connect( "destroy", Gtk.main_quit )


Gtk.main()




#
