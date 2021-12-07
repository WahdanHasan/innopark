import cv2
import time
import numpy as np

net = cv2.dnn.readNetFromTensorflow("./config/maskrcnn/frozen_inference_graph_coco.pb", "./config/maskrcnn/mask_rcnn_inception_v2_coco_2018_01_28.pbtxt")

parked_car = cv2.imread("./data/reference footage/images/car_parked3_new_cropped.jpg")

height, width, _ = parked_car.shape

#blob = cv2.dnn.blobFromImage(parked_car, 1/255, (224, 142), [0, 0, 0], 1, crop=False)
blob = cv2.dnn.blobFromImage(parked_car, 2.0, swapRB=True)
# blob = cv2.dnn.blobFromImage(parked_car, swapRB=True)
start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
# while True:
net.setInput(blob)
boxes, masks = net.forward(["detection_out_final", "detection_masks"])

box = boxes[0, 0, 0]
x = int(box[3] * width)
y = int(box[4] * height)
x2 = int(box[5] * width)
y2 = int(box[6] * height)

rcnn_output = parked_car.copy()

# print(box)

cv2.rectangle(rcnn_output, (x, y), (x2, y2), (255, 0, 0), 3)

roi = parked_car[y: y2, x: x2]
roi_height, roi_width, _ = roi.shape

class_id = box[1]

mask = masks[0, int(class_id)]
mask = cv2.resize(mask, (roi_width, roi_height))
_, mask = cv2.threshold(mask, 0.5, 255, cv2.THRESH_BINARY)

contours, _ = cv2.findContours(np.array(mask, np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

masked_image = roi.copy()

for cnt in contours:
    cv2.fillPoly(masked_image, [cnt], (0, 0, 0))

# cv2.imshow("image", parked_car)
# cv2.imshow("Mask", mask)
# cv2.imshow("maskrcnn Detection", rcnn_output)
cv2.imshow("maskrcnn Segmentation", masked_image)
cv2.waitKey(0)

counter += 1
if (time.time() - start_time) > seconds_before_display:
    print("FPS: ", counter / (time.time() - start_time))
    print("time: ", (time.time() - start_time))
    counter = 0
    start_time = time.time()

    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     cv2.destroyAllWindows()
    #     break
