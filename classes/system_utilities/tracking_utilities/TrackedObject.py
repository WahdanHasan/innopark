import classes.system_utilities.image_utilities.ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities.Enums import ObjectToPoolManagerInstruction, TrackedObjectStatus, \
    TrackerToTrackedObjectInstruction, ShutDownEvent, TrackedObjectToBrokerInstruction
from classes.super_classes.ShutDownEventListener import ShutDownEventListener

import sys
import cv2
import copy
import numpy as np
from threading import Thread
from multiprocessing import Process, Pipe, shared_memory


class TrackedObjectPoolManager(ShutDownEventListener):
    # Manages tracked object processes in a pool.

    def __init__(self, tracked_object_pool_request_queue, new_tracked_object_process_event, initialized_event, shutdown_event, broker_request_queue):
        # Creates a pool of tracked object processes, their active status, and a pipe to communicate with each
        ShutDownEventListener.__init__(self, shutdown_event)

        self.tracked_object_pool_request_queue = tracked_object_pool_request_queue
        self.broker_request_queue = broker_request_queue
        self.pool_process = 0
        self.pool_size = Constants.base_pool_size
        self.shutdown_event = shutdown_event
        self.new_tracked_object_process_event = new_tracked_object_process_event
        self.initialized_event = initialized_event

        self.tracked_object_process_pool = []
        self.tracked_object_process_pipes = []
        self.tracked_object_process_active_statuses = []
        self.tracked_object_bb_shared_memory_managers = []
        self.tracked_object_id_shared_memory_managers = []
        self.tracked_object_id_shared_memory = []

        self.process_listener_thread = 0
        self.process_listener_thread_stopped = 0
        self.shutdown_listener_thread = 0

    def startProcess(self):

        self.pool_process = Process(target=self.start)
        self.pool_process.start()

    def stopProcess(self):

        self.pool_process.terminate()

    def start(self):

        ShutDownEventListener.initialize(self)

        # Create tracked object subprocesses
        for i in range(self.pool_size):
            self.createTrackedObjectProcess(process_number=i)

        self.initialized_event.set()

        print("[TrackedObjectPoolManager] Starting pool manager.", file=sys.stderr)

        print("[TrackedObjectPoolManager] Request listener thread started.", file=sys.stderr)
        self.process_listener_thread = Thread(target=self.listenForProcessRequests)
        self.process_listener_thread_stopped = False
        self.process_listener_thread.daemon = True
        self.process_listener_thread.start()

        self.process_listener_thread.join()

        print("[TrackedObjectPoolManager] Stopped pool manager", file=sys.stderr)

    def listenForProcessRequests(self):

        while not self.process_listener_thread_stopped:
            (instructions) = self.tracked_object_pool_request_queue.get()


            if instructions == ShutDownEvent.SHUTDOWN:
                print("[TrackedObjectPoolManager] Cleaning up.", file=sys.stderr)
                self.cleanUp()
                return

            elif instructions[0] == ObjectToPoolManagerInstruction.GET_PROCESS:
                self.getTrackedObjectProcessRequest(instructions)
            elif instructions[0] == ObjectToPoolManagerInstruction.RETURN_PROCESS:
                self.returnTrackedObjectProcessRequest(instructions)
            elif instructions[0] == ObjectToPoolManagerInstruction.SET_PROCESS_NEW_ID:
                self.setProcessNewId(instructions)

    def setProcessNewId(self, instructions):
        new_id = instructions[1]
        old_id = instructions[2]

        for i in range(len(self.tracked_object_id_shared_memory)):
            temp_ids = self.integerTrackedObjectIdsToAscii(self.tracked_object_id_shared_memory[i])

            if temp_ids[2] == old_id:
                temp_list = np.array([ord(c) for c in new_id], dtype=np.uint8)

                self.tracked_object_id_shared_memory[i][2: temp_list.shape[0] + 2] = temp_list
                break

    def integerTrackedObjectIdsToAscii(self, camera_id_and_license_in_shared_memory):
        temp_list = camera_id_and_license_in_shared_memory.tolist()

        # If object id is none, return only the camera id, else, return both
        if temp_list[1] == Constants.tracked_process_ids_example[1]:
            return [int(temp_list[0]), None]
        else:
            # Convert all non 0 integers to ascii only
            return [int(temp_list[0]), int(temp_list[1]),
                    ''.join('' if i == 0 else chr(i) for i in temp_list[2:])]

    def getTrackedObjectProcessRequest(self, instructions):
        (sender_pipe) = instructions[1]

        temp_pipe, bb_in_shared_memory_manager, process_idx = self.getTrackedObjectProcess()

        sender_pipe.send((temp_pipe, bb_in_shared_memory_manager, process_idx))

    def getTrackedObjectProcess(self):

        # Returns the next free process from the pool
        # If all processes are active, creates a new process, adds it to the pool, and then returns it

        for i in range(self.pool_size):
            if not self.tracked_object_process_active_statuses[i]:
                print("[TrackedObjectPoolManager] Lending process " + str(i+1) + " of " + str(self.pool_size) + ".", file=sys.stderr)
                self.tracked_object_process_active_statuses[i] = True
                return self.tracked_object_process_pipes[i], self.tracked_object_bb_shared_memory_managers[i], i

        print("[TrackedObjectPoolManager] Creating and returning process " + str(self.pool_size + 1) + " as all " + str(self.pool_size) + " tracked objects are in use.", file=sys.stderr)

        self.createTrackedObjectProcess(process_number=self.pool_size)

        self.pool_size += 1
        temp_pipe = self.tracked_object_process_pipes[len(self.tracked_object_process_pipes) - 1]
        bb_in_shared_memory_manager = self.tracked_object_bb_shared_memory_managers[len(self.tracked_object_bb_shared_memory_managers) - 1]

        # # Set event for all listening processes to grab the new tracked object
        # self.new_tracked_object_process_event.set()
        #
        #
        # # Reset event for all listening processes
        # self.new_tracked_object_process_event.clear()

        return temp_pipe, bb_in_shared_memory_manager, self.pool_size -1

    def returnTrackedObjectProcessRequest(self, instructions):
        (process_idx) = instructions[1]
        camera_id = instructions[2]
        temp_exit_side = instructions[3]



        self.broker_request_queue.put((TrackedObjectToBrokerInstruction.PUT_VOYAGER,
                                       camera_id,
                                       self.integerTrackedObjectIdsToAscii(self.tracked_object_id_shared_memory[process_idx])[2],
                                       temp_exit_side))

        self.returnTrackedObjectProcess(process_idx)

    def returnTrackedObjectProcess(self, process_idx):
        self.tracked_object_process_active_statuses[process_idx] = False
        self.tracked_object_process_pipes[process_idx].send(TrackerToTrackedObjectInstruction.STOP_TRACKING)
        print("[TrackedObjectPoolManager] Received return request for process with id " + str(process_idx + 1) + ".", file=sys.stderr)

        count = 0

        for i in range(len(self.tracked_object_process_active_statuses)):
            if self.tracked_object_process_active_statuses[i]:
                count += 1

        print("[TrackedObjectPoolManager] " + str(count) + " of " + str(self.pool_size) + " are currently active.", file=sys.stderr)

    def getObjectIdsFromProcessId(self, process_idx):
        return

    def createTrackedObjectProcess(self, process_number):
        # Creates a tracked object process and opens a pipe to it
        # Returns the process and the other end of the pipe

        # Create a pipe to give to the subprocess
        pipe1, pipe2 = Pipe()

        # Create a bounding box blank to write to a shared memory space that holds the bounding box
        temp_bb_shared_memory_manager_name = Constants.bb_shared_memory_manager_prefix + str(process_number)
        bb_in_shared_memory_manager = shared_memory.SharedMemory(create=True,
                                                                 name=temp_bb_shared_memory_manager_name,
                                                                 size=np.asarray(Constants.bb_example, dtype=np.float32).nbytes)

        # Create a pair of ids in shared memory space
        temp_ids_shared_memory_manager_name = Constants.tracked_process_ids_shared_memory_prefix + str(process_number)
        ids_in_shared_memory_manager = shared_memory.SharedMemory(create=True,
                                                                  name=temp_ids_shared_memory_manager_name,
                                                                  size=np.asarray(Constants.tracked_process_ids_example, dtype=np.uint8).nbytes)

        self.tracked_object_id_shared_memory.append(np.ndarray(shape=np.asarray(Constants.tracked_process_ids_example, dtype=np.uint8).shape,
                                                               dtype=np.uint8,
                                                               buffer=ids_in_shared_memory_manager.buf))

        # Create a process for the tracked object and pass it the pipe and shared memory for its bounding box
        temp_tracked_object = TrackedObjectProcess()
        tracked_object_process = Process(target=temp_tracked_object.awaitInstructions, args=(pipe2, bb_in_shared_memory_manager, ids_in_shared_memory_manager))
        tracked_object_process.start()

        # Add new tracked object values to pool
        self.tracked_object_process_pool.append(tracked_object_process)
        self.tracked_object_process_pipes.append(pipe1)
        self.tracked_object_process_active_statuses.append(False)
        self.tracked_object_bb_shared_memory_managers.append(bb_in_shared_memory_manager)
        self.tracked_object_id_shared_memory_managers.append(ids_in_shared_memory_manager)

    def destroyPool(self):
        # Destroys all processes stored in the pool

        for i in range(self.pool_size):
            self.tracked_object_process_pool[i].terminate()

    def cleanUp(self):
        for shm_bb in self.tracked_object_bb_shared_memory_managers:
            shm_bb.unlink()

        for shm_id in self.tracked_object_id_shared_memory_managers:
            shm_id.unlink()

        for pipes in self.tracked_object_process_pipes:
            pipes.send(ShutDownEvent.SHUTDOWN)
            pipes.close()




