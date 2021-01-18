import ctypes
import threading
import time


class AutoRoute(threading.Thread):

    def __init__(self, tello):
        threading.Thread.__init__(self)
        self.tello = tello
        self.paused = False
        # Explicitly using Lock over RLock since the use of self.paused
        # break reentrancy anyway, and I believe using Lock could allow
        # one thread to pause the worker, while another resumes; haven't
        # checked if Condition imposes additional limitations that would
        # prevent that. In Python 2, use of Lock instead of RLock also
        # boosts performance.
        self.pause_cond = threading.Condition(threading.Lock())

    def isPaused(self):
        return self.paused

    def run(self):
        while True:
            with self.pause_cond:
                while self.paused:
                    self.pause_cond.wait()

                # thread should do the thing if not paused
                self._flyingLogic()
            time.sleep(5)

        # Close the socket
        self.tello.__del__()

    def pause(self):
        self.paused = True
        # If in sleep, we acquire immediately, otherwise we wait for thread
        # to release condition. In race, worker will still see self.paused
        # and begin waiting until it's set back to False
        self.pause_cond.acquire()

    # should just resume the thread
    def resume(self):
        self.paused = False
        # Notify so thread will wake after lock released
        self.pause_cond.notify()
        # Now release the lock
        self.pause_cond.release()


    def _flyingLogic(self):
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

