import {
  Dialog
} from '@jupyterlab/apputils';

export const deleteTrialDialog = (trialName: string, props: Tables.Trial) => {
  const dialog = new Dialog({
    title: `Delete ${trialName}`,
    body: `Are you sure you want to delete trial: ${trialName}?`,
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.warnButton({ label: 'Delete' }),
    ]
  });

  dialog.launch()
    .then(response => {
      if (response.button.label === 'Delete') {
        props.kernelExecute(`delete_trial('${props.projectName}', '${trialName}')`)
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
  export interface Trial {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    experiment: {[key: string]: {[key: string]: any}}
    setSelectedExperiment: (experimentName: string | null) => void;
    selectedExperiment: string;
  }
}
