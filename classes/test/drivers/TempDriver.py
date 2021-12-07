import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants
import classes.system_utilities.image_utilities.ObjectDetection as OD
import cv2

bb_a = [[[50, 50], [50, 50]], [[500, 500], [500, 500]]]
bb_b = [[33, 87], [111, 151]]

print(bb_a)
for i in range(len(bb_a)):
    bb_a[i].append(i)


print(bb_a)



# print(IU.AreBoxesOverlapping(parking_bounding_box=bb_a, car_bounding_box=bb_b))