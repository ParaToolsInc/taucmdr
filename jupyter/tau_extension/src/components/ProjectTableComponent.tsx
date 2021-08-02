import React, { useState, useEffect } from 'react';

import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

import { IMimeBundle } from '@jupyterlab/nbformat'; 
import { ProjectList } from './interfaces';

export const ProjectTable = (props: any) => {
   
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    var json:any = null;
    let rowData:any[] = null;

    useEffect(() => {
	setOutputHandle(true);
    }, [props.output]);

    if (props.output && outputHandle) { 
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, '')) as ProjectList;

	    if ('status' in json) {
	        console.log(json);
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
                    <h2>Projects</h2>
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
                                    <TableRow 
					className='tau-table-row tau-table-row-clickable' 
					key={row.name} 
					onClick={() => {
						props.model.execute(`TauKernel.change_project('${row.name}')`); 
						props.onSetProject(row.name);
					}}>
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
        	</div>
            ) : null }
    	</React.Fragment>
    )
};
