from PIL import Image
from PIL import ImageTk
import Tkinter as tki
from Tkinter import Toplevel, Scale
import threading
import datetime
import cv2
import os
import time
import platform

from Perimeter_Sweep import AutoRoute


class TelloUI:
    """Wrapper class to enable the GUI."""

    def __init__(self,tello,outputpath):
        """
        Initial all the element of the GUI,support by Tkinter

        :param tello: class interacts with the Tello drone.

        Raises:
            RuntimeError: If the Tello rejects the attempt to enter command mode.
        """        

        self.tello = tello # videostream device
        self.outputPath = outputpath # the path that save pictures created by clicking the takeSnapshot button 
        self.frame = None  # frame read from h264decoder and used for pose recognition 
        self.thread = None # thread of the Tkinter mainloop
        self.stopEvent = None

        # control variables
        self.distance = self.tello.distance  # default distance for 'move' cmd
        self.degree = self.tello.degree  # default degree for 'cw' or 'ccw' cmd

        # Auto Route
        self.auto_route = AutoRoute(self.tello)
        self.auto_route_thread = threading.Thread(target=self.auto_route.perimeter_sweep)

        # if the flag is TRUE,the auto-takeoff thread will stop waiting for the response from tello
        self.quit_waiting_flag = False

        # initialize the root window and image panel
        self.root = tki.Tk()
        self.panel = None

        # create buttons
        self.btn_snapshot = tki.Button(self.root, text="Snapshot!",
                                       command=self.takeSnapshot)
        self.btn_snapshot.pack(side="bottom", fill="both",
                               expand="yes", padx=10, pady=5)

        self.btn_pause = tki.Button(self.root, text="Pause", relief="raised", command=self.pauseVideo)
        self.btn_pause.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_manual = tki.Button(
            self.root, text="Open Command Window", relief="raised", command=self.openCmdWindow)
        self.btn_manual.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.btn_restart = tki.Button(
            self.root, text="Restart", relief="raised", command=self.restart)
        self.btn_restart.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)
        
        # start a thread that constantly pools the video sensor for
        # the most recently read frame
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.thread.start()

        # the sending_command will send command to tello every 5 seconds
        #self.sending_command_thread = threading.Thread(target=self._sendingCommand)

        # set a callback to handle when the window is closed
        self.root.wm_title("TELLO Controller")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

    def videoLoop(self):
        """
        The mainloop thread of Tkinter 
        Raises:
            RuntimeError: To get around a RunTime error that Tkinter throws due to threading.
        """
        self.tello.manual = False
        time.sleep(3)
        # self.sending_command_thread.start()
        self.auto_route_thread.start()
        try:
            # start the thread that get GUI image and drwa skeleton 
            time.sleep(0.5)
            while not self.stopEvent.is_set():
                system = platform.system()

            # read the frame for GUI show
                self.frame = self.tello.read()
                if self.frame is None or self.frame.size == 0:
                    continue 
            
            # transfer the format from frame to image         
                image = Image.fromarray(self.frame)

            # we found compatibility problem between Tkinter,PIL and Macos,and it will 
            # sometimes result the very long preriod of the "ImageTk.PhotoImage" function,
            # so for Macos,we start a new thread to execute the _updateGUIImage function.
                if system =="Windows" or system =="Linux":                
                    self._updateGUIImage(image)

                else:
                    thread_tmp = threading.Thread(target=self._updateGUIImage,args=(image,))
                    thread_tmp.start()
                    time.sleep(0.03)
        except RuntimeError, e:
            print("[INFO] caught a RuntimeError")

           
    def _updateGUIImage(self,image):
        """
        Main operation to initial the object of image,and update the GUI panel 
        """  
        image = ImageTk.PhotoImage(image)
        # if the panel none ,we need to initial it
        if self.panel is None:
            self.panel = tki.Label(image=image)
            self.panel.image = image
            self.panel.pack(side="left", padx=10, pady=10)
        # otherwise, simply update the panel
        else:
            self.panel.configure(image=image)
            self.panel.image = image

    def _setQuitWaitingFlag(self):  
        """
        set the variable as TRUE,it will stop computer waiting for response from tello  
        """       
        self.quit_waiting_flag = True
   
    def openCmdWindow(self):
        """
        open the cmd window and initial all the button and text
        """        
        panel = Toplevel(self.root)
        panel.wm_title("Command Panel")

        # create text input entry
        text0 = tki.Label(panel,
                          text='This Controller map keyboard inputs to Tello control commands\n'
                               'Adjust the trackbar to reset distance and degree parameter',
                          font='Helvetica 10 bold'
                          )
        text0.pack(side='top')

        text1 = tki.Label(panel, text=
                          'W - Move Tello Up\t\t\tArrow Up - Move Tello Forward\n'
                          'S - Move Tello Down\t\t\tArrow Down - Move Tello Backward\n'
                          'A - Rotate Tello Counter-Clockwise\t\tArrow Left - Move Tello Left\n'
                          'D - Rotate Tello Clockwise\t\t\tArrow Right - Move Tello Right',
                          justify="left")
        text1.pack(side="top")

        self.btn_landing = tki.Button(
            panel, text="Land", relief="raised", command=self.telloLanding)
        self.btn_landing.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.btn_takeoff = tki.Button(
            panel, text="Takeoff", relief="raised", command=self.telloTakeOff)
        self.btn_takeoff.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        # binding arrow keys to drone control
        self.tmp_f = tki.Frame(panel, width=100, height=2)
        self.tmp_f.bind('<KeyPress-w>', self.on_keypress_w)
        self.tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
        self.tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
        self.tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
        self.tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
        self.tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
        self.tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
        self.tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        self.tmp_f.pack(side="bottom")
        self.tmp_f.focus_set()

        self.btn_manual = tki.Button(
            panel, text="Activate Manual Mode", relief="raised", command=self.toggle_manual_mode)
        self.btn_manual.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.distance_bar = Scale(panel, from_=1, to=50, tickinterval=1, digits=2, label='Distance(m)',)
        self.distance_bar.set(self.distance)
        self.distance_bar.pack(side="left")

        self.btn_distance = tki.Button(panel, text="Set Distance", relief="raised",
                                       command=self.updateDistancebar,
                                       )
        self.btn_distance.pack(side="left", fill="both",
                               expand="yes", padx=10, pady=5)

        self.degree_bar = Scale(panel, from_=1, to=360, tickinterval=10, label='Degree',)
        self.degree_bar.set(self.degree)
        self.degree_bar.pack(side="right")

        self.btn_distance = tki.Button(panel, text="Set Degree", relief="raised", command=self.updateDegreebar)
        self.btn_distance.pack(side="right", fill="both",
                               expand="yes", padx=10, pady=5)
       
    def takeSnapshot(self):
        """
        save the current frame of the video as a jpg file and put it into outputpath
        """

        # grab the current timestamp and use it to construct the filename
        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))

        p = os.path.sep.join((self.outputPath, filename))

        # save the file
        cv2.imwrite(p, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))
        print("[INFO] saved {}".format(filename))


    def pauseVideo(self):
        """
        Toggle the freeze/unfreze of video
        """
        if self.btn_pause.config('relief')[-1] == 'sunken':
            self.btn_pause.config(relief="raised")
            self.tello.video_freeze(False)
        else:
            self.btn_pause.config(relief="sunken")
            self.tello.video_freeze(True)

    def telloTakeOff(self):
        return self.tello.takeoff()                

    def telloLanding(self):
        return self.tello.land()

    def updateDistancebar(self):
        self.distance = self.distance_bar.get()
        self.tello.set_distance(self.distance)
        print 'Set distance to %.1f' % self.distance

    def updateDegreebar(self):
        self.degree = self.degree_bar.get()
        self.tello.set_degree(self.degree)
        print 'Set distance to %d' % self.degree

    def on_keypress_w(self, event):
        self.tello.move_up(self.distance)

    def on_keypress_s(self, event):
        self.tello.move_down(self.distance)

    def on_keypress_a(self, event):
        self.tello.rotate_ccw(self.degree)

    def on_keypress_d(self, event):
        self.tello.rotate_cw(self.degree)

    def on_keypress_up(self, event):
        self.tello.move_forward(self.distance)

    def on_keypress_down(self, event):
        self.tello.move_backward(self.distance)

    def on_keypress_left(self, event):
        self.tello.move_left(self.distance)

    def on_keypress_right(self, event):
        self.tello.move_right(self.distance)

    def on_keypress_enter(self, event):
        if self.frame is not None:
            self.registerFace()
        self.tmp_f.focus_set()

    def toggle_manual_mode(self):
        if self.tello.manual:
            self.btn_manual.config(relief="raised")
            self.tello.move_back_to_perimeter_flag = True
            self.tello.back_to_perimeter_sweep()
        else:
            self.btn_manual.config(relief="sunken")
            self.tello.move_back_to_perimeter_flag = False
            self.tello.manual = True
            self.tello.stop()

    def restart(self):
        self.auto_route.restart()

    def _sendingCommand(self):
        """
        start a while loop that sends 'command' to tello every 5 second
        """
        while not self.stopEvent.is_set():
            self.tello.send('command', 0)
            time.sleep(5)

    def onClose(self):
        """
        set the stop event, cleanup the camera, and allow the rest of
        
        the quit process to continue
        """
        print("[INFO] closing...")
        self.auto_route.stop()
        self.stopEvent.set()
        del self.tello
        self.root.quit()

