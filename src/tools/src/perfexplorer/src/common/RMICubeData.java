package edu.uoregon.tau.perfexplorer.common;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

/**
 * This object contains the data necessary to generate an OpenGL 3D cube of
 * data.  This data is usually correlation data.  It can reasonably have up 
 * to 4 dimensions (x,y,z,color).
 *
 * <P>CVS $Id: RMICubeData.java,v 1.5 2009/02/27 00:45:09 khuck Exp $</P>
 * @author khuck
 * @version 0.1
 * @since   0.1
 *
 */
public class RMICubeData implements Serializable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 57014019656871136L;

	int dimensions = 0;

	String[] names = null;
	List<float[]> values = null;

	/**
	 * Constructor.
	 * 
	 * @param dimensions
	 */
	public RMICubeData (int dimensions) {
		this.names = new String[dimensions];
		this.values = new ArrayList<float[]>();
	}

	/**
	 * Set the name for this dimension.
	 * 
	 * @param dimension
	 * @param name
	 */
	public void setName (int dimension, String name) {
		this.names[dimension] = name;
	}

	/**
	 * Set the names.
	 * 
	 * @param names
	 */
	public void setNames (String[] names) {
		this.names = names;
	}

	/**
	 * Add a set of values for one point.
	 * 
	 * @param values
	 */
	public void addValues(float[] values) {
		this.values.add(values);
	}

	/**
	 * Get the set of values for one point.
	 * 
	 * @param index
	 * @return
	 */
	public float[] getValues(int index) { 
		return values.get(index); 
	}

	/**
	 * Get all points.
	 * 
	 * @return
	 */
	public float[][] getValues() {
		float v[][] = new float[values.size()][this.dimensions];
		for (int i = 0 ; i < values.size() ; i++) {
			v[i] = values.get(i);
		}
		return v;
	}

	/**
	 * Get the names for the dimensions.
	 * 
	 * @param dimension
	 * @return the names
	 */
	public String getNames(int dimension) { 
		return names[dimension]; 
	}

	/**
	 * Get the full list of names
	 * @return the list of names
	 */
	public String[] getNames() { 
		return names; 
	}

}
