import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

const writeCopyBody = (name: string) => {
  let copyName = name + '_copy';
  return (
    <div>
      <label>
        Name of new project:
        <br/>
        <input className='tau-Dialog-name' type='text' name='name' defaultValue={copyName}/>
      </label>
      <br/><br/>
      <label>
        T.A.M. Suffix:
        <br/>
        <input className='tau-Dialog-name' type='text' name='name' defaultValue='_copy'/>
      </label>
    </div>
  )
};

class DialogBody extends Widget {
  constructor(domElement: HTMLElement) {
    super({node : domElement});
  }

  getValue() {
    let response = this.node.querySelectorAll('input');
    return Array.from(response); 
  }
};

export const copyProjectDialog = (name: string) => {

  let body = document.createElement('div');
  ReactDOM.render(writeCopyBody(name), body);

  const dialog = new Dialog({
    title: `Copy ${name}`,
    body: new DialogBody(body),
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.okButton({ label: 'Submit' })
    ]
  });

  dialog.addClass('tau-Dialog-body');

  return dialog;
};
