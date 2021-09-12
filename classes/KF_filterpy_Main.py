import cv2
import numpy as np
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.camera.Camera import Camera
import time
import copy

from KalmanFilter2D import KalmanFilter2D

scale_percentage = 0.5

cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4")

#cap = cv2.VideoCapture("..\\data\\reference footage\\videos\\Car_Pass3.mp4")

feature_params = dict(maxCorners=1,
                      qualityLevel=0.01,
                      minDistance=7,
                      blockSize=3)

lk_params = dict(winSize=(15, 15),
                 maxLevel=3,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

_, frame = cap.read()
frame = IU.RescaleImageToScale(frame, scale_factor=scale_percentage)
old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# cv2.imshow("frame", frame)
# cv2.waitKey()

bbox = [[170, 207], [644,395]] #car_leg_full
bbox_tl = [170, 207]
bbox_br = [644, 395]
# bbox = [[99, 85], [187,200]] #car_pass3_before_barrier

# initialize array
old_points = np.zeros((1, 2))

#mouse function
def SelectPoint(event, x, y, flags, params):
    global selectedPoint, point_selected, old_points
    if event == cv2.EVENT_LBUTTONDOWN:
        selectedPoint = (int(x), int(y))
        point_selected = True
        old_points = np.array([[x, y]], dtype=np.float32)

# cv2.namedWindow("Frame")
# cv2.setMouseCallback("Frame", SelectPoint)
# point_selected = False
# selectedPoint = ()

# cv2.imshow('Frame', frame)
# cv2.waitKey(0)

def GetBboxGoodFeatures(bbox, gray):
    cropped_frame = IU.CropImage(gray, bbox)

    points = cv2.goodFeaturesToTrack(cropped_frame, **feature_params)

    # translate old_points of bbox to the non-cropped frame
    for i in range(len(points)):
        points[i][0][0] += bbox[0][0]
        points[i][0][1] += bbox[0][1]
        if points[i][0][0] > frame.shape[1]:
            points[i][0][0] = frame.shape[1]

        if points[i][0][1] > frame.shape[0]:
            points[i][0][1] = frame.shape[0]

    return points

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

def convert_x_to_bbox(x,score=None):
  """
  Takes a bounding box in the centre form [x,y,s,r] and returns it in the form
    [x1,y1,x2,y2] where x1,y1 is the top left and x2,y2 is the bottom right
  """
  w = np.sqrt(x[2]*x[3])
  h = x[2]/w
  if(score==None):
    return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.]).reshape((1,4))
  # else:
  #   return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.,score]).reshape((1,5))

z = convert_bbox_to_z((bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]))
old_points = np.array([[int(z[0]), int(z[1])]], dtype=np.float32)

#old_points = GetBboxGoodFeatures(bbox, old_gray)

# Create a random color
color = np.random.randint(0, 255, (100, 3))

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0

frames_num = 1
x_old = 0; y_old = 0
ctr = 0

KF = KalmanFilter2D(0.1, 1, 1, 1, 0.1 ,0.1)
while True:
    frames_num+=1
    _, frame = cap.read()
    frame = IU.RescaleImageToScale(frame, scale_factor=scale_percentage)

    new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # if point_selected is False:
    #     continue

    cv2.circle(frame, (int(z[0]), int(z[1])), 5, (0, 0, 255), 2)

    #Predict KF
    if ctr == 0:
        x = [355.505, 285.805]
        y = [355.505, 285.805]
        ctr+=1
    else:
        (x, y) = KF.predict()

    if(frames_num==2): x = x[0] ; y = y[0]
    else: x = x[0] ; y = y[1]

    bbox_tl[0] = int(bbox_tl[0] + (int(x) - x_old))
    # bbox_tl[1] = int(bbox_tl[1] + (int(y) - y_old))
    bbox_br[0] = int(bbox_br[0] + (int(x) - x_old))
    # bbox_br[1] = int(bbox_br[1] + (int(y) - y_old))
    #cv2.rectangle(frame, (bbox_tl[0], bbox_tl[1]), (bbox_br[0], bbox_br[1]), (255, 0, 0), 2)
    frame = IU.DrawBoundingBox(frame, [[bbox_tl, bbox_br]])

    cv2.imshow("Frame bbox", frame)
    cv2.waitKey(100)

    # cv2.rectangle(frame, (int(x) - 15, int(y) - 15), (int(x) + 15, int(y) + 15), (0, 0, 255), 2)
    #
    # cv2.imshow("Frame", frame)
    # cv2.waitKey(0)
    #Lucas Kenade
    new_points, status, error = cv2.calcOpticalFlowPyrLK(old_gray, new_gray, old_points, None, **lk_params)

    #bbox = [[170, 207], [644, 395]]

    # draw the tracks
    for i in range(len(new_points)):
        a, b = new_points.ravel()
        c, d = old_points.ravel()
        a = int(a);
        b = int(b);
        c = int(c);
        d = int(d)
        # draws new point
        frame = cv2.circle(frame, (a, b), 2, (0, 255, 0), 2)

        #print("a: ", a, "| b: ", b)
        point = KF.update((a, b))
        x1 = point[0][0]; y1 = point[1][1]
        #print("updated points: ", x1, "| ", y1)
        # Draw a rectangle as the estimated object position
        cv2.rectangle(frame, (int(x1) - 15, int(y1) - 15), (int(x1) + 15, int(y1) + 15), (0, 0, 255), 2)
        cv2.putText(frame, "Estimated Position", (int(x1) + 15, int(y1) + 10), 0, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, "Predicted Position", (int(x) + 15, int(y)), 0, 0.5, (255, 0, 0), 2)
        cv2.putText(frame, "Measured Position", (int(a) + 15, int(b) - 15), 0, 0.5, (0, 191, 255), 2)

    cv2.imshow("Frame1 mask added", frame)
    #cv2.waitKey(0)

    # update previous frame and old points
    old_gray = new_gray.copy()
    old_points = new_points.reshape(-1, 1, 2)
    x_old = int(x)
    y_old = int(y)

    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) == 27:
        cap.release()
        cv2.destroyAllWindows()
        break