/* Copyright (c) 2017, ParaTools, Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * (1) Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 * (2) Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimer in the documentation
 *     and/or other materials provided with the distribution.
 * (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
 *     be used to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

import {Widget} from '@phosphor/widgets';

import {Message} from '@phosphor/messaging';

import {IRenderMime} from '@jupyterlab/rendermime-interfaces';

import {ReadonlyJSONObject} from '@phosphor/coreutils';

import {BarChart3D} from "./bar_chart_3d";

import '../style/index.css';

export const MIME_TYPE = 'application/tau';

/**
 * A widget for rendering data, for usage with rendermime.
 */
export class RenderedTAUData extends Widget implements IRenderMime.IRenderer {


    private _mimeType: string;
    private renderDiv: HTMLDivElement;

    constructor(options: IRenderMime.IRendererOptions) {
        super();
        console.log("TAU Renderer created");
        this.addClass('jp-RenderedTAUData');
        this._mimeType = options.mimeType;
        this.renderDiv = document.createElement('div');
        this.node.appendChild(this.renderDiv);
    }

    /**
     * Render into this widget's node.
     */
    renderModel(model: IRenderMime.IMimeModel): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            let data = JSON.parse(model.data[this._mimeType] as string) as ReadonlyJSONObject;
            let barchart = new BarChart3D(data);
            barchart.renderTo(this.renderDiv);
            this.update();
            resolve();
        });
    }

    /**
     * A message handler invoked on an `'after-show'` message.
     */
    protected onAfterShow(msg: Message): void {
        this.update();
    }

    /**
     * A message handler invoked on a `'resize'` message.
     */
    protected onResize(msg: Widget.ResizeMessage): void {
        this.update();
    }

    /**
     * A message handler invoked on an `'update-request'` message.
     */
    protected onUpdateRequest(msg: Message): void {

    }

}

/**
 * A mime renderer factory for TAU data.
 */
export const rendererFactory: IRenderMime.IRendererFactory = {
    safe: true,
    mimeTypes: [MIME_TYPE],
    createRenderer: options => new RenderedTAUData(options)
};


const extensions: IRenderMime.IExtension | IRenderMime.IExtension[] = [
    {
        id: 'taucmdr_renderer:factory',
        rendererFactory,
        rank: 0,
        dataType: 'json',
        fileTypes: [{
            name: 'tau',
            mimeTypes: [MIME_TYPE],
            extensions: ['.tau'],
        }],
        documentWidgetFactoryOptions: {
            name: 'tau',
            primaryFileType: 'tau',
            fileTypes: ['tau'],
            defaultFor: ['tau']
        }
    }
];


export default extensions;
