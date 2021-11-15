import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import tesserocr
from PIL import Image
import re as regex
import numpy as np
from object_detection.utils import config_util
from object_detection.utils import label_map_util
from object_detection.builders import model_builder
from tensorflow import keras


# Global variable declarations
license_detection_model = 0
license_category_index = 0
def OnLoad():
    # All models and internal/external dependencies should be both loaded and initialized here

    # Set tensorflow model memory allocation in megabytes
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            tf.config.experimental.set_virtual_device_configuration(
                gpus[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=512)])
        except RuntimeError as e:
            print(e)

    # Initialize license_plate_detector model and class categories
    global license_detection_model
    global license_category_index

    configs = config_util.get_configs_from_pipeline_file("config\\license_plate_detector\\pipeline.config")
    config_util.save_pipeline_config(configs['model'], directory=".")
    license_detection_model = model_builder.build(model_config=configs['model'],
                                                  is_training=False)

    # license_detection_model = keras.models.load_model("config\\license_plate_detector\\custom-416")

    # temp_model = tf.compat.v2.train.Checkpoint(model=license_detection_model)
    # temp_model.restore("config\\license_plate_detector\\license_plate_model").expect_partial()

    license_category_index = label_map_util.create_category_index_from_labelmap("config\\license_plate_detector\\label_map.pbtxt")

    from classes.system_utilities.helper_utilities import Constants

    # Run blank detection to initialize model
    DetectLicenseInImage(image=np.zeros(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]), dtype=np.uint8))

def DetectLicenseInImage(image):
    # return False, [['yes']], [[[0, 0], [0, 0]]], 'yes'
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
    text = tesserocr.image_to_text(Image.fromarray(license_plate))

    # Extract characters that match the regex pattern
    license_plate = []
    for character in text:
        if regex.match(valid_ascii_pattern, character[0]):
            license_plate.append(character)

    license_plate = ''.join(license_plate)

    return license_plate
