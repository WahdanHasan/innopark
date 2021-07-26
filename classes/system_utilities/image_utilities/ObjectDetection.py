import cv2
import pytesseract
import re as regex
import numpy as np
import tensorflow as tf
from object_detection.utils import config_util
from object_detection.utils import label_map_util
from object_detection.builders import model_builder
import classes.system_utilities.image_utilities.ImageUtilities as IU
from object_detection.utils import visualization_utils as viz_utils

# Global variable declarations
license_detection_model = 0
license_category_index = 0
yolo_net = 0
yolo_class_names = 0
yolo_output_layer_names = 0
yolo_net_input_size = 0


def OnLoad():
    # All models and internal/external dependencies should be both loaded and initialized here

    # Set tensorflow model memory allocation in megabytes
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            tf.config.experimental.set_virtual_device_configuration(
                gpus[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=512)])
        except RunTimeError as e:
            print(e)

    # Initialize pytesseract cmd
    pytesseract.pytesseract.tesseract_cmd = "modules\\TesseractOCR\\tesseract.exe"

    # Initialize license plate detector model and class categories
    global license_detection_model
    global license_category_index

    configs = config_util.get_configs_from_pipeline_file("data\\license plate detector\\pipeline.config")

    license_detection_model = model_builder.build(model_config=configs['model'],
                                                  is_training=False)

    temp_model = tf.compat.v2.train.Checkpoint(model=license_detection_model)
    temp_model.restore("data\\license plate detector\\license_plate_model").expect_partial()

    license_category_index = label_map_util.create_category_index_from_labelmap("data\\license plate detector\\label_map.pbtxt")

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
    yolo_net_input_size = 320

    yolo_net = cv2.dnn.readNetFromDarknet(model_config, model_weights)
    # Set the target device for computation
    yolo_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    yolo_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    yolo_layer_names = yolo_net.getLayerNames()
    yolo_output_layer_names = [yolo_layer_names[i[0] - 1] for i in yolo_net.getUnconnectedOutLayers()]



# This function executes when the class loads
OnLoad()



def DetectLicenseInImage(image):
    # Attempts to detect license plates in the image.
    # Returns a True if at least 1 license was detected, otherwise False.
    # It should be noted that the bounding boxes are in the [TL, BR] format. With [x, y] points.

    # Declare variables
    detection_threshold = 0.6
    height, width, _ = image.shape

    # Convert image to tensor flow format
    image_np = np.array(image)

    input_tensor = tf.convert_to_tensor(value=np.expand_dims(image_np, 0),
                                        dtype=tf.float32)

    # Identify license plates in image
    image, shapes = license_detection_model.preprocess(input_tensor)

    prediction_dict = license_detection_model.predict(image, shapes)

    detections = license_detection_model.postprocess(prediction_dict, shapes)

    # Retrieves the number of license plates detected in the image
    num_detections = int(detections.pop('num_detections'))

    # Creates a hashmap for their probability and classes
    detections = {key: value[0, :num_detections].numpy()
                  for key, value in detections.items()}
    detections['num_detections'] = num_detections

    detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

    # Filters all the scores above the detection threshold
    is_one_license_above_threshold = False
    scores = []
    for i in range(len(detections['detection_scores'])):
        if detections['detection_scores'][i] > detection_threshold:
            scores.append(detections['detection_scores'][i] * 100)
            is_one_license_above_threshold = True

    # Filter bounding boxes based on the filtered scores
    bounding_boxes = detections['detection_boxes'][:len(scores)]

    # Filter classes based on the filtered scores
    bounding_box_classes = detections['detection_classes'][:len(scores)]

    # Convert numpy array to list
    bounding_box_classes = bounding_box_classes.tolist()
    bounding_boxes = bounding_boxes.tolist()

    # Convert class indexes to class names
    label_id_offset = 1
    for i in range(len(bounding_box_classes)):
        bounding_box_classes[i] = license_category_index[bounding_box_classes[i] + label_id_offset]['name']

    # Display licenses above threshold
    image_np_with_detections = image_np.copy()

    # Convert the bounding box to [TL, BR] format
    temp_bounding_boxes = []
    for idx, box in enumerate(bounding_boxes):
        top_x = int(box[1] * width)
        top_y = int(box[0] * height)
        bottom_x = int(box[3] * width)
        bottom_y = int(box[2] * height)

        temp_bounding_boxes.append([[top_x, top_y], [bottom_x, bottom_y]])

    bounding_boxes = temp_bounding_boxes

    return is_one_license_above_threshold, bounding_box_classes, bounding_boxes, scores

def GetLicenseFromImage(license_plate):
    # Takes a cropped license plate to extract [A-Z] and [0-9] ascii characters from the image.
    # The extracted characters are then returned as a string

    # Define regex pattern
    valid_ascii_pattern = "([A-Z]|[0-9])"

    # Extract text from image
    boxes = pytesseract.image_to_boxes(license_plate)
    # Split text into entries of Character : Bounding_box format
    boxes = boxes.splitlines()

    # Extract characters that match the regex pattern
    boxes_temp = []
    for box in boxes:
        box = box.split(' ')
        if regex.match(valid_ascii_pattern, box[0]):
            boxes_temp.append(box)

    boxes = boxes_temp

    license_plate = ""

    # Create a list of the characters
    for box in boxes:
        license_plate = license_plate + box[0]


    return license_plate

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
    confidence_threshold = 0.5
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













# EXPERIMENTAL CODE

class SubtractionModel:
    # As this form of object detection builds on the output of a stationary camera, it is essentially tied to that
    # camera. Due to this, we must treat it as a class of its own so that we may create multiple copies of it to be
    # used on a per stationary camera basis.

    def __init__(self):
        # Initialize subtraction object detection model

        self.subtraction_model = cv2.createBackgroundSubtractorMOG2(history=1000)
        self.subtraction_model_output_mask = 0

    def FeedSubtractionModel(self, image):
        # This function is to be called once per iteration if DetectMovingObjects is being used.

        self.subtraction_model_output_mask = self.subtraction_model.apply(image)

        # Filter out shadows
        _, self.subtraction_model_output_mask = cv2.threshold(self.subtraction_model_output_mask, 254, 255, cv2.THRESH_BINARY)

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


        return bounding_boxes