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
import subprocess


# TAU modules
import cf
import logger
import settings
import error
import controller
import util
import environment
from model.project import Project
from model.target import Target
from model.compiler import Compiler

LOGGER = logger.getLogger(__name__)


class Experiment(controller.Controller):
  """
  Experiment data model controller
  """
  
  attributes = {
    'selection': {
      'model': 'Selection',
      'required': True
    },
    'CC': {
      'model': 'Compiler',
      'required': True
    },
    'CXX': {
      'model': 'Compiler',
      'required': True
    },
    'FC': {
      'model': 'Compiler',
      'required': True
    },
    'trials': {
      'collection': 'Trial',
      'via': 'experiment'
    },
  }

  @classmethod
  def configure(cls, selected, compiler_cmd):
    """
    Installs all software required to perform the experiment and configures
    environment variables
    """
    selected.populate()
    target = selected['target']
    application = selected['application']
    measurement = selected['measurement']
    compiler = Compiler.identify(target, compiler_cmd)
    
    # See if we've already configured this experiment
    found = cls.one(keys={'selection': selected.eid, compiler['role']: compiler.eid})
    if found:
      LOGGER.debug("Found experiment: %s" % found)
      return found
    
    LOGGER.debug("Experiment not found, creating new experiment")
    fields = {'selection': selected.eid}
    
    # Discover and configure compilers
    compilers = {compiler['role']: compiler}
    for info in cf.compiler.getCompilerFamily(compiler['command']):
      if info.role != compiler['role']:
        try:
          other = Compiler.identify(target, info.command)
        except error.ConfigurationError:
          continue
        if os.path.dirname(other['path']) == os.path.dirname(compiler['path']):
          compilers[other['role']] = other
    try:
      cc = compilers['CC']
    except KeyError:
      raise error.ConfigurationError("C compiler matching '%s' not found" % compiler_cmd)
    try:
      cxx = compilers['CXX']
    except KeyError:
      raise error.ConfigurationError("C++ compiler matching '%s' not found" % compiler_cmd)
    try:
      fc = compilers['FC']
    except KeyError:
      raise error.ConfigurationError("Fortran compiler matching '%s' not found" % compiler_cmd)

    fields['CC'] = cc.eid
    fields['CXX'] = cxx.eid
    fields['FC'] = fc.eid

    # Create a place to store project files and settings
    prefix = selected['project']['prefix']
    try: 
      util.mkdirp(prefix)
    except:
      raise error.ConfigurationError('Cannot create directory %r' % prefix, 
                                     'Check that you have `write` access')

    # Configure/build/install TAU if needed
    tau = cf.tau.Tau(prefix, cc, cxx, fc, target['tau'], target['host_arch'],
                     verbose=(logger.LOG_LEVEL == 'DEBUG'),
                     profile=measurement['profile'],
                     trace=measurement['trace'],
                     sample=measurement['sample'],
                     source_inst=measurement['source_inst'],
                     compiler_inst=measurement['compiler_inst'],
                     # TODO: Library wrapping inst
                     openmp_support=application['openmp'], 
                     openmp_measurements=measurement['openmp'],
                     pthreads_support=application['pthreads'], 
                     pthreads_measurements=None, # TODO
                     mpi_support=application['mpi'], 
                     mpi_measurements=measurement['mpi'],
                     cuda_support=application['cuda'],
                     cuda_measurements=None, # Todo
                     shmem_support=application['shmem'],
                     shmem_measurements=None, # TODO
                     mpc_support=application['mpc'],
                     mpc_measurements=None, # TODO
                     memory_support=None, # TODO
                     memory_measurements=None, # TODO
                     callpath=measurement['callpath'])
    tau.install()
    
    # Create a new experiment record to mark configuration success 
    exp = Experiment.create(fields)
    exp.tau = tau
    return exp

  def build(self, compiler_cmd, compiler_args):
    """
    TODO: Docs
    """
    compiler = self.tau.getCompiler(compiler_cmd)
    tauOpts, tauEnv = tau.getCompiletimeConfig()
    
    cmd = [compiler] + tauOpts + compiler_args
    env = environment.buildEnvironment(tauEnv)
    
    # Make sure TAU's bin is always in PATH
    env['PATH'] = os.pathsep.join(tau.bin_path, env['PATH'])
    
    LOGGER.debug('Creating subprocess: cmd=%r, env=%r' % (cmd, env))
    LOGGER.info('\n'.join(['%s=%s' % i for i in env.iteritems() if i[0].startswith('TAU')]))
    LOGGER.info(' '.join(cmd))
 
    # Control build output
    with logger.logging_streams():
      proc = subprocess.Popen(cmd, env=env, stdout=sys.stdout, stderr=sys.stderr)
      return proc.wait()
