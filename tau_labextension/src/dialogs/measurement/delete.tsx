import {
  Dialog
} from '@jupyterlab/apputils';

export const deleteMeasurementDialog = (measurementName: string, props: Tables.Measurement) => {
  const dialog = new Dialog({
    title: `Delete ${measurementName}`,
    body: `Are you sure you want to delete measurement: ${measurementName}?`,
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.warnButton({ label: 'Delete' }),
    ]
  });
  dialog.launch()
    .then(response => {
      if (response.button.label == 'Delete') {
        props.kernelExecute(`delete_measurement('${measurementName}')`)
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
  export interface Measurement {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    measurements: {[key: string]: any};
  }
}


