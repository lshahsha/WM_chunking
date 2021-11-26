# Create target file for different tasks
# @ Ladan Shahshahani  - Nov. 2021
import pandas as pd
import numpy as np
import random
from itertools import product
import constants as consts


class WMChunking():

    def __init__(self, num_repetition = 5, iti_dur = [1, 1], item_dur = 2, 
                 run_number = 1, study_name = 'behavioural', 
                 feedback_dur = [0, 0.5], hand = 'right', seq_length = 6):
        """
        class for the WMChunking task target file
        Args:
            num_repetition : number of times you want each trial type to be repeated
            iti_dur : inter trial interval. enter as a list: [<iti after encoding> <iti after retrieval>]
            run_number : number of the run (different target files will be used for different runs)
            study_name : 'behavioural' or 'fmri' ('fmri' is UNDER RECONSTRUCTION!)
            feedback_dur : time interval during which feedback is displayed. Enter as a list: [<feedback_dur after encoding> <feedback dur after retrieval>]
            hand : hand used in the experiment (DEFAULT: right)
            seq_length : length of the sequence (DEFAULT: 6)
            item_dur : duration of time a "memory" item remains on the screen (DEFAULT: 1)
        """

        self.num_repetition = num_repetition 
        self.iti_dur = iti_dur 
        self.feedback_dur = feedback_dur 
        self.study_name = study_name 
        self.run_number = run_number
        self.hand = hand
        self.seq_length = seq_length
        self.item_dur = item_dur

        # create an empty dataframe 
        self.target_df = pd.DataFrame()

        # trial_type stuff
        self.chunk = [2, 3]
        self.recall_dir = [0, 1]

        self.num_trial_unique = len(self.chunk) * len(self.recall_dir)
        self.num_trials_total = self.num_trial_unique * self.num_repetition

        ## Creating a list of dictionaries with dicts of all pairs
        self.seq_dict_list = [dict(zip(('recall_dir', 'chunk'), (i,j))) for i,j in product(self.recall_dir, self.chunk)]

        # file naming stuff
        self.target_filename = f"WMC_{self.run_number:02d}"
        self.target_dir      = consts.target_dir / self.study_name

        self.target_filedir = self.target_dir / f"{self.target_filename}.csv"

    def generate_random_seq(self):
        """
        generates a random sequence of digits
        """
        self.seq_list = []
        for i in range(self.seq_length):
            self.seq_list.append(str(random.randint(1, 4)))
        
        # concatenate the digits into one string without any spaces in between
        self.seq_str = ' '.join(self.seq_list)
    
    def generate_masked_seq(self):
        """
        generates masked sequence
        """

        # first generate the whole sequence
        self.seq_masked = '#' * self.seq_length
        self.seq_masked = ' '.join(self.seq_masked)

    def make_trials(self):

        # create an array for unique trials repeated
        # the numbers within trials_unique are used to pick 
        # trial_type for each trial
        self.trials_unique = np.tile(np.arange(1, self.num_trial_unique+1), [self.num_repetition])
        ## randomly shuffle the trial types
        # np.random.shuffle(self.trials_unique)
        self.trials = random.sample(list(self.trials_unique), self.num_trials_total)

        for trial_number in range(len(self.trials)):
            # initialize a dictionary with the trial info as keys
            # NOTE: we have pairs of trials: "encoding" followed by "retrieval"
            # info for a pair is added simoultaneously
            self.trial_dict = {}

            self.trial_dict['hand'] = [self.hand for i in range(2)]
            self.trial_dict['item_dur'] = [self.item_dur for i in range(2)]
            self.trial_dict['iti_dur'] = self.iti_dur
            self.trial_dict['run_number'] = self.run_number
            self.trial_dict['phase_type'] = [0, 1]
            self.trial_dict['phase'] = ['enc', 'ret'] # enc for encoding and ret for retrieval
            self.trial_dict['display_trial_feedback'] = [False, True]
            self.trial_dict['feedback_dur'] = self.feedback_dur
            self.trial_dict['feedback_type'] = ['None', 'acc']
            self.trial_dict['seq_length'] = [self.seq_length for i in range(2)]

            # get the type of the current trial
            trial_type_id = self.trials[trial_number]
            ## now use the trial_type_id to get the trial_type (chunk and recall_dir) from the dictionary
            trial_type = self.seq_dict_list[trial_type_id-1] # 1 is subtracted because indices in python start from 0
            # add the info to the dictionary
            self.trial_dict['chunk'] = [trial_type['chunk'] for i in range(2)]
            self.trial_dict['recall_dir'] = [trial_type['recall_dir'] for i in range(2)]
            
            # calculate trial duration
            trial_dur = trial_type['chunk'] * self.item_dur
            self.trial_dict['trial_dur'] = [trial_dur, 'None']

            # generate a sequence of random numbers
            ## once the following routine is executed, self.seq_list, self.seq_str are created
            self.generate_random_seq()
            ## add self.seq_str to the trial dictionary
            self.trial_dict['seq_str'] = []
            self.trial_dict['seq_str'].append(self.seq_str) # for the encoding phase

            # generate a sequence masked
            self.generate_masked_seq()
            self.trial_dict['seq_str'].append(self.seq_masked) # for the retrieval phase

            # add the info to the target dataframe
            trial_df = pd.DataFrame(self.trial_dict)
            self.target_df = self.target_df.append(trial_df, ignore_index=True)
        return

    def save_target_file(self):
        """
        save the target file in the corresponding directory
        """
        consts.dircheck(self.target_dir)
        self.target_df.to_csv(self.target_filedir)

def make_files(number_of_runs = 8):
    """
    make target files for each run
    Args:
    number_of_runs : number of runs (target files) you want to create
    """

    for r in range(1, number_of_runs + 1):
        Task_run = WMChunking(run_number = r)
        # make trials and fill in the target dataframe
        Task_run.make_trials()
        # save the target file for the current run
        Task_run.save_target_file()