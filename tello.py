import socket
import threading
import time
import numpy as np
import libh264decoder

class Tello:
    """Wrapper class to interact with the Tello drone."""

    def __init__(self, local_ip, local_port, imperial=False, command_timeout=.3, tello_ip='192.168.10.1',
                 tello_port=8889):
        """
        Binds to the local IP/port and puts the Tello into command mode.

        :param local_ip (str): Local IP address to bind.
        :param local_port (int): Local port to bind.
        :param imperial (bool): If True, speed is MPH and distance is feet.
                             If False, speed is KPH and distance is meters.
        :param command_timeout (int|float): Number of seconds to wait for a response to a command.
        :param tello_ip (str): Tello IP.
        :param tello_port (int): Tello port.
        """

        self.abort_flag = False
        self.decoder = libh264decoder.H264Decoder()
        self.command_timeout = command_timeout
        self.imperial = imperial
        self.response = None  
        self.frame = None  # numpy array BGR -- current camera output frame
        self.is_freeze = False  # freeze current camera output
        self.last_frame = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for sending cmd
        self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for receiving video stream
        self.tello_address = (tello_ip, tello_port)
        self.local_video_port = 11111  # port for receiving video stream

        self.height = 0
        self.manual = True
        self.manual_move = []
        self.move_back_to_perimeter_flag = False
        self.socket.bind((local_ip, local_port))
        self.distance = 2
        self.degree = 30

        # thread for receiving cmd ack
        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True

        self.receive_thread.start()

        # to receive video -- send cmd: command, streamon
        self.socket.sendto(b'command', self.tello_address)
        print ('sent: command')
        self.socket.sendto(b'streamon', self.tello_address)
        print ('sent: streamon')

        self.socket_video.bind((local_ip, self.local_video_port))

        # thread for receiving video
        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True

        self.receive_video_thread.start()
        self.send("Command", 3)

    # Send the preplanned route to Tello and allow for a delay in seconds
    def send_preplanned_route(self, message, delay):
        # Try to send the message otherwise print the exception
        try:
            self.socket.sendto(message.encode(), self.tello_address)
            print("Sending message: " + message)
        except Exception as e:
            print("Error sending: " + str(e))

        # Delay for a user-defined period of time
        time.sleep(delay)

    # Send the message to Tello and allow for a delay in seconds
    def send(self, message, delay):
        if message.lower() == "land":
            self.height = 0
        elif message.lower() == "takeoff":
            self.height += 30
        # Try to send the message otherwise print the exception
        try:
            self.socket.sendto(message.encode(), self.tello_address)
            print("Sending message: " + message)
        except Exception as e:
            print("Error sending: " + str(e))

        # Delay for a user-defined period of time
        time.sleep(delay)

    # Receive the message from Tello
    def receive(self):
        # Continuously loop and listen for incoming messages
        while True:
            # Try to receive the message otherwise print the exception
            try:
                response, ip_address = self.socket.recvfrom(128)
                print("Received message: " + response.decode(encoding='utf-8'))
            except Exception as e:
                # If there's an error close the socket and break out of the loop
                self.socket.close()
                print("Error receiving: " + str(e))
            break

    def __del__(self):
        """Closes the local socket."""

        self.socket.close()
        self.socket_video.close()
    
    def read(self):
        """Return the last frame from camera."""
        if self.is_freeze:
            return self.last_frame
        else:
            return self.frame

    def video_freeze(self, is_freeze=True):
        """Pause video output -- set is_freeze to True"""
        self.is_freeze = is_freeze
        if is_freeze:
            self.last_frame = self.frame

    def _receive_thread(self):
        """Listen to responses from the Tello.

        Runs as a thread, sets self.response to whatever the Tello last returned.

        """
        while True:
            try:
                self.response, ip = self.socket.recvfrom(3000)
                #print(self.response)
            except socket.error as exc:
                print ("Caught exception socket.error : %s" % exc)

    def _receive_video_thread(self):
        """
        Listens for video streaming (raw h264) from the Tello.

        Runs as a thread, sets self.frame to the most recent frame Tello captured.

        """
        packet_data = ""
        while True:
            try:
                res_string, ip = self.socket_video.recvfrom(2048)
                packet_data += res_string
                # end of frame
                if len(res_string) != 1460:
                    for frame in self._h264_decode(packet_data):
                        self.frame = frame
                    packet_data = ""

            except socket.error as exc:
                print ("Caught exception socket.error : %s" % exc)
    
    def _h264_decode(self, packet_data):
        """
        decode raw h264 format data from Tello
        
        :param packet_data: raw h264 data array
       
        :return: a list of decoded frame
        """
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
                # print 'frame size %i bytes, w %i, h %i, linesize %i' % (len(frame), w, h, ls)

                frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep='')
                frame = (frame.reshape((h, ls / 3, 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)

        return res_frame_list

    def takeoff(self):
        if self.height != 0:
            print("Drone already took off!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.height += 30
            self.send('takeoff', 3)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((0, 0, self.height, 0))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[2] != 0:
                        new_distance = last_move[2] + self.height
                        self.manual_move.append((0, 0, new_distance, 0))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((0, 0, self.height, 0))

    def land(self):
        if self.height == 0:
            print("Drone already landed!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.send('land', 3)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((0, 0, -self.height, 0))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[2] != 0:
                        new_distance = last_move[2] - self.height
                        self.manual_move.append((0, 0, new_distance, 0))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((0, 0, -self.height, 0))
            self.height = 0

    def rotate_cw(self, degree):
        if self.height == 0:
            print("Please take off drone to rotate the drone!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.send('cw %s' % degree, 1)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((0, 0, 0, degree))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[3] != 0:
                        new_degree = last_move[3] + degree
                        if new_degree > 360:
                            new_degree -= 360
                        self.manual_move.append((0, 0, 0, new_degree))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((0, 0, 0, degree))

    def rotate_ccw(self, degree):
        if self.height == 0:
            print("Please take off drone to rotate the drone!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.send('ccw %s' % degree, 1)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((0, 0, 0, -degree))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[3] != 0:
                        new_degree = last_move[3] - degree
                        if new_degree < -360:
                            new_degree += 360
                        self.manual_move.append((0, 0, 0, new_degree))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((0, 0, 0, -degree))

    def move_up(self, distance):
        if not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.height += distance
            self.send('up %s' % distance, 1)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((0, 0, distance, 0))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[2] != 0:
                        new_distance = last_move[2] + self.distance
                        self.manual_move.append((0, 0, new_distance, 0))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((0, 0, distance, 0))

    def move_down(self, distance):
        if self.height == 0:
            print("Drone already landed and cannot go lower!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            if self.height - distance < 0:
                self.send('down %s' % self.height, 1)
                if not self.move_back_to_perimeter_flag:
                    if len(self.manual_move) == 0:
                        self.manual_move.append((0, 0, -self.height, 0))
                    else:
                        last_index = len(self.manual_move) - 1
                        last_move = self.manual_move.pop(last_index)
                        if last_move[2] != 0:
                            new_distance = last_move[2] - distance
                            self.manual_move.append((0, 0, new_distance, 0))
                        else:
                            self.manual_move.append(last_move)
                            self.manual_move.append((0, 0, -self.height, 0))
                self.height = 0
            else:
                self.send('down %s' % distance, 1)
                if not self.move_back_to_perimeter_flag:
                    if len(self.manual_move) == 0:
                        self.manual_move.append((0, 0, -distance, 0))
                    else:
                        last_index = len(self.manual_move) - 1
                        last_move = self.manual_move.pop(last_index)
                        if last_move[2] != 0:
                            new_distance = last_move[2] - distance
                            self.manual_move.append((0, 0, new_distance, 0))
                        else:
                            self.manual_move.append(last_move)
                            self.manual_move.append((0, 0, -distance, 0))

    def move_backward(self, distance):
        if self.height == 0:
            print("Please take off drone to move the drone!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.send('back %s' % distance, 1)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((0, -distance, 0, 0))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[1] != 0:
                        new_distance = last_move[1] - distance
                        self.manual_move.append((0, new_distance, 0, 0))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((0, -distance, 0, 0))

    def move_forward(self, distance):
        if self.height == 0:
            print("Please take off drone to move the drone!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.send('forward %s' % distance, 1)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((0, distance, 0, 0))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[1] != 0:
                        new_distance = last_move[1] + distance
                        self.manual_move.append((0, new_distance, 0, 0))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((0, distance, 0, 0))

    def move_left(self, distance):
        if self.height == 0:
            print("Please take off drone to move the drone!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.send('left %s' % distance, 1)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((-distance, 0, 0, 0))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[0] != 0:
                        new_distance = last_move[0] - distance
                        self.manual_move.append((new_distance, 0, 0, 0))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((-distance, 0, 0, 0))

    def move_right(self, distance):
        if self.height == 0:
            print("Please take off drone to move the drone!")
        elif not self.manual:
            print("Please activate manual mode to control the drone")
        else:
            self.send('right %s' % distance, 1)
            if not self.move_back_to_perimeter_flag:
                if len(self.manual_move) == 0:
                    self.manual_move.append((distance, 0, 0, 0))
                else:
                    last_index = len(self.manual_move) - 1
                    last_move = self.manual_move.pop(last_index)
                    if last_move[0] != 0:
                        new_distance = last_move[0] + distance
                        self.manual_move.append((new_distance, 0, 0, 0))
                    else:
                        self.manual_move.append(last_move)
                        self.manual_move.append((distance, 0, 0, 0))

    def stop(self):
        self.manual = True
        self.send('stop', 2)

    def set_degree(self, degree):
        self.degree = degree

    def set_distance(self, distance):
        self.distance = distance

    def back_to_perimeter_sweep(self):
        while len(self.manual_move) and self.move_back_to_perimeter_flag:
            last_index = len(self.manual_move) - 1
            to_move = self.manual_move.pop(last_index)
            if to_move[0] < 0:
                self.move_right(-to_move[0])
            elif to_move[0] > 0:
                self.move_left(to_move[0])
            elif to_move[1] < 0:
                self.move_forward(-to_move[1])
            elif to_move[1] > 0:
                self.move_backward(to_move[1])
            elif to_move[2] < 0:
                self.move_up(to_move[2])
            elif to_move[2] > 0:
                self.move_down(to_move[2])
            elif to_move[3] < -180 or to_move[3] > 180:
                self.rotate_cw(to_move[3])
            elif to_move[3] != 0 and (to_move[3] >= -180 or to_move[3] <= 180):
                self.rotate_ccw(to_move[3])
        self.manual = False
