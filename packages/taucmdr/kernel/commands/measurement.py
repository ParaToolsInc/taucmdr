import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.measurement.create import COMMAND as create_measurement_cmd
from taucmdr.cli.commands.measurement.edit import COMMAND as edit_measurement_cmd
from taucmdr.cli.commands.measurement.delete import COMMAND as delete_measurement_cmd
from taucmdr.cli.commands.measurement.copy import COMMAND as copy_measurement_cmd

def new_measurement(project, name, profile, trace, sample, source_inst, compiler_inst, openmp, cuda, io, mpi, shmem):
    select_project_cmd.main([project])
    try:
        create_measurement_cmd.main([name,
                    '--profile', profile,
                    '--trace', trace,
                    '--sample', sample,
                    '--source-inst', source_inst,
                    '--compiler-inst', compiler_inst,
                    '--openmp', openmp,
                    '--cuda', cuda,
                    '--io', io,
                    '--mpi', mpi,
                    '--shmem', shmem])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in creation'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def edit_measurement(project, name, new_name, profile, trace, sample, source_inst, compiler_inst, openmp, cuda, io, mpi, shmem):
    select_project_cmd.main([project])
    try:
        edit_measurement_cmd.main([name,
                    '--new-name', new_name,
                    '--profile', profile,
                    '--trace', trace,
                    '--sample', sample,
                    '--source-inst', source_inst,
                    '--compiler-inst', compiler_inst,
                    '--openmp', openmp,
                    '--cuda', cuda,
                    '--io', io,
                    '--mpi', mpi,
                    '--shmem', shmem])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})


def copy_measurement(project, name, new_name, is_project=False):
    if not is_project:
        select_project_cmd.main([project])
    
    try:
        copy_measurement_cmd.main([name, new_name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in copy'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def delete_measurement(name):
    try:
        delete_measurement_cmd.main([name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})
