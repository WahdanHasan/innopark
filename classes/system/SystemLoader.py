from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import YoloModel
import sys
from multiprocessing import Event, Queue


camera_ids_and_links = Constants.CAMERA_DETAILS

def LoadComponents(shutdown_event, start_system_event):

    print("[SystemLoader] Loading system components", file=sys.stderr)

    new_tracked_object_event = Event()
    pool_initialized_event = Event()
    object_detector_initialized_event = Event()
    license_detector_initialized_event = Event()
    ptm_initialized_event = Event()
    pvm_initialized_event = Event()
    entrance_cameras_initialized_event = Event()
    object_detector_request_queue = Queue()
    license_detector_request_queue = Queue()
    recovery_input_queue = Queue()

    broker_request_queue = StartBroker()

    wait_license_processing_event = StartEntranceCameras(broker_request_queue=broker_request_queue,
                                                         detector_request_queue=object_detector_request_queue,
                                                         license_detector_request_queue=license_detector_request_queue,
                                                         entrance_cameras_initialized_event=entrance_cameras_initialized_event,
                                                         shutdown_event=shutdown_event,
                                                         start_system_event=start_system_event)

    tracked_object_pool_request_queue = StartTrackedObjectPool(new_tracked_object_event=new_tracked_object_event,
                                                               initialized_event=pool_initialized_event,
                                                               shutdown_event=shutdown_event)

    _, tracker_initialized_events = StartTrackers(broker_request_queue=broker_request_queue,
                                                  tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                                  detector_request_queue=object_detector_request_queue,
                                                  detector_initialized_event=object_detector_initialized_event,
                                                  shutdown_event=shutdown_event,
                                                  start_system_event=start_system_event,
                                                  ptm_initialized_event=ptm_initialized_event)

    for i in range(len(tracker_initialized_events)):
        tracker_initialized_events[i].wait()

    StartLicenseRecoveryProcess(recovery_input_queue=recovery_input_queue,
                                license_detector_queue=license_detector_request_queue)

    StartDetectorProcess(detector_request_queue=object_detector_request_queue,
                         detector_initialized_event=object_detector_initialized_event)

    StartDetectorProcess(detector_request_queue=license_detector_request_queue,
                         detector_initialized_event=license_detector_initialized_event,
                         model=YoloModel.LICENSE_DETECTOR)

    StartParkingTariffManager(new_tracked_object_event=new_tracked_object_event,
                              shutdown_event=shutdown_event,
                              start_system_event=start_system_event,
                              ptm_initialized_event=ptm_initialized_event,
                              recovery_input_queue=recovery_input_queue)

    StartParkingViolationManager(new_tracked_object_event=new_tracked_object_event,
                                 shutdown_event=shutdown_event,
                                 start_system_event=start_system_event,
                                 pvm_initialized_event=pvm_initialized_event,
                                 ptm_initialized_event=ptm_initialized_event)

    print("[SystemLoader] Waiting for all components to finish loading..", file=sys.stderr)
    entrance_cameras_initialized_event.wait()
    pool_initialized_event.wait()
    wait_license_processing_event.wait()
    object_detector_initialized_event.wait()
    pvm_initialized_event.wait()
    ptm_initialized_event.wait()
    print("[SystemLoader] Done Loading. Awaiting system start.", file=sys.stderr)

    return new_tracked_object_event, object_detector_request_queue, tracked_object_pool_request_queue, broker_request_queue, license_detector_request_queue, recovery_input_queue

def StartParkingTariffManager(new_tracked_object_event, shutdown_event, start_system_event, ptm_initialized_event, recovery_input_queue):
    from classes.system.parking.ParkingTariffManager import ParkingTariffManager

    ptm = ParkingTariffManager(amount_of_trackers=len(camera_ids_and_links),
                               new_object_in_pool_event=new_tracked_object_event,
                               seconds_parked_before_charge=3,
                               shutdown_event=shutdown_event,
                               start_system_event=start_system_event,
                               ptm_initialized_event=ptm_initialized_event,
                               recovery_input_queue=recovery_input_queue)

    ptm.startProcess()

    return ptm

