import React from 'react';
import ReactDOM from 'react-dom';

import { KernelModel } from '../../KernelModel';
import { Dialog } from '@jupyterlab/apputils';
import { Checkbox } from '@jupyterlab/ui-components';
import { Widget } from '@lumino/widgets';

import { IMimeBundle } from '@jupyterlab/nbformat'; 
import { ProjectList } from '../interfaces';

const writeEditBody = (model: KernelModel, form: string, currentRow: any, currentProject: any) => {

    let bundle = model.output['data'] as IMimeBundle;
    let string_output = bundle['text/plain'] as string;
    let json = JSON.parse(string_output.replace(/\'/g, '')) as ProjectList;

    if (form == 'Project') {

        return (
            <React.Fragment>
                <form className='tau-dialog-form'>
                    <label>
                        Edit name:
                        <br/>
                        <input className='tau-dialog-name' type='text' name='name' defaultValue={currentRow.name}/>
                    </label>
                </form>
            </React.Fragment>
        )
    }

    if (form == 'Target') {
	
        return (
            <React.Fragment>
                <form className='tau-dialog-form'>
                    <label>
                        Name:
                        <br/>
                        <input className='tau-dialog-name' type='text' name='name' defaultValue={currentRow.name} />
                    </label>
                    <br/><br/>
                    <label>
                      Host OS:
                      <select defaultValue={currentRow.hostOS} name='hostos'>
                        <option value='Darwin'>Darwin</option>
                        <option value='Linux'>Linux</option>
                        <option value='CNK'>CNK</option>
                        <option value='CNL'>CNL</option>
                        <option value='Android'>Android</option>
                      </select>
                    </label>
                    <label>
                      Host Arch:
                      <select defaultValue={currentRow.hostArch} name='hostArch'>
                        <option value='x86_64'>x86_64</option>
                        <option value='KNC'>KNC</option>
                        <option value='KNL'>KNL</option>
                        <option value='BGL'>BGL</option>
                        <option value='BGP'>BGP</option>
                        <option value='BGQ'>BGQ</option>
                        <option value='IBM64'>IBM64</option>
                        <option value='ppc64'>ppc64</option>
                        <option value='ppc64le'>ppc64le</option>
                        <option value='aarch32'>aarch32</option>
                        <option value='aarch64'>aarch64</option>
                      </select>
                    </label>
                    <label>
                      Host Compilers:
                      <select defaultValue={currentRow.hostCompilers} name='hostCompiler'>
                        <option value='Apple'>Apple</option>
                        <option value='Arm'>Arm</option>
                        <option value='bluegene'>BlueGene</option>
                        <option value='Cray'>Cray</option>
                        <option value='GNU'>GNU</option>
                        <option value='IBM'>IBM</option>
                        <option value='Intel'>Intel</option>
                        <option value='PGI'>PGI</option>
                        <option value='System'>System</option>
                      </select>
                    </label>
                    <label>
                      MPI Compilers:
                      <select defaultValue={currentRow.mpiCompilers} name='mpiCompiler'>
                        <option value='Cray'>Cray</option>
                        <option value='IBM'>IBM</option>
                        <option value='Intel'>Intel</option>
                        <option value='System'>System</option>
                      </select>
                    </label>
                    <label>
                      SHMEM Compilers:
                      <select defaultValue={currentRow.shmemCompilers} name='shmemCompiler'>
                        <option value='Cray'>Cray</option>
                        <option value='OpenSHMEM'>OpenSHMEM</option>
                        <option value='SOS'>SOS</option>
                      </select>
                    </label>
                  </form>
            </React.Fragment>
        )
    }

    if (form == 'Application') {

	let openmp = (currentRow.OpenMP == 'Yes') ? true : false;
	let pthreads = (currentRow.pThreads == 'Yes') ? true : false;	
	let tbb = (currentRow.tbb == 'Yes') ? true : false;
	let mpi = (currentRow.mpi == 'Yes') ? true : false;	
	let cuda = (currentRow.cuda == 'Yes') ? true : false;
	let opencl = (currentRow.openCL == 'Yes') ? true : false;	
	let shmem = (currentRow.shmem == 'Yes') ? true : false;
	let mpc = (currentRow.mpc == 'Yes') ? true : false;	

        return (
            <React.Fragment>
                <form className='tau-dialog-form'>
                    <label>
                        Name:
                        <br/>
                        <input className='tau-dialog-name' type='text' name='name' defaultValue={currentRow.name}/>
                    </label>
                    <br/><br/>
                    <label>
                      Linkage:
                      <select defaultValue={currentRow.linkage} name='linkage'>
                        <option value='static'>Static</option>
                        <option value='dynamic'>Dynamic</option>
                      </select>
                    </label>

                    <div className='tau-dialog-checkbox-container'>
                        <div className='tau-dialog-checkbox'>
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

    if (form == 'Measurement') {

	let sample = (currentRow.sample == 'Yes') ? true : false;
	let cuda = (currentRow.cuda == 'Yes') ? true : false;
	let io = (currentRow.io == 'Yes') ? true : false;
	let mpi = (currentRow.mpi == 'Yes') ? true : false;
	let shmem = (currentRow.shmem == 'Yes') ? true : false;

        return (
            <React.Fragment>
                <form className='tau-dialog-form'>
                    <label>
                        Name:
                        <br/>
                        <input className='tau-dialog-name' type='text' name='name' defaultValue={currentRow.name}/>
                    </label>
                    <br/><br/>
                    <label>
                      Profile:
                      <select defaultValue={currentRow.profile} name='profile'>
                        <option value='tau'>Tau</option>
                        <option value='merged'>Merged</option>
                        <option value='cubex'>Cubex</option>
                        <option value='sqlite'>SQLite</option>
                        <option value='none'>None</option>
                      </select>
                    </label>
                    <label>
                      Trace:
                      <select defaultValue={currentRow.trace} name='trace'>
                        <option value='slog2'>Slog2</option>
                        <option value='otf2'>OTF2</option>
                        <option value='none'>None</option>
                      </select>
                    </label>
                    <label>
                      Source Instrumentation:
                      <select defaultValue={currentRow.srcInst} name='sourceInstr'>
                        <option value='automatic'>Automatic</option>
                        <option value='manual'>Manual</option>
                        <option value='never'>Never</option>
                      </select>
                    </label>
                    <label>
                      Compiler Instrumentation:
                      <select defaultValue={currentRow.compInst} name='compilerInstr'>
                        <option value='always'>Always</option>
                        <option value='fallback'>Fallback</option>
                        <option value='never'>Never</option>
                      </select>
                    </label>
                    <label>
                      OpenMP:
                      <select defaultValue={currentRow.openMP} name='openmp'>
                        <option value='ignore'>Ignore</option>
                        <option value='opari'>OPARI</option>
                        <option value='ompt'>OMPT</option>
                      </select>
                    </label>
                    <div className='tau-dialog-checkbox-container'>
                        <div className='tau-dialog-checkbox'>
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

    if (form == 'Experiment') {

        return (
            <React.Fragment>
                <form className='tau-dialog-form'>
                    <label>
                        Name:
                        <br/>
                        <input className='tau-dialog-name' type='text' name='name' defaultValue={currentRow.name}/>
                    </label>
		    <br/><br/>
                    <label>
                        Target:
                        <select name='target' defaultValue={currentRow.target}>
                        {
                            Object.keys(json[currentProject]['targets']).map((target: string) =>
                                <option key={target} value={target}>{target}</option>)
                        }
                        </select>
                    </label>
                    <label>
                        Application:
                        <select name='application' defaultValue={currentRow.application}>
                        {
                            Object.keys(json[currentProject]['applications']).map((application: string) =>
                                <option key={application} value={application}>{application}</option>)
                        }
                        </select>
                    </label>
                    <label>
                        Measurement:
                        <select name='measurement' defaultValue={currentRow.measurement}>
                        {
                            Object.keys(json[currentProject]['measurements']).map((measurement: string) =>
                                <option key={measurement} value={measurement}>{measurement}</option>)
                        }
                        </select>
                    </label>
                </form>
            </React.Fragment>
        )
    }
};

class EditDialogBody extends Widget {
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

export const makeEditDialog = (model: KernelModel, form: string, currentRow: any, currentProject?: string) => {

    let body = document.createElement('div');
    ReactDOM.render(writeEditBody(model, form, currentRow, currentProject), body);

    const dialog = new Dialog({
      title: `Edit ${form}`,
      body: new EditDialogBody(body),
      buttons: [
        Dialog.cancelButton({ label: 'Cancel' }),
        Dialog.okButton({ label: 'Submit' })
      ]
    });

    dialog.addClass('tau-dialog-body');

    return dialog.launch().then(result => {
        dialog.dispose();

        if (result.value) {
            let args;
            switch (form.toLowerCase()) {
                case 'project':
                    args = `'${currentRow.name}', '${result.value.name}'`;
                    break;

                case 'target':
                    args = `'${currentRow.name}', '${result.value.name}', '${result.value.hostos}', '${result.value.hostArch}', '${result.value.hostCompiler}', '${result.value.mpiCompiler}', '${result.value.shmemCompiler}'`;
                    break;

                case 'application':
                    args = `'${currentRow.name}', '${result.value.name}', '${result.value.linkage}', '${result.value.openmp}', '${result.value.cuda}', '${result.value.pthreads}', '${result.value.opencl}', '${result.value.tbb}', '${result.value.shmem}', '${result.value.mpi}', '${result.value.mpc}'`;
                    break;

                case 'measurement':
                    args = `'${currentRow.name}', '${result.value.name}', '${result.value.profile}', '${result.value.trace}', '${result.value.sourceInstr}', '${result.value.compilerInstr}', '${result.value.openmp}', '${result.value.sample}', '${result.value.mpi}', '${result.value.cuda}', '${result.value.shmem}', '${result.value.io}'`;
                    break;

                case 'experiment':
                    args = `'${currentRow.name}', '${result.value.name}', '${result.value.target}', '${result.value.application}', '${result.value.measurement}'`;
                    break;

                default:
                    return;
            }

            model.execute(`TauKernel.edit_${form.toLowerCase()}(${args})`);
            model.execute('TauKernel.refresh()');
        }
    });
};
