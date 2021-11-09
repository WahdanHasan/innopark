from threading import Thread

class ShutDownEventListener:
    def __init__(self, shutdown_event):
        self.listener_thread = 0
        self.shutdown_should_keep_listening = True
        self.shutdown_event = shutdown_event

    def initialize(self):
        self.listener_thread = Thread(target=self.startListening)
        self.listener_thread.start()

    def startListening(self):

        while self.shutdown_should_keep_listening:
            self.shutdown_event.wait()
            self.shutdown_should_keep_listening = False
