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
    'environment': {
      'type': 'string',
      'required': True
    },
    'begin_time': {
      'type': 'datetime'
    },
    'end_time': {
      'type': 'datetime'
    },
    'return_code': {
      'type': 'integer'
    },
    'data_size': {
      'type': 'integer'
    },                
  }
  
  def prefix(self):
    """
    Path to trial data
    """
    experiment = self.populate('experiment')
    return os.path.join(experiment.prefix(), str(self['number']))
  
  def onCreate(self):
    """
    Initialize trial data
    """
    prefix = self.prefix()
    try:
      util.mkdirp(prefix)
    except Exception as err:
      raise error.ConfigurationError('Cannot create directory %r: %s' % (prefix, err), 
                                     'Check that you have `write` access')
  
  def onDelete(self):
    """
    Clean up trial data
    """
    prefix = self.prefix()
    try:
      shutil.rmtree(prefix)
    except Exception as err:
      if os.path.exists(prefix):
        LOGGER.error("Could not remove trial data at '%s': %s" % (prefix, err))
  
  @classmethod
  def perform(cls, experiment, cmd, cwd, env):
    """
    TODO: Docs
    """
    def banner(mark, name, time):
      LOGGER.info('{:=<{}}'.format('== %s %s (%s) ==' %
                                   (mark, name, time), logger.LINE_WIDTH))    
    measurement = experiment.populate('measurement')
    cmd_str = ' '.join(cmd)
    begin_time = str(datetime.utcnow())
    
    trials = experiment.populate('trials')
    trial_number = None
    all_trial_numbers = sorted([trial['number'] for trial in trials])
    LOGGER.debug("Trial numbers: %s" % all_trial_numbers)
    for i, ii in enumerate(all_trial_numbers):
      if i != ii:
        trial_number = i
        break
    if trial_number == None:
      trial_number = len(all_trial_numbers)
    LOGGER.debug("New trial number is %d" % trial_number)
    
    fields = {'number': trial_number,
              'experiment': experiment.eid,
              'command': cmd_str,
              'cwd': cwd,
              'environment': 'FIXME',
              'begin_time': begin_time}

    banner('BEGIN', experiment.name(), begin_time)
    trial = cls.create(fields)
    prefix = trial.prefix()
    try:
      retval = util.createSubprocess(cmd, cwd=cwd, env=env)
      if retval:
        LOGGER.warning("Nonzero return code '%d' from '%s'" % (retval, cmd_str))
      else:
        LOGGER.info("'%s' returned 0" % cmd_str)
  
      # Copy profile files to trial prefix
      if measurement['profile']:
        profiles = glob.glob(os.path.join(cwd, 'profile.*.*.*'))
        multi_profiles= glob.glob(os.path.join(cwd, 'MULTI__*'))
 	
        if profiles:
          LOGGER.info("Found %d profile files. Adding to trial..." % len(profiles))
          for file in profiles:
            shutil.move(file, prefix)
            LOGGER.debug("'%s' => '%s'" % (file, prefix))
	elif multi_profiles:
          LOGGER.info("Found %d multi_profile direcotries. Adding to trial..." % len(multi_profiles))
          for dirs in multi_profiles:
            shutil.move(dirs, prefix)
            LOGGER.debug("'%s' => '%s'" % (dirs, prefix))
	else:
          LOGGER.error("%s did not generate any profile files or MULTI__ directories!" % cmd_str)
  
      # TODO: Handle traces
      
      end_time = str(datetime.utcnow())
    except:
      # Something went wrong so revert the trial
      LOGGER.error("Exception raised, reverting trial...")
      cls.delete(eids=[trial.eid])
      raise
    else:
      # Trial successful, update record and record state for provenance
      data_size = sum(os.path.getsize(os.path.join(prefix, f)) for f in os.listdir(prefix))
      shutil.copy(storage.user_storage.dbfile, prefix)
      cls.update({'end_time': end_time, 
                  'return_code': retval,
                  'data_size': data_size}, eids=[trial.eid])
      banner('END', experiment.name(), end_time)
    
    return retval
