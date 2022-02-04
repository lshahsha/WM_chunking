# import libraries
from pathlib import Path
import os

# default response keys and the corresponding fingers. Can be modified
## first enter the keys for the right hand and then the keys for the left hand
# change experiment name to a name you've chosen for your own experiment
experiment_name = 'WM_chunking'
# change the str inside Path() to a directory of your choise.
## make sure 'stimuli' and 'experiment_code' folders are placed within your base_dir
base_dir   = Path('C:\\Users\\khash\\OneDrive\\Documents\\GitHub').absolute()

target_dir = base_dir / experiment_name /"target_files" # contains target files for the task
raw_dir    = base_dir/ experiment_name / "data"         # This is where the result files are being saved

# setting some defaults for the stimuli presentation
width_object = 8
height_object = 2
height_text = 1

def dircheck(path2dir):
    """
    Checks if a directory exists! if it does not exist, it creates it
    Args:
    dir_path    -   path to the directory you want to be created!
    """

    if not os.path.exists(path2dir):
        print(f"creating {path2dir}")
        os.makedirs(path2dir)
    else:
        print(f"{path2dir} already exists")

# use dirtree to make sure you have all the folders needed
def dirtree():
    """
    Create all the directories if they don't already exist
    """
    
    fpaths = [raw_dir, target_dir]
    for fpath in fpaths:
        dircheck(fpath)