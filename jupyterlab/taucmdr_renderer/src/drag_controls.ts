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

export interface Draggable {
    drag(x : number, y: number) : void;
}

export interface Zoomable {
    zoom(level : number) : void;
}

export class DragControls {

    protected startDragX : number | null;
    protected startDragY : number | null;
    protected deltaX : number;
    protected deltaY : number;

    protected zoomListeners : Array<Zoomable>;
    protected dragListeners : Array<Draggable>;

    constructor(element : HTMLElement) {
        this.startDragX = null;
        this.startDragY = null;
        this.deltaX = 0;
        this.deltaY = 0;
        this.zoomListeners = [];
        this.dragListeners = [];
        element.addEventListener('wheel', (e : WheelEvent) => {this.mouseWheelHandler(e)});
        element.addEventListener('mousedown', (e: MouseEvent) => {this.mouseDownHandler(e)});
        element.addEventListener('mousemove', (e: MouseEvent) => {this.mouseMoveHandler(e)});
        element.addEventListener('mouseup', (e: MouseEvent) => {this.mouseUpHandler(e)});
    }

    public addZoomListener(zoomable : Zoomable) {
        this.zoomListeners.push(zoomable);
    }

    public addDragListener(draggable : Draggable) {
        this.dragListeners.push(draggable);
    }

    protected mouseWheelHandler(e : WheelEvent) : boolean {
        this.zoomListeners.forEach(listener => {
            listener.zoom(e.deltaY);
        });
        e.preventDefault();
        return false;
    }

    protected mouseDownHandler(e: MouseEvent) : boolean {
        this.startDragX = e.clientX;
        this.startDragY = e.clientY;
        e.preventDefault();
        return false;
    }

    protected mouseMoveHandler(e: MouseEvent) : boolean {
        if(this.startDragX === null || this.startDragY === null) {
            return true;
        }
        this.dragListeners.forEach(listener => {
            if(this.startDragX === null || this.startDragY == null) {
                return;
            }
            listener.drag(e.clientX - this.startDragX, e.clientY - this.startDragY);
        });
        this.startDragX = e.clientX;
        this.startDragY = e.clientY;
        e.preventDefault();
        return false;
    }

    protected mouseUpHandler(e: MouseEvent) : boolean {
        this.startDragX = null;
        this.startDragY = null;
        e.preventDefault();
        return false;
    }

}