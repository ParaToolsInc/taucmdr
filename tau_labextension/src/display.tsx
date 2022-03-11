import {
  Widget,
  PanelLayout
} from '@lumino/widgets';

import {
  IFrame
} from '@jupyterlab/apputils';

import {
  IPlotlyDisplayItem
} from './tables';

// import * as ReactDOM from 'react-dom';

export class PlotlyDisplay extends Widget {
  constructor(options: PlotlyDisplay.IOptions) {
    super();
    this.addClass('tau-TauDisplay');

    const layout = (this.layout = new PanelLayout());
    const project = options.trialPath['project'];
    const experiment = options.trialPath['experiment'];
    const trial = options.trialPath['trial'];

    const iframe = new IFrame();
    iframe.sandbox = ['allow-scripts', 'allow-same-origin'];
    iframe.url = `http://127.0.0.1:8889/${project}/${experiment}/${trial}`;
    layout.addWidget(iframe);
  }

  /**
   * Handle an update request.
   */
  protected onUpdateRequest(): void {
    if (!this.isVisible) {
      return;
    }
  }

  /**
   * Rerender after showing.
   */
  protected onAfterShow(): void {
    this.update();
  }
}

export namespace PlotlyDisplay {
  export interface IOptions {
    trialPath: IPlotlyDisplayItem;
  }
}
