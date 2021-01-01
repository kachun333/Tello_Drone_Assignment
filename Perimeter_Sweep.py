import tello
import time

# Create Billy
billy = tello.Tello('', 8889)  

# Send the takeoff command
billy.takeoff()

print("\n")

# Start at checkpoint 1 and print destination
print("From the charging base to the starting checkpoint of sweep pattern.\n")

billy.move_forward(50)
time.sleep(4)
billy.rotate_ccw(150)
time.sleep(4)
print("Current location: Checkpoint 0 " +  "\n")

billy.move_forward(100)
time.sleep(4)
print("Arrived at current location: Checkpoint 1\n")

billy.rotate_ccw(90)
time.sleep(4)
billy.move_forward(80)
time.sleep(4)
print("Arrived at current location: Checkpoint 2\n")

billy.rotate_ccw(90)
time.sleep(4)
billy.move_forward(40)
time.sleep(4)
print("Arrived at current location: Checkpoint 3\n")

billy.rotate_ccw(90)
time.sleep(4)
billy.move_forward(40)
time.sleep(4)
print("Arrived at current location: Checkpoint 4\n")

billy.rotate_cw(90)
time.sleep(4)
billy.move_forward(60)
time.sleep(4)
print("Arrived at current location: Checkpoint 5\n")

billy.rotate_ccw(90)
time.sleep(4)
billy.move_forward(40)
time.sleep(4)
print("Arrived at current location: Checkpoint 0\n")

# Reach back at Checkpoint 0
print("Complete sweep. Return to charging base.\n")
billy.rotate_ccw(150)
time.sleep(4)
billy.move_forward(50)
time.sleep(4)


# Turn to original direction before land
print("Turn to original direction before land.\n")
billy.rotate_cw
billy.rotate_cw(180)
time.sleep(4)

# Land
billy.land()
time.sleep(3)


# Close the socket
billy.__del__()


