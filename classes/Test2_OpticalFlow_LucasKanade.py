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

# cv2.namedWindow("Frame1")
# cv2.setMouseCallback("Frame1", SelectPoint)
# point_selected = False
# point = ()

# to be put inside the while True
# if point_selected is True:
    # cv2.circle(frame, point, 5, (0, 0, 255), 2)

# if frame_count % features_refresh_rate == 0: # regenerate features every "features_refresh_rate" frames
#     frame = cap.GetRawNextFrame()
#     old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     old_points = GetBboxGoodFeatures(bbox, old_gray)
#     mask = np.zeros_like(frame)
#     features_refresh_count+=1

#cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Car_Pass_Starting_Full.mp4")
cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4")
#cap = Camera("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4", 0)
#cap = Camera("..\\data\\reference footage\\videos\\Car_Pass_Starting_Full.mp4", 0)
#cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Parking_Open_2.mp4")

#bbox = [[217, 406], [319, 479]]

# Define ShiTomasi params
# feature_params = dict(maxCorners=100, # number of points to locate
#                       qualityLevel=0.3, # min quality(0-1); everyone below is rejected
#                       minDistance=7, # min eucledian distance b/w corners detected
#                       blockSize=7) # size of an avg block for computing a derivative covariance (directional relationship b/w 2 random variables, aka how 2 random variables will change together)

feature_params = dict(maxCorners=100,
                      qualityLevel=0.1,
                      minDistance=7,
                      blockSize=3)

# # Define Lucas Kanae params
# lk_params = dict(winSize=(15, 15), # size of search window at each pyramid level
#                  maxLevel=3, # 0 indicates zero pyramids (single level), 1 indicates 1 pyramid (2 levels)
#                  criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

lk_params = dict(winSize=(15, 15), # to avoid aperature problems, make it smaller, but in turn points dont re-allocate correctly
                 maxLevel=3,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
                # criteria- telling the algo to end after some number of iteration (TERM_CRITERIA ITER),
                # or when then convergence metric reaches some small value, aka search window moves by less than than epsilon value (TERM_CRITERIA_EPS)

# Create old fram
_, frame = cap.read()
#frame = cap.GetRawNextFrame()
frame = cv2.resize(frame, (int(frame.shape[1]*scale_percentage), int(frame.shape[0]*scale_percentage)), interpolation=cv2.INTER_AREA)
old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#bbox = [[38, 247], [530,419]] #car_pass_full
bbox = [[170, 207], [644,395]] #car_leg_full
#bbox = [[400, 611], [564,716]] #bbox of Parking_Open_2
bbox_tl = [170, 207]
bbox_br = [644, 395]

# initialize array
old_points = np.zeros((1, 2))

def GetBboxGoodFeatures(bbox, gray):
    cropped_frame = IU.CropImage(gray, bbox)

    points = cv2.goodFeaturesToTrack(cropped_frame, mask=None,
                                       maxCorners=2,
                                       qualityLevel=0.03,
                                       minDistance=7,
                                       blockSize=3)

    # draw the points
    for i in range(len(points)):
        a, b = points[i].ravel()
        out_img3 = cv2.circle(cropped_frame, (int(a), int(b)), 2, (0, 0, 255), 2)

    cv2.imshow('img3', out_img3)
    cv2.waitKey(0)

    # translate old_points of bbox to the non-cropped frame
    for i in range(len(points)):
        points[i][0][0] += bbox[0][0]
        points[i][0][1] += bbox[0][1]
        if points[i][0][0] > frame.shape[1]:
            points[i][0][0] = frame.shape[1]

        if points[i][0][1] > frame.shape[0]:
            points[i][0][1] = frame.shape[0]

    return points


old_points = GetBboxGoodFeatures(bbox, old_gray)
# plot keypoints on the image

# Create a random color
color = np.random.randint(0, 255, (100, 3))

# Create a mask img to see optical flow drawing
mask = np.zeros_like(frame)

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
while True:
    _, frame = cap.read()
    #frame = cap.GetRawNextFrame()
    frame = cv2.resize(frame, (int(frame.shape[1] * scale_percentage), int(frame.shape[0] * scale_percentage)), interpolation=cv2.INTER_AREA)

    new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #Lucas Kenade
    # return status as 1 (if next_points are found) and 0 (if none are found)
    # None is for the mask
    # ** lk_params - passing a dictionary

    # print("bbox before: TL - ", bbox_tl, "| BR - ", bbox_br)
    # print("predicted estimates:", (int(x), int(y)))
    # bbox_tl[0] = int(bbox_tl[0] + (int(x) - x_old))
    # bbox_tl[1] = int(bbox_tl[1] + (int(y) - y_old))
    # bbox_br[0] = int(bbox_br[0] + (int(x) - x_old))
    # bbox_br[1] = int(bbox_br[1] + (int(y) - y_old))
    # print("bbox after: TL - ", bbox_tl, "| BR - ", bbox_br)
    # # cv2.rectangle(frame, (bbox_tl[0], bbox_tl[1]), (bbox_br[0], bbox_br[1]), (255, 0, 0), 2)
    # frame = IU.DrawBoundingBox(frame, [[bbox_tl, bbox_br]])
    #
    new_points, status, error = cv2.calcOpticalFlowPyrLK(old_gray, new_gray, old_points, None, **lk_params)

    # select good points
    if new_points is not None:
        good_new = new_points[status==1]
        good_old = old_points[status==1]

    # #draw the points
    # for i in range(len(new_points)):
    #     a, b = new_points[i].ravel()
    #     cv2.circle(frame, (int(a), int(b)), 2, (0, 255, 0), 2)

    # draw new bbox
    # x to the right, increases
    # y to up, decreases
    change = ((old_points[1][0][0] - new_points[1][0][0]), (old_points[1][0][1] - new_points[1][0][1]))
    if (int(change[0]) !=0): # if there's no significant change, don't move box
        bbox_tl[0] = int(bbox_tl[0] - change[0])
        bbox_br[0] = int(bbox_br[0] - change[0])
        #bbox_tl[1] = int(bbox_tl[1] - change[1])
        #bbox_br[1] = int(bbox_br[1] - change[1])
        print("CHANGE HAPPENED")

    print("old points: ", old_points, "new points: ", new_points)
    print("CHANGE: ", change)
    print("bbox_tl: ", bbox_tl, "bbox_br: ", bbox_br, "\n\n")
    frame1 = IU.DrawBoundingBox(frame, [[bbox_tl, bbox_br]])
    #cv2.waitKey(100)

    # draw the tracks
    for i, (new, old) in enumerate(zip(good_new, good_old)):
       a, b = new.ravel()
       c, d = old.ravel()
       a = int(a); b = int(b); c = int(c); d = int(d)
       # draws a line connecting old point with new point
       mask = cv2.line(mask, (a, b), (c, d), (0, 0, 255), 1)
       # draws new point
       frame = cv2.circle(frame, (a, b), 2, (0, 255, 0), 2)

    frame = cv2.add(frame, mask)
    cv2.imshow("Frame", frame)
    cv2.imshow("Frame_bbox", frame1)
    # update previous frame and old points
    # so every new frame is being compared to its previous frame
    old_gray = new_gray.copy()
    old_points = new_points.reshape(-1, 1, 2)
    #old_point_move_bbox = (old_points[0][0][0], old_points[0][0][1])

    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) == 27:
        cap.release()
        cv2.destroyAllWindows()
        break