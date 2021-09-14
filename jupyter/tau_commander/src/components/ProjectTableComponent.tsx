import React, { useState, useEffect } from 'react';

import { makeDeleteDialog } from './Dialogs/DeleteDialog';
import { makeErrorDialog } from './Dialogs/ErrorDialog';
import { makeCopyDialog } from './Dialogs/CopyDialog';
import { makeEditDialog } from './Dialogs/EditDialog';
import { LoadingDialog } from './Dialogs/LoadingDialog';

import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

import { IMimeBundle } from '@jupyterlab/nbformat'; 
import { ProjectList } from './interfaces';

export const ProjectTable = (props: any) => {
   
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    const [activeRow, setActiveRow] = useState<any>({});
    var json:any = null;
    let rowData:any[];

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, currentRow: any) => {
	let offset = document.getElementById('project-title').getBoundingClientRect().x
	root.style.setProperty('--tau-menu-margin', `${event.nativeEvent.clientX - offset}px`);
        setAnchorEl(event.currentTarget);
	setActiveRow(currentRow);
    };

    const handleClose = () => {
        setAnchorEl(null);
	setActiveRow(null);
    };

    useEffect(() => {
	setOutputHandle(true);
    }, [props.output]);

    if (props.output && outputHandle) { 
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, '')) as ProjectList;

	    let loadingDialog: HTMLElement = document.getElementById('loading-dialog');
	    if (loadingDialog) {
		LoadingDialog.terminate();
	    }

	    if ('status' in json) {
		if (json['status'] == false) {
		    makeErrorDialog(json['message']);
		} 
					
	    } else {
                rowData = [];
                Object.entries(json).map((project: any) => {
                    let name = project[0];
                    let targets = Object.keys(project[1]['targets']).join(', ');
                    let applications = Object.keys(project[1]['applications']).join(', ');
                    let measurements = Object.keys(project[1]['measurements']).join(', ');
                    let numExperiments = Object.keys(project[1]['experiments']).length;
                    rowData.push({ name, targets, applications, measurements, numExperiments });
                });
	        setRows(rowData);
		setOutputHandle(false);
	    }
    } 

    return (
        <React.Fragment>
            {props.output ? (
        	<div>
                    <h2 id='project-title'>Projects</h2>
                    <TableContainer component={Paper}>
                        <Table className='tau-table' size='small' aria-label='simple table'>
                            <TableHead>
                                <TableRow>
                                    <TableCell className='tau-table-column'>Name</TableCell>
                                    <TableCell className='tau-table-column' align='right'>Targets</TableCell>
                                    <TableCell className='tau-table-column' align='right'>Applications</TableCell>
                                    <TableCell className='tau-table-column' align='right'>Measurements</TableCell>
                                    <TableCell className='tau-table-column' align='right'># Experiments</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {rows.map((row: any) => (
				    <TableRow className='tau-table-row tau-table-row-clickable' key={row.name} onClick={(e) => {handleClick(e, row)}}>
					<TableCell component='th' scope='row'>{row.name}</TableCell>
					<TableCell align='right'>{row.targets}</TableCell>
					<TableCell align='right'>{row.applications}</TableCell>
					<TableCell align='right'>{row.measurements}</TableCell>
					<TableCell align='right'>{row.numExperiments}</TableCell>
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
			    props.model.execute(`TauKernel.change_project('${activeRow.name}')`); 
			    props.onSetProject(activeRow.name);
			    props.onSetExperiment(null);}}
			>
			    Select
			</MenuItem>

  			<MenuItem onClick={() => {
			    handleClose();
			    props.onSetProject(null);
			    makeEditDialog(props.model, 'Project', activeRow);}}
			>
			    Edit
			</MenuItem>

  			<MenuItem onClick={() => {
			    handleClose();
			    makeCopyDialog(props.model, 'Project', `${activeRow.name}`);}}
			>
			    Copy
			</MenuItem>
				
			<MenuItem onClick={() => {
			    handleClose();
			    makeDeleteDialog(props.model, 'Project', `${activeRow.name}`);
			    props.onSetProject(null);}}
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
};
