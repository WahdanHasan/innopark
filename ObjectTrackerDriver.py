import cv2
from classes.camera.Camera import Camera
# import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import classes.system_utilities.image_utilities.ObjectTracker as OT

import time
import numpy as np



def main():
    cam_parking = Camera(rtsp_link="data\\reference footage\\videos\\Parking_Open_2.mp4",
                         camera_id=0)

    parked_car_mask = cv2.imread("data\\reference footage\\images\\Parked_Car_3_Mask.png")

    tracker = OT.Tracker(cam_parking)
    bounding_box = [[217, 406], [319, 479]]
    tracked_object = OT.TrackedObjectProcess([0, "A35020", bounding_box])
    tracked_object.mask = parked_car_mask

    tracker.AddToMask(tracked_object)

    start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0

    bounding_box = [[397, 599], [566, 718]]
    parked_car = cv2.imread("data\\reference footage\\images\\Parked_Car.png")
    parked_car_mask = cv2.imread("data\\reference footage\\images\\Parked_Car_Mask.png")
    isolated_car = cv2.subtract(parked_car, parked_car_mask)
    removed_car = cv2.subtract(parked_car_mask, parked_car)

    dst = cv2.Canny(parked_car, 50, 200, None, 3)
    # Copy edges to the images that will display the results in BGR
    cdst = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)
    cdstP = np.copy(cdst)

    linesP = cv2.HoughLinesP(dst, 1, np.pi / 180, 50, None, 50, 10)

    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[i][0]
            cv2.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv2.LINE_AA)




    cv2.imshow("Isolated Car", IU.RescaleImageToScale(isolated_car, 3.0))
    cv2.imshow("Removed Car", IU.RescaleImageToScale(removed_car, 3.0))
    cv2.imshow("Removed Car hough", IU.RescaleImageToScale(dst, 3.0))
    cv2.waitKey(0)
    x = 0
    while True:
        x = x + 1
        frame_parking = cam_parking.GetScaledNextFrame()

        subtracted_from_mask = tracker.SubtractMaskFromImage(frame_parking, tracker.base_mask)
        if x == 1000:
            tracker.RemoveFromMask(tracked_object)
        base_mask = tracker.base_mask

        frame_parking = IU.DrawBoundingBoxes(frame_parking, [tracked_object.bounding_box])

        dst = cv2.Canny(frame_parking, 50, 200, None, 3)

        cv2.imshow("OTD: canny", dst)
        cv2.imshow("OTD: Subtracted", subtracted_from_mask)
        cv2.imshow("OTD: Base Mask", base_mask)
        cv2.imshow("OTD: Parking Feed", frame_parking)
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