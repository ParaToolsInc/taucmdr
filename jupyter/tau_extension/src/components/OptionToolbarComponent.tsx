import React from 'react';

import { makeDialog } from './Dialogs';

import { makeStyles } from '@material-ui/core/styles';
import Button from "@material-ui/core/Button";
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';


const useStyles = makeStyles({
  header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline',
      borderBottom: '.5px solid #aaa',
      padding: '0% 0% 0% 0%',
  },
  button: {
      borderRadius: '0px',
      padding: '2px 8px',
      textTransform: 'none',
      minWidth: '50px',
  },
  current: {
      paddingRight: '5px',
  },
  menu: {
      '& ul': {
            padding: '0% 0% 0% 0%',
      },
      '& .MuiPaper-rounded': {
            borderRadius: "0px",
      },
  },
});

export const OptionToolbar = (props: any) => {

  const classes = useStyles();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

    return (
        <div className={classes.header}>
        	{ props.project ? (
			<React.Fragment>
	     	    <div>
					<Button 
						className={classes.button} 
						size='small' 
						onClick={() => { 
							props.model.execute('from kernel import run\nrun()'); 
							props.onSetProject(null); 
						}}
					>
                    	Update
                	</Button>

					<Button 
					  className={classes.button} 
					  size='small'
                      aria-controls="simple-menu" 
                      aria-haspopup="true" 
                      onClick={handleClick}
					>
   	    			    New
          			</Button>

                    <Menu
                      id="simple-menu"
                      anchorEl={anchorEl}
                      keepMounted
                      open={Boolean(anchorEl)}
                      onClose={handleClose}
                      className={classes.menu}
                    >
                        <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Project');}}>New Project</MenuItem>
                        <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Target');}}>New Target</MenuItem>
                        <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Application');}}>New Application</MenuItem>
                        <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Measurement');}}>New Measurement</MenuItem>
                        <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Experiment');}}>New Experiment</MenuItem>
                    </Menu>
		 		</div>

				<div>
					<p className={classes.current}>
		    				<b>Current project: </b>
		    				{props.project}
					</p>
				</div>
		    </React.Fragment>
		) : (
			<React.Fragment>
				<Button 
					className={classes.button} 
					size='small' 
					onClick={() => { 
						props.model.execute('from kernel import run\nrun()'); 
						props.onSetProject(null); 
					}}
				>
					Update
				</Button>
			</React.Fragment>
		)}
	</div>
    )
};
