import json
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.trial.delete import COMMAND as delete_trial

def delete_trial(number):
    try:
        delete_trial.main([number])

    except SystemExit as e:
        return json.dumps({'status': 'failure', 'message': 'Error in deletion'})

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': e.message})

    PROJECT_STORAGE.disconnect_filesystem()
    return json.dumps({'status': 'success'})

