import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Checkbox } from '@jupyterlab/ui-components';
import { Widget } from '@lumino/widgets';


const writeNewBody = () => {
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
          Linkage:
          <select defaultValue='static' name='linkage'>
          <option value='static'>Static</option>
          <option value='dynamic'>Dynamic</option>
          </select>
        </label>

        <div className='tau-Dialog-checkbox-container'>
          <div className='tau-Dialog-checkbox'>
            <Checkbox label='OpenMP' name='openMP'/>
            <Checkbox label='PThreads' name='pThreads'/>
            <Checkbox label='TBB' name='tbb'/>
            <Checkbox label='MPI' name='mpi'/>
          </div>
          <div>
            <Checkbox label='CUDA' name='cuda'/>
            <Checkbox label='OpenCL' name='openCL'/>
            <Checkbox label='SHMEM' name='shmem'/>
            <Checkbox label='MPC' name='mpc'/>
          </div>
        </div>
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

export const newApplicationDialog = () => {

  let body = document.createElement('div');
  ReactDOM.render(writeNewBody(), body);

  const dialog = new Dialog({
    title: `New Application`,
    body: new DialogBody(body),
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }), 
      Dialog.okButton({ label: 'Submit' })
    ]   
  }); 

  dialog.addClass('tau-Dialog-body');

  return dialog;

}
