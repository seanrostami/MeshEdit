

WHERE THE DATA COMES FROM: 

MeshEdit reads all its initial data from a _text_ file, provided by the user at execution (example: python .../MESHEDIT.py .../points.txt). Likely this file was generated by MATLAB or Octave. 



WHAT THE DATA CONTAINS: 

One line of the file will specify a corner of the outermost box. Another line of the file will specify the lengths of the sides of the outermost box. An example of such a file is provided in the same directory as the source scripts. 



HOW THE DATA SHOULD BE FORMATTED: 

The line specifying the corner must contain the letter "O" somewhere (example: O=[0,0,0]). The line specifying the lengths must contain the letter "L" somewhere (example: L=[1,1,1]). These two lines must all occur _before_ the lines containing points, but you can specify O and L in any order. You also can, anywhere before the first line containing a point, use a '%' character to specify that the line containing it should be ignored (so you can have multiple versions of O and L that you alternate as desired).

It is almost completely irrelevant how you format these lines:

The only thing that matters is that the line contains three floating-point numbers in the order x, y, z. You can group the points using brackets, parentheses, braces, or nothing, or almost anything else that doesn't have a special meaning (obviously, don't surround your point with "4", or "L", or...). You can use commas to separate the numbers, or spaces, or almost anything else that doesn't have a special meaning. The numbers can be given in exponential format (e.g. 2.018e+3) or non-exponential format (e.g. 2018). 

Really, almost anything is ok: " { +1.1E2, 2e2 | -0.0 O" is a perfectly good specification of the box's corner and yields (110,200,0) internally. 



REMARKS ON USAGE: 

You can specify _negative_ numbers for the lengths and they will be treated sensibly. For example, providing O=[0,0,0] and L=[-3,2,-1] will produce a box of height 1 whose base has vertices [0,0,-1], [-3,0,-1], [0,2,-1], [-3,2,-1]. Internally, the box will have "origin" [-3,0,-1] and side lengths [3,2,1]

You can use both positive and negative values when specifying a scaling factor C, and the sign controls the "style" of scaling. Let (X,Y,Z) be the corner of the outermost box closest to (Infinity, Infinity, Infinity), and let (x,y,z) be the opposite corner, closest to (-Infinity, -Infinity, -Infinity). Positive C scales as if (x,y,z) were the origin of 3-space: the corner (x,y,z) remains in its original position while all seven other corners move away (if C>1) or towards (if C<1) (x,y,z) until the side lengths of the resulting box are in ratio C with their initial values. Negative C does the opposite: corner (X,Y,Z) is fixed and all seven other corners move away/towards it until the lengths are in ratio |C| with their initial values.

Whenever MeshEdit communicates a box to you, it does so by providing a pair of triples ( (x,y,z), (X,Y,Z) ) and the meaning of the box is precisely as in the previous remark: the other six corners of the corresponding box are (x,Y,z), (x,y,Z), (x,Y,Z), (X,y,z), (X,y,Z), (X,Y,z).

For safety, there is an absolute bound B on depth and the program will not allow you to partition into more than 8^B pieces -- see CONFIG.py for the exact value of B. If you really want to partition further, you can increase this bound inside the CONFIG.py file. Similarly, the outermost box cannot be magnified by a factor larger than F _in a single operation_ -- see CONFIG.py for the exact value of F. You are, of course, allowed to perform as many magnifications as you want, thereby exceeding any factor in total, or you can increase the bound inside the CONFIG.py file.



FUTURE:

Make de-highlighting more efficient: only redraw that small area rather than refreshing the whole image

Consider caching BoxView's GdkPixbufs, one for each page, rather than redrawing them automatically. Be sure to delete them whenever the user changes the fundamentals of the outermost box (refine/coarsen, shift, scale), probably by attaching BoxView as an observer of BigBox.

Use different sizes for points in the big picture and small pictures?

It may be appropriate and worthwhile to specify some tiny tolerance t such that if points P and Q satisfy ||P-Q||<t then P and Q are considered by the program to be identical.



REMARKS ON IMPLEMENTATION:

Remarks on data structures:

	1) all points are either dictionaries {"x":_,"y":_,"z":_} or mere tuples (_,_,_)
		I make an effort to refer to these keys and indices by 'axis' and 'a' when they are iterated over in loops etc.

	2) all bounding boxes are nested dictionaries {"min":{{"x":_,"y":_,"z":_}},"max":{{"x":_,"y":_,"z":_}}}

	3) anything corresponding to the standard coordinate planes is a dictionary {"XY":_,"YZ":_,"XZ":_}
		I make an effort to refer to the keys by 'plane' when they are iterated over in loops etc.

Remarks on partitioning:

	For BigBox to be partitioned into SmallBoxes, there must be a coherent way to decide who "owns" a point when the point is on the boundary between two closed boxes. The most elegant way to do this (which may or may not be what Minghao is doing in MATLAB) is to declare that the three sides of a box closest to -Infinity are owned by the SmallBox and the other three sides are not. In other words, the projections onto the three axes of a SmallBox are half-open intervals of the form [a,b). The main conditional in method .delete_some reflects this choice. This also means that the BigBox cannot contain points on its three sides closest to +Infinity, and MESHEDIT.py reflects this. An exception to this concept of ownership, which cannot be any other way because of the topology of the Real Line, is the bounding box of the user's points.


Remarks on coordinate systems:

	In truth, this program uses three coordinate systems: Euclidean, Offsets, Screen. 
		1) Euclidean coordinates are the familiar triples (x,y,z) in 3-space. 
		2) Offsets are triples of integers specifying the position of a SmallBox inside the BigBox, thinking of the partitioned BigBox as a 3D-array of SmallBoxes with indices increasing as the x-, y-, z-coordinates become closer to Infinity. 
		3) Screen coordinates (X,Y) are what the window system uses to specify a pixel. 
	It is frequently necessary to convert between these: 
		a) To draw a point on the screen requires converting from Euclidean to Screen. 
		b) To insert a point into the appropriate SmallBox requires converting from Euclidean to Offsets. 
		c) The user is able to click on a SmallBox and view three enlarged projections of that SmallBox, and this requires converting from Screen to Offsets. 
		d) If the user was to be informed of the xy-coordinates of the points in 3-space clicked by the mouse, this would require converting from Screen to Euclidean. 
	When viewing a slice (="page") of the BigBox, points are always depicted (1) as projections onto the xy-plane, (2) relative to the boundary of the BigBox, (3) with the point closest to (-Infinity,-Infinity) in the lower left corner. In other words, if you projected the slice onto the xy-plane, looked at the xy-plane as any Math student would, and cropped away anything not inside the projection of the BigBox, you would see exactly what is depicted by the program. 
	Because Screen coordinates have the origin at the upper-left corner, it is always necessary to reflect the vertical axis when converting Screen coordinates to/from Euclidean coordinates.