class TrackedObjectProcess:
    # Tracks objects assigned to it

    def __init__(self):
        self.camera_id = -1
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
        self.ids_in_shared_memory = 0
        self.ids_in_shared_memory_manager = 0
        self.frame_in_shared_memory = 0
        self.mask_in_shared_memory = 0
        self.frame = 0
        self.mask = 0
        self.frame_shape = 0
        self.mask_shape = 0
        self.lk_params = dict(
                              maxLevel=50,
                              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    def awaitInstructions(self, tracking_instruction_pipe, bb_in_shared_memory_manager, ids_in_shared_memory_manager):
        # The tracked object process sits idle until an object tracker sends a new task to it

        if self.tracking_instruction_pipe == 0:
            self.firstTimeSetup(tracking_instruction_pipe, bb_in_shared_memory_manager, ids_in_shared_memory_manager)

        # Reset tracked process
        self.resetTrackedProcess()

        # Wait for instructions
        instruction = tracking_instruction_pipe.recv()

        if instruction == ShutDownEvent.SHUTDOWN:
            return

        (camera_id, tracker_id, new_bb, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape) = instruction


        # Initialize new settings and begin tracking
        self.initialize(camera_id, tracker_id, new_bb, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape)
        self.startTracking(self.tracking_instruction_pipe)

    def firstTimeSetup(self, tracking_instruction_pipe, bb_in_shared_memory_manager, ids_in_shared_memory_manager):

        # Initialize instruction and info request pipes
        self.tracking_instruction_pipe = tracking_instruction_pipe

        # Create a reference to the bb in shared memory and its buffer
        self.bb_in_shared_memory_manager = bb_in_shared_memory_manager
        self.bb_in_shared_memory = np.ndarray(shape=np.asarray(Constants.bb_example, dtype=np.float32).shape,
                                              dtype=np.float32,
                                              buffer=bb_in_shared_memory_manager.buf)

        self.ids_in_shared_memory_manager = ids_in_shared_memory_manager
        self.ids_in_shared_memory = np.ndarray(shape=np.asarray(Constants.tracked_process_ids_example, dtype=np.uint8).shape,
                                               dtype=np.uint8,
                                               buffer=ids_in_shared_memory_manager.buf)

        self.resetTrackedProcess()

    def initialize(self, camera_id, tracker_id, bb, shared_memory_manager_frame, base_frame_shape, shared_memory_manager_mask, base_mask_shape):
        # Sets the parameters for the tracked object

        self.object_id = None
        self.camera_id = camera_id
        self.bb = bb
        self.should_keep_tracking = True

        self.frame_shape = base_frame_shape
        self.mask_shape = base_mask_shape

        self.frame_in_shared_memory = np.ndarray(self.frame_shape, dtype=np.uint8, buffer=shared_memory_manager_frame.buf)
        self.mask_in_shared_memory = np.ndarray(self.mask_shape, dtype=np.uint8, buffer=shared_memory_manager_mask.buf)

        self.ids_in_shared_memory[0] = np.uint8(tracker_id)
        self.ids_in_shared_memory[1] = np.uint8(camera_id)

        self.initializeOpticalFlow(bb=self.bb)

    def initializeOpticalFlow(self, bb):
        # Optical flow LK params

        temp_cropped = IU.CropImage(self.frame_in_shared_memory, bb)
        self.old_gray_cropped = cv2.cvtColor(temp_cropped, cv2.COLOR_BGR2GRAY)
        self.old_gray = cv2.cvtColor(self.frame_in_shared_memory, cv2.COLOR_BGR2GRAY)

        self.old_points_cropped = cv2.goodFeaturesToTrack(self.old_gray_cropped, 100, 0.2, 10)

        for i in range(len(self.old_points_cropped)):
            self.old_points_cropped[i][0][0] = self.old_points_cropped[i][0][0] + bb[0][0]
            self.old_points_cropped[i][0][1] = self.old_points_cropped[i][0][1] + bb[0][1]

    def writeObjectIdToSharedMemory(self, object_id):
        temp_list = np.array([ord(c) for c in object_id], dtype=np.uint8)

        self.ids_in_shared_memory[2: temp_list.shape[0] + 2] = temp_list

    def resetTrackedProcess(self):
        self.bb_in_shared_memory[:] = Constants.bb_example.copy()[:]
        self.ids_in_shared_memory[:] = np.asarray(Constants.tracked_process_ids_example, dtype=np.uint8)

    def startTracking(self, pipe):
        # Continues tracking the object until the object tracker sends -1 through the pipe.
        # In which case the process then returns and awaits for the next set of instructions
        pipe.send((TrackedObjectStatus.BB_UPDATED))

        while self.should_keep_tracking:

            # Wait for confirmation to read
            instruction = pipe.recv()

            if instruction == ShutDownEvent.SHUTDOWN:
                self.cleanUp()
                return

            # Validate if the message received is a proper instruction
            if not isinstance(instruction, TrackerToTrackedObjectInstruction):
                if isinstance(instruction, list):
                    if not isinstance(instruction[0], TrackerToTrackedObjectInstruction):
                        continue
                    elif instruction[0] == TrackerToTrackedObjectInstruction.STORE_NEW_ID:
                        new_object_id = instruction[2]
                        self.writeObjectIdToSharedMemory(object_id=new_object_id)
                        instruction = instruction[1]

                        print("[TrackedObjectProcess] Started tracking " + str(new_object_id) + ".", file=sys.stderr)
                    elif instruction[0] == TrackerToTrackedObjectInstruction.STORE_NEW_BB:
                        self.initializeOpticalFlow(instruction[1])
                        self.bb[:] = instruction[1][:]
                        continue


            if instruction == TrackerToTrackedObjectInstruction.STOP_TRACKING:
                self.should_keep_tracking = False
                continue

            # Create a local copy of the frame and mask
            self.frame = self.frame_in_shared_memory.copy()
            self.mask = self.mask_in_shared_memory.copy()

            # Update based on object movement status
            if instruction == TrackerToTrackedObjectInstruction.OBJECT_MOVING:
                self.updateMovingObject()

            pipe.send((TrackedObjectStatus.BB_UPDATED))

        print("[TrackedObjectProcess] Process released by tracker. Awaiting instructions. ", file=sys.stderr)

        self.awaitInstructions(tracking_instruction_pipe=self.tracking_instruction_pipe,
                               bb_in_shared_memory_manager=None,
                               ids_in_shared_memory_manager=None)

    def updateMovingObject(self):
        self.calculateNewBoundingBox(self.frame)

    def calculateNewBoundingBox(self, frame):
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
        self.bb_in_shared_memory[:] = np.asarray(self.bb, dtype=np.float32)

    def cleanUp(self):
        self.tracking_instruction_pipe.close()
