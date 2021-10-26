import json

from taucmdr.model.project import Project
from taucmdr.model.experiment import Experiment

from taucmdr.cli.commands.initialize import COMMAND as tau_init_cmd
from taucmdr.cli.commands.project.create import COMMAND as create_project_cmd
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.project.edit import COMMAND as edit_project_cmd
from taucmdr.cli.commands.project.delete import COMMAND as delete_project_cmd
from taucmdr.cli.commands.project.copy import COMMAND as copy_project_cmd

from .target import delete_target
from .application import delete_application
from .measurement import delete_measurement
from .experiment import delete_experiment

from .target import copy_target
from .application import copy_application
from .measurement import copy_measurement

from taucmdr.cf.storage.project import ProjectStorageError 
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.compiler.shmem import SHMEM_CC

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
                     {'header': 'Trials', 'function': lambda x, y: len([i for i in x['trials'] if i['number'] in y])},
                     {'header': 'Data Size', 'function': data_size},
                     {'header': 'Target', 'function': lambda x: x['target']['name']},
                     {'header': 'Application', 'function': lambda x: x['application']['name']},
                     {'header': 'Measurement', 'function': lambda x: x['measurement']['name']},
                     {'header': 'TAU Makefile', 'value': 'tau_makefile'}]

trial_columns = [{'header': 'Number', 'value': 'number'},
                {'header': 'Data Size', 'function': lambda x: util.human_size(x.get('data_size', None))},
                {'header': 'Command', 'value': 'command'},
                {'header': 'Description', 'value': 'description'},
                {'header': 'Status', 'value': 'phase'},
                {'header': 'Elapsed Seconds', 'value': 'elapsed'}]

def read_column(source, dashboard_columns, is_experiment=False, is_trial=False):
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
                if (is_experiment and col['header'] == 'Trials'):
                    ctrl = Experiment.controller()
                    expr = ctrl.one({'name': record['name']})
                    trials = [trial['number'] for trial in expr.populate('trials') if trial.populate('experiment')['name'] == record['name']]
                    cell = col['function'](populated, trials)
                else:
                    cell = col['function'](populated)
            else:
                raise InternalError("Invalid column definition: %s" % col)
            row.append(cell)
        rows.append(row)
    keys = rows[0]
    ret_val = {}

    for meas in [dict(zip(keys, values)) for values in rows[1:]]:
        if is_trial:
            name = meas.pop('Number')
        else:
            name = meas.pop('Name')
        ret_val[name] = meas

    return ret_val

def get_project(proj):
    project = {}
    target = proj.populate('targets')
    application = proj.populate('applications')
    measurement = proj.populate('measurements')
    experiment = proj.populate('experiments')
    
    project['name'] = proj['name']
    project['targets'] = read_column(target, target_columns)
    project['applications'] = read_column(application, application_columns)
    project['measurements'] = read_column(measurement, measurement_columns)
    project['experiments'] = read_column(experiment, experiment_columns, is_experiment=True)

    for experiment_name, _ in project['experiments'].items():
        ctrl = Experiment.controller()
        expr = ctrl.one({'name': experiment_name})
        trials = expr.populate('trials')
        exp_trials = [trial for trial in trials if trial.populate('experiment')['name'] == experiment_name]
        project['experiments'][experiment_name]['Trial Data'] = read_column(exp_trials, trial_columns, is_trial=True)

    return project

def get_all_projects():
    try:
        ctrl = Project.controller()
        projects = ctrl.all()

    except ProjectStorageError as e:
        try:
            tau_init_cmd.main([])
            ctrl = Project.controller()
            projects = ctrl.all()

        except SystemExit as e:
            PROJECT_STORAGE.disconnect_filesystem()
            return json.dumps({'status': 'failure', 'data': 'Error in initialization'})

        except Exception as e:
            PROJECT_STORAGE.disconnect_filesystem()
            return json.dumps({'status': 'failure', 'data': e.message})

    if len(projects) == 0:
        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': 'success', 'data': {}})
    
    try:
        project_dict = {}
        for project in projects:
            select_project_cmd.main([project['name']])
            project_dict[project['name']] = get_project(project)

        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': 'success', 'data': project_dict})
    except Exception as e:
        PROJECT_STORAGE.disconnect_filesystem()
        return json.dumps({'status': 'failure', 'data': e.message})

def new_project(name):
    PROJECT_STORAGE.connect_filesystem()
    try:
        create_project_cmd.main([name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in creation'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})


def delete_project(name):
    select_project_cmd.main([name])
    try:
        ctrl = Project.controller()
        project = ctrl.one({'name':name})

        for target in project.populate('targets'):
            delete_target(target['name'])

        for application in project.populate('applications'):
            delete_application(application['name'])

        for measurement in project.populate('measurements'):
            delete_measurement(measurement['name'])

        for experiment in project.populate('experiments'):
            delete_experiment(experiment['name'])

        delete_project_cmd.main([name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def copy_project(name, new_name, suffix):
    try:
        create_project_cmd.main([new_name])
        select_project_cmd.main([new_name])

        ctrl = Project.controller()
        project = ctrl.one({'name':name})

        curr_targets = project['targets'].copy()
        curr_applications = project['applications'].copy()
        curr_measurements = project['measurements'].copy()
        

        for target in project.populate('targets'):
            target_name = target['name']
            copy_target(name, target_name, target_name + suffix, True)

        for application in project.populate('applications'):
            application_name = application['name']
            copy_application(name, application_name, application_name + suffix, True)

        for measurement in project.populate('measurements'):
            measurement_name = measurement['name']
            copy_measurement(name, measurement_name, measurement_name + suffix, True)

        ctrl.update({'targets': curr_targets}, {'name': name})
        ctrl.update({'applications': curr_applications}, {'name': name})
        ctrl.update({'measurements': curr_measurements}, {'name': name})

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in copy'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def edit_project(name, new_name):
    PROJECT_STORAGE.connect_filesystem()
    try:
        edit_project_cmd.main([name, '--new-name', new_name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})
