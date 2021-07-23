import cv2
from classes.camera.Camera import Camera
import classes.system_utilities.ImageUtilities as IU

def main():

    cam = Camera(rtsp_link="data\\reference footage\\videos\\Parking_Open_1.mp4",
                 camera_id=0)

    # webcam = Camera(rtsp_link=0,
    #                 camera_id=0)

    while True:
        frame = cam.GetScaledNextFrame()
        # webcam_frame = webcam.GetScaledNextFrame()

        cv2.imshow("Feed", frame)

        # IU.DetectObjectsInImage(frame)
        # IU.DetectLicenseInImage(webcam_frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            cv2.destroyAllWindows()

    cv2.waitKey(0)

if __name__ == "__main__":
    main()