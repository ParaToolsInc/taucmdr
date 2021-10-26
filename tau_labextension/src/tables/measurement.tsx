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
  editMeasurementDialog, 
  copyMeasurementDialog,
  deleteMeasurementDialog
} from '../dialogs';

import * as React from 'react';

export const MeasurementTable = (props: Tables.Measurement) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);
  const [activeRow, setActiveRow] = React.useState<any | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, row: any) => {
    let root = document.documentElement;
    let offset = document.getElementById(`tau-Measurement-title-${props.projectName}`)!.getBoundingClientRect().x
    root.style.setProperty('--tau-Menu-margin', `${event.nativeEvent.clientX - offset}px`);
    setAnchorEl(event.currentTarget);
    setActiveRow(row);
  };  

  const handleClose = () => {
    setAnchorEl(null);
    setActiveRow(null);
  };  

  let rows = Object.entries(props.measurements).map(([name, row]) => {
    let rowItem = {...row, 'Name': name};
    return (
      <TableRow className='tau-Table-row tau-Table-row-clickable' key={name} onClick={(e) => handleClick(e, rowItem)}>
        <TableCell component='th' scope='row'>{name}</TableCell>
        <TableCell align='right'>{row['Profile']}</TableCell>
        <TableCell align='right'>{row['Trace']}</TableCell>
        <TableCell align='right'>{row['Sample']}</TableCell>
        <TableCell align='right'>{row['Source Inst.']}</TableCell>
        <TableCell align='right'>{row['Compiler Inst.']}</TableCell>
        <TableCell align='right'>{row['OpenMP']}</TableCell>
        <TableCell align='right'>{row['CUDA']}</TableCell>
        <TableCell align='right'>{row['I/O']}</TableCell>
        <TableCell align='right'>{row['MPI']}</TableCell>
        <TableCell align='right'>{row['SHMEM']}</TableCell>
      </TableRow>
    )   
  }); 

  return (
    <div>
      <h2 id={`tau-Measurement-title-${props.projectName}`}>Measurements</h2>
      <TableContainer component={Paper}>
        <Table size='small' className='tau-Table' aria-label='simple table'>
          <TableHead>
            <TableRow>
              <TableCell className='tau-Table-column'>Name</TableCell>
              <TableCell className='tau-Table-column' align='right'>Profile</TableCell>
              <TableCell className='tau-Table-column' align='right'>Trace</TableCell>
              <TableCell className='tau-Table-column' align='right'>Sample</TableCell>
              <TableCell className='tau-Table-column' align='right'>Source Inst.</TableCell>
              <TableCell className='tau-Table-column' align='right'>Compiler Inst.</TableCell>
              <TableCell className='tau-Table-column' align='right'>OpenMP</TableCell>
              <TableCell className='tau-Table-column' align='right'>CUDA</TableCell>
              <TableCell className='tau-Table-column' align='right'>I/O</TableCell>
              <TableCell className='tau-Table-column' align='right'>MPI</TableCell>
              <TableCell className='tau-Table-column' align='right'>SHMEM</TableCell>
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
          editMeasurementDialog(activeRow, props);
        }}>
          Edit
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          copyMeasurementDialog(activeRow['Name'], props);
        }}>   
          Copy
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose(); 
          deleteMeasurementDialog(activeRow['Name'], props);
        }}> 
          Delete
        </MenuItem>
      </Menu>
    </div>
  );  
}

namespace Tables {
  export interface Measurement {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    measurements: {[key: string]: any};
  }
}


