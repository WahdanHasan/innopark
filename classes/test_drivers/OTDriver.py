
import classes.system_utilities.tracking_utilities.TrackedObject as TO
from classes.system_utilities.tracking_utilities.ObjectTrackerBroker import ObjectTrackerBroker
from classes.helper_classes.Enums import EntrantSide

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

    # mm = cv2.imread("data\\mm_2.png")
    #
    # import classes.system_utilities.image_utilities.ObjectDetection as OD
    # import classes.system_utilities.image_utilities.ImageUtilities as IU
    #
    # return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=mm)
    #
    # mm = IU.DrawBoundingBoxAndClasses(mm, classes, _,bounding_boxes)
    #
    # cv2.imshow("EEE", mm)
    # cv2.waitKey(0)

    get_voyager_request_queue = multiprocessing.Queue()
    send_voyager_request_queue = multiprocessing.Queue()

    broker_process = StartBroker(send_voyager_request_queue, get_voyager_request_queue)

    get_pool_queue, return_pool_queue, pool_process = StartTrackedObjectPool()

    import classes.system_utilities.tracking_utilities.ObjectTracker as OT

    tracker_1 = OT.Tracker(tracked_object_get_pool_queue=get_pool_queue,
                           tracked_object_return_pool_queue=return_pool_queue,
                           get_voyager_request_queue=get_voyager_request_queue,
                           send_voyager_request_queue=send_voyager_request_queue,
                           is_debug_mode=True)

    tracker_2 = OT.Tracker(tracked_object_get_pool_queue=get_pool_queue,
                           tracked_object_return_pool_queue=return_pool_queue,
                           get_voyager_request_queue=get_voyager_request_queue,
                           send_voyager_request_queue=send_voyager_request_queue,
                           is_debug_mode=True)

    tracker_2.AddParkingSpaceToTracker(189, [[195, 211], [346, 213], [147, 414], [477, 391]])
    tracker_2.AddParkingSpaceToTracker(188, [[349, 214], [481, 214], [480, 391], [718, 367]])
    tracker_2.AddParkingSpaceToTracker(187, [[483, 213], [604, 214], [718, 366], [718, 265]])

    # License camera goes here
    send_voyager_request_queue.put((1, 'J71612', EntrantSide.LEFT))

    tracker_1.StartProcess(camera_rtsp="data\\reference footage\\test journey\\Leg_1.mp4",
                           camera_id=2)

    tracker_2.StartProcess(camera_rtsp="data\\reference footage\\test journey\\Leg_2.mp4",
                           camera_id=3)


    # time.sleep(1)
    #
    # pipe1, pipe2 = multiprocessing.Pipe()
    #
    # send_voyager_request_queue.put((1, 50, "left"))
    #
    # get_voyager_request_queue.put((2, "left", pipe2))
    #
    #
    # print("Waiting for id")
    # temp_id = pipe1.recv()
    # print(temp_id)
    #
    #
    cv2.namedWindow("Close this to close all")
    cv2.waitKey(0)

    tracker_1.StopProcess()
    tracker_2.StopProcess()

    # Pool should release all tracked objects before terminating
    pool_process.terminate()
    broker_process.terminate()

def StartBroker(voyager_input_queue, voyager_output_queue):

    driver = ObjectTrackerBroker()
    broker_process = multiprocessing.Process(target=driver.Start, args=(voyager_input_queue, voyager_output_queue))
    broker_process.start()

    return broker_process

def StartTrackedObjectPool():

    tracked_object_pool = TO.TrackedObjectPoolManager()
    get_pool_queue, return_pool_queue = tracked_object_pool.Initialize(pool_size=10)
    pool_process = multiprocessing.Process(target=tracked_object_pool.Start)
    pool_process.start()

    return get_pool_queue, return_pool_queue, pool_process



if __name__ == "__main__":
    main()