import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ObjectToPoolManagerInstruction
from classes.system_utilities.helper_utilities.Enums import TrackerToTrackedObjectInstruction

import sys
import cv2
import copy
import numpy as np
from threading import Thread
from multiprocessing import Process, Pipe, Queue, shared_memory


class TrackedObjectPoolManager:
    # Manages tracked object processes in a pool.

    def __init__(self):
        # Creates a pool of tracked object processes, their active status, and a pipe to communicate with each

        self.tracked_object_pool_request_queue = 0

        self.pool_size = 0
        self.new_tracked_object_process_event = 0

        self.tracked_object_process_pool = []
        self.tracked_object_process_pipes = []
        self.tracked_object_process_active_statuses = []
        self.tracked_object_bb_shared_memory_managers = []

        self.process_listener_thread = 0
        self.process_listener_thread_stopped = 0

    def Initialize(self, pool_size=1):

        self.tracked_object_pool_request_queue = Queue()

        self.pool_size = pool_size
        self.new_tracked_object_process_event = 0

        return self.tracked_object_pool_request_queue

    def Start(self):

        # Create tracked object subprocesses
        for i in range(self.pool_size):
            temp_pipe, bb_in_shared_memory_manager, temp_tracked_object_process = self.CreateTrackedObjectProcess()
            self.tracked_object_process_pool.append(temp_tracked_object_process)
            self.tracked_object_process_pipes.append(temp_pipe)
            self.tracked_object_process_active_statuses.append(False)
            self.tracked_object_bb_shared_memory_managers.append(bb_in_shared_memory_manager)

        print("[TrackedObjectPoolManager] Starting pool manager.", file=sys.stderr)

        print("[TrackedObjectPoolManager] Request listener thread started.", file=sys.stderr)
        self.process_listener_thread = Thread(target=self.ListenForProcessRequests)
        self.process_listener_thread_stopped = False
        self.process_listener_thread.daemon = True
        self.process_listener_thread.start()

        self.process_listener_thread.join()

        print("[TrackedObjectPoolManager] Stopped pool manager", file=sys.stderr)

    def ListenForProcessRequests(self):

        while not self.process_listener_thread_stopped:
            (instructions) = self.tracked_object_pool_request_queue.get()

            if instructions[0] == ObjectToPoolManagerInstruction.GET_PROCESS:
                self.GetTrackedObjectProcessRequest(instructions)
            if instructions[0] == ObjectToPoolManagerInstruction.RETURN_PROCESS:
                self.ReturnTrackedObjectProcessRequest(instructions)

    def GetTrackedObjectProcessRequest(self, instructions):
        (sender_pipe) = instructions[1]

        temp_pipe, bb_in_shared_memory_manager = self.GetTrackedObjectProcess()

        sender_pipe.send((temp_pipe, bb_in_shared_memory_manager))

    def GetTrackedObjectProcess(self):

        # Returns the next free process from the pool
        # If all processes are active, creates a new process, adds it to the pool, and then returns it

        for i in range(self.pool_size):
            if not self.tracked_object_process_active_statuses[i]:
                print("[TrackedObjectPoolManager] Returning process " + str(i+1) + " of " + str(self.pool_size) + ".", file=sys.stderr)
                self.tracked_object_process_active_statuses[i] = True
                return self.tracked_object_process_pipes[i], self.tracked_object_bb_shared_memory_managers[i]

        print("[TrackedObjectPoolManager] Creating and returning process " + str(self.pool_size + 1) + " as all " + str(self.pool_size) + " tracked objects are in use.", file=sys.stderr)

        temp_pipe, bb_in_shared_memory_manager, temp_tracked_object_process = self.CreateTrackedObjectProcess()

        # Set event for all listening processes to grab the new tracked object
        self.new_tracked_object_process_event.set()

        # Add new tracked object values to pool
        self.tracked_object_process_pool.append(temp_tracked_object_process)
        self.tracked_object_process_pipes.append(temp_pipe)
        self.tracked_object_process_active_statuses.append(True)
        self.tracked_object_bb_shared_memory_managers.append(bb_in_shared_memory_manager)

        # Reset event for all listening processes
        self.new_tracked_object_process_event.clear()

        return temp_pipe, bb_in_shared_memory_manager


    def ReturnTrackedObjectProcessRequest(self, instructions):
        x=10

    def ReturnTrackedObjectProcess(self):
        x=10

    def CreateTrackedObjectProcess(self):
        # Creates a tracked object process and opens a pipe to it
        # Returns the process and the other end of the pipe

        # Create a pipe to give to the subprocess
        pipe1, pipe2 = Pipe()

        # Create a bounding box blank to write to a shared memory space that holds the bounding box
        bb_in_shared_memory_manager = shared_memory.SharedMemory(create=True, size=np.asarray(Constants.bb_example, dtype=np.int32).nbytes)

        # Create a process for the tracked object and pass it the pipe and shared memory for its bounding box
        temp_tracked_object = TrackedObjectProcess()
        tracked_object_process = Process(target=temp_tracked_object.AwaitInstructions, args=(pipe2, bb_in_shared_memory_manager))
        tracked_object_process.start()

        return pipe1, bb_in_shared_memory_manager, temp_tracked_object

    def DestroyPool(self):
        # Destroys all processes stored in the pool

        for i in range(self.pool_size):
            self.tracked_object_process_pool[i].terminate()



