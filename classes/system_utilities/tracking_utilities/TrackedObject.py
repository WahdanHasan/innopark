import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.enum_classes.Enums import ObjectTrackerPipeStatus

import sys
import cv2
import copy
import numpy as np
from multiprocessing import Process, Pipe, Queue

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

        print("[TrackedObjectPoolManager] Starting pool manager.", file=sys.stderr)
        while self.should_continue_accepting_requests:
            (sender_pipe) = self.request_queue.get()

            temp_pipe, _ = self.GetTrackedObjectProcess()

            sender_pipe.send(temp_pipe)

        print("[TrackedObjectPoolManager] Stopped pool manager", file=sys.stderr)

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
                self.tracked_object_process_active_statuses[i] = True
                return self.tracked_object_process_pipes[i], self.tracked_object_process_pool[i]

        temp_pipe, temp_tracked_object_process = self.CreateTrackedObjectProcess()

        self.tracked_object_process_pool.append(temp_tracked_object_process)
        self.tracked_object_process_pipes.append(temp_pipe)
        self.tracked_object_process_active_statuses.append(True)

        return temp_pipe, temp_tracked_object_process

    # def ReturnTrackedObject(self, tracked_object_):

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
        self.old_gray = 0
        self.old_gray_cropped = 0
        self.old_points_cropped = 0
        self.new_gray = 0
        self.new_gray_cropped = 0
        self.new_points_cropped = 0
        self.frame_shared_memory = 0
        self.mask_shared_memory = 0
        self.frame_shape = 0
        self.mask_shape = 0
        self.frame = 0
        self.mask = 0
        self.lk_params = dict(
                              maxLevel=50,
                              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    def AwaitInstructions(self, pipe):
        # The tracked object process sits idle until an object tracker sends a new task to it

        if self.pipe == 0:
            self.pipe = pipe

        (new_bb, new_object_id, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape) = pipe.recv()



        self.Initialize(new_object_id, new_bb, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape)
        self.StartTracking(self.pipe)

    def Initialize(self, object_id, bb, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape):
        # Sets the parameters for the tracked object

        self.object_id = object_id
        self.bb = bb
        self.should_keep_tracking = True

        self.frame_shared_memory = shared_memory_manager_frame
        self.frame_shape = base_frame_shape
        self.mask_shared_memory = shared_memory_manager_mask
        self.mask_shape = base_mask_shape

        self.frame = np.ndarray(self.frame_shape, dtype=np.uint8, buffer=self.frame_shared_memory.buf)
        self.mask = np.ndarray(self.mask_shape, dtype=np.uint8, buffer=self.mask_shared_memory.buf)

        # Optical flow LK params

        temp_cropped = IU.CropImage(self.frame, self.bb)
        self.old_gray_cropped = cv2.cvtColor(temp_cropped, cv2.COLOR_BGR2GRAY)
        self.old_gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        self.old_points_cropped = cv2.goodFeaturesToTrack(self.old_gray_cropped, 100, 0.4, 10)

        for i in range(len(self.old_points_cropped)):
            self.old_points_cropped[i][0][0] = self.old_points_cropped[i][0][0] + self.bb[0][0]
            self.old_points_cropped[i][0][1] = self.old_points_cropped[i][0][1] + self.bb[0][1]

    def StartTracking(self, pipe):
        # Continues tracking the object until the object tracker sends -1 through the pipe.
        # In which case the process then returns and awaits for the next set of instructions

        while self.should_keep_tracking:

            instructions = pipe.recv()

            if not isinstance(instructions, ObjectTrackerPipeStatus):
                self.should_keep_tracking = False
                continue
            elif instructions.value != ObjectTrackerPipeStatus.CanRead.value:
                continue

            temp_frame = np.ndarray(self.frame_shape, dtype=np.uint8, buffer=self.frame_shared_memory.buf)
            temp_mask = np.ndarray(self.mask_shape, dtype=np.uint8, buffer=self.mask_shared_memory.buf)

            self.frame = temp_frame.copy()
            self.mask = temp_mask.copy()

            frame = self.CalculateNewBoundingBox(self.frame)
            cropped_mask = IU.CropImage(img=self.mask, bounding_set=IU.FloatBBToIntBB(self.bb))

            cv2.imshow("me smoll process frame ", frame)
            # cv2.imshow("me smoll process frame mask", mask)
            cv2.imshow("me smoll process frame mask cropped", cropped_mask)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

        print("Stopped running")

        self.AwaitInstructions(pipe=None)

    def CalculateNewBoundingBox(self, frame):
        # Takes the latest current frame and calculates the new bounding box from it
        # This function needs to be updated to improve the tracker

        self.new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        new_pts, status, err = cv2.calcOpticalFlowPyrLK(self.old_gray,
                                                        self.new_gray,
                                                        self.old_points_cropped,
                                                        None,
                                                        **self.lk_params)

        # Move bounding box by the average (x, y) movement of all points
        avg_x = 0
        avg_y = 0
        for i in range(len(new_pts)):
            x, y = new_pts[i].ravel()
            x_o, y_o = self.old_points_cropped[i].ravel()

            cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
            avg_x += (x - x_o)
            avg_y += (y - y_o)

        avg_x = avg_x / len(new_pts)
        avg_y = avg_y / len(new_pts)

        self.bb = [[self.bb[0][0] + avg_x, self.bb[0][1] + avg_y], [self.bb[1][0] + avg_x, self.bb[1][1] + avg_y]]

        self.old_gray = copy.deepcopy(self.new_gray)
        self.old_points_cropped = copy.deepcopy(new_pts)

        return IU.DrawBoundingBoxes(frame, [IU.FloatBBToIntBB(self.bb)])
