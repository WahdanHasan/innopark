from classes.system_utilities.image_utilities import ObjectDetection as OD
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.camera.CameraBuffered import Camera
import time
import cv2

cam = Camera(rtsp_link="data\\journeys\\set_1\\leg_1.mp4", camera_id=0)

OD.OnLoad()
seconds_before_display = 1
counter = 0
start_time = time.time()
while True:
    frame = cam.GetScaledNextFrame()

    is_one_detection_above_threshold, class_names, bounding_boxes, confidence_scores = OD.DetectObjectsInImage(frame)

    frame_processed = IU.DrawBoundingBoxes(image=frame, bounding_boxes=bounding_boxes)


    cv2.imshow("Frame", frame)
    cv2.imshow("Frame processed", frame_processed)

    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break

