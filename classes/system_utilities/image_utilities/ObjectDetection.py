import cv2
import numpy as np
import classes.system_utilities.image_utilities.ImageUtilities as IU

# Global variable declarations
yolo_net = 0
yolo_class_names = 0
yolo_output_layer_names = 0
yolo_net_input_size = 0

def OnLoad(weight_idx=0):
    # All models and internal/external dependencies should be both loaded and initialized here


    # Initialize YOLOv3 model
    global yolo_net
    global yolo_class_names
    global yolo_output_layer_names
    global yolo_net_input_size

    classes_file = 'config\\yolov3\\coco.names'

    with open(classes_file, 'rt') as f:
        yolo_class_names = f.read().rstrip('\n').split('\n')


    if weight_idx == 0:
        model_config = 'config\\yolov4\\yolov4-tiny.cfg'
        model_weights = 'config\\yolov4\\yolov4-tiny.weights'
        yolo_net_input_size = 320
    elif weight_idx == 1:
        model_config = 'config\\yolov3\\yolov3-320.cfg'
        model_weights = 'config\\yolov3\\yolov3-320.weights'
        yolo_net_input_size = 320



    yolo_net = cv2.dnn.readNetFromDarknet(model_config, model_weights)
    # Set the target device for computation
    yolo_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    yolo_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    yolo_layer_names = yolo_net.getLayerNames()
    yolo_output_layer_names = [yolo_layer_names[i[0] - 1] for i in yolo_net.getUnconnectedOutLayers()]


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