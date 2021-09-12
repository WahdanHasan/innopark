import classes.system_utilities.image_utilities.ObjectTracker as OT
import multiprocessing
import cv2
# #
# #
# class myClass:
#     def __init__(self, obj):
#         self.obj = obj
#
#     def getObj(self):
#         return self.obj
# #
def main():


    # tracker_1 = OT.Tracker(is_debug_mode=False)
    tracker_2 = OT.Tracker(is_debug_mode=True)
    # tracker_3 = OT.Tracker()
    # tracker_4 = OT.Tracker()

    tracker_2.AddParkingSpaceToTracker(189, [[195, 211], [346, 213], [147, 414], [477, 391]])
    tracker_2.AddParkingSpaceToTracker(188, [[349, 214], [481, 214], [480, 391], [718, 367]])
    tracker_2.AddParkingSpaceToTracker(187, [[483, 213], [604, 214], [718, 366], [718, 265]])

    # tracker_1.Start(camera_rtsp="data\\reference footage\\test journey\\Leg_1.mp4",
    #                 camera_id=1)

    tracker_2.Start(camera_rtsp="data\\reference footage\\test journey\\Leg_2_Short.mp4",
                    camera_id=2)

    # tracker_3.Start(camera_rtsp="data\\reference footage\\test journey\\Entrance_Bottom.mp4",
    #                 camera_id=3)
    #
    # tracker_4.Start(camera_rtsp="data\\reference footage\\test journey\\Entrance_Top.mp4",
    #                 camera_id=4)



    cv2.namedWindow("Close this to close all")
    cv2.waitKey(0)

    # tracker_1.Stop()
    tracker_2.Stop()
    # tracker_3.Stop()
    # tracker_4.Stop()
# #
# #
# #
#     conn1, conn2 = multiprocessing.Pipe()
#
#     p1 = multiprocessing.Process(target=target1, args=(conn1, ))
#     p1.start()
#     a = myClass("Hello mister")
#     conn2.send(a)
#     msg = conn2.recv()
#     print(msg)
#     # p1.join()
#     print("done")
#
#
# # def StartTrackerProcess()
#
#
# def target1(conn):
#     msg = conn.recv().getObj()
#     print(msg)
#     conn.send(msg)
#     print("finished target1")
# #
# #
# #
# #
if __name__ == "__main__":
    main()