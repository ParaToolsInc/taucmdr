import {
  Dialog
} from '@jupyterlab/apputils';

export const deleteExperimentDialog = (experimentName: string, props: Tables.Experiment) => {
  const dialog = new Dialog({
    title: `Delete ${experimentName}`,
    body: `Are you sure you want to delete experiment: ${experimentName}?`,
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.warnButton({ label: 'Delete' }),
    ]
  });

  dialog.launch()
    .then(response => {
      if (response.button.label == 'Delete') {
        props.kernelExecute(`delete_experiment('${props.projectName}', '${experimentName}')`)
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
  export interface Experiment {
    project: any;
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    experiments: {[key: string]: any};
  }
}
