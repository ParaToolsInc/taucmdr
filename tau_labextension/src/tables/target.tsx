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
  editTargetDialog,
  copyTargetDialog,
  deleteTargetDialog,
} from '../dialogs';

import * as React from 'react';

export const TargetTable = (props: Tables.Target) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);
  const [activeRow, setActiveRow] = React.useState<any | null>(null);

  let root = document.documentElement;
  const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, row: any) => {
    let offset = document.getElementById(`tau-Target-title-${props.projectName}`)!.getBoundingClientRect().x
    root.style.setProperty('--tau-Menu-margin', `${event.nativeEvent.clientX - offset}px`);
    setAnchorEl(event.currentTarget);
    setActiveRow(row);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setActiveRow(null);
  };

  let rows = Object.entries(props.targets).map(([name, row]) => {
    let rowItem = {...row, 'Name': name};
    return (
      <TableRow className='tau-Table-row tau-Table-row-clickable' key={name} onClick={(e) => handleClick(e, rowItem)}>
        <TableCell component='th' scope='row'>{name}</TableCell>
        <TableCell align='right'>{row['Host OS']}</TableCell>
        <TableCell align='right'>{row['Host Arch']}</TableCell>
        <TableCell align='right'>{row['Host Compilers']}</TableCell>
        <TableCell align='right'>{row['MPI Compilers']}</TableCell>
        <TableCell align='right'>{row['SHMEM Compilers']}</TableCell>
      </TableRow>
    )
  });

  return (
    <div>
      <h2 id={`tau-Target-title-${props.projectName}`}>Targets</h2>
      <TableContainer component={Paper}>
        <Table size='small' className='tau-Table' aria-label='simple table'>
          <TableHead>
            <TableRow>
              <TableCell className='tau-Table-column'>Name</TableCell>
              <TableCell className='tau-Table-column' align='right'>Host OS</TableCell>
              <TableCell className='tau-Table-column' align='right'>Host Arch</TableCell>
              <TableCell className='tau-Table-column' align='right'>Host Compilers</TableCell>
              <TableCell className='tau-Table-column' align='right'>MPI Compilers</TableCell>
              <TableCell className='tau-Table-column' align='right'>SHMEM Compilers</TableCell>
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
          editTargetDialog(activeRow, props);
        }}>
          Edit
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          copyTargetDialog(activeRow['Name'], props);
        }}>
          Copy
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          deleteTargetDialog(activeRow['Name'], props);
        }}>
          Delete
        </MenuItem>
      </Menu>
    </div>
  );
}

namespace Tables {
  export interface Target {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    targets: {[key: string]: any};
  }
}


