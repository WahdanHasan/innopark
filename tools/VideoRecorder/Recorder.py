from classes.camera.Camera import Camera
import cv2
import time

print("Cameras starting... ")
cam_1 = Camera(rtsp_link="rtsp://192.168.0.144",
               camera_id=0)

cam_2 = Camera(rtsp_link="rtsp://192.168.0.139",
               camera_id=1)

# cam_3 = Camera(rtsp_link="rtsp://192.168.0.197:8080/h264_ulaw.sdp",
#                camera_id=3)

# cam_1 = cv2.VideoCapture("rtsp://192.168.0.144")
# cam_2 = cv2.VideoCapture("rtsp://192.168.0.139")
# cam_3 = cv2.VideoCapture("rtsp://192.168.0.197:8080/h264_ulaw.sdp")


fourcc = cv2.VideoWriter_fourcc(*'DIVX')
# _, frame_1 = cam_1.read()
# _, frame_2 = cam_2.read()
# _, frame_3 = cam_3.read()
cam_1_out = cv2.VideoWriter('ip7plus_recording.avi', fourcc, cam_1.feed.get(cv2.CAP_PROP_FPS), (cam_1.GetRawNextFrame().shape[1], cam_1.GetRawNextFrame().shape[0]))
cam_2_out = cv2.VideoWriter('ip7_recording.avi', fourcc, cam_2.feed.get(cv2.CAP_PROP_FPS), (cam_2.GetRawNextFrame().shape[1], cam_2.GetRawNextFrame().shape[0]))
# cam_3_out = cv2.VideoWriter('s4_recording.avi', fourcc, cam_3.feed.get(cv2.CAP_PROP_FPS), (cam_3.GetRawNextFrame().shape[1], cam_3.GetRawNextFrame().shape[0]))
# cam_1_out = cv2.VideoWriter('ip7plus_recording.avi', fourcc, cam_1.get(cv2.CAP_PROP_FPS), (frame_1.shape[1], frame_1.shape[0]))
# cam_2_out = cv2.VideoWriter('ip7_recording.avi', fourcc, cam_2.get(cv2.CAP_PROP_FPS), (frame_2.shape[1], frame_2.shape[0]))
# cam_3_out = cv2.VideoWriter('s4_recording.avi', fourcc, cam_3.get(cv2.CAP_PROP_FPS), (frame_3.shape[1], frame_3.shape[0]))

print("Started feed...")
start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
while True:
    # _, frame_1 = cam_1.read()
    # _, frame_2 = cam_2.read()
    # _, frame_3 = cam_3.read()
    frame_1 = cam_1.GetRawNextFrame()
    frame_2 = cam_2.GetRawNextFrame()
    # frame_3 = cam_3.GetRawNextFrame()


    cv2.imshow("x", frame_1)

    cam_1_out.write(frame_1)
    cam_2_out.write(frame_2)
    # cam_3_out.write(frame_3)

    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()
    if cv2.waitKey(1) & 0xFF == ord('q'):
        # cam_1.ReleaseFeed()
        cam_1_out.release()
        cam_2_out.release()
        cam_3_out.release()
        cv2.destroyAllWindows()
        break
