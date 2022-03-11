import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeCopyBody = (applicationName: string) => {
  const copyName = applicationName + '_copy';

  return (
    <div>
      <label>
        Name of new application:
        <br/>
        <input className='tau-Dialog-name' type='text' name='name' defaultValue={copyName}/>
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

export const copyApplicationDialog = (applicationName: string, props: Tables.Application) => {
  const body = document.createElement('div');
  ReactDOM.render(writeCopyBody(applicationName), body);

  const dialog = new Dialog({
    title: 'Copy Application',
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
        const newName = response.value![0].value;
        props.kernelExecute(`copy_application('${props.projectName}', '${applicationName}', '${newName}')`)
          .then((result) => {
            if (result) {
              props.updateProject(props.projectName);
            }
          });
      }
      dialog.dispose();
    });
}

namespace Tables {
  export interface Application {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    applications: {[key: string]: any};
  }
}
