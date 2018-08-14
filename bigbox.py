
from smallbox import SmallBox

from CONFIG import BIGBOXMAXDEPTH, BIGBOXMAXSCALE


SMALLBOXINFOFMT = "SmallBox is at offset (%d,%d,%d), contains %d points"


class BigBox:

	def __init__( self, O, L ):
		"""Initializes the structure that describes the outermost box B. Conceptually, parameter O is the corner of B "closest" to (-Infinity, -Infinity, -Infinity) in 3-space and L contains the three lengths of B's sides. However, it is allowed that O is any corner of B and L is treated as a *vector* from O to the opposite corner of B. In particular, if O was any of the other seven corners than the "natural" one already mentioned then at least one element of L must be negative. Anyway, BigBox normalizes whatever it is given so that, internally, it is as though O and L were the "natural" choices. The depth of subdivision is initialized to 0, i.e. there is no subdivision at all; the user can refine as desired via the GUI."""
		# Note: Together with the user's points, which aren't directly stored by BigBox 
		#	and don't change after program starts, these next three pieces of data 
		#	completely determine the intrinsic state of the user's "scenario".
		self.Origin = { "x":min(O[0],O[0]+L[0]) , "y":min(O[1],O[1]+L[1]) , "z":min(O[2],O[2]+L[2]) }  # standardizes the user's input
		self.Lengths = { "x":abs(L[0]) , "y":abs(L[1]) , "z":abs(L[2]) }
		self.Depth = 0

		self.Pages = [ {} ] # each element will be a dictionary assigning a SmallBox to each key ( x-offset, y-offset )

		self.CurPage = 0 # a.k.a. z-offset		

		# dependent data, updated only once or only occasionally, stored for speed
		self.Steps = { "x":self.Lengths["x"], "y":self.Lengths["y"], "z":self.Lengths["z"] }
		self.NumPoints = 0 # "statistics"
		self.bbox = { "min":{ "x":None, "y":None, "z":None }, "max":{ "x":None, "y":None, "z":None } } # "statistics" (bbox describes the minimal box containing all the user's points)

		self.Fullest = {} # "statistics"
		self.Thinnest = {} # "statistics"
		self.NumOccupied = None # "statistics"

		self.Observers = {} # dictionary of GtkLabels etc. that depend on BigBox's state


	def __len__( self ):
		assert( 0 <= self.Depth and self.Depth <= BIGBOXMAXDEPTH )
		return 2**(self.Depth)


	def get_number_of_points( self, refresh = False ): # pass refresh=True to recalculate, otherwise will use most recently calculated value (for efficiency)
		if refresh:
			self.NumPoints = 0
			for page in self.Pages:
				self.NumPoints += sum( [ len( page[xyoffset] ) for xyoffset in page ] )
		return self.NumPoints


