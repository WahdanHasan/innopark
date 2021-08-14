from classes.camera.Camera import Camera
import cv2
import time

print("Cameras starting... ")
# cam_1 = Camera(rtsp_link="rtsp://192.168.0.144",
#                camera_id=0)

# cam_2 = Camera(rtsp_link="rtsp://192.168.0.197:8080/h264_ulaw.sdp",
#                camera_id=1)

cam_2 = Camera(rtsp_link="rtsp://192.168.0.139",
               camera_id=2)

print("Started feed...")
start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
while True:
    # frame_1 = cam_1.GetRawNextFrame()
    frame_2 = cam_2.GetRawNextFrame()

    # cv2.imshow("1", frame_1)
    cv2.imshow("2", frame_2)

    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
