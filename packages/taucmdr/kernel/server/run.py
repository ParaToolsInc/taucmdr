from .pages.app import app

def start():
    app.run_server(mode='jupyterlab', debug=False, host='0.0.0.0', port=8889, height=800)

if __name__ == '__main__':
    app.run_server(mode='jupyterlab', debug=False, host='0.0.0.0', port=8889, height=800)
