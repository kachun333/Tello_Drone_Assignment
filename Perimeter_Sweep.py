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

    def take_off(self):
        self.tello.send("takeoff", 7)
        self.counter += 1

    def flyingLogic(self):
        # Billy's flight path
        if self.tello.manual:
            return
        # Send the takeoff command
        if self.counter == 0:
            if self.tello.height == 0:
                self.tello.send("takeoff", 7)
            self.counter += 1

        # Start at checkpoint 1 and print destination
        elif self.counter == 1:
            print("From the charging base to the starting checkpoint of sweep pattern.\n")
            self.tello.send(self.frombase[0] + " " + str(self.frombase[1]), 4)
            self.counter += 1

        elif self.counter == 2:
            self.tello.send(self.frombase[2] + " " + str(self.frombase[3]), 4)
            self.counter += 1
            print("Current location: Checkpoint 0 " + "\n")

        elif 3 <= self.counter <= 12:
            for i in range(len(self.checkpoint)):

                if self.stop_thread or self.tello.manual:
                    return
                if self.counter == (3 + i * 2):
                    if i == len(self.checkpoint) - 1:
                        print("Returning to Checkpoint 0. \n")
                    print("Rotating drone before going to: Checkpoint " + str(self.checkpoint[i][0]) + "\n")
                    self.tello.send(self.checkpoint[i][1] + " " + str(self.checkpoint[i][2]), 4)
                    self.counter += 1

                if self.stop_thread or self.tello.manual:
                    return
                if self.counter == (3 + i * 2 + 1):
                    print("Moving drone to: Checkpoint " + str(self.checkpoint[i][0]) + "\n")
                    self.tello.send(self.checkpoint[i][3] + " " + str(self.checkpoint[i][4]), 4)
                    self.counter += 1
                    print("Arrived at current location: Checkpoint " + str(self.checkpoint[i][0]) + "\n")
                    time.sleep(4)

        # Reach back at Checkpoint 0
        elif self.counter == 13:
            print("Complete sweep. Return to charging base.\n")
            self.tello.send(self.tobase[0] + " " + str(self.tobase[1]), 4)
            self.counter += 1

        elif self.counter == 14:
            self.tello.send(self.tobase[2] + " " + str(self.tobase[3]), 4)
            self.counter += 1

        elif self.counter == 15 and not self.tello.manual:
            # Turn to original direction before land
            print("Turn to original direction before land.\n")
            self.tello.send("cw 180", 4)

        elif self.counter == 16:
            # Land
            self.tello.send("land", 3)
            self.counter += 1
