# Defines the Experiment as a class
# @ Ladan Shahshahani Nov 2021

# import libraries
import os
import pandas as pd
import numpy as np
import math
import glob
import sys

from psychopy import visual, core, event, gui # data, logging

import experiment_code.constants as consts
from experiment_code.task_blocks import TASK_MAP
from experiment_code.ttl import ttl
from experiment_code.screen import Screen
from psychopy.hardware.emulator import launchScan
from psychopy.hardware import keyboard
import pylink as pl # to connect to eyelink

class Run():
    """
    A general class for a run of the task
    """

    def __init__(self, subject_id, screen_number = 1, eye_flag = False, **kwargs):
        """
        Args:
            subject_id : id set for the subject. Example: sub-01
            eye_flag : flag specifying whether you want to do eye tracking
            screen_number : number for the subject screen. 
                            Set to 1 when there are multiple monitors available
                            otherwise set to 0 (your laptop screen will be the subject screen)
        """

        self.subject_id = subject_id
        self.eye_flag = eye_flag
        self.__dict__.update(kwargs)

        # open up a screen and display fixation
        ## you can set the resolution of the subject screen here: (check screen code)
        self.subject_screen = Screen(screen_number = screen_number)

        # connect to the eyetracker already
        if self.eye_flag:
            # create an Eyelink class
            ## the default ip address is 100.1.1.1.
            ## in the ethernet settings of the laptop, 
            ## set the ip address of the EyeLink ethernet connection 
            ## to 100.1.1.2 and the subnet mask to 255.255.255.0
            self.tk = pl.EyeLink('100.1.1.1')
        
    def set_experiment_info(self, **kwargs):
        """
        setting the info for the experiment:

        Is it behavioral training?
        what is the run number?
        what is the subject_id?
        does it need to wait for ttl pulse? (for fmri it does)

        The following parameters will be set:
        behav_trianing  - is it behavioral training or scanning?
            ** behavioral training target/run files are always stored under behavioral and scanning files are under fmri  
        run_number      - run number 
        ttl_flag        - should the program wait for the ttl pulse or not? For scanning THIS FLAG HAS TO BE SET TO TRUE

        Args:
        debug (bool)    -   if True, uses default names and info for testing, otherwise, a dialogue box will pop up
        ** When debugging, most things are hard-coded. So you will need to change them here if you want to see how the code works
           for different values of these variables
        """
        if not kwargs['debug']:
            # a dialogue box pops up so you can enter info
            # set up input box
            inputDlg = gui.Dlg(title = f"{self.subject_id}")
            inputDlg.addField('Enter Run Number (int):')      # run number (int)
            inputDlg.addField('Is it a training session?', initial = True) # true for behavioral and False for fmri
            inputDlg.addField('Wait for TTL pulse?', initial = True) # a checkbox for ttl pulse (set it true for scanning)

            inputDlg.show()

            # record user inputs
            self.run_info = {}
            if gui.OK:
                self.run_info['subject_id']     = self.subject_id
                self.run_info['run_number']     = int(inputDlg.data[0])
                self.run_info['behav_training'] = bool(inputDlg.data[1])

                # ttl flag that will be used to determine whether the program waits for ttl pulse or not
                self.run_info['ttl_flag'] = bool(inputDlg.data[2])
                self.run_info['eye_flag'] = self.eye_flag

            else:
                sys.exit()
        else: 
            print("running in debug mode")
            # pass on the values for your debugging with the following keywords
            self.run_info = {
                'subject_id': 'test00',
                'run_number': 1,
                'behav_training': True,
                'ttl_flag': False, 
                'eye_flag': False
            }
            self.run_info.update(**kwargs)

        return
    def get_targetfile(self, run_number):
        """
        gets the target file information for the current run
        Args:
            run_number : number assigned to the current run
        Returns:
            target_taskInfo(dict)  -   a dictionary containing target file info for the task
                target_file    : target csv file opened as a pandas dataframe
        """
        # load the target file
        self.targetfile_run = pd.read_csv(consts.target_dir/ self.study_name / f"WMC_{run_number:02}.csv")
    def start_timer(self):
        """
        starts the timer for the experiment (for behavioral study)
        Returns:
            timer_info(dict)    -   a dictionary with all the info for the timer. keys are:
            global_clock : the clock from psychopy?
            t0           : the start time
        """
        #initialize a dictionary with timer info
        self.timer_info = {}

        # wait for ttl pulse or not?
        if self.ttl_flag: # if true then wait
            
            ttl.reset()
            while ttl.count <= 0:
                # print out the text to the screen
                ttl_wait_text = f"Waiting for the scanner\n"
                ttl_wait_ = visual.TextStim(self.stimuli_screen.window, text=ttl_wait_text, 
                                                pos=(0.0,0.0), color=self.stimuli_screen.window.rgb + 0.5, units='deg')
                ttl.check()
            
                ttl_wait_.draw()
                self.stimuli_screen.window.flip()

            # print(f"Received TTL pulse")
            # get the ttl clock
            self.timer_info['global_clock'] = ttl.clock
        else:
            self.timer_info['global_clock'] = core.Clock()
        
        self.timer_info['t0'] = self.timer_info['global_clock'].getTime()

    def start_eyetracker(self):
        """
        sets up a connection with the eyetracker and start recording eye position
        """
        
        # opening an edf file to store eye recordings
        ## the file name should not have too many characters (<=8?)
        ### get the run number
        self.tk_filename = f"{self.subject_id}_r{self.run_number}.edf"
        self.tk.openDataFile(self.tk_filename)
        # set the sampling rate for the eyetracker
        ## you can set it to 500 or 250 
        self.tk.sendCommand("sample_rate  500")
        # start eyetracking and send a text message to tag the start of the file
        self.tk.startRecording(1, 1, 1, 1)
        # pl.sendMessageToFile(f"task_name: {self.task_name} start_track: {pl.currentUsec()}")
        return
    def stop_eyetracker(self):
        """
        stop recording
        close edf file
        receive edf file?
            - receiving the edf file takes time and might be problematic during scanning
            maybe it would be better to take the edf files from eyelink host computer afterwards
        """
        self.tk.stopRecording()
        self.tk.closeDataFile()
        # self.tk.receiveDataFile(self.tk_filename, self.tk_filename)
        self.tk.close()
        return

    def check_run_results(self):
        """
        checks if there is a raw data file for the current run
        """
        pass
    def set_run_results(self, all_run_response, save = True):
        pass
    def show_scoreboard(self, screen):
        pass
    def init_run(self):
        pass
    def end_run(self):
        pass
    def wait_dur(self):
        pass
    def run(self):
        pass

class Task():
    def __init__(self) -> None:
        pass