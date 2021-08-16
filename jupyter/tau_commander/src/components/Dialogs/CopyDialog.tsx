import React from 'react';
import ReactDOM from 'react-dom';

import { KernelModel } from '../../KernelModel';
import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeCopyBody = (form:string, currentForm:string) => {
    let copyName = currentForm + '_copy';

    if (form != 'Project') {
        return (
	    <div>
	        <label> 
		    Name of new {form}:
                    <br/>
                    <input className='tau-dialog-name' type='text' name='name' defaultValue={copyName}/>
	        </label>
	    </div>
        )
    } else {
	return (
	    <div>
	        <label> 
		    Name of new {form}:
                    <br/>
                    <input className='tau-dialog-name' type='text' name='name' defaultValue={copyName}/>
	        </label>
		<br/><br/>
		<label>
		    Suffix:
		    <br/>
                    <input className='tau-dialog-name' type='text' name='name' defaultValue='_copy'/>
		</label>
	    </div>
        )
    }
};

class CopyDialogBody extends Widget {
    constructor(domElement: HTMLElement) {
        super({node : domElement});
    }

    getValue() {
        let response = this.node.querySelectorAll('input');
        return response
    }
};

export const makeCopyDialog = (model: KernelModel, form: string, currentForm: string) => {

    let body = document.createElement('div');
    ReactDOM.render(writeCopyBody(form, currentForm), body);

    const dialog = new Dialog({
      title: `Copy ${currentForm}`,
      body: new CopyDialogBody(body),
      buttons: [
        Dialog.cancelButton({ label: 'Cancel' }),
        Dialog.okButton({ label: 'Submit' })
      ]
    });

    dialog.addClass('tau-dialog-body');

    return dialog.launch().then(result => {
        dialog.dispose();

        if (result.value) {
	    if (form != 'Project') {
		console.log(result.value);
	        model.execute(`TauKernel.copy_${form.toLowerCase()}('${currentForm}', '${result.value[0].value}')`);
	    } else {
		console.log(result.value);
	        model.execute(`TauKernel.copy_${form.toLowerCase()}('${currentForm}', '${result.value[0].value}', '${result.value[1].value}')`);
	    }
            model.execute('TauKernel.refresh()');
        }
    });
};
