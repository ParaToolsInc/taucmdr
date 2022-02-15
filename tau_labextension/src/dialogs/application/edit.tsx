import React from 'react'; 
import ReactDOM from 'react-dom'; 
 
import { Dialog } from '@jupyterlab/apputils'; 
import { Checkbox } from '@jupyterlab/ui-components';
import { Widget } from '@lumino/widgets'; 
 
const writeEditBody = (currentRow: any) => { 
  let openmp = (currentRow['OpenMP'] == 'Yes') ? true : false;
  let pthreads = (currentRow['Pthreads'] == 'Yes') ? true : false;   
  let tbb = (currentRow['TBB'] == 'Yes') ? true : false;
  let mpi = (currentRow['MPI'] == 'Yes') ? true : false; 
  let cuda = (currentRow['CUDA'] == 'Yes') ? true : false;
  let opencl = (currentRow['OpenCL'] == 'Yes') ? true : false;   
  let shmem = (currentRow['SHMEM'] == 'Yes') ? true : false;
  let mpc = (currentRow['MPC'] == 'Yes') ? true : false; 

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
          Linkage:
          <select defaultValue={currentRow['Linkage']} name='linkage'>
          <option value='static'>Static</option>
          <option value='dynamic'>Dynamic</option>
          </select>
        </label>
        <div className='tau-Dialog-checkbox-container'>
          <div className='tau-Dialog-checkbox'>
            <Checkbox defaultChecked={openmp} label='OpenMP' name='openmp'/>
            <Checkbox defaultChecked={pthreads} label='PThreads' name='pthreads'/>
            <Checkbox defaultChecked={tbb} label='TBB' name='tbb'/>
            <Checkbox defaultChecked={mpi} label='MPI' name='mpi'/>
          </div>
          <div>
            <Checkbox defaultChecked={cuda} label='CUDA' name='cuda'/>
            <Checkbox defaultChecked={opencl} label='OpenCL' name='opencl'/>
            <Checkbox defaultChecked={shmem} label='SHMEM' name='shmem'/>
            <Checkbox defaultChecked={mpc} label='MPC' name='mpc'/>
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

export const editApplicationDialog = (currentRow: any, props: Tables.Application) => {
  let body = document.createElement('div');
  ReactDOM.render(writeEditBody(currentRow), body);

  const dialog = new Dialog({
    title: `Edit Application`,
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
        let name = currentRow['Name'];
        let newName = response.value!.name;
        let linkage = response.value!.linkage;
        let openMP = response.value!.openmp;
        let pThreads = response.value!.pthreads;
        let tbb = response.value!.tbb;
        let mpi = response.value!.mpi;
        let cuda = response.value!.cuda;
        let openCL = response.value!.opencl;
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

        props.kernelExecute(`edit_application('${props.projectName}', '${name}', '${newName}', args)`) 
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
