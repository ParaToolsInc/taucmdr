import {
  Dialog
} from '@jupyterlab/apputils';

export const deleteProjectDialog = (project: string) => {
  const dialog = new Dialog({
    title: `Delete ${project}`,
    body: `Are you sure you want to delete project: ${project}?`,
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.warnButton({ label: 'Delete' }),
    ]
  });
  return dialog;
}
