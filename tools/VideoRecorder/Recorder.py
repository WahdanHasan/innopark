from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
from queue import Queue
from threading import Thread

cam_1 = 0
cam_2 = 0
cam_3 = 0
cam_4 = 0
cameras = [cam_1, cam_2, cam_3]
cam_count = len(cameras)

cam_1_out = 0
cam_2_out = 0
cam_3_out = 0
cam_4_out = 0
video_writers = [cam_1_out, cam_2_out, cam_3_out, cam_4_out]


cam_1_frames = Queue(maxsize=0)
cam_2_frames = Queue(maxsize=0)
cam_3_frames = Queue(maxsize=0)
cam_4_frames = Queue(maxsize=0)
cam_frames = [cam_1_frames, cam_2_frames, cam_3_frames, cam_4_frames]

def main():

    cv2.namedWindow("EE")
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')

    global video_writers
    global cameras

    # Connect to cameras
    print("Initializing cameras 1")
    cameras[0] = Camera(rtsp_link="http://192.168.0.144:4747/video?1920x1080",
                        camera_id=0)
    video_writers[0] = cv2.VideoWriter('ip7plus_recording.avi', fourcc, 30.0, (1920, 1080))

    print("Initializing cameras 2")
    cameras[1] = Camera(rtsp_link="http://192.168.0.139:4747/video?1920x1080",
                        camera_id=1)
    video_writers[1] = cv2.VideoWriter('ip7_recording.avi', fourcc, 30.0, (1920, 1080))

    print("Initializing cameras 4")
    cameras[2] = Camera(rtsp_link="http://192.168.0.137:4747/video?1920x1080",
                        camera_id=2)
    video_writers[2] = cv2.VideoWriter('ip11_recording.avi', fourcc, 30.0, (1920, 1080))

    # print("Initializing cameras 3")
    # cameras[3] = Camera(rtsp_link="http://192.168.0.197:4747/video?1920x1080",
    #                     camera_id=3)
    # video_writers[3] = cv2.VideoWriter('s4_recording.avi', fourcc, 30.0, (1920, 1080))


    threads = [0, 0, 0, 0]
    print("Starting video writer threads...")
    for i in range(cam_count):
        threads[i] = Thread(target=WriteVideo, args=(i,))
        threads[i].daemon = True
        threads[i].start()

    print("Started feed...")
    start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0



    while True:
        # Read frames from cameras
        for i in range(cam_count):
            temp_frame = cameras[i].GetRawNextFrame()
            cam_frames[i].put(temp_frame)

        # Log fps to console
        counter += 1
        if (time.time() - start_time) > seconds_before_display:
            print("FPS: ", counter / (time.time() - start_time))
            counter = 0
            start_time = time.time()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            for i in range(cam_count):
                cameras[i].ReleaseFeed()
            cv2.destroyAllWindows()
            break

def WriteVideo(index):
    while True:
        video_writers[index].write(cam_frames[index].get())

if __name__ == "__main__":
    main()