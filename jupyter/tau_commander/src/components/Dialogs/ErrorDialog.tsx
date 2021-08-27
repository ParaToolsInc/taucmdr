import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeErrorBody = (message:string) => {

    let newMessage = message.split('\\n');
    console.log(newMessage);
    return (
	<div className='tau-error-dialog'>
	    {newMessage.map((val) => (<p>{val}</p>))}
	</div> 
    )
};

class ErrorDialogBody extends Widget {
    constructor(domElement: HTMLElement) {
        super({node : domElement});
    }
};

export const makeErrorDialog = (message: string) => {

    let body = document.createElement('div');
    ReactDOM.render(writeErrorBody(message), body);

    const dialog = new Dialog({
	title: 'Error',
	body: new ErrorDialogBody(body),
	buttons: [
	    Dialog.okButton({ label: 'Okay' }),
	]
    });

    return dialog.launch().then(result => {
	dialog.dispose();
    });
};

