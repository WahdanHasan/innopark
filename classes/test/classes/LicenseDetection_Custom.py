from classes.test.classes.LicenseDetectionConfig import cfg, BuildModel

import os
# comment out below line to enable tensorflow outputs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import cv2
import numpy as np
import tesserocr
from PIL import Image
import re as regex
from tensorflow import keras

# Global variable declarations
license_detection_model = 0

def OnLoad():

    saved_model_file = str(cfg.YOLO.SAVEDMODEL)+"/saved_model.pb"
    if os.path.isfile(saved_model_file)==False:
        print("building model")
        BuildModel()

    # Set tensorflow model memory allocation in megabytes
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            tf.config.experimental.set_virtual_device_configuration(
                gpus[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=512)])
        except RuntimeError as e:
            print(e)

    # global config
    # global sess
    # config = tf.compat.v1.ConfigProto()
    # sess = tf.compat.v1.InteractiveSession(config=config)

    # config.gpu_options.allow_growth = True
    # global sess

    # LoadConfig()

    # config_util.save_pipeline_config(config, directory=".")
    # Initialize/load license_plate_detector model

    global license_detection_model
    global infer

    # license_detection_model = tf.saved_model.load(cfg.YOLO.SAVEDMODEL)
    # infer = license_detection_model.signatures[tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY]
    license_detection_model = keras.models.load_model("config\\license_plate_detector\\custom-416")
    #
    #


    # Define variables
    global input_size
    input_size = cfg.VAR.INPUT_SIZE


    # Run blank detection to initialize model
    # print(DetectLicenseInImage(image=[np.zeros(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]), dtype=np.uint8)]))
    # print(DetectLicenseInImage(image=[np.zeros(shape=(Constants.default_camera_shape[1], Constants.default_camera_shape[0], Constants.default_camera_shape[2]), dtype=np.uint8)]))

@tf.function
def inferImage(batch_data):
    x = infer(batch_data)
    return x

def DetectLicenseInImage(image):
    # Attempts to detect license plates in a list of images.
    # returns bounding box as [[[TL], [BR]]] or [[[x1, y1], [x2, y2]]]


    # Run the custom yolo4 model on each image
    #if np.all(image[0]==0):
    if not np.count_nonzero(image):
        return

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image_data = cv2.resize(image, (input_size, input_size))

    image_data = image_data / 255.

    images_data = [image_data]

    images_data = np.asarray(images_data).astype(np.float32)

    batch_data = tf.constant(images_data)

    pred_bbox = inferImage(batch_data)


    print("pred_bbox: ", pred_bbox)
    #
    # for key, value in pred_bbox.items():
    #     boxes = value[:, :, 0:4]
    #     pred_conf = value[:, :, 4:]
    #
    # # Get the best bounding boxes out of the detections using IOU and SCORE
    # boxes, scores, classes, validity_status = tf.image.combined_non_max_suppression(
    #     boxes=tf.reshape(boxes, (tf.shape(boxes)[0], -1, 1, 4)),
    #     scores=tf.reshape(pred_conf, (tf.shape(pred_conf)[0], -1, tf.shape(pred_conf)[-1])),
    #     max_output_size_per_class=1,
    #     max_total_size=1,
    #     iou_threshold=cfg.VAR.IOU,
    #     score_threshold=cfg.VAR.SCORE
    # )
    #
    # # Format bounding boxes from ymin, xmin, ymax, xmax to xmin, ymin, xmax, ymax
    # height, width, _ = image.shape
    # bbox = IU.convertBbFormat(boxes.numpy()[0], height, width)
    #
    # # Convert bounding boxes to type int
    # bb = bbox.astype(np.int32)[0]
    #
    # # Convert bounding boxes to format [TL, BR]
    # bounding_boxes_converted = [[[bb[0], bb[1]], [bb[2], bb[3]]]]


    # return validity_status.numpy()[0], classes, bounding_boxes_converted, scores.numpy()[0]

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
