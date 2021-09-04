import cv2
import numpy as np
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.camera.Camera import Camera
import time
import copy

scale_percentage = 0.5

#mouse function
def SelectPoint(event, x, y, flags, params):
    global point, point_selected, old_points
    if event == cv2.EVENT_LBUTTONDOWN:
        point = (x, y)
        point_selected = True
        old_points = np.array([[x, y]], dtype=np.float32)


cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4")

cv2.namedWindow("Frame")
cv2.setMouseCallback("Frame", SelectPoint)
point_selected = False
point = ()
old_points = np.array([[]])

lk_params = dict(winSize=(15, 15),
                 maxLevel=3,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

_, frame = cap.read()
frame = IU.RescaleImageToScale(frame, scale_factor=scale_percentage)
old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

bbox = [[170, 207], [644,395]] #car_leg_full
frame = IU.DrawBoundingBox(frame, [bbox])

# Create a mask img to see optical flow drawing
mask = np.zeros_like(frame)

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0

cv2.imshow("Frame", frame)
cv2.waitKey(0)
while True:
    _, frame = cap.read()
    frame = IU.RescaleImageToScale(frame, scale_factor=scale_percentage)
    new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    frame = IU.DrawBoundingBox(frame, [bbox])

    if point_selected is False:
        continue

    cv2.circle(frame, point, 5, (0, 0, 255), 2)

    new_points, status, error = cv2.calcOpticalFlowPyrLK(old_gray, new_gray, old_points, None, **lk_params)

    # x, y = new_points.ravel()
    # cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 0), -1)

    # draw the tracks
    for i in range(len(new_points)):
        a, b = new_points.ravel()
        c, d = old_points.ravel()
        a = int(a); b = int(b); c = int(c); d = int(d)
        # draws a line connecting old point with new point
        mask = cv2.line(mask, (a, b), (c, d), (0, 0, 255), 1)
        # draws new point
        frame = cv2.circle(frame, (a, b), 2, (0, 255, 0), 2)

    frame = cv2.add(frame, mask)
    cv2.imshow("Frame", frame)

    old_gray = new_gray.copy()
    #old_points = new_points
    old_points = new_points.reshape(-1, 1, 2)

    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) == 27:
        cap.release()
        cv2.destroyAllWindows()
        break