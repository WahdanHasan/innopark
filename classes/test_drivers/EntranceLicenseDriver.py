import cv2
from classes.camera.CameraBuffered import Camera
from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector

from classes.system_utilities.image_utilities.ObjectDetection import DetectObjectsInImage

licenseDetector = EntranceLicenseDetector()

licenseDetector.StartProcess(["D:\\DownloadsD\\License_Footage\\Entrance_Bottom_Simulated_2.mp4", 0],
                             ["D:\\DownloadsD\\License_Footage\\Entrance_Top.mp4", 1])

# cam = Camera(rtsp_link="D:\\DownloadsD\\License_Footage\\Entrance_Top.mp4",
#             camera_id=0)


# cam = Camera(rtsp_link=camera1[0],
#             camera_id=camera1[1])
#
# cam2 = Camera(rtsp_link=camera2[0],
#              camera_id=camera2[1])
#
# subtraction_model2 = OD.SubtractionModel()
#
# while True:
#     frame = cam.GetScaledNextFrame()
#     frame2 = cam2.GetScaledNextFrame()
#
#     subtraction_model2.FeedSubtractionModel(image=frame2, learningRate=0.0001)
#     mask2 = subtraction_model2.GetOutput()
#
#     cv2.imshow('camera1', frame)
#     cv2.imshow('camera2', frame2)
#     cv2.imshow('subtraction_model2', mask2)
#
#     if cv2.waitKey(1) == 27:
#         cam.release()
#         cam2.release()
#         cv2.destroyAllWindows()
#         break

