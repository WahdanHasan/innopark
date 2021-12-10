import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities import Enums
import classes.system_utilities.image_utilities.ObjectDetection as OD
import cv2
import numpy as np

from classes.system_utilities.image_utilities import OCR

OD.OnLoad(model=Enums.YoloModel.LICENSE_DETECTOR)

img = cv2.imread("data\\reference footage\\images\\nisa.jpg")

height, width, _ = img.shape

resized = cv2.resize(img, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
gray = cv2.bilateralFilter(gray, 11, 5, 5)
ret, thresh1 = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)

modified = cv2.erode(thresh1, np.ones((5, 5), np.uint8), iterations=1)

resized = cv2.resize(modified, (width, height), interpolation=cv2.INTER_AREA)

cv2.imshow("img", img)
cv2.imshow("modified", modified)
cv2.imshow("thresh", thresh1)
cv2.imshow("resized", resized)

print(OCR.GetLicenseFromImage(resized))

cv2.waitKey(0)