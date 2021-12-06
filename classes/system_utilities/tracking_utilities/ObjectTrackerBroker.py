from classes.system_utilities.helper_utilities.Enums import EntrantSide
from classes.system_utilities.helper_utilities.Enums import TrackedObjectToBrokerInstruction
from classes.system_utilities.helper_utilities.Enums import ShutDownEvent

import sys
from threading import Thread

from multiprocessing import Process

class ObjectTrackerBroker:
    # Facilitates the exchange of tracked objects between object trackers


    def __init__(self, broker_request_queue):

        # Adjacency matrix of cameras with their id in the correct spot
        # self.adjacency_matrix = [ # UP DOWN LEFT RIGHT
        #                          [-1, -1, 2, -1],
        #                          [-1, -1, 1, 3],
        #                          [-1, -1, 2, -1]
        #                         ]

        self.adjacency_matrix = [ # UP DOWN LEFT RIGHT
                                 [-1, -1, -1, 2],
                                 [-1, -1, 1, 3],
                                 [-1, -1, 2, 4],
                                 [-1, -1, 3, -5]
                                ]

        self.voyager_holding_list = []

        self.listen_for_requests_thread = 0
        self.listen_for_requests_thread_stopped = 0
        self.broker_request_queue = broker_request_queue
        self.broker_process = 0

    def StartProcess(self):
        self.broker_process = Process(target=self.Start)
        self.broker_process.start()

    def StopProcess(self):
        self.broker_process.terminate()

    def Start(self):
        # Starts a thread that listens for requests from object trackers

        print("[ObjectTrackerBroker] Starting Broker.", file=sys.stderr)

        print("[ObjectTrackerBroker] Request listener thread started.", file=sys.stderr)
        self.listen_for_requests_thread = Thread(target=self.ListenForVoyagerRequests)
        self.listen_for_requests_thread_stopped = False
        self.listen_for_requests_thread.daemon = True
        self.listen_for_requests_thread.start()

        self.listen_for_requests_thread.join()

        print("[ObjectTrackerBroker] Stopped Broker.", file=sys.stderr)

    def ListenForVoyagerRequests(self):
        # Listens for requests from object trackers

        while not self.listen_for_requests_thread_stopped:
            (instructions) = self.broker_request_queue.get()

            if instructions == ShutDownEvent.SHUTDOWN:
                print("[ObjectTrackerBroker] Cleaning up.", file=sys.stderr)
                return

            if instructions[0] == TrackedObjectToBrokerInstruction.GET_VOYAGER:
                self.GetVoyagerRequest(instructions)

            elif instructions[0] == TrackedObjectToBrokerInstruction.PUT_VOYAGER:
                self.PutVoyagerRequest(instructions)

    def GetVoyagerRequest(self, instructions):

        (recipient_camera_id, arrival_direction, pipe) = instructions[1:4]

        sender_camera_id = self.GetCameraByDirection(recipient_camera_id, arrival_direction)

        for i in range(len(self.voyager_holding_list)):
            if self.voyager_holding_list[i][0] == sender_camera_id and self.voyager_holding_list[i][1] == recipient_camera_id:
                pipe.send(self.voyager_holding_list[i][2])
                self.voyager_holding_list.pop(i)
                return

        # If entrant is not found, send none through pipe
        pipe.send("None")
        return

    def PutVoyagerRequest(self, instructions):

        (sender_camera_id, voyager_id, exit_direction) = instructions[1:4]

        recipient_camera_id = self.GetCameraByDirection(sender_camera_id, exit_direction)

        self.voyager_holding_list.append([sender_camera_id, recipient_camera_id, voyager_id])

        print("[ObjectTrackerBroker] Received object with id " + str(voyager_id), file=sys.stderr)

    def GetCameraByDirection(self, sender_camera, direction):

        if direction == EntrantSide.TOP:
            return self.adjacency_matrix[sender_camera-1][0]
        elif direction == EntrantSide.BOTTOM:
            return self.adjacency_matrix[sender_camera-1][1]
        elif direction == EntrantSide.LEFT:
            return self.adjacency_matrix[sender_camera-1][2]
        elif direction == EntrantSide.RIGHT:
            return self.adjacency_matrix[sender_camera-1][3]
