import os
# comment out below line to enable tensorflow outputs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import cv2
import numpy as np
import tensorflow as tf
from classes.system_utilities.image_utilities.LicenseDetectionConfig import cfg, loadConfig
import classes.system_utilities.image_utilities.ImageUtilities as IU

# Global variable declarations
license_detection_model = 0

def OnLoad():
    from tensorflow.python.saved_model import tag_constants
    from tensorflow.compat.v1 import ConfigProto
    from tensorflow.compat.v1 import InteractiveSession

    # Declare variables
    global license_detection_model
    loaded_weights_path = './config/license_plate_detector/custom-416'

    # Set tensorflow model memory allocation in megabytes
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            tf.config.experimental.set_virtual_device_configuration(
                gpus[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=512)])
        except RuntimeError as e:
            print(e)

    config = ConfigProto()
    config.gpu_options.allow_growth = True
    InteractiveSession(config=config)

    loadConfig()

    # Initialize/load license_plate_detector model
    license_detection_model = tf.saved_model.load(loaded_weights_path, tags=[tag_constants.SERVING])

    # Run blank detection to initialize model
    from classes.system_utilities.helper_utilities import Constants
    DetectLicenseInImage(image=[np.zeros(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]), dtype=np.uint8)])





def DetectLicenseInImage(image):
    # Attempts to detect license plates in a list of images.
    # It should be noted that the bounding boxes are in the [TL, BR] format. With [x, y] points.

    # Define variables
    input_size = cfg.VAR.INPUT_SIZE
    bounding_box_classes = IU.readClasses(cfg.YOLO.CLASSES)

    # Run the custom yolo4 model on each image
    #if np.all(image[0]==0):
    if not np.count_nonzero(image):
        print("img is filled with zeros")
        return

    from tensorflow.python.saved_model import tag_constants
    license_detection_model = tf.saved_model.load(cfg.YOLO.SAVEDMODEL, tags=[tag_constants.SERVING])
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image_data = cv2.resize(image, (input_size, input_size))
    image_data = image_data / 255.

    images_data = []

    for i in range(1):
        images_data.append(image_data)
    images_data = np.asarray(images_data).astype(np.float32)

    infer = license_detection_model.signatures['serving_default']
    batch_data = tf.constant(images_data)
    pred_bbox = infer(batch_data)
    for key, value in pred_bbox.items():
        boxes = value[:, :, 0:4]
        pred_conf = value[:, :, 4:]

    # Get the best bounding boxes out of the detections using IOU and SCORE
    boxes, scores, classes, validity_status = tf.image.combined_non_max_suppression(
        boxes=tf.reshape(boxes, (tf.shape(boxes)[0], -1, 1, 4)),
        scores=tf.reshape(pred_conf, (tf.shape(pred_conf)[0], -1, tf.shape(pred_conf)[-1])),
        max_output_size_per_class=1,
        max_total_size=1,
        iou_threshold=cfg.VAR.IOU,
        score_threshold=cfg.VAR.SCORE
    )

    # Format bounding boxes from ymin, xmin, ymax, xmax to xmin, ymin, xmax, ymax
    height, width, _ = image.shape
    bbox = IU.convertBbFormat(boxes.numpy()[0], height, width)

    # Convert bounding boxes to type int
    bb = bbox.astype(np.int32)[0]

    # Convert bounding boxes to format [TL, BR]
    bounding_boxes_converted = [[[bb[0], bb[1]], [bb[2], bb[3]]]]

    img = IU.DrawBoundingBoxAndClasses(image, bounding_box_classes, bounding_boxes_converted)
    print("status validity: ", validity_status.numpy()[0])
    cv2.imshow("image", img)
    cv2.waitKey(0)

    return validity_status.numpy()[0], bounding_box_classes, bounding_boxes_converted, scores.numpy()[0]

def BuildModel():
    from classes.system_utilities.image_utilities.LicenseDetectionModel import YOLO, decode, filterBoxes
    from classes.system_utilities.image_utilities.LicenseDetectionConfig import loadWeights

    # All models and internal/external dependencies should be both loaded and initialized here
    input_size = cfg.VAR.INPUT_SIZE
    score_threshold = cfg.YOLO.IOU_LOSS_THRESH
    weights_path = cfg.YOLO.WEIGHTS
    output_path = cfg.YOLO.SAVEDMODEL

    STRIDES, ANCHORS, NUM_CLASS, XYSCALE = loadConfig()

    input_layer = tf.keras.layers.Input([input_size, input_size, 3])
    feature_maps = YOLO(input_layer, NUM_CLASS)
    bbox_tensors = []
    prob_tensors = []

    for i, fm in enumerate(feature_maps):
        if i == 0:
            output_tensors = decode(fm, input_size // 8, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE)
        elif i == 1:
            output_tensors = decode(fm, input_size // 16, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE)
        else:
            output_tensors = decode(fm, input_size // 32, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE)
        bbox_tensors.append(output_tensors[0])
        prob_tensors.append(output_tensors[1])

    pred_bbox = tf.concat(bbox_tensors, axis=1)
    pred_prob = tf.concat(prob_tensors, axis=1)

    boxes, pred_conf = filterBoxes(pred_bbox, pred_prob, score_threshold=score_threshold,
                                   input_shape=tf.constant([input_size, input_size]))
    pred = tf.concat([boxes, pred_conf], axis=-1)

    model = tf.keras.Model(input_layer, pred)
    loadWeights(model, weights_path)
    model.summary()
    model.save(output_path)

def GetLicenseFromImage(license_plate):
    # Takes a cropped license plate to extract [A-Z] and [0-9] ascii characters from the image.
    # The extracted characters are then returned as a string

    # Define regex pattern
    valid_ascii_pattern = "([A-Z]|[0-9])"

    # Extract text from image
    text = tesserocr.image_to_text(Image.fromarray(license_plate))

    # Extract characters that match the regex pattern
    license_plate = []
    for character in text:
        if regex.match(valid_ascii_pattern, character[0]):
            license_plate.append(character)

    license_plate = ''.join(license_plate)

    return license_plate
