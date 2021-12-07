import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants
import classes.system_utilities.image_utilities.ObjectDetection as OD
import cv2

bb_a = [[32, 89], [111, 89], [32, 151], [111, 151]]
bb_b = [[33, 87], [111, 151]]

print(IU.AreBoxesOverlapping(parking_bounding_box=bb_a, car_bounding_box=bb_b))