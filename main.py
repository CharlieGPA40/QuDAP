import platform
import os
import sys
from shutil import which
from subprocess import call


if sys.version_info[:2] < (3, 7):
    print("Requires Python 3.7 or newer. "
          "Python %d.%d detected" % sys.version_info[:2])
    sys.exit(-1)

if platform.system() == 'Windows':
    OS = 'Windows'
elif platform.system() == 'Linux':
    OS = 'Linux'
elif platform.system() == 'Darwin':
    OS = 'Darwin'


os.system('pip install -r requirements.txt')
os.system('pip install latex')
if OS == 'Windows':
    if which('latex'):
        print('latex installed')
    else:
        print('Please install Latex before using the software')
        sys.exit(-1)
elif OS == 'Darwin':
    if which('latex'):
        print('latex installed')
    else:
        os.system(
            '/bin / bash - c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
        os.system('brew install mactex')
else:  # Linux
    pwd = Start.Linux()
    cmd = 'sudo apt install -y idle3 texlive-latex-extra cm-super dvipng'
    return_call = call('echo {} | sudo -S {}'.format(pwd, cmd), shell=True)
    while return_call == 1:
        pwd = Start.Linux()
        cmd = 'sudo apt install -y idle3 texlive-latex-extra cm-super dvipng'
        return_call = call('echo {} | sudo -S {}'.format(pwd, cmd), shell=True)

if OS == 'Windows':
    pass
elif OS == 'Darwin':
    pass
else:  # Linux
    pass
