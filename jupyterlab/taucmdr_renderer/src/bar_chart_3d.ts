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
    WebGLRenderer,
} from 'three';

const DEFAULT_HEIGHT: number = 400;
const DEFAULT_WIDTH: number = 400;
const DEFAULT_FOV: number = 45;
const DEFAULT_NEAR_CLIP: number = 0.1;
const DEFAULT_FAR_CLIP: number = 1000;
const DEFAULT_BG_COLOR: number = 0x000000;
const DEFAULT_BG_ALPHA: number = 1.0;
const DEFAULT_ANTIALIAS: boolean = true;

/* Input settings for the 3D bar chart */
export interface BarChart3DData {
    height?: number;
    width?: number;
    fieldOfView?: number;
    nearClip?: number;
    farClip?: number;
    bgColor?: number;
    bgAlpha?: number;
    antialias?: boolean;
    xLabels?: Array<string>;
    yLabels?: Array<string>;
    zMin?: number;
    zMax?: number;
    values?: Array<number>;
}

/* Renderer for the 3D bar chart */
export class BarChart3D {

    protected data: BarChart3DData;

    protected scene : Scene;
    protected camera : PerspectiveCamera;
    protected renderer : WebGLRenderer;

    /* This needs to be a lambda because we need to call it from outside the
    class context but need to access `this`. We create this once at instance creation
    to avoid allocating a new lambda each time through the event loop. */
    protected renderLoop = () => {
        //this.controls.update();
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

    public get values(): Array<number> {
        return this.data.values || [];
    }

    /* Rendering Functions */

    public renderTo(div: HTMLDivElement): void {
        console.log("Rendering");
        console.log(this.data);

        this.scene = new Scene();
        this.camera = new PerspectiveCamera(this.fieldOfView, this.width / this.height, this.nearClip, this.farClip);
        this.renderer = new WebGLRenderer({antialias: this.antialias});

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


        let cubeGeometry = new BoxGeometry(4, 4, 4);
        let cubeMaterial = new MeshLambertMaterial({color: 0xff0000, wireframe: false});
        let cube = new Mesh(cubeGeometry, cubeMaterial);
        cube.position.set(-4, 3, 0);

        this.scene.add(cube);
        this.camera.position.set(-30, 40, 30);
        this.camera.lookAt(this.scene.position);
        div.appendChild(this.renderer.domElement);

        /*this.controls = new TrackballControlsModule(this.camera);
        this.controls.rotateSpeed = 1.0;
        this.controls.zoomSpeed = 1.2;
        this.controls.panSpeed = 0.8;
        this.controls.noZoom = false;
        this.controls.noPan = false;
        this.controls.staticMoving = true;
        this.controls.dynamicDampingFactor = 0.3;
        */

        // start rendering the scene
        this.renderLoop();
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