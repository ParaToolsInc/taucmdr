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


import {Kernels} from "./kernels";
import JSONResult = Kernels.JSONResult;

import '../style/index.css'

export class Table {
    protected data : Array<JSONResult>;
    protected fields : Array<string>;
    protected table_class : string;
    protected table : HTMLTableElement;

    constructor(data : Array<JSONResult>, fields : Array<string>, table_class : string) {
        this.data = data;
        this.fields = fields;
        this.table_class = table_class;
        this.update_table();
    }

    protected update_table() {
        this.table = document.createElement('table');
        this.table.className = this.table_class;
        let tHead = this.table.createTHead();
        let tBody = this.table.createTBody();

        let tHeadRow = tHead.insertRow();
        this.fields.forEach(field => {
            let cell = document.createElement('th');
            cell.appendChild(document.createTextNode(field));
            tHeadRow.appendChild(cell);
        });

        this.data.forEach(rowData => {
            let row = tBody.insertRow();
            this.fields.forEach(field => {
                let cell = row.insertCell();
                cell.appendChild(document.createTextNode(rowData[field]));
                row.appendChild(cell);
            });
        });
    }

    get_table() : HTMLTableElement {
        return this.table;
    }
}
