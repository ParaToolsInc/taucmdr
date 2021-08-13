import React, { useState } from 'react';

import { makeNewDialog, makeColorDialog } from './Dialogs';

import Button from "@material-ui/core/Button";
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

export const OptionToolbar = (props: any) => {

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    let root = document.documentElement;
    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
	let offset = document.getElementById('new-button').getBoundingClientRect().x
	root.style.setProperty('--tau-menu-margin', `${event.nativeEvent.clientX - offset}px`);
        setAnchorEl(event.currentTarget);
    };

    const handleClose = () => {
        setAnchorEl(null);
    };

    return (
        <div className='tau-option-header'>
            <div>
		<Button
		    className='tau-option-button'
		    size='small'
		    target='_blank'
		    href='https://github.com/ParaToolsInc'
		>
		    <span className='tau-logo-button'></span> 
		</Button>

                <Button 
                    className='tau-option-button' 
                    size='small' 
                    onClick={() => { 
                        props.model.execute('from kernel import TauKernel\nTauKernel.refresh()'); 
                        props.onSetProject(null); 
                    }}
                >
                    { props.output ? 'Refresh' : 'Connect to Tau' }
                </Button>

                { props.output ? (
                    <Button 
                      className='tau-option-button' 
		      id='new-button'
                      size='small'
                      aria-controls="simple-menu" 
                      aria-haspopup="true" 
                      onClick={handleClick}
                    >
                        New
                    </Button>
                ) : (
                    <React.Fragment></React.Fragment>
                )}
            </div>

            <div className='tau-option-right-side'>
                { props.project ? (
                    <p className='tau-option-current'>
                        <b>Current project: </b>
                        {props.project}
                    </p>
                ) : (
                    <React.Fragment></React.Fragment>
                )}

                { props.output ? (
	 	    <Button
		        className='tau-option-button'
		        size='small'
		        onClick={() => {makeColorDialog();}}
		    >
		        <span className='tau-color-button'></span> 
		    </Button>
	        ) : (
		    <React.Fragment></React.Fragment>
	        )}
            </div>

	    <Menu
              id="simple-menu"
              anchorEl={anchorEl}
              keepMounted
              open={Boolean(anchorEl)}
              onClose={handleClose}
              className='tau-option-menu'
            >
                <MenuItem onClick={() => {handleClose(); makeNewDialog(props.model, 'Project', props.project);}}>New Project</MenuItem>
                { props.project ? (
                    <div>
                        <MenuItem onClick={() => {handleClose(); makeNewDialog(props.model, 'Target', props.project);}}>New Target</MenuItem>
                        <MenuItem onClick={() => {handleClose(); makeNewDialog(props.model, 'Application', props.project);}}>New Application</MenuItem>
                        <MenuItem onClick={() => {handleClose(); makeNewDialog(props.model, 'Measurement', props.project);}}>New Measurement</MenuItem>
                        <MenuItem onClick={() => {handleClose(); makeNewDialog(props.model, 'Experiment', props.project);}}>New Experiment</MenuItem>
                    </div>
                ) : (
		    <div></div>
                )}
            </Menu>
        </div>
    )
};
