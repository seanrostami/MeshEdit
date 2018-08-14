
class SmallBox:

	def __init__( self ):
		self.Points = [] # will contain points in 3-space, expressed as tuples (x,y,z)


	def __len__( self ):
		return len( self.Points )


	def __iter__( self ): # only sensible interpretation of iteration on a SmallBox is iteration over its points, which is a common operation anyway
		return iter( self.Points ) # subsequent applications of next() will be directed towards this List iterator (i.e. I don't need to define __next__ for SmallBox)


	def insert_point( self, P, tol = 0 ): # P likely comes directly from the datafile, so most convenient to assume P is a tuple (x,y,z) rather than a dictionary
		self.Points.append( P ) # is there any reason to do .append( (P[0],P[1],P[2]) ) instead?
	# TO DO: if tol>0 provided, use it to weaken the concept of equality for floating-point values


	def delete_all( self, router ):
		"""Deletes all points currently stored by self and passes each points to the parameter router (a function that accepts one tuple and whose return, if any, is ignored)."""
		for P in self.Points:
			router( P ) # allow insertion of deleted points somewhere else (very common need)
		del self.Points[:]



	def delete_some( self, bbox, router ): # delete all points outside of bbox, reinsert those deleted via router
		"""Deletes any point (x,y,z) that is outside of the bounding box described by the parameter bbox (see CONFIG.py for details about what structure bbox should have and what precisely it means for a point to be "in" a bounding box) and passes each of those deleted points to the parameter router (a function that accepts one tuple and whose return, if any, is ignored)."""
		for i in range( len( self.Points ), 0, -1 ): # important to delete backwards!
			P = self.Points[i-1]
			if P[0] < bbox["min"]["x"] or bbox["max"]["x"] <= P[0] or P[1] < bbox["min"]["y"] or bbox["max"]["y"] <= P[1] or P[2] < bbox["min"]["z"] or bbox["max"]["z"] <= P[2]:
				del self.Points[i-1]
				router( P )
		# FASTER? for each coordinate, sort, then search the list from each end until necessary inequalities are violated, then delete everything except the middle

