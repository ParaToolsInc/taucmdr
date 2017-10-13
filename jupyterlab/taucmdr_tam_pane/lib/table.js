"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
require("../style/index.css");
var Table = (function () {
    function Table(data, fields, table_class) {
        this.data = data;
        this.fields = fields;
        this.table_class = table_class;
        this.update_table();
    }
    Table.prototype.update_table = function () {
        var _this = this;
        this.table = document.createElement('table');
        this.table.className = this.table_class;
        var tHead = this.table.createTHead();
        var tBody = this.table.createTBody();
        var tHeadRow = tHead.insertRow();
        this.fields.forEach(function (field) {
            var cell = document.createElement('th');
            cell.appendChild(document.createTextNode(field));
            tHeadRow.appendChild(cell);
        });
        this.data.forEach(function (rowData) {
            var row = tBody.insertRow();
            _this.fields.forEach(function (field) {
                var cell = row.insertCell();
                cell.appendChild(document.createTextNode(rowData[field]));
                row.appendChild(cell);
            });
        });
    };
    Table.prototype.get_table = function () {
        return this.table;
    };
    return Table;
}());
exports.Table = Table;
