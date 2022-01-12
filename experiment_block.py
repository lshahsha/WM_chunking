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

    def __init__(self, subject_id, screen_number = 1):
        """
        Args:
            subject_id : id set for the subject. Example: sub-01
            eye_flag : flag specifying whether you want to do eye tracking
            screen_number : number for the subject screen. 
                            Set to 1 when there are multiple monitors available
                            otherwise set to 0 (your laptop screen will be the subject screen)
        """

        self.subject_id = subject_id

        # open up a screen and display fixation
        ## you can set the resolution of the subject screen here: (check screen code)
        self.subject_screen = Screen(screen_number = screen_number)
    
    def get_run_results(self):
        """
        Checks if a file for behavioral data of the current run already exists
        """
        self.run_dir = consts.raw_dir / self.study_name / 'raw' / self.subject_id / f"WMC_{self.subject_id}.csv"
        if os.path.isfile(self.run_dir):
            # load in run_file results if they exist 
            self.run_file_results = pd.read_csv(self.run_dir)
        else:
            self.run_iter = 1
            self.run_file_results = pd.DataFrame()

        return
    
    def show_scoreboard(self):
        """
        Shows the final scoreboard for the run
        """

        # get the dataframe for the current run
        run_df = self.run_file_results.loc[self.run_file_results['run_number'] == self.run_number]

        # calculate median movement time
        # median_MT = run_df['MT'].median()
        # mode_MT = run_df['MT'].mode()
        mean_MT = run_df['MT'].mean()

        # calculate % correct
        percent_correct = (1 - ((run_df['is_error'].sum())/len(run_df.index)))*100

        # calculate total points for the current run
        total_points = run_df['points'].sum()

        # incorporating movement time into the pointing system
        ## if on average the movement time is below 8 seconds, double the points
        if mean_MT <= 8:
            total_points = total_points*2

        # display feedback
        feedback_string = f"Total points: {total_points}\n\n% correct {percent_correct:0.2f}\n\nMT {mean_MT:0.2f}"
        feedback_text = visual.TextStim(self.subject_screen.window, text = feedback_string, 
                                        color = 'black', pos = [0, 2], alignText = 'center')

        feedback_text.draw()
        self.subject_screen.window.flip()
    
    def init_run(self, debug = False, **kwargs):
        """
        initializing the run:
        Asking the user to input the run number
        Checking if there is already a file with the behavioural data for the subject
        Opening the target file for the current run
        """

        # get info from the user
        if not debug:
            # a dialogue box pops up so you can enter info
            # set up input box
            inputDlg = gui.Dlg(title = f"{self.subject_id}")
            inputDlg.addField('Enter Run Number (int):')      # run number (int)
            # inputDlg.addField('Is it a training session?', initial = True) # true for behavioral and False for fmri
        
            inputDlg.show()

            # record user inputs
            self.run_info = {}
            if gui.OK:
                self.run_info['subject_id']     = self.subject_id
                self.run_info['run_number']     = int(inputDlg.data[0])

            else:
                sys.exit()
        else: 
            print("running in debug mode")
            # pass on the values for your debugging with the following keywords
            self.run_info = {
                'subject_id': 'test00',
                'run_number': 1,
            }
            self.run_info.update(**kwargs)

        # defining new variables corresponding to experiment info (easier for coding)
        self.run_number = self.run_info['run_number'] 
        self.subject_id = self.run_info['subject_id']   
        self.study_name = 'behavioural'

        # make subject folder in data/raw/<subject_id>
        subject_dir = consts.raw_dir/ self.study_name / 'raw' / self.subject_id
        consts.dircheck(subject_dir) # making sure the directory is created!

        # load the target file
        ## the dataframe is read with index_col = [0] option to avoid the Unnamed: 0 column added to the dataframe
        self.targetfile_run = pd.read_csv(consts.target_dir/ self.study_name / f"WMC_{self.run_number:02}.csv", index_col=[0])
   
    def end_run(self):
        """
        finishes the run.
        converting the log of all responses to a dataframe and saving it
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
            # quit screen and exit
            self.subject_screen.window.close()
            core.quit()
    
    def do(self, debug = False):
        """
        do a run of the experiment
        """
        print(f"running the experiment")
        
        # initialize the run
        self.init_run(debug = debug)

        # create an instance of the task object
        Task_obj = WMChunking(screen = self.subject_screen, 
                              target_file = self.targetfile_run,
                              study_name = 'behavioural', 
                              run_number = self.run_number, 
                              save_response = False)

        # run the task
        Task_obj.run()

        # check if run file results already exists
        ## load it if it exists
        self.get_run_results()

        # append the results of the current run 
        self.run_file_results = pd.concat([self.run_file_results, Task_obj.response_df], axis = 0)

        # save the results
        self.run_file_results.to_csv(self.run_dir, index = False)

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
        # reset the timer
        self.clock.reset()
        # initialize some variables
        self.trial_points    = 0     # the number of points the participant gets for the trial
        self.is_error        = False # will set to True only if no error is made
        self.response        = []    # will contain the pressed keys
        self.response_time   = []    # will contain the times of presses
        self.number_response = 0     # will contain the number of presses made. Each time a press is detected, this is incremented
        self.number_correct  = 0     # will be the numbere of correct ore
        # self.movement_time  = []    # will contain the movement time of the trial

        # get the current trial
        self.current_trial = self.target_file.loc[self.trial_index]

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
            while self.clock.getTime()-self.chunkStartTime <= (self.item_dur):
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
            # while self.clock.getTime()-self.chunkEndTime <= (0.5):
            #     pass

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

                    # if all the digits are retrieved correctly, 
                    # participant recieves extra points:
                    if self.number_correct == self.seq_length:
                        self.trial_points = 10

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
            print(self.trial_response)

            self.trial_response['response']       = [self.response]
            self.trial_response['response_time']  = [self.response_time]
            self.trial_response['MT']             = movement_time
            self.trial_response['is_error']       = self.is_error
            self.trial_response['number_correct'] = self.number_correct
            self.trial_response['points']         = self.trial_points

            # add the trial index as the first column
            self.trial_response.insert(loc = 0, column='TN', value=self.trial_index)
            
            self.response_df = pd.concat([self.response_df, self.trial_response])

            # STATE: show feedback
            if self.display_trial_feedback:
                # feedback is only shown if this flag is set to True in the target file
                self.show_trial_feedback()

            # STATE: ITI
            self.wait_iti()

# do a run of the experiment
def main(subject_id, debug = False):
    Run_Block = Run(subject_id = subject_id)
    Run_Block.do(debug = debug)