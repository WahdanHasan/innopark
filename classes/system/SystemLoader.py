from classes.system_utilities.helper_utilities import Constants

import sys
from multiprocessing import Event, Queue


camera_ids_and_links = Constants.CAMERA_DETAILS

def LoadComponents(shutdown_event, start_system_event):

    print("[SystemLoader] Loading system components", file=sys.stderr)

    new_tracked_object_event = Event()
    pool_initialized_event = Event()
    detector_initialized_event = Event()
    detector_request_queue = Queue()

    broker_request_queue = StartBroker()

    wait_license_processing_event = StartEntranceCameras(broker_request_queue=broker_request_queue,
                                                         shutdown_event=shutdown_event,
                                                         start_system_event=start_system_event)

    tracked_object_pool_request_queue = StartTrackedObjectPool(new_tracked_object_event=new_tracked_object_event,
                                                               initialized_event=pool_initialized_event,
                                                               shutdown_event=shutdown_event)

    _, tracker_initialized_events = StartTrackers(broker_request_queue=broker_request_queue,
                                                  tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                                  detector_request_queue=detector_request_queue,
                                                  detector_initialized_event=detector_initialized_event,
                                                  shutdown_event=shutdown_event,
                                                  start_system_event=start_system_event)

    StartDetectorProcess(detector_request_queue=detector_request_queue,
                         detector_initialized_event=detector_initialized_event,
                         tracker_initialized_events=tracker_initialized_events,
                         shutdown_event=shutdown_event)

    StartParkingTariffManager(new_tracked_object_event=new_tracked_object_event,
                              shutdown_event=shutdown_event,
                              start_system_event=start_system_event)

    print("[SystemLoader] Waiting for all components to finish loading..", file=sys.stderr)
    pool_initialized_event.wait()
    wait_license_processing_event.wait()
    print("[SystemLoader] Done Loading. Awaiting system start.", file=sys.stderr)

def StartParkingTariffManager(new_tracked_object_event, shutdown_event, start_system_event):
    from classes.system.parking.ParkingTariffManager import ParkingTariffManager

    ptm = ParkingTariffManager(amount_of_trackers=len(camera_ids_and_links),
                               new_object_in_pool_event=new_tracked_object_event,
                               seconds_parked_before_charge=3,
                               shutdown_event=shutdown_event,
                               start_system_event=start_system_event)

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
                                                                 shutdown_event=shutdown_event)
    tracked_object_pool.StartProcess()

    return tracked_object_pool_request_queue

def StartTrackers(broker_request_queue, tracked_object_pool_request_queue, detector_request_queue, detector_initialized_event, shutdown_event, start_system_event):
    from classes.system_utilities.tracking_utilities import ObjectTracker as OT


    temp_trackers = []
    temp_tracker_events = []

    for i in range(len(camera_ids_and_links)):
        temp_tracker_events.append(Event())
        temp_tracker = OT.Tracker(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                  broker_request_queue=broker_request_queue,
                                  detector_request_queue=detector_request_queue,
                                  detector_initialized_event=detector_initialized_event,
                                  tracker_initialized_event=temp_tracker_events[i],
                                  shutdown_event=shutdown_event,
                                  start_system_event=start_system_event)

        temp_trackers.append(temp_tracker)


    for i in range(len(temp_trackers)):
        temp_trackers[i].StartProcess(tracker_id=i,
                                      camera_rtsp=camera_ids_and_links[i][1],
                                      camera_id=camera_ids_and_links[i][0])

    return temp_trackers, temp_tracker_events

def StartDetectorProcess(detector_request_queue, detector_initialized_event, tracker_initialized_events, shutdown_event):
    from classes.system_utilities.image_utilities.ObjectDetectionProcess import DetectorProcess

    for i in range(len(tracker_initialized_events)):
        tracker_initialized_events[i].wait()

    detector = DetectorProcess(amount_of_trackers=len(camera_ids_and_links),
                               detector_request_queue=detector_request_queue,
                               detector_initialized_event=detector_initialized_event,
                               shutdown_event=shutdown_event)
    detector.StartProcess()

def StartEntranceCameras(broker_request_queue, shutdown_event, start_system_event):
    from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector

    wait_license_processing_event = Event()

    license_frames_request_queue = Queue()

    license_detector = EntranceLicenseDetector(license_frames_request_queue=license_frames_request_queue,
                                               broker_request_queue=broker_request_queue,
                                               top_camera=Constants.ENTRANCE_CAMERA_DETAILS[0],
                                               bottom_camera=Constants.ENTRANCE_CAMERA_DETAILS[1],
                                               wait_license_processing_event=wait_license_processing_event,
                                               shutdown_event=shutdown_event,
                                               start_system_event=start_system_event)
    license_detector.StartProcess()


    return wait_license_processing_event

