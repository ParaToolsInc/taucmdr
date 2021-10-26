import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

class DialogBody extends Widget {
    constructor(domElement: HTMLElement) {
        super({node : domElement});
    }

    getValue() {
        let response = this.node.querySelector('input');
        if (response) {
          return response.value;
        }
        return ''
    }
};

const writeEditBody = (project: string) => {
    return (
        <React.Fragment>
            <form className='tau-Dialog-form'>
                <label>
                    Edit name:
                    <br/>
                    <input className='tau-Dialog-name' type='text' name='name' defaultValue={project}/>
                </label>
            </form>
        </React.Fragment>
    )
}

export const editProjectDialog = (project: string) => {

    let body = document.createElement('div');
    ReactDOM.render(writeEditBody(project), body);

    const dialog = new Dialog({
      title: `Edit Project`,
      body: new DialogBody(body),
      buttons: [
        Dialog.cancelButton({ label: 'Cancel' }),
        Dialog.okButton({ label: 'Submit' })
      ]
    });

    dialog.addClass('tau-Dialog-body');

    return dialog
}
