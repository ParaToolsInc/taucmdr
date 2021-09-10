import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

import FadeLoader from 'react-spinners/FadeLoader';

export class LoadingDialog extends Dialog<any> {
    static currentDialog: any;
    static terminate() {
	LoadingDialog.currentDialog.resolve();
	LoadingDialog.currentDialog = null;
    }

    constructor(options: Partial<Dialog.IOptions<any>> = {}) {
	super(options);
	LoadingDialog.currentDialog = this;
	this.id = 'loading-dialog';
    }

    _evtClick(event: any) {
        const content = this.node.getElementsByClassName('jp-Dialog-content')[0];
        if (!content.contains(event.target)) {
            event.stopPropagation();
            event.preventDefault();
            return;
        }
    }
};

class LoadingDialogBody extends Widget {
    constructor(domElement: HTMLElement) {
	super({node : domElement});
    }
};

export const makeLoadingDialog = () => {

    let body = document.createElement('div');
    body.classList.add('tau-center-dialog');
    ReactDOM.render(<FadeLoader color={'#BCDAEC'} loading={true} height={15} width={5} radius={15} />, body);

    const options: any = {
	title: 'Loading',
        body: new LoadingDialogBody(body),
        buttons: [
	    Dialog.okButton({ label: 'Please wait' })
        ]
    };

    const dialog = new LoadingDialog(options);

    dialog.addClass('tau-dialog-body');

    return dialog.launch().then(result => {
	dialog.dispose();
    });
};