class TrackedObjectProcess:
    # Tracks objects assigned to it

    def __init__(self):
        self.object_id = -1
        self.bb = 0
        self.tracking_instruction_pipe = 0
        self.info_request_pipe = 0
        self.should_keep_tracking = False
        self.old_gray = 0
        self.old_gray_cropped = 0
        self.old_points_cropped = 0
        self.new_gray = 0
        self.new_gray_cropped = 0
        self.new_points_cropped = 0

        self.bb_in_shared_memory = 0
        self.bb_in_shared_memory_manager = 0
        self.frame_in_shared_memory = 0
        self.mask_in_shared_memory = 0
        self.frame = 0
        self.mask = 0
        self.frame_shape = 0
        self.mask_shape = 0
        self.lk_params = dict(
                              maxLevel=50,
                              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    def AwaitInstructions(self, tracking_instruction_pipe, bb_in_shared_memory_manager):
        # The tracked object process sits idle until an object tracker sends a new task to it

        if self.tracking_instruction_pipe == 0:
            self.FirstTimeSetup(tracking_instruction_pipe, bb_in_shared_memory_manager)

        # Reset bb
        self.bb_in_shared_memory[:] = Constants.bb_example.copy()[:]

        (new_bb, new_object_id, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape) = tracking_instruction_pipe.recv()


        self.Initialize(new_object_id, new_bb, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape)
        self.StartTracking(self.tracking_instruction_pipe)

    def FirstTimeSetup(self, tracking_instruction_pipe, bb_in_shared_memory_manager):

        # Initialize instruction and info request pipes
        self.tracking_instruction_pipe = tracking_instruction_pipe

        # Create a reference to the bb in shared memory and its buffer
        self.bb_in_shared_memory_manager = bb_in_shared_memory_manager
        self.bb_in_shared_memory = np.ndarray(np.asarray(Constants.bb_example, dtype=np.int32).shape, dtype=np.int32,
                                              buffer=bb_in_shared_memory_manager.buf)

    def Initialize(self, object_id, bb, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape):
        # Sets the parameters for the tracked object

        self.object_id = object_id
        self.bb = bb
        self.should_keep_tracking = True

        self.frame_shape = base_frame_shape
        self.mask_shape = base_mask_shape

        self.frame_in_shared_memory = np.ndarray(self.frame_shape, dtype=np.uint8, buffer=shared_memory_manager_frame.buf)
        self.mask_in_shared_memory = np.ndarray(self.mask_shape, dtype=np.uint8, buffer=shared_memory_manager_mask.buf)

        # Optical flow LK params

        temp_cropped = IU.CropImage(self.frame_in_shared_memory, self.bb)
        self.old_gray_cropped = cv2.cvtColor(temp_cropped, cv2.COLOR_BGR2GRAY)
        self.old_gray = cv2.cvtColor(self.frame_in_shared_memory, cv2.COLOR_BGR2GRAY)

        self.old_points_cropped = cv2.goodFeaturesToTrack(self.old_gray_cropped, 100, 0.2, 10)

        for i in range(len(self.old_points_cropped)):
            self.old_points_cropped[i][0][0] = self.old_points_cropped[i][0][0] + self.bb[0][0]
            self.old_points_cropped[i][0][1] = self.old_points_cropped[i][0][1] + self.bb[0][1]

    def StartTracking(self, pipe):
        # Continues tracking the object until the object tracker sends -1 through the pipe.
        # In which case the process then returns and awaits for the next set of instructions

        print("[TrackedObjectProcess] Started tracking " + str(self.object_id) + ".", file=sys.stderr)
        while self.should_keep_tracking:

            # Wait for confirmation to read
            instruction = pipe.recv()

            # Validate if the message received is what was expected
            if not isinstance(instruction, TrackerToTrackedObjectInstruction):
                continue

            if instruction.value == TrackerToTrackedObjectInstruction.STOP_TRACKING.value:
                self.should_keep_tracking = False
                continue

            # Create a local copy of the frame and mask
            self.frame = self.frame_in_shared_memory.copy()
            self.mask = self.mask_in_shared_memory.copy()

            # Update based on object movement status
            if instruction.value == TrackerToTrackedObjectInstruction.OBJECT_MOVING.value:
                self.UpdateMovingObject()
            elif instruction.value == TrackerToTrackedObjectInstruction.OBJECT_STATIONARY.value:
                self.UpdateMovingObject()
                # self.UpdateStationaryObject()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

        print("[TrackedObjectProcess] Stopped running.", file=sys.stderr)

        self.AwaitInstructions(tracking_instruction_pipe=None, info_request_pipe=None ,bb_in_shared_memory_manager=None)

    def UpdateMovingObject(self):
        self.CalculateNewBoundingBox(self.frame)

        # cropped_mask = IU.CropImage(img=self.mask, bounding_set=IU.FloatBBToIntBB(self.bb))
        # cv2.imshow("me smoll process frame mask cropped", cropped_mask)

    def UpdateStationaryObject(self):
        x=10

    def CalculateNewBoundingBox(self, frame):
        # Takes the latest current frame and calculates the new bounding box from it
        # This function needs to be updated to improve the tracker

        # Calculate the new position of the optical flow points
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

        # Set variables for next optical flow run
        self.old_gray = copy.deepcopy(self.new_gray)
        self.old_points_cropped = copy.deepcopy(new_pts)

        # Write the new bounding box to shared memory
        self.bb_in_shared_memory[:] = np.asarray(IU.FloatBBToIntBB(self.bb), dtype=np.int32)

        return IU.DrawBoundingBoxes(frame, [IU.FloatBBToIntBB(self.bb)])



