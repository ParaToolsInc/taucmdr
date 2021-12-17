import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.project.select import COMMAND as select_project_cmd
from taucmdr.cli.commands.trial.edit import COMMAND as edit_trial_cmd
from taucmdr.cli.commands.trial.renumber import COMMAND as renumber_trial_cmd
from taucmdr.cli.commands.trial.delete import COMMAND as delete_trial_cmd

def edit_trial(project, number, new_number, description):
    select_project_cmd.main([project])
    try:
        renumber_trial_cmd.main([number, '--to', new_number])
        edit_trial_cmd.main([new_number, '--description', description])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in edit'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

def delete_trial(project, number):
    select_project_cmd.main([project])
    try:
        delete_trial_cmd.main([number])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