# _assumes_ that all points are contained in user-provided box!
	def get_bounding_box( self, refresh = False ): # pass refresh=True to recalculate, otherwise will use most recently calculated value (for efficiency)
		if refresh:
			N = 2**(self.Depth)
			Lz = None
			for zoffset in range( N ): # find the lowest page that has at least one point and calculate the lowest z-coordinate in that page
				page = self.Pages[zoffset]
				for xyoffset in page:
					for P in page[xyoffset]:
						if ( Lz is None ) or ( P[2] < Lz ):
							Lz = P[2]
				if Lz is not None:
					self.bbox["min"]["z"] = Lz
					break
			Rz = None
			for zoffset in range( N, 0, -1 ): # similar to previous block, but find the highest z-coordinate in the highest page that has at least one point
				page = self.Pages[zoffset-1]
				for xyoffset in page:
					for P in page[xyoffset]:
						if ( Rz is None ) or ( Rz < P[2] ):
							Rz = P[2]
				if Rz is not None:
					self.bbox["max"]["z"] = Rz
					break
			Lx = None
			for xoffset in range( N ): # analogous to previous, but for x-coordinates
				for zoffset in range( N ):
					page = self.Pages[zoffset]
					for yoffset in range( N ):
						if (xoffset,yoffset) in page:
							for P in page[ (xoffset,yoffset) ]:
								if ( Lx is None ) or ( P[0] < Lx ):
									Lx = P[0]
				if Lx is not None:
					self.bbox["min"]["x"] = Lx
					break
			Rx = None
			for xoffset in range( N, 0, -1 ):
				for zoffset in range( N ):
					page = self.Pages[zoffset]
					for yoffset in range( N ):
						if (xoffset-1,yoffset) in page:
							for P in page[ (xoffset-1,yoffset) ]:
								if ( Rx is None ) or ( Rx < P[0] ):
									Rx = P[0]
				if Rx is not None:
					self.bbox["max"]["x"] = Rx
					break
			Ly = None
			for yoffset in range( N ): # analogous to previous, but for y-coordinates
				for zoffset in range( N ):
					page = self.Pages[zoffset]
					for xoffset in range( N ):
						if (xoffset,yoffset) in page:
							for P in page[ (xoffset,yoffset) ]:
								if ( Ly is None ) or ( P[1] < Ly ):
									Ly = P[1]
				if Ly is not None:
					self.bbox["min"]["y"] = Ly
					break
			Ry = None
			for yoffset in range( N, 0, -1 ):
				for zoffset in range( N ):
					page = self.Pages[zoffset]
					for xoffset in range( N ):
						if (xoffset,yoffset-1) in page:
							for P in page[ (xoffset,yoffset-1) ]:
								if ( Ry is None ) or ( Ry < P[1] ):
									Ry = P[1]
				if Ry is not None:
					self.bbox["max"]["y"] = Ry
					break
		return self.bbox


	def refresh_statistics( self ):
		"""calculates and stores:
			1) the xyz-offset of at least one SmallBox containing the largest number of points found in any SmallBox 
			2) the xyz-offset of at least one SmallBox containing the smallest number of points found in any non-empty SmallBox
			3) the number of non-empty boxes
		"""
		self.Fullest = {}
		maxsize = -1 # will be updated upon first comparison
		self.Thinnest = {}
		minsize = self.NumPoints + 1 # will be updated upon first comparison
		self.NumOccupied = 0
		numoccupied_DEBUG = 0
		for ( zoffset, page ) in enumerate( self.Pages ):
			self.NumOccupied += len( page ) # number of keys, "should" always be the number of SmallBoxes that contain at least one point
			for xyoffset in page:
				numoccupied_DEBUG += 1
				n = len( page[xyoffset] )
				assert n > 0, "BigBox.refresh_statistics : SmallBox with no points associated to key"
				if n < minsize:
					minsize = n
					self.Thinnest["x"] = xyoffset[0]
					self.Thinnest["y"] = xyoffset[1]
					self.Thinnest["z"] = zoffset
				if maxsize < n:
					maxsize = n
					self.Fullest["x"] = xyoffset[0]
					self.Fullest["y"] = xyoffset[1]
					self.Fullest["z"] = zoffset
		assert numoccupied_DEBUG == self.NumOccupied


	def increment_page( self, fully = False ):
		assert fully or ( ( self.CurPage + 1 ) < 2**(self.Depth) )
		self.CurPage = ( 2**(self.Depth) - 1 if fully else self.CurPage + 1 )
		self.notify_observers()


	def decrement_page( self, fully = False ):
		assert fully or ( self.CurPage > 0 )
		self.CurPage = ( 0 if fully else self.CurPage - 1 )
		self.notify_observers()


	def euclidean2offsets( self, P ): # P likely comes directly from the datafile, so most convenient to assume P is a tuple (x,y,z) rather than a dictionary
		"""Given a genuine point P in 3-space, return the offsets (x,y,z) of the SmallBox which contains P."""
		return { "x":int((P[0]-self.Origin["x"])/self.Steps["x"]), "y":int((P[1]-self.Origin["y"])/self.Steps["y"]), "z":int((P[2]-self.Origin["z"])/self.Steps["z"]) }


	def insert_point( self, P, tol = 0 ): # P likely comes directly from the datafile, so most convenient to assume P is a tuple (x,y,z) rather than a dictionary
	# Note: Although it's true that .insert_point changes BigBox's internal state, 
	#	I don't calculate/refresh any statistics or notify observers here 
	#	because .insert_point is likely to be called a very large number of times, 
	#	much of which happens during initialization of the program, so it would be 
	#	very wasteful and pointless to include statistics/notifications with each call.
		offsets = self.euclidean2offsets( P )
		page = self.Pages[offsets["z"]]
		if (offsets["x"],offsets["y"]) not in page:
			page[ (offsets["x"],offsets["y"]) ] = SmallBox()
		page[ (offsets["x"],offsets["y"]) ].insert_point( P, tol )


	def draw( self, bv, tohighlight = None ):
		"""Completely redraws bv's image data to depict self's current state. The optional parameter tohighlight, if provided, indicates which SmallBox to highlight."""
		bv.reset()
		bv.draw_grid( 2**(self.Depth) )
		if tohighlight is not None: # highlight (important to do before drawing points)
			for axis in tohighlight:
				assert tohighlight[axis] >= 0 and tohighlight[axis] < 2**(self.Depth)
			bv.highlight( { "min":bv.offsets2screen( tohighlight, 2**(self.Depth) ), "max":bv.offsets2screen( { "x":tohighlight["x"]+1, "y":tohighlight["y"]+1 }, 2**(self.Depth) ) } )
		page = self.Pages[self.CurPage]
		for xyoffset in page:
			bv.draw( page[xyoffset], (self.Origin["x"],self.Origin["y"]), (self.Lengths["x"],self.Lengths["y"]) )


	def draw_projection( self, bv, xyoffset, pr ): # caller passes as pr any one of the three standard planar projections
		assert xyoffset["x"] >= 0 and xyoffset["y"] >= 0 and xyoffset["x"] < 2**(self.Depth) and xyoffset["y"] < 2**(self.Depth)
		bv.reset()
		page = self.Pages[self.CurPage]
		if (xyoffset["x"],xyoffset["y"]) in page:
			bv.draw( [ pr( P ) for P in page[ (xyoffset["x"],xyoffset["y"]) ] ], pr( ( self.Origin["x"] + ( xyoffset["x"] * self.Steps["x"] ), self.Origin["y"] + ( xyoffset["y"] * self.Steps["y"] ), self.Origin["z"] + ( self.CurPage * self.Steps["z"] ) ) ), pr( ( self.Steps["x"], self.Steps["y"], self.Steps["z"] ) ) )


	def repair( self, sx = 1, sy = 1, sz = 1 ):
		"""Whenever it is known or suspected that some SmallBoxes include points that are outside of their legal bounding boxes, 
		and the correct SmallBox already exists, .repair will iterate through each SmallBox and reassign ownership of its illegal 
		points to the correct SmallBox. So long as the number of boxes and their relative placement are unchanged (i.e. the universe 
		of keys [zoffset][xoffset,yoffset] used for self.Pages is unchanged) then .repair will always produce a legal distribution."""
		numstrips = 2**(self.Depth)
		bbox = { "min":{ "x":None, "y":None, "z":None }, "max":{ "x":None, "y":None, "z":None } }
		for zoffset in range( 0, numstrips, sz ):
			page = self.Pages[zoffset]
			bbox["min"]["z"] = self.Origin["z"]+(zoffset*self.Steps["z"]) # z-coordinate of the correct bounding box's "lowest" corner
			bbox["max"]["z"] = bbox["min"]["z"] + self.Steps["z"] # z-coordinate of the correct bounding box's "highest" corner
			for xoffset in range( 0, numstrips, sx ):
				bbox["min"]["x"] = self.Origin["x"]+(xoffset*self.Steps["x"]) # x-coordinate of the correct bounding box's "lowest" corner
				bbox["max"]["x"] = bbox["min"]["x"] + self.Steps["x"] # x-coordinate of the correct bounding box's "highest" corner
				for yoffset in range( 0, numstrips, sy ):
					if (xoffset,yoffset) in page:
						bbox["min"]["y"] = self.Origin["y"]+(yoffset*self.Steps["y"]) # y-coordinate of the correct bounding box's "lowest" corner
						bbox["max"]["y"] = bbox["min"]["y"] + self.Steps["y"] # y-coordinate of the correct bounding box's "highest" corner
						page[ (xoffset,yoffset) ].delete_some( bbox, self.insert_point ) # relocate any that don't belong
						if len( page[ (xoffset,yoffset) ] ) == 0:
							del page[ (xoffset,yoffset) ]


	def refine( self ):
		assert self.Depth < BIGBOXMAXDEPTH

		N = 2**(self.Depth)

		for _ in range( N ): # enlarge the list of pages by a factor of two
			self.Pages.append( None )

		for i in range( N ): # reindex the old pages from 0,1,2,...,N-1 to 0,2,4,...,2N-2
			I = N-1-i # must perform reindexing backwards!
			self.Pages[2*I] = self.Pages[I] # necessary to copy?
			self.Pages[(2*I)+1] = {} # each new page caused by refinement (will occupy odd indices) is assigned an empty dictionary
		assert len( self.Pages ) == 2**(self.Depth+1)

		for i in range( N ): # for each OLD page (which now occupy even indices), reindex the old SmallBoxes from (i,j) to (2i,2j)
			page = self.Pages[2*i]
			for xoffset in range( N ):
				U = N-1-xoffset # must perform reindexing backwards!
				for yoffset in range( N ):
					V = N-1-yoffset # must perform reindexing backwards!
					if ( (U,V) in page ) and ( U != 0 or V != 0 ): # only reindex if the SmallBox actually contained something (also, don't need to reindex origin!)
						page[ (2*U,2*V) ] = page[ (U,V) ]
						del page[ (U,V) ]

		for i in range( N ): # for each OLD page (which now occupy even indices), "insert" three empty SmallBoxes surrounding the "lvalues" from the previous tri-loop
			page = self.Pages[2*i]
			for xoffset in range( N ):
				U = 2*xoffset
				for yoffset in range( N ):
					V = 2*yoffset
					if (U+1,V) in page:
						del page[ (U+1,V) ]
					if (U,V+1) in page:
						del page[ (U,V+1) ]
					if (U+1,V+1) in page:
						del page[ (U+1,V+1) ]

		self.Depth += 1 # increase self.Depth... 
		for axis in self.Steps: # ... and modify self.Steps accordingly
			self.Steps[axis] /= 2
		self.CurPage *= 2 # sensibly adjust the current page to fit within the new range of pages

		self.repair( 2, 2, 2 ) # finally, go through all the old boxes (which are now resized and contain out-of-bounds points) and move those points to the appropriate box
		self.refresh_statistics() # likely that statistics changed, force recalculation
		self.notify_observers()


