import ctypes
import threading
import time


class AutoRoute(threading.Thread):

    def __init__(self, tello):
        threading.Thread.__init__(self)
        self.tello = tello

    def run(self):
        self.tello = self.tello
        try:
            self._flyingLogic()
        finally:
            print("auto mode ended")
        # Close the socket
        self.tello.__del__()

    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_interrupt(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Interrupt failure')

    def _flyingLogic(self):
        while True:
            # Send the takeoff command
            self.tello.takeoff()

            print("\n")

            # Start at checkpoint 1 and print destination
            print("From the charging base to the starting checkpoint of sweep pattern.\n")

            self.tello.move_forward(50)
            time.sleep(4)
            self.tello.rotate_ccw(150)
            time.sleep(4)
            print("Current location: Checkpoint 0 " + "\n")

            self.tello.move_forward(100)
            time.sleep(4)
            print("Arrived at current location: Checkpoint 1\n")

            self.tello.rotate_ccw(90)
            time.sleep(4)
            self.tello.move_forward(80)
            time.sleep(4)
            print("Arrived at current location: Checkpoint 2\n")

            self.tello.rotate_ccw(90)
            time.sleep(4)
            self.tello.move_forward(40)
            time.sleep(4)
            print("Arrived at current location: Checkpoint 3\n")

            self.tello.rotate_ccw(90)
            time.sleep(4)
            self.tello.move_forward(40)
            time.sleep(4)
            print("Arrived at current location: Checkpoint 4\n")

            self.tello.rotate_cw(90)
            time.sleep(4)
            self.tello.move_forward(60)
            time.sleep(4)
            print("Arrived at current location: Checkpoint 5\n")

            self.tello.rotate_ccw(90)
            time.sleep(4)
            self.tello.move_forward(40)
            time.sleep(4)
            print("Arrived at current location: Checkpoint 0\n")

            # Reach back at Checkpoint 0
            print("Complete sweep. Return to charging base.\n")
            self.tello.rotate_ccw(150)
            time.sleep(4)
            self.tello.move_forward(50)
            time.sleep(4)

            # Turn to original direction before land
            print("Turn to original direction before land.\n")
            self.tello.rotate_cw(180)
            time.sleep(4)

            # Land
            self.tello.land()
            time.sleep(3)

