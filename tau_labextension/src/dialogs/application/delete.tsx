import {
  Dialog
} from '@jupyterlab/apputils';

export const deleteApplicationDialog = (applicationName: string, props: Tables.Application) => {
  const dialog = new Dialog({
    title: `Delete ${applicationName}`,
    body: `Are you sure you want to delete application: ${applicationName}?`,
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.warnButton({ label: 'Delete' }),
    ]
  });

  dialog.launch()
    .then(response => {
      if (response.button.label == 'Delete') {
        props.kernelExecute(`delete_application('${applicationName}')`)
          .then((result) => {
            if (result) {
              props.updateProject(props.projectName);
            }
          });
      }
      dialog.dispose();
    });
}

namespace Tables {
  export interface Application {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    applications: {[key: string]: any};
  }
}
