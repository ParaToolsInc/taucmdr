import React from 'react';

import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';
import { makeStyles } from '@material-ui/core/styles';

import { IMimeBundle } from '@jupyterlab/nbformat'; 
import { ProjectList } from './interfaces';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
  tableRow: {
    '&:hover': {
        backgroundColor: '#d9e6fa',
        cursor: 'pointer',
    },
  },
  columnHeader: {
    fontWeight: 'bold',
    backgroundColor: '#e7eaeb',
  },
});

export const ProjectTable = (props: any) => {

    const classes = useStyles();

    var rows:any = null;
    var json:any = null;

    if (props.output) { 
        let bundle = props.output['data'] as IMimeBundle;
        let string_output = bundle['text/plain'] as string;
        json = JSON.parse(string_output.replace(/\'/g, '')) as ProjectList;

        rows = [];
        Object.entries(json).map((project: any) => {
            let name = project[0];
            let targets = Object.keys(project[1]['targets']).join(', ');
            let applications = Object.keys(project[1]['applications']).join(', ');
            let measurements = Object.keys(project[1]['measurements']).join(', ');
            let numExperiments = Object.keys(project[1]['experiments']).length;
            rows.push({ name, targets, applications, measurements, numExperiments });
        });
    } 

    return (
        <div>
            <h2>Projects</h2>
            {props.output ? (
                <TableContainer component={Paper}>
                    <Table className={classes.table} size='small' aria-label='simple table'>
                        <TableHead>
                            <TableRow>
                                <TableCell className={classes.columnHeader}>Name</TableCell>
                                <TableCell className={classes.columnHeader} align='right'>Targets</TableCell>
                                <TableCell className={classes.columnHeader} align='right'>Applications</TableCell>
                                <TableCell className={classes.columnHeader} align='right'>Measurements</TableCell>
                                <TableCell className={classes.columnHeader} align='right'># Experiments</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {rows.map((row: any) => (
                                <TableRow className={classes.tableRow} key={row.name} onClick={() => props.onSetProject(row.name)}>
                                    <TableCell component='th' scope='row'>
                                        {row.name}
                                    </TableCell>
                                    <TableCell align='right'>{row.targets}</TableCell>
                                    <TableCell align='right'>{row.applications}</TableCell>
                                    <TableCell align='right'>{row.measurements}</TableCell>
                                    <TableCell align='right'>{row.numExperiments}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            ) : (
                <p>No data</p>
            )}
        </div>
    )
};
