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
import shutil
from datetime import datetime

# TAU modules
import logger
import util
import storage
import controller as ctl

LOGGER = logger.getLogger(__name__)


class Trial(ctl.Controller):
  """
  Trial data model controller
  """
  
  attributes = {      
    'number': {
      'type': 'integer',
      'required': True
    },
    'experiment': {
      'model': 'Experiment',
      'required': True
    },
    'command': {
      'type': 'string',
      'required': True
    },
    'cwd': {
      'type': 'string',
      'required': True
    },
#     'env': {
#       'type': 'string',
#       'required': True
#     },
    'begin_time': {
      'type': 'datetime'
    },
    'end_time': {
      'type': 'datetime'
    },
    'return_code': {
      'type': 'integer'
    },
  }
  
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
    trial_number = str(len(experiment['trials']))
    prefix = os.path.join(experiment['project']['prefix'],
                          experiment['project']['name'],
                          target['name'], 
                          application['name'], 
                          measurement['name'], 
                          trial_number)
    cmd_str = ' '.join(cmd)
    
    # Create trial prefix
    try:
      util.mkdirp(prefix)
    except Exception as err:
      raise error.ConfigurationError('Cannot create directory %r: %s' % (prefix, err), 
                                     'Check that you have `write` access')
    
    fields = {'number': trial_number,
              'experiment': experiment.eid,
              'command': cmd_str,
              'cwd': cwd,
#               'env': repr(env),
              'begin_time': begin_time}

    banner('BEGIN', experiment.name(), begin_time)
    trial = cls.create(fields)
    try:
      retval = util.createSubprocess(cmd, cwd=cwd, env=env)
      if retval:
        LOGGER.warning("Nonzero return code '%d' from '%s'" % (retval, cmd_str))
      else:
        LOGGER.info("'%s' returned 0" % cmd_str)
  
      # Copy profile files to trial prefix
      if measurement['profile']:
        profiles = glob.glob(os.path.join(cwd, 'profile.*.*.*'))
        if not profiles:
          LOGGER.error("%s did not generate any profile files!" % cmd_str)
        else:
          LOGGER.info("Found %d profile files. Adding to trial..." % len(profiles))
          for file in profiles:
            shutil.move(file, prefix)
            LOGGER.debug("'%s' => '%s'" % (file, prefix))
  
      # TODO: Handle traces
      
      end_time = str(datetime.utcnow())
    except:
      # Something went wrong so revert the trial
      LOGGER.error("Exception raised, reverting trial...")
      cls.delete(eids=[trial.eid])
      shutil.rmtree(prefix, ignore_errors=True)
      raise
    else:
      # Trial successful, mark experiment end time
      cls.update({'end_time': end_time, 'return_code': retval}, eids=[trial.eid])
      # Record configuration state for provenance
      shutil.copy(storage.user_storage.dbfile, prefix)
      banner('END', experiment.name(), end_time)
    
    return retval
  