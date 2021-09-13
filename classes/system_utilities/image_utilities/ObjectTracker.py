import classes.system_utilities.image_utilities.ObjectDetection as OD
import classes.system_utilities.image_utilities.ImageUtilities as IU
import cv2
import time
import numpy as np
from multiprocessing import Process, Pipe, Queue
from classes.camera.CameraBuffered import Camera
from classes.enum_classes.Enums import EntrantSide


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


class TrackedObjectPoolManager:
    # Manages tracked object processes in a pool.

    def __init__(self):
        # Creates a pool of tracked object processes, their active status, and a pipe to communicate with each

        self.should_continue_accepting_requests = True

        self.request_queue = 0

        self.pool_size = 0

        self.tracked_object_process_pool = []
        self.tracked_object_process_pipes = []
        self.tracked_object_process_active_statuses = []

    def Initialize(self, pool_size=1):

        self.request_queue = Queue()

        self.pool_size = pool_size

        return self.request_queue

    def Start(self):
        for i in range(self.pool_size):
            temp_pipe, temp_tracked_object_process = self.CreateTrackedObjectProcess()
            self.tracked_object_process_pool.append(temp_tracked_object_process)
            self.tracked_object_process_pipes.append(temp_pipe)
            self.tracked_object_process_active_statuses.append(False)

        print("Started pool manager")
        while self.should_continue_accepting_requests:
            (sender_pipe) = self.request_queue.get()

            temp_pipe, _ = self.GetTrackedObjectProcess()

            sender_pipe.send(temp_pipe)

        print("Stopped pool manager")

    def CreateTrackedObjectProcess(self):
        # Creates a tracked object process and opens a pipe to it
        # Returns the process and the other end of the pipe

        pipe1, pipe2 = Pipe()
        temp_tracked_object = TrackedObjectProcess()
        tracked_object_process = Process(target=temp_tracked_object.AwaitInstructions, args=(pipe2,))
        tracked_object_process.start()

        return pipe1, tracked_object_process

    def GetTrackedObjectProcess(self):
        # Returns the next free process from the pool
        # If all processes are active, creates a new process, adds it to the pool, and then returns it

        for i in range(self.pool_size):
            if not self.tracked_object_process_active_statuses[i]:
                print("Returning process " + str(i))
                return self.tracked_object_process_pipes[i], self.tracked_object_process_pool[i]

        temp_pipe, temp_tracked_object_process = self.CreateTrackedObjectProcess()

        self.tracked_object_process_pool.append(temp_tracked_object_process)
        self.tracked_object_process_pipes.append(temp_pipe)
        self.tracked_object_process_active_statuses.append(True)

        return temp_pipe, temp_tracked_object_process

    def DestroyPool(self):
        # Destroys all processes stored in the pool

        for i in range(self.pool_size):
            self.tracked_object_process_pool[i].terminate()


