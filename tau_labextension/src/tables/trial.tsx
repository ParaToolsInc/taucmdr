import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

import * as React from 'react';

import {
  editTrialDialog, 
  deleteTrialDialog
} from '../dialogs';

export const TrialTable = (props: Tables.Trial) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);
  const [activeRow, setActiveRow] = React.useState<any | null>(null);

  let root = document.documentElement;
  const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, row: any) => {
    let offset = document.getElementById(`tau-Trial-title-${props.projectName}`)!.getBoundingClientRect().x
    root.style.setProperty('--tau-Menu-margin', `${event.nativeEvent.clientX - offset}px`);
    setAnchorEl(event.currentTarget);
    setActiveRow(row);
  };  

  const handleClose = () => {
    setAnchorEl(null);
    setActiveRow(null);
  };  

  if (!(props.experiment)) {
    return (
      <React.Fragment></React.Fragment>
    )
  }

  let rows = Object.entries(props.experiment['Trial Data']).map(([name, row]) => {
    let rowItem = {...row, 'Number': name};
    return (
      <TableRow className='tau-Table-row tau-Table-row-clickable' key={name} onClick={(e) => {handleClick(e, rowItem)}}>
        <TableCell component='th' scope='row'>{name}</TableCell>
        <TableCell align='right'>{row['Data Size']}</TableCell>
        <TableCell align='right'>{row['Command']}</TableCell>
        <TableCell align='right'>{row['Description']}</TableCell>
        <TableCell align='right'>{row['Status']}</TableCell>
        <TableCell align='right'>{row['Elapsed Seconds'].toFixed(5)}</TableCell>
      </TableRow>
    )   
  }); 

  if (!(rows.length)) {
    props.setSelectedExperiment(null);
    return (
      <React.Fragment></React.Fragment>
    )
  }

  return (
    <div>
      <h2 id={`tau-Trial-title-${props.projectName}`}>Trials</h2>
      <TableContainer component={Paper}>
        <Table size='small' className='tau-Table' aria-label='simple table'>
          <TableHead>
            <TableRow>
              <TableCell className='tau-Table-column'>Number</TableCell>
              <TableCell className='tau-Table-column' align='right'>Data Size</TableCell>
              <TableCell className='tau-Table-column' align='right'>Command</TableCell>
              <TableCell className='tau-Table-column' align='right'>Description</TableCell>
              <TableCell className='tau-Table-column' align='right'>Status</TableCell>
              <TableCell className='tau-Table-column' align='right'>Elapsed Seconds</TableCell>
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
          props.openDisplayCommand({
              project: props.projectName, 
              experiment: props.selectedExperiment, 
              trial: activeRow['Number']
          });
        }}>   
          Display
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          editTrialDialog(activeRow, props);
        }}>   
          Edit
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose(); 
          deleteTrialDialog(activeRow['Number'], props);
        }}>   
          Delete
        </MenuItem>
      </Menu>
    </div>
  );  
}

export interface IPlotlyDisplayItem {
  [key: string]: any
}

namespace Tables {
  export interface Trial {
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    experiment: {[key: string]: {[key: string]: any}}
    setSelectedExperiment: (experiment: string | null) => void;
    selectedExperiment: string;
    openDisplayCommand: (trialPath: IPlotlyDisplayItem) => void
  }
}
