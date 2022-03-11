import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeCopyBody = (name: string) => {
  const copyName = name + '_copy';
  return (
    <div>
      <label>
        Name of new project:
        <br/>
        <input className='tau-Dialog-name' type='text' name='name' defaultValue={copyName}/>
      </label>
      <br/><br/>
      <label>
        T.A.M. Suffix:
        <br/>
        <input className='tau-Dialog-name' type='text' name='name' defaultValue='_copy'/>
      </label>
    </div>
  )
};

class DialogBody extends Widget {
  constructor(domElement: HTMLElement) {
    super({node : domElement});
  }

  getValue() {
    const response = this.node.querySelectorAll('input');
    return Array.from(response);
  }
};

export const copyProjectDialog = (props: Sidebar.Project) => {
  const body = document.createElement('div');
  ReactDOM.render(writeCopyBody(props.projectName), body);

  const dialog = new Dialog({
    title: `Copy ${name}`,
    body: new DialogBody(body),
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.okButton({ label: 'Submit' })
    ]
  });

  dialog.addClass('tau-Dialog-body');
  dialog.launch()
    .then(response => {
      if (response.button.label === 'Submit') {
        const copyProject = response.value![0].value;
        const tamSuffix = response.value![1].value;
        props.kernelExecute(`copy_project('${props.projectName}', '${copyProject}', '${tamSuffix}')`)
          .then((result) => {
            if (result) {
              props.updateProjects();
            }
          });
      }
      dialog.dispose();
    });
}

namespace Sidebar {
  export interface Project {
    projectName: string;
    kernelExecute: (code: string) => Promise<any>;
    updateProjects: () => void;
  }
}
