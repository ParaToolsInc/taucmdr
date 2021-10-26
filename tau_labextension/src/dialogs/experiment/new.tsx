import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeNewBody = (project: any) => {
  return (
    <React.Fragment>
      <form className='tau-Dialog-form'>
        <label>
          Name:
          <br/>
          <input className='tau-Dialog-name' type='text' name='name' />
        </label>
        <br/><br/>
        <label>
          Target:
          <select name='target'>
          {
            Object.keys(project['targets']).map((target: string) =>
              <option key={target} value={target}>{target}</option>)
          }
          </select>
        </label>
        <label>
          Application:
          <select name='application'>
          {
            Object.keys(project['applications']).map((application: string) =>
              <option key={application} value={application}>{application}</option>)
          }
          </select>
        </label>
        <label>
          Measurement:
          <select name='measurement'>
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
    let response = this.node.querySelectorAll('input, select');
    let responseDict: { [id: string] : string } = {};
    Object.entries(response).map((resp) => {
      let elem = resp[1];
      if (resp[1].tagName == 'INPUT') {
        let inputElem = elem as HTMLInputElement;
        if (inputElem.type == 'text') {
            responseDict[inputElem.name] = inputElem.value;
        } else {
            responseDict[inputElem.name] = inputElem.checked.toString();
        }
      } else {
        let selectElem = elem as HTMLSelectElement;
        responseDict[selectElem.name] = selectElem.value;
      }
    });
    return responseDict;
  }
};

export const newExperimentDialog = (project: any) => {

  let body = document.createElement('div');
  ReactDOM.render(writeNewBody(project), body);

  const dialog = new Dialog({
    title: `New Experiment`,
    body: new DialogBody(body),
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }), 
      Dialog.okButton({ label: 'Submit' })
    ]   
  }); 

  dialog.addClass('tau-Dialog-body');

  return dialog;

}
