import cv2
from classes.camera.Camera import Camera
import classes.system_utilities.ImageUtilities as IU

def main():

    cam = Camera(rtsp_link="data\\reference footage\\IP7_Test.mov",
                 camera_id=0)

    img = cv2.imread("data\\reference footage\\example_1.PNG")

    while True:
        frame = cam.GetNextFrame()

        frame = IU.RescaleImage(img=frame,
                                scale_factor=0.5)

        cv2.imshow("Feed", frame)

        text = IU.GetLicenseFromImage(img)

        print(text)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            cv2.destroyAllWindows()

    cv2.waitKey(0)

if __name__ == "__main__":
    main()