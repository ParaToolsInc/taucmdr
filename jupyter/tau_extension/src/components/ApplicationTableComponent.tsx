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

export const ApplicationTable = (props: any) => {

    const classes = useStyles();

    var json:any = null;
    var rows:any = null;

    if (props.output) {
        if (props.project) {
            let bundle = props.output['data'] as IMimeBundle;
            let string_output = bundle['text/plain'] as string;
            json = JSON.parse(string_output.replace(/\'/g, "")) as ProjectList;

            rows = [];
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
                rows.push({ name, linkage, openMP, pThreads, tbb, mpi, cuda, openCL, shmem, mpc});
            });

            return (
                <div>
                    <h2>Application</h2>
                    <TableContainer component={Paper}>
                        <Table size="small" className={classes.table} aria-label="simple table">
                            <TableHead>
                                <TableRow>
                                    <TableCell className={classes.columnHeader}>Name</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Linkage</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">OpenMP</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">Pthreads</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">TBB</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">MPI</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">CUDA</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">OpenCL</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">SHMEM</TableCell>
                                    <TableCell className={classes.columnHeader} align="right">MPC</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {rows.map((row: any) => (
                                    <TableRow className={classes.tableRow} key={row.name}>
                                        <TableCell component="th" scope="row">
                                            {row.name}
                                        </TableCell>
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
