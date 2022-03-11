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

export const newMeasurementDialog = (props: Dashboard.Measurement) => {
  const body = document.createElement('div');
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
  dialog.launch()
    .then(response => {
      if (response.button.label === 'Submit') {
        const name = response.value!.name;
        const profile = response.value!.profile;
        const trace = response.value!.trace;
        const sample = response.value!.sample;
        const sourceInst = response.value!.sourceInst;
        const compilerInst = response.value!.compilerInst;
        const openMP = response.value!.openMP;
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

        props.kernelExecute(`new_measurement('${props.projectName}', '${name}', args)`)
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
  export interface Measurement {
    projectName: string;
    kernelExecute: (code: string) => Promise<any>;
    updateProject: (project: string) => void;
  }
}
