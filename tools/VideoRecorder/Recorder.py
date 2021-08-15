from classes.camera.Camera import Camera
import sys
import cv2
import time
from queue import Queue
from threading import Thread


is_recording = False
show_feed = False
window_name = "Video Recorder Options"
recording_start_time = 0
recording_end_time = 0

# Allocate memory for video writers
video_writers = []

# Allocate memory for camera names
cam_names = []
cam_count = 0

# Allocate queues for storing camera frames
cam_frames = []

def main():

    # Create global references
    global video_writers
    global cam_frames
    global cam_count
    global cam_names

    # Allocate memory for cameras array
    cameras = []

    # Create options GUI
    CreateGUI()

    # Input camera links
    cam_links = [
                 # "http://192.168.0.144:4747/video?1920x1080",
                 "http://192.168.0.139:4747/video?1920x1080",
                 # "http://192.168.0.137:4747/video?1920x1080",
                 # "http://192.168.0.197:4747/video?1920x1080"
                 ]

    # Input camera link names
    cam_names = [
                 # "IP7plus",
                 "IP7",
                 # "IP11",
                 # "S4"
                 ]

    # Get amount of cameras
    cam_count = len(cam_links)

    # Initialize cameras and cam_frames queue
    for i in range(cam_count):
        print("Initializing camera " + str(i+1) + "...")

        temp_camera = Camera(rtsp_link=cam_links[i],
                             camera_id=i,
                             name=cam_names[i])

        cameras.append(temp_camera)
        cam_frames.append(Queue(maxsize=0))

    # Allocate memory for video writers
    for i in range(cam_count):
        video_writers.append(0)


    # Create threads for video writing
    threads = []
    print("Starting video writer threads...")
    for i in range(cam_count):
        threads.append(Thread(target=WriteVideo, args=(i,)))
        threads[i].daemon = True
        threads[i].start()

    # Create empty array for storing temporary frames

    # Start feed
    print("Started feed...")
    program_start_time = time.time()
    fps_start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0

    temp_frames = [0, 0, 0, 0]
    while True:
        # Read frames from cameras
        for i in range(cam_count):
            temp_frames[i] = cameras[i].GetRawNextFrame()

        # Add frames to queue if recording is on
        if is_recording:
            for i in range(cam_count):
                cam_frames[i].put(temp_frames[i])

        # Show frame previews if previews are on
        if show_feed:
            for i in range(cam_count):
                cv2.imshow(str(i), temp_frames[i])

        # Log fps to console
        counter += 1
        if (time.time() - fps_start_time) > seconds_before_display:
            print("FPS: ", counter / (time.time() - fps_start_time))
            counter = 0
            fps_start_time = time.time()

        # Quit if user presses 'q', otherwise loop after 1ms
        if cv2.waitKey(1) & 0xFF == ord('q'):

            # Waits for all of the writer threads to finish writing the frames currently in the queue.
            print("Waiting for video writing threads to finish... ")
            can_quit = False
            while not can_quit:
                for i in range(cam_count):
                    if cam_frames[i].empty():
                        can_quit = True
                        break

                    # Put the main thread to sleep for 1 second
                    time.sleep(1)

            # Release cameras and video writers
            print("Releasing resources... ")
            for i in range(cam_count):
                cameras[i].ReleaseFeed()

            cv2.destroyAllWindows()
            break

    print("System run time: " + str(int(time.time()-program_start_time)) + " seconds.")
    print("The program will now exit.")

def WriteVideo(index):
    while True:
        try:
            video_writers[index].write(cam_frames[index].get())
        except:
            continue

def CreateGUI():


    cv2.namedWindow(window_name)

    cv2.createTrackbar('Recording', window_name, 0, 1, RecordingCallBack)
    cv2.setTrackbarPos('Recording', window_name, 0)

    cv2.createTrackbar('Preview', window_name, 0, 1, ShowFeedCallBack)
    cv2.setTrackbarPos('Preview', window_name, 0)

def RecordingCallBack(option):
    # Start the video writers when the option is 1 and stop them when the option is 0 (this saves the video)

    global is_recording
    global recording_start_time
    global recording_end_time

    if option == 0:
        is_recording = False
        recording_end_time = time.time()
        StopVideoWriters()
        print("Recording time was " + str(int(recording_end_time - recording_start_time)) + " seconds.", file=sys.stderr)
        print("The recordings will be saved and become available once the queue has finished.", file=sys.stderr)
        print("Kindly move these files out to avoid overwriting them.", file=sys.stderr)
    elif option == 1:
        is_recording = True
        recording_start_time = time.time()
        StartVideoWriters(cam_names=cam_names)
        print("Recording started.", file=sys.stderr)

def ShowFeedCallBack(option):
    global show_feed

    if option == 0:
        show_feed = False
    elif option == 1:
        show_feed = True

def StartVideoWriters(cam_names):
    # Set video codec
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')

    for i in range(cam_count):
        video_writers[i] = cv2.VideoWriter("recordings\\" + cam_names[i] + "_recording.avi", fourcc, 30.0, (1920, 1080))

def StopVideoWriters():

    for i in range(cam_count):
        video_writers[i].release()

if __name__ == "__main__":
    main()