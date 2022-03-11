import React from 'react';
import ReactDOM from 'react-dom';

import {
  Dialog,
  WidgetTracker
} from '@jupyterlab/apputils';

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

const writeEditBody = (project: string) => {
  return (
    <React.Fragment>
      <form className='tau-Dialog-form'>
        <label>
          Edit name:
          <br/>
          <input className='tau-Dialog-name' type='text' name='name' defaultValue={project}/>
        </label>
      </form>
    </React.Fragment>
  )
}

export const editProjectDialog = (props: Sidebar.Project) => {
  const body = document.createElement('div');
  ReactDOM.render(writeEditBody(props.projectName), body);

  const dialog = new Dialog({
    title: `Edit Project`,
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
        props.kernelExecute(`edit_project('${props.projectName}', '${response.value}')`)
          .then((result) => {
            if (result) {
              props.updateProjects();
              const exists = props.tracker.find((widget) => {
                return widget.id === `project-${props.projectName}`;
              });

              if (exists) {
                exists.id = `project-${response.value}` as string;
                exists.title.label = `${response.value} Dashboard`;
                return;
              }
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
    tracker: WidgetTracker;
  }
}
