package edu.uoregon.tau.paraprof;

import edu.uoregon.tau.common.MetaDataMap.MetaDataKey;
import edu.uoregon.tau.paraprof.enums.UserEventValueType;
import edu.uoregon.tau.paraprof.enums.ValueType;
import edu.uoregon.tau.paraprof.enums.VisType;
import edu.uoregon.tau.perfdmf.Function;
import edu.uoregon.tau.perfdmf.Metric;
import edu.uoregon.tau.perfdmf.Thread;
import edu.uoregon.tau.perfdmf.UserEvent;
import edu.uoregon.tau.vis.Vec;
import edu.uoregon.tau.vis.Axes.Orientation;

/**
 * Represents the settings of the 3d window/control panels
 * This class is not really that useful since the shapes (plots) themselves
 * do most of the controlling.  The original idea was that this could be
 * cloned such that the user could continue to drag a slider, so if the visualization
 * was slow, it wouldn't do a redraw 5 times inbetween, you would just get the 
 * last setting.  Unfortunately, all the JOGL stuff is forced onto the AWT-EventQueue
 * thread, so my plan got nixed.
 *    
 * TODO : ...
 *
 * <P>CVS $Id: ThreeDeeSettings.java,v 1.3 2009/09/10 00:13:49 amorris Exp $</P>
 * @author	Alan Morris
 * @version	$Revision: 1.3 $
 */
public class ThreeDeeSettings implements Cloneable {

    private float plotWidth, plotHeight, plotDepth;

    private Metric heightMetric, colorMetric;
    private ValueType colorValue = ValueType.EXCLUSIVE, heightValue = ValueType.EXCLUSIVE;
    private VisType visType = VisType.TRIANGLE_MESH_PLOT;
    //private VisType visType = VisType.BAR_PLOT;

    private Orientation axisOrientation = Orientation.NW;
    private boolean axesEnabled = true;

    private Metric[] scatterMetrics = { null, null, null, null };
    private ValueType[] scatterValueTypes = { ValueType.EXCLUSIVE, ValueType.EXCLUSIVE, ValueType.EXCLUSIVE, ValueType.EXCLUSIVE };
    private Function[] scatterFunctions = new Function[4];
    
    
    //TOPOLOGY SETTINGS
    
    //private int[] topoRanges = new int[2];
    private int minTopoRange=0;
    private int maxTopoRange=100;
    
    private int[] topoAxesVisible={-1,-1,-1};
    public int getTopoVisAxis(int dex){
    	return topoAxesVisible[dex];
    }
    public void setTopoVisAxis(int axis,int dex){
    	topoAxesVisible[dex]=axis;
    }
    
    public int[] getTopoVisAxes(){
    	return topoAxesVisible;
    }
    
    private int[] customTopoAxes={-1,-1,-1};
    public int getCustomTopoAxis(int dex){
    	return customTopoAxes[dex];
    }
    public void setCustomTopoAxis(int axis,int dex){
    	customTopoAxes[dex]=axis;
    }
    
    public int[] getCustomTopoAxes(){
    	return customTopoAxes;
    }
    
    /**Index of selected atomic event data type**/
    public int[] atomicETDex={0,0,0,0};
    
    /**Index of selected interval event data type**/
    public int[] intervalETDex={0,0,0,0};
    
    
    private Metric[] topoMetric= new Metric[4];
    private ValueType[] topoValueType = {ValueType.EXCLUSIVE,ValueType.EXCLUSIVE,ValueType.EXCLUSIVE,ValueType.EXCLUSIVE};
    private Function[] topoFunction = new Function[4];
    private String topoCart = null;

    public Metric getTopoMetric(int i) {
		return topoMetric[i];
	}

	public void setTopoMetric(Metric topoMetric,int i) {
		this.topoMetric[i] = topoMetric;
	}

	public ValueType getTopoValueType(int i) {
		return topoValueType[i];
	}

	public void setTopoValueType(ValueType topoValueType, int i) {
		this.topoValueType[i] = topoValueType;
	}

	public String getTopoCart() {
		return topoCart;
	}

	public void setTopoCart(String topoCart) {
		this.topoCart = topoCart;
	}
	
	private String topoDefFile=null;

	public String getTopoDefFile() {
		return topoDefFile;
	}
	public void setTopoDefFile(String topoDefFile) {
		this.topoDefFile = topoDefFile;
	}
	
	
	private String topoMapFile=null;

