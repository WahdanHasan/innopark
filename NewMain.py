from multiprocessing import Event, Queue
from classes.system_utilities.helper_utilities import Constants
# from classes.system_utilities.helper_utilities.Enums import TrackedObjectToBrokerInstruction
# from classes.system_utilities.helper_utilities.Enums import EntrantSide
import time
# import sys
from multiprocessing import Process

base_pool_size = 10

is_debug_mode = True

camera_ids_and_links = Constants.CAMERA_DETAILS


# This needs to be changed to GUI
def main():
    # print(sys.getsizeof(Constants.tracked_process_ids_example[0]))
    # return
    # Start helper processes
    new_tracked_object_event = Event()

    pool_initialized_event = Event()
    detector_initialized_event = Event()
    detector_request_queue = Queue()


    tracked_object_pool_request_queue = StartTrackedObjectPool(new_tracked_object_event=new_tracked_object_event,
                                                               initialized_event=pool_initialized_event)

    broker_request_queue = StartBroker()

    pool_initialized_event.wait()

    # broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, 1, 'J71612', EntrantSide.LEFT))

    # temp_event = StartEntranceCameras(broker_request_queue)
    #
    # temp_event.wait()

    trackers = StartTrackers(broker_request_queue=broker_request_queue,
                             tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                             detector_request_queue=detector_request_queue,
                             detector_initialized_event=detector_initialized_event)




    time.sleep(5)
    # Start main components
    StartDetectorProcess(new_tracked_object_event=new_tracked_object_event,
                         detector_request_queue=detector_request_queue,
                         detector_initialized_event=detector_initialized_event)
    # StartParkingTariffManager(new_tracked_object_event=new_tracked_object_event)

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

def StartTrackedObjectPool(new_tracked_object_event, initialized_event):
    from classes.system_utilities.tracking_utilities import TrackedObject

    tracked_object_pool_request_queue = Queue()

    tracked_object_pool = TrackedObject.TrackedObjectPoolManager(tracked_object_pool_request_queue=tracked_object_pool_request_queue,
                                                                 new_tracked_object_process_event=new_tracked_object_event,
                                                                 initialized_event=initialized_event,
                                                                 pool_size=base_pool_size)
    tracked_object_pool.StartProcess()

    return tracked_object_pool_request_queue

def StartTrackers(broker_request_queue, tracked_object_pool_request_queue, detector_request_queue, detector_initialized_event):
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

def StartDetectorProcess(new_tracked_object_event, detector_request_queue, detector_initialized_event):
    from classes.system_utilities.image_utilities.ObjectDetectionProcess import DetectorProcess
    time.sleep(3)
    detector = DetectorProcess(amount_of_trackers=len(camera_ids_and_links),
                               base_pool_size=base_pool_size,
                               new_object_in_pool_event=new_tracked_object_event,
                               detector_request_queue=detector_request_queue,
                               detector_initialized_event=detector_initialized_event)
    detector.StartProcess()


def StartEntranceCameras(broker_request_queue):

    wait_license_processing_event = Event()

    license_frames_request_queue = Queue()

    license_detector_process = StartEntranceTopCam(license_frames_request_queue, wait_license_processing_event)
    license_processing_process = StartProcessingLicenseFrames(license_frames_request_queue=license_frames_request_queue,
                                                              broker_request_queue=broker_request_queue,
                                                              wait_license_processing_event=wait_license_processing_event)

    return wait_license_processing_event

def StartEntranceTopCam(license_frames_request_queue, wait_license_processing_event):
    from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector

    license_detector = EntranceLicenseDetector(license_frames_request_queue)

    license_detector.InitializeCameras(Constants.ENTRANCE_CAMERA_DETAILS[1], Constants.ENTRANCE_CAMERA_DETAILS[0])

    license_detector_process = Process(target=license_detector.Start, args=(wait_license_processing_event,))
    license_detector_process.start()

    return license_detector_process

def StartProcessingLicenseFrames(license_frames_request_queue, broker_request_queue, wait_license_processing_event):
    from classes.system_utilities.tracking_utilities.ProcessLicenseFrames import ProcessLicenseFrames

    license_processing_frames = ProcessLicenseFrames(broker_request_queue, license_frames_request_queue)
    license_processing_process = Process(target=license_processing_frames.Start, args=(wait_license_processing_event,))
    license_processing_process.start()

    return license_processing_process

if __name__ == "__main__":
    main()
