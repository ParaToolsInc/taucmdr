///<reference path="../node_modules/@types/three/three-core.d.ts"/>
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

import {ReadonlyJSONObject} from '@phosphor/coreutils';

import {
    AmbientLight,
    AxisHelper,
    BoxGeometry,
    Mesh,
    MeshLambertMaterial,
    PerspectiveCamera,
    PointLight,
    Scene,
    Vector3,
    WebGLRenderer,
} from 'three'

import {
    MeshText2D,
    textAlign
} from "three-text2d";

import {
    zip
} from 'lodash-es';

import {
    DragControls,
    Draggable,
    Zoomable
} from "./drag_controls";

const DEFAULT_HEIGHT: number = 400;
const DEFAULT_WIDTH: number = 400;
const DEFAULT_FOV: number = 45;
const DEFAULT_NEAR_CLIP: number = 0.1;
const DEFAULT_FAR_CLIP: number = 1000;
const DEFAULT_BG_COLOR: number = 0x000000;
const DEFAULT_BG_ALPHA: number = 1.0;
const DEFAULT_ANTIALIAS: boolean = true;
const DEFAULT_DRAG_SPEED : number = 450;
const DEFAULT_ZOOM_SPEED : number = 0.05;
const DEFAULT_BAR_SIZE : number = 5;
const DEFAULT_BAR_SPACING : number = 10;

/* Input settings for the 3D bar chart */
export interface BarChart3DData {
    height? : number;
    width? : number;
    fieldOfView? : number;
    nearClip? : number;
    farClip? : number;
    bgColor? : number;
    bgAlpha? : number;
    antialias? : boolean;
    dragSpeed? : number;
    zoomSpeed? : number;
    barSize? : number;
    barSpacing? : number;
    xLabels? : Array<string>;
    yLabels? : Array<string>;
    zMin? : number;
    zMax? : number;
    heights? : Array<number>;
    colors? : Array<number>;
}

/* Renderer for the 3D bar chart */
export class BarChart3D implements Draggable, Zoomable {

    protected data: BarChart3DData;

    protected scene : Scene;
    protected camera : PerspectiveCamera;
    protected renderer : WebGLRenderer;

    protected center : Vector3;
    protected dragControls : DragControls;

    /* This needs to be a lambda because we need to call it from outside the
    class context but need to access `this`. We create this once at instance creation
    to avoid allocating a new lambda each time through the event loop. */
    protected renderLoop = () => {
        this.renderer.render(this.scene, this.camera);
        requestAnimationFrame(this.renderLoop);
    };

    constructor(data?: ReadonlyJSONObject) {
        this.data = data || {};
    }

    /* Accessors */

    public get height(): number {
        return this.data.height || DEFAULT_HEIGHT;
    }

    public set height(newHeight: number) {
        this.data.height = newHeight;
        this.updateCamera();
    }

    public get width(): number {
        return this.data.width || DEFAULT_WIDTH;
    }

    public set width(newWidth: number) {
        this.data.width = newWidth;
        this.updateCamera();
    }

    public get fieldOfView(): number {
        return this.data.fieldOfView || DEFAULT_FOV;
    }

    public set fieldOfView(newFieldOfView: number) {
        this.data.fieldOfView = newFieldOfView;
        if (this.camera) {
            this.camera.fov = this.fieldOfView;
            this.updateCamera();
        }
    }

    public get nearClip(): number {
        return this.data.nearClip || DEFAULT_NEAR_CLIP;
    }

    public set nearClip(newFarClip: number) {
        this.data.nearClip = newFarClip;
        if (this.camera) {
            this.camera.near = this.farClip;
            this.updateCamera();
        }
    }

    public get farClip(): number {
        return this.data.nearClip || DEFAULT_FAR_CLIP;
    }

    public set farClip(newFarClip: number) {
        this.data.farClip = newFarClip;
        if (this.camera) {
            this.camera.far = this.farClip;
            this.updateCamera();
        }
    }

    public get bgColor(): number {
        return this.data.bgColor || DEFAULT_BG_COLOR;
    }

    public set bgColor(newColor: number) {
        this.data.bgColor = newColor;
        if (this.renderer) {
            this.renderer.setClearColor(this.bgColor, this.bgAlpha);
        }
    }

    public get bgAlpha(): number {
        return this.data.bgAlpha || DEFAULT_BG_ALPHA;
    }

    public set bgAlpha(newAlpha: number) {
        this.data.bgAlpha = newAlpha;
        if (this.renderer) {
            this.renderer.setClearColor(this.bgColor, this.bgAlpha);
        }
    }

    public get antialias(): boolean {
        return this.data.antialias || DEFAULT_ANTIALIAS;
    }

    public get zoomSpeed(): number {
        return this.data.zoomSpeed || DEFAULT_ZOOM_SPEED;
    }

    public set zoomSpeed(newZoomSpeed: number) {
        this.data.zoomSpeed = newZoomSpeed;
    }

