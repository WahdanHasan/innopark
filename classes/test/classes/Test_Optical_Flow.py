import cv2
import numpy as np
import math
import copy
import time
from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ImageUtilities as IU

cap = Camera(rtsp_link="E:\\PycharmProjects\\InnoPark\\data\\reference footage\\videos\\Car_Pass3.mp4",
             camera_id=0)


# old_pts = np.array([[200, 140], [200, 160]], dtype="float32").reshape(-1, 1, 2)
frame = cap.GetScaledNextFrame()

old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

bbox = [[190, 114], [250, 180]]

cropped = IU.CropImage(frame, bbox)
cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

old_pts = cv2.goodFeaturesToTrack(cropped_gray, 100, 0.5, 10)

# bbox_p = [[int(bbox[0][0]/720), int(bbox[0][1]/480)], [int(bbox[1][0]/720), int(bbox[1][1]/480)]]


for i in range(len(old_pts)):
    old_pts[i][0][0] = float(old_pts[i][0][0] + bbox[0][0])
    old_pts[i][0][1] = float(old_pts[i][0][1] + bbox[0][1])


mask = np.zeros_like(frame)
print(mask.shape)
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
        cv2.circle(mask, (int(new_pts[i][0][0]), int(new_pts[i][0][1])), 2, (0, 255, 0), 2)
    # combined = cv2.addWeighted(frame2, 1.0, mask, 1.0, 1.0)
    combined = cv2.add(mask, frame2)

    avg_x = 0
    avg_y = 0
    for i in range(len(new_pts)):
        x, y = new_pts[i].ravel()
        x_o, y_o = old_pts[i].ravel()
        # t_x = x + self.bb[0][0]
        # t_y = y + self.bb[0][1]
        cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
        avg_x += (x - x_o)
        avg_y += (y - y_o)

    avg_x = avg_x / len(new_pts)
    avg_y = avg_y / len(new_pts)

    bbox = [[bbox[0][0] + avg_x, bbox[0][1] + avg_y], [bbox[1][0] + avg_x, bbox[1][1] + avg_y]]

    frame2 = cv2.rectangle(img=frame2,
                               pt1=[int(bbox[0][0]),int(bbox[0][1])],
                               pt2=[int(bbox[1][0]),int(bbox[1][1])],
                               color=(0, 255, 0),
                               thickness=2)

    cv2.imshow("new win", mask)
    cv2.imshow("new", frame2)
    cv2.imshow("comb", combined)

    old_gray = copy.deepcopy(new_gray)
    old_pts = copy.deepcopy(new_pts)
    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) == 27:
        cap.release()
        cv2.destroyAllWindows()
        break
