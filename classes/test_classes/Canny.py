import numpy as np
import cv2
import time
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.camera.Camera import Camera

def callback(x):
    print(x)

def ApplyCanny(img):
    canny = cv2.Canny(img, 100, 255)
    return canny



def main():
	#cam_parking = Camera(rtsp_link="..\\data\\reference footage\\images\\canny_before\\canny_carInFocus_manyCars_before.png", camera_id=0)

	start_time = time.time()
	seconds_before_display = 1  # displays the frame rate every 1 second
	counter = 0

	cv2.namedWindow('image')  # make a window with name 'image'
	cv2.createTrackbar('L', 'image', 0, 1000, callback)  # lower threshold trackbar for window 'image
	cv2.createTrackbar('U', 'image', 0, 1000, callback)  # upper threshold trackbar for window 'image

	img = cv2.imread("..\\data\\reference footage\\images\\canny_before\\canny_carInFocus_manyCars_before.png")
	while True:
		l = cv2.getTrackbarPos('L', 'image')
		u = cv2.getTrackbarPos('U', 'image')
		#
		# canny_img = canny = cv2.Canny(frame_parking, l, u)

		# med_val = np.median(img)
		# print(med_val)
		# lower = int(max(0, 0.7 * med_val))
		# upper = int(min(255, 1.3 * med_val))
		# print("lower", lower)
		# print("upper", upper)
		# edges = cv2.Canny(image=img, threshold1=lower, threshold2=upper)

		# The standard stuff: image reading, grayscale conversion, inverting, morphology & edge detection
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		gray = cv2.bitwise_not(gray)
		sqKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
		gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, sqKernel)
		thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
		edges = cv2.Canny(thresh, 50, 200)

		# Finding and sorting contours based on contour area
		cnts = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cnts = cnts[0] if len(cnts) == 2 else cnts[1]
		cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

		# Filling the contours with black color
		for c in cnts:
			cv2.drawContours(img, [c], -1, (0, 0, 0), -1)

		cv2.imshow('canny_img', img)

		#cv2.waitKey(0)

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