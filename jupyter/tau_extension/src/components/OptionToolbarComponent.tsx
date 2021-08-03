import React, { useState } from 'react';

import { makeDialog } from './Dialogs';

import Button from "@material-ui/core/Button";
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

export const OptionToolbar = (props: any) => {

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
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

                <Menu
                  id="simple-menu"
                  anchorEl={anchorEl}
                  keepMounted
                  open={Boolean(anchorEl)}
                  onClose={handleClose}
                  className='tau-option-menu'
                >
                    <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Project', props.project);}}>New Project</MenuItem>
                    { props.project ? (
                        <div>
                            <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Target', props.project);}}>New Target</MenuItem>
                            <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Application', props.project);}}>New Application</MenuItem>
                            <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Measurement', props.project);}}>New Measurement</MenuItem>
                            <MenuItem onClick={() => {handleClose(); makeDialog(props.model, 'Experiment', props.project);}}>New Experiment</MenuItem>
                        </div>
                    ) : (
			<React.Fragment></React.Fragment>
                    )}
                </Menu>
            </div>

            <div>
                { props.project ? (
                    <p className='tau-option-current'>
                        <b>Current project: </b>
                        {props.project}
                    </p>
                ) : (
                    <React.Fragment></React.Fragment>
                )}
            </div>
        </div>
    )
};
