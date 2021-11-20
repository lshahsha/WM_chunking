# WM_chunking
Codes for the WM chunking experiment

# instructions
Make sure you have Python 3.8.9, ipython, and Visual Studio code (VS code) installed

## Modify the constants
open constants.py and change base_dir to the directory where you want the project to be stored in

## Make target files
In VS code open a terminal and type in the following commands (without $)
> $ipython
> 
> $from make_target import WMChunking, make_files
> 
> $make_files(number_of_runs = 8)
