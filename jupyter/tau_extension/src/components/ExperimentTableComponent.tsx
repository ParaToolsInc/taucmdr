import React from 'react';

import { IMimeBundle } from '@jupyterlab/nbformat'; 
import { makeStyles } from '@material-ui/core/styles';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

import { ProjectList } from './interfaces';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
  tableRow: {
    '&:hover': {
        backgroundColor: '#d9e6fa',
    },
  },
  columnHeader: {
    fontWeight: 'bold',
    backgroundColor: '#e7eaeb',
  },
});

export const ExperimentTable = (props: any) => {

    const classes = useStyles();

    var json:any = null;
    var rows:any = null;

    if (props.output) {
        if (props.project) {
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, "")) as ProjectList;

            rows = [];
            Object.entries(json[props.project]['experiments']).map((experiment: any) => {
                let name = experiment[0];
                let numTrials = experiment[1]['Trials'];
                let dataSize = experiment[1]['Data Size'];
                let target = experiment[1]['Target'];
                let application = experiment[1]['Application'];
                let measurement = experiment[1]['Measurement'];
                let tauMakefile = experiment[1]['TAU Makefile'];
                rows.push({ name, numTrials, dataSize, target, application, measurement, tauMakefile });
            });

            return (
                <div>
                    <h2>Experiments</h2>
                    <TableContainer component={Paper}>
                        <Table size="small" className={classes.table} aria-label="simple table">
                            <TableHead>
                                <TableRow>
                                    <TableCell className={classes.columnHeader}>Name</TableCell>
                                    <TableCell className={classes.columnHeader} align="right"># Trials</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Data Size</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Target</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Application</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Measurement</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">TAU Makefile</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {rows.map((row: any) => (
                                    <TableRow className={classes.tableRow} key={row.name}>
                                        <TableCell component="th" scope="row">
                                            {row.name}
                                        </TableCell>
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
                </div>
            )
        } else {
            return (
                <div>
                </div>
            )
        }
    } else {
        return (
            <div>
            </div>
        )
    }
};
