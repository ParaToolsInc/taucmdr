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
This file is used for importing commands that the JupyterLab Extension will use with
its IPython Kernel
"""
import os
import sys

from taucmdr.kernel.commands.connect import connect                                               # pylint: disable=unused-import
from taucmdr.kernel.commands.project import (                                                     # pylint: disable=unused-import
        get_all_projects, new_project, copy_project, edit_project, delete_project
)
from taucmdr.kernel.commands.target import (                                                      # pylint: disable=unused-import
        new_target, edit_target, copy_target, delete_target
)
from taucmdr.kernel.commands.application import (                                                 # pylint: disable=unused-import
        new_application, edit_application, copy_application, delete_application
)
from taucmdr.kernel.commands.measurement import (                                                 # pylint: disable=unused-import
        new_measurement, edit_measurement, copy_measurement, delete_measurement
)
from taucmdr.kernel.commands.experiment import (                                                  # pylint: disable=unused-import
        new_experiment, select_experiment, edit_experiment, delete_experiment
)
from taucmdr.kernel.commands.trial import edit_trial, delete_trial                                # pylint: disable=unused-import