	public String getTopoMapFile() {
		return topoMapFile;
	}
	public void setTopoMapFile(String topoMapFile) {
		this.topoMapFile = topoMapFile;
	}
	
	private boolean customTopo=false;
	

	public boolean isCustomTopo() {
		return customTopo;
	}
	public void setCustomTopo(boolean customTopo) {
		this.customTopo = customTopo;
	}

//  public int[] getTopoRanges(){
//  return topoRanges;
//}
//public void setTopoRanges(int value, int index) {
//  this.topoRanges[index] = value;
//}

private UserEvent[] topoUserEvent=new UserEvent[4];
public UserEvent getTopoAtomic(int i){
	return topoUserEvent[i];
}
public void setTopoAtomic(UserEvent ue, int i){
	topoUserEvent[i]=ue;
}

private MetaDataKey[] topoMetadata=new MetaDataKey[4];
public MetaDataKey getTopoMetadata(int i){
	return topoMetadata[i];
}
public void setTopoMetadata(MetaDataKey ue, int i){
	topoMetadata[i]=ue;
}


private int[] dataType ={0,0,0,0};//0=timer/counter,1=atomic, 2=metadata
public int getDataType(int i){
	return dataType[i];
}

/**
 * 
 * @param b 0=timer/counter,1=atomic, 2=metadata
 * @param i index of the selector being changed
 */
public void setDataType(int b, int i)
{
	dataType[i]=b;
}

private UserEventValueType[] topoUserEventValueType = {UserEventValueType.MAX,UserEventValueType.MAX,UserEventValueType.MAX,UserEventValueType.MAX};
public UserEventValueType getTopoUserEventValueType(int i){
	return topoUserEventValueType[i];
}
public void setTopoUserEventValueType(UserEventValueType uevt, int i){
	topoUserEventValueType[i] = uevt;
}

public Function getTopoFunction(int i){
	return topoFunction[i];
}
public void setTopoFunction(Function f, int i){
	topoFunction[i]=f;
}
public int getMinTopoRange() {
	return minTopoRange;
}

public void setMinTopoRange(int minTopoRange) {
	this.minTopoRange = minTopoRange;
}

public int getMaxTopoRange() {
	return maxTopoRange;
}

public void setMaxTopoRange(int maxTopoRange) {
	this.maxTopoRange = maxTopoRange;
}

	
//    
//    private int minTopoValue=0;
//    private int maxTopoValue=0;
    
//    private float minTopoShown=0;
//    private float maxTopoShown=0;
//    
//    
//    public float getMinTopoShown() {
//		return minTopoShown;
//	}
//
//	public void setMinTopoShown(float minTopoShown) {
//		this.minTopoShown = minTopoShown;
//	}
//
//	public float getMaxTopoShown() {
//		return maxTopoShown;
//	}
//
//	public void setMaxTopoShown(float maxTopoShown) {
//		this.maxTopoShown = maxTopoShown;
//	}

//	public int getMinTopoValue() {
//		return minTopoValue;
//	}
//
//	public void setMinTopoValue(int minTopoValue) {
//		this.minTopoValue = minTopoValue;
//	}
//
//	public int getMaxTopoValue() {
//		return maxTopoValue;
//	}
//
//	public void setMaxTopoValue(int maxTopoValue) {
//		this.maxTopoValue = maxTopoValue;
//	}

	
//END OF TOPO

	private Thread selectedThread;

    // the function and thread selected by the two scrollbars
    private int[] selections = { -1, 0 };

    private Vec scatterAim = new Vec(7.5f, 7.5f, 7.5f), scatterEye;
    private Vec regularAim, regularEye;

    /**
     * @return Returns the visType.
     */
    public VisType getVisType() {
        return visType;
    }

    /**
     * @param visType The visType to set.
     */
    public void setVisType(VisType visType) {
        this.visType = visType;
    }

    /**
     * @return Returns the colorValue.
     */
    public ValueType getColorValue() {
        return colorValue;
    }

    /**
     * @param colorValue The colorValue to set.
     */
    public void setColorValue(ValueType colorValue) {
        this.colorValue = colorValue;
    }

    /**
     * @return Returns the heightValue.
     */
    public ValueType getHeightValue() {
        return heightValue;
    }

    /**
     * @param heightValue The heightValue to set.
     */
    public void setHeightValue(ValueType heightValue) {
        this.heightValue = heightValue;
    }

    public void setSize(float plotWidth, float plotDepth, float plotHeight) {
        this.plotWidth = plotWidth;
        this.plotDepth = plotDepth;
        this.plotHeight = plotHeight;

    }

