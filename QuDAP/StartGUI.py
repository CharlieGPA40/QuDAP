import platform
import os
import sys
import initalization


if sys.version_info[:2] < (3, 10):
    print("Requires Python 3.10 or newer. "
          "Python %d.%d detected" % sys.version_info[:2])
    sys.exit(-1)

if platform.system() == 'Windows':
    OS = 'Windows'
    os.system('py -m pip install --upgrade pip')
    os.system('py -m pip install -r requirements.txt')
# elif platform.system() == 'Linux':
#     OS = 'Linux'
# os.system('python3 -m pip install --upgrade pip')
#     os.system('python3 -m pip install -r requirements.txt')
# elif platform.system() == 'Darwin':
#     OS = 'Darwin'
# os.system('python3 -m pip install --upgrade pip')
#     os.system('python3 -m pip install -r requirements.txt')


if OS == 'Windows':
    if __name__ == '__main__':
        initalization.main()
# elif OS == 'Darwin':
# else:  # Linux

