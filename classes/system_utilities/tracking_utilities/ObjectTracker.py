from classes.camera.CameraBuffered import Camera
from classes.super_classes.PtmListener import PtmListener
from classes.system_utilities.tracking_utilities.SubtractionModel import SubtractionModel
from classes.system_utilities.helper_utilities.Enums import EntrantSide, TrackerToTrackedObjectInstruction, TrackedObjectStatus, TrackedObjectToBrokerInstruction, ObjectToPoolManagerInstruction
from classes.system_utilities.helper_utilities import Constants
from classes.super_classes.ShutDownEventListener import ShutDownEventListener
import classes.system_utilities.image_utilities.ImageUtilities as IU

import math
import sys
import cv2
import time
import copy
import numpy as np
from multiprocessing import Process, Pipe, shared_memory


class Tracker(ShutDownEventListener):

    def __init__(self, tracked_object_pool_request_queue, broker_request_queue, detector_request_queue, tracker_initialized_event, detector_initialized_event, shutdown_event, start_system_event, ptm_initialized_event, seconds_between_detections):
        ShutDownEventListener.__init__(self, shutdown_event)
        self.tracker_process = 0
        self.parking_spaces = []
        self.broker_request_queue = broker_request_queue
        self.tracked_object_pool_request_queue = tracked_object_pool_request_queue
        self.ptm_initialized_event = ptm_initialized_event
        self.detector_request_queue = detector_request_queue
        self.seconds_between_detections = seconds_between_detections
        self.detector_initialized_event = detector_initialized_event
        self.tracker_initialized_event = tracker_initialized_event
        self.shutdown_event = shutdown_event
        self.start_system_event = start_system_event
        self.shared_memory_manager_id = 0
        self.shared_memory_manager_frame = 0
        self.shared_memory_manager_mask = 0
        self.camera_rtsp = 0
        self.camera_id = 0
        self.should_keep_tracking = True
        self.tracker_id = 0

        self.receive_pipe = 0
        self.send_pipe = 0

    def StartProcess(self, tracker_id, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        print("[ObjectTracker]:[Camera " + str(camera_id) + "] Starting Tracker.", file=sys.stderr)
        self.Initialize(tracker_id, camera_rtsp, camera_id)
        self.tracker_process = Process(target=self.StartTracking)
        self.tracker_process.start()

    def StopProcess(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    def Initialize(self, tracker_id, camera_rtsp, camera_id):

        self.tracker_id = tracker_id

        self.camera_rtsp = camera_rtsp
        self.camera_id = camera_id

    def StartTracking(self):

        ShutDownEventListener.initialize(self)

        # Variable declarations
        subtraction_model = SubtractionModel()
        tracked_object_pool_indexes = []
        tracked_object_ids = []
        tracked_object_pipes = []
        tracked_object_bbs_shared_memory_managers = []
        tracked_object_bbs_shared_memory = []
        tracked_object_old_bbs = []
        tracked_object_movement_status = []
        tracked_objects_without_ids = []
        tracked_objects_without_ids_bbs = []
        self.receive_pipe, self.send_pipe = Pipe()
        time_at_detection = time.time()

        # Initialize camera
        cam = Camera(rtsp_link=self.camera_rtsp,
                     camera_id=self.camera_id)

        # Create shared memory space for frame and mask
        frame = cam.GetScaledNextFrame()
        subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)
        mask = subtraction_model.GetOutput()

        self.shared_memory_manager_frame = shared_memory.SharedMemory(create=True,
                                                                      name=Constants.frame_shared_memory_prefix + str(self.camera_id),
                                                                      size=frame.nbytes)

        self.shared_memory_manager_mask = shared_memory.SharedMemory(create=True,
                                                                     name=Constants.object_tracker_mask_shared_memory_prefix + str(self.camera_id),
                                                                     size=mask.nbytes)

        frame = np.ndarray(frame.shape, dtype=np.uint8, buffer=self.shared_memory_manager_frame.buf)
        mask = np.ndarray(mask.shape, dtype=np.uint8, buffer=self.shared_memory_manager_mask.buf)

        height, width = cam.default_resolution[1], cam.default_resolution[0]

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')

        # Wait for events
        self.tracker_initialized_event.set()
        self.ptm_initialized_event.wait()

        ptm_listener = PtmListener()
        ptm_listener.initialize()

        self.detector_initialized_event.wait()
        self.start_system_event.wait()



        # Debug variables
        start_time = time.time()
        seconds_before_display = 1
        counter = 0

        temp_loop_counter = 0
        # Main loop
        while self.should_keep_tracking:
            if not self.shutdown_should_keep_listening:
                print("[ObjectTracker] Camera " + str(self.camera_id) + "  Cleaning up.", file=sys.stderr)
                self.cleanUp()
                return

            temp_should_keep_looping = True

            # Write new frame into shared memory space
            frame[:] = cam.GetScaledNextFrame()[:]

            # Feed subtraction model
            subtraction_model.FeedSubtractionModel(image=frame, learningRate=Constants.subtraction_model_learning_rate)

            # Write new mask into shared memory space
            mask[:] = subtraction_model.GetOutput()[:]

            # Find fastest moving object and give it priority for movement
            fastest_object_dist = 0.00
            fastest_object_idx = -1
            for i in range(len(tracked_object_old_bbs)):
                temp_old_bb_centroid = IU.GetBoundingBoxCenterFloat(tracked_object_old_bbs[i])
                temp_new_bb_centroid = IU.GetBoundingBoxCenterFloat(tracked_object_bbs_shared_memory[i])

                old_new_dist = math.dist(temp_old_bb_centroid, temp_new_bb_centroid)
                if self.camera_id == 3:
                    print(old_new_dist)
                if old_new_dist > fastest_object_dist:
                    fastest_object_dist = old_new_dist
                    fastest_object_idx = i

            if fastest_object_idx != -1:
                for i in range(len(tracked_object_old_bbs)):
                    if i == fastest_object_idx:
                        continue
                    if IU.CheckIfPolygonIntersects(bounding_box_a=IU.GetFullBoundingBox(tracked_object_bbs_shared_memory[fastest_object_idx]),
                                                   bounding_box_b=IU.GetFullBoundingBox(tracked_object_bbs_shared_memory[i])):
                        # print("INTERSECTING")
                        tracked_object_movement_status[i] = TrackedObjectStatus.STATIONARY
                    # else:
                        # print("NOT INTERSECTING")
                        # print(type(tracked_object_movement_status[i]))

            # if self.camera_id == 2:
            #     print(fastest_object_dist)

            # Store new bb positions
            tracked_object_old_bbs = copy.deepcopy(tracked_object_bbs_shared_memory)

            # Send signal to tracked object processes to read frame and mask along with an instruction
            # TODO: Validate for noise on the last and new bounding box if object doesnt have an id. The object can be going the wrong direction as a result.
            for i in range(len(tracked_object_pipes)):
                primary_instruction_to_send = 0
                if tracked_object_movement_status[i] == TrackedObjectStatus.STATIONARY:
                    primary_instruction_to_send = TrackerToTrackedObjectInstruction.OBJECT_STATIONARY
                elif tracked_object_movement_status[i] == TrackedObjectStatus.MOVING:
                    primary_instruction_to_send = TrackerToTrackedObjectInstruction.OBJECT_MOVING


                try:
                    temp_idx = tracked_objects_without_ids.index(i)
                    object_doesnt_have_id = True

                except ValueError:
                    object_doesnt_have_id = False

                # Get the side from which the object appeared in the camera, then request the broker for information on the entrant
                if object_doesnt_have_id:

                    temp_bb_a = tracked_object_bbs_shared_memory[i].tolist()
                    if temp_bb_a == IU.IntBBToFloatBB(Constants.bb_example):
                        tracked_object_pipes[i].send(primary_instruction_to_send)

                    temp_entrant_side = self.GetEntrantSide(old_bb=tracked_objects_without_ids_bbs[temp_idx],
                                                            new_bb=temp_bb_a)

                    self.broker_request_queue.put((TrackedObjectToBrokerInstruction.GET_VOYAGER, self.camera_id, temp_entrant_side, self.send_pipe))
                    temp_entrant_id = self.receive_pipe.recv()
                    tracked_object_pipes[i].send([TrackerToTrackedObjectInstruction.STORE_NEW_ID, primary_instruction_to_send, temp_entrant_id])
                    tracked_object_ids[i] = temp_entrant_id
                    tracked_objects_without_ids.pop(temp_idx)
                    tracked_objects_without_ids_bbs.pop(temp_idx)
                else:
                    tracked_object_pipes[i].send(primary_instruction_to_send)

            # Reset movement statuses
            for i in range(len(tracked_object_pipes)):
                tracked_object_movement_status[i] = TrackedObjectStatus.MOVING

            # Check if tracked objects are still within the image
            while temp_should_keep_looping:

                if temp_loop_counter >= len(tracked_object_pipes):
                    temp_should_keep_looping = False
                    temp_loop_counter = 0
                    continue

                temp_img_bb = [[0, 0], [int(width), int(height)]]
                temp_bb_b = tracked_object_bbs_shared_memory[temp_loop_counter].tolist()[:]

                if temp_bb_b == IU.IntBBToFloatBB(Constants.bb_example):
                    continue

                a_contains_b = IU.CheckIfPolygonFullyContainsPolygonTF(big_box=temp_img_bb, small_box=temp_bb_b)

                if not a_contains_b:
                    try:
                        temp_mask = IU.CropImage(img=mask, bounding_set=temp_bb_b)

                        white_points_percentage = (np.sum(temp_mask == 255) / (temp_mask.shape[1] * temp_mask.shape[0])) * 100
                    except:
                        white_points_percentage = 100.0

                    if white_points_percentage < 30.0:
                        temp_exit_side = self.GetExitSide(temp_bb_b, height, width)
                        self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER, self.camera_id, tracked_object_ids[temp_loop_counter], temp_exit_side))
                        print("[ObjectTracker]:[Camera " + str(self.camera_id) + "] Object exited from " + temp_exit_side.value, file=sys.stderr)
                        self.tracked_object_pool_request_queue.put((ObjectToPoolManagerInstruction.RETURN_PROCESS, tracked_object_pool_indexes[temp_loop_counter]))
                        tracked_object_ids.pop(temp_loop_counter)
                        tracked_object_bbs_shared_memory.pop(temp_loop_counter)
                        tracked_object_bbs_shared_memory_managers.pop(temp_loop_counter)
                        tracked_object_movement_status.pop(temp_loop_counter)
                        tracked_object_pipes[temp_loop_counter].send(TrackerToTrackedObjectInstruction.STOP_TRACKING)
                        tracked_object_pipes.pop(temp_loop_counter)
                        tracked_object_old_bbs.pop(temp_loop_counter)
                        tracked_object_pool_indexes.pop(temp_loop_counter)

                temp_loop_counter += 1

            # Detect new entrants
            if (time.time() - time_at_detection) > self.seconds_between_detections:
                self.DetectNewEntrants(frame, mask, self.send_pipe, self.receive_pipe, tracked_object_pool_indexes, ptm_listener, tracked_object_pipes, tracked_object_bbs_shared_memory_managers, tracked_object_bbs_shared_memory, tracked_object_movement_status, tracked_object_ids, tracked_objects_without_ids, tracked_objects_without_ids_bbs)
                time_at_detection = time.time()

            # Wait for all tracked objects to finish updating their boxes
            for i in range(len(tracked_object_pipes)):
                tracked_object_pipes[i].recv()

            temp_frame = IU.DrawBoundingBoxes(image=frame, bounding_boxes=tracked_object_bbs_shared_memory)

            cv2.imshow(str(self.camera_id), temp_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

            # Print fps rate of tracker
            counter += 1
            if (time.time() - start_time) > seconds_before_display:
                # print("[ObjectTracker]:[Camera " + str(self.camera_id) + "] FPS: ", int(counter / (time.time() - start_time)))
                counter = 0
                start_time = time.time()

    def StopTracking(self):
        self.should_keep_tracking = False

    def GetExitSide(self, bb, height, width):
        # Takes the bounding box of the entrant and the height and width of the image
        # Calculates the side where the entrant came from depending on the distance of the bb center from the center
        # of each side
        # Returns the side as a string

        bb_center = np.array(IU.GetBoundingBoxCenter(bb))

        left_side_point = np.array((0, int(height/2)))
        right_side_point = np.array((width, int(height/2)))
        top_side_point = np.array((int(width/2), 0))
        bottom_side_point = np.array((int(width/2), height))

        # UP DOWN LEFT RIGHT
        sides = (top_side_point, bottom_side_point, left_side_point, right_side_point)
        sides_string = (EntrantSide.TOP, EntrantSide.BOTTOM, EntrantSide.LEFT, EntrantSide.RIGHT)

        side_distances = []

        for i in range(len(sides)):
            side_distances.append(np.linalg.norm(abs(bb_center - sides[i])))

        index_of_closest = 0

        for i in range(len(sides)):
            if side_distances[i] < side_distances[index_of_closest]:
                index_of_closest = i

        print("[Camera " + str(self.camera_id) + "] Detected entrant from the " + sides_string[index_of_closest].value + " side.")
        return sides_string[index_of_closest]

    def GetEntrantSide(self, old_bb, new_bb):

        # Get BB centers
        old_bb_center = IU.GetBoundingBoxCenter(bounding_box=old_bb)
        new_bb_center = IU.GetBoundingBoxCenter(bounding_box=new_bb)

        # Get object distance traveled horizontally
        dist_horizontal = int(old_bb_center[0] - new_bb_center[0])
        # Get object distance traveled vertically
        dist_vertical = int(old_bb_center[1] - new_bb_center[1])

        # Get greater distance travel side

        # TODO: Get this working
        # if abs(dist_horizontal) > abs(dist_vertical):
        #     if dist_horizontal > 0:
        #         return EntrantSide.LEFT
        #     else:
        #         return EntrantSide.RIGHT
        # else:
        #     if dist_vertical > 0:
        #         return EntrantSide.TOP
        #     else:
        #         return EntrantSide.BOTTOM

        if dist_horizontal > 0:
            return EntrantSide.LEFT
        else:
            return EntrantSide.RIGHT

    def DetectNewEntrants(self, frame, mask, send_pipe, receive_pipe, tracked_object_pool_indexes, ptm_listener,
                          tracked_object_pipes, tracked_object_bbs_shared_memory_managers,
                          tracked_object_bbs_shared_memory, tracked_object_movement_status,
                          tracked_object_ids, tracked_objects_without_indexes, tracked_objects_without_ids_bbs):

        self.detector_request_queue.put((self.camera_id, send_pipe))

        return_status, _, detected_bbs, _ = receive_pipe.recv()

        if return_status:
            # Compare old boxes with new. Idea is that if new and old are overlapping by like 95%, its the same box and the object is parked, so just remove it
            temp_percentage_lower = 0
            for i in range(len(tracked_object_bbs_shared_memory)):
                temp_tracked_bb_area = (tracked_object_bbs_shared_memory[i][1][0] - tracked_object_bbs_shared_memory[i][0][0]) * (tracked_object_bbs_shared_memory[i][1][1] - tracked_object_bbs_shared_memory[i][0][1])
                for j in range(len(detected_bbs)):
                    if not IU.CheckIfPolygonsAreIntersectingTF(IU.GetFullBoundingBox(tracked_object_bbs_shared_memory[i]), IU.GetFullBoundingBox(detected_bbs[j])):
                        continue

                    temp_new_bb_area = (detected_bbs[j][1][0] - detected_bbs[j][0][0]) * (detected_bbs[j][1][1] - detected_bbs[j][0][1])

                    if temp_tracked_bb_area > temp_new_bb_area:
                        temp_percentage_lower = temp_new_bb_area/temp_tracked_bb_area
                    else:
                        temp_percentage_lower = temp_tracked_bb_area/temp_new_bb_area

                    if float(100 - temp_percentage_lower) <= Constants.ot_bb_area_difference_percentage_threshold:
                        detected_bbs.pop(j)
                        break

            if len(detected_bbs) == 0:
                return

            # Figure out the closest new bb to the old bbs to update their pos. Left over bbs are new objects
            bbs_to_be_updated = []
            for i in range(len(tracked_object_bbs_shared_memory)):
                reject_detected_bb = False

                if tracked_object_movement_status[i] == TrackedObjectStatus.STATIONARY:
                    reject_detected_bb = True

                temp_bb_centroid = IU.GetBoundingBoxCenter(tracked_object_bbs_shared_memory[i])
                temp_closest_bb_dist = Constants.INT_MAX
                temp_closest_bb_idx = -1

                for j in range(len(detected_bbs)):
                    temp_bb_new_centroid = IU.GetBoundingBoxCenter(detected_bbs[j])
                    temp_dy = (temp_bb_centroid[0] - temp_bb_new_centroid[0]) ** 2
                    temp_dx = (temp_bb_centroid[1] - temp_bb_new_centroid[1]) ** 2
                    temp_dist = math.sqrt(temp_dx + temp_dy)

                    if temp_dist < temp_closest_bb_dist:
                        temp_closest_bb_idx = j
                        temp_closest_bb_dist = temp_dist

                        if not reject_detected_bb:
                            temp_closest_bb = detected_bbs[j][:]
                            bbs_to_be_updated.append([tracked_object_pipes[i], temp_closest_bb])

                if temp_closest_bb_idx != -1 or reject_detected_bb:
                    detected_bbs.pop(temp_closest_bb_idx)

            for i in range(len(bbs_to_be_updated)):
                bbs_to_be_updated[i][0].send([TrackerToTrackedObjectInstruction.STORE_NEW_BB, bbs_to_be_updated[i][1]])

            if len(detected_bbs) == 0:
                return

            for i in range(len(detected_bbs)):
                # Request for a tracked object to represent the new entrant from the tracked object pool
                self.tracked_object_pool_request_queue.put((ObjectToPoolManagerInstruction.GET_PROCESS, self.send_pipe))

                # Receive the tracked object's pipe and its bounding box shared memory manager from the tracked object pool
                (temp_pipe, temp_shared_memory_bb_manager, temp_process_pool_idx) = self.receive_pipe.recv()

                # Create an array reference to the tracked object's shared memory bounding box
                temp_shared_memory_array = np.ndarray(np.asarray(Constants.bb_example, dtype=np.float32).shape,
                                                      dtype=np.float32, buffer=temp_shared_memory_bb_manager.buf)

                # Send the tracked object instructions on the object it is supposed to represent
                temp_pipe.send((self.camera_id, self.tracker_id, detected_bbs[i], self.shared_memory_manager_frame,
                                frame.shape, self.shared_memory_manager_mask, mask.shape))

                # Add the tracked object pipe and shared memory reference to local arrays
                tracked_object_pool_indexes.append(temp_process_pool_idx)
                tracked_object_pipes.append(temp_pipe)
                tracked_object_bbs_shared_memory_managers.append(temp_shared_memory_bb_manager)
                tracked_object_bbs_shared_memory.append(temp_shared_memory_array)
                tracked_object_movement_status.append(TrackedObjectStatus.MOVING)
                tracked_object_ids.append(None)

                tracked_objects_without_indexes.append(len(tracked_object_pipes) - 1)
                tracked_objects_without_ids_bbs.append(detected_bbs[i])

    def RemoveObjectFromTracker(self, tracked_object):
        self.tracked_objects.remove(tracked_object)

    def SubtractMaskFromImage(self, image, mask):
        # Takes an image and subtracts the provided mask from it
        # Returns the outcome of the subtraction

        # masked_image = cv2.bitwise_and(image, image, mask=mask)
        masked_image = cv2.subtract(image, mask)

        return masked_image

    def AddToMask(self, tracked_object):
        # Takes a tracked object and adds its mask to the base mask
        # It should be noted that moving objects should continually remove their old mask and add their own

        if len(tracked_object.bounding_box) == 4:
            bounding_box = IU.GetPartialBoundingBox(bounding_box=tracked_object.bounding_box)
        else:
            bounding_box = tracked_object.bounding_box

        bounding_box_center = IU.GetBoundingBoxCenter(bounding_box=bounding_box)

        self.base_mask = IU.PlaceImage(base_image=self.base_mask,
                                       img_to_place=tracked_object.mask,
                                       center_x=bounding_box_center[0],
                                       center_y=bounding_box_center[1])

    def RemoveFromMask(self, tracked_object): # Change this in the future to not subtract adjacent masks
        # Takes a tracked object and removes its mask from the base mask
        # It should be noted that moving objects should continually remove their old mask and add their own

        if len(tracked_object.bounding_box) == 4:
            bounding_box = IU.GetPartialBoundingBox(bounding_box=tracked_object.bounding_box)
        else:
            bounding_box = tracked_object.bounding_box

        bounding_box_center = IU.GetBoundingBoxCenter(bounding_box=bounding_box)

        tracked_object_mask_height, tracked_object_mask_width, _ = tracked_object.mask.shape

        tracked_object.mask = np.zeros((tracked_object_mask_height, tracked_object_mask_width, 3), dtype='uint8')

        self.base_mask = IU.PlaceImage(base_image=self.base_mask,
                                       img_to_place=tracked_object.mask,
                                       center_x=bounding_box_center[0],
                                       center_y=bounding_box_center[1])

    def cleanUp(self):
        self.receive_pipe.close()
        self.send_pipe.close()
        self.shared_memory_manager_frame.unlink()
        self.shared_memory_manager_mask.unlink()


