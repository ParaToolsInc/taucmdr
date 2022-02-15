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

export const newApplicationDialog = (props: Dashboard.Application) => {
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
  dialog.launch()
    .then(response => {
      if (response.button.label == 'Submit') {
        let name = response.value!.name;
        let linkage = response.value!.linkage;
        let openMP = response.value!.openMP;
        let pThreads = response.value!.pThreads;
        let tbb = response.value!.tbb;
        let mpi = response.value!.mpi;
        let cuda = response.value!.cuda;
        let openCL = response.value!.openCL;
        let shmem = response.value!.shmem;
        let mpc = response.value!.mpc;

        props.kernelExecute(`
            args = {'linkage': '${linkage}', 
                'openmp': '${openMP}', 
                'pthreads': '${pThreads}', 
                'tbb': '${tbb}', 
                'mpi': '${mpi}', 
                'cuda': '${cuda}', 
                'opencl': '${openCL}', 
                'shmem': '${shmem}',
                'mpc': '${mpc}' 
            }`
        )

        props.kernelExecute(`new_application('${props.projectName}', '${name}', args)`) 
          .then((result) => {
            if (result) {
              props.updateProject(props.projectName);
            }
          });
      }

      dialog.dispose(); 
    });
}

namespace Dashboard {
  export interface Application {
    projectName: string;
    kernelExecute: (code: string) => Promise<any>;
    updateProject: (project: string) => void; 
  }
}
