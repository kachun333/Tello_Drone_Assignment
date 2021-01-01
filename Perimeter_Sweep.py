import tello
import time

# Create Billy
billy = tello.Tello()

# Travel to/from starting checkpoint 0 from/to the charging base
frombase = ["forward", 50, "ccw", 150]
tobase = ["ccw", 150, "forward", 50]

# Flight path to Checkpoint 1 to 5 and back to Checkpoint 0 sequentially
checkpoint = [[1, "cw", 90, "forward", 100], [2, "ccw", 90, "forward", 80], [3, "ccw", 90, "forward", 40],
           [4, "ccw", 90, "forward", 40], [5, "cw", 90, "forward", 60], [0, "ccw", 90, "forward", 40]]



# Put Tello into command mode
billy.send("command", 3)

# Send the takeoff command
billy.send("takeoff", 7)

print("\n")

# Start at checkpoint 1 and print destination
print("From the charging base to the starting checkpoint of sweep pattern.\n")

billy.send(frombase[0] + " " + str(frombase[1]), 4)
billy.send(frombase[2] + " " + str(frombase[3]), 4)

print("Current location: Checkpoint 0 " +  "\n")


# Billy's flight path
for i in range(len(checkpoint)):
    if i == len(checkpoint)-1:
        print("Returning to Checkpoint 0. \n")

    billy.send(checkpoint[i][1] + " " + str(checkpoint[i][2]), 4)
    billy.send(checkpoint[i][3] + " " + str(checkpoint[i][4]), 4)

    print("Arrived at current location: Checkpoint " + str(checkpoint[i][0]) + "\n")
    time.sleep(4)

# Reach back at Checkpoint 0
print("Complete sweep. Return to charging base.\n")
billy.send(tobase[0] + " " + str(tobase[1]), 4)
billy.send(tobase[2] + " " + str(tobase[3]), 4)


# Turn to original direction before land
print("Turn to original direction before land.\n")
billy.send("cw 180", 4)

# Land
billy.send("land", 3)


# Close the socket
billy.sock.close()


