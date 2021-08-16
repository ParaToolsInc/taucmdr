import React from 'react';
import ReactDOM from 'react-dom';

import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

import { GithubPicker } from 'react-color';

class ColorDialogBody extends Widget {
    constructor(domElement: HTMLElement) {
	super({node : domElement});
    }
};

export const makeColorDialog = () => {

    let root = document.documentElement;
    const handleColorChange = (colorPicked: any) => {

	let r = colorPicked.rgb.r;
	let g = colorPicked.rgb.g;
	let b = colorPicked.rgb.b;
	let a = Math.ceil(colorPicked.rgb.a * 100);
	let rgba = 'rgb(' + r + " " + g + " " + b + ' / ' + a + '%)';
	root.style.setProperty('--tau-table-color', rgba);
    };

    let colors = ['#eb14147a', '#eb14bc7a', '#4014eb7a', '#14b8eb7a', '#14eb757a', '#7aeb147a', '#ebdb147a', '#eb78147a', 
	          '#eb141442', '#eb14bc42', '#4014eb42', '#14b8eb42', '#14eb7542', '#7aeb1442', '#ebdb1442', '#eb781442'];
    
    let body = document.createElement('div');
    ReactDOM.render(<GithubPicker colors={colors} triangle='hide' onChangeComplete={ handleColorChange }/>, body);

    const dialog = new Dialog({
	title: `Color Change`,
	body: new ColorDialogBody(body), 
	buttons: [
	    Dialog.cancelButton({ label: 'Revert' }),
	    Dialog.okButton({ label: 'Okay' }),
	]
    });

    return dialog.launch().then(result => {
	if (result.button.label == 'Revert') {
	    root.style.setProperty('--tau-table-color', '#E7EAEB');
	}
	dialog.dispose();
    });
};

