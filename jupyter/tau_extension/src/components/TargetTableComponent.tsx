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

export const TargetTable = (props: any) => {

    const classes = useStyles();

    var json:any = null;
    var rows:any = null;

    if (props.output) {
        if (props.project) {
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, "")) as ProjectList;

            rows = [];
            Object.entries(json[props.project]['targets']).map((target: any) => {
                let name = target[0];
                let hostOS = target[1]['Host OS'];
                let hostArch = target[1]['Host Arch'];
                let hostCompilers = target[1]['Host Compilers'];
                let mpiCompilers = target[1]['MPI Compilers'];
                let shmemCompilers = target[1]['SHMEM Compilers'];
                rows.push({ name, hostOS, hostArch, hostCompilers, mpiCompilers, shmemCompilers });
            });

            return (
                <div>
                    <h2>Targets</h2>
                    <TableContainer component={Paper}>
                        <Table size="small" className={classes.table} aria-label="simple table">
                            <TableHead>
                                <TableRow>
                                    <TableCell className={classes.columnHeader}>Name</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Host OS</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Host Arch</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Host Compilers</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">MPI Compilers</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">SHMEM Compilers</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {rows.map((row: any) => (
                                    <TableRow className={classes.tableRow} key={row.name}>
                                        <TableCell component="th" scope="row">
                                            {row.name}
                                        </TableCell>
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
