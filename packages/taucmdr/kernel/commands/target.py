import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.target.create import COMMAND as create_target_cmd
from taucmdr.cli.commands.target.edit import COMMAND as edit_target_cmd
from taucmdr.cli.commands.target.copy import COMMAND as copy_target_cmd
from taucmdr.cli.commands.target.delete import COMMAND as delete_target_cmd

def new_target(project, name, host_os, host_arch, host_compiler, mpi_compiler, shmem_compiler):
    select_project_cmd.main([project])
    try:
        create_target_cmd.main([name, 
                    '--os', host_os, 
                    '--arch', host_arch, 
                    '--compilers', host_compiler, 
                    '--mpi-wrappers', mpi_compiler, 
                    '--shmem-compilers', shmem_compiler])
    
    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in creation'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def edit_target(project, name, new_name, host_os, host_arch, host_compiler, mpi_compiler, shmem_compiler):
    select_project_cmd.main([project])
    try:
        edit_target_cmd.main([name, 
                    '--new-name', new_name,
                    '--os', host_os, 
                    '--arch', host_arch, 
                    '--compilers', host_compiler, 
                    '--mpi-wrappers', mpi_compiler, 
                    '--shmem-compilers', shmem_compiler])
    
    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})


def copy_target(project, name, new_name, is_project=False):
    if not is_project:
        select_project_cmd.main([project])

    try:
        copy_target_cmd.main([name, new_name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in copy'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})


def delete_target(name):
    try:
        delete_target_cmd.main([name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

