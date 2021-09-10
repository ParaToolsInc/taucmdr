import { Dialog } from '@jupyterlab/apputils';
import { KernelModel } from '../../KernelModel';

import { makeLoadingDialog } from './LoadingDialog';

export const makeSelectDialog = (model: KernelModel, form:string, currentForm: string) => {
    const dialog = new Dialog({
	title: `Select ${form}`,
	body: `Are you sure you want to select ${form}: ${currentForm}?`,
	buttons: [
	    Dialog.cancelButton({ label: 'Cancel' }),
	    Dialog.okButton({ label: 'Select' }),
	]
    });

    return dialog.launch().then(result => {
	if (result.button.label == 'Select') {
	    model.execute(`TauKernel.select_${form.toLowerCase()}('${currentForm}')`);
   	    model.execute('TauKernel.refresh()');
	    makeLoadingDialog(); 
	}
	dialog.dispose();
    });
};

