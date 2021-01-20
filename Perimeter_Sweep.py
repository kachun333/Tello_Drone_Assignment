import ctypes
import threading
import time


class AutoRoute:

    def __init__(self, tello):
        self.tello = tello
        self.counter = 0  # counter to indicate reach which step/checkpoint
        self.stop_thread = False  # kill the thread
        # Travel to/from starting checkpoint 0 from/to the charging base
        self.frombase = ["forward", 50, "ccw", 150]
        self.tobase = ["ccw", 150, "forward", 50]
        self.checkpoint = [[1, "cw", 90, "forward", 100], [2, "ccw", 90, "forward", 80], [3, "ccw", 90, "forward", 40],
                    [4, "ccw", 90, "forward", 40], [5, "cw", 90, "forward", 60], [0, "ccw", 90, "forward", 40]]

    def restart(self):
        if self.counter >= 16:
            self.counter = 0
        else:
            print("Previous perimeter sweep is not done yet!")

    def stop(self):
        self.stop_thread = True

    def perimeter_sweep(self):
        while True:
            if self.stop_thread:
                break
            self.flyingLogic()

    def flyingLogic(self):
        # Billy's flight path
        if not self.tello.manual:
            # Send the takeoff command
            if self.counter == 0 and not self.tello.manual:
                if self.tello.height == 0:
                    self.tello.send("takeoff", 7)
                self.counter += 1

            if self.stop_thread:
                return

            # Start at checkpoint 1 and print destination
            if self.counter == 1 and not self.tello.manual:
                print("From the charging base to the starting checkpoint of sweep pattern.\n")
                self.tello.send(self.frombase[0] + " " + str(self.frombase[1]), 4)
                self.counter += 1

            if self.stop_thread:
                return

            if self.counter == 2 and not self.tello.manual:
                self.tello.send(self.frombase[2] + " " + str(self.frombase[3]), 4)
                self.counter += 1
                print("Current location: Checkpoint 0 " + "\n")
            current = 3

            if self.stop_thread:
                return

            for i in range(len(self.checkpoint)):
                if i == len(self.checkpoint) - 1:
                    print("Returning to Checkpoint 0. \n")

                if self.stop_thread or self.tello.manual:
                    return
                if self.counter == current:
                    print("Rotating drone before going to: Checkpoint " + str(self.checkpoint[i][0]) + "\n")
                    self.tello.send(self.checkpoint[i][1] + " " + str(self.checkpoint[i][2]), 4)
                    self.counter += 1
                current += 1
                if self.stop_thread or self.tello.manual:
                    return
                if self.counter == current:
                    print("Moving drone to: Checkpoint " + str(self.checkpoint[i][0]) + "\n")
                    self.tello.send(self.checkpoint[i][3] + " " + str(self.checkpoint[i][4]), 4)
                    self.counter += 1
                    print("Arrived at current location: Checkpoint " + str(self.checkpoint[i][0]) + "\n")
                    time.sleep(4)
                current += 1


            if self.stop_thread:
                return
            # Reach back at Checkpoint 0
            if self.counter == current and not self.tello.manual:
                print("Complete sweep. Return to charging base.\n")
                self.tello.send(self.tobase[0] + " " + str(self.tobase[1]), 4)
                self.counter += 1
            current += 1

            if self.stop_thread:
                return
            if self.counter == current and not self.tello.manual:
                self.tello.send(self.tobase[2] + " " + str(self.tobase[3]), 4)
                self.counter += 1
            current += 1

            if self.stop_thread:
                return
            if self.counter == current and not self.tello.manual:
                # Turn to original direction before land
                print("Turn to original direction before land.\n")
                self.tello.send("cw 180", 4)
            current += 1

            if self.stop_thread:
                return
            if self.counter == 0 and not self.tello.manual:
                if self.tello.height != 0:
                    # Land
                    self.tello.send("land", 3)
                self.counter += 1
