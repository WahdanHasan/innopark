import cv2
# from classes.camera.CameraBuffered import Camera
# from classes.system_utilities.image_utilities import ObjectDetection as OD
# from classes.system_utilities.image_utilities import ImageUtilities as IU
# import time
#
def main():
    LD.DetectLicenseInImage(cv2.imread("./config/license_plate_detector/carr2.jpg"))



if __name__ == "__main__":
    main()

#     img = LD.DetectLicenseInImage(cv2.imread("./config/license_plate_detector/carr2.jpg"))
#     cv2.imshow("img", img)
#     cv2.waitKey(0)

#     img = cv2.imread("data\\reference footage\\images\\carr2.jpg")
