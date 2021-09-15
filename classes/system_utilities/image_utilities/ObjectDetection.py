import cv2
import numpy as np
from shapely.geometry import Polygon
import classes.system_utilities.image_utilities.ImageUtilities as IU
import classes.system_utilities.tracking_utilities.tracker as T

# Global variable declarations
yolo_net = 0
yolo_class_names = 0
yolo_output_layer_names = 0
yolo_net_input_size = 0
tracker = T.EuclideanDistTracker()

def OnLoad():
    # All models and internal/external dependencies should be both loaded and initialized here


    # Initialize YOLOv3 model
    global yolo_net
    global yolo_class_names
    global yolo_output_layer_names
    global yolo_net_input_size

    classes_file = 'modules\\YOLOv3\\coco.names'

    with open(classes_file, 'rt') as f:
        yolo_class_names = f.read().rstrip('\n').split('\n')


    model_config = 'modules\\YOLOv3\\yolov3-320.cfg'
    model_weights = 'modules\\YOLOv3\\yolov3-320.weights'
    yolo_net_input_size = 256

    yolo_net = cv2.dnn.readNetFromDarknet(model_config, model_weights)
    # Set the target device for computation
    yolo_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    yolo_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    yolo_layer_names = yolo_net.getLayerNames()
    yolo_output_layer_names = [yolo_layer_names[i[0] - 1] for i in yolo_net.getUnconnectedOutLayers()]



# This function executes when the class loads
OnLoad()





def DetectObjectsInImage(image):
    # The function takes an input image and outputs all of the objects it detects in the image.
    # The bounding box is output in the format of [TL, BR] with points [x, y]

    height, width, _ = image.shape

    # Convert image to blob for the yolo network
    blob = IU.ImageToBlob(image=image,
                          input_size=yolo_net_input_size)

    yolo_net.setInput(blob)

    yolo_outputs = yolo_net.forward(yolo_output_layer_names)

    # Declare variables
    bounding_boxes = []
    class_ids = []
    confidence_scores = []
    # Higher confidence threshold means that the detections with confidence above threshold will be shown
    # Lower nms means that the threshold for overlapping bounding boxes is lowering meaning they filter out more
    confidence_threshold = 0.8
    nms_threshold = 0.3

    # Obtain bounding boxes of the detections that are over the threshold value
    is_one_detection_above_threshold = False
    for output in yolo_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > confidence_threshold:
                is_one_detection_above_threshold = True

                w, h = int(detection[2] * width), int(detection[3] * height)
                x, y = int((detection[0] * width) - w/2), int((detection[1] * height) - h/2)

                bounding_boxes.append([x, y, w, h])
                class_ids.append(class_id)
                confidence_scores.append(float(confidence))

    # Determines indices to keep by filtering overlapping bounding boxes with the same object against the threshold
    indices_to_keep = cv2.dnn.NMSBoxes(bounding_boxes, confidence_scores, confidence_threshold, nms_threshold)

    # Filter detections based on indices to keep
    temp_bounding_boxes = []
    class_names = []
    temp_confidence_scores = []
    for index in indices_to_keep:
        index = index[0]

        # Filter detections by classes
        if yolo_class_names[class_ids[index]] != 'car' and yolo_class_names[class_ids[index]] != 'truck':
            continue

        box = bounding_boxes[index]

        x, y, w, h = box[0], box[1], box[2], box[3]

        temp_bounding_boxes.append([x, y, w, h])

        # Get class ids corresponding class name
        temp_class_name = yolo_class_names[class_ids[index]].upper()
        class_names.append(temp_class_name)

        # Convert confidence score to percentage out of 100
        temp_confidence_scores.append(confidence_scores[index] * 100)

    bounding_boxes = temp_bounding_boxes
    confidence_scores = temp_confidence_scores

    # Convert bounding boxes to [TL, BR] format
    for i in range(len(bounding_boxes)):
        bounding_boxes[i][2] = bounding_boxes[i][0] + bounding_boxes[i][2]
        bounding_boxes[i][3] = bounding_boxes[i][1] + bounding_boxes[i][3]

        bounding_boxes[i] = [[bounding_boxes[i][0], bounding_boxes[i][1]], [bounding_boxes[i][2], bounding_boxes[i][3]]]


    return is_one_detection_above_threshold, class_names, bounding_boxes, confidence_scores

def CreateInvertedMask(img, bbox):
    # Takes a full image and the bounding box of the object of interest within it.
    # Returns the inverted mask of the object contained within the bounding box

    # Increase bounding box
    increased_bbox = IU.GetIncreasedBB(img_dimensions=img.shape[:2],
                                       bbox=bbox)

    # Get a cropped image based on the increased bounding box
    increased_bbox_img = IU.CropImage(img=img,
                                      bounding_set=increased_bbox)

    # Get the bounding box points in respect to increased bounding box (irt = in respect to)
    bbox_irt_increased_bbox = IU.GetBBInRespectTo(bbox=bbox,
                                                  bbox_of_new_parent=increased_bbox)

    # Create a black mask based on the cropped image dimensions
    mask = np.zeros(increased_bbox_img.shape[:2], dtype=np.uint8)

    # Create bg and fg standard model arrays. These are for grabcut's internal use.
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)


    # Apply grabcut to image
    # Convert bb to opencv format
    increased_bbox_converted = [bbox_irt_increased_bbox[0][0],
                                bbox_irt_increased_bbox[0][1],
                                bbox_irt_increased_bbox[1][0],
                                bbox_irt_increased_bbox[1][1]]

    # mask outputs 0 (definite bg), 1 (definite fg), 2 (probable bg), 3 (probable fg)
    (mask, _, _) = cv2.grabCut(img=increased_bbox_img,
                               mask=mask,
                               rect=increased_bbox_converted,
                               bgdModel=bg_model,
                               fgdModel=fg_model,
                               iterCount=1,
                               mode=cv2.GC_INIT_WITH_RECT)

    # Define output mask based on mask output values from grabcut
    output_mask = (np.where((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD), 1, 0)*255).astype("uint8")
    cv2.imshow("EEE", increased_bbox_img)
    return output_mask

