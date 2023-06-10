import os
import pandas as pd
import numpy as np
from pandas import DataFrame
import sys





################################################################################################
############################################################################### Parameter
################################################################################################
folder_name = "data_20230510090201_0001"

system      = "Win"  if sys.platform=="win32" else "Linux"
folder_ast  = "D:\\Prog\\Code_Aster\\v2019\\bin\\" if system=="Win" else "/home/tirazone/aster/bin/"
folder_app  = "D:\\calculhub\\autodim_dash\\" if system=="Win" else "/home/tirazone/calculhub/autodim/"
folder_data = "D:\\calculhub\\autodim_dash\\data\\"+folder_name+"\\" if system=="Win" else "/home/tirazone/calculhub/autodim/data/"+folder_name+"/"





################################################################################################
############################################################################### Code
################################################################################################

################################################################## Run
os.system("cd " + folder_app)
os.system(folder_ast + "as_run --run " + folder_data + "Median.export")












