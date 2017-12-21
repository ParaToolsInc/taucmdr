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
    Box3,
    BoxGeometry, Font,
    FontLoader,
    Geometry,
    Line,
    LineBasicMaterial,
    Mesh,
    MeshLambertMaterial,
    PerspectiveCamera,
    PointLight,
    Raycaster,
    Scene, TextGeometry,
    Vector2,
    Vector3,
    WebGLRenderer,
} from 'three'

import {MeshText2D, SpriteText2D, textAlign} from "three-text2d";

import {zip} from 'lodash-es';

import {DragControls, Draggable, Selectable, Zoomable,} from "./drag_controls";

import {Text2D} from "three-text2d/lib/Text2D";


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
const DEFAULT_TEXT_SCALE : number = 0.05;
const DEFAULT_TEXT_OFFSET : number = -3;
const DEFAULT_FONT : string = "bold 90px Arial";
const DEFAULT_FONT_COLOR : string = "#FFFFFF";
const DEFAULT_FONT_ANTIALIAS : boolean = true;
const DEFAULT_TEXT_TYPE : string = "mesh";

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
    textScale? : number;
    textOffset? : number;
    font? : string;
    fontColor? : string;
    fontAntialias? : boolean;
    textType? : string;
}

/* Renderer for the 3D bar chart */
export class BarChart3D implements Draggable, Zoomable, Selectable {

    protected data: BarChart3DData;

    protected scene : Scene;
    protected camera : PerspectiveCamera;
    protected renderer : WebGLRenderer;

    protected center : Vector3;
    protected dragControls : DragControls;

    protected xSelectRects : Array<Mesh>;
    protected ySelectRects : Array<Mesh>;


    protected threeFont : Font;

    /* This needs to be a lambda because we need to call it from outside the
    class context but need to access `this`. We create this once at instance creation
    to avoid allocating a new lambda each time through the event loop. */
    protected renderLoop = () => {
        this.renderer.render(this.scene, this.camera);
        requestAnimationFrame(this.renderLoop);
    };

