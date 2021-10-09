from classes.system_utilities.image_utilities import LicenseDetection as LD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2

LD.OnLoad()

img = cv2.imread("E:\\PycharmProjects\\InnoPark\\data\\reference footage\\images\\carr2.jpg")

is_one_license_above_threshold, bounding_box_classes, bounding_boxes, score = LD.DetectLicenseInImage(img)

frame_processed = IU.DrawBoundingBoxAndClasses(image=img,
                                               class_names=bounding_box_classes,
                                               bounding_boxes=bounding_boxes)
#
# frame_processed = IU.DrawBoundingBoxes(image=img,
#                                        bounding_boxes=bounding_boxes)

cv2.imshow("test", frame_processed)
print(is_one_license_above_threshold)
print(score)

cv2.waitKey(0)



