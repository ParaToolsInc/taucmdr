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
This file is used for configuring measurements related commands called by the JupyterLab Extension
"""

import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.measurement.create import COMMAND as create_measurement_cmd
from taucmdr.cli.commands.measurement.edit import COMMAND as edit_measurement_cmd
from taucmdr.cli.commands.measurement.delete import COMMAND as delete_measurement_cmd
from taucmdr.cli.commands.measurement.copy import COMMAND as copy_measurement_cmd


#def new_measurement(project, name, profile, trace, sample, source_inst, compiler_inst, openmp, cuda, io, mpi, shmem):
def new_measurement(project, name, args):
    """
    This function is called by the JupyterLab New Measurement Dialog box to create an Measurement
    """

    select_project_cmd.main([project])
    try:
        create_measurement_cmd.main([name,
                    '--profile', args['profile'],
                    '--trace', args['trace'],
                    '--sample', args['sample'],
                    '--source-inst', args['source_inst'],
                    '--compiler-inst', args['compiler_inst'],
                    '--openmp', args['openmp'],
                    '--cuda', args['cuda'],
                    '--io', args['io'],
                    '--mpi', args['mpi'],
                    '--shmem', args['shmem']])

    except SystemExit:
        return json.dumps({'status': 'failure', 'message': 'Error in creation'})

    except NameError as other:
        return json.dumps({'status': 'failure', 'message': other})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def edit_measurement(project, name, new_name, args):
    """
    This function is called by the JupyterLab Edit Measurement Dialog box to edit an Measurement
    """
    select_project_cmd.main([project])
    try:
        edit_measurement_cmd.main([name,
                    '--new-name', new_name,
                    '--profile', args['profile'],
                    '--trace', args['trace'],
                    '--sample', args['sample'],
                    '--source-inst', args['source_inst'],
                    '--compiler-inst', args['compiler_inst'],
                    '--openmp', args['openmp'],
                    '--cuda', args['cuda'],
                    '--io', args['io'],
                    '--mpi', args['mpi'],
                    '--shmem', args['shmem']])

    except SystemExit:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except NameError as other:
        return json.dumps({'status': 'failure', 'message': other})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})


def copy_measurement(project, name, new_name, is_project=False):
    """
    This function is called by the JupyterLab Copy Measurement Dialog box to copy an Measurement
    """
    if not is_project:
        select_project_cmd.main([project])

    try:
        copy_measurement_cmd.main([name, new_name])

    except SystemExit:
        return json.dumps({'status': 'failure', 'message': 'Error in copy'})

    except NameError as other:
        return json.dumps({'status': 'failure', 'message': other})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def delete_measurement(name):
    """
    This function is called by the JupyterLab Delete Measurement Dialog box to delete an Measurement
    """
    try:
        delete_measurement_cmd.main([name])

    except SystemExit:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except NameError as other:
        return json.dumps({'status': 'failure', 'message': other})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})
