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

import constants as consts
from screen import Screen
from psychopy.hardware.emulator import launchScan
from psychopy.hardware import keyboard
import pylink as pl # to connect to eyelink

class Run():
    """
    A general class for a run of the task
    """

    def __init__(self, subject_id, screen_number = 1, 
                 run_number = 1, eye_flag = False, **kwargs):
        """
        Args:
            subject_id : id set for the subject. Example: sub-01
            eye_flag : flag specifying whether you want to do eye tracking
            screen_number : number for the subject screen. 
                            Set to 1 when there are multiple monitors available
                            otherwise set to 0 (your laptop screen will be the subject screen)
        """

        self.subject_id = subject_id
        self.run_number = run_number
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
        # self.targetfile_run = pd.read_csv(consts.target_dir/ self.study_name / f"WMC_{run_number:02}.csv")
        self.targetfile_run = pd.read_csv(consts.target_dir/ self.study_name / f"ENC_01.csv")

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
        Checks if a file for behavioral data of the current run already exists
        Args:
            experiment_info(dict)   -   a dictionary with all the info for the experiment (after user inputs info in the GUI)
        Returns:
            run_iter    -   how many times this run has been run:)
        """
        self.run_dir = consts.raw_dir / self.study_name / 'raw' / self.subj_id / f"{self.study_name}_{self.subj_id}.csv"
        if os.path.isfile(self.run_dir):
            # load in run_file results if they exist 
            self.run_file_results = pd.read_csv(self.run_dir)
            if len(self.run_file_results.query(f'run_name=="{self.run_name}"')) > 0:
                current_iter = self.run_file_results.query(f'run_name=="{self.run_name}"')['run_iter'].max() # how many times has this run_file been executed?
                self.run_iter = current_iter+1
            else:
                self.run_iter = 1 
        else:
            self.run_iter = 1
            self.run_file_results = pd.DataFrame()

        return
        
        pass
    
    def set_run_results(self, all_run_response, save = True):
        """
        gets the behavioral results of the current run and returns a dataframe to be saved
        Args:
            all_run_response(list)    -   list of dictionaries with behavioral results of the current run
            save(bool)                -   if True, saves the run results. Default: True
        Returns:
            run_file_results(pandas dataframe)    -   a dataframe containing behavioral results
        """

        # save run results 
        new_df = pd.concat([self.run_info['run_file'], pd.DataFrame.from_records(all_run_response)], axis=1)

        # check if a file with results for the current run already exists
        self.check_runfile_results()
        self.run_file_results = pd.concat([self.run_file_results, new_df], axis=0, sort=False)

        # save the run results if save is True
        if save:
            self.run_file_results.to_csv(self.run_dir, index=None, header=True)

        return
    
    def show_scoreboard(self, screen):
        pass
    
    def init_run(self):
        """
        initializing the run:
        making sure a directory is created for the behavioral results
        getting run file
        opening a screen to show the stimulus
        starting the timer
        """

        # defining new variables corresponding to experiment info (easier for coding)
        self.run_number = self.run_info['run_number'] 
        self.subject_id = self.run_info['subject_id']   
        self.ttl_flag   = self.run_info['ttl_flag']
        self.eye_flag   = self.run_info['eye_flag']

        # if it's behavioral training then use the files under behavioral
        if self.run_info['behav_training']:
            self.study_name = 'behavioural'
        else:
            self.study_name = 'fmri'

        # 1. get the target file for the current run
        self.get_targetfile(self.run_number)

        # 2. make subject folder in data/raw/<subj_id>
        subject_dir = consts.raw_dir/ self.study_name / 'raw' / self.subject_id
        consts.dircheck(subject_dir) # making sure the directory is created!

        # 3. check if a file for the result of the run already exists
        # self.check_runfile_results()

        # 5. start the eyetracker if eyeflag = True
        if self.eye_flag:
            self.start_eyetracker()

        # 5. timer stuff!
        ## start the timer. Needs to know whether the experimenter has chosen to wait for ttl pulse 
        ## creates self.timer_info
        self.start_timer()

        # 6. initialize a list for responses
        self.all_run_response = []
   
    def end_run(self):
        """
        finishes the run.
        converting the log of all responses to a dataframe and saving it
        showing a scoreboard with results from all the tasks
        showing a final text and waiting for key to close the stimuli screen
        """

        self.set_runfile_results(self.all_run_response, save = True)

        # present feedback from all tasks on screen 
        self.show_scoreboard(self.task_obj_list, self.stimuli_screen)

        # stop the eyetracker
        if self.eye_flag:
            self.stop_eyetracker()
            # get the edf file from Eyelink PC
            self.tk.receiveDataFile(self.tk_filename, self.tk_filename)

        # end experiment
        end_exper_text = f"End of run\n\nTake a break!"
        end_experiment = visual.TextStim(self.stimuli_screen.window, text=end_exper_text, color=[-1, -1, -1])
        end_experiment.draw()
        self.stimuli_screen.window.flip()

        # waits for a key press to end the experiment
        # event.waitKeys()
        # Make keyboard object
        kb = keyboard.Keyboard()
        # Listen for keypresses until escape is pressed
        keys = kb.getKeys()
        if 'space' in keys:
            # quit screen and exit
            self.stimuli_screen.window.close()
            core.quit()
    def wait_dur(self):
        pass
    def do(self):
        """
        do a run of the experiment
        """
        print(f"running the experiment")
        
        # initialize the run
        self.init_run()

        # create an instance of the task object
        Task_obj = WMChunking(screen = self.subject_screen, 
                        target_file = self.targetfile_run,
                        study_name = 'behavioural', 
                        save_response = False)

        # run the task
        Task_obj.run()

class WMChunking():
    """
    Creates an instance of WMChunking class
    The Run class creates an instance of WMChunking with the proper attributes
    Args:
        screen        : subject screen
        target_file   : the target file containing trial information for a run of the task
        study_name    : either 'behavioural' or 'fmri'
        save_response : whether you want to save the responses into a file
    """
    def __init__(self, screen, target_file, 
                 study_name, save_response = True):
        
        self.screen         = screen
        self.window         = screen.window
        self.monitor        = screen.monitor
        self.clock          = core.Clock()
        self.save_response  = save_response
        self.target_file    = target_file
        self.study_name     = study_name
        self.trial_response = {} # a dictionary with the responses for all of the trials
        self.run_response   = []

        # overall points and errors????

    # ==================================================
    # helper functions used in main functions for states
    def _create_chunked_str(self, seq_str, chunk):
        """
        creates a chunked version of the sequence to be displayed
        is used in display_digits routine
        """
        # get the digits of the sequence
        ## in the target file they were separated by spaces
        seq_list = seq_str.split(" ")

        seq_chunked_list = [] # a list containing chunked seq as strings
        for i in range(0, len(seq_list), chunk):
            # separate the chunk
            seq_chunked     = seq_list[i:i+chunk]
            # put the digits of the chunk together
            seq_chunked_str = ''.join(seq_chunked)
            # append the chunk to the list
            seq_chunked_list.append(seq_chunked_str)

        return seq_chunked_list
    # ==================================================

    def get_current_trial_time(self):
        """
        gets the current time in the trial.
        """
        # gets the current time in the trial
        t_current = self.clock.getTime()
        return t_current
    
    def display_digits(self):
        """
        displays the digits during encoding phase
        Chunks will be displayed stay on the screen for a certain amount of time
        and then get masked (turn into *)
        info from the target file this routine needs:
            chunk (2 or 3)
            seq_str (string representing digits)
            trial_dur?
            item_dur (time duration that a memory item remains on the screen)
        """
        # create a list with all the digits
        ## digits are separated by space 
        seq_str  = self.current_trial['seq_str']
        chunk    = self.current_trial['chunk']
        item_dur = self.current_trial['item_dur']

        # separate chunks
        ## create a list rep of the seq string
        seq_chunked_list = self._create_chunked_str(seq_str, chunk)

        # create a chunked masked string
        chunk_masked_str = '*' * int(chunk)

        # loop over chunks and display
        ## initialize stuff
        self.seq_text_obj = [] 
        ch_idx = 0 # chunk index
        x_pos = 5 # starting x position for the the sequence. The position is chosen so that the seq is centered on the display
        text_str = '' # initialize a string to be displayed
        text_masked_str = '' # initialize a string to contain masked digits
        for ch in seq_chunked_list:
            text_str = text_masked_str+ch
            # get the current time in the trial
            self.chunk_startTime = self.get_current_trial_time()

            # display each chunk
            self.seq_text_obj.append(visual.TextStim(self.window, text = text_str, 
                                                     color = [-1, -1, -1], height = 2, 
                                                     pos = [x_pos, 0], alignText = 'left'))
            self.seq_text_obj[ch_idx].draw()
            self.window.flip()
            # let it remain on the screen for "item_dur"
            while self.clock.getTime()-self.chunk_startTime <= item_dur:
                pass

            # convert all the elements to * and display
            text_masked_str = text_masked_str + chunk_masked_str
            self.seq_text_obj[ch_idx] = visual.TextStim(self.window, text = text_masked_str, 
                                                     color = [-1, -1, -1], height = 2, 
                                                     pos = [x_pos, 0], alignText = 'left')
            self.seq_text_obj[ch_idx].draw()
            self.window.flip()

            # change chunk index and x_pos for the next chunk
            ch_idx = ch_idx + 1

    def wait_iti(self):
        """
        duration of the inter-trial interval
        Waits here for the iti duration
        """
        # get the iti
        iti_dur = self.current_trial['iti_dur']
        # get the current time in the trial
        ## gets here for ITIs so the time corresponds to the end of an event
        self.iti_startTime = self.get_current_trial_time()

        # wait here for the duration of the iti
        while self.clock.getTime()-self.iti_startTime <= iti_dur:
            pass

    def get_response():
        """
        recording the subjects' responses during retrieval
        Shows the masked digits
        Shows recall direction
        record pressed keys, press times, reaction time
        """
        pass
    
    def show_trial_feedback():
        """
        shows trial feedback
        Number of points subject gets during the trial:
            Points are determined based on total number of current digits:
            +6 (6 correct digits)
            +5 (5 correct digits)
            .
            .
            .
        """
        pass
    
    def run(self):
        """
        runs the task
        get the trials from target file and loop over trials
        """
        # initialize a list to collect responses from all trials
        self.all_trial_response = []

        # loop over trials
        for self.trial_index in self.target_file.index:
            
            # get info for the current trial
            self.current_trial = self.target_file.iloc[self.trial_index]

            # STATE: encoding: show digits
            self.display_digits()

            # STATE: ITI
            self.wait_iti()

            # STATE: retrieval: record responses

            # STATE: show trial feedback

            # STATE: ITI
