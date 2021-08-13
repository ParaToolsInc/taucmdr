import React, { useState, useEffect } from 'react';

import { makeDeleteDialog } from './Dialogs';

import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

import { makeErrorDialog } from './Dialogs';
import { IMimeBundle } from '@jupyterlab/nbformat'; 
import { ProjectList } from './interfaces';

export const ProjectTable = (props: any) => {
   
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    const [activeRow, setActiveRow] = useState<string | null>(null);
    var json:any = null;
    let rowData:any[];

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, rowName: string) => {
	let offset = document.getElementById('project-title').getBoundingClientRect().x
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
    }, [props.output]);

    if (props.output && outputHandle) { 
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, '')) as ProjectList;

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
				    <TableRow className='tau-table-row tau-table-row-clickable' key={row.name} onClick={(e) => {handleClick(e, row.name)}}>
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
                      keepMounted
                      open={Boolean(anchorEl)}
                      onClose={handleClose}
                      className='tau-option-menu'
                    >
			<MenuItem onClick={() => {
			    handleClose(); 
			    props.model.execute(`TauKernel.change_project('${activeRow}')`); 
			    props.onSetProject(activeRow);}}
			>
			    Select
			</MenuItem>
				
			<MenuItem onClick={() => {
			    handleClose();
			    makeDeleteDialog(props.model, 'Project', `${activeRow}`);
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
