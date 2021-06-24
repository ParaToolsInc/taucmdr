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

export const MeasurementTable = (props: any) => {

    const classes = useStyles();

    var json:any = null;
    var rows:any = null;

    if (props.output) {
        if (props.project) {
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, "")) as ProjectList;

            rows = [];
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
                rows.push({ name, profile, trace, sample, srcInst, compInst, openMP, cuda, io, mpi, shmem });
            });

            return (
                <div>
                    <h2>Measurements</h2>
                    <TableContainer component={Paper}>
                        <Table size="small" className={classes.table} aria-label="simple table">
                            <TableHead>
                                <TableRow>
                                    <TableCell className={classes.columnHeader}>Name</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Profile</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Trace</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Sample</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Source Inst.</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Compiler Inst.</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">OpenMP</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">CUDA</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">I/O</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">MPI</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">SHMEM</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {rows.map((row: any) => (
                                    <TableRow className={classes.tableRow} key={row.name}>
                                        <TableCell component="th" scope="row">
                                            {row.name}
                                        </TableCell>
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
