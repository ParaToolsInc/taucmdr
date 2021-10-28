import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.experiment.create import COMMAND as create_experiment_cmd
from taucmdr.cli.commands.experiment.select import COMMAND as select_experiment_cmd
from taucmdr.cli.commands.experiment.edit import COMMAND as edit_experiment_cmd
from taucmdr.cli.commands.experiment.delete import COMMAND as delete_experiment_cmd

def new_experiment(project, name, target, application, measurement):
    select_project_cmd.main([project])
    try:
        create_experiment_cmd.main([name,
                   '--target', target,
                   '--application', application,
                   '--measurement', measurement])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in creation'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def select_experiment(project, experiment_name):
    select_project_cmd.main([project])
    try:
        select_experiment_cmd.main([experiment_name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in selection'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def edit_experiment(project, name, new_name, target, application, measurement):
    select_project_cmd.main([project])
    try:
        edit_experiment_cmd.main([name,
                   '--new-name', new_name,
                   '--target', target,
                   '--application', application,
                   '--measurement', measurement])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})


def delete_experiment(project, name):
    select_project_cmd.main([project])
    try:
        delete_experiment_cmd.main([name])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})
