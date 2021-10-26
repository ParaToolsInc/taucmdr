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

 
  let rows = Object.entries(props.trials).map(([name, row]) => {
    let rowItem = {...row, 'Name': name};
    console.log(rowItem);
    return (
      <TableRow className='tau-Table-row tau-Table-row-clickable' key={row.number} onClick={(e) => {handleClick(e, rowItem)}}>
        <TableCell component='th' scope='row'>{row.number}</TableCell>
        <TableCell align='right'>{row.dataSize}</TableCell>
        <TableCell align='right'>{row.command}</TableCell>
        <TableCell align='right'>{row.description}</TableCell>
        <TableCell align='right'>{row.status}</TableCell>
        <TableCell align='right'>{row.elapsedSeconds}</TableCell>
      </TableRow>
    )   
  }); 

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
          console.log(activeRow);
    
          }}  
        >   
          Edit
        </MenuItem>

        <MenuItem onClick={() => {
          handleClose(); 
          }}  
        >   
          Delete
        </MenuItem>
      </Menu>
    </div>
  );  
}

namespace Tables {
  export interface Trial {
    projectName: string;
    trials: {[key: string]: any}
  }
}
