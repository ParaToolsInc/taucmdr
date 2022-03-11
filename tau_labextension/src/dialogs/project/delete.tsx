import {
  Dialog,
  WidgetTracker
} from '@jupyterlab/apputils';

export const deleteProjectDialog = (props: Sidebar.Project) => {
  const dialog = new Dialog({
    title: `Delete ${props.projectName}`,
    body: `Are you sure you want to delete project: ${props.projectName}?`,
    buttons: [
      Dialog.cancelButton({ label: 'Cancel' }),
      Dialog.warnButton({ label: 'Delete' }),
    ]
  });

  dialog.addClass('tau-Dialog-body');
  dialog.launch()
    .then(response => {
      if (response.button.label === 'Delete') {
        props.kernelExecute(`delete_project('${props.projectName}')`)
          .then((result) => {
            if (result) {
              props.updateProjects();
              const exists = props.tracker.find((widget) => {
                return widget.id === `project-${props.projectName}`;
              });

              if (exists) {
                exists.dispose();
                return;
              }
            }
          });
      }
      dialog.dispose();
    });
}

namespace Sidebar {
  export interface Project {
    projectName: string;
    kernelExecute: (code: string) => Promise<any>;
    updateProjects: () => void;
    tracker: WidgetTracker;
  }
}
