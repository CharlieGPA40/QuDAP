import clr
import sys
# import clr
# print(dir(clr))

import clr
import glob
import os



directory_path = "C:/Windows/Microsoft.NET/assembly/GAC_64/Newport.XPS.CommandInterface"
print(os.path.isdir(directory_path))
if os.path.isdir(directory_path):
    directories = [f for f in glob.glob(f"{directory_path}/*") if os.path.isdir(f)]
    print(directories)

print(f'{directories[0]}/Newport.XPS.CommandInterface.dll')
clr.AddReference(f'{directories[0]}/Newport.XPS.CommandInterface.dll')
# clr.AddReference("Newport.XPS.CommandInterface.dll")
from CommandInterfaceXPS import *

myXPS = XPS()
timeout = 1000
result = myXPS.OpenInstrument(address, port, timeout)
if result == 0:
    print('Open ', address, ":", port, " => Successful")
else:
    print('Open ', address, ":", port, " => failure ", result)

directory_path = "C:/Windows/Microsoft.NET/assembly/GAC_64/Newport.XPS.CommandInterface"