import React, { useState, useEffect } from 'react';

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

export const ExperimentTable = (props: any) => {

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [outputHandle, setOutputHandle] = useState<boolean>(false); 
    const [rows, setRows] = useState<any[]>([]);
    const [activeRow, setActiveRow] = useState<string | null>(null);
    var json:any = null;
    let rowData:any[];

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, rowName: string) => {
	let offset = document.getElementById('experiment-title').getBoundingClientRect().x
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
                Object.entries(json[props.project]['experiments']).map((experiment: any) => {
                    let name = experiment[0];
                    let numTrials = experiment[1]['Trials'];
                    let dataSize = experiment[1]['Data Size'];
                    let target = experiment[1]['Target'];
                    let application = experiment[1]['Application'];
                    let measurement = experiment[1]['Measurement'];
                    let tauMakefile = experiment[1]['TAU Makefile'];
                    rowData.push({ name, numTrials, dataSize, target, application, measurement, tauMakefile });
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
                        <h2 id='experiment-title'>Experiments</h2>
                        <TableContainer component={Paper}>
                            <Table size="small" className='tau-table' aria-label="simple table">
                                <TableHead>
                                    <TableRow>
                                        <TableCell className='tau-table-column'>Name</TableCell>
                                        <TableCell className='tau-table-column' align="right"># Trials</TableCell>
                                        <TableCell className='tau-table-column' align="right">Data Size</TableCell>
                                        <TableCell className='tau-table-column' align="right">Target</TableCell>
                                        <TableCell className='tau-table-column' align="right">Application</TableCell>
                                        <TableCell className='tau-table-column' align="right">Measurement</TableCell>
                                        <TableCell className='tau-table-column' align="right">TAU Makefile</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {rows.map((row: any) => (
					<TableRow className='tau-table-row tau-table-row-clickable' key={row.name} onClick={(e) => {handleClick(e, row.name)}}>
                                            <TableCell component="th" scope="row">{row.name}</TableCell>
                                            <TableCell align="right">{row.numTrials}</TableCell>
                                            <TableCell align="right">{row.dataSize}</TableCell>
                                            <TableCell align="right">{row.target}</TableCell>
                                            <TableCell align="right">{row.application}</TableCell>
                                            <TableCell align="right">{row.measurement}</TableCell>
                                            <TableCell align="right">{row.tauMakefile}</TableCell>
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
			    <MenuItem onClick={() => {handleClose(); makeDeleteDialog(props.model, 'Experiment', `${activeRow}`)}}>Delete</MenuItem>
                	</Menu>
                    </div>
                ) : ( 
		    <React.Fragment></React.Fragment>
		)}
            </React.Fragment>
        )
    }
};
