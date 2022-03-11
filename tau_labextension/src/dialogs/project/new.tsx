import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

class DialogBody extends Widget {
  constructor(domElement: HTMLElement) {
    super({node : domElement});
  }

  getValue() {
    const response = this.node.querySelector('input');
    if (response) {
      return response.value;
    }
    return ''
  }
};

const writeNewBody = () => {
  return (
    <React.Fragment>
      <form className='tau-Dialog-form'>
        <label>
          Name:
          <br/>
          <input className='tau-Dialog-name' type='text' name='name' />
        </label>
      </form>
    </React.Fragment>
  )
}

export const newProjectDialog = (props: Sidebar.Project) => {
  const body = document.createElement('div');
  ReactDOM.render(writeNewBody(), body);

  const dialog = new Dialog({
    title: `New Project`,
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
        props.kernelExecute(`new_project('${response.value}')`)
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
    kernelExecute: (code: string) => Promise<any>;
    updateProjects: () => void;
  }
}
