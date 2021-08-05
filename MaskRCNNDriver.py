import cv2

net = cv2.dnn.readNetFromTensorflow("modules\\MaskRCNN\\frozen_inference_graph_coco.pb", "modules\\MaskRCNN\\mask_rcnn_inception_v2_coco_2018_01_28.pbtxt")

parked_car = cv2.imread("data\\reference footage\\images\\Parked_Car.png")

height, width, _ = parked_car.shape

#blob = cv2.dnn.blobFromImage(parked_car, 1/255, (224, 142), [0, 0, 0], 1, crop=False)
blob = cv2.dnn.blobFromImage(parked_car, 2.0, swapRB=True)
# blob = cv2.dnn.blobFromImage(parked_car, swapRB=True)
net.setInput(blob)
boxes, masks = net.forward(["detection_out_final", "detection_masks"])

box = boxes[0, 0, 0]
x = int(box[3] * width)
y = int(box[4] * height)
x2 = int(box[5] * width)
y2 = int(box[6] * height)

rcnn_output = parked_car.copy()

print(box)

cv2.rectangle(rcnn_output, (x, y), (x2, y2), (255, 0, 0), 3)

cv2.imshow("image", parked_car)
cv2.imshow("MaskRCNN", rcnn_output)

cv2.waitKey(0)