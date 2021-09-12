from multiprocessing import Queue
from threading import Thread

class ObjectTrackerBroker:
    def __init__(self):

        self.adjacency_matrix = [ # UP DOWN LEFT RIGHT
                                 [-1, -1, 2, -1],
                                 [-1, -1, 1, 3],
                                 [-1, -1, 2, -1]
                                ]

        self.voyager_holding_list = []

        self.voyager_input_queue = 0
        self.voyager_output_queue = 0

        self.input_listener_thread = 0
        self.input_listener_thread_stopped = 0

        self.output_listener_thread = 0
        self.output_listener_thread_stopped = 0

    def Start(self, voyager_input_queue, voyager_output_queue):
        print("Started process")
        self.voyager_input_queue = voyager_input_queue
        self.voyager_output_queue = voyager_output_queue


        self.input_listener_thread = Thread(target=self.ListenForVoyagerInputs)
        self.input_listener_thread_stopped = False
        self.input_listener_thread.daemon = True
        self.input_listener_thread.start()

        self.output_listener_thread = Thread(target=self.ListenForVoyagerOutputs)
        self.output_listener_thread_stopped = False
        self.output_listener_thread.daemon = True
        self.output_listener_thread.start()

        self.input_listener_thread.join()
        self.output_listener_thread.join()


    def ListenForVoyagerInputs(self):
        print("input thread started")
        while not self.input_listener_thread_stopped:
            (sender_camera_id, voyager_id, exit_direction) = self.voyager_input_queue.get()

            recipient_camera_id = self.GetCameraByDirection(sender_camera_id, exit_direction)

            self.voyager_holding_list.append([sender_camera_id, recipient_camera_id, voyager_id])



    def ListenForVoyagerOutputs(self):
        print("Output thread started")
        while not self.output_listener_thread_stopped:
            (recipient_camera_id, arrival_direction, pipe) = self.voyager_output_queue.get()

            sender_camera_id = self.GetCameraByDirection(recipient_camera_id, arrival_direction)

            for i in range(len(self.voyager_holding_list)):
                if self.voyager_holding_list[i][0] == sender_camera_id and self.voyager_holding_list[i][1] == recipient_camera_id:
                    pipe.send(self.voyager_holding_list[i][2])
                    continue

            pipe.send("None")



    def GetCameraByDirection(self, sender_camera, direction):

        if direction == "top":
            return self.adjacency_matrix[sender_camera-1][0]
        elif direction == "bottom":
            return self.adjacency_matrix[sender_camera-1][1]
        elif direction == "left":
            return self.adjacency_matrix[sender_camera-1][2]
        elif direction == "right":
            return self.adjacency_matrix[sender_camera-1][3]
