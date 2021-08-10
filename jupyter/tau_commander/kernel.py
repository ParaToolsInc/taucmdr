import os
import sys
import json

parent_dir = os.path.abspath(os.path.join(os.path.abspath("."), "../.."))
sys.path.insert(0, os.path.join(parent_dir, 'packages'))

from taucmdr.model.project import Project
from taucmdr.cli.commands.project.select import COMMAND as select_project

from taucmdr.cli.commands.project.create import COMMAND as create_project
from taucmdr.cli.commands.target.create import COMMAND as create_target
from taucmdr.cli.commands.application.create import COMMAND as create_application
from taucmdr.cli.commands.measurement.create import COMMAND as create_measurement
from taucmdr.cli.commands.experiment.create import COMMAND as create_experiment

from taucmdr.cf.storage.levels import PROJECT_STORAGE

from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.compiler.shmem import SHMEM_CC
from taucmdr.cli.cli_view import ListCommand
from taucmdr.model.target import Target
from taucmdr.model.compiler import Compiler
from taucmdr import util

def data_size(expr):
    return util.human_size(sum(int(trial.get('data_size', 0)) for trial in expr['trials']))


target_columns = [{'header': 'Name', 'value': 'name', 'align': 'r'},
                     {'header': 'Host OS', 'value': 'host_os'},
                     {'header': 'Host Arch', 'value': 'host_arch'},
                     {'header': 'Host Compilers', 'function':
                      lambda data: data[CC.keyword]['family']},
                     {'header': 'MPI Compilers', 'function':
                      lambda data: data.get(MPI_CC.keyword, {'family': 'None'})['family']},
                     {'header': 'SHMEM Compilers', 'function':
                      lambda data: data.get(SHMEM_CC.keyword, {'family': 'None'})['family']}]


application_columns = [{'header': 'Name', 'value': 'name', 'align': 'r'},
                     {'header': 'Linkage', 'value': 'linkage'},
                     {'header': 'OpenMP', 'yesno': 'openmp'},
                     {'header': 'Pthreads', 'yesno': 'pthreads'},
                     {'header': 'TBB', 'yesno': 'tbb'},
                     {'header': 'MPI', 'yesno': 'mpi'},
                     {'header': 'CUDA', 'yesno': 'cuda'},
                     {'header': 'OpenCL', 'yesno': 'opencl'},
                     {'header': 'SHMEM', 'yesno': 'shmem'},
                     {'header': 'MPC', 'yesno': 'mpc'}]

measurement_columns = [{'header': 'Name', 'value': 'name', 'align': 'r'},
                     {'header': 'Profile', 'value': 'profile'},
                     {'header': 'Trace', 'value': 'trace'},
                     {'header': 'Sample', 'yesno': 'sample'},
                     {'header': 'Source Inst.', 'value': 'source_inst'},
                     {'header': 'Compiler Inst.', 'value': 'compiler_inst'},
                     {'header': 'OpenMP', 'value': 'openmp'},
                     {'header': 'CUDA', 'yesno': 'cuda'},
                     {'header': 'I/O', 'yesno': 'io'},
                     {'header': 'MPI', 'yesno': 'mpi'},
                     {'header': 'SHMEM', 'yesno': 'shmem'}]

experiment_columns = [{'header': 'Name', 'value': 'name', 'align': 'r'},
                     {'header': 'Trials', 'function': lambda x: len(x['trials'])},
                     {'header': 'Data Size', 'function': data_size},
                     {'header': 'Target', 'function': lambda x: x['target']['name']},
                     {'header': 'Application', 'function': lambda x: x['application']['name']},
                     {'header': 'Measurement', 'function': lambda x: x['measurement']['name']},
                     {'header': 'TAU Makefile', 'value': 'tau_makefile'}]

