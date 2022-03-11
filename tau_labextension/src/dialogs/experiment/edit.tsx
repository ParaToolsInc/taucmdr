import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeEditBody = (currentRow: any, project: any) => {
  return (
    <React.Fragment>
      <form className='tau-Dialog-form'>
        <label>
          Name:
          <br/>
          <input className='tau-Dialog-name' type='text' name='name' defaultValue={currentRow['Name']}/>
        </label>
        <br/><br/>
        <label>
          Target:
          <select name='target' defaultValue={currentRow['Target']}>
          {
            Object.keys(project['targets']).map((target: string) =>
              <option key={target} value={target}>{target}</option>)
          }
          </select>
        </label>
        <label>
          Application:
          <select name='application' defaultValue={currentRow['Application']}>
          {
            Object.keys(project['applications']).map((application: string) =>
              <option key={application} value={application}>{application}</option>)
          }
          </select>
        </label>
        <label>
          Measurement:
          <select name='measurement' defaultValue={currentRow['Measurement']}>
          {
            Object.keys(project['measurements']).map((measurement: string) =>
              <option key={measurement} value={measurement}>{measurement}</option>)
          }
          </select>
        </label>
      </form>
    </React.Fragment>
  )
}

class DialogBody extends Widget {
    constructor(domElement: HTMLElement) {
        super({node : domElement});
    }

    getValue() {
        const response = this.node.querySelectorAll('input, select');
        const responseDict: { [id: string] : string } = {};
        Object.entries(response).map((resp) => {
            const elem = resp[1];
            if (resp[1].tagName === 'INPUT') {
                const inputElem = elem as HTMLInputElement;
                if (inputElem.type === 'text') {
                        responseDict[inputElem.name] = inputElem.value;
                } else {
                        responseDict[inputElem.name] = inputElem.checked.toString();
                }
            } else {
                const selectElem = elem as HTMLSelectElement;
                responseDict[selectElem.name] = selectElem.value;
            }
        });
        return responseDict;
    }
};

export const editExperimentDialog = (currentRow: any, props: Tables.Experiment) => {
  const body = document.createElement('div');
  ReactDOM.render(writeEditBody(currentRow, props.project), body);

  const dialog = new Dialog({
    title: `Edit Experiment`,
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
        const name = currentRow['Name'];
        const newName = response.value!.name;
        const target = response.value!.target;
        const application = response.value!.application;
        const measurement = response.value!.measurement;
        props.kernelExecute(`edit_experiment('${props.projectName}', '${name}', '${newName}', '${target}', '${application}', '${measurement}')`)
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
  export interface Experiment {
    project: any;
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    experiments: {[key: string]: any};
  }
}
