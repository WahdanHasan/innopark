import cv2
# import pixellib
# from pixellib.instance import instance_segmentation

# from classes.camera.CameraBuffered import Camera
# from classes.system_utilities.image_utilities import ObjectDetection as OD
from classes.system_utilities.image_utilities import ImageUtilities as IU
import time
#
def main():
    # car_img = cv2.imread("./data/reference footage/images/car_parked3_new_cropped.jpg")

    # car_img_grey = cv2.cvtColor(car_img, cv2.COLOR_RGB2GRAY)
    # # car_img_hsv = cv2.cvtColor(car_img, cv2.COLOR_BGR2HSV)
    #
    # car_img_grey = cv2.bilateralFilter(car_img_grey, 11, 17, 17)

    print("Started feed...")
    start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0

    # instance_segmentation_model = instance_segmentation()
    # instance_segmentation_model.load_model('./config/maskrcnn/mask_rcnn_coco.h5')
    #
    # print("done")
    # # apply instance segmentation
    # result = instance_segmentation_model.segmentImage("./data/reference footage/images/car_parked3_new_cropped.jpg", show_bboxes=True)
    # img = result[1]
    #
    # cv2.imshow("instance segmented img", img)
    # cv2.waitKey(0)

    segment_image = semantic_segmentation()
    segment_image.load_pascalvoc_model("./config/maskrcnn/deeplabv3_xception_tf_dim_ordering_tf_kernels.h5")
    result = segment_image.segmentAsPascalvoc("./data/reference footage/images/car_parked3_new_cropped.jpg")
    mask = result[1]

if __name__ == "__main__":
    main()

#     img = LD.DetectLicenseInImage(cv2.imread("./config/license_plate_detector/carr2.jpg"))
#     cv2.imshow("img", img)
#     cv2.waitKey(0)

#     img = cv2.imread("data\\reference footage\\images\\carr2.jpg")
