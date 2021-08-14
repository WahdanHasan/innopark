from classes.camera.Camera import Camera
import cv2
import time

cv2.namedWindow("EE")
fourcc = cv2.VideoWriter_fourcc(*'DIVX')

# Connect to cameras
print("Initializing cameras 1")
cam_1 = Camera(rtsp_link="http://192.168.0.144:4747/video?1920x1080",
               camera_id=0)
cam_1_out = cv2.VideoWriter('ip7plus_recording.avi', fourcc, cam_1.feed.get(cv2.CAP_PROP_FPS), (cam_1.GetRawNextFrame().shape[1], cam_1.GetRawNextFrame().shape[0]))

print("Initializing cameras 2")
cam_2 = Camera(rtsp_link="http://192.168.0.139:4747/video?1920x1080",
               camera_id=1)
cam_2_out = cv2.VideoWriter('ip7_recording.avi', fourcc, cam_2.feed.get(cv2.CAP_PROP_FPS), (cam_2.GetRawNextFrame().shape[1], cam_2.GetRawNextFrame().shape[0]))

# print("Initializing cameras 3")
# cam_3 = Camera(rtsp_link="http://192.168.0.197:4747/video?1920x1080",
#                camera_id=3)
# cam_3_out = cv2.VideoWriter('s4_recording.avi', fourcc, cam_3.feed.get(cv2.CAP_PROP_FPS), (cam_3.GetRawNextFrame().shape[1], cam_3.GetRawNextFrame().shape[0]))

# Initialize array of cameras and video writers
cameras = [cam_1, cam_2]
video_writers = [cam_1_out, cam_2_out]


print("Started feed...")
start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0

# Initialize list
frames = []
cam_count = len(cameras)
for i in range(cam_count):
    frames.append(0)

while True:
    # Read frames from cameras
    for i in range(cam_count):
        frames[i] = cameras[i].GetRawNextFrame()
        # cv2.imshow(str(i), frames[i])

    # Write frames to video file
    for i in range(cam_count):
        video_writers[i].write(frames[i])

    # Log fps to console
    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        # Release video writers and cameras
        for i in range(cam_count):
            video_writers[i].release()
            cameras[i].ReleaseFeed()

        cv2.destroyAllWindows()
        break

# import cv2
# import numpy as np
# import classes.system_utilities.image_utilities.ImageUtilities as IU
# import time
#
# url = "http://192.168.0.197:4747/video?1920x1080"
# # url2= "http://192.168.0.139:4747/video?1920x1080"
#
# cap = cv2.VideoCapture(url)
# # cap2 = cv2.VideoCapture(url2)
#
# print("Started feed...")
# start_time = time.time()
# seconds_before_display = 1  # displays the frame rate every 1 second
# counter = 0
#
# while True:
#     _, frame = cap.read()
#     # _, frame2 = cap2.read()
#     cv2.imshow("x", frame)
#     # cv2.imshow("y", frame2)
#
#     counter += 1
#     if (time.time() - start_time) > seconds_before_display:
#         print("FPS: ", counter / (time.time() - start_time))
#         counter = 0
#         start_time = time.time()
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         cv2.destroyAllWindows()
#         break