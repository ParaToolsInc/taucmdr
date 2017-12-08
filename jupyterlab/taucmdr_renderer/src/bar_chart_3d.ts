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

import {
    ReadonlyJSONValue
} from '@phosphor/coreutils';

import {
    Scene,
    PerspectiveCamera,
    WebGLRenderer,
    AxisHelper,
    MeshBasicMaterial,
    Mesh,
    BoxGeometry,
    Color
} from 'three';


export class BarChart3D {

    private readonly data : ReadonlyJSONValue;

    constructor(data : ReadonlyJSONValue) {
        this.data = data;
    }

    renderTo(div : HTMLDivElement) : void {
        console.log("Rendering: " + this.data)
        let scene = new Scene();
        let camera = new PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        let renderer = new WebGLRenderer();
        renderer.setClearColor(new Color(0xEEEEEE), 1.0);
        renderer.setSize(400, 400);
        let axes = new AxisHelper(20);
        scene.add(axes);
        let cubeGeometry = new BoxGeometry(4, 4, 4);
        let cubeMaterial = new MeshBasicMaterial({color: 0xff0000, wireframe: true});
        let cube = new Mesh(cubeGeometry, cubeMaterial);
        cube.position.x = -4;
        cube.position.y = 3;
        cube.position.z = 0;
        scene.add(cube);
        camera.position.x = -30;
        camera.position.y = 40;
        camera.position.z = 30;
        camera.lookAt(scene.position);
        div.appendChild(renderer.domElement);
        // render the scene
        renderer.render(scene, camera);
    }

}