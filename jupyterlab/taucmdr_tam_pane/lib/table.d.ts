import { Kernels } from "./kernels";
import JSONResult = Kernels.JSONResult;
import '../style/index.css';
export declare class Table {
    protected data: Array<JSONResult>;
    protected fields: Array<string>;
    protected table_class: string;
    protected table: HTMLTableElement;
    constructor(data: Array<JSONResult>, fields: Array<string>, table_class: string);
    protected update_table(): void;
    get_table(): HTMLTableElement;
}
