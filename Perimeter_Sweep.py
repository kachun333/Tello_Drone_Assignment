import ctypes
import threading
import time


class AutoRoute(threading.Thread):

    def __init__(self, tello):
        threading.Thread.__init__(self)
        self.tello = tello
        self.__flag = threading.Event() # The flag used to pause the thread
        self.__flag.set() # Set to True
        self.__running = threading.Event() # Used to stop the thread identification
        self.__running.set() # Set running to True

    def isRunning(self):
        return self.__running.isSet()

    def isPaused(self):
        return not self.__flag.isSet()

    def run(self):
        self.tello = self.tello
        while self.__running.isSet():
            self._flyingLogic()
        # Close the socket
        self.tello.__del__()

    def pause(self):
        self.__flag.clear() # Set to False to block the thread

    def resume(self):
        self.__flag.set() # Set to True, let the thread stop blocking

    def stop(self):
        self.__flag.set() # Resume the thread from the suspended state, if it is already suspended
        self.__running.clear() # Set to False

    def _flyingLogic(self):
        # Send the takeoff command
        self.tello.takeoff()

        print("\n")

        # Start at checkpoint 1 and print destination
        print("From the charging base to the starting checkpoint of sweep pattern.\n")

        self.tello.move_forward(50)
        self._checkIsInterrupted()
        self.tello.rotate_ccw(150)
        self._checkIsInterrupted()
        print("Current location: Checkpoint 0 " + "\n")

        self.tello.move_forward(100)
        self._checkIsInterrupted()
        print("Arrived at current location: Checkpoint 1\n")

        self.tello.rotate_ccw(90)
        self._checkIsInterrupted()
        self.tello.move_forward(80)
        self._checkIsInterrupted()
        print("Arrived at current location: Checkpoint 2\n")

        self.tello.rotate_ccw(90)
        self._checkIsInterrupted()
        self.tello.move_forward(40)
        self._checkIsInterrupted()
        print("Arrived at current location: Checkpoint 3\n")

        self.tello.rotate_ccw(90)
        self._checkIsInterrupted()
        self.tello.move_forward(40)
        self._checkIsInterrupted()
        print("Arrived at current location: Checkpoint 4\n")

        self.tello.rotate_cw(90)
        self._checkIsInterrupted()
        self.tello.move_forward(60)
        self._checkIsInterrupted()
        print("Arrived at current location: Checkpoint 5\n")

        self.tello.rotate_ccw(90)
        self._checkIsInterrupted()
        self.tello.move_forward(40)
        self._checkIsInterrupted()
        print("Arrived at current location: Checkpoint 0\n")

        # Reach back at Checkpoint 0
        print("Complete sweep. Return to charging base.\n")
        self.tello.rotate_ccw(150)
        self._checkIsInterrupted()
        self.tello.move_forward(50)
        self._checkIsInterrupted()

        # Turn to original direction before land
        print("Turn to original direction before land.\n")
        self.tello.rotate_cw(180)
        self._checkIsInterrupted()

        # Land
        self.tello.land()
        self._checkIsInterrupted()

    def _checkIsInterrupted(self):
        self.__flag.wait()  # return immediately when it is True, block until the internal flag is True when it is False
        time.sleep(5)
