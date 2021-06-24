import { KernelModel } from '../KernelModel';
import { Dialog } from '@jupyterlab/apputils';

export function makeDialog(model: KernelModel, form: string) {

    const dialog = new Dialog({
      title: `New ${form}`,
      body: 'INSERT SELECT FIELDS HERE',
      buttons: [
        Dialog.cancelButton({ label: 'Cancel' }),
        Dialog.okButton({ label: 'Submit' })
      ]
    });

    return dialog.launch().then(result => {

        dialog.dispose();

        if (result.value) {
            console.log(result);
        }

        return null;

    });


};
