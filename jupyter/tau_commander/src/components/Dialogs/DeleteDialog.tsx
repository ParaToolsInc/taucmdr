import { Dialog } from '@jupyterlab/apputils';
import { KernelModel } from '../../KernelModel';

export const makeDeleteDialog = (model: KernelModel, form:string, currentForm: string) => {
    const dialog = new Dialog({
	title: `Delete ${form}`,
	body: `Are you sure you want to delete ${form}: ${currentForm}?`,
	buttons: [
	    Dialog.cancelButton({ label: 'Cancel' }),
	    Dialog.warnButton({ label: 'Delete' }),
	]
    });

    return dialog.launch().then(result => {
	if (result.button.label == 'Delete') {
	    model.execute(`TauKernel.delete_${form.toLowerCase()}('${currentForm}')`);
   	    model.execute('TauKernel.refresh()');
	}
	dialog.dispose();
    });
};

