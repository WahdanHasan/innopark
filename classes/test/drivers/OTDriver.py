import classes.system_utilities.tracking_utilities.TrackedObject as TO
from classes.system_utilities.tracking_utilities.ObjectTrackerBroker import ObjectTrackerBroker
from classes.system_utilities.helper_utilities.Enums import EntrantSide
from classes.system_utilities.helper_utilities.Enums import TrackedObjectToBrokerInstruction

import multiprocessing
import cv2

def main():



    broker_request_queue = multiprocessing.Queue()

    broker_process = StartBroker(broker_request_queue)

    tracked_object_pool_request_queue, pool_process = StartTrackedObjectPool()

    import classes.system_utilities.tracking_utilities.ObjectTracker as OT

    tracker_1 = OT.Tracker(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                           broker_request_queue=broker_request_queue,
                           is_debug_mode=True)

    tracker_2 = OT.Tracker(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                           broker_request_queue=broker_request_queue,
                           is_debug_mode=True)

    # tracker_2.AddParkingSpaceToTracker(189, [[195, 211], [346, 213], [147, 414], [477, 391]])
    # tracker_2.AddParkingSpaceToTracker(188, [[349, 214], [481, 214], [480, 391], [718, 367]])
    # tracker_2.AddParkingSpaceToTracker(187, [[483, 213], [604, 214], [718, 366], [718, 265]])

    # License camera goes here
    broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, 1, 'J71612', EntrantSide.LEFT))

    tracker_1.StartProcess(camera_rtsp="data\\reference footage\\test journey\\Leg_1.mp4",
                           camera_id=2)

    tracker_2.StartProcess(camera_rtsp="data\\reference footage\\test journey\\Leg_2.mp4",
                           camera_id=3)


    cv2.namedWindow("Close this to close all")
    cv2.waitKey(0)

    tracker_1.StopProcess()
    tracker_2.StopProcess()

    # Pool should release all tracked objects before terminating
    pool_process.terminate()
    broker_process.terminate()

def StartBroker(broker_request_queue):

    driver = ObjectTrackerBroker()
    broker_process = multiprocessing.Process(target=driver.Start, args=(broker_request_queue,))
    broker_process.start()

    return broker_process

def StartTrackedObjectPool():

    tracked_object_pool = TO.TrackedObjectPoolManager()
    tracked_object_pool_request_queue = tracked_object_pool.Initialize(pool_size=10)
    pool_process = multiprocessing.Process(target=tracked_object_pool.start)
    pool_process.start()

    return tracked_object_pool_request_queue, pool_process



if __name__ == "__main__":
    main()