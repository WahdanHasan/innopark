import numpy as np
import cv2
import time
from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ImageUtilities as IU


<<<<<<< HEAD
def getBlackMask(img, bbox):
=======
#img = cv2.imread("data\\reference footage\\images\\Parked_Car.png")
img = cv2.imread("..\\data\\reference footage\\images\\Parked_Car.png")
mask = np.zeros(img.shape[:2], np.uint8)
>>>>>>> 1c111f395fe0b9dbf0067cffc9dff600cb446f52

	# create an empty mask according to the shape of img
	mask = np.zeros(img.shape[:2], np.uint8)

	# create empty arrays where the bg and fg will be stored
	bgModel = np.zeros((1, 65), np.float64)
	fgModel = np.zeros((1, 65), np.float64)


	# apply GrabCut using the the bounding box segmentation method
	# mask outputs 0 (definite bg), 1 (definite fg), 2 (probable bg), 3 (probable fg)
	(mask, _, _) = cv2.grabCut(img, mask, bbox, bgModel, fgModel, iterCount=5, mode=cv2.GC_INIT_WITH_RECT)

	outputMask = (np.where((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD), 1, 0)*255).astype("uint8")
	return outputMask

#img = cv2.imread("..\\data\\reference footage\\images\\Parked_Car.png")

def main():
	cam_parking = Camera(rtsp_link="data\\reference footage\\videos\\Parking_Open_2.mp4", camera_id=0)


	#rect = (11, 16, 154, 119)
	#rect = (1, 1, 163, 121)
	bbox = [[217, 406], [319, 479]]

	start_time = time.time()
	seconds_before_display = 1  # displays the frame rate every 1 second
	counter = 0

	while True:
		frame_parking = cam_parking.GetScaledLoopingNextFrame()

		#frame_parking_with_bbox = IU.DrawBoundingBox(frame_parking, [bbox])

		# values = (cv2.GC_BGD, cv2.GC_PR_BGD, cv2.GC_FGD, cv2.GC_PR_FGD)
		# # loop over the possible GrabCut mask values
		# for (value) in values:
		# 	# construct a mask that for the current value
		# 	valueMask = (mask == value).astype("uint8") * 255
		#
		# cv2.imshow('mask', valueMask)

		mask = getBlackMask(frame_parking, bbox)
		cv2.imshow('mask', mask)
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