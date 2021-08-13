import React, { useState, useEffect } from 'react';

import { makeDeleteDialog } from './Dialogs';

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

export const TargetTable = (props: any) => {

    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    const [activeRow, setActiveRow] = useState<string | null>(null);
    var json:any = null;
    let rowData:any[];

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, rowName: string) => {
	let offset = document.getElementById('target-title').getBoundingClientRect().x
	root.style.setProperty('--tau-menu-margin', `${event.nativeEvent.clientX - offset}px`);
        setAnchorEl(event.currentTarget);
	setActiveRow(rowName);
    };

    const handleClose = () => {
        setAnchorEl(null);
	setActiveRow(null);
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
                Object.entries(json[props.project]['targets']).map((target: any) => {
                    let name = target[0];
                    let hostOS = target[1]['Host OS'];
                    let hostArch = target[1]['Host Arch'];
                    let hostCompilers = target[1]['Host Compilers'];
                    let mpiCompilers = target[1]['MPI Compilers'];
                    let shmemCompilers = target[1]['SHMEM Compilers'];
                    rowData.push({ name, hostOS, hostArch, hostCompilers, mpiCompilers, shmemCompilers });
                });

	        setRows(rowData);
		setOutputHandle(false);
	    }

        }
        return ( <React.Fragment></React.Fragment> )
    } else {
        return (
   	    <React.Fragment>
	        {props.output ? (	
		    <div>
		        <h2 id='target-title'>Targets</h2>
		        <TableContainer component={Paper}>
			    <Table size="small" className='tau-table' aria-label="simple table">
			        <TableHead>
				    <TableRow>
				        <TableCell className='tau-table-column'>Name</TableCell>
				        <TableCell className='tau-table-column' align="right">Host OS</TableCell>
				        <TableCell className='tau-table-column' align="right">Host Arch</TableCell>
				        <TableCell className='tau-table-column' align="right">Host Compilers</TableCell>
				        <TableCell className='tau-table-column' align="right">MPI Compilers</TableCell>
				        <TableCell className='tau-table-column' align="right">SHMEM Compilers</TableCell>
			    	    </TableRow>
			        </TableHead>
			        <TableBody>
				    {rows.map((row: any) => (
					<TableRow className='tau-table-row tau-table-row-clickable' key={row.name} onClick={(e) => {handleClick(e, row.name)}}>
					    <TableCell component="th" scope="row">{row.name}</TableCell>
					    <TableCell align="right">{row.hostOS}</TableCell>
					    <TableCell align="right">{row.hostArch}</TableCell>
					    <TableCell align="right">{row.hostCompilers}</TableCell>
					    <TableCell align="right">{row.mpiCompilers}</TableCell>
					    <TableCell align="right">{row.shmemCompilers}</TableCell>
				        </TableRow>
				    ))}
			        </TableBody>
			    </Table>
		        </TableContainer>
                    	<Menu
                          id="simple-menu"
                  	  anchorEl={anchorEl}
                          keepMounted
                          open={Boolean(anchorEl)}
                          onClose={handleClose}
                          className='tau-option-menu'
                        >
			    <MenuItem>Edit</MenuItem>
			    <MenuItem>Copy</MenuItem>
			    <MenuItem onClick={() => {handleClose(); makeDeleteDialog(props.model, 'Target', `${activeRow}`)}}>Delete</MenuItem>
                	</Menu>
		    </div>				
	        ) : (
		    <React.Fragment></React.Fragment>
		)}
	    </React.Fragment>
	)
    }
};
