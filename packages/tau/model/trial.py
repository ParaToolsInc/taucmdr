"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# System modules
import os
import sys
import glob
import zlib
import json
import base64
from datetime import datetime

# TAU modules
import logger
import util
import controller as ctl

LOGGER = logger.getLogger(__name__)


class Trial(ctl.Controller):
  """
  Trial data model controller
  """
  
  attributes = {      
    'experiment': {
      'model': 'Experiment',
      'required': True
    },
    'experiment_snapshot': {
      'type': 'string',
      'required': True
    },
    'begin_time': {
      'type': 'datetime'
    },
    'end_time': {
      'type': 'datetime'
    },
    'outcome': {
      'type': 'string'
    },
  }
  
  def name(self):
    return "Trial%04d" % self.eid
  
  @classmethod
  def performTrial(cls, experiment, cmd, cwd, env):
    """
    TODO: Docs
    """
    def banner(mark, name, time):
      LOGGER.info('{:=<{}}'.format('== %s %s (%s) ==' %
                                   (mark, name, time), logger.LINE_WIDTH))    

    experiment.populate()
    target = experiment['target']
    application = experiment['application']
    measurement = experiment['measurement']
    begin_time = str(datetime.utcnow())
    
    # Snapshot the experiment, compress, and store as base64
    snapshot_data = {}
    for obj in target, application, measurement:
      obj.populate()
      obj_data = dict(obj.data)
      for excluded in 'project', 'projects':
        try: del obj_data[excluded]
        except: pass
      snapshot_data[obj.model_name] = obj_data
    LOGGER.debug("Snapshot data: %s" % snapshot_data)
    snapshot_json = json.dumps(repr(snapshot_data))
    snapshot = base64.b64encode(zlib.compress(snapshot_json))
    LOGGER.debug("Compressed %d bytes to %d bytes" % (len(snapshot_json), len(snapshot)))

    fields = {'experiment': experiment.eid,
              'experiment_snapshot': snapshot,
              'begin_time': begin_time}   

    banner('BEGIN', experiment.name(), begin_time)    
    trial = cls.create(fields)

    cmd_str = ' '.join(cmd)
    retval = util.createSubprocess(cmd, cwd=cwd, env=env)
    if retval != 0:
      LOGGER.warning("Nonzero return code '%d' from '%s'" % (retval, cmd_str))
    else:
      LOGGER.info("'%s' returned 0" % cmd_str)
    outcome = 'Return code %d' % retval

    # Add profile data to tauDB
    if measurement['profile']:
      profiles = glob.glob(os.path.join(cwd, 'profile.*.*.*'))
      if not profiles:
        LOGGER.error("%s did not generate any profile files!" % cmd_str)
        outcome = 'No profile files'
      else:
        LOGGER.info("Found %d profile files. Adding to local database..." % len(profiles))     
        cmd = ['taudb_loadtrial', '-n', trial.name(), 
               '-a', application['name'], '-x', experiment.name()]
        taudb_retval = util.createSubprocess(cmd, cwd=cwd, env=env)
        if taudb_retval != 0:
          LOGGER.warning("Failed to add profiles to local database! Make a copy of %s/profile.* if you want to preserve this data" % cwd)
          outcome = 'Upload failed'

    # TODO: Handle traces

    # Mark experiment end time and return
    end_time = str(datetime.utcnow())
    cls.update({'end_time': end_time, 'outcome': outcome}, eids=[trial.eid])
    banner('END', experiment.name(), end_time)
    return retval