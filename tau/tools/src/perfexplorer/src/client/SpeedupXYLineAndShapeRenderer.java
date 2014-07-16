package edu.uoregon.tau.perfexplorer.client;

import java.awt.Color;
import java.awt.Paint;

import org.jfree.chart.renderer.xy.XYLineAndShapeRenderer;

public class SpeedupXYLineAndShapeRenderer extends XYLineAndShapeRenderer {
	/**
	 * 
	 */
	private static final long serialVersionUID = 4962881172454711849L;
	private int numRows = 0;

	public SpeedupXYLineAndShapeRenderer (int numRows) {
		super();
		this.numRows = numRows;
	}

	public java.awt.Paint getSeriesPaint(int series) {
		if (series == numRows)
			return Color.black;
		else
			//return super.getSeriesPaint(series);
        	return GoodColors.colors[series%GoodColors.numcolors];
	}

	/*
	 * These overrides cause lines to be drawn after shapes so the normal/ideal
	 * line will be visible on top.
	 * 
	 * @see org.jfree.chart.renderer.xy.XYLineAndShapeRenderer#isLinePass(int)
	 */
	protected boolean isLinePass(int pass) {
		return pass == 1;
	}
	protected boolean isItemPass(int pass) {
		return pass == 0;
	}

}
