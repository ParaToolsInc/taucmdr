import React, { useState, useEffect } from 'react';

import { makeDeleteDialog } from './Dialogs/DeleteDialog';
import { makeCopyDialog } from './Dialogs/CopyDialog';
import { makeEditDialog } from './Dialogs/EditDialog';

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

export const ApplicationTable = (props: any) => {

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    const [activeRow, setActiveRow] = useState<any | null>(null);
    var json:any = null;
    let rowData:any[];

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, row: any) => {
	let offset = document.getElementById('application-title').getBoundingClientRect().x
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
                Object.entries(json[props.project]['applications']).map((application: any) => {
                    let name = application[0];
                    let linkage = application[1]['Linkage'];
                    let openMP = application[1]['OpenMP'];
                    let pThreads = application[1]['Pthreads'];
                    let tbb = application[1]['TBB'];
                    let mpi = application[1]['MPI'];
                    let cuda = application[1]['CUDA'];
                    let openCL = application[1]['OpenCL'];
                    let shmem = application[1]['SHMEM'];
                    let mpc = application[1]['MPC'];
                    rowData.push({ name, linkage, openMP, pThreads, tbb, mpi, cuda, openCL, shmem, mpc});
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
                        <h2 id='application-title'>Application</h2>
                        <TableContainer component={Paper}>
                            <Table size="small" className='tau-table' aria-label="simple table">
                                <TableHead>
                                    <TableRow>
                                        <TableCell className='tau-table-column'>Name</TableCell>
                                        <TableCell className='tau-table-column' align="right">Linkage</TableCell>
                                        <TableCell className='tau-table-column' align="right">OpenMP</TableCell>
                                        <TableCell className='tau-table-column' align="right">Pthreads</TableCell>
                                        <TableCell className='tau-table-column' align="right">TBB</TableCell>
                                        <TableCell className='tau-table-column' align="right">MPI</TableCell>
                                        <TableCell className='tau-table-column' align="right">CUDA</TableCell>
                                        <TableCell className='tau-table-column' align="right">OpenCL</TableCell>
                                        <TableCell className='tau-table-column' align="right">SHMEM</TableCell>
                                        <TableCell className='tau-table-column' align="right">MPC</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {rows.map((row: any) => (
					<TableRow className='tau-table-row tau-table-row-clickable' key={row.name} onClick={(e) => {handleClick(e, row)}}>
                                            <TableCell component="th" scope="row">{row.name}</TableCell>
                                            <TableCell align="right">{row.linkage}</TableCell>
                                            <TableCell align="right">{row.openMP}</TableCell>
                                            <TableCell align="right">{row.pThreads}</TableCell>
                                            <TableCell align="right">{row.tbb}</TableCell>
                                            <TableCell align="right">{row.mpi}</TableCell>
                                            <TableCell align="right">{row.cuda}</TableCell>
                                            <TableCell align="right">{row.openCL}</TableCell>
                                            <TableCell align="right">{row.shmem}</TableCell>
                                            <TableCell align="right">{row.mpc}</TableCell>
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
				makeEditDialog(props.model, 'Application', activeRow);}}
			    >
				Edit
			    </MenuItem>

			    <MenuItem onClick={() => {
				handleClose();
				makeCopyDialog(props.model, 'Application', `${activeRow.name}`);}}
			    >
				Copy
			    </MenuItem>

			    <MenuItem onClick={() => {
				handleClose(); 
				makeDeleteDialog(props.model, 'Application', `${activeRow.name}`);}}
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
