import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.abspath("."), "../../.."))
sys.path.insert(0, os.path.join(parent_dir, 'packages'))

from .commands.connect import connect
from .commands.project import get_all_projects, new_project, copy_project, edit_project, delete_project
from .commands.target import new_target, edit_target, copy_target, delete_target
from .commands.application import new_application, edit_application, copy_application, delete_application
from .commands.measurement import new_measurement, edit_measurement, copy_measurement, delete_measurement
from .commands.experiment import new_experiment, select_experiment, edit_experiment, delete_experiment
from .commands.trial import edit_trial, delete_trial
