import cv2
import numpy as np
import time

cap = cv2.VideoCapture("C:\\Users\\wahda\\PycharmProjects\\InnoPark\\data\\reference footage\\videos\\Parking_Open_2.mp4")


old_pts = np.array([[475, 628], [512, 689], [498, 628], [409, 671], [415, 621]], dtype="float32").reshape(-1, 1, 2)

_, frame = cap.read()
old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
mask = np.zeros_like(frame)

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
while True:
    _, frame2 = cap.read()

    new_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    new_pts, status, err = cv2.calcOpticalFlowPyrLK(old_gray,
                                                    new_gray,
                                                    old_pts,
                                                    None, maxLevel=1,
                                                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                                                              15, 0.08))

    for i in range(len(new_pts)):
        cv2.circle(frame2, (int(new_pts[i][0][0]), int(new_pts[i][0][1])), 2, (0, 255, 0), 2)
    combined = cv2.addWeighted(frame2, 0.7, mask, 0.3, 0.1)

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
