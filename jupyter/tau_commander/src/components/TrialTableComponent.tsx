import React, { useState, useEffect } from 'react';

import { makeEditDialog } from './Dialogs/EditDialog';
import { makeDeleteDialog } from './Dialogs/DeleteDialog';

import { IMimeBundle } from '@jupyterlab/nbformat'; 
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

import { ProjectList } from './interfaces';

export const TrialTable = (props: any) => {

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    const [activeRow, setActiveRow] = useState<any | null>(null);
    var json:any = null;
    let rowData:any[];

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, row: any) => {
	let offset = document.getElementById('trial-title').getBoundingClientRect().x
	root.style.setProperty('--tau-menu-margin', `${event.nativeEvent.clientX - offset}px`);
        setAnchorEl(event.currentTarget);
	setActiveRow(row);
    };

    const handleClose = () => {
        setAnchorEl(null);
    };

    useEffect(() => {
	setOutputHandle(true);
    }, [props.output, props.project]);

    if (outputHandle) {
        if (props.project) {
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, "")) as ProjectList;

	    if (!('status' in json)) {
                rowData = [];
                Object.entries(json[props.project]['experiments'][props.experiment]['Trial Data']).map((trial: any) => {
                    let number = trial[0];
                    let dataSize = trial[1]['Data Size'];
                    let command = trial[1]['Command'];
                    let description = trial[1]['Description'];
                    let status = trial[1]['Status'];
                    let elapsedSeconds = trial[1]['Elapsed Seconds'];
                    rowData.push({ number, dataSize, command, description, status, elapsedSeconds });
                });
                
                setRows(rowData);
                setOutputHandle(false);
                }
	    }
	    return ( <React.Fragment></React.Fragment> )
    } else {
        return (
            <React.Fragment>
                { props.output ? (
                    <div>
                        <h2 id='trial-title'>Trials</h2>
                        <TableContainer component={Paper}>
                            <Table size="small" className='tau-table' aria-label="simple table">
                                <TableHead>
                                    <TableRow>
                                        <TableCell className='tau-table-column'>Number</TableCell>
                                        <TableCell className='tau-table-column' align="right">Data Size</TableCell>
                                        <TableCell className='tau-table-column' align="right">Command</TableCell>
                                        <TableCell className='tau-table-column' align="right">Description</TableCell>
                                        <TableCell className='tau-table-column' align="right">Status</TableCell>
                                        <TableCell className='tau-table-column' align="right">Elapsed Seconds</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {rows.map((row: any) => (
					<TableRow className='tau-table-row tau-table-row-clickable' key={row.number} onClick={(e) => {handleClick(e, row)}}>
                                            <TableCell component="th" scope="row">{row.number}</TableCell>
                                            <TableCell align="right">{row.dataSize}</TableCell>
                                            <TableCell align="right">{row.command}</TableCell>
                                            <TableCell align="right">{row.description}</TableCell>
                                            <TableCell align="right">{row.status}</TableCell>
                                            <TableCell align="right">{row.elapsedSeconds}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    	<Menu
                          id="simple-menu"
                  	  anchorEl={anchorEl}
                          open={Boolean(anchorEl)}
                          onClose={handleClose}
                          className='tau-option-menu'
                        >
			    <MenuItem onClick={() => {
				handleClose();
				makeEditDialog(props.model, 'Trial', activeRow);}}
			    >
				Edit
			    </MenuItem>

			    <MenuItem onClick={() => {
				handleClose();
				makeDeleteDialog(props.model, 'Trial', `${activeRow.number}`);}}
			    >
				Delete
			    </MenuItem>
                	</Menu>
                    </div>
                ) : ( 
		    <React.Fragment></React.Fragment>
		)}
            </React.Fragment>
        )
    }
};
