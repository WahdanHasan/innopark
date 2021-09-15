import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe, Queue, shared_memory
from classes.camera.CameraBuffered import Camera
from classes.enum_classes.Enums import EntrantSide
from classes.enum_classes.Enums import ObjectTrackerPipeStatus


class ParkingSpace:
    def __init__(self):
        self.id = -1
        self.bb = []
        self.is_occupied = False

    def UpdateId(self, new_id):
        self.id = new_id

    def UpdateBB(self, new_bb):
        # [TL, TR, BL, BR]
        self.bb = new_bb

    def UpdateStatus(self, is_occupied):
        self.is_occupied = is_occupied


class Tracker:

    def __init__(self, tracked_object_pool_queue, get_voyager_request_queue, send_voyager_request_queue, is_debug_mode):

        self.tracker_process = 0
        self.parking_spaces = []
        self.get_voyager_request_queue = get_voyager_request_queue
        self.send_voyager_request_queue = send_voyager_request_queue
        self.is_debug_mode = is_debug_mode
        self.tracked_object_pool_queue = tracked_object_pool_queue
        self.shared_memory_manager_frame = 0
        self.shared_memory_manager_mask = 0

    def Start(self, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        # ADD MASK INITIALIZATION HERE !!!!!!!!!
        self.tracker_process = Process(target=self.Update, args=(camera_rtsp, camera_id))
        self.tracker_process.start()

    def Stop(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    def Update(self, camera_rtsp, camera_id):

        subtraction_model = OD.SubtractionModel()
        tracked_object_pipes = []

        # Initialize camera
        cam = Camera(rtsp_link=camera_rtsp,
                     camera_id=camera_id)

        # Create shared memory space for frame and mask
        frame = cam.GetScaledNextFrame()
        subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)
        mask = subtraction_model.GetOutput()

        self.shared_memory_manager_frame = shared_memory.SharedMemory(create=True, size=frame.nbytes)
        self.shared_memory_manager_mask = shared_memory.SharedMemory(create=True, size=mask.nbytes)

        frame = np.ndarray(frame.shape, dtype=np.uint8, buffer=self.shared_memory_manager_frame.buf)
        mask = np.ndarray(mask.shape, dtype=np.uint8, buffer=self.shared_memory_manager_mask.buf)

        height, width = cam.default_resolution[1], cam.default_resolution[0]

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')

        # Debug variables
        start_time = time.time()
        seconds_before_display = 1
        counter = 0



        receive_pipe, send_pipe = Pipe()

        only_one = False
        # Main loop
        while True:
            # Write new frame into shared memory space
            frame[:] = cam.GetScaledNextFrame()[:]

            # Feed subtraction model
            subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)

            # Write new mask into shared memory space
            mask[:] = subtraction_model.GetOutput()[:]


            # Send signal to tracked object processes to read frame and mask
            for i in range(len(tracked_object_pipes)):
                tracked_object_pipes[i].send(ObjectTrackerPipeStatus.CanRead)


            # Detect new entrants
            return_status, detected_classes, detected_bbs = self.DetectNewEntrants(frame)

            if return_status and (not only_one):
                for i in range(len(detected_classes)):
                    entered_object_side = self.GetEntrantSide(detected_bbs[i], height, width)
                    self.get_voyager_request_queue.put((camera_id, entered_object_side, send_pipe))
                    entered_object_id = receive_pipe.recv()

                    self.tracked_object_pool_queue.put(send_pipe)
                    (temp_pipe) = receive_pipe.recv()
                    # TODO: Generate random id if the id is "none"
                    temp_pipe.send((detected_bbs[i], entered_object_id, self.shared_memory_manager_frame, frame.shape, self.shared_memory_manager_mask, mask.shape))
                    tracked_object_pipes.append(temp_pipe)
                    # break

                only_one = True


            # Information code
            if self.is_debug_mode:
                counter += 1
                if (time.time() - start_time) > seconds_before_display:
                    print("Camera " + str(camera_id) + " FPS: ", counter / (time.time() - start_time))
                    counter = 0
                    start_time = time.time()

                frame_processed = IU.DrawBoundingBoxes(image=frame,
                                                       bounding_boxes=detected_bbs,
                                                       thickness=2)

                cv2.imshow("Camera " + str(camera_id) + " Live Feed", frame)
                cv2.imshow("Camera " + str(camera_id) + " Processed Feed", frame_processed)
                cv2.imshow("Camera " + str(camera_id) + " Mask", self.base_mask)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def GetEntrantSide(self, bb, height, width):
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

        return sides_string[index_of_closest]

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        # masked_image = self.SubtractMaskFromImage(image, self.base_mask)
        masked_image = image.copy()
        return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=masked_image)


        return return_status, classes, bounding_boxes

    # def AddObjectToTracker(self, name, identifier, bounding_box):
    #     tracked_object = [name, identifier, bounding_box]
    #
    #     self.tracked_objects.append(TrackedObjectProcess(tracked_object=tracked_object))

    def RemoveObjectFromTracker(self, tracked_object):
        self.tracked_objects.remove(tracked_object)

    def AddParkingSpaceToTracker(self, parking_space_id, parking_space_bb):
        # Add parking space to tracker's list of parking space

        temp_space = ParkingSpace()
        temp_space.UpdateId(parking_space_id)
        temp_space.UpdateBB(parking_space_bb)

        self.parking_spaces.append(temp_space)

    def SubtractMaskFromImage(self, image, mask):
        # Takes an image and subtracts the provided mask from it
        # Returns the outcome of the subtraction

        masked_image = cv2.bitwise_and(image, image, mask=mask)


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

