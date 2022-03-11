import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Checkbox } from '@jupyterlab/ui-components';
import { Widget } from '@lumino/widgets';

const writeEditBody = (currentRow: any) => {
  const sample = (currentRow['Sample'] === 'Yes') ? true : false;
  const cuda = (currentRow['CUDA'] === 'Yes') ? true : false;
  const io = (currentRow['I/O'] === 'Yes') ? true : false;
  const mpi = (currentRow['MPI'] === 'Yes') ? true : false;
  const shmem = (currentRow['SHMEM'] === 'Yes') ? true : false;

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

export const editMeasurementDialog = (currentRow: any, props: Tables.Measurement) => {
  const body = document.createElement('div');
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
      if (response.button.label === 'Submit') {
        const name = currentRow['Name'];
        const newName = response.value!.name;
        const profile = response.value!.profile;
        const trace = response.value!.trace;
        const sample = response.value!.sample;
        const sourceInst = response.value!.sourceInst;
        const compilerInst = response.value!.compilerInst;
        const openMP = response.value!.openmp;
        const cuda = response.value!.cuda;
        const io = response.value!.io;
        const mpi = response.value!.mpi;
        const shmem = response.value!.shmem;

        props.kernelExecute(`
            args = {'profile': '${profile}',
                'trace': '${trace}',
                'sample': '${sample}',
                'source_inst': '${sourceInst}',
                'compiler_inst': '${compilerInst}',
                'openmp': '${openMP}',
                'cuda': '${cuda}',
                'io': '${io}',
                'mpi': '${mpi}',
                'shmem': '${shmem}'
                }`
        )

        props.kernelExecute(`edit_measurement('${props.projectName}', '${name}', '${newName}', args)`)
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


