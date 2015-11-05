import os
from cx_Freeze import setup, Executable

packages = ["tau", "lockfile", "termcolor", "texttable", "tinydb"]

excludes = ["Tkinter", "pygments", "wx", "PyQt4", "IPython",
            "matplotlib", "scipy", "pango", "PIL", "cairo",
            "beaker"]

buildOptions = dict(packages=packages, excludes=excludes,
                    optimize=2, compressed=True)

executables = [
    Executable(os.path.abspath('bin/tau'), 'Console', targetName="tau")
]

setup(name='TAU Commander',
      version='0.1',
      description='Software performance engineering made easy.',
      options=dict(build_exe=buildOptions),
      executables=executables)

