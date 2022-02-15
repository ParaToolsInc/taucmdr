#
# Copyright (c) 2022, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
This file is used for configuring trial related commands called by the JupyterLab Extension
"""

import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.trial.edit import COMMAND as edit_trial_cmd
from taucmdr.cli.commands.trial.renumber import COMMAND as renumber_trial_cmd
from taucmdr.cli.commands.trial.delete import COMMAND as delete_trial_cmd

def edit_trial(project, number, new_number, description):
    """
    This function is called by the JupyterLab Edit Trial Dialog box to copy a Trial
    """
    select_project_cmd.main([project])
    try:
        renumber_trial_cmd.main([number, '--to', new_number])
        edit_trial_cmd.main([new_number, '--description', description])

    except SystemExit:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except NameError as other:
        return json.dumps({'status': 'failure', 'message': other})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def delete_trial(project, number):
    """
    This function is called by the JupyterLab Delete Trial Dialog box to delete a Trial
    """
    select_project_cmd.main([project])
    try:
        delete_trial_cmd.main([number])

    except SystemExit:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except NameError as other:
        return json.dumps({'status': 'failure', 'message': other})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})