# can this be rewritten to use .repair()?
	def coarsen( self ):
		assert self.Depth > 0

		self.Depth -= 1 # decrease self.Depth... 
		for axis in self.Steps: # ... and modify self.Steps accordingly
			self.Steps[axis] *= 2
		self.CurPage = int( self.CurPage / 2 ) # sensibly adjust the current page to fit within the new range of pages

		N = 2**(self.Depth)

		for zoffset in range( N ): # for each cluster of eight SmallBoxes, move into the box closest to (-Inf,-Inf,-Inf) all the points from the other seven boxes
			W = 2*zoffset
			page = self.Pages[W]
			for xoffset in range( N ):
				U = 2*xoffset
				for yoffset in range( N ):
					V = 2*yoffset
					for (u,v,w) in ( (U+1,V,W), (U,V+1,W), (U+1,V+1,W), (U,V,W+1), (U+1,V,W+1), (U,V+1,W+1), (U+1,V+1,W+1) ): # the seven boxes to transfer FROM
						if (u,v) in self.Pages[w]: # definitely will insert a point...
							if (U,V) not in page: # ... but may need to create receiver
								page[ (U,V) ] = SmallBox()
							(self.Pages[w])[ (u,v) ].delete_all( page[ (U,V) ].insert_point )
							del (self.Pages[w])[ (u,v) ] # this SmallBox is now empty, should eliminate its key entirely

		for i in range( N ): # delete (backwards) the odd pages (the even pages will automatically be reindexed to 0,1,2,...,N-1)
			I = N-1-i # must perform reindexing backwards!
			assert len( self.Pages[(2*I)+1] ) == 0
			del self.Pages[(2*I)+1]
		assert len( self.Pages ) == 2**(self.Depth)

		for page in self.Pages: # reindex from (i,j) to (i/2,j/2) each SmallBox that is the closest to (-Infinity,-Infinity,-Infinity) among the four in its cluster
			for xoffset in range( N ):
				for yoffset in range( N ):
					if (2*xoffset,2*yoffset) in page: # only reindex if the SmallBox actually contained something
						page[ (xoffset,yoffset) ] = page[ (2*xoffset,2*yoffset) ]
					elif (xoffset,yoffset) in page: # at present, supposed to be empty, so delete if still keyed
						del page[ (xoffset,yoffset) ]

		for page in self.Pages: # delete all the SmallBoxes that were not "lvalues" in the previous tri-loop
			for xoffset in range( 0, 2*N, 2 ): # together, this loop and the next delete all page[(i,j)] except when both i<N,j<N
				y0 = ( N if xoffset < N else 0 )
				for yoffset in range( y0, 2*N, 2 ):
					if (xoffset,yoffset) in page:
						del page[ (xoffset,yoffset) ]

		self.refresh_statistics() # likely that statistics changed, force recalculation
		self.notify_observers()


	def shift( self, trvec ): # translates box (but not points!) by some vector
		for (a,axis) in ( (0,"x"), (1,"y"), (2,"z") ): # check first that new box will contain all points: need O+trvec<self.bbox["min"] and O+L+trvec>self.bbox["max"]
			if ( self.bbox["min"][axis] < ( self.Origin[axis] + trvec[a] ) ) or ( ( self.Origin[axis] + trvec[a] + self.Lengths[axis] ) <= self.bbox["max"][axis] ):
				return False # caller can notify user that translation was illegal
		for (a,axis) in ( (0,"x"), (1,"y"), (2,"z") ):
			self.Origin[axis] += trvec[a]
		self.repair() # possible that every SmallBox now contains some points that are not within their bounding boxes
		self.refresh_statistics() # likely that statistics changed, force recalculation
		self.notify_observers()
		return True


	def scale( self, c ):
		C = min( abs( c ), BIGBOXMAXSCALE ) # safety
		if C == 1:
			return True
		if c > 0: # c > 0 indicates (by convention) that scaling should be done relative to the (-Infinity,-Infinity,-Infinity) corner
			if( C < 1 ): # if shrinking, check first that shrunken box will contain all points (not an issue for magnification)
				for axis in self.Origin:
					if self.Origin[axis]+(C*self.Lengths[axis]) <= self.bbox["max"][axis]:
						return False # caller can notify user that translation was illegal
			for axis in self.Lengths:
				self.Lengths[axis] *= C
				self.Steps[axis] *= C
		else: # c < 0 indicates (by convention) that scaling should be done relative to the (Infinity,Infinity,Infinity) corner
			if C < 1:
				for axis in self.Origin:
					if self.Origin[axis] + ((1-C)*self.Lengths[axis]) > self.bbox["min"][axis]:
						return False # caller can notify user that translation was illegal
			for axis in self.Origin:
				self.Origin[axis] += (1-C)*self.Lengths[axis]
				self.Lengths[axis] *= C
				self.Steps[axis] *= C
		self.repair()
		self.refresh_statistics() # likely that statistics changed, force recalculation
		self.notify_observers()
		return True


