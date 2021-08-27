import cv2
import numpy as np
import time
from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ImageUtilities as IU

cap = Camera(rtsp_link="C:\\Users\\wahda\\PycharmProjects\\InnoPark\\data\\reference footage\\videos\\Car_Pass3.mp4",
             camera_id=0)


old_pts = np.array([[200, 140], [200, 160]], dtype="float32").reshape(-1, 1, 2)

frame = cap.GetScaledNextFrame()

old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
mask = np.zeros_like(frame)

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
while True:
    frame2 = cap.GetScaledNextFrame()

    new_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    new_pts, status, err = cv2.calcOpticalFlowPyrLK(old_gray,
                                                    new_gray,
                                                    old_pts,
                                                    None, maxLevel=10,
                                                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                                                              15, 0.08))

    for i in range(len(new_pts)):
        cv2.circle(frame2, (int(new_pts[i][0][0]), int(new_pts[i][0][1])), 2, (0, 255, 0), 2)
    combined = cv2.addWeighted(mask, 0.7, mask, 0.3, 0.1)

    cv2.imshow("new win", mask)
    cv2.imshow("new", frame2)
    # cv2.imshow("wind", combined)

    old_gray = new_gray.copy()
    old_pts = new_pts.copy()
    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) == 27:
        cap.release()
        cv2.destroyAllWindows()
        break
