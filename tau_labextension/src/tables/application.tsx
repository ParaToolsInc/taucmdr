import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

import {
  editApplicationDialog,
  copyApplicationDialog,
  deleteApplicationDialog,
} from '../dialogs';

import * as React from 'react';

export const ApplicationTable = (props: Tables.Application) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);
  const [activeRow, setActiveRow] = React.useState<any | null>(null);

  let root = document.documentElement;
  const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, row: any) => {
    let offset = document.getElementById(`tau-Application-title-${props.projectName}`)!.getBoundingClientRect().x
    root.style.setProperty('--tau-Menu-margin', `${event.nativeEvent.clientX - offset}px`);
    setAnchorEl(event.currentTarget);
    setActiveRow(row);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setActiveRow(null);
  };

  let rows = Object.entries(props.applications).map(([name, row]) => {
    let rowItem = {...row, 'Name': name};
    return (
      <TableRow className='tau-Table-row tau-Table-row-clickable' key={name} onClick={(e) => handleClick(e, rowItem)} >
        <TableCell component='th' scope='row'>{name}</TableCell>
        <TableCell align='right'>{row['Linkage']}</TableCell>
        <TableCell align='right'>{row['OpenMP']}</TableCell>
        <TableCell align='right'>{row['Pthreads']}</TableCell>
        <TableCell align='right'>{row['TBB']}</TableCell>
        <TableCell align='right'>{row['MPI']}</TableCell>
        <TableCell align='right'>{row['CUDA']}</TableCell>
        <TableCell align='right'>{row['OpenCL']}</TableCell>
        <TableCell align='right'>{row['SHMEM']}</TableCell>
        <TableCell align='right'>{row['MPC']}</TableCell>
      </TableRow>
    )
  });

  return (
    <div>
      <h2 id={`tau-Application-title-${props.projectName}`}>Applications</h2>
      <TableContainer component={Paper}>
        <Table size='small' className='tau-Table' aria-label='simple table'>
          <TableHead>
            <TableRow>
              <TableCell className='tau-Table-column'>Name</TableCell>
              <TableCell className='tau-Table-column' align='right'>Linkage</TableCell>
              <TableCell className='tau-Table-column' align='right'>OpenMP</TableCell>
              <TableCell className='tau-Table-column' align='right'>Pthreads</TableCell>
              <TableCell className='tau-Table-column' align='right'>TBB</TableCell>
              <TableCell className='tau-Table-column' align='right'>MPI</TableCell>
              <TableCell className='tau-Table-column' align='right'>CUDA</TableCell>
              <TableCell className='tau-Table-column' align='right'>OpenCL</TableCell>
              <TableCell className='tau-Table-column' align='right'>SHMEM</TableCell>
              <TableCell className='tau-Table-column' align='right'>MPC</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows}
          </TableBody>
        </Table>
      </TableContainer>
      <Menu
        id="simple-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        className='tau-Option-menu'
      >
        <MenuItem onClick={() => {
          handleClose();
          editApplicationDialog(activeRow, props);
        }}>
          Edit
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          copyApplicationDialog(activeRow['Name'], props);
        }}>
          Copy
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          deleteApplicationDialog(activeRow['Name'], props);
          }}
        >
          Delete
        </MenuItem>

      </Menu>
    </div>
  );
}

namespace Tables {
  export interface Application {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    applications: {[key: string]: any};
  }
}
