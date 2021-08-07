import numpy as np
import cv2
import time
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.camera.Camera import Camera

#img = cv2.imread("data\\reference footage\\images\\Parked_Car.png")

def getBlackMask(img, bbox):
	# get cropped img
	cropped_img, enlarged_bbox = getCroppedImageAndEnlargedBbox(img, bbox)

	#get the resized bbox
	resized_bbox = getResizedBbox(bbox, enlarged_bbox)

	# create an empty mask according to the shape of img
	mask = np.zeros(cropped_img.shape[:2], np.uint8)

	# create empty arrays where the bg and fg will be stored
	bgModel = np.zeros((1, 65), np.float64)
	fgModel = np.zeros((1, 65), np.float64)


	# apply GrabCut using the the bounding box segmentation method
	# mask outputs 0 (definite bg), 1 (definite fg), 2 (probable bg), 3 (probable fg)
	bbox_converted = [resized_bbox[0][0], resized_bbox[0][1], resized_bbox[1][0], resized_bbox[1][1]]

	(mask, _, _) = cv2.grabCut(cropped_img, mask, bbox_converted, bgModel, fgModel, iterCount=7, mode=cv2.GC_INIT_WITH_RECT)


	outputMask = (np.where((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD), 1, 0)*255).astype("uint8")
	output = cv2.bitwise_and(cropped_img, cropped_img, mask=outputMask)
	cv2.imshow("Input", cropped_img)
	cv2.imshow("GrabCut Mask", outputMask)
	cv2.imshow("GrabCut Output", output)
	cv2.waitKey(1)

	return outputMask

def getCroppedImageAndEnlargedBbox(img, bbox):
	percentage = 0.1
	height, width, _ = img.shape

	bbox2 = [[bbox[0][0], bbox[0][1]], [bbox[1][0], bbox[1][1]]]

	# increase the TL
	for y in range(2):
		bbox2[0][y] = int(bbox2[0][y] - (bbox2[0][y] * percentage))
		if bbox2[0][y] < 0:
			bbox2[0][y] = 0

	#increase the BR
	bbox2[1][0] = int(bbox2[1][0] + (bbox2[1][0] * percentage))
	if bbox2[1][0] > width:
		bbox2[1][0] = width

	bbox2[1][1] = int(bbox2[1][1] + (bbox2[1][1] * percentage))
	if bbox2[1][1] > height:
		bbox2[1][1] = height

	cropped_img = IU.CropImage(img, bbox2)

	return cropped_img, bbox2

def getResizedBbox(bbox, enlarged_bbox):
	TL = [bbox[0][0]-enlarged_bbox[0][0], bbox[0][1]-enlarged_bbox[0][1]]
	BR = [bbox[1][0] - enlarged_bbox[0][0], bbox[1][1]-enlarged_bbox[0][1]]

	bbox2 = [[TL[0], TL[1]], [BR[0], BR[1]]]

	return bbox2


def main():
	cam_parking = Camera(rtsp_link="..\\data\\reference footage\\videos\\Parking_Open_2.mp4", camera_id=0)

	bbox = [[217, 406], [319, 479]]

	start_time = time.time()
	seconds_before_display = 1  # displays the frame rate every 1 second
	counter = 0

	while True:
		frame_parking = cam_parking.GetScaledNextFrame()

		#frame_parking_with_bbox = IU.DrawBoundingBox(frame_parking, [bbox])

		# values = (cv2.GC_BGD, cv2.GC_PR_BGD, cv2.GC_FGD, cv2.GC_PR_FGD)
		# # loop over the possible GrabCut mask values
		# for (value) in values:
		# 	# construct a mask that for the current value
		# 	valueMask = (mask == value).astype("uint8") * 255
		#
		# cv2.imshow('mask', valueMask)

		mask = getBlackMask(frame_parking, bbox)


		#cv2.imshow('mask', mask)

		#output = cv2.bitwise_and(img, img, mask=outputMask)


		counter += 1
		if (time.time() - start_time) > seconds_before_display:
			print("FPS: ", counter / (time.time() - start_time))
			counter = 0
			start_time = time.time()

		if cv2.waitKey(1) & 0xFF == ord('q'):
			cv2.destroyAllWindows()
			break

if __name__ == "__main__":
    main()