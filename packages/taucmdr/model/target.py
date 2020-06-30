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
"""Target data model.

:any:`Target` fully describes the hardware and software environment that our
experiments will be performed in.  The hardware architecture, available compilers,
and system libraries are described in the target record.  There will be multiple
target records for any physical computer system since each target record uniquely
describes a specific set of system features.  For example, if both GNU and Intel
compilers are installed then there will target configurations for each compiler family.
"""

import os
import glob
import fasteners
from taucmdr import logger, util
from taucmdr.error import ConfigurationError, IncompatibleRecordError
from taucmdr.error import ProjectSelectionError, ExperimentSelectionError
from taucmdr.mvc.model import Model
from taucmdr.mvc.controller import Controller
from taucmdr.model.compiler import Compiler
from taucmdr.cf import software
from taucmdr.cf.platforms import Architecture, OperatingSystem
from taucmdr.cf.platforms import HOST_ARCH, INTEL_KNC, HOST_OS, DARWIN, CRAY_CNL
from taucmdr.cf.compiler import Knowledgebase, InstalledCompilerSet
from taucmdr.cf.storage.levels import PROJECT_STORAGE, SYSTEM_STORAGE


LOGGER = logger.get_logger(__name__)


def _require_compiler_family(family, *hints):
    """Creates a compatibility callback to check a compiler family.

    Args:
        family: The required compiler family.
        *hints: String hints to show the user when the check fails.

    Returns:
        callable: a compatibility checking callback for use with data models.
    """
    def callback(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
        """Compatibility checking callback for use with data models.

        Requires ``rhs[rhs_attr]`` to be a compiler in a certain compiler family.

        Args:
            lhs (Model): The model invoking `check_compatibility`.
            lhs_attr (str): Name of the attribute that defines the 'compat' property.
            lhs_value: Value of the attribute that defines the 'compat' property.
            rhs (Model): Model we are checking against (argument to `check_compatibility`).
            rhs_attr (str): The right-hand side attribute we are checking for compatibility.

        Raises:
            ConfigurationError: Invalid compiler family specified in target configuration.
        """
        lhs_name = lhs.name.lower()
        rhs_name = rhs.name.lower()
        msg = ("%s = %s in %s requires %s in %s to be a %s compiler" %
               (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name, family))
        try:
            compiler_record = rhs.populate(rhs_attr)
        except KeyError:
            raise ConfigurationError("%s but it is undefined" % msg)
        given_family_name = compiler_record['family']
        if given_family_name != family.name:
            raise ConfigurationError("%s but it is a %s compiler" % (msg, given_family_name), *hints)
    return callback

def knc_require_k1om(*_):
    """Compatibility checking callback for use with data models.

    Requires that the Intel k1om tools be installed if the host architecture is KNC.

    Raises:
        ConfigurationError: Invalid compiler family specified in target configuration.
    """
    k1om_ar = util.which('x86_64-k1om-linux-ar')
    if not k1om_ar:
        for path in glob.glob('/usr/linux-k1om-*'):
            k1om_ar = util.which(os.path.join(path, 'bin', 'x86_64-k1om-linux-ar'))
            if k1om_ar:
                break
        else:
            raise ConfigurationError('k1om tools not found', 'Try installing on compute node', 'Install MIC SDK')


def papi_source_default():
    """Choose the best default PAPI source."""
    if HOST_OS is DARWIN:
        return None
    elif HOST_OS is CRAY_CNL:
        for path in ('/opt/cray/papi/default', '/opt/cray/pe/papi/default'):
            if os.path.isdir(path):
                return path
    return 'download'


def cuda_toolkit_default():
    for path in sorted(glob.glob('/usr/local/cuda*')):
        if os.path.exists(os.path.join(path, 'bin', 'nvcc')):
            return path
    nvcc = util.which('nvcc')
    if nvcc:
        cuda_dir = os.path.dirname(os.path.dirname(nvcc))
        if os.path.exists(os.path.join(cuda_dir, 'include', 'cuda.h')):
            return cuda_dir
    return None


def tau_source_default():
    """"Per Sameer's request, override managed TAU installation with an existing unmanaged TAU installation.

    If a file named "override_tau_source" exists in the system-level storage prefix, use the contents of
    that file as the default path for TAU.  Otherwise use "download" as the default.

    Returns:
        str: Path to TAU or "download".
    """
    try:
        with open(os.path.join(SYSTEM_STORAGE.prefix, 'override_tau_source')) as fin:
            path = fin.read()
    except IOError:
        return 'download'
    path = path.strip()
    if not (os.path.isdir(path) and util.path_accessible(path)):
        LOGGER.warning("'%s' does not exist or is not accessible.")
        return 'download'
    return path

def attributes():
    """Construct attributes dictionary for the target model.

    We build the attributes in a function so that classes like ``taucmdr.module.project.Project`` are
    fully initialized and usable in the returned dictionary.

    Returns:
        dict: Attributes dictionary.
    """
    from taucmdr.model.project import Project
    from taucmdr.cli.arguments import ParsePackagePathAction
    from taucmdr.cf.compiler.host import CC, CXX, FC, UPC, INTEL
    from taucmdr.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC, INTEL as INTEL_MPI
    from taucmdr.cf.compiler.shmem import SHMEM_CC, SHMEM_CXX, SHMEM_FC
    from taucmdr.cf.compiler.cuda import CUDA_CXX, CUDA_FC
    from taucmdr.cf.compiler.caf import CAF_FC
    from taucmdr.cf.compiler.python import PY

    knc_intel_only = _require_compiler_family(INTEL,
                                              "You must use Intel compilers to target the Xeon Phi (KNC)",
                                              "Try adding `--compilers=Intel` to the command line")
    knc_intel_mpi_only = _require_compiler_family(INTEL_MPI,
                                                  "You must use Intel MPI compilers to target the Xeon Phi (KNC)",
                                                  "Try adding `--mpi-wrappers=Intel` to the command line")

    return {
        'projects': {
            'collection': Project,
            'via': 'targets',
            'description': 'projects using this target'
        },
        'name': {
            'primary_key': True,
            'type': 'string',
            'unique': True,
            'description': 'target configuration name',
        },
        'host_os': {
            'type': 'string',
            'required': True,
            'description': 'host operating system',
            'default': HOST_OS.name,
            'argparse': {'flags': ('--os',),
                         'group': 'host',
                         'metavar': '<os>',
                         'choices': OperatingSystem.keys()},
            'rebuild_required': True
        },
        'host_arch': {
            'type': 'string',
            'required': True,
            'description': 'host architecture',
            'default': HOST_ARCH.name,
            'argparse': {'flags': ('--arch',),
                         'group': 'host',
                         'metavar': '<arch>',
                         'choices': Architecture.keys()},
            'compat': {str(INTEL_KNC):
                       (Target.require('host_arch', knc_require_k1om),
                        Target.require(CC.keyword, knc_intel_only),
                        Target.require(CXX.keyword, knc_intel_only),
                        Target.require(FC.keyword, knc_intel_only),
                        Target.require(MPI_CC.keyword, knc_intel_mpi_only),
                        Target.require(MPI_CXX.keyword, knc_intel_mpi_only),
                        Target.require(MPI_FC.keyword, knc_intel_mpi_only))},
            'rebuild_required': True
        },
        CC.keyword: {
            'model': Compiler,
            'required': True,
            'description': 'Host C compiler command',
            'argparse': {'flags': ('--cc',),
                         'group': 'host',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        CXX.keyword: {
            'model': Compiler,
            'required': True,
            'description': 'Host C++ compiler command',
            'argparse': {'flags': ('--cxx',),
                         'group': 'host',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'Host Fortran compiler command',
            'argparse': {'flags': ('--fc',),
                         'group': 'host',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        UPC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'Universal Parallel C compiler command',
            'argparse': {'flags': ('--upc',),
                         'group': 'Universal Parallel C',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        MPI_CC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'MPI C compiler command',
            'argparse': {'flags': ('--mpi-cc',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        MPI_CXX.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'MPI C++ compiler command',
            'argparse': {'flags': ('--mpi-cxx',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        MPI_FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'MPI Fortran compiler command',
            'argparse': {'flags': ('--mpi-fc',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        'mpi_libraries': {
            'type': 'array',
            'description': 'libraries to link to when building MPI applications',
            'argparse': {'flags': ('--mpi-libraries',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<flag>'},
            'compat': {bool: (Target.require(MPI_CC.keyword),
                              Target.require(MPI_CXX.keyword),
                              Target.require(MPI_FC.keyword))},
            'rebuild_required': True
        },
        SHMEM_CC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM C compiler command',
            'argparse': {'flags': ('--shmem-cc',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        SHMEM_CXX.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM C++ compiler command',
            'argparse': {'flags': ('--shmem-cxx',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        SHMEM_FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM Fortran compiler command',
            'argparse': {'flags': ('--shmem-fc',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        'shmem_libraries': {
            'type': 'array',
            'description': 'libraries to link to when building SHMEM applications',
            'argparse': {'flags': ('--shmem-libraries',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<flag>'},
            'rebuild_required': True
        },
        CUDA_CXX.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'CUDA compiler command',
            'argparse': {'flags': ('--cuda-cxx',),
                         'group': 'CUDA',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        CUDA_FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'CUDA Fortran compiler command',
            'argparse': {'flags': ('--cuda-fc',),
                         'group': 'CUDA',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        CAF_FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'Coarray Fortran compiler command',
            'argparse': {'flags': ('--caf-fc',),
                         'group': 'CAF',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        PY.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'Python Interpreter command',
            'argparse': {'flags': ('--python-interpreter',),
                         'group': 'python',
                         'metavar': '<command>'},
            'rebuild_required': True
        },
        'cuda_toolkit': {
            'type': 'string',
            'description': 'path to NVIDIA CUDA Toolkit (enables OpenCL support)',
            'default': cuda_toolkit_default(),
            'argparse': {'flags': ('--cuda-toolkit',),
                         'group': 'CUDA',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
            'rebuild_required': True
        },
        'tau_source': {
            'type': 'string',
            'description': 'path or URL to a TAU installation or archive file',
            'default': tau_source_default(),
            'argparse': {'flags': ('--tau',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|nightly)',
                         'action': ParsePackagePathAction},
            'compat': {True: Target.require('tau_source')},
            'rebuild_required': True
        },
        'pdt_source': {
            'type': 'string',
            'description': 'path or URL to a PDT installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--pdt',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'rebuild_required': True
        },
        'binutils_source': {
            'type': 'string',
            'description': 'path or URL to a GNU binutils installation or archive file',
            'default': 'download' if HOST_OS is not DARWIN else None,
            'argparse': {'flags': ('--binutils',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN)},
            'rebuild_required': True
        },
        'libunwind_source': {
            'type': 'string',
            'description': 'path or URL to a libunwind installation or archive file',
            'default': 'download' if HOST_OS is not DARWIN else None,
            'argparse': {'flags': ('--libunwind',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN)},
            'rebuild_required': True
        },
        'papi_source': {
            'type': 'string',
            'description': 'path or URL to a PAPI installation or archive file',
            'default': papi_source_default(),
            'argparse': {'flags': ('--papi',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN)},
            'rebuild_required': True
        },
        'scorep_source': {
            'type': 'string',
            'description': 'path or URL to a Score-P installation or archive file',
            'default': 'download' if HOST_OS is not DARWIN else None,
            'argparse': {'flags': ('--scorep',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): (Target.discourage('host_os', DARWIN),
                                                   Target.require(CC.keyword),
                                                   Target.require(CXX.keyword),
                                                   Target.require(FC.keyword))},
            'rebuild_required': True
        },
        'ompt_source': {
            'type': 'string',
            'description': 'path or URL to OMPT installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--ompt',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|download-tr6|None)',
                         'action': ParsePackagePathAction},
            'rebuild_required': True
        },
        'libotf2_source': {
            'type': 'string',
            'description': 'path or URL to libotf2 installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--otf',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'rebuild_required': True
        },
        'forced_makefile': {
            'type': 'string',
            'description': 'Populate target configuration from a TAU Makefile (WARNING: Overrides safety checks)',
            'argparse': {'flags': ('--from-tau-makefile',),
                         'metavar': '<path>'},
            'rebuild_required': True
        }
    }

class TargetController(Controller):
    """Target data controller."""
    def delete(self, keys, context=True):
        # pylint: disable=unexpected-keyword-arg
        from taucmdr.error import ImmutableRecordError
        from taucmdr.model.experiment import Experiment
        changing = self.search(keys, context=context)
        for model in changing:
            expr_ctrl = Experiment.controller()
            found = expr_ctrl.search({'target': model.eid})
            used_by = [expr['name'] for expr in found if expr.data_size() > 0]
            if used_by:
                raise ImmutableRecordError("Target '%s' cannot be modified because "
                                           "it is used by these experiments: %s" % (model['name'], ', '.join(used_by)))
        return super(TargetController, self).delete(keys)

class Target(Model):
    """Target data model."""

    __attributes__ = attributes
    __controller__ = TargetController

    def __init__(self, *args, **kwargs):
        super(Target, self).__init__(*args, **kwargs)
        self._compilers = None

    def on_create(self):
        for comp in self.compilers().itervalues():
            comp.generate_wrapper(os.path.join(self.storage.prefix, 'bin', self['name']))

    def on_delete(self):
        util.rmtree(os.path.join(self.storage.prefix, 'bin', self['name']))

    def on_update(self, changes):
        from taucmdr.error import ImmutableRecordError
        from taucmdr.model.experiment import Experiment
        expr_ctrl = Experiment.controller()
        found = expr_ctrl.search({'target': self.eid})
        used_by = [expr['name'] for expr in found if expr.data_size() > 0]
        if used_by:
            raise ImmutableRecordError("Target '%s' cannot be modified because "
                                       "it is used by these experiments: %s" % (self['name'], ', '.join(used_by)))
        for expr in found:
            try:
                expr.verify()
            except IncompatibleRecordError as err:
                raise ConfigurationError("Changing measurement '%s' in this way will create an invalid condition "
                                         "in experiment '%s':\n    %s." % (self['name'], expr['name'], err),
                                         "Delete experiment '%s' and try again." % expr['name'])
        if self.is_selected():
            for attr, change in changes.iteritems():
                props = self.attributes[attr]
                if props.get('rebuild_required'):
                    if props.get('model', None) == Compiler:
                        old_comp = Compiler.controller(self.storage).one(change[0])
                        new_comp = Compiler.controller(self.storage).one(change[1])
                        message = {attr: (old_comp['path'], new_comp['path'])}
                    else:
                        message = {attr: change}
                    self.controller(self.storage).push_to_topic('rebuild_required', message)

    def is_selected(self):
        """Returns True if this target configuration is part of the selected experiment, False otherwise."""
        from taucmdr.model.project import Project
        try:
            selected = Project.selected().experiment()
        except (ProjectSelectionError, ExperimentSelectionError):
            return False
        return selected['target'] == self.eid

    def architecture(self):
        return Architecture.find(self['host_arch'])

    def operating_system(self):
        return OperatingSystem.find(self['host_os'])

    def sources(self):
        """Get paths to all source packages known to this target.

        Returns:
            dict: Software package paths indexed by package name.
        """
        sources = {}
        for attr, val in self.iteritems():
            if val and attr.endswith('_source'):
                sources[attr.replace('_source', '')] = val
        return sources

    def get_installation(self, name):
        cls = software.get_installation(name)
        return cls(self.sources(), self.architecture(), self.operating_system(), self.compilers())

    def acquire_sources(self):
        """Acquire all source code packages known to this target."""
        for attr, val in self.iteritems():
            if val and attr.endswith('_source'):
                inst = self.get_installation(attr.replace('_source', ''))
                try:
                    inst.acquire_source()
                except ConfigurationError as err:
                    # Not a warning since using an existing installation is OK and in that case
                    # there is no source code package to acquire.
                    LOGGER.info(err)

    def compilers(self):
        """Get information about the compilers used by this target configuration.

        Returns:
            InstalledCompilerSet: Collection of installed compilers used by this target.
        """
        if not self._compilers:
            eids = []
            compilers = {}
            for role in Knowledgebase.all_roles():
                try:
                    with fasteners.InterProcessLock(os.path.join(PROJECT_STORAGE.prefix, '.lock')):
                        compiler_record = self.populate(role.keyword)
                except KeyError:
                    continue
                compilers[role.keyword] = compiler_record.installation()
                LOGGER.debug("compilers[%s] = '%s'", role.keyword, compilers[role.keyword].absolute_path)
                eids.append(compiler_record.eid)
            self._compilers = InstalledCompilerSet('_'.join([str(x) for x in sorted(eids)]), **compilers)
        return self._compilers

    def check_compiler(self, compiler_cmd, compiler_args):
        """Checks a compiler command its arguments for compatibility with this target configuration.

        Checks that the given compiler matches at least one, **but possibly more**, of the compilers
        used in the target. Also performs any special checks for invalid compiler arguments,
        e.g. -mmic is only for native KNC.

        If the given compiler command and arguments are compatible with this target then information about
        matching compiler installations is returned as a list of n :any:`InstalledCompiler` instances.

        Args:
            compiler_cmd (str): The compiler command as passed by the user.
            compiler_args (list): Compiler command line arguments.

        Returns:
            list: Information about matching installed compilers as :any:`Compiler` instances.

        Raises:
            ConfigurationError: The compiler or command line arguments are incompatible with this target.
        """
        if '-mmic' in compiler_args and self['host_arch'] != str(INTEL_KNC):
            raise ConfigurationError("Host architecture of target '%s' is '%s'"
                                     " but the '-mmic' compiler argument requires '%s'" %
                                     (self['name'], self['host_arch'], INTEL_KNC),
                                     "Select a different target",
                                     "Create a new target with host architecture '%s'" % INTEL_KNC)
        compiler_ctrl = Compiler.controller(self.storage)
        absolute_path = util.which(compiler_cmd)
        compiler_cmd = os.path.basename(compiler_cmd)
        found = []
        known_compilers = [comp for comp in self.compilers().itervalues()]
        for info in Knowledgebase.find_compiler(command=compiler_cmd):
            try:
                compiler_record = self.populate(info.role.keyword)
            except KeyError:
                # Target was not configured with a compiler in this role
                continue
            compiler_path = compiler_record['path']
            if (absolute_path and (compiler_path == absolute_path) or
                    (not absolute_path and (os.path.basename(compiler_path) == compiler_cmd))):
                found.append(compiler_record)
            else:
                # Target was configured with a wrapper compiler so check if that wrapper wraps this compiler
                while 'wrapped' in compiler_record:
                    compiler_record = compiler_ctrl.one(compiler_record['wrapped'])
                    known_compilers.append(compiler_record.installation())
                    compiler_path = compiler_record['path']
                    if (absolute_path and (compiler_path == absolute_path) or
                            (not absolute_path and (os.path.basename(compiler_path) == compiler_cmd))):
                        found.append(compiler_record)
                        break
        if not found:
            parts = ["No compiler in target '%s' matches '%s'." % (self['name'], absolute_path or compiler_cmd),
                     "The known compiler commands are:"]
            parts.extend('  %s (%s)' % (comp.absolute_path, comp.info.short_descr) for comp in known_compilers)
            hints = ("Try one of the valid compiler commands",
                     "Create and select a new target configuration that uses the '%s' compiler" % (
                         absolute_path or compiler_cmd),
                     "Check loaded modules and the PATH environment variable")
            raise ConfigurationError('\n'.join(parts), *hints)
        return found

    def papi_metrics(self, event_type="PRESET", include_modifiers=False):
        if not self.get('papi_source'):
            return []
        return self.get_installation('papi').papi_metrics(event_type, include_modifiers)

    def tau_metrics(self):
        return self.get_installation('tau').tau_metrics()

    def cupti_metrics(self):
        if not self.get('cuda'):
            return []
        # FIXME: not implemented
