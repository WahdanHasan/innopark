import classes.system_utilities.image_utilities.ImageUtilities as IU

bb_a = [[50, 50], [100, 100]]
bb_b = [[50, 50], [100, 100]]

print(IU.CheckIfPolygonFullyContainsPolygonTF(bb_a, bb_b))
