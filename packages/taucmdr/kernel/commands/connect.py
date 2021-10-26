import json

def connect():
    try:
        from taucmdr import EXIT_SUCCESS
        return json.dumps({'status': 'success'})
    except Exception as e:
        return json.dumps({'status': 'failure', 'data': e.message})