    public get dragSpeed(): number {
        return this.data.dragSpeed || DEFAULT_DRAG_SPEED;
    }

    public set dragSpeed(newDragSpeed: number) {
        this.data.dragSpeed = newDragSpeed;
    }

    public get barSize(): number {
        return this.data.barSize || DEFAULT_BAR_SIZE;
    }

    public set barSize(newBarSize: number) {
        this.data.barSize = newBarSize;
    }

    public get barSpacing(): number {
        return this.data.barSpacing || DEFAULT_BAR_SPACING;
    }

    public set barSpacing(newBarSpacing: number) {
        this.data.barSpacing = newBarSpacing;
    }

    public get xLabels(): Array<string> {
        return this.data.xLabels || [];
    }

    public get yLabels(): Array<string> {
        return this.data.yLabels || [];
    }

    public get zMin(): number {
        return this.data.zMin || 0;
    }

    public get zMax(): number {
        return this.data.zMax || 0;
    }

    public get heights(): Array<number> {
        return this.data.heights || [];
    }

    public get colors(): Array<number> {
        return this.data.colors || Array(this.heights.length).fill(0xFF0000);
    }

    /* Rendering Functions */

    public renderTo(div: HTMLDivElement): void {
        console.log("Rendering");
        console.log(this.data);

        this.scene = new Scene();
        this.camera = new PerspectiveCamera(this.fieldOfView, this.width / this.height, this.nearClip, this.farClip);
        this.renderer = new WebGLRenderer({antialias: this.antialias});
        this.center = new Vector3(0, 0, 0);

        this.renderer.setClearColor(this.bgColor, this.bgAlpha);
        this.renderer.setSize(this.width, this.height);

        let axes = new AxisHelper(20);
        this.scene.add(axes);

        // The ambient lights illuminates everything equally
        let ambientLight = new AmbientLight(0x404040); // soft white light
        this.scene.add(ambientLight);

        // The point light illuminates from above the chart
        let pointLight = new PointLight(0xFFFFFF, 1, 0);
        pointLight.position.set(50, 50, 50);
        this.scene.add(pointLight);

        this.renderData();

        this.camera.up = new Vector3(0, 0, 1);
        this.camera.position.set(30, 40, 30);
        this.camera.lookAt(this.center);

        div.appendChild(this.renderer.domElement);

        this.dragControls = new DragControls(div);
        this.dragControls.addDragListener(this);
        this.dragControls.addZoomListener(this);

        let text = new MeshText2D("FOO", {align: textAlign.left, font: '30px Arial', fillStyle: '#FFFFFF', antialias: true});
        text.rotation.x = Math.PI / 2;

        this.scene.add(text);

        // start rendering the scene
        this.renderLoop();
    }

    public renderData() : void {
        const y_size = this.yLabels.length;
        let x = 0;
        let y = 0;
        zip(this.heights, this.colors).forEach(bar => {
            const height = bar[0];
            const color = bar[1];
            const barGeometry = new BoxGeometry(this.barSize, this.barSize, height);
            const barMaterial = new MeshLambertMaterial({color: color});
            let mesh = new Mesh(barGeometry, barMaterial);
            mesh.position.set((x * this.barSpacing) + (this.barSize/2.0),
                (y * this.barSpacing) + (this.barSize/2.0), height/2.0);
            this.scene.add(mesh);
            y++;
            if(y >= y_size) {
                y = 0;
                x++;
            }
        });
    }

    /* Mouse Controls */

    public drag(deltaX : number, deltaY: number) : void {
        const radPerPixel = (Math.PI / this.dragSpeed);
	    const deltaPhi = radPerPixel * deltaX;
	    const deltaTheta = radPerPixel * deltaY;
	    let pos = this.camera.position.sub(this.center);
	    const radius = pos.length();
	    let theta = Math.acos(pos.z / radius);
	    let phi = Math.atan2(pos.y, pos.x);

        theta = Math.min(Math.max(theta - deltaTheta, 0), Math.PI);
        phi -= deltaPhi;

        pos.x = radius * Math.sin(theta) * Math.cos(phi);
        pos.y = radius * Math.sin(theta) * Math.sin(phi);
        pos.z = radius * Math.cos(theta);

        this.camera.position.add(this.center);
        this.camera.lookAt(this.center);
    }

    public zoom(amount : number) : void {
        let scale : number;
        if(amount < 0) {
            scale = 1.0 - this.zoomSpeed;
        } else {
            scale = 1.0 + this.zoomSpeed;
        }
        let radius = this.camera.position.length();
        if(radius <= this.nearClip || radius >= this.farClip) {
            return;
        }
        this.camera.position.sub(this.center).multiplyScalar(scale).add(this.center);
    }

    protected updateCamera(): void {
        if (this.camera) {
            this.camera.aspect = this.width / this.height;
            this.camera.updateProjectionMatrix();
        }
        if (this.renderer) {
            this.renderer.setSize(this.width, this.height);
        }
    }

}