class TauKernel(object):

    current_project = None
    
    @staticmethod
    def read_column(source, dashboard_columns):
        header_row = [col['header'] for col in dashboard_columns]
        rows = [header_row]
        for record in source:
            populated = record.populate(context=False)
            row = []
            for col in dashboard_columns:
                if 'value' in col:
                    try:
                       cell = populated[col['value']]
                    except KeyError:
                        cell = 'N/A'
                elif 'yesno' in col:
                    cell = 'Yes' if populated.get(col['yesno'], False) else 'No'
                elif 'function' in col:
                    cell = col['function'](populated)
                else:
                    raise InternalError("Invalid column definition: %s" % col)
                row.append(cell)
            rows.append(row)
        keys = rows[0]
        ret_val = {}
        for meas in [dict(zip(keys, values)) for values in rows[1:]]:
            name = meas.pop('Name')
            ret_val[name] = meas

        return ret_val

    @staticmethod
    def get_project(proj):
        project = {}
        target = proj.populate('targets')
        application = proj.populate('applications')
        measurement = proj.populate('measurements')
        experiment = proj.populate('experiments')

        project['name'] = proj['name']
        project['targets'] = TauKernel.read_column(target, target_columns)
        project['applications'] = TauKernel.read_column(application, application_columns)
        project['measurements'] = TauKernel.read_column(measurement, measurement_columns)
        project['experiments'] = TauKernel.read_column(experiment, experiment_columns)
        return project

    @staticmethod
    def get_all_projects():
        ctrl = Project.controller()
        TauKernel.current_project = ctrl.selected()['name']

        projects = ctrl.all()
        project_dict = {}
        for project in projects:
            select_project.main([project['name']])
            project_dict[project['name']] = TauKernel.get_project(project)

        return project_dict

    @staticmethod
    def refresh():
        projects = TauKernel.get_all_projects()
        json_ret = json.dumps(projects)
        PROJECT_STORAGE.disconnect_filesystem()
        return json_ret

    @staticmethod
    def change_project(project_name):
        TauKernel.current_project = project_name
        return

    @staticmethod
    def new_project(name):
        PROJECT_STORAGE.connect_filesystem()
        try:
            create_project.main([name])

        except SystemExit as e:
            return json.dumps({'status': False, 'message': 'Error in creation'})

        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': True})

    @staticmethod
    def new_target(name, host_os, host_arch, host_compiler, mpi_compiler, shmem_compiler):
        select_project.main([TauKernel.current_project])
        try:
            create_target.main([name, 
                        '--os', host_os, 
                        '--arch', host_arch, 
                        '--compilers', host_compiler, 
                        '--mpi-wrappers', mpi_compiler, 
                        '--shmem-compilers', shmem_compiler])
        
        except SystemExit as e:
            return json.dumps({'status': False, 'message': 'Error in creation'})

        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': True})

    @staticmethod
    def new_application(name, linkage, openmp, cuda, pthreads, opencl, tbb, shmem, mpi, mpc):
        select_project.main([TauKernel.current_project])
        try:
            create_application.main([name,
                        '--linkage', linkage,
                        '--openmp', openmp,
                        '--cuda', cuda,
                        '--pthreads', pthreads,
                        '--opencl', opencl,
                        '--tbb', tbb,
                        '--shmem', shmem,
                        '--mpi', mpc])

        except SystemExit as e:
            return json.dumps({'status': False, 'message': 'Error in creation'})

        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': True})

    @staticmethod
    def new_measurement(name, profile, trace, source_inst, compiler_inst, openmp, sample, mpi, cuda, shmem, io):
        select_project.main([TauKernel.current_project])
        try:
            create_measurement.main([name,
                        '--profile', profile,
                        '--trace', trace,
                        '--source-inst', source_inst,
                        '--compiler-inst', compiler_inst,
                        '--openmp', openmp,
                        '--sample', sample,
                        '--mpi', mpi,
                        '--cuda', cuda,
                        '--shmem', shmem,
                        '--io', io])

        except SystemExit as e:
            return json.dumps({'status': False, 'message': 'Error in creation'})

        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': True})

    @staticmethod
    def new_experiment(name, target, application, measurement, record):
        select_project.main([TauKernel.current_project])
        try:
            create_experiment.main([name,
                       '--target', target,
                       '--application', application,
                       '--measurement', measurement,
                       '--record-output', record])

        except SystemExit as e:
            return json.dumps({'status': False, 'message': 'Error in creation'})

        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': True})