def IsCarInParkingBB(parking_bounding_box, car_bounding_box):
    #takes two full bounding boxes
    #uses the TL, BR points to get intersection, area and IoU

    acceptable_threshold = 0.6

    #get x,y coordinates of TL, BR
    xA = max(parking_bounding_box[0][0], car_bounding_box[0][0])                                                #A = [[283, 330], [346,329], [309, 365], [381,360]]                                                                                                            #B = [[282, 331], [347, 330], [307, 366], [379, 364]]
    yA = max(parking_bounding_box[0][1], car_bounding_box[0][1])

    xB = min(parking_bounding_box[3][0], car_bounding_box[3][0])
    yB = min(parking_bounding_box[3][1], car_bounding_box[3][1])

    #check whether intersection exists first
    if (xA > xB or yA > yB):
        print ("No intersection")
        return -1

    #get area of intersecting width and height
    intersecting_area = max(0, xB - xA) * max(0, yB - yA)

    #get the area of both bounding boxes separately
    parking_bounding_box_area = (parking_bounding_box[3][0] - parking_bounding_box[0][0]) * (parking_bounding_box[3][1] - parking_bounding_box[0][1])
    car_bounding_box_area = (car_bounding_box[3][0] - car_bounding_box[0][0]) * (car_bounding_box[3][1] - car_bounding_box[0][1])

    #calculate IoU
    #union = area - intersecting area
    iou = intersecting_area / float(parking_bounding_box_area + car_bounding_box_area - intersecting_area)

    # return the intersection over union value
    print(iou)

    if (iou > acceptable_threshold):
        return True
    else:
        return False

def IsCarInParkingBBN(parking_bounding_box, car_bounding_box):
    # Takes 2 bounding boxes, one for the car, one for the parking spot
    # It should be noted that the parking bounding box must be in the format [TL, TR, BL, BR] while the car box should
    # be in the format of [TL, BR]
    # Returns true if overlapping, false otherwise

    acceptable_threshold = 0.08

    # Define each polygon
    temp_parking_bb = [parking_bounding_box[0], parking_bounding_box[1], parking_bounding_box[3], parking_bounding_box[2]]
    temp_car_bb = IU.GetFullBoundingBox(car_bounding_box)
    temp_car_bb = [temp_car_bb[0], temp_car_bb[1], temp_car_bb[3], temp_car_bb[2]]
    polygon1_shape = Polygon(temp_parking_bb)
    polygon2_shape = Polygon(temp_car_bb)

    # Calculate intersection and union, and the IOU
    polygon_intersection = polygon1_shape.intersection(polygon2_shape).area
    polygon_union = polygon1_shape.area + polygon2_shape.area - polygon_intersection

    iou = polygon_intersection / polygon_union

    # print(iou)
    if (iou > acceptable_threshold):
        return True
    else:
        return False










# EXPERIMENTAL CODE

class SubtractionModel:
    # As this form of object detection builds on the output of a stationary camera, it is essentially tied to that
    # camera. Due to this, we must treat it as a class of its own so that we may create multiple copies of it to be
    # used on a per stationary camera basis.

    def __init__(self, detectShadows=False):
        # Initialize subtraction object detection model

        self.subtraction_model = cv2.createBackgroundSubtractorMOG2(history=100)
        self.subtraction_model.setDetectShadows(detectShadows)
        self.subtraction_model_output_mask = 0

    def FeedSubtractionModel(self, image, learningRate=-1):
        # This function is to be called once per iteration if DetectMovingObjects is being used.

        self.subtraction_model_output_mask = self.subtraction_model.apply(image, learningRate=learningRate)

        # Filter out shadows
        # _, self.subtraction_model_output_mask = cv2.threshold(self.subtraction_model_output_mask, 254, 255, cv2.THRESH_BINARY)

    def DetectMovingObjects(self, area_threshold=100):
        # Detect objects that have moved within the image.
        # Returns the bounding boxes of all the objects detected.
        # It is to be noted that if this function is to be used, FeedSubtractionModel must be called at least once beforehand

        contours, _ = cv2.findContours(self.subtraction_model_output_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxes = []
        for contour in contours:
            area = cv2.contourArea(contour)

            if area > area_threshold:
                x, y, w, h = cv2.boundingRect(contour)

                bounding_boxes.append([x, y, w, h])


        # Convert bounding boxes to [TL, BR] format
        for i in range(len(bounding_boxes)):
            bounding_boxes[i][2] = bounding_boxes[i][0] + bounding_boxes[i][2]
            bounding_boxes[i][3] = bounding_boxes[i][1] + bounding_boxes[i][3]

            bounding_boxes[i] = [[bounding_boxes[i][0], bounding_boxes[i][1]],
                                 [bounding_boxes[i][2], bounding_boxes[i][3]]]


        self.subtraction_model_output_mask = IU.DrawBoundingBoxes(self.subtraction_model_output_mask, bounding_boxes)
        cv2.imshow("Subtraction Mask", self.subtraction_model_output_mask)

        return bounding_boxes

    def GetOutput(self):
        return self.subtraction_model_output_mask
