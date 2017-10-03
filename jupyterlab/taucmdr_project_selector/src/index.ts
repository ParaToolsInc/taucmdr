import {
    Widget
} from '@phosphor/widgets';

import {
    JupyterLab, JupyterLabPlugin, ILayoutRestorer
} from '@jupyterlab/application';

import {
    ICommandPalette
} from '@jupyterlab/apputils';

import {
    Session
} from '@jupyterlab/services';

import '../style/index.css';

const widget_id = 'taucmdr_project_selector';

class ProjectSelectorWidget extends Widget {

    readonly session_path: string = 'taucmdr.ipynb';

    readonly kernel_code: string = `
import os,sys,subprocess
tauLoc=subprocess.Popen(["bash","-c","which tau"],
                       shell=False,stdout=subprocess.PIPE).communicate()[0].replace("\\n","")
tauHome=tauLoc.replace("/bin/tau","")
tauPackages=tauHome+"/packages"
os.environ["__TAU_HOME__"]=tauHome
os.environ["__TAU_SCRIPT__"]=tauLoc
sys.path.insert(0,tauPackages)
from taucmdr.model.project import Project
print(Project.controller().all())
`;

    contentDiv: HTMLDivElement;
    session: Session.ISession;

    constructor() {
        super();
        this.id = widget_id;
        this.title.label = 'Projects';
        this.title.closable = true;

        this.contentDiv = document.createElement("div");
        let button = document.createElement('button');
        button.appendChild(document.createTextNode("Refresh project list"));
        button.addEventListener('click', () => {this.list_projects()});
        this.contentDiv.appendChild(button);
        this.node.appendChild(this.contentDiv);

    };

    start_session(): boolean {
        let result = false;
        if(!this.session) {
            Session.findByPath(this.session_path).then(model => {
                Session.connectTo(model.id).then(s => {
                    this.session = s;
                    console.log(`Connected to an existing session ${model.id}`);
                    result = true;
                });
            }, () => {
                let options: Session.IOptions = {
                    kernelName: 'python',
                    path: this.session_path
                };
                Session.startNew(options).then(s => {
                    this.session = s;
                    console.log(`Started a new session ${s.id}`);
                    result = true;
                });
            });
            return result;
        } else {
            return true;
        }
    };

    list_projects(): void {
        if(this.start_session()) {
            let future = this.session.kernel.requestExecute({code: this.kernel_code});
            future.onReply = msg => {
                console.log("future fulfilled");
                console.log(msg)
            };
            future.onIOPub = msg => {
                console.log("future iopub");
                console.log(msg);
                if(msg.header.msg_type == "stream") {
                    this.contentDiv.appendChild(document.createTextNode(msg.content.text.toString()));
                }
            };
        }
    };
}

function activate(app: JupyterLab, palette: ICommandPalette, restorer: ILayoutRestorer) {
    console.log('JupyterLab extension taucmdr_project_selector is activated!');

    // Declare a widget variable
    let widget: ProjectSelectorWidget;

    widget = new ProjectSelectorWidget();

    app.shell.addToLeftArea(widget, {rank: 1000});

    restorer.add(widget, widget_id);
}

/**
 * Initialization data for the jupyterlab_xkcd extension.
 */
const extension: JupyterLabPlugin<void> = {
    id: widget_id,
    autoStart: true,
    requires: [ICommandPalette, ILayoutRestorer],
    activate: activate
};

export default extension;