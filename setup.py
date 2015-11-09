import os
import sys
from cx_Freeze import setup, Executable


includes = []

excludes = ["Tkinter", "pygments", "wx", "PyQt4", "IPython",
            "matplotlib", "scipy", "pango", "PIL", "cairo",
            "beaker"]

packages = ["tau", "lockfile", "termcolor", "texttable", "tinydb"]

tau_exe = Executable(os.path.abspath('bin/tau'), 'Console', targetName="tau")

options = {
    "build_exe": {
        "optimize": 2,
        "includes": includes,
        "excludes": excludes,
        "packages": packages,
        "path": sys.path,
        "create_shared_zip": True,
        "append_script_to_exe": False}
}

setup(name='TAU Commander',
      version='0.1',
      description='Software performance engineering made easy.',
      executables=[tau_exe],
      options=options)

