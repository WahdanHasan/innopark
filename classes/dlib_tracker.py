import os
import glob

from classes.camera.Camera import Camera
import cv2
import time
import dlib

# Path to the video frames
#video_folder = os.path.join("..", "examples", "video_frames")
cap = Camera(rtsp_link="..\\data\\reference footage\\videos\\Car_Pass3.mp4",
             camera_id=0)
#cap = Camera("..\\data\\reference footage\\videos\\Leg_2_Starting_Full.mp4", 0)
# 138, 166, 485, 349
#bbox = [[38, 247], [530,419]] #car_full

frame = cap.GetScaledNextFrame()

# Create the correlation tracker - the object needs to be initialized
# before it can be used
tracker = dlib.correlation_tracker()

win = dlib.image_window()

#tracker.start_track(frame, dlib.rectangle(74, 67, 112, 153))
tracker.start_track(frame, dlib.rectangle(160, 100, 350, 219))

start_time = time.time()
seconds_before_display = 1  # displays the frame rate every 1 second
counter = 0
while True:

    tracker.update(frame)
    frame = cap.GetScaledNextFrame()

    win.clear_overlay()
    win.set_image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    win.add_overlay(tracker.get_position())
    #dlib.hit_enter_to_continue()

    counter += 1
    if (time.time() - start_time) > seconds_before_display:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()

    if cv2.waitKey(1) == 27:
        cap.release()
        cv2.destroyAllWindows()
        break