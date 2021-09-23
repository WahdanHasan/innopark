from multiprocessing import Event, Queue
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import TrackedObjectToBrokerInstruction
from classes.system_utilities.helper_utilities.Enums import EntrantSide
import time
import sys


base_pool_size = 10

is_debug_mode = True

camera_ids_and_links = Constants.CAMERA_DETAILS


# This needs to be changed to GUI
def main():
    # print(sys.getsizeof(Constants.tracked_process_ids_example[0]))
    # return
    # Start helper processes
    new_tracked_object_event = Event()

    tracked_object_pool_request_queue = StartTrackedObjectPool(new_tracked_object_event=new_tracked_object_event)

    broker_request_queue = StartBroker()

    broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, 1, 'J71612', EntrantSide.LEFT))

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

    ptm = ParkingTariffManager(amount_of_trackers=len(camera_ids_and_links),
                               base_pool_size=base_pool_size,
                               new_object_in_pool_event=new_tracked_object_event,
                               seconds_parked_before_charge=3,
                               is_debug_mode=is_debug_mode)

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


    temp_trackers = []

    for i in range(len(camera_ids_and_links)):
        temp_tracker = OT.Tracker(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                  broker_request_queue=broker_request_queue)

        temp_trackers.append(temp_tracker)


    for i in range(len(temp_trackers)):
        temp_trackers[i].StartProcess(tracker_id=i,
                                      camera_rtsp=camera_ids_and_links[i][1],
                                      camera_id=camera_ids_and_links[i][0])

    return temp_trackers





if __name__ == "__main__":
    main()