# should self.CurPage be considered part of BigBox's intrinsic state?
	def get_memento( self ): 
		return { "op":None, "Ox":self.Origin["x"] , "Oy":self.Origin["y"] , "Oz":self.Origin["z"] , "Lx":self.Lengths["x"] , "Ly":self.Lengths["y"] , "Lz":self.Lengths["z"] , "D":self.Depth, "cP":self.CurPage }


	def undo( self, memento ):
		if 'r' in memento["op"]:
			self.coarsen()
		elif 'c' in memento["op"]:
			self.refine()
		else:
			self.Origin["x"] = memento["Ox"]
			self.Origin["y"] = memento["Oy"]
			self.Origin["z"] = memento["Oz"]
			self.Lengths["x"] = memento["Lx"]
			self.Lengths["y"] = memento["Ly"]
			self.Lengths["z"] = memento["Lz"]
			self.Steps["x"] = self.Lengths["x"]/(2**(memento["D"]))
			self.Steps["y"] = self.Lengths["y"]/(2**(memento["D"]))
			self.Steps["z"] = self.Lengths["z"]/(2**(memento["D"]))
			self.repair() # these supported undos are fundamentally shifts/scales, so must repair
			self.refresh_statistics() # likely that statistics changed, force recalculation
			self.notify_observers()


	def attach_observer( self, key, obs ):
		assert key not in self.Observers # never should happen that we overwrite a preexisting observer
		self.Observers[key] = obs


	def notify_observers( self ):
		# at present, BigBox's "internal state" consists of: Origin, Lengths, CurPage, Depth, fullest SmallBox, emptiest SmallBox 
		# fullest/emptiest SmallBox depends on Origin,Lengths,Depth,points, but points do not (at this time) change after initialization, so fullest is effectively dependent 
		# NumPoints and bbox do not (at this time) change after initialization 
		# number of boxes is completely dependent on Depth

		AVERAGE_FMT	= "%d points, %d non-empty SmallBoxes (of %d), average %.2f points-per-nonempty"
		AVERAGE_ARGS	= ( self.get_number_of_points( False ), self.NumOccupied, 8**(self.Depth), float(self.get_number_of_points( False ))/float(self.NumOccupied) )
		EXTREME_FMT	= "fullest SmallBox @ (%d,%d,%d) with %d points (not necessarily unique)\nemptiest nonempty SmallBox @ (%d,%d,%d) with %d points (not necessarily unique)"
		EXTREME_ARGS	= ( self.Fullest["x"], self.Fullest["y"], self.Fullest["z"], len( (self.Pages[self.Fullest["z"]])[(self.Fullest["x"],self.Fullest["y"])] ), self.Thinnest["x"], self.Thinnest["y"], self.Thinnest["z"], len( (self.Pages[self.Thinnest["z"]])[(self.Thinnest["x"],self.Thinnest["y"])] ) )
		OUTERMOST_FMT	= "outermost box: Xmin = %f;Ymin = %f;Zmin = %f;BoxLength = %f;" # WARNING: that there is a single "BoxLength" only makes sense for the current application -- be sure to update this if the BigBox ever becomes non-cubical
		OUTERMOST_ARGS	= ( self.Origin["x"], self.Origin["y"], self.Origin["z"], self.Lengths["x"] )
		BOUNDING_FMT	= "bounding box is [ (%f,%f,%f), (%f,%f,%f) ]"
		BOUNDING_ARGS	= ( self.bbox["min"]["x"], self.bbox["min"]["y"], self.bbox["min"]["z"], self.bbox["max"]["x"], self.bbox["max"]["y"], self.bbox["max"]["z"] )
		FMT = AVERAGE_FMT + "\n" + EXTREME_FMT + "\n" + BOUNDING_FMT + "\n" + OUTERMOST_FMT
		ARGS = AVERAGE_ARGS + EXTREME_ARGS + BOUNDING_ARGS + OUTERMOST_ARGS # concatenate tuples
		self.Observers["bl"].set_text( FMT % ARGS )

		self.Observers["bf"].set_label( "Current Page (%d of %d), contains all SmallBoxes with offset (*,*,%d)" % ( self.CurPage + 1, 2**(self.Depth), self.CurPage ) )

		if self.CurPage > 0:
			self.Observers["Fb"].set_sensitive( True )
			self.Observers["Pb"].set_sensitive( True )
		else:
			self.Observers["Fb"].set_sensitive( False )
			self.Observers["Pb"].set_sensitive( False )

		if self.CurPage + 1 < 2**(self.Depth):			
			self.Observers["Nb"].set_sensitive( True )
			self.Observers["Lb"].set_sensitive( True )
		else:
			self.Observers["Nb"].set_sensitive( False )
			self.Observers["Lb"].set_sensitive( False )

		self.Observers["Rb"].set_sensitive( self.Depth < BIGBOXMAXDEPTH )
		self.Observers["Cb"].set_sensitive( self.Depth > 0 )
		
	# Note: This is not a "true" Observer pattern in that there is no universal interface for updates. 
	# However, the extra flexibility offered by that aspect of Observer is simply not needed here, and it would be messy to attach such an interface to each observer.


	def get_SMALLBOXINFO( self, xyoffset ):
		return ( xyoffset["x"], xyoffset["y"], self.CurPage, len( (self.Pages[self.CurPage])[(xyoffset["x"],xyoffset["y"])] ) if ( (xyoffset["x"],xyoffset["y"]) in self.Pages[self.CurPage] ) else 0 )




#
