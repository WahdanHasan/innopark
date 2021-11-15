# from classes.system_utilities.image_utilities import LicenseDetection as LD
from classes.system_utilities.image_utilities import ObjectDetection as OD
from classes.camera.CameraBuffered import Camera
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities.Enums import YoloModel
from classes.system_utilities.helper_utilities import Constants
import cv2
import time

OD.OnLoad(model=YoloModel.LICENSE_DETECTOR)
cam = Camera(rtsp_link="data\\reference footage\\test journey\\Entrance_Bottom.mp4",
             camera_id=0)
# img = cv2.imread("data\\reference footage\\images\\Car_Pass3_Parked.jpg")
# img = IU.RescaleImageToResolution(img, (Constants.default_camera_shape[0], Constants.default_camera_shape[1]))
start_time = time.time()
seconds_before_display = 1
counter = 0
while True:
    img = cam.GetScaledNextFrame()
    is_one_detection_above_threshold, bounding_box_classes, bounding_boxes, confidence_scores = OD.DetectObjectsInImage(img)
    # LD.DetectLicenseInImage(img)
    # is_one_license_above_threshold, bounding_box_classes, bounding_boxes, score = LD.DetectLicenseInImage(img)

    frame_processed = IU.DrawBoundingBoxAndClasses(image=img,
                                                   class_names=bounding_box_classes,
                                                   bounding_boxes=bounding_boxes)
    # #
    # # frame_processed = IU.DrawBoundingBoxes(image=img,
    # #                                        bounding_boxes=bounding_boxes)
    #
    # cv2.imshow("test", frame_processed)
    # print(is_one_license_above_threshold)
    # print(score)

    cv2.imshow("LOOOL RAMA ", frame_processed)
    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print(" FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
