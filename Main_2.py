import cv2
# from classes.camera.CameraBuffered import Camera
# from classes.system_utilities.image_utilities import ObjectDetection as OD
from classes.system_utilities.image_utilities import ImageUtilities as IU
# import time
#
def main():
    car_img = cv2.imread("./data/reference footage/images/car_parked3_new_cropped.jpg")

    car_img_grey = cv2.cvtColor(car_img, cv2.COLOR_RGB2GRAY)
    # car_img_hsv = cv2.cvtColor(car_img, cv2.COLOR_BGR2HSV)

    car_img_grey = cv2.bilateralFilter(car_img_grey, 11, 17, 17)

    clahe = cv2.createCLAHE(clipLimit=5)
    final_img = clahe.apply(car_img_grey) + 30

    _, ordinary_img = cv2.threshold(car_img_grey, 155, 255, cv2.THRESH_BINARY)

    # detect edges
    canny = cv2.Canny(ordinary_img, 170, 200)

    # find the contours in canny image
    contours, hierarchy = cv2.findContours(canny.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

    img = car_img.copy()
    cv2.drawContours(img, contours, -1, (0, 255, 0), 3)

    plate_contour = None
    rectangle_sides = 4
    windshield_img = car_img.copy()

    # loop through the sorted contours and find the rectangle shape
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) == rectangle_sides:  # Select the contour with 4 corners
            print("approx", approx)
            plate_contour = approx  # This is our approx Number Plate Contour

            # Crop those contours and store it in Cropped Images folder
            x, y, w, h = cv2.boundingRect(c)  # This will find out co-ord for plate
            windshield_img = ordinary_img[y:y + h, x:x + w]  # Create new image
            break

    # # Drawing the selected contour on the original image
    # img2 = car_img.copy()
    # cv2.drawContours(img2, [plate_contour], -1, (0, 255, 0), 3)



    # cv2.imshow("car_grey", car_img_grey)
    # cv2.imshow("clahe", final_img)
    cv2.imshow("threshold", ordinary_img)
    cv2.imshow("30 best contours", img)
    cv2.imshow("windshield", windshield_img)

    cv2.waitKey(0)

if __name__ == "__main__":
    main()

#     img = LD.DetectLicenseInImage(cv2.imread("./config/license_plate_detector/carr2.jpg"))
#     cv2.imshow("img", img)
#     cv2.waitKey(0)

#     img = cv2.imread("data\\reference footage\\images\\carr2.jpg")
