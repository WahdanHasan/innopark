from multiprocessing import Event, Queue
from classes.system_utilities.helper_utilities import Constants
import time



base_pool_size = 10

is_debug_mode = True

# This needs to be changed to GUI
def main():

    # Start helper processes
    new_tracked_object_event = Event()

    broker_request_queue = StartBroker()

    tracked_object_pool_request_queue = StartTrackedObjectPool(new_tracked_object_event=new_tracked_object_event)

    trackers = StartTrackers(broker_request_queue=broker_request_queue,
                             tracked_object_pool_request_queue=tracked_object_pool_request_queue)


    time.sleep(2)
    # Start main components
    StartParkingTariffManager(new_tracked_object_event=new_tracked_object_event)

    import cv2
    cv2.namedWindow("Close this to close all")
    cv2.waitKey(0)


def StartParkingTariffManager(new_tracked_object_event):
    from classes.system.parking.ParkingTariffManager import ParkingTariffManager

    ptm = ParkingTariffManager(base_pool_size=base_pool_size,
                               new_object_in_pool_event=new_tracked_object_event)

    ptm.StartProcess()

    return ptm

def StartBroker():
    from classes.system_utilities.tracking_utilities.ObjectTrackerBroker import ObjectTrackerBroker

    broker_request_queue = Queue()

    ob = ObjectTrackerBroker(broker_request_queue=broker_request_queue)

    ob.StartProcess()

    return broker_request_queue

def StartTrackedObjectPool(new_tracked_object_event):
    from classes.system_utilities.tracking_utilities import TrackedObject

    tracked_object_pool_request_queue = Queue()

    tracked_object_pool = TrackedObject.TrackedObjectPoolManager(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                                                 new_tracked_object_process_event=new_tracked_object_event,
                                                                 pool_size=base_pool_size)
    tracked_object_pool.StartProcess()

    return tracked_object_pool_request_queue


def StartTrackers(broker_request_queue, tracked_object_pool_request_queue):
    from classes.system_utilities.tracking_utilities import ObjectTracker as OT

    camera_ids_and_links = Constants.CAMERA_DETAILS

    temp_trackers = []

    for i in range(len(camera_ids_and_links)):
        temp_tracker = OT.Tracker(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                  broker_request_queue=broker_request_queue,
                                  is_debug_mode=is_debug_mode)

        temp_trackers.append(temp_tracker)


    for i in range(len(temp_trackers)):
        temp_trackers[i].StartProcess(camera_rtsp=camera_ids_and_links[i][1],
                                      camera_id=camera_ids_and_links[i][0])

    return temp_trackers





if __name__ == "__main__":
    main()
