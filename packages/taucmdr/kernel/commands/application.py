import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.application.create import COMMAND as create_application_cmd
from taucmdr.cli.commands.application.edit import COMMAND as edit_application_cmd
from taucmdr.cli.commands.application.delete import COMMAND as delete_application_cmd
from taucmdr.cli.commands.application.copy import COMMAND as copy_application_cmd

def new_application(project, name, linkage, openmp, pthreads, tbb, mpi, cuda, opencl, shmem, mpc):
    select_project_cmd.main([project])
    try:
        create_application_cmd.main([name,
                    '--linkage', linkage,
                    '--openmp', openmp,
                    '--pthreads', pthreads,
                    '--tbb', tbb,
                    '--mpi', mpi,
                    '--cuda', cuda,
                    '--opencl', opencl,
                    '--shmem', shmem,
                    '--mpc', mpc])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in creation'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def edit_application(project, name, new_name, linkage, openmp, pthreads, tbb, mpi, cuda, opencl, shmem, mpc):
    select_project_cmd.main([project])
    try:
        edit_application_cmd.main([name,
                    '--new-name', new_name,
                    '--linkage', linkage,
                    '--openmp', openmp,
                    '--pthreads', pthreads,
                    '--tbb', tbb,
                    '--mpi', mpi,
                    '--cuda', cuda,
                    '--opencl', opencl,
                    '--shmem', shmem,
                    '--mpc', mpc])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})


def copy_application(project, name, new_name, is_project=False):
    if not is_project:
        select_project_cmd.main([project])

    try:
        copy_application_cmd.main([name, new_name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in copy'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def delete_application(name):
    try:
        delete_application_cmd.main([name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