    public float getPlotHeight() {
        return plotHeight;
    }

    public float getPlotDepth() {
        return plotDepth;
    }

    public float getPlotWidth() {
        return plotWidth;
    }

    public void setHeightMetric(Metric metric) {
        this.heightMetric = metric;
    }

    public void setColorMetric(Metric metric) {
        this.colorMetric = metric;
    }

    public Metric getHeightMetric() {
        return this.heightMetric;
    }

    public Metric getColorMetric() {
        return this.colorMetric;
    }

    public Object clone() {
        ThreeDeeSettings newSettings = new ThreeDeeSettings();

        newSettings.plotDepth = this.plotDepth;
        newSettings.plotHeight = this.plotHeight;
        newSettings.plotWidth = this.plotWidth;
        newSettings.heightMetric = this.heightMetric;
        newSettings.colorMetric = this.colorMetric;
        newSettings.colorValue = this.colorValue;
        newSettings.heightValue = this.heightValue;

        newSettings.visType = this.visType;
        newSettings.axisOrientation = this.axisOrientation;
        newSettings.axesEnabled = this.axesEnabled;

        newSettings.scatterMetrics = (Metric[]) this.scatterMetrics.clone();
        newSettings.scatterValueTypes = (ValueType[]) this.scatterValueTypes.clone();
        newSettings.scatterFunctions = (Function[]) this.scatterFunctions.clone();
        //newSettings.topoRanges = (int[]) this.topoRanges.clone();
        newSettings.minTopoRange=this.minTopoRange;
        newSettings.maxTopoRange=this.maxTopoRange;
        
//        newSettings.minTopoValue=this.minTopoValue;
//        newSettings.maxTopoValue=this.maxTopoValue;

        newSettings.topoMetric= this.topoMetric;
        newSettings.topoCart=this.topoCart;
        newSettings.topoValueType=this.topoValueType;
        
        newSettings.regularAim = this.regularAim;
        newSettings.regularEye = this.regularEye;

        newSettings.scatterAim = this.scatterAim;
        newSettings.scatterEye = this.scatterEye;

        newSettings.selections = (int[]) this.selections.clone();
        newSettings.topoAxesVisible=(int[])this.topoAxesVisible.clone();

        return newSettings;
    }
    
    

    //    public Plot getPlot() {
    //        return plot;
    //    }

    //    public Axes getAxes() {
    //        return axes;
    //    }
    /**
     * @return Returns the axisOrientation.
     */
    public Orientation getAxisOrientation() {
        return axisOrientation;
    }

    /**
     * @param axisOrientation The axisOrientation to set.
     */
    public void setAxisOrientation(Orientation axisOrientation) {
        this.axisOrientation = axisOrientation;
    }

    public boolean isAxesEnabled() {
        return axesEnabled;
    }

    public void setAxesEnabled(boolean axesEnabled) {
        this.axesEnabled = axesEnabled;
    }



    
    public Function[] getScatterFunctions() {
        return scatterFunctions;
    }

    public void setScatterFunction(Function function, int index) {
        this.scatterFunctions[index] = function;
    }

    public Metric[] getScatterMetrics() {
        return scatterMetrics;
    }

    public void setScatterMetric(Metric scatterMetric, int index) {
        this.scatterMetrics[index] = scatterMetric;
    }

    public ValueType[] getScatterValueTypes() {
        return scatterValueTypes;
    }

    public void setScatterValueType(ValueType scatterValueType, int index) {
        this.scatterValueTypes[index] = scatterValueType;
    }

    public Vec getRegularAim() {
        return regularAim;
    }

    public void setRegularAim(Vec regularAim) {
        this.regularAim = regularAim;
    }

    public Vec getRegularEye() {
        return regularEye;
    }

    public void setRegularEye(Vec regularEye) {
        this.regularEye = regularEye;
    }

    public Vec getScatterAim() {
        return scatterAim;
    }

    public void setScatterAim(Vec scatterAim) {
        this.scatterAim = scatterAim;
    }

    public Vec getScatterEye() {
        return scatterEye;
    }

    public void setScatterEye(Vec scatterEye) {
        this.scatterEye = scatterEye;
    }

    public int[] getSelections() {
        return this.selections;
    }

    public void setSelection(int index, int value) {
        this.selections[index] = value;
    }

    public Thread getSelectedThread() {
        return selectedThread;
    }

    public void setSelectedThread(Thread selectedThread) {
        this.selectedThread = selectedThread;
    }

}
