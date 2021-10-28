import {
  Dialog
} from '@jupyterlab/apputils';

export const selectExperimentDialog = (experimentName: string, props: Tables.Experiment) => {
  const dialog = new Dialog({
    title: `Select ${experimentName}`,
    body: `Are you sure you want to select experiment: ${experimentName}?`,
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.okButton({ label: 'Select' })
    ]
  });

  dialog.launch()
    .then(response => {
      if (response.button.label == 'Select') {
        props.kernelExecute(`select_experiment('${props.projectName}', '${experimentName}')`)
          .then((result) => {
            if (result) {
              props.setSelectedExperiment(experimentName);
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
    setSelectedExperiment: (experimentName: string | null) => void;
    experiments: {[key: string]: any};
  }
}
