import cv2
from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import time
import numpy as np

def main():

    cam_license = Camera(rtsp_link="data\\reference footage\\videos\\License_3.mp4",
                         camera_id=0)
    cam_parking = Camera(rtsp_link="data\\reference footage\\videos\\Parking_Open_1.mp4",
                         camera_id=0)

    # webcam = Camera(rtsp_link=0,
    #                 camera_id=0)

    new_model = OD.SubtractionModel()

    start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0
    while True:
        frame_license = cam_license.GetScaledLoopingNextFrame()
        frame_parking = cam_parking.GetScaledLoopingNextFrame()
        # webcam_frame = webcam.GetScaledNextFrame()

        # license_return_status, license_classes, license_bounding_boxes, license_scores = OD.DetectLicenseInImage(frame_license)
        #
        # if license_return_status == True:
        #     bb_license = IU.DrawBoundingBoxAndClasses(image=frame_license,
        #                                               class_names=license_classes,
        #                                               probabilities=license_scores,
        #                                               bounding_boxes=license_bounding_boxes)
        #
        #     cv2.imshow("Drawn box license", bb_license)
        #
        # parking_return_status, parking_classes, parking_bounding_boxes, parking_scores = OD.DetectObjectsInImage(frame_parking)

        # if parking_return_status == True:
        #     bb_parking = IU.DrawBoundingBoxAndClasses(image=frame_parking,
        #                                               class_names=parking_classes,
        #                                               probabilities=parking_scores,
        #                                               bounding_boxes=parking_bounding_boxes)
        #
        #     cv2.imshow("Drawn box parking", bb_parking)

        new_model.FeedSubtractionModel(frame_parking)

        boxes = new_model.DetectMovingObjects()

        t_i = IU.DrawBoundingBox(frame_parking, boxes)

        # box_ids = OD.tracker.update(boxes)

        # for box_id in box_ids:
        #     x, y, w, h, id = box_id
        #     cv2.putText(frame_parking, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)
        #     cv2.rectangle(frame_parking, (x, y), (x+w, y+h), (0, 255, 0), 1)

        cv2.imshow("Subtraction Detection", t_i)
        # cv2.imshow("Feed License", frame_license)
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