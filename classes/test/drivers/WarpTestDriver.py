import cv2
import numpy as np
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.helper_utilities.Enums import ParkingStatus


img = cv2.imread("data\\reference footage\\images\\parked_resized.png")

# TL, TR, BL, BR
parking_bb = [
                [349, 214],
                [481, 214],
                [480, 391],
                [718, 367]
             ]

pts1 = np.array(parking_bb, dtype=np.float32)

# BL, TL, BR, TR
pts2 = np.float32([
                    [500 - 349, 1000 - 214],  # BL
                    [500 - 349, 500], #TL
                    [1000 - 349, 1000 - 214],  # BR
                    [1000-349, 500], #TR
                   ])

pts3 = np.float32([
                    [500 - 349, 1000 - 314],  # BL
                    [500 - 349, 500], #TL
                    [1000 - 349, 1000 - 314],  # BR
                    [1000-349, 500], #TR
                   ])
# pts2= np.float32([
# [234, 176],
# [860, 176],
# [860, 620],
# [234, 620]
#
#
#
# ])

parking_bb_partial = IU.GetPartialBoundingBox(parking_bb)
parking_bb_partial_full = IU.GetFullBoundingBox(parking_bb_partial)

height, width, _ = img.shape

img_box = IU.DrawParkingBoxes(image=img,
                              bounding_boxes=[parking_bb_partial_full],
                              are_occupied=[ParkingStatus.NOT_OCCUPIED])

M = cv2.getPerspectiveTransform(pts1, pts2)
M2 = cv2.getPerspectiveTransform(pts2, pts3)

TL_post_transform = IU.CalculatePointPositionAfterTransform(parking_bb[1], M)
BR_post_transform = IU.CalculatePointPositionAfterTransform(parking_bb[2], M)
T1 = np.float32([[1, 0, -TL_post_transform[0]], [0, 1, -BR_post_transform[1]]])



warped_img = cv2.warpPerspective(img, M, (width*3, height*3))
warped_img2 = cv2.warpPerspective(warped_img, M2, (width*3, height*3))
offset_img = cv2.warpAffine(warped_img, T1, (width, height))
warped_img = cv2.circle(warped_img, TL_post_transform, 5, (0, 0, 255), 2)
warped_img = cv2.circle(warped_img, BR_post_transform, 5, (255, 0, 0), 2)

offset_img = IU.CropImage(warped_img, [TL_post_transform, BR_post_transform])

# cv2.imshow("normal", img)
cv2.imshow("parking", img_box)
cv2.imshow("offset_img", offset_img)
cv2.imshow("warped_img", warped_img)
cv2.imshow("warped_img2", warped_img2)


cv2.waitKey(0)
