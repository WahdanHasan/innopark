import cv2
import classes.test.classes.Beta_ProcessLicenseFrames as PL
import classes.system_utilities.image_utilities.LicenseDetection_Custom as LD
from classes.camera.CameraBuffered import Camera

def main():
    x=0
    #LD.BuildModel()
    # LD.OnLoad()
    # LD.DetectLicenseInImage(cv2.imread("./config/license_plate_detector/carr2.jpg"))

    #pl = PL.ProcessLicenseFrames()
    #LD.OnLoad()
    # pl.DetectLicensePlates()

    # cam_license = Camera(
    #     rtsp_link="D:\\ProgramData\\Grad Project\\Experiments\\License_Footage\\Entrance_Bottom_Simulated_2.mp4",
    #     camera_id=0)
    #
    # frame_licenses = []
    #
    # for i in range(12):
    #     img = cv2.imread("./data/saves/frame"+str(i+1)+".png")
    #     frame_licenses.append(img)
    #
    # while True:
    #
    #     pl.DetectLicensePlates(frame_licenses)
    #     print("out in main")

        # license_return_status, license_classes, license_bounding_boxes, license_scores = pl.DetectLicenseInImage(
        #     frame_license)
        #
        # if license_return_status == True:
        #     bb_license = IU.DrawBoundingBoxAndClasses(image=frame_license,
        #                                               class_names=license_classes,
        #                                               probabilities=license_scores,
        #                                               bounding_boxes=license_bounding_boxes)
        #
        #     cv2.imshow("Drawn box license", bb_license)

        # if cv2.waitKey(100) & 0xFF == ord('q'):
        #     cv2.destroyAllWindows()
        #     break
if __name__ == "__main__":
    main()