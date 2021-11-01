# import cv2
# from classes.camera.CameraBuffered import Camera
# from classes.system_utilities.image_utilities import ObjectDetection as OD
# from classes.system_utilities.image_utilities import ImageUtilities as IU
# import time
#
# def main():
#
#     cam_parking = Camera(
#         rtsp_link="data\\reference footage\\test journey\\Leg_2.mp4",
#         camera_id=0)
#
#     OD.OnLoad()
#     seconds_before_display = 1
#     counter = 0
#     start_time = time.time()
#     while True:
#         frame_parking = cam_parking.GetScaledNextFrame()
#
#
#         parking_return_status, parking_classes, parking_bounding_boxes, parking_scores = OD.DetectObjectsInImage(frame_parking)
#
#         if parking_return_status == True:
#             bb_parking = IU.DrawBoundingBoxAndClasses(image=frame_parking,
#                                                       class_names=parking_classes,
#                                                       probabilities=parking_scores,
#                                                       bounding_boxes=parking_bounding_boxes)
#
#             cv2.imshow("Drawn box parking", bb_parking)
#
#
#
#         cv2.imshow("Feed parking", frame_parking)
#         counter += 1
#         if (time.time() - start_time) > seconds_before_display:
#             print("FPS: ", counter / (time.time() - start_time))
#             counter = 0
#             start_time = time.time()
#
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             cv2.destroyAllWindows()
#             break
# if __name__ == "__main__":
#     main()
import classes.system_utilities.image_utilities.LicenseDetection_Custom as LD
import cv2
import classes.system_utilities.image_utilities.ImageUtilities as IU
# LD.BuildModel()
LD.OnLoad()

img = cv2.imread("data\\reference footage\\images\\carr2.jpg")
validity_status, classes, bounding_boxes_converted, scores = LD.DetectLicenseInImage(img)

img = IU.CropImage(img, bounding_boxes_converted[0])

cv2.imshow("EE", img)

print(LD.GetLicenseFromImage(img))

print("Done")

cv2.waitKey(0)