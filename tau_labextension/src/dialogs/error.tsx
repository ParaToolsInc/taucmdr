import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

class DialogBody extends Widget {
    constructor(domElement: HTMLElement) {
        super({node : domElement});
    }
};

const writeErrorBody = (message:string) => {
  const newMessage = message.split('\\n');
  const elements = newMessage.map((val) => {
    return (val === "")
      ? (<React.Fragment><br/></React.Fragment>)
      : (<React.Fragment><code>{val}</code><br/></React.Fragment>)
  });
  return (
    <pre className='tau-Dialog-error'>
      { elements }
    </pre>
  )
};

export const errorDialog = (message: string) => {
  const body = document.createElement('div');
  ReactDOM.render(writeErrorBody(message), body);

  const dialog = new Dialog({
    title: 'Kernel Error',
    body: new DialogBody(body),
    buttons: [
      Dialog.okButton({ label: 'Okay' }),
    ]
  });

  return dialog;
};
