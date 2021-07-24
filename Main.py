import cv2
from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import time
import numpy as np

def main():

    cam_license = Camera(rtsp_link="data\\reference footage\\videos\\License_2.mp4",
                         camera_id=0)
    cam_parking = Camera(rtsp_link="data\\reference footage\\videos\\Parking_Open_1.mp4",
                         camera_id=0)

    # webcam = Camera(rtsp_link=0,
    #                 camera_id=0)

    start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0
    while True:
        frame_license = cam_license.GetScaledLoopingNextFrame()
        frame_parking = cam_parking.GetScaledLoopingNextFrame()
        # webcam_frame = webcam.GetScaledNextFrame()


        cv2.imshow("Feed License", frame_license)
        cv2.imshow("Feed Parking", frame_parking)


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