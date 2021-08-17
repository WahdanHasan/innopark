from classes.camera.Camera import Camera
import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.enum_classes.Enums import ImageResolution
import sys
import cv2
import time
from queue import Queue
from threading import Thread


is_recording = False
is_fps_boost = False
preview_index = 0
show_feed = False
options_window_name = "Video Recorder Options"
preview_window_name = "Live Preview Cam "
concatenated_window_name = "Concatenated Preview"
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

    # Input camera links
    cam_links = [
                 "http://10.115.0.35:4747/video?1920x1080",
                 # "http://192.168.0.139:4747/video?1920x1080",
                 # "http://192.168.0.137:4747/video?1920x1080",
                 # "http://192.168.0.187:4747/video?1920x1080",
                 # "http://192.168.0.197:4747/video?1920x1080"
                 ]

    # Input camera link names
    cam_names = [
                 "IP7plus",
                 # "IP7",
                 # "IP11",
                 # "IPA",
                 # "S4"
                 ]

    # Get amount of cameras
    cam_count = len(cam_links)

    # Create options GUI
    CreateGUI()

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

    # Allocate memory for temporary frames
    temp_frames = []
    for i in range(cam_count):
        temp_frames.append(0)

    # Set recording variables
    recording_fps_target = 60
    recording_start = time.time()
    seconds_before_next_capture = 1/recording_fps_target
    counter_x = 0

    # Start feed
    print("Started feed...")
    program_start_time = time.time()
    fps_start_time = time.time()
    seconds_before_display = 1  # displays the frame rate every 1 second
    counter = 0


    while True:
        # Read frames from cameras
        for i in range(cam_count):
            temp_frames[i] = cameras[i].GetRawNextFrame()

        # Add frames to queue if recording is on
        counter_x += 1
        if (time.time() - recording_start) > seconds_before_next_capture:
            recording_start = time.time()
            if is_recording:
                for i in range(cam_count):
                    cam_frames[i].put(temp_frames[i])

        # Show concatenated frame previews
        if show_feed and not is_fps_boost:
            for i in range(cam_count):
                temp_frames[i] = IU.RescaleImageToResolution(img=temp_frames[i],
                                                             new_dimensions=ImageResolution.NTSC.value)
            concatenated_feed = IU.ConcatenatePictures(temp_frames)

            cv2.imshow(concatenated_window_name, concatenated_feed)
        else:
            try:
                cv2.destroyWindow(concatenated_window_name)
            except:
                x=10

        # Show single frame preview
        if is_fps_boost:
            cv2.imshow(preview_window_name, temp_frames[preview_index])
        else:
            try:
                cv2.destroyWindow(preview_window_name)
            except:
                x=10


        # Log fps to console
        counter += 1
        if (time.time() - fps_start_time) > seconds_before_display:
            print("FPS: ", counter / (time.time() - fps_start_time))
            counter = 0
            fps_start_time = time.time()

        # Quit if user presses 'q', otherwise loop after 1ms
        if cv2.waitKey(1) & 0xFF == ord('q'):

            # Waits for all of the writer threads to finish writing the frames currently in the queue.
            print("Waiting for video writing threads to finish... ", file=sys.stderr)
            can_quit = False
            while not can_quit:
                can_quit = True
                for i in range(cam_count):
                    if not cam_frames[i].empty():
                        can_quit = False
                        break

                # Put the main thread to sleep for 1 second
                time.sleep(1)

            # Release cameras and video writers
            print("Releasing resources... ", file=sys.stderr)
            for i in range(cam_count):
                cameras[i].ReleaseFeed()

            cv2.destroyAllWindows()
            break

    print("System run time: " + str(int(time.time()-program_start_time)) + " seconds.", file=sys.stderr)
    print("The program will now exit.", file=sys.stderr)



def CreateGUI():

    cv2.namedWindow(options_window_name)
    cv2.resizeWindow(options_window_name, (500, 120))

    cv2.createTrackbar('Recording', options_window_name, 0, 1, RecordingCallBack)
    cv2.setTrackbarPos('Recording', options_window_name, 0)

    cv2.createTrackbar('FPreview', options_window_name, 0, 1, ShowFeedCallBack)
    cv2.setTrackbarPos('FPreview', options_window_name, 0)

    cv2.createTrackbar('SPreview', options_window_name, 0, cam_count, LivePreviewCallBack)
    cv2.setTrackbarPos('SPreview', options_window_name, 0)

def RecordingCallBack(option):
    # Start the video writers when the option is 1 and stop them when the option is 0 (this saves the video)

    global is_recording
    global recording_start_time
    global recording_end_time

    if option == 0:
        is_recording = False
        recording_end_time = time.time()
        # StopVideoWriters()
        t1 = Thread(target=StopVideoWriters, args=())
        t1.daemon = True
        t1.start()
        print("Recording time was " + str(round(recording_end_time - recording_start_time, 2)) + " seconds.", file=sys.stderr)
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

def LivePreviewCallBack(option):
    global is_fps_boost
    global preview_index

    if option == 0:
        is_fps_boost = False
    elif option == 1:
        is_fps_boost = True

    preview_index = option - 1

def StartVideoWriters(cam_names):
    # Set video codec
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    for i in range(cam_count):
        video_writers[i] = cv2.VideoWriter("recordings\\" + cam_names[i] + "_recording.avi", fourcc, 30.0, (1920, 1080))

def WriteVideo(index):
    while True:
        try:
            video_writers[index].write(cam_frames[index].get())
        except:
            continue

def StopVideoWriters():

    # for i in range(cam_count):
    #     video_writers[i].release()

    can_quit = False
    while not can_quit:
        can_quit = True
        for i in range(cam_count):
            if not cam_frames[i].empty():
                can_quit = False
                break

        # Put the main thread to sleep for 1 second
        time.sleep(1)

    for i in range(cam_count):
        video_writers[i].release()

    print("Finished saving!", file=sys.stderr)


if __name__ == "__main__":
    main()