import tensorflow as tf

# YOLO4
def YOLO(input_layer, NUM_CLASS):
    route_a, route_b, conv = darknet53(input_layer)

    route = conv
    conv = convolution(conv, (1, 1, 512, 256))
    conv = upsample(conv)
    route_b = convolution(route_b, (1, 1, 512, 256))
    conv = tf.concat([route_b, conv], axis=-1)

    conv = convolution(conv, (1, 1, 512, 256))
    conv = convolution(conv, (3, 3, 256, 512))
    conv = convolution(conv, (1, 1, 512, 256))
    conv = convolution(conv, (3, 3, 256, 512))
    conv = convolution(conv, (1, 1, 512, 256))

    route_b = conv
    conv = convolution(conv, (1, 1, 256, 128))
    conv = upsample(conv)
    route_a = convolution(route_a, (1, 1, 256, 128))
    conv = tf.concat([route_a, conv], axis=-1)

    conv = convolution(conv, (1, 1, 256, 128))
    conv = convolution(conv, (3, 3, 128, 256))
    conv = convolution(conv, (1, 1, 256, 128))
    conv = convolution(conv, (3, 3, 128, 256))
    conv = convolution(conv, (1, 1, 256, 128))

    route_a = conv
    conv = convolution(conv, (3, 3, 128, 256))
    conv_sbbox = convolution(conv, (1, 1, 256, 3 * (NUM_CLASS + 5)), activate=False, bn=False)

    conv = convolution(route_a, (3, 3, 128, 256), downsample=True)
    conv = tf.concat([conv, route_b], axis=-1)

    conv = convolution(conv, (1, 1, 512, 256))
    conv = convolution(conv, (3, 3, 256, 512))
    conv = convolution(conv, (1, 1, 512, 256))
    conv = convolution(conv, (3, 3, 256, 512))
    conv = convolution(conv, (1, 1, 512, 256))

    route_b = conv
    conv = convolution(conv, (3, 3, 256, 512))
    conv_mbbox = convolution(conv, (1, 1, 512, 3 * (NUM_CLASS + 5)), activate=False, bn=False)

    conv = convolution(route_b, (3, 3, 256, 512), downsample=True)
    conv = tf.concat([conv, route], axis=-1)

    conv = convolution(conv, (1, 1, 1024, 512))
    conv = convolution(conv, (3, 3, 512, 1024))
    conv = convolution(conv, (1, 1, 1024, 512))
    conv = convolution(conv, (3, 3, 512, 1024))
    conv = convolution(conv, (1, 1, 1024, 512))

    conv = convolution(conv, (3, 3, 512, 1024))
    conv_lbbox = convolution(conv, (1, 1, 1024, 3 * (NUM_CLASS + 5)), activate=False, bn=False)

    return [conv_sbbox, conv_mbbox, conv_lbbox]

def decode(feature_map, size_output, NUM_CLASS, STRIDES, ANCHORS, i=0, XYSCALE=[1, 1, 1]):
    batch_size = tf.shape(feature_map)[0]
    feature_map = tf.reshape(feature_map,
                             (batch_size, size_output, size_output, 3, 5 + NUM_CLASS))

    conv_raw_dxdy, conv_raw_dwdh, conv_raw_conf, conv_raw_prob = tf.split(feature_map, (2, 2, 1, NUM_CLASS),
                                                                          axis=-1)

    xy_grid = tf.meshgrid(tf.range(size_output), tf.range(size_output))
    xy_grid = tf.expand_dims(tf.stack(xy_grid, axis=-1), axis=2)  # [gx, gy, 1, 2]
    xy_grid = tf.tile(tf.expand_dims(xy_grid, axis=0), [batch_size, 1, 1, 3, 1])

    xy_grid = tf.cast(xy_grid, tf.float32)

    pred_xy = ((tf.sigmoid(conv_raw_dxdy) * XYSCALE[i]) - 0.5 * (XYSCALE[i] - 1) + xy_grid) * STRIDES[i]
    pred_wh = (tf.exp(conv_raw_dwdh) * ANCHORS[i])
    pred_xywh = tf.concat([pred_xy, pred_wh], axis=-1)

    pred_conf = tf.sigmoid(conv_raw_conf)
    pred_prob = tf.sigmoid(conv_raw_prob)

    pred_prob = pred_conf * pred_prob
    pred_prob = tf.reshape(pred_prob, (batch_size, -1, NUM_CLASS))
    pred_xywh = tf.reshape(pred_xywh, (batch_size, -1, 4))

    return pred_xywh, pred_prob

def filterBoxes(box, scores, score_threshold=0.4, input_shape=tf.constant([416, 416])):
    scores_max = tf.math.reduce_max(scores, axis=-1)

    mask = scores_max >= score_threshold
    class_boxes = tf.boolean_mask(box, mask)
    pred_conf = tf.boolean_mask(scores, mask)
    class_boxes = tf.reshape(class_boxes, [tf.shape(scores)[0], -1, tf.shape(class_boxes)[-1]])
    pred_conf = tf.reshape(pred_conf, [tf.shape(scores)[0], -1, tf.shape(pred_conf)[-1]])

    box_xy, box_wh = tf.split(class_boxes, (2, 2), axis=-1)

    input_shape = tf.cast(input_shape, dtype=tf.float32)

    box_yx = box_xy[..., ::-1]
    box_hw = box_wh[..., ::-1]

    box_mins = (box_yx - (box_hw / 2.)) / input_shape
    box_maxes = (box_yx + (box_hw / 2.)) / input_shape
    boxes = tf.concat([
        box_mins[..., 0:1],  # y_min
        box_mins[..., 1:2],  # x_min
        box_maxes[..., 0:1],  # y_max
        box_maxes[..., 1:2]  # x_max
    ], axis=-1)

    return (boxes, pred_conf)

