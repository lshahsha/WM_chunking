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
from psychopy import core
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
        # self.eye_flag = eye_flag
        self.__dict__.update(kwargs)

        # open up a screen and display fixation
        ## you can set the resolution of the subject screen here: (check screen code)
        self.subject_screen = Screen(screen_number = screen_number)

        # # connect to the eyetracker already
        # if self.eye_flag:
        #     # create an Eyelink class
        #     ## the default ip address is 100.1.1.1.
        #     ## in the ethernet settings of the laptop, 
        #     ## set the ip address of the EyeLink ethernet connection 
        #     ## to 100.1.1.2 and the subnet mask to 255.255.255.0
        #     self.tk = pl.EyeLink('100.1.1.1')
        
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
            # inputDlg.addField('Is it a training session?', initial = True) # true for behavioral and False for fmri
            # inputDlg.addField('Wait for TTL pulse?', initial = True) # a checkbox for ttl pulse (set it true for scanning)

            inputDlg.show()

            # record user inputs
            self.run_info = {}
            if gui.OK:
                self.run_info['subject_id']     = self.subject_id
                self.run_info['run_number']     = int(inputDlg.data[0])
                # self.run_info['behav_training'] = bool(inputDlg.data[1])

                # # ttl flag that will be used to determine whether the program waits for ttl pulse or not
                # self.run_info['ttl_flag'] = bool(inputDlg.data[2])
                # self.run_info['eye_flag'] = self.eye_flag

            else:
                sys.exit()
        else: 
            print("running in debug mode")
            # pass on the values for your debugging with the following keywords
            self.run_info = {
                'subject_id': 'test00',
                'run_number': 1,
                # 'behav_training': True,
                # 'ttl_flag': False, 
                # 'eye_flag': False
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
        # self.targetfile_run = pd.read_csv(consts.target_dir/ self.study_name / f"ENC_01.csv")

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

        # # wait for ttl pulse or not?
        # if self.ttl_flag: # if true then wait
            
        #     ttl.reset()
        #     while ttl.count <= 0:
        #         # print out the text to the screen
        #         ttl_wait_text = f"Waiting for the scanner\n"
        #         ttl_wait_ = visual.TextStim(self.stimuli_screen.window, text=ttl_wait_text, 
        #                                         pos=(0.0,0.0), color=self.stimuli_screen.window.rgb + 0.5, units='deg')
        #         ttl.check()
            
        #         ttl_wait_.draw()
        #         self.stimuli_screen.window.flip()

        #     # print(f"Received TTL pulse")
        #     # get the ttl clock
        #     self.timer_info['global_clock'] = ttl.clock
        # else:
        #     self.timer_info['global_clock'] = core.Clock()
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
        self.run_dir = consts.raw_dir / self.study_name / 'raw' / self.subject_id / f"WMC_{self.subject_id}.csv"
        if os.path.isfile(self.run_dir):
            # load in run_file results if they exist 
            self.run_file_results = pd.read_csv(self.run_dir)
        else:
            self.run_iter = 1
            self.run_file_results = pd.DataFrame()

        return
    
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
    
    def show_scoreboard(self):

        # get the dataframe for the current run
        run_df = self.run_file_results.loc[self.run_file_results['run_number'] == self.run_number]

        # calculate median movement time
        median_MT = run_df['MT'].median()

        # calculate % correct
        percent_correct = (1 - ((run_df['is_error'].sum())/len(run_df.index)))*100

        # display feedback
        feedback_string = f"% correct {percent_correct:0.2f}\n\nMT {median_MT:0.2f}"
        feedback_text = visual.TextStim(self.subject_screen.window, text = feedback_string, 
                                        color = 'black', pos = [0, 2], alignText = 'center')

        feedback_text.draw()
        self.subject_screen.window.flip()
    
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
        # self.ttl_flag   = self.run_info['ttl_flag']
        # self.eye_flag   = self.run_info['eye_flag']

        # if it's behavioral training then use the files under behavioral
        # if self.run_info['behav_training']:
        #     self.study_name = 'behavioural'
        # else:
        #     self.study_name = 'fmri'
        self.study_name = 'behavioural'

        # 1. get the target file for the current run
        self.get_targetfile(self.run_number)

        # 2. make subject folder in data/raw/<subj_id>
        subject_dir = consts.raw_dir/ self.study_name / 'raw' / self.subject_id
        consts.dircheck(subject_dir) # making sure the directory is created!

        # 3. check if a file for the result of the run already exists
        # self.check_runfile_results()

        # # 5. start the eyetracker if eyeflag = True
        # if self.eye_flag:
        #     self.start_eyetracker()

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
        # end experiment
        # end_exper_text = f"End of run\n\nTake a break!"
        # end_experiment = visual.TextStim(self.subject_screen.window, text=end_exper_text, color=[-1, -1, -1])
        # end_experiment.draw()
        # self.subject_screen.window.flip()

        # waits for a key press to end the experiment
        event.waitKeys()
        # Make keyboard object
        kb = keyboard.Keyboard()
        print(f"ending the run")
        # Listen for keypresses until escape is pressed
        keys = kb.getKeys()
        if 'space' in keys:
            # print(f"quiting")
            # quit screen and exit
            self.subject_screen.window.close()
            core.quit()
    
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
                              run_number = self.run_number, 
                              save_response = False)

        # run the task
        Task_obj.run()

        # check if run file results already exists
        self.check_run_results()

        # append the results of the current run 
        self.run_file_results = pd.concat([self.run_file_results, Task_obj.response_df], axis = 0)

        # save the results
        self.run_file_results.to_csv(self.run_dir)

        # show scoreboard
        self.show_scoreboard()

        # end the run
        self.end_run()

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
    def __init__(self, screen, target_file, run_number, 
                 study_name, save_response = True):
        
        self.screen         = screen
        self.window         = screen.window
        self.monitor        = screen.monitor
        self.clock          = core.Clock()
        self.save_response  = save_response
        self.target_file    = target_file
        self.study_name     = study_name
        self.trial_response = {} # a dictionary with the responses for all of the trials
        self.run_number     = run_number
        self.run_response   = []

        # overall points and errors????

    # ==================================================
    # helper functions used in main functions for states
    def _create_chunked_seq(self):
        """
        creates a chunked version of the sequence to be displayed
        is used in display_digits routine
        """
        # get the digits of the sequence
        ## in the target file they were separated by spaces
        seq_list = self.seq_str.split(" ")
        # create a variable containing correct presses
        ## this will be used later in the retrieval routine
        self.seq_correct = seq_list.copy()

        self.seq_chunked_list = [] # a list containing chunked seq as strings
        for i in range(0, len(seq_list), self.chunk):
            # separate the chunk
            seq_chunked     = seq_list[i:i+self.chunk]
            # put the digits of the chunk together
            seq_chunked_str = ' '.join(seq_chunked)
            # append the chunk to the list
            self.seq_chunked_list.append(seq_chunked_str)
        return 
    # ==================================================

    def init_trial(self):
        """
        initialize the trial
        gets all the necessary information for the current trial
        """
        # initialize some variables
        self.trial_points    = 0     # the number of points the participant gets for the trial
        self.is_error        = False # will set to True only if no error is made
        self.response        = []    # will contain the pressed keys
        self.response_time   = []    # will contain the times of presses
        self.number_response = 0     # will contain the number of presses made. Each time a press is detected, this is incremented
        self.number_correct  = 0     # will be the numbere of correct ore
        # self.movement_time  = []    # will contain the movement time of the trial

        # get the current trial
        self.current_trial = self.target_file.iloc[self.trial_index]

        # get info for the current trial
        self.item_dur     = self.current_trial['item_dur']
        self.iti_dur      = self.current_trial['iti_dur']
        self.run_number   = self.current_trial['run_number']
        self.phase_type   = self.current_trial['phase_type']
        self.feedback_dur = self.current_trial['feedback_dur']
        self.seq_length   = self.current_trial['seq_length']
        self.chunk        = self.current_trial['chunk']
        self.recall_dir   = self.current_trial['recall_dir']
        self.trial_dur    = self.current_trial['trial_dur']
        self.seq_str      = self.current_trial['seq_str']
        self.seq_list     = self.seq_str.split(" ")

        self.display_trial_feedback = self.current_trial['display_trial_feedback']

    def get_current_trial_time(self):
        """
        gets the current time in the trial.
        """
        # gets the current time in the trial
        t_current = self.clock.getTime()
        return t_current
    
    def phase_encoding(self):
        """
        gets here during the encoding phase
        1. display a big box (rectangular):
            - encloses the sequence
            - It's colored red (red to instruct the subject not to press anything!)
        2. display chunks
            - determine the chunks first
            - loop over chunks:
                - show the chunk
                - the chunk remains on the screen for a certain amount of time
                - mask the chunk
                - a short delay before the next chunk appears? 
        """

        # Create a rectangle that will enclose the sequence of digits
        self.rect_frame = visual.rect.Rect(self.window, width = 8, height = 2, 
                                           lineWidth = 1, lineColor = 'red', 
                                           pos = [0, 0])
        # Divide the sequence into chunks
        ## once this routine is executed, self.seq_chunked_str is created
        self._create_chunked_seq()

        # Loop over chunks
        self.text_object = []
        x_pos            = 0
        chunk_index      = 0
        text_str         = '' # text string that will be shown
        text_masked_str  = '' # text string containing masked digist
        for chunk in self.seq_chunked_list:
            # display the current chunk
            self.chunkStartTime = self.get_current_trial_time()
            text_str    = text_masked_str + chunk
            text_object = visual.TextStim(self.window, text = text_str, 
                                          color = 'black', pos = [5, 0], alignText = 'left') 

            self.rect_frame.draw()
            text_object.draw()
            self.window.flip(clearBuffer = True)

            # keep it on the screen for item_dur
            while self.clock.getTime()-self.chunkStartTime <= (self.item_dur - 0.5):
                pass
            
            # Change it to masked 
            text_masked_str = text_masked_str + '# '*int(self.chunk)
            text_object = visual.TextStim(self.window, text = text_masked_str, 
                                          color = 'black', pos = [5, 0], alignText = 'left')
            self.rect_frame.draw() 
            text_object.draw()
            self.window.flip(clearBuffer = True)
            # a short delay
            self.chunkEndTime = self.get_current_trial_time()
            while self.clock.getTime()-self.chunkEndTime <= (0.5):
                pass

    def phase_retrieval(self):
        """
        gets here during the retrieval phase
        1. change the color of the big box to green 
        2. draw a box (blue/yellow) to the left of the big box
            - this box determines whether it's backwards or forwards recall
        3. show the masked sequence of digits
        4. records and check responses made: response, response_time
            - an immediate feedback is given based on the response 
                correct response: green
                wrong response: red
        """

        # change the color of the big box to green
        self.rect_frame.lineColor = 'green'

        # create a filled box to instruct the recall direction
        if self.recall_dir == 0: # backwards recall
            box_color = 'blue'
        elif self.recall_dir == 1: # forwards recall
            box_color = 'yellow'
            
        self.rect_rd = visual.rect.Rect(self.window, width = 2, height = 2, 
                                        lineWidth = 1, lineColor = box_color, 
                                        fillColor = box_color, 
                                        pos = [-5, 0])

        # # display the masked sequence
        # text_seq_object = visual.TextStim(self.window, text = self.seq_str, 
        #                                   color = 'black', pos = [5, 0], alignText = 'left')

        # flip the sequence if it's a backwards condition
        if self.recall_dir == 0:
            self.seq_correct.reverse()

        # create text objects for each element in the sequence
        xpos = 5 # initial x position for the text
        idx  = 0 # index within the sequence
        self.seq_text_object = []
        for item in self.seq_list:
            # create a text object for each element within the sequence
            self.seq_text_object.append(visual.TextStim(self.window, text = item, 
                                        color = 'black', pos = [xpos, 0], alignText = 'left'))
            self.seq_text_object[idx].draw()
            idx +=1
            xpos = xpos + 0.855 # this floating point number was determined by trial and error
            self.rect_frame.draw()
            self.rect_rd.draw()

        self.window.flip(clearBuffer = True)

        # while the sequence is not finished, wait for responses from the subject
        while self.number_response<self.seq_length:
            # record presses
            press = event.getKeys(timeStamped=self.clock) # records the pressed key
            if len(press)>0: # a press has been made`
                # self.pressed_digits.append(self._get_press_digit(press[0][0])) # the pressed key is converted to its corresponding digit and appended to the list
                self.response.append(press[0][0]) # get the pressed key
                self.response_time.append(press[0][1])  # get the time of press for the key

                # seq_index is defined to handle the backwards conditions
                ## in backwards conditions, the color change (based on response)
                ## starts from the right
                if self.recall_dir == 0: # if it is a backwards recall
                    self.seq_index = self.seq_length - self.number_response - 1
                elif self.recall_dir == 1: # if it is a forwards recall
                    self.seq_index = self.number_response
                
                try:
                    if self.response[self.number_response] == self.seq_correct[self.number_response]: # the press is correct
                        self.number_correct = self.number_correct + 1
                        self.trial_points  += 1
                        
                        item_color = 'green'
                    else: # the press is incorrect
                        # at least one wrong press is made and the trial is considered ERROR
                        self.is_error = True

                        item_color = 'red'
                    # changing the color based on the response:
                    ## correct: green
                    ## wrong: red
                    self.seq_text_object[self.seq_index].setColor(item_color)
                    self.seq_text_object[self.seq_index].draw()
                    for obj in self.seq_text_object:
                        obj.draw()
                        self.rect_frame.draw()
                        self.rect_rd.draw()
                    self.window.flip(clearBuffer = True)
                except IndexError: # if the number of presses exceeds the length of the threshold
                    self.correct_response = False
                finally:
                    self.number_response = self.number_response + 1 # a press has been made => increase the number of presses
    
    def show_trial_feedback(self):
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
        # display the trial feedback
        trial_feedback = visual.TextStim(self.window, text = f"+{self.trial_points}", 
                                        color = 'black', pos = [0, 0])

        # keep the feedbacl on the screen
        trial_feedback.draw()
        self.rect_frame.draw()
        self.rect_rd.draw()
        self.window.flip(clearBuffer = True)

        feedback_startTime = self.get_current_trial_time() # get the time before iti starts
        while self.clock.getTime()-feedback_startTime <= self.iti_dur:
            # stays here for the duration of the feedback_dur
            pass
    
    def wait_iti(self):
        """
        waits here for the duration of iti
        """
        iti_startTime = self.get_current_trial_time() # get the time before iti starts
        while self.clock.getTime()-iti_startTime <= self.feedback_dur:
            # stays here for the duration of the iti
            pass

    def run(self):
        """
        runs the task
        get the trials from target file and loop over trials
        """
        # initialize a list to collect responses from all trials
        self.all_trial_response = []
        self.response_df = pd.DataFrame()

        # loop over trials
        for self.trial_index in self.target_file.index:
            
            print(f"trial number {self.trial_index}")
            # get info for the current trial
            self.init_trial()

            if self.phase_type == 0: # encoding
                # STATE: encoding: show digits
                self.phase_encoding()
                movement_time = 0 # no press/movement is made
            elif self.phase_type == 1: # retrieval
                # STATE: retrieval: record responses
                self.phase_retrieval()
                # calculate movement time: time beteween first and last press
                movement_time = self.response_time[-1] - self.response_time[0]

            # append the recorded responses to the datafarme for the trial
            self.trial_response = self.current_trial.to_frame().T

            self.trial_response['response']       = [self.response]
            self.trial_response['response_time']  = [self.response_time]
            self.trial_response['MT']             = movement_time
            self.trial_response['run_number']     = self.run_number
            self.trial_response['is_error']       = self.is_error
            self.trial_response['number_correct'] = self.number_correct

            self.response_df = pd.concat([self.response_df, self.trial_response])

            # STATE: show feedback
            if self.display_trial_feedback:
                # feedback is only shown if this flag is set to True in the target file
                self.show_trial_feedback()

            # STATE: ITI
            self.wait_iti()