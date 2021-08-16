import { Dialog } from '@jupyterlab/apputils';

export const makeErrorDialog = (message: string) => {
    const dialog = new Dialog({
	title: 'Error',
	body: message,
	buttons: [
	    Dialog.cancelButton({ label: 'Okay' }),
	]
    });

    return dialog.launch().then(result => {
	dialog.dispose();
    });
};

