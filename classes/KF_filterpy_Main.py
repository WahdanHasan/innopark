import cv2
import numpy as np
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.camera.Camera import Camera
import time
import copy

scale_percentage = 0.5

#cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Car_Pass_Starting_Full.mp4")
cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4")
#cap = Camera("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4", 0)
#cap = Camera("..\\data\\reference footage\\videos\\Car_Pass_Starting_Full.mp4", 0)
#cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Parking_Open_2.mp4")

#bbox = [[217, 406], [319, 479]]

feature_params = dict(maxCorners=100,
                      qualityLevel=0.1,
                      minDistance=7,
                      blockSize=3)

lk_params = dict(winSize=(15, 15),
                 maxLevel=3,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))


_, frame = cap.read()
frame = cv2.resize(frame, (int(frame.shape[1]*scale_percentage), int(frame.shape[0]*scale_percentage)), interpolation=cv2.INTER_AREA)
old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#bbox = [[38, 247], [530,419]] #car_pass_full
bbox = [[170, 207], [644,395]] #car_leg_full
#bbox = [[400, 611], [564,716]] #bbox of Parking_Open_2
# bbox_tl = [170, 207]
# bbox_br = [644, 395]

def GetBboxGoodFeatures(bbox, gray):
    cropped_frame = IU.CropImage(gray, bbox)

    points = cv2.goodFeaturesToTrack(cropped_frame, mask=None,
                                       maxCorners=5,
                                       qualityLevel=0.03,
                                       minDistance=7,
                                       blockSize=3)


    # translate old_points of bbox to the non-cropped frame
    for i in range(len(points)):
        points[i][0][0] += bbox[0][0]
        points[i][0][1] += bbox[0][1]
        if points[i][0][0] > frame.shape[1]:
            points[i][0][0] = frame.shape[1]

        if points[i][0][1] > frame.shape[0]:
            points[i][0][1] = frame.shape[0]

    # draw the points
    for i in range(len(points)):
        a, b = points[i].ravel()
        img = cv2.circle(frame, (int(a), int(b)), 2, (0, 255, 0), 2)
        cv2.imshow("initial points", img)

    return points

def boundOpticalFlowPoints(frame, points):
    height, width = frame.shape[:2]
    leftMost_x = width
    rightMost_x = 0
    top_y = height
    bottom_y = 0
    for i in range(len(points)):
        a, b = points[i].ravel()
        if a < leftMost_x:
            leftMost_x = a
        if b < top_y:
            top_y = b
        if a > rightMost_x:
            rightMost_x = a
        if b > bottom_y:
            bottom_y = b

    bbox_tl = [int(leftMost_x), int(top_y)]
    bbox_br = [int(rightMost_x), int(bottom_y)]

    return bbox_tl, bbox_br

def convert_bbox_to_z(bbox):
    """
    Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
    [x,y,s,r] where x,y is the centre of the box and s is the scale/area and r is
    the aspect ratio
    """
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]
    x = bbox[0]+w/2.
    y = bbox[1]+h/2.
    s = w*h    #scale is just area
    r = w/float(h)
    return np.array([x,y,s,r]).reshape((4,1))

old_points = GetBboxGoodFeatures(bbox, old_gray)
bbox_tl, bbox_br = boundOpticalFlowPoints(frame, old_points)

# Create a random color
color = np.random.randint(0, 255, (100, 3))

# Create a mask img to see optical flow drawing
mask = np.zeros_like(frame)

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
frame_counter = 1
while True:
    frame_counter+=1
    t1 = time.time() - start_time
    _, frame = cap.read()
    frame = cv2.resize(frame, (int(frame.shape[1] * scale_percentage), int(frame.shape[0] * scale_percentage)), interpolation=cv2.INTER_AREA)

    new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #Lucas Kenade
    new_points, status, error = cv2.calcOpticalFlowPyrLK(old_gray, new_gray, old_points, None, **lk_params)
    t2 = time.time() - start_time

    # draw new bbox
    change = ((old_points[0][0][0] - new_points[0][0][0]), (old_points[0][0][1] - new_points[0][0][1]))
    if (int(change[0]) !=0): # if there's no significant change, don't move box
        bbox_tl, bbox_br = boundOpticalFlowPoints(frame, new_points)
        # bbox_tl[0] = int(bbox_tl[0] - change[0])
        # bbox_br[0] = int(bbox_br[0] - change[0])
        # #bbox_tl[1] = int(bbox_tl[1] - change[1])
        # #bbox_br[1] = int(bbox_br[1] - change[1])
        # print("CHANGE HAPPENED")
    frame1 = IU.DrawBoundingBoxes(frame, [[bbox_tl, bbox_br]])

    #get rid of inconsistent points
    print("new: ", new_points)
    print("old: ", old_points)
    if(frame_counter % 7 == 0):
        print("LENGTH: ", len(new_points))
        for i in range(len(new_points)):
            a, b = new_points[i].ravel()
            c, d = old_points[i].ravel()
            velocity = [((a-c)/(t2-t1)), ((b-d)/(t2-t1))]
            if (velocity[0] == 0.000 and velocity[1]==0.000):
                print("element DELETED: ", i)
                new_points = np.delete(new_points, [i], axis=0)
                for i in range(len(new_points)):
                    a, b = new_points[i].ravel()
                    cv2.circle(frame, (int(a), int(b)), 2, (0, 255, 0), 2)
                cv2.imshow("Frame_bbox", frame)
                cv2.waitKey(0)
                break


    # draw the points
    for i in range(len(new_points)):
        a, b = new_points[i].ravel()
        cv2.circle(frame, (int(a), int(b)), 2, (0, 255, 0), 2)

    cv2.imshow("Frame_bbox", frame)

    # update previous frame and old points
    # so every new frame is being compared to its previous frame
    old_gray = new_gray.copy()
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