import React from 'react'; 
import ReactDOM from 'react-dom'; 
 
import { Dialog } from '@jupyterlab/apputils'; 
import { Checkbox } from '@jupyterlab/ui-components';
import { Widget } from '@lumino/widgets'; 
 
const writeEditBody = (currentRow: any) => { 
  let sample = (currentRow['Sample'] == 'Yes') ? true : false;
  let cuda = (currentRow['CUDA'] == 'Yes') ? true : false;
  let io = (currentRow['I/O'] == 'Yes') ? true : false;
  let mpi = (currentRow['MPI'] == 'Yes') ? true : false;
  let shmem = (currentRow['SHMEM'] == 'Yes') ? true : false;

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
          Profile:
          <select defaultValue={currentRow['Profile']} name='profile'>
          <option value='tau'>Tau</option>
          <option value='merged'>Merged</option>
          <option value='cubex'>Cubex</option>
          <option value='sqlite'>SQLite</option>
          <option value='none'>None</option>
          </select>
        </label>
        <label>
          Trace:
          <select defaultValue={currentRow['Trace']} name='trace'>
          <option value='slog2'>Slog2</option>
          <option value='otf2'>OTF2</option>
          <option value='none'>None</option>
          </select>
        </label>
        <label>
          Source Instrumentation:
          <select defaultValue={currentRow['Source Inst.']} name='sourceInst'>
          <option value='automatic'>Automatic</option>
          <option value='manual'>Manual</option>
          <option value='never'>Never</option>
          </select>
        </label>
        <label>
          Compiler Instrumentation:
          <select defaultValue={currentRow['Compiler Inst.']} name='compilerInst'>
          <option value='always'>Always</option>
          <option value='fallback'>Fallback</option>
          <option value='never'>Never</option>
          </select>
        </label>
        <label>
          OpenMP:
          <select defaultValue={currentRow['OpenMP']} name='openmp'>
          <option value='ignore'>Ignore</option>
          <option value='opari'>OPARI</option>
          <option value='ompt'>OMPT</option>
          </select>
        </label>
        <div className='tau-Dialog-checkbox-container'>
          <div className='tau-Dialog-checkbox'>
            <Checkbox defaultChecked={sample} label='Sample' name='sample'/>
            <Checkbox defaultChecked={cuda} label='CUDA' name='cuda'/>
            <Checkbox defaultChecked={io} label='I/O' name='io'/>
          </div>
          <div>
            <Checkbox defaultChecked={mpi} label='MPI' name='mpi'/>
            <Checkbox defaultChecked={shmem} label='SHMEM' name='shmem'/>
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

export const editMeasurementDialog = (currentRow: any, props: Tables.Measurement) => {
  let body = document.createElement('div');
  ReactDOM.render(writeEditBody(currentRow), body);

  const dialog = new Dialog({
    title: `Edit Measurement`,
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
        let new_name = response.value!.name;
        let profile = response.value!.profile;
        let trace = response.value!.trace;
        let sample = response.value!.sample;
        let sourceInst = response.value!.sourceInst;
        let compilerInst = response.value!.compilerInst;
        let openMP = response.value!.openmp;
        let cuda = response.value!.cuda;
        let io = response.value!.io;
        let mpi = response.value!.mpi;
        let shmem = response.value!.shmem;
        props.kernelExecute(`edit_measurement('${props.projectName}', '${name}', '${new_name}', '${profile}', '${trace}', '${sample}', '${sourceInst}', '${compilerInst}', '${openMP}', '${cuda}', '${io}', '${mpi}', '${shmem}')`)
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
  export interface Measurement {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    measurements: {[key: string]: any};
  }
}


