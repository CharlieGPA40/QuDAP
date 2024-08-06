import platform
import os
import sys
import initalization


if sys.version_info[:2] < (3, 10):
    print("Requires Python 3.7 or newer. "
          "Python %d.%d detected" % sys.version_info[:2])
    sys.exit(-1)

if platform.system() == 'Windows':
    OS = 'Windows'
# elif platform.system() == 'Linux':
#     OS = 'Linux'
# elif platform.system() == 'Darwin':
#     OS = 'Darwin'

os.system('pip install -r requirements.txt')
if OS == 'Windows':
    initalization
# elif OS == 'Darwin':
# else:  # Linux