    constructor(data?: ReadonlyJSONObject) {
        this.data = data || {};
        this.xSelectRects = [];
        this.ySelectRects = [];
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

    public set nearClip(newNearClip: number) {
        this.data.nearClip = newNearClip;
        if (this.camera) {
            this.camera.near = this.nearClip;
            this.updateCamera();
        }
    }

    public get farClip(): number {
        return this.data.farClip || DEFAULT_FAR_CLIP;
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

    public get textScale(): number {
        return this.data.textScale || DEFAULT_TEXT_SCALE;
    }

    public set textScale(newTextScale: number) {
        this.data.textScale = newTextScale;
    }

    public get textOffset(): number {
        return this.data.textOffset || DEFAULT_TEXT_OFFSET;
    }

    public set textOffset(newTextOffset: number) {
        this.data.textOffset = newTextOffset;
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
        return this.data.zMax || 100;
    }

    public get heights(): Array<number> {
        return this.data.heights || [];
    }

    public get colors(): Array<number> {
        return this.data.colors || Array(this.heights.length).fill(0xFF0000);
    }

    public get font(): string {
        return this.data.font || DEFAULT_FONT;
    }

    public set font(newFont: string) {
        this.data.font = newFont;
    }

    public get fontColor(): string {
        return this.data.fontColor || DEFAULT_FONT_COLOR;
    }

    public set fontColor(newFontColor: string) {
        this.data.fontColor = newFontColor;
    }

    public get fontAntialias(): boolean {
        return this.data.fontAntialias || DEFAULT_FONT_ANTIALIAS;
    }

    public set fontAntialias(newFontAntialias: boolean) {
        this.data.fontAntialias = newFontAntialias;
    }

    public get textType(): string {
        return this.data.textType || DEFAULT_TEXT_TYPE;
    }

    public set textType(newTextType: string) {
        if(newTextType == "mesh" || newTextType == "sprite" || newTextType == "3d") {
            this.data.textType = newTextType;
        } else {
            throw new RangeError("Text type may only be 'mesh' or 'sprite'");
        }
    }

    /* Rendering Functions */

    fitViewToScene() : void {
       const boundingSphere = new Box3().setFromObject(this.scene).getBoundingSphere();
       console.log("Bounding sphere radius = " + boundingSphere.radius);

       const objectAngularSize = ( this.camera.fov * Math.PI / 180 );
       const distanceToCamera = boundingSphere.radius / Math.tan( objectAngularSize / 2 );
       const len = Math.sqrt( Math.pow( distanceToCamera, 2 ) + Math.pow( distanceToCamera, 2 ) ) * 0.8;
       console.log("camera len = " + len);

       this.camera.position.set(len, len, len);
       this.camera.lookAt( boundingSphere.center );
       this.center = boundingSphere.center;
       this.camera.updateProjectionMatrix();
       if(len * 2 > this.farClip) {
           this.farClip = len * 2;
       }
    }

    public renderTo(div: HTMLDivElement): void {
        console.log("Rendering");
        console.log(this.data);

        this.scene = new Scene();
        this.camera = new PerspectiveCamera(this.fieldOfView, this.width / this.height, this.nearClip, this.farClip);
        console.log("Creating camera with fov = " + this.camera.fov + ", aspect = " + this.camera.aspect +
            ", near = " + this.camera.near + ", far = " + this.camera.far);
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
        pointLight.position.set(this.barSpacing*this.yLabels.length, this.barSpacing*this.xLabels.length, 400);
        this.scene.add(pointLight);


        this.renderData();

        this.camera.up = new Vector3(0, 0, 1);
        this.camera.position.set(30, 40, 30);
        this.camera.lookAt(this.center);

        div.appendChild(this.renderer.domElement);

        this.dragControls = new DragControls(div);
        this.dragControls.addDragListener(this);
        this.dragControls.addZoomListener(this);
        this.dragControls.addSelectListener(this);

        this.fitViewToScene();

        if(this.textType == '3d') {
            let loader = new FontLoader();
            loader.load("https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/fonts/helvetiker_regular.typeface.json", font => {
                this.threeFont = font;
                this.renderLabels();
            });
        } else {
            this.renderLabels();
        }


        // start rendering the scene
        this.renderLoop();
    }

    public renderLabel(label : string, align: Vector2, rotation: number, x : number, y : number, z: number) : void {
        let text : Text2D | Mesh;
        if(this.textType == 'mesh') {
            text = new MeshText2D(label, {
                align: align, font: this.font,
                fillStyle: this.fontColor, antialias: this.fontAntialias
            });
        } else if(this.textType == 'sprite') {
            text = new SpriteText2D(label, {
                align: align, font: this.font,
                fillStyle: this.fontColor, antialias: this.fontAntialias
            });
        } else if(this.textType == '3d') {
            let textGeom = new TextGeometry(label, {font: this.threeFont, size: 5, height: 1});
            let textMat = new MeshLambertMaterial();
            text = new Mesh(textGeom, textMat);
        } else {
            throw new RangeError("Text type must be 'mesh', 'sprite', or '3d'");
        }
        text.rotation.z = rotation;
        text.scale.set(this.textScale, this.textScale, this.textScale);
        text.position.set(x, y,  z);
        this.scene.add(text);
    }

    public renderSelectBar(x: number, y: number, xSize : number, ySize: number, arr: Array<Mesh>) {
        const selectGeometry = new BoxGeometry(xSize, ySize, 0.01);
        const selectMaterial = new MeshLambertMaterial();
        let selectMesh = new Mesh(selectGeometry, selectMaterial);
        selectMesh.position.set(x, y, -1);
        selectMesh.visible = false;
        this.scene.add(selectMesh);
        arr.push(selectMesh);
    }

    public renderAxis(x: number, y: number, z: number) : void {
        let geom = new Geometry();
        geom.vertices.push(new Vector3(0, 0, 0));
        geom.vertices.push(new Vector3(x, y, z));
        let mat = new LineBasicMaterial();
        let line = new Line(geom, mat);
        this.scene.add(line);
    }

    public renderLabels() : void {
        let i = 0;
        this.yLabels.forEach( yLabel => {
            const barLen = this.xLabels.length * this.barSpacing;
            this.renderLabel(yLabel, textAlign.right, Math.PI / 2, i * this.barSpacing, this.textOffset, 0);
            this.renderLabel(yLabel, textAlign.left, Math.PI / 2, i * this.barSpacing, barLen + this.textOffset, 0);
            this.renderSelectBar((i * this.barSpacing) + (this.barSize/2), barLen / 2, this.barSize,
                barLen, this.ySelectRects);
            i++;
        });
        this.renderAxis(i * this.barSpacing, 0, 0);

        i = 0;
        this.xLabels.forEach( xLabel => {
            const barLen = this.yLabels.length * this.barSpacing;
            this.renderLabel(xLabel, textAlign.left, Math.PI, this.textOffset, i * this.barSpacing,0);
            this.renderLabel(xLabel, textAlign.right, Math.PI, barLen + this.textOffset, i * this.barSpacing, 0);
            this.renderSelectBar(barLen / 2, (i * this.barSpacing) + (this.barSize/2), barLen,
                this.barSize, this.xSelectRects);
            i++;
        });
        this.renderAxis(0, i * this.barSpacing, 0);

        const hMax = this.heights.reduce( (prev, cur) => {
            return Math.max(prev, cur);
        }, 10);
        this.renderAxis(0, 0, hMax);

    }

    public renderData() : void {
        const x_size = this.xLabels.length;
        let i = 0;
        let j = 0;
        zip(this.heights, this.colors).forEach(bar => {
            const height = bar[0];
            const color = bar[1];
            const barGeometry = new BoxGeometry(this.barSize, this.barSize, height);
            const barMaterial = new MeshLambertMaterial({color: color});
            let mesh = new Mesh(barGeometry, barMaterial);
            mesh.position.set((i * this.barSpacing) + (this.barSize/2.0),
                (j * this.barSpacing) + (this.barSize/2.0), height/2.0);
            mesh.name = i + "," + j;
            this.scene.add(mesh);
            j++;
            if(j >= x_size) {
                j = 0;
                i++;
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
        let oldPos = this.camera.position.clone();
        this.camera.position.sub(this.center).multiplyScalar(scale).add(this.center);
        let radius = this.camera.position.length();
        if(radius <= this.nearClip || radius >= this.farClip) {
            console.log("radius " + radius + " out of bounds");
            this.camera.position.copy(oldPos);
        }
    }

    public select(x: number, y: number): void {
        const cameraX = (x / this.width) * 2 - 1;
        const cameraY = -(y / this.height) * 2 + 1;
        const mousePos = new Vector2(cameraX, cameraY);
        const raycaster = new Raycaster();
        raycaster.setFromCamera(mousePos, this.camera);
        const intersects = raycaster.intersectObjects(this.scene.children);
        this.xSelectRects.forEach(rect => {
            rect.visible = false;
        });
        this.ySelectRects.forEach(rect => {
            rect.visible = false;
        });
        if(intersects.length > 0) {
            const selected = intersects[0].object;
            if(selected instanceof Mesh) {
                const mesh = selected as Mesh;
                if(mesh.name) {
                    console.log(mesh.name);
                    let coords = mesh.name.split(",");
                    if(coords.length == 2) {
                        let i = parseInt(coords[0], 10);
                        let j = parseInt(coords[1], 10);
                        this.xSelectRects[j].visible = true;
                        this.ySelectRects[i].visible = true;
                    }
                }
            }
        }
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