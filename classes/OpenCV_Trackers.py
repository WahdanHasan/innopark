import cv2
from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ImageUtilities as IU
import time
import numpy as np

def main():
    # cam_parking = Camera(rtsp_link="..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4",
    #                      camera_id=0)

    cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4")

    start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0

    # Set up tracker
    #tracker_types = ['BOOSTING', 'MIL', 'KCF', 'CSRT', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE']
    tracker_types = ['BOOSTING', 'MIL', 'KCF', 'CSRT', 'TLD', 'MEDIANFLOW', 'MOSSE']

    # Change the index to change the tracker type
    tracker_type = tracker_types[2]

    if tracker_type == 'BOOSTING':
        tracker = cv2.legacy_TrackerBoosting.create()
    elif tracker_type == 'MIL':
        tracker = cv2.TrackerMIL_create()
    elif tracker_type == 'KCF':
        tracker = cv2.TrackerKCF_create()
    elif tracker_type == 'CSRT':
        tracker = cv2.legacy_TrackerCSRT.create()
    elif tracker_type == 'TLD':
        tracker = cv2.legacy_TrackerTLD.create()
    elif tracker_type == 'MEDIANFLOW':
        tracker = cv2.legacy_TrackerMedianFlow.create()
    else:
        tracker = cv2.legacy_TrackerMOSSE.create()

    # frame = cam_parking.GetScaledNextFrame()
    _, frame = cap.read()
    frame = IU.RescaleImageToScale(frame, 0.5)
    # bbox = (222, 398, 312, 476)
    # bbox = (130, 181, 482, 353)
    bbox = (170, 207, 644, 395)
    #bbox = [[170, 207], [644, 395]]


    bbox_partial = [[[bbox[0], bbox[1]], [bbox[2], bbox[3]]]]
    t_i = IU.DrawBoundingBox(frame, bbox_partial)
    cv2.imshow(tracker_type, t_i)

    ok = tracker.init(frame, bbox)

    fps = 0
    while True:
        _, frame = cap.read()
        frame = IU.RescaleImageToScale(frame, 0.5)

        # Update tracker
        ok, bbox = tracker.update(frame)
        if not ok:
            continue

        if (time.time() - start_time) > seconds_before_display:
            fps = counter / (time.time() - start_time)
            counter = 0
            start_time = time.time()

        bbox_t = [1,2,3,4]
        bbox_t[0] = int(bbox[0])
        bbox_t[1] = int(bbox[1])
        bbox_t[2] = int(bbox[2])
        bbox_t[3] = int(bbox[3])
        bbox = bbox_t
        bbox_partial = [[[bbox[0], bbox[1]], [bbox[2], bbox[3]]]]

        t_i = IU.DrawBoundingBox(frame, bbox_partial)

        # Display Info
        cv2.putText(t_i, tracker_type + " Tracker", (150, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        cv2.putText(t_i, "FPS : " + str(int(fps)), (150, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        cv2.imshow(tracker_type, t_i)
        #cv2.imshow("Feed Parking", frame)
        counter += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    main()