# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
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
"""``target`` subcommand."""

from __future__ import absolute_import
from taucmdr.cli.cli_view import RootCommand
from taucmdr.model.target import Target

HELP_PAGE = """
TAU Commander Target:
========================================================================

The Target settings define the environment including: the host architecture,
compiler family and instaled software libraries.

Creating new targets:
Enter: `tau target create <new_target_name>`

Copying a TAU Commander Target:
Enter: `tau target copy <existing_target_name> <new_target_name>`
The new target has the same properties as the original existing target.

Editing a TAU Commander Target:
Enter: `tau target edit <target_name> --<target_property> <property setting>`

The target name can be changed with --new-name as shown below:
`tau target edit <target_name> --new-name <new_target_name>`

Delete a TAU Commander Target:
Enter: `tau target delete <target_name>`

List TAU Commander Target in a project:
Enter: `tau target list`
`tau target list –l` (long description)
`tau target list –s` (short description)

_________________________________________________________________________
"""


COMMAND = RootCommand(Target, __name__, group="configuration", help_page_fmt=HELP_PAGE)
