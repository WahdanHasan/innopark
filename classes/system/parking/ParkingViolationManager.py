from classes.super_classes.TrackedObjectListener import TrackedObjectListener
from classes.system.parking.ParkingSpace import ParkingSpace
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ParkingStatus
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.data_utilities.Avenues import GetAllParkings
from classes.system_utilities.helper_utilities.Enums import ImageResolution

from multiprocessing import Process, shared_memory
import numpy as np
import cv2
import sys
import json
import time



def main():


    frame = cv2.imread("data\\reference footage\\images\\Car_Pass3_Parked.jpg")

    frame = IU.RescaleImageToResolution(frame, Constants.default_camera_shape[:2])
    IU.SaveImage(frame, "SD_parked")

    # gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #blurred_frame = cv2.GaussianBlur(gray_frame, (5,5), 1)


    height, width = frame.shape[:2]

    # Car endpoints
    # pt_A = [465, 120]
    # pt_B = [465, 365]
    # pt_C = [820, 365]
    # pt_D = [820, 120]

    # Parking endpoint
    # pt_A = [349, 214]
    # # pt_A = [320, 175]
    # pt_B = [480, 391]
    # pt_C = [718, 367]
    # pt_D = [481, 214]
    # pt_D = [500, 170]

    pt_TL = [349, 214]
    pt_TR = [481, 214]
    pt_BL = [480, 391]
    pt_BR = [718, 367]



    # width_AD = np.sqrt(((pt_A[0] - pt_D[0]) ** 2) + ((pt_A[1] - pt_D[1]) ** 2))
    # width_BC = np.sqrt(((pt_B[0] - pt_C[0]) ** 2) + ((pt_B[1] - pt_C[1]) ** 2))
    # maxWidth = max(int(width_AD), int(width_BC))
    #
    # height_AB = np.sqrt(((pt_A[0] - pt_B[0]) ** 2) + ((pt_A[1] - pt_B[1]) ** 2))
    # height_CD = np.sqrt(((pt_C[0] - pt_D[0]) ** 2) + ((pt_C[1] - pt_D[1]) ** 2))
    # maxHeight = max(int(height_AB), int(height_CD))

    # coordinates in the source image
    pts1 = np.float32([pt_TL, pt_TR , pt_BL , pt_BR])
    # pts2 = np.float32([[0,0], [width, 0], [0, height], [width, height]])
    # pts2 = np.float32(np.float32([[0, 0],
    #                     [0, maxHeight - 1],
    #                     [maxWidth - 1, maxHeight - 1],
    #                     [maxWidth - 1, 0]]))

    # coordinates in the output image
    # pts2 = np.float32(np.float32([[0, 0], [width, 0], [width, height], [0, height]]))
    # pts2 = np.float32(np.float32([[width, height], [0, 0], [width, 0], [0, height]]))
    pts2 = np.float32(np.float32([[860, 176], [860, 620], [234, 620], [234, 176]]))

    # T1 = np.float32([[1, 0, int(50 / 2)], [0, 1, int(100 / 2)]])

    # affined_img = cv2.warpAffine(frame, T1, (width + 100, height + 100))

    # warped_img = cv2.warpPerspective(frame, 50, (width + 50, height + 50))

    # Crop plate
    # temp_plate = CropPlate(plate=temp_plate, bounding_set=bounding_set)

    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped_img = cv2.warpPerspective(frame, matrix, (width, height))


    for x in range(4):
        cv2.circle(frame, (int(pts1[x][0]), int(pts1[x][1])), 5, (0,0,255), cv2.FILLED)

    cv2.imshow("original img: ", frame)
    cv2.imshow("output img: ", warped_img)
    cv2.waitKey(0)

    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # # cv2.imshow("converted to gray", gray)
    #
    # # gray = cv2.medianBlur(gray, 5)
    # cv2.imshow("blurred gray", gray)
    # # cv2.waitKey(0)
    #
    # rows = gray.shape[0]
    # print("rows: ", rows)




    # CONTOURS
    # r = 20
    # ret,gray_threshed = cv2.threshold(gray,r,255,cv2.THRESH_BINARY)
    # edge_detected_image = cv2.Canny(gray, 75, 200)
    #
    # contours, _ = cv2.findContours(edge_detected_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # contour_list = []
    # for contour in contours:
    #     # approximte for circles
    #     approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
    #     area = cv2.contourArea(contour)
    #     if ((len(approx) > 8) & (area > 30)):
    #         contour_list.append(contour)
    #
    # # Draw contours on the original image
    # cv2.drawContours(frame, contour_list, -1, (255, 0, 0), 2)

    # # there is an outer boundary and inner boundary for each edge, so contours double
    # print('Number of found circles: {}'.format(int(len(contour_list) / 2)))


    # HOUGH CIRCLE
    # circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, rows / 8,
    #                           param1=200, param2=30,
    #                           minRadius=80, maxRadius=0)
    #
    # if circles is not None:
    #     print("found circles!!!!!!!")
    #     circles = np.uint16(np.around(circles))
    #     for i in circles[0, :]:
    #         center = (i[0], i[1])
    #         # circle center
    #         cv2.circle(frame, center, 1, (0, 100, 100), 3)
    #         # circle outline
    #         radius = i[2]
    #         cv2.circle(frame, center, radius, (255, 0, 255), 3)


    # HOUGHLINES
    # edges = cv2.Canny(gray, 50, 200)
    # # Detect points that form a line
    # lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 150, minLineLength=10, maxLineGap=250)
    # # Draw lines on the image
    # for line in lines:
    #     x1, y1, x2, y2 = line[0]
    #     cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

    # cv2.imshow("detected circles", frame)
    # cv2.waitKey(0)
# get the parking slot region (determine the region of interest)

# construct the bg to know what's bg and fg (Guassuan Mixture Model [GMM]).
# Get mask of car using background subtraction model -- using morphological algo for it to be filled
#

# detect and filter the car that's in the fg
# detect number of wheels







# track the object??


if __name__ == "__main__":
    main()