def darknet53(data):
    data = convolution(data, (3, 3, 3, 32), activate_type="mish")
    data = convolution(data, (3, 3, 32, 64), downsample=True, activate_type="mish")

    route = data
    route = convolution(route, (1, 1, 64, 64), activate_type="mish")
    data = convolution(data, (1, 1, 64, 64), activate_type="mish")
    for i in range(1):
        data = residualBlock(data, 64, 32, 64, activate_type="mish")
    data = convolution(data, (1, 1, 64, 64), activate_type="mish")

    data = tf.concat([data, route], axis=-1)
    data = convolution(data, (1, 1, 128, 64), activate_type="mish")
    data = convolution(data, (3, 3, 64, 128), downsample=True, activate_type="mish")
    route = data
    route = convolution(route, (1, 1, 128, 64), activate_type="mish")
    data = convolution(data, (1, 1, 128, 64), activate_type="mish")
    for i in range(2):
        data = residualBlock(data, 64, 64, 64, activate_type="mish")
    data = convolution(data, (1, 1, 64, 64), activate_type="mish")
    data = tf.concat([data, route], axis=-1)

    data = convolution(data, (1, 1, 128, 128), activate_type="mish")
    data = convolution(data, (3, 3, 128, 256), downsample=True, activate_type="mish")
    route = data
    route = convolution(route, (1, 1, 256, 128), activate_type="mish")
    data = convolution(data, (1, 1, 256, 128), activate_type="mish")
    for i in range(8):
        data = residualBlock(data, 128, 128, 128, activate_type="mish")
    data = convolution(data, (1, 1, 128, 128), activate_type="mish")
    data = tf.concat([data, route], axis=-1)

    data = convolution(data, (1, 1, 256, 256), activate_type="mish")
    route_1 = data
    data = convolution(data, (3, 3, 256, 512), downsample=True, activate_type="mish")
    route = data
    route = convolution(route, (1, 1, 512, 256), activate_type="mish")
    data = convolution(data, (1, 1, 512, 256), activate_type="mish")
    for i in range(8):
        data = residualBlock(data, 256, 256, 256, activate_type="mish")
    data = convolution(data, (1, 1, 256, 256), activate_type="mish")
    data = tf.concat([data, route], axis=-1)

    data = convolution(data, (1, 1, 512, 512), activate_type="mish")
    route_2 = data
    data = convolution(data, (3, 3, 512, 1024), downsample=True, activate_type="mish")
    route = data
    route = convolution(route, (1, 1, 1024, 512), activate_type="mish")
    data = convolution(data, (1, 1, 1024, 512), activate_type="mish")
    for i in range(4):
        data = residualBlock(data, 512, 512, 512, activate_type="mish")
    data = convolution(data, (1, 1, 512, 512), activate_type="mish")
    data = tf.concat([data, route], axis=-1)

    data = convolution(data, (1, 1, 1024, 1024), activate_type="mish")
    data = convolution(data, (1, 1, 1024, 512))
    data = convolution(data, (3, 3, 512, 1024))
    data = convolution(data, (1, 1, 1024, 512))

    data = tf.concat([tf.nn.max_pool(data, ksize=13, padding='SAME', strides=1), tf.nn.max_pool(data, ksize=9, padding='SAME', strides=1)
                            , tf.nn.max_pool(data, ksize=5, padding='SAME', strides=1), data], axis=-1)
    data = convolution(data, (1, 1, 2048, 512))
    data = convolution(data, (3, 3, 512, 1024))
    data = convolution(data, (1, 1, 1024, 512))

    return route_1, route_2, data

class batchNormalization(tf.keras.layers.BatchNormalization):
    def call(self, x, training=False):
        if not training:
            training = tf.constant(False)
        training = tf.logical_and(training, self.trainable)
        return super().call(x, training)

def convolution(input_layer, filters_shape, downsample=False, activate=True, bn=True, activate_type='leaky'):
    if downsample:
        input_layer = tf.keras.layers.ZeroPadding2D(((1, 0), (1, 0)))(input_layer)
        padding = 'valid'
        strides = 2
    else:
        strides = 1
        padding = 'same'

    conv = tf.keras.layers.Conv2D(filters=filters_shape[-1], kernel_size = filters_shape[0], strides=strides, padding=padding,
                                  use_bias=not bn, kernel_regularizer=tf.keras.regularizers.l2(0.0005),
                                  kernel_initializer=tf.random_normal_initializer(stddev=0.01),
                                  bias_initializer=tf.constant_initializer(0.))(input_layer)

    if bn:
        conv = batchNormalization()(conv)

    if activate == True:
        if activate_type == "leaky":
            conv = tf.nn.leaky_relu(conv, alpha=0.1)
        elif activate_type == "mish":
            conv = mish(conv)
    return conv

def mish(x):
    return x * tf.math.tanh(tf.math.softplus(x))

def residualBlock(input_layer, input_channel, filter_num1, filter_num2, activate_type='leaky'):
    short_cut = input_layer
    conv = convolution(input_layer, filters_shape=(1, 1, input_channel, filter_num1), activate_type=activate_type)
    conv = convolution(conv, filters_shape=(3, 3, filter_num1, filter_num2), activate_type=activate_type)

    residual_output = short_cut + conv
    return residual_output

def upsample(input_layer):
    # process of expansion and filtration
    # insert zero-valued samples between the samples to increase the sampling rate
    return tf.image.resize(input_layer, (input_layer.shape[1] * 2, input_layer.shape[2] * 2), method='bilinear')

