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
  selectExperimentDialog,
  editExperimentDialog,
  deleteExperimentDialog,
} from '../dialogs';

import * as React from 'react';

export const ExperimentTable = (props: Tables.Experiment) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);
  const [activeRow, setActiveRow] = React.useState<any | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLTableRowElement>, row: any) => {
    const root = document.documentElement;
    const offset = document.getElementById(`tau-Experiment-title-${props.projectName}`)!.getBoundingClientRect().x
    root.style.setProperty('--tau-Menu-margin', `${event.nativeEvent.clientX - offset}px`);
    setAnchorEl(event.currentTarget);
    setActiveRow(row);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setActiveRow(null);
  };

  const rows = Object.entries(props.experiments).map(([name, row]) => {
    const rowItem = {...row, 'Name': name};
    return (
      <TableRow className='tau-Table-row tau-Table-row-clickable' key={name} onClick={(e) => handleClick(e, rowItem)}>
        <TableCell component='th' scope='row'>{name}</TableCell>
        <TableCell align='right'>{row['Trials']}</TableCell>
        <TableCell align='right'>{row['Data Size']}</TableCell>
        <TableCell align='right'>{row['Target']}</TableCell>
        <TableCell align='right'>{row['Application']}</TableCell>
        <TableCell align='right'>{row['Measurement']}</TableCell>
        <TableCell align='right'>{row['TAU Makefile']}</TableCell>
      </TableRow>
    )
  });

  return (
    <div>
      <h2 id={`tau-Experiment-title-${props.projectName}`}>Experiments</h2>
      <TableContainer component={Paper}>
        <Table size='small' className='tau-Table' aria-label='simple table'>
          <TableHead>
            <TableRow>
              <TableCell className='tau-Table-column'>Name</TableCell>
              <TableCell className='tau-Table-column' align='right'># Trials</TableCell>
              <TableCell className='tau-Table-column' align='right'>Data Size</TableCell>
              <TableCell className='tau-Table-column' align='right'>Target</TableCell>
              <TableCell className='tau-Table-column' align='right'>Application</TableCell>
              <TableCell className='tau-Table-column' align='right'>Measurement</TableCell>
              <TableCell className='tau-Table-column' align='right'>TAU Makefile</TableCell>
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
          selectExperimentDialog(activeRow['Name'], props);
        }}>
          Select
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          editExperimentDialog(activeRow, props);
        }}>
          Edit
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose();
          deleteExperimentDialog(activeRow['Name'], props);
        }}>
          Delete
        </MenuItem>
      </Menu>
    </div>
  );
}

namespace Tables {
  export interface Experiment {
    project: any;
    projectName: string;
    kernelExecute: (code: string) => Promise<string>;
    updateProject: (projectName: string) => void;
    setSelectedExperiment: (experimentName: string | null) => void;
    experiments: {[key: string]: any};
  }
}
