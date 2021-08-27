import cv2
import numpy as np
import classes.system_utilities.image_utilities.ImageUtilities as IU
import time


#mouse function
def SelectPoint(event, x, y, flags, params):
    global point, point_selected, old_points
    if event == cv2.EVENT_LBUTTONDOWN:
        point = (x, y)
        point_selected = True
        old_points = np.array([[x, y]], dtype=np.float32)


cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Parking_Open_2.mp4")

#bbox = [[217, 406], [319, 479]]

# Define ShiTomasi params
feature_params = dict(maxCorners=100,
                      qualityLevel=0.3,
                      minDistance=7,
                      blockSize=7)

# Define Lucas Kanae params
lk_params = dict(winSize=(15, 15),
                 maxLevel=3,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# cv2.namedWindow("Fram1")
# cv2.setMouseCallback("Frame1", SelectPoint)

# Create old fram
_, frame = cap.read()
old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

cv2.imshow("gray frame", old_gray)

bbox = [[400, 611], [564,716]]
cropped_frame = IU.CropImage(old_gray, bbox)

# Find corners in old frame
old_points = cv2.goodFeaturesToTrack(cropped_frame, mask=None, **feature_params)

for i in range(len(old_points)):
    old_points[i][0][0] += bbox[0][0]
    old_points[i][0][1] += bbox[0][1]
    if old_points[i][0][0] > frame.shape[1]:
        old_points[i][0][0] = frame.shape[1]

    if old_points[i][0][1] > frame.shape[0]:
        old_points[i][0][1] = frame.shape[0]

#old_points_conv = [1, 2, 3, 4]

# Create a random color
color = np.random.randint(0, 255, (100, 3))

# Create a mask img to see optical flow drawing
mask = np.zeros_like(frame)

point_selected = False
point = ()
#old_points = np.array([[]])

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
while True:
    _, frame = cap.read()
    # cv2.imshow("Frame1", frame)

    new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # if point_selected is True:
    # cv2.circle(frame, point, 5, (0, 0, 255), 2)

    #Lucas Kenade
    # return status as 1 (if next_points are found) and 0 (if none are found)
    # None is for the mask
    # ** lk_params - passing a dictionary
    new_points, status, error = cv2.calcOpticalFlowPyrLK(old_gray, new_gray, old_points, None, **lk_params)

    # select good points
    # if new_points is not None:
    #     good_new = new_points[status==1]
    #     good_old = old_points[status==1]

    # update previous frame and old points
    # so every new frame is being compared to its previous frame
    old_gray = new_gray.copy()
    old_points = new_points.reshape(-1, 1, 2)
