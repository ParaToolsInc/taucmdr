package edu.uoregon.tau.perfexplorer.common;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

/**
 * This class is the main RMI object which contains the performance analysis
 * results from either correlation or some other type of background
 * analysis.
 *
 * <P>CVS $Id: RMIVarianceData.java,v 1.4 2009/02/27 00:45:09 khuck Exp $</P>
 * @author khuck
 * @version 0.1
 * @since   0.1
 *
 */
public class RMIVarianceData implements Serializable {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1579815095104774043L;
	private List<String> eventNames = null;
	private List<String> valueNames = null;
	private List<double[]> values = null;
	
	public RMIVarianceData() {
		this.eventNames = new ArrayList<String>();
		this.valueNames = new ArrayList<String>();
		this.values = new ArrayList<double[]>();
	}
	
	public void addEventName(String name) {
		this.eventNames.add(name);
	}
	
	public void addValueName(String name) {
		this.valueNames.add(name);
	}

	public void addValues(double[] values) {
		this.values.add(values);
	}
	
	public String getEventName(int index) {
		return eventNames.get(index);
	}

	public String getValueName(int index) {
		return valueNames.get(index);
	}

	public double[] getValues(int index) {
		return values.get(index);
	}
	
	public int getEventCount() {
		return eventNames.size();
	}

	public int getValueCount() {
		return valueNames.size();
	}

	/**
	 * @return
	 */
	public Object[] getColumnNames() {
		Object[] tmpArray = valueNames.toArray();
		return tmpArray;
	}

	/**
	 * @return
	 */
	public Object[][] getDataMatrix() {
		Object[][] matrix = new Object[eventNames.size()][valueNames.size() + 1];
		for (int i = 0 ; i < eventNames.size() ; i++) {
			matrix[i][0] = eventNames.get(i);
			double[] tmpValues = this.values.get(i);
			for (int j = 0 ; j < tmpValues.length ; j++) {
				matrix[i][j+1] = new Double(tmpValues[j]);
			}
		}
		return matrix;
	}
}
