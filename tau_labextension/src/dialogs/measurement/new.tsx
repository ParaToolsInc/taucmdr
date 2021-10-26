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
          Profile:
          <select defaultValue='tau' name='profile'>
            <option value='tau'>Tau</option>
            <option value='merged'>Merged</option>
            <option value='cubex'>Cubex</option>
            <option value='sqlite'>SQLite</option>
            <option value='none'>None</option>
          </select>
        </label>
        <label>
          Trace:
          <select defaultValue='none' name='trace'>
            <option value='slog2'>Slog2</option>
            <option value='otf2'>OTF2</option>
            <option value='none'>None</option>
          </select>
        </label>
        <label>
          Source Instrumentation:
          <select defaultValue='never' name='sourceInst'>
            <option value='automatic'>Automatic</option>
            <option value='manual'>Manual</option>
            <option value='never'>Never</option>
          </select>
        </label>
        <label>
          Compiler Instrumentation:
          <select defaultValue='never' name='compilerInst'>
            <option value='always'>Always</option>
            <option value='fallback'>Fallback</option>
            <option value='never'>Never</option>
          </select>
        </label>
        <label>
          OpenMP:
          <select defaultValue='ignore' name='openMP'>
            <option value='ignore'>Ignore</option>
            <option value='opari'>OPARI</option>
            <option value='ompt'>OMPT</option>
          </select>
        </label>
        <div className='tau-Dialog-checkbox-container'>
          <div className='tau-Dialog-checkbox'>
            <Checkbox label='Sample' name='sample'/>
            <Checkbox label='CUDA' name='cuda'/>
            <Checkbox label='I/O' name='io'/>
          </div>
          <div>
            <Checkbox label='MPI' name='mpi'/>
            <Checkbox label='SHMEM' name='shmem'/>
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

export const newMeasurementDialog = () => {

  let body = document.createElement('div');
  ReactDOM.render(writeNewBody(), body);

  const dialog = new Dialog({
    title: `New Measurement`,
    body: new DialogBody(body),
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }), 
      Dialog.okButton({ label: 'Submit' })
    ]   
  }); 

  dialog.addClass('tau-Dialog-body');

  return dialog;

}
