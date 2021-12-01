import classes.system_utilities.image_utilities.ImageUtilities as IU

bb_b = [[0, 0], [485, 485]]
bb_a = [[0, 0], [500, 500]]

print(IU.CheckIfPolygonsAreIntersectingTF(IU.GetFullBoundingBox(bb_a), IU.GetFullBoundingBox(bb_b)))
