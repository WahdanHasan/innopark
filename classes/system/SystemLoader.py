from classes.system_utilities.helper_utilities import Constants

import time
from multiprocessing import Event, Queue


base_pool_size = 3
camera_ids_and_links = Constants.CAMERA_DETAILS

def LoadComponents(shutdown_event):

    # Start helper processes
    new_tracked_object_event = Event()

    pool_initialized_event = Event()
    detector_initialized_event = Event()
    detector_request_queue = Queue()


    tracked_object_pool_request_queue = StartTrackedObjectPool(new_tracked_object_event=new_tracked_object_event,
                                                               initialized_event=pool_initialized_event,
                                                               shutdown_event=shutdown_event)

    broker_request_queue = StartBroker()

    pool_initialized_event.wait()


    wait_license_processing_event = StartEntranceCameras(broker_request_queue)

    wait_license_processing_event.wait()

    trackers = StartTrackers(broker_request_queue=broker_request_queue,
                             tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                             detector_request_queue=detector_request_queue,
                             detector_initialized_event=detector_initialized_event,
                             shutdown_event=shutdown_event)

    # Start main components
    StartDetectorProcess(detector_request_queue=detector_request_queue,
                         detector_initialized_event=detector_initialized_event,
                         shutdown_event=shutdown_event)

    StartParkingTariffManager(new_tracked_object_event=new_tracked_object_event,
                              shutdown_event=shutdown_event)


def StartParkingTariffManager(new_tracked_object_event, shutdown_event):
    from classes.system.parking.ParkingTariffManager import ParkingTariffManager

    ptm = ParkingTariffManager(amount_of_trackers=len(camera_ids_and_links),
                               base_pool_size=base_pool_size,
                               new_object_in_pool_event=new_tracked_object_event,
                               seconds_parked_before_charge=3)

    ptm.StartProcess()

    return ptm

def StartBroker():
    from classes.system_utilities.tracking_utilities.ObjectTrackerBroker import ObjectTrackerBroker

    broker_request_queue = Queue()

    ob = ObjectTrackerBroker(broker_request_queue=broker_request_queue)

    ob.StartProcess()

    return broker_request_queue

def StartTrackedObjectPool(new_tracked_object_event, initialized_event, shutdown_event):
    from classes.system_utilities.tracking_utilities import TrackedObject

    tracked_object_pool_request_queue = Queue()

    tracked_object_pool = TrackedObject.TrackedObjectPoolManager(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                                                 new_tracked_object_process_event=new_tracked_object_event,
                                                                 initialized_event=initialized_event,
                                                                 pool_size=base_pool_size)
    tracked_object_pool.StartProcess()

    return tracked_object_pool_request_queue

def StartTrackers(broker_request_queue, tracked_object_pool_request_queue, detector_request_queue, detector_initialized_event, shutdown_event):
    from classes.system_utilities.tracking_utilities import ObjectTracker as OT


    temp_trackers = []

    for i in range(len(camera_ids_and_links)):
        temp_tracker = OT.Tracker(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                  broker_request_queue=broker_request_queue,
                                  detector_request_queue=detector_request_queue,
                                  detector_initialized_event=detector_initialized_event)

        temp_trackers.append(temp_tracker)


    for i in range(len(temp_trackers)):
        temp_trackers[i].StartProcess(tracker_id=i,
                                      camera_rtsp=camera_ids_and_links[i][1],
                                      camera_id=camera_ids_and_links[i][0])

    return temp_trackers

def StartDetectorProcess(detector_request_queue, detector_initialized_event, shutdown_event):
    from classes.system_utilities.image_utilities.ObjectDetectionProcess import DetectorProcess
    time.sleep(3)
    detector = DetectorProcess(amount_of_trackers=len(camera_ids_and_links),
                               detector_request_queue=detector_request_queue,
                               detector_initialized_event=detector_initialized_event)
    detector.StartProcess()

def StartEntranceCameras(broker_request_queue, shutdown_event):
    from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector

    wait_license_processing_event = Event()

    license_frames_request_queue = Queue()

    license_detector = EntranceLicenseDetector(license_frames_request_queue=license_frames_request_queue,
                                               broker_request_queue=broker_request_queue,
                                               top_camera=Constants.ENTRANCE_CAMERA_DETAILS[0],
                                               bottom_camera=Constants.ENTRANCE_CAMERA_DETAILS[1],
                                               wait_license_processing_event=wait_license_processing_event)
    license_detector.StartProcess()


    return wait_license_processing_event


