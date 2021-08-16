import React, { useState, useEffect } from 'react';

import { makeDeleteDialog } from './Dialogs/DeleteDialog';
import { makeCopyDialog } from './Dialogs/CopyDialog';

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

export const MeasurementTable = (props: any) => {

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    const [activeRow, setActiveRow] = useState<string | null>(null);
    var json:any = null;
    let rowData:any[];

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, rowName: string) => {
	let offset = document.getElementById('measurement-title').getBoundingClientRect().x
	root.style.setProperty('--tau-menu-margin', `${event.nativeEvent.clientX - offset}px`);
        setAnchorEl(event.currentTarget);
	setActiveRow(rowName);
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
                Object.entries(json[props.project]['measurements']).map((measurement: any) => {
                    let name = measurement[0];
                    let profile = measurement[1]['Profile'];
                    let trace = measurement[1]['Trace'];
                    let sample = measurement[1]['Sample'];
                    let srcInst = measurement[1]['Source Inst.'];
                    let compInst = measurement[1]['Compiler Inst.'];
                    let openMP = measurement[1]['OpenMP'];
                    let cuda = measurement[1]['CUDA'];
                    let io = measurement[1]['I/O'];
                    let mpi = measurement[1]['MPI'];
                    let shmem = measurement[1]['SHMEM'];
                    rowData.push({ name, profile, trace, sample, srcInst, compInst, openMP, cuda, io, mpi, shmem });
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
                        <h2 id='measurement-title'>Measurements</h2>
                        <TableContainer component={Paper}>
                            <Table size="small" className='tau-table' aria-label="simple table">
                                <TableHead>
                                    <TableRow>
                                        <TableCell className='tau-table-column'>Name</TableCell>
                                        <TableCell className='tau-table-column' align="right">Profile</TableCell>
                                        <TableCell className='tau-table-column' align="right">Trace</TableCell>
                                        <TableCell className='tau-table-column' align="right">Sample</TableCell>
                                        <TableCell className='tau-table-column' align="right">Source Inst.</TableCell>
                                        <TableCell className='tau-table-column' align="right">Compiler Inst.</TableCell>
                                        <TableCell className='tau-table-column' align="right">OpenMP</TableCell>
                                        <TableCell className='tau-table-column' align="right">CUDA</TableCell>
                                        <TableCell className='tau-table-column' align="right">I/O</TableCell>
                                        <TableCell className='tau-table-column' align="right">MPI</TableCell>
                                        <TableCell className='tau-table-column' align="right">SHMEM</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {rows.map((row: any) => (
					<TableRow className='tau-table-row tau-table-row-clickable' key={row.name} onClick={(e) => {handleClick(e, row.name)}}>
                                            <TableCell component="th" scope="row">{row.name}</TableCell>
                                            <TableCell align="right">{row.profile}</TableCell>
                                            <TableCell align="right">{row.trace}</TableCell>
                                            <TableCell align="right">{row.sample}</TableCell>
                                            <TableCell align="right">{row.srcInst}</TableCell>
                                            <TableCell align="right">{row.compInst}</TableCell>
                                            <TableCell align="right">{row.openMP}</TableCell>
                                            <TableCell align="right">{row.cuda}</TableCell>
                                            <TableCell align="right">{row.io}</TableCell>
                                            <TableCell align="right">{row.mpi}</TableCell>
                                            <TableCell align="right">{row.shmem}</TableCell>
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
			    <MenuItem onClick={() => {
				handleClose();
				makeCopyDialog(props.model, 'Measurement', `${activeRow}`);}}
			    >
				Copy
			    </MenuItem>


			    <MenuItem onClick={() => {handleClose(); makeDeleteDialog(props.model, 'Measurement', `${activeRow}`)}}>Delete</MenuItem>
                	</Menu>
                    </div>
                ) : ( 
		    <React.Fragment></React.Fragment>
		)}
            </React.Fragment>
        )
    }
};
