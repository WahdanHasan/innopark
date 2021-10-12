from classes.system_utilities.image_utilities.ImageUtilities import readClasses
from easydict import EasyDict as edict
import numpy as np


__C                           = edict()

cfg                           = __C

# YOLO configurations
__C.YOLO                      = edict()

__C.YOLO.CLASSES              = "./config/license_plate_detector/custom.names"
__C.YOLO.WEIGHTS              = "./config/license_plate_detector/custom.weights"
__C.YOLO.SAVEDMODEL           = "./config/license_plate_detector/custom-416"
__C.YOLO.ANCHORS              = [12,16, 19,36, 40,28, 36,75, 76,55, 72,146, 142,110, 192,243, 459,401]
__C.YOLO.STRIDES              = [8, 16, 32]
__C.YOLO.XYSCALE              = [1.2, 1.1, 1.05]
__C.YOLO.ANCHOR_PER_SCALE     = 3
__C.YOLO.IOU_LOSS_THRESH      = 0.5
__C.YOLO.IOU_LOSS_THRESH      = 0.7

# model variables
__C.VAR                      = edict()

__C.VAR.INPUT_SIZE = 416
__C.VAR.IOU = 0.45
__C.VAR.SCORE = 0.85


def loadWeights(model, weights_file):
    layer_size = 110
    output_pos = [93, 101, 109]

    wf = open(weights_file, 'rb')
    major, minor, revision, seen, _ = np.fromfile(wf, dtype=np.int32, count=5)

    j = 0
    for i in range(layer_size):
        conv_layer_name = 'conv2d_%d' %i if i > 0 else 'conv2d'
        bn_layer_name = 'batch_normalization_%d' %j if j > 0 else 'batch_normalization'

        conv_layer = model.get_layer(conv_layer_name)
        filters = conv_layer.filters
        k_size = conv_layer.kernel_size[0]
        in_dim = conv_layer.input_shape[-1]

        if i not in output_pos:
            # darknet weights: [beta, gamma, mean, variance]
            bn_weights = np.fromfile(wf, dtype=np.float32, count=4 * filters)
            # tf weights: [gamma, beta, mean, variance]
            bn_weights = bn_weights.reshape((4, filters))[[1, 0, 2, 3]]
            bn_layer = model.get_layer(bn_layer_name)
            j += 1
        else:
            conv_bias = np.fromfile(wf, dtype=np.float32, count=filters)

        # darknet shape (out_dim, in_dim, height, width)
        conv_shape = (filters, in_dim, k_size, k_size)
        conv_weights = np.fromfile(wf, dtype=np.float32, count=np.product(conv_shape))
        # tf shape (height, width, in_dim, out_dim)
        conv_weights = conv_weights.reshape(conv_shape).transpose([2, 3, 1, 0])

        if i not in output_pos:
            conv_layer.set_weights([conv_weights])
            bn_layer.set_weights(bn_weights)
        else:
            conv_layer.set_weights([conv_weights, conv_bias])

    wf.close()

def loadConfig():
    STRIDES = np.array(cfg.YOLO.STRIDES)

    ANCHORS = getAnchors(cfg.YOLO.ANCHORS)

    XYSCALE = cfg.YOLO.XYSCALE

    NUM_CLASS = len(readClasses(cfg.YOLO.CLASSES))

    return STRIDES, ANCHORS, NUM_CLASS, XYSCALE

def getAnchors(anchors_path):
    anchors = np.array(anchors_path)

    return anchors.reshape(3, 3, 2)