class TrackedObjectProcess:
    # Tracks objects assigned to it

    def __init__(self):
        self.object_id = -1
        self.bb = 0
        self.pipe = 0
        self.should_keep_tracking = False
        self.old_gray_cropped = 0
        self.old_points_cropped = 0
        self.new_gray_cropped = 0
        self.new_points_cropped = 0
        self.lk_params = dict(winSize=(100, 100),
                              maxLevel=100,
                              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    def AwaitInstructions(self, pipe):
        # The tracked object process sits idle until an object tracker sends a new task to it

        if self.pipe == 0:
            self.pipe = pipe

        (new_bb, new_object_id, base_frame) = pipe.recv()

        self.Initialize(new_object_id, new_bb, base_frame)
        self.StartTracking(self.pipe)

    def Initialize(self, object_id, bb, frame):
        # Sets the parameters for the tracked object

        self.object_id = object_id
        self.bb = bb
        self.should_keep_tracking = True

        # Optical flow LK params

        temp_cropped = IU.CropImage(frame, self.bb)
        self.old_gray_cropped = cv2.cvtColor(temp_cropped, cv2.COLOR_BGR2GRAY)
        self.old_points_cropped = cv2.goodFeaturesToTrack(self.old_gray_cropped, 100, 0.5, 10)

    def StartTracking(self, pipe):
        # Continues tracking the object until the object tracker sends -1 through the pipe.
        # In which case the process then returns and awaits for the next set of instructions

        while self.should_keep_tracking:

            frame = pipe.recv()

            # if isinstance(instructions, int):
            #     self.should_keep_tracking = False
            #     continue
            # else:
            #     frame = instructions

            temp_cropped = IU.CropImage(frame, self.bb)
            self.new_gray_cropped = cv2.cvtColor(temp_cropped, cv2.COLOR_BGR2GRAY)

            new_pts, status, err = cv2.calcOpticalFlowPyrLK(self.old_gray_cropped,
                                                            self.new_gray_cropped,
                                                            self.old_points_cropped,
                                                            None,
                                                            winSize=(100, 100),
                                                            maxLevel=10,
                                                            criteria=(
                                                            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

            # new_pts, status, err = cv2.calcOpticalFlowPyrLK(self.old_gray_cropped,
            #                                                 self.new_gray_cropped,
            #                                                 self.old_points_cropped,
            #                                                 None, maxLevel=10,
            #                                                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
            #                                                           15, 0.08))

            avg_x = 0
            avg_y = 0
            for i in range(len(new_pts)):
                x, y = new_pts[i].ravel()
                x_o, y_o = self.old_points_cropped[i].ravel()
                t_x = x + self.bb[0][0]
                t_y = y + self.bb[0][1]
                cv2.circle(frame, (int(t_x), int(t_y)), 3, (0, 255, 0), -1)
                avg_x += x - x_o
                avg_y += y - y_o

            avg_x = int(avg_x/len(new_pts))
            avg_y = int(avg_y/len(new_pts))
            self.bb = [[self.bb[0][0] + avg_x, self.bb[0][1] + avg_y], [self.bb[1][0] + avg_x, self.bb[1][1] + avg_y]]
            frame = IU.DrawBoundingBoxes(frame, [self.bb])
            cv2.imshow("me smoll process frame ", frame)
            cv2.imshow("me smoll process frame cropped", temp_cropped)
            # cv2.waitKey(0)
            # cv2.waitKey(2000)
            # OD.CreateInvertedMask(frame, self.bb)
            # print(frame)
            self.old_gray_cropped = self.new_gray_cropped
            self.old_points_cropped = new_pts

            # pipe.send(self.bb)
            # cv2.imshow("frame", frame)
            # cv2.imshow("mask", mask)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

        print("Stopped running")

        self.AwaitInstructions(pipe=None)







class Tracker:

    def __init__(self, tracked_object_pool_queue, get_voyager_request_queue, send_voyager_request_queue, is_debug_mode):

        self.tracker_process = 0
        self.parking_spaces = []
        self.get_voyager_request_queue = get_voyager_request_queue
        self.send_voyager_request_queue = send_voyager_request_queue
        self.is_debug_mode = is_debug_mode
        self.tracked_object_pool_queue = tracked_object_pool_queue

    def Start(self, camera_rtsp, camera_id):
        # All parking spots should be instantiated prior to calling this function

        # ADD MASK INITIALIZATION HERE !!!!!!!!!
        self.tracker_process = Process(target=self.Update, args=(camera_rtsp, camera_id))
        self.tracker_process.start()

    def Stop(self):
        # Sets the tracker continue to false then waits for it to stop
        self.tracker_process.terminate()

    def Update(self, camera_rtsp, camera_id):

        tracked_object_pipes = []

        # Initialize camera
        cam = Camera(rtsp_link=camera_rtsp,
                     camera_id=camera_id)


        height, width = cam.default_resolution[1], cam.default_resolution[0]

        self.base_mask = np.zeros((height, width, 3), dtype='uint8')

        # Debug variables
        start_time = time.time()
        seconds_before_display = 1
        counter = 0

        subtraction_model = OD.SubtractionModel()

        receive_pipe, send_pipe = Pipe()

        only_one = False
        # Main loop
        while True:

            frame = cam.GetScaledNextFrame()

            subtraction_model.FeedSubtractionModel(image=frame, learningRate=0.0001)

            # Detect new entrants
            # return_status, detected_classes, detected_bbs = self.DetectNewEntrants(image=frame)

            return_status, detected_classes, detected_bbs = self.DetectNewEntrants(frame)

            if return_status and (not only_one):
                for i in range(len(detected_classes)):
                    entered_object_side = self.GetEntrantSide(detected_bbs[i], height, width)
                    self.get_voyager_request_queue.put((camera_id, entered_object_side, send_pipe))
                    entered_object_id = receive_pipe.recv()

                    self.tracked_object_pool_queue.put(send_pipe)
                    (temp_pipe) = receive_pipe.recv()
                    # TODO: Generate random id if the id is "none"
                    temp_pipe.send((detected_bbs[i], entered_object_id, frame))
                    tracked_object_pipes.append(temp_pipe)
                    break

                only_one = True


            for i in range(len(tracked_object_pipes)):
                tracked_object_pipes[i].send(frame)

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

    def UpdateTracker(self, image):  # Work off a camera id or something, don't leave the detection for the user.
        x=10

    def DetectNewEntrants(self, image):
        # Returns new entrants within an image by running YOLO on the image after the application of the base mask
        # This results in only untracked objects being detected

        # masked_image = self.SubtractMaskFromImage(image, self.base_mask)
        masked_image = image.copy()
        return_status, classes, bounding_boxes, _ = OD.DetectObjectsInImage(image=masked_image)


        return return_status, classes, bounding_boxes

    def AddObjectToTracker(self, name, identifier, bounding_box):
        tracked_object = [name, identifier, bounding_box]

        self.tracked_objects.append(TrackedObjectProcess(tracked_object=tracked_object))

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

