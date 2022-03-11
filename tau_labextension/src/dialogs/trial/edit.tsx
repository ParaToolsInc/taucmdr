import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeEditBody = (currentRow: any) => {
  return (
    <React.Fragment>
      <form className='tau-Dialog-form'>
        <label>
          Number:
          <br/>
          <input className='tau-Dialog-name' type='text' name='number' defaultValue={currentRow['Number']}/>
        </label>
        <br/><br/>
        <label>
          Description:
          <br/>
          <input className='tau-Dialog-name' type='text' name='description' defaultValue={currentRow['Description']}/>
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
    const response = this.node.querySelectorAll('input');
    const responseDict: { [id: string] : string } = {};
    Object.entries(response).map((resp) => {
      const inputElem = resp[1] as HTMLInputElement;
      responseDict[inputElem.name] = inputElem.value;
    });
    return responseDict;
  }
};

export const editTrialDialog = (currentRow: any, props: Tables.Trial) => {
  const body = document.createElement('div');
  ReactDOM.render(writeEditBody(currentRow), body);

  const dialog = new Dialog({
    title: `Edit Trial`,
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
        const num = currentRow['Number'];
        const newNum = response.value!.number;
        const description = response.value!.description;
        props.kernelExecute(`edit_trial('${props.projectName}', '${num}', '${newNum}', "${description}")`)
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
  export interface Trial {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    experiment: {[key: string]: {[key: string]: any}}
    setSelectedExperiment: (experiment: string | null) => void;
    selectedExperiment: string;
  }
}
