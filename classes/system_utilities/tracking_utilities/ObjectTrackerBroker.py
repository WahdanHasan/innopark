from classes.helper_classes.Enums import EntrantSide

import sys
from threading import Thread

class ObjectTrackerBroker:
    # Facilitates the exchange of tracked objects between object trackers

    # TODO: The broker should facilitate transfer of tracked object process pipes rather than just ids
    def __init__(self):

        # Adjacency matrix of cameras with their id in the correct spot
        self.adjacency_matrix = [ # UP DOWN LEFT RIGHT
                                 [-1, -1, 2, -1],
                                 [-1, -1, 1, 3],
                                 [-1, -1, 2, -1]
                                ]

        self.voyager_holding_list = []

        self.voyager_input_queue = 0
        self.voyager_output_queue = 0

        self.put_voyager_listener_thread = 0
        self.put_voyager_listener_thread_stopped = 0

        self.get_voyager_listener_thread = 0
        self.get_voyager_listener_thread_stopped = 0

    def Start(self, send_voyager_request_queue, get_voyager_request_queue):
        # Starts 2 threads that listen for requests from object trackers

        print("[ObjectTrackerBroker] Starting Broker.", file=sys.stderr)
        self.voyager_input_queue = send_voyager_request_queue
        self.voyager_output_queue = get_voyager_request_queue

        print("[ObjectTrackerBroker] Put voyager thread started.", file=sys.stderr)
        self.put_voyager_listener_thread = Thread(target=self.PutVoyagerRequestHandler)
        self.put_voyager_listener_thread_stopped = False
        self.put_voyager_listener_thread.daemon = True
        self.put_voyager_listener_thread.start()

        print("[ObjectTrackerBroker] Get voyager thread started.", file=sys.stderr)
        self.get_voyager_listener_thread = Thread(target=self.GetVoyagerRequestHandler)
        self.get_voyager_listener_thread_stopped = False
        self.get_voyager_listener_thread.daemon = True
        self.get_voyager_listener_thread.start()

        self.put_voyager_listener_thread.join()
        self.get_voyager_listener_thread.join()

        print("[ObjectTrackerBroker] Stopped Broker.", file=sys.stderr)

    def PutVoyagerRequestHandler(self):
        # Handles requests from trackers to notify the broker about an object that left the tracker

        while not self.put_voyager_listener_thread_stopped:
            (sender_camera_id, voyager_id, exit_direction) = self.voyager_input_queue.get()

            recipient_camera_id = self.GetCameraByDirection(sender_camera_id, exit_direction)

            self.voyager_holding_list.append([sender_camera_id, recipient_camera_id, voyager_id])



    def GetVoyagerRequestHandler(self):
        # Handles requests from trackers to check with the broker if it knows who their new entrant is

        found_entrant = False
        while not self.get_voyager_listener_thread_stopped:
            (recipient_camera_id, arrival_direction, pipe) = self.voyager_output_queue.get()

            sender_camera_id = self.GetCameraByDirection(recipient_camera_id, arrival_direction)

            for i in range(len(self.voyager_holding_list)):
                if self.voyager_holding_list[i][0] == sender_camera_id and self.voyager_holding_list[i][1] == recipient_camera_id:
                    pipe.send(self.voyager_holding_list[i][2])
                    found_entrant = True
                    break

            if found_entrant:
                found_entrant = False
                continue

            # If entrant is not found, return none
            pipe.send("None")



    def GetCameraByDirection(self, sender_camera, direction):

        if direction == EntrantSide.TOP:
            return self.adjacency_matrix[sender_camera-1][0]
        elif direction == EntrantSide.BOTTOM:
            return self.adjacency_matrix[sender_camera-1][1]
        elif direction == EntrantSide.LEFT:
            return self.adjacency_matrix[sender_camera-1][2]
        elif direction == EntrantSide.RIGHT:
            return self.adjacency_matrix[sender_camera-1][3]