def StartParkingViolationManager(new_tracked_object_event, shutdown_event, start_system_event, pvm_initialized_event, ptm_initialized_event):
    from classes.system.parking.ParkingViolationManager import ParkingViolationManager

    pvm = ParkingViolationManager(amount_of_trackers=len(camera_ids_and_links),
                                  new_object_in_pool_event=new_tracked_object_event,
                                  shutdown_event=shutdown_event,
                                  start_system_event=start_system_event,
                                  pvm_initialized_event=pvm_initialized_event,
                                  ptm_initialized_event=ptm_initialized_event)

    pvm.startProcess()

    return pvm

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
    tracked_object_pool.startProcess()

    return tracked_object_pool_request_queue

def StartTrackers(broker_request_queue, tracked_object_pool_request_queue, detector_request_queue, detector_initialized_event, shutdown_event, start_system_event, ptm_initialized_event):
    from classes.system_utilities.tracking_utilities import ObjectTracker as OT


    temp_trackers = []
    temp_tracker_events = []

    seconds_before_detection = Constants.ot_seconds_before_scan

    for i in range(len(camera_ids_and_links)):
        temp_tracker_events.append(Event())
        temp_tracker = OT.Tracker(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                  broker_request_queue=broker_request_queue,
                                  detector_request_queue=detector_request_queue,
                                  detector_initialized_event=detector_initialized_event,
                                  tracker_initialized_event=temp_tracker_events[i],
                                  shutdown_event=shutdown_event,
                                  start_system_event=start_system_event,
                                  ptm_initialized_event=ptm_initialized_event,
                                  seconds_between_detections=seconds_before_detection)

        temp_trackers.append(temp_tracker)

        seconds_before_detection += Constants.ot_seconds_before_scan_growth


    for i in range(len(temp_trackers)):
        temp_trackers[i].StartProcess(tracker_id=i,
                                      camera_rtsp=camera_ids_and_links[i][1],
                                      camera_id=camera_ids_and_links[i][0])

    return temp_trackers, temp_tracker_events

def StartLicenseRecoveryProcess(recovery_input_queue, license_detector_queue):
    from classes.system_utilities.tracking_utilities.LicenseRecoveryProcess import LicenseRecoveryProcess

    license_recovery_process = LicenseRecoveryProcess(recovery_input_queue=recovery_input_queue,
                                                      license_detector_queue=license_detector_queue)

    license_recovery_process.startProcess()


def StartDetectorProcess(detector_request_queue, detector_initialized_event, model=YoloModel.YOLOV3):
    from classes.system_utilities.image_utilities.ObjectDetectionProcess import DetectorProcess

    detector = DetectorProcess(amount_of_trackers=len(camera_ids_and_links),
                               detector_request_queue=detector_request_queue,
                               detector_initialized_event=detector_initialized_event,
                               model=model)
    detector.StartProcess()

def StartEntranceCameras(broker_request_queue, detector_request_queue, license_detector_request_queue, entrance_cameras_initialized_event, shutdown_event, start_system_event):
    from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector

    wait_license_processing_event = Event()

    license_frames_request_queue = Queue()

    license_detector = EntranceLicenseDetector(license_frames_request_queue=license_frames_request_queue,
                                               broker_request_queue=broker_request_queue,
                                               detector_request_queue=detector_request_queue,
                                               license_detector_request_queue=license_detector_request_queue,
                                               top_camera=Constants.ENTRANCE_CAMERA_DETAILS[0],
                                               bottom_camera=Constants.ENTRANCE_CAMERA_DETAILS[1],
                                               entrance_cameras_initialized_event=entrance_cameras_initialized_event,
                                               wait_license_processing_event=wait_license_processing_event,
                                               shutdown_event=shutdown_event,
                                               start_system_event=start_system_event)
    license_detector.StartProcess()


    return wait_license_processing_event


