package edu.uoregon.tau.paraprof;

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Image;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.awt.image.BufferedImage;
import java.awt.image.ImageObserver;
import java.awt.print.PageFormat;
import java.awt.print.Printable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Observable;
import java.util.Observer;
import java.util.Stack;

import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JPanel;
import javax.swing.JSplitPane;

import com.graphbuilder.math.VarMap;

import edu.uoregon.tau.common.MetaDataMap.MetaDataKey;
import edu.uoregon.tau.common.MetaDataMap.MetaDataValue;
import edu.uoregon.tau.paraprof.ThreeDeeGeneralPlotUtils.CoordMap;
import edu.uoregon.tau.paraprof.enums.SortType;
import edu.uoregon.tau.paraprof.enums.UserEventValueType;
import edu.uoregon.tau.paraprof.enums.ValueType;
import edu.uoregon.tau.paraprof.enums.VisType;
import edu.uoregon.tau.paraprof.graph.Layout;
import edu.uoregon.tau.paraprof.graph.Vertex;
import edu.uoregon.tau.paraprof.graph.Vertex.BackEdge;
import edu.uoregon.tau.paraprof.interfaces.ParaProfWindow;
import edu.uoregon.tau.paraprof.interfaces.SortListener;
import edu.uoregon.tau.paraprof.interfaces.UnitListener;
import edu.uoregon.tau.perfdmf.CallPathUtilFuncs;
import edu.uoregon.tau.perfdmf.DataSource;
import edu.uoregon.tau.perfdmf.Function;
import edu.uoregon.tau.perfdmf.FunctionProfile;
import edu.uoregon.tau.perfdmf.Metric;
import edu.uoregon.tau.perfdmf.Thread;
import edu.uoregon.tau.perfdmf.UserEvent;
import edu.uoregon.tau.perfdmf.UserEventProfile;
import edu.uoregon.tau.perfdmf.UtilFncs;
import edu.uoregon.tau.vis.Axes;
import edu.uoregon.tau.vis.BarPlot;
import edu.uoregon.tau.vis.ColorScale;
import edu.uoregon.tau.vis.ExceptionHandler;
import edu.uoregon.tau.vis.Plot;
import edu.uoregon.tau.vis.ScatterPlot;
import edu.uoregon.tau.vis.TopoPlot;
import edu.uoregon.tau.vis.TriangleMeshPlot;
import edu.uoregon.tau.vis.Vec;
import edu.uoregon.tau.vis.VisCanvas;
import edu.uoregon.tau.vis.VisCanvasListener;
import edu.uoregon.tau.vis.VisRenderer;
import edu.uoregon.tau.vis.VisTools;
import edu.uoregon.tau.vis.XmasTree;
import edu.uoregon.tau.vis.XmasTree.Ornament;

public class ThreeDeeWindow extends JFrame implements ActionListener,
		KeyListener, Observer, Printable, ParaProfWindow, UnitListener,
		SortListener, VisCanvasListener, ThreeDeeImageProvider {

	/**
	 * 
	 */
	private static final long serialVersionUID = 5841023264079846115L;

	private final int defaultToScatter = 4000;

	private VisCanvas visCanvas;
	private VisRenderer visRenderer = new VisRenderer();

	private Plot plot;
	private Axes axes;
	private ColorScale colorScale = new ColorScale();

	private ParaProfTrial ppTrial;
	private JMenu optionsMenu = null;
	private DataSorter dataSorter;

	private ThreeDeeControlPanel controlPanel;
	private ThreeDeeSettings settings = new ThreeDeeSettings();
	private ThreeDeeSettings oldSettings;
	private javax.swing.Timer fpsTimer;

	private JSplitPane jSplitPane;

	private TriangleMeshPlot triangleMeshPlot;
	private BarPlot barPlot;
	private ScatterPlot scatterPlot;
	private TopoPlot topoPlot;
	private Axes fullDataPlotAxes;
	private Axes scatterPlotAxes;

	private List<String> functionNames;
	private List<String> threadNames;
	private List<Function> functions;
	private List<Thread> threads;
	// private List<Function> selectedFunctions = new ArrayList<Function>();

	private int units = ParaProf.preferences.getUnits();

	float minHeightValue = 0;
	float minColorValue = 0;
	float maxHeightValue = 0;
	float maxColorValue = 0;

	float minScatterValues[];
	float maxScatterValues[];

	public ThreeDeeWindow(ParaProfTrial ppTrial, Component invoker) {
		// set the VisTools exception handler
		VisTools.setSwingExceptionHandler(new ExceptionHandler() {
			public void handleException(Exception e) {
				ParaProfUtils.handleException(e);
			}
		});
		this.ppTrial = ppTrial;

		settings.setColorMetric(ppTrial.getDefaultMetric());
		settings.setHeightMetric(ppTrial.getDefaultMetric());
		settings.setScatterMetric(ppTrial.getDefaultMetric(), 0);
		settings.setScatterMetric(ppTrial.getDefaultMetric(), 1);
		settings.setScatterMetric(ppTrial.getDefaultMetric(), 2);
		settings.setScatterMetric(ppTrial.getDefaultMetric(), 3);
		settings.setTopoMetric(ppTrial.getDefaultMetric(), 0);
		settings.setTopoMetric(ppTrial.getDefaultMetric(), 1);
		settings.setTopoMetric(ppTrial.getDefaultMetric(), 2);
		settings.setTopoMetric(ppTrial.getDefaultMetric(), 3);

		List<String> tList = ppTrial.getTopologyArray();

		String topoc = null;
		if (tList != null && tList.size() > 0)
			topoc = tList.get(0);
		if (topoc != null)
			settings.setTopoCart(topoc);
		else
			settings.setTopoCart("Custom");

		dataSorter = new DataSorter(ppTrial);
		dataSorter.setSortType(SortType.NAME);

		this.setTitle("TAU: ParaProf: 3D Visualizer: "
				+ ppTrial.getTrialIdentifier(ParaProf.preferences
						.getShowPathTitleInReverse()));
		ParaProfUtils.setFrameIcon(this);

		// Add some window listener code
		addWindowListener(new java.awt.event.WindowAdapter() {
			public void windowClosing(java.awt.event.WindowEvent evt) {
				thisWindowClosing(evt);
			}
		});

		setupMenus();

		ThreeDeeWindow.this.validate();

		// IA64 workaround
		String os = System.getProperty("os.name").toLowerCase();
		String cpu = System.getProperty("os.arch").toLowerCase();
		if (os.startsWith("linux") && cpu.equals("ia64")) {
			this.setVisible(true);
		}

		DataSource dataSource = ppTrial.getDataSource();
		int numThreads = dataSource.getNumThreads();

		// initialize the scatterplot functions to the 4 most varying functions
		// we just get the first four stddev functions
		DataSorter dataSorter = new DataSorter(ppTrial);
		dataSorter.setSelectedMetric(ppTrial.getDefaultMetric());
		dataSorter.setDescendingOrder(true);
		List<PPFunctionProfile> stdDevList = dataSorter
				.getFunctionProfiles(dataSource.getStdDevData());
		int count = 0;
		for (Iterator<PPFunctionProfile> it = stdDevList.iterator(); it
				.hasNext() && count < 4;) {
			PPFunctionProfile fp = it.next();
			if (!fp.isCallPathObject()) {
				if (count == 0) {
					settings.setTopoFunction(fp.getFunction(), 3);
				}
				settings.setScatterFunction(fp.getFunction(), count);
				count++;
			}
		}

		// if the number of threads is above this threshold, we default to the
		// scatterplot
		if (numThreads > defaultToScatter) {
			settings.setVisType(VisType.SCATTER_PLOT);
		}

		generate3dModel(true, settings);

		oldSettings = (ThreeDeeSettings) settings.clone();

		visRenderer.addShape(plot);
		visRenderer.addShape(colorScale);
		visRenderer.setVisCanvasListener(this);
		visCanvas = new VisCanvas(visRenderer);

		visCanvas.addKeyListener(this);

		JPanel panel = new JPanel() {
			/**
			 * 
			 */
			private static final long serialVersionUID = 7050395373997175369L;

			public Dimension getMinimumSize() {
				return new Dimension(10, 10);
			}
		};

		panel.addKeyListener(this);
		panel.setLayout(new GridBagLayout());
		GridBagConstraints gbc = new GridBagConstraints();

		gbc.fill = GridBagConstraints.BOTH;
		gbc.anchor = GridBagConstraints.WEST;
		gbc.weightx = 1.0;
		gbc.weighty = 1.0;
		gbc.gridx = 0;
		gbc.gridy = 0;
		gbc.gridwidth = 1;
		gbc.gridheight = 1;
		panel.add(visCanvas.getActualCanvas(), gbc);
		panel.setPreferredSize(new Dimension(5, 5));

		controlPanel = new ThreeDeeControlPanel(this, settings, ppTrial,
				visRenderer);
		jSplitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, panel,
				controlPanel);
		jSplitPane.setContinuousLayout(true);
		jSplitPane.setResizeWeight(1.0);
		jSplitPane.setOneTouchExpandable(true);
		jSplitPane.addKeyListener(this);
		this.getContentPane().add(jSplitPane);

		setSize(ParaProfUtils.checkSize(new Dimension(1000, 750)));
		this.setLocation(WindowPlacer.getNewLocation(this, invoker));

		// //Grab the screen size.
		// Toolkit tk = Toolkit.getDefaultToolkit();
		// Dimension screenDimension = tk.getScreenSize();
		// int screenHeight = screenDimension.height;
		// int screenWidth = screenDimension.width;

		// IA64 workaround
		if (os.startsWith("linux") && cpu.equals("ia64")) {
			this.validate();
		}
		this.setVisible(true);

		if (System.getProperty("vis.fps") != null) {
			fpsTimer = new javax.swing.Timer(1000, this);
			fpsTimer.start();
		}

		ParaProf.incrementNumWindows();
		ppTrial.addObserver(this);

	}

	public static ThreeDeeWindow createThreeDeeWindow(ParaProfTrial ppTrial,
			JFrame parentFrame) {
		return new ThreeDeeWindow(ppTrial, parentFrame);
	}

	private void generateScatterPlot(boolean autoSize, ThreeDeeSettings settings) {

		Function[] scatterFunctions = settings.getScatterFunctions();

		ValueType[] scatterValueTypes = settings.getScatterValueTypes();
		Metric[] scatterMetricIDs = settings.getScatterMetrics();

		DataSource dataSource = ppTrial.getDataSource();
		int numThreads = dataSource.getNumThreads();

		float[][] values = new float[numThreads][4];

		int threadIndex = 0;

		minScatterValues = new float[4];
		maxScatterValues = new float[4];
		for (int f = 0; f < 4; f++) {
			minScatterValues[f] = Float.MAX_VALUE;
		}

		for (Iterator<Thread> it = ppTrial.getDataSource().getAllThreads()
				.iterator(); it.hasNext();) {
			Thread thread = it.next();
			
			//System.out.print(thread.getNodeID()+": ");
			
			for (int f = 0; f < scatterFunctions.length; f++) {
				if (scatterFunctions[f] != null) {
					FunctionProfile functionProfile = thread
							.getFunctionProfile(scatterFunctions[f]);

					if (functionProfile != null) {
						values[threadIndex][f] = (float) scatterValueTypes[f]
								.getValue(functionProfile, scatterMetricIDs[f],
										ppTrial.getSelectedSnapshot());
						
					}
					else{
						values[threadIndex][f]=0;
					}
						
						//System.out.print(values[threadIndex][f]+" -- ");
						maxScatterValues[f] = Math.max(maxScatterValues[f],
								values[threadIndex][f]);
						minScatterValues[f] = Math.min(minScatterValues[f],
								values[threadIndex][f]);
					}
					
				
			}
			//System.out.println();
			threadIndex++;
		}

		if (scatterPlotAxes == null) {
			scatterPlotAxes = new Axes();
		}

		setAxisStrings();

		axes = scatterPlotAxes;

		if (scatterPlot == null) {
			scatterPlot = new ScatterPlot();
			if (numThreads > defaultToScatter) {
				scatterPlot.setSphereSize(0);
			}
		}

		scatterPlot.setSize(15, 15, 15);
		scatterPlot.setAxes(axes);
		scatterPlot.setValues(values);
		scatterPlot.setColorScale(colorScale);
		plot = scatterPlot;
	}

	private float getColorValue(Thread thread) {

		float color = Float.NaN;

		if (settings.getDataType(3)==0) {
			Function topoFunction = settings.getTopoFunction(3);
			ValueType topoValueType = settings.getTopoValueType(3);
			Metric topoMetricID = settings.getTopoMetric(3);

			if (topoFunction != null) {
				FunctionProfile functionProfile = thread
						.getFunctionProfile(topoFunction);

				if (functionProfile != null) {
					color = (float) topoValueType.getValue(functionProfile,
							topoMetricID, ppTrial.getSelectedSnapshot());
				} else {
					return 0;
				}
			}
		} else if(settings.getDataType(3)==1){
			UserEvent ue = settings.getTopoAtomic(3);
			if (ue != null) {
				UserEventProfile uep = thread.getUserEventProfile(ue);
				if (uep != null) {
					UserEventValueType uevt = settings
							.getTopoUserEventValueType(3);
					if (uevt != null)
						color = (float) uevt.getValue(uep,
								ppTrial.getSelectedSnapshot());
				}
			}
		}else if(settings.getDataType(3)==2){
			MetaDataKey metaKey=settings.getTopoMetadata(3);//.toString();
			if(metaKey!=null){
				MetaDataValue mdVal=thread.getMetaData().get(metaKey);
				
				if(mdVal==null){
					mdVal=ppTrial.getDataSource().getMetaData().get(metaKey);
				}
				if(mdVal==null){
					//System.out.println(thread.getNodeID()+" null");	
					return 0;
				}
				//System.out.println(mdVal.toString());		
				
				float tmp=Float.NaN;
				String metaVal=mdVal.toString();
				try{
				tmp = Float.parseFloat(metaVal);
				}catch(NumberFormatException e){
					return tmp;
				}
				color=tmp;
			}
			//TODO: Handle non-numerical metadata?
		}

		return color;
	}

	private void generateGeneralPlot(boolean autoSize, ThreeDeeSettings settings) {

		minScatterValues = new float[4];
		maxScatterValues = new float[4];
		for (int f = 0; f < 4; f++) {
			minScatterValues[f] = Float.MAX_VALUE;
			maxScatterValues[f] = Float.MIN_VALUE;
		}

		DataSource dataSource = ppTrial.getDataSource();
		int numThreads = dataSource.getNumThreads();

		float[][] values = defaultTopology(numThreads);

		if (scatterPlotAxes == null) {
			scatterPlotAxes = new Axes();
		}

		setAxisStrings();

		axes = scatterPlotAxes;

		if (topoPlot == null) {
			topoPlot = new TopoPlot();
			if (numThreads > defaultToScatter) {
				topoPlot.setSphereSize(0);
			}
		}

		// scatterPlot.setSize(15, 15, 15);
		// //scatterPlot.clearValues();
		// scatterPlot.setMinMax(minScatterValues[3], maxScatterValues[3]);
		topoPlot.setMinMax(minScatterValues, maxScatterValues);

		if (restrict) {
			topoPlot.setSize(15, 15, 15);
		} else {
			topoPlot.setSize(tsizes[0], tsizes[1], tsizes[2]);
		}
		topoPlot.setIsTopo(true);
		topoPlot.setAxes(axes);
		topoPlot.setTopoVis(settings.getTopoVisAxes());
		topoPlot.setValues(values);
		topoPlot.setColorScale(colorScale);
		topoPlot.setVisRange(settings.getMinTopoRange(),
				settings.getMaxTopoRange());
		plot = topoPlot;

		// settings.setMinTopoShown(scatterPlot.getMinShown());
		// settings.setMaxTopoShown(scatterPlot.getMaxShown());
	}

	int[] tsizes = { 0, 0, 0 };
	boolean restrict = false;
	Thread[][][] threadTopo=null;

	private float[][] defaultTopology(int numThreads) {
		float[][] values = new float[numThreads][4];
		
		//Thread[][][] threadTopo=null;

		String prefix = settings.getTopoCart();

		if (prefix == null || prefix.equals("Custom")) {
			int xdim = settings.getCustomTopoAxis(0);
			int ydim = settings.getCustomTopoAxis(1);
			int zdim = settings.getCustomTopoAxis(2);

			if (xdim <= 0) {
				xdim = 1;
			}
			if (ydim <= 0) {
				ydim = 1;
			}
			if (ydim <= 0) {
				ydim = 1;
			}
			if (xdim * ydim * zdim < numThreads) {
				zdim = (int) Math.ceil((double) numThreads / (double) xdim
						/ (double) ydim);
			}

			int threadIndex = 0;

			for (Iterator<Thread> it = ppTrial.getDataSource().getAllThreads()
					.iterator(); it.hasNext();) {
				Thread thread = it.next();

				for (int f = 0; f < 4; f++) {
					if (f == 0) {
						values[threadIndex][f] = threadIndex % xdim;
					}
					if (f == 1) {
						values[threadIndex][f] = (threadIndex / xdim) % ydim;// ycor;
					} else if (f == 2) {
						values[threadIndex][f] = (threadIndex / xdim / ydim)
								% zdim;
					} else if (f == 3) {

						float color = getColorValue(thread);
						if (color != Float.NaN) {
							values[threadIndex][3] = color;
							maxScatterValues[3] = Math.max(maxScatterValues[3],
									values[threadIndex][3]);
							minScatterValues[3] = Math.min(minScatterValues[3],
									values[threadIndex][3]);
						}

					}
					maxScatterValues[f] = Math.max(maxScatterValues[f],
							values[threadIndex][f]);
					minScatterValues[f] = Math.min(minScatterValues[f],
							values[threadIndex][f]);
				}
				threadIndex++;
			}
			for (int i = 0; i < 3; i++){
				tsizes[i] = (int) maxScatterValues[i];
			}

		} 
		
		else if (prefix.equals("Map")) {
			String fileLoc = settings.getTopoMapFile();
			if (fileLoc == null)
				return null;
			CoordMap map = ThreeDeeGeneralPlotUtils.parseMapFile(fileLoc);

			for (int i = 0; i < 3; i++) {
				maxScatterValues[i] = tsizes[i] = map.max[i];
				minScatterValues[i] = map.min[i];
			}
			// scatterPlot.setSize(tsizes[0],tsizes[1], tsizes[2]);

			// int minVis=settings.getMinTopoRange();
			// int maxVix=settings.getMaxTopoRange();

			int threadIndex = 0;
			for (Iterator<Thread> it = ppTrial.getDataSource().getAllThreads()
					.iterator(); it.hasNext();) {
				Thread thread = it.next();

				// String coord = thread.getMetaData().get(coord_key);
				// if(coord==null){
				// continue;
				// }
				// int[] coords = ThreeDeeGeneralPlotUtils.parseTuple(coord);

				values[threadIndex][0] = map.coords[threadIndex][0];// coords[0];
				values[threadIndex][1] = map.coords[threadIndex][1];
				values[threadIndex][2] = map.coords[threadIndex][2];

				// Function topoFunction = settings.getTopoFunction(3);
				// ValueType topoValueType = settings.getTopoValueType(3);
				// Metric topoMetricID = settings.getTopoMetric(3);

				float color = getColorValue(thread);
				if (color != Float.NaN) {
					values[threadIndex][3] = color;
					maxScatterValues[3] = Math.max(maxScatterValues[3],
							values[threadIndex][3]);
					minScatterValues[3] = Math.min(minScatterValues[3],
							values[threadIndex][3]);
				}

				// if (topoFunction != null) {
				// FunctionProfile functionProfile =
				// thread.getFunctionProfile(topoFunction);
				//
				// if (functionProfile != null) {
				//
				//
				// values[threadIndex][3] = (float)
				// topoValueType.getValue(functionProfile,
				// topoMetricID,ppTrial.getSelectedSnapshot());
				// maxScatterValues[3] = Math.max(maxScatterValues[3],
				// values[threadIndex][3]);
				// minScatterValues[3] = Math.min(minScatterValues[3],
				// values[threadIndex][3]);
				// }
				// }

				threadIndex++;
			}

		} else if (settings.isCustomTopo()) {
			String fileLoc = settings.getTopoDefFile();// "/home/wspear/Code/JavaMath/test.txt";
			// List<String> names = getCustomTopoNames(fileLoc);
			Map<String, String> expressions = ThreeDeeGeneralPlotUtils
					.getExpressions(fileLoc, prefix);
			// Function topoFunction = settings.getTopoFunction(3);
			// ValueType topoValueType = settings.getTopoValueType(3);
			// Metric topoMetricID = settings.getTopoMetric(3);

			// int[] custTopoDims = null;
			int xdim = settings.getCustomTopoAxis(0);
			int ydim = settings.getCustomTopoAxis(1);
			int zdim = settings.getCustomTopoAxis(2);

			// int xdim = topoValues[0];
			if (xdim <= 0) {
				xdim = 1;
			}
			// /int ydim = topoValues[1];
			if (ydim <= 0) {
				ydim = 1;
			}
			// int zdim = topoValues[2];
			if (ydim <= 0) {
				ydim = 1;
			}
			if (xdim * ydim * zdim < numThreads) {
				zdim = (int) Math.ceil((double) numThreads / (double) xdim
						/ (double) ydim);
			}

			float[] varMins = { 0, 0, 0, 0 };
			float[] varMaxs = { 0, 0, 0, 0 };

			boolean start = true;
			for (Iterator<Thread> it = ppTrial.getDataSource().getAllThreads()
					.iterator(); it.hasNext();) {
				Thread thread = it.next();
				for (int i = 0; i < 4; i++) {
					Function f = settings.getScatterFunctions()[i];
					if (f != null) {
						FunctionProfile fp = thread.getFunctionProfile(f);
						if (fp != null) {
							Metric m = settings.getScatterMetrics()[i];
							ValueType vt = settings.getScatterValueTypes()[i];
							if (start) {
								varMins[i] = (float) vt.getValue(fp, m,
										ppTrial.getSelectedSnapshot());
								varMaxs[i] = (float) vt.getValue(fp, m,
										ppTrial.getSelectedSnapshot());
								start = false;
							} else {
								varMins[i] = Math.min(
										varMins[i],
										(float) vt.getValue(fp, m,
												ppTrial.getSelectedSnapshot()));
								varMaxs[i] = Math.max(
										varMaxs[i],
										(float) vt.getValue(fp, m,
												ppTrial.getSelectedSnapshot()));
							}
						}
					}
				}
			}

			float[] varMeans = { 0, 0, 0, 0 };
			Thread mt = ppTrial.getMeanThread();
			for (int i = 0; i < 4; i++) {
				Function f = settings.getScatterFunctions()[i];
				if (f != null) {
					FunctionProfile fp = mt.getFunctionProfile(f);
					if (fp != null) {
						Metric m = settings.getScatterMetrics()[i];
						ValueType vt = settings.getScatterValueTypes()[i];

						varMeans[i] = (float) vt.getValue(fp, m,
								ppTrial.getSelectedSnapshot());

					}
				}
			}

			int rankIndex = 0;
			int dataIndex = 0;
			VarMap vm = null;
			int pointsPerRank = -1;
			int loopPoints = 1;
			for (Iterator<Thread> it = ppTrial.getDataSource().getAllThreads()
					.iterator(); it.hasNext();) {
				Thread thread = it.next();

				// int sqrt = (int) Math.sqrt(numThreads);
				// FunctionProfile functionProfile =
				// thread.getFunctionProfile(topoFunction);
				// float colorValue=0;//Float.NaN;//TODO: Support treating this
				// as a non-value or 0.
				// if(functionProfile!=null){
				// colorValue = (float) topoValueType.getValue(functionProfile,
				// topoMetricID,ppTrial.getSelectedSnapshot());
				// }

				float[] topoVals = { 0, 0, 0, 0 };
				for (int i = 0; i < 4; i++) {
					if (settings.getDataType(i)==0) {
						Function f = settings.getTopoFunction(i);
						if (f != null) {
							FunctionProfile fp = thread.getFunctionProfile(f);
							if (fp != null) {
								Metric m = settings.getTopoMetric(i);
								ValueType vt = settings.getTopoValueType(i);
								topoVals[i] = (float) vt.getValue(fp, m,
										ppTrial.getSelectedSnapshot());
							}
						}
					} else if(settings.getDataType(i)==1) {
						UserEvent ue = settings.getTopoAtomic(i);
						if (ue != null) {
							UserEventProfile uep = thread
									.getUserEventProfile(ue);
							if (uep != null) {
								UserEventValueType uevt = settings
										.getTopoUserEventValueType(i);
								if (uevt != null)
									topoVals[i] = (float) uevt.getValue(uep,
											ppTrial.getSelectedSnapshot());
							}
						}
					}
					else if(settings.getDataType(i)==2) {
						MetaDataKey metaKey=settings.getTopoMetadata(i);
						if(metaKey!=null){
							String metaVal=thread.getMetaData().get(metaKey).toString();
							float tmp=Float.NaN;
							try{
							tmp = Float.parseFloat(metaVal);
							}catch(NumberFormatException e){
								
							}
							topoVals[i]=tmp;
						}
						//TODO: Metadata support
					}
				}
				// float[] ueVal={0,0,0,0};
				// for(int i=0;i<4;i++){
				// UserEvent ue = settings.getTopoAtomic(i);
				// if(ue!=null){
				// UserEventProfile uep = thread.getUserEventProfile(ue);
				// if(uep!=null)
				// {
				// UserEventValueType uevt =
				// settings.getTopoUserEventValueType(i);
				// if(uevt!=null)
				// ueVal[i] = (float)uevt.getValue(uep,
				// ppTrial.getSelectedSnapshot());
				// }
				// }
				// }

				vm = ThreeDeeGeneralPlotUtils.getEvaluation(
						rankIndex,
						numThreads,
						thread,
						ppTrial,
						topoVals, varMins, varMaxs, varMeans, settings
								.getCustomTopoAxes(), expressions);

				if (pointsPerRank == -1) {
					pointsPerRank = ThreeDeeGeneralPlotUtils
							.getPointsPerRank(vm);
					if (pointsPerRank > 1) {
						values = new float[numThreads * pointsPerRank][4];
						loopPoints = pointsPerRank;
					}
				}
				boolean multiColor = ThreeDeeGeneralPlotUtils.checkSet(vm,
						"color0");
				double[][] cords = ThreeDeeGeneralPlotUtils.getRankCoordinate(
						vm, pointsPerRank, multiColor);
				for (int ppn = 0; ppn < loopPoints; ppn++) {
					for (int f = 0; f < 4; f++) {

						// double
						// theta=2f*Math.PI/sqrt*((float)(threadIndex%sqrt));
						// double phi = Math.PI/sqrt*((threadIndex/sqrt));
						// if(f==0){
						// values[threadIndex][f] = (float) ((float)
						// Math.cos(theta)*Math.sin(phi)*100);//threadIndex%xdim;
						// }
						// if(f==1)
						// {
						// values[threadIndex][f] = (float) ((float)
						// Math.sin(theta)*Math.sin(phi)*100);//(threadIndex/xdim)%ydim;//
						// ycor;
						// }
						// else if(f==2)
						// {
						// values[threadIndex][f] = (float)
						// Math.cos(phi)*100;//0;//(threadIndex/xdim/ydim)%zdim;
						// }
						// if(f<3){
						values[dataIndex + ppn][f] = (float) cords[ppn][f];
						// }
						// else if(f==3)
						// {
						//
						// if (topoFunction != null) {
						//
						//
						// if (functionProfile != null) {
						// values[threadIndex][3] = colorValue;
						// maxScatterValues[3] = Math.max(maxScatterValues[3],
						// values[threadIndex][3]);
						// minScatterValues[3] = Math.min(minScatterValues[3],
						// values[threadIndex][3]);
						// }
						// }
						// }
						maxScatterValues[f] = Math.max(maxScatterValues[f],
								values[dataIndex + ppn][f]);
						minScatterValues[f] = Math.min(minScatterValues[f],
								values[dataIndex + ppn][f]);
					}
				}
				dataIndex += loopPoints;
				rankIndex++;
			}
			restrict = ThreeDeeGeneralPlotUtils.checkSet(vm, "restrictDim");
			for (int i = 0; i < 3; i++) {
				tsizes[i] = (int) maxScatterValues[i];
				// System.out.println(tsizes[i]);
			}

		} 

			else {
				
			String coord_key = prefix + " Coords";
			String size_key = prefix + " Size";
			
			
			boolean isBGQ=false;
			if(prefix.equals("BGQ")){
				coord_key="MPI Processor Name";
				isBGQ=true;
			}
			
			String tsize = ppTrial.getDataSource().getMetaData().get(size_key);
			if(tsize==null)
			{
				System.out.println("Topology sizes not defined");
				return values;
			}
				
			
			int[] tempsizes = ThreeDeeGeneralPlotUtils.parseTuple(tsize);
			
			int offset=5;
			if(tempsizes.length>3){
				
				calculateTSize(tempsizes,offset);
				if(tsizes[0]<0)
					return values;
			}
			else{
				tsizes = tempsizes;
			}
			
			threadTopo = new Thread[Math.max(1,tsizes[0])][Math.max(1,tsizes[1])][Math.max(1,tsizes[2])];
			
			for (int i = 0; i < 3; i++) {
				if(!isBGQ)
				maxScatterValues[i] = tsizes[i];
				minScatterValues[i] = 0;
			}


			int threadIndex = 0;
			int coreCoordinate=0;//Used to generate final core coordinate mapping;
			for (Iterator<Thread> it = ppTrial.getDataSource().getAllThreads()
					.iterator(); it.hasNext();) {
				Thread thread = it.next();

				String coord = thread.getMetaData().get(coord_key);
				if (coord == null) {
					continue;
				}
				
				
				int[] coords; 
				
				if(isBGQ){
					coords = ThreeDeeGeneralPlotUtils.parseMPIProcName(coord);
				}
				else{
					coords = ThreeDeeGeneralPlotUtils.parseTuple(coord);
				}
				if(coords.length<tempsizes.length){
					int[] tempcoords=new int[tempsizes.length];
					int i=0;
					for(i=0;i<coords.length;i++){
						tempcoords[i]=coords[i];
					}
					if(coreCoordinate==tempsizes[tempsizes.length-1])
					{
						coreCoordinate=0;
					}
					tempcoords[i]=coreCoordinate;
					coreCoordinate++;
					coords=tempcoords;
				}
				
				
				if(tempsizes.length==6&&isBGQ){
					
					values[threadIndex][0] = coords[4]*tempsizes[5]+coords[5]+offset*coords[4];
					values[threadIndex][1] = coords[0]*tempsizes[1]+coords[1]+offset*coords[0];
					values[threadIndex][2] = coords[2]*tempsizes[3]+coords[3]+offset*coords[2];
					
					for (int i = 0; i < 3; i++) {
						maxScatterValues[i] = Math.max(maxScatterValues[i], values[threadIndex][i]);
					}
					
					
				}
//				else if(tempsizes.length==5){
//					values[threadIndex][0]=coords[4]*offset;
//					values[threadIndex][1]=coords[0]*tempsizes[1]+coords[1]+offset*coords[0];;
//					values[threadIndex][2]=coords[2]*tempsizes[3]+coords[3]+offset*coords[2];
//				}else if (tempsizes.length==4){
//					values[threadIndex][0]=coords[3]*offset;
//					values[threadIndex][1]=coords[0]*tempsizes[1]+coords[1]+offset*coords[0];
//					values[threadIndex][2]=coords[2]*offset;
//				}
				
				else 
					if(tempsizes.length<=3){
					

					for (int i = 0; i < coords.length; i++) {
						
						
							values[threadIndex][i] = coords[i];
						
						
					}
					
				}
				else{
					//System.out.println("Dimension "+coords.length+" Unsupported");
				}
				
				int dex0=(int)values[threadIndex][0];
				int dex1=(int)values[threadIndex][1];
				int dex2=(int)values[threadIndex][2];
				threadTopo[dex0][dex1][dex2]=thread;

				
				float color = getColorValue(thread);
				if (color != Float.NaN) {
					values[threadIndex][3] = color;
					maxScatterValues[3] = Math.max(maxScatterValues[3],
							values[threadIndex][3]);
					minScatterValues[3] = Math.min(minScatterValues[3],
							values[threadIndex][3]);
				}

				threadIndex++;
			}//Values populator loop
			}

		return values;
	}
	
	private void calculateTSize(int[] tempSize, int offset){
		
//		for(int i=0;i<tempSize.length;i++){
//			tempSize[i]=tempSize[i]+1;
//		}
		
		if(tempSize.length==6){
			
			tsizes[0]=tempSize[4]*tempSize[5]+tempSize[4]*offset;
			tsizes[1]=tempSize[0]*tempSize[1]+tempSize[0]*offset;
			tsizes[2]=tempSize[2]*tempSize[3]+tempSize[2]*offset;
			
		}
		else
//		else if(tempSize.length==5){
//			tsizes[0]=tempSize[4]*offset;
//			tsizes[1]=tempSize[0]*tempSize[1]+tempSize[0]*offset;
//			tsizes[2]=tempSize[2]*tempSize[3]+tempSize[2]*offset;
//		}
//		else if(tempSize.length==4){
//			tsizes[0]=tempSize[3]*offset;
//			tsizes[1]=tempSize[0]*tempSize[1]+tempSize[0]*offset;
//			tsizes[2]=tempSize[2]*offset;
//		}
//		else 
			if(tempSize.length<=3)
			for(int i=0;i<3;i++){
				tsizes[i]=tempSize[i+3];
			}
		else{
			System.out.println("Dimension "+tempSize.length+" Unsupported");
			tsizes[0]=-1;
		}
	}

	// String[] expressions =
	// {"sqrt(maxRank)","2*pi()/rootRanks*mod(rank,rootRanks)","pi()/rootRanks*(rank/rootRanks)","cos(theta)*sin(phi)*100","sin(theta)*sin(phi)*100","cos(phi)*100"};
	// String[] ids = {"rootRanks","theta","phi","x","y","z"};

	// private float[][] customTopology(int numThreads){
	//
	// Function[] scatterFunctions = settings.getScatterFunctions();
	//
	// ValueType[] scatterValueTypes = settings.getScatterValueTypes();
	// Metric[] scatterMetricIDs = settings.getScatterMetrics();
	//
	// int[] topoValues = settings.getTopoValues();
	//
	//
	//
	// float[][] values = new float[numThreads][4];
	//
	// int threadIndex = 0;
	//
	// for (Iterator<Thread> it =
	// ppTrial.getDataSource().getAllThreads().iterator(); it.hasNext();) {
	// Thread thread = it.next();
	//
	// int xdim = topoValues[0];
	// if(xdim<=0){
	// xdim=1;
	// }
	// int ydim = topoValues[1];
	// if(ydim<=0){
	// ydim=1;
	// }
	// int zdim = topoValues[2];
	// if(ydim<=0){
	// ydim=1;
	// }
	// if(xdim*ydim*zdim<numThreads){
	// zdim=(int)Math.ceil((double)numThreads/(double)xdim/(double)ydim);
	// }
	//
	// for (int f = 0; f < 4; f++) {
	// if(f==0){
	// values[threadIndex][f] = threadIndex%xdim;
	// }
	// if(f==1)
	// {
	// values[threadIndex][f] = (threadIndex/xdim)%ydim;// ycor;
	// }
	// else if(f==2)
	// {
	// values[threadIndex][f] = (threadIndex/xdim/ydim)%zdim;
	// }
	// else if(f==3)
	// {
	//
	// if (scatterFunctions[f] != null) {
	// FunctionProfile functionProfile =
	// thread.getFunctionProfile(scatterFunctions[f]);
	//
	// if (functionProfile != null) {
	// values[threadIndex][f] = (float)
	// scatterValueTypes[f].getValue(functionProfile, scatterMetricIDs[f],
	// ppTrial.getSelectedSnapshot());
	// }
	// else
	// break;
	// }
	// else break;
	// }
	// maxScatterValues[f] = Math.max(maxScatterValues[f],
	// values[threadIndex][f]);
	// minScatterValues[f] = Math.min(minScatterValues[f],
	// values[threadIndex][f]);
	// }
	// threadIndex++;
	// }
	// return values;
	// }

	private List<List<Vertex>> createGraph(DataSource dataSource,
			ThreeDeeSettings settings) {
		List<BackEdge> backEdges;
		Map<FunctionProfile, Vertex> vertexMap;

		vertexMap = new HashMap<FunctionProfile, Vertex>();
		backEdges = new ArrayList<BackEdge>();

		Thread thread = settings.getSelectedThread();
		if (thread == null) {
			thread = dataSource.getMeanData();
		}

		CallPathUtilFuncs.buildThreadRelations(dataSource, thread);
		List<FunctionProfile> functionProfileList = thread
				.getFunctionProfiles();

		for (int i = 0; i < functionProfileList.size(); i++) {
			FunctionProfile fp = functionProfileList.get(i);
			if (fp == null) // skip it if this thread didn't call this function
				continue;

			if (!fp.isCallPathFunction()) { // skip callpath functions (we only
											// want the actual functions)

				Vertex v = new Vertex(fp, 1, 1);
				v.setColorRatio(1);
				vertexMap.put(fp, v);
			}
		}

		// now we follow the call paths and eliminate back edges
		Stack<FunctionProfile> toVisit = new Stack<FunctionProfile>();
		Stack<FunctionProfile> currentPath = new Stack<FunctionProfile>();

		for (int i = 0; i < functionProfileList.size(); i++) {
			FunctionProfile fp = functionProfileList.get(i);
			if (fp == null) // skip it if this thread didn't call this function
				continue;

			if (!fp.isCallPathFunction()) { // skip callpath functions (we only
											// want the actual functions)

				// get the vertex for this FunctionProfile
				Vertex root = vertexMap.get(fp);

				if (!root.getVisited()) {

					currentPath.add(fp);
					toVisit.add(null); // null in the toVisit stack marks the
										// end of a set of children (they must
										// get pushed into the stack prior to
										// the children)

					// add all the children to the toVisit list
					for (Iterator<FunctionProfile> it = fp.getChildProfiles(); it
							.hasNext();) {
						FunctionProfile childFp = it.next();
						toVisit.add(childFp);
					}

					while (!toVisit.empty()) {
						FunctionProfile childFp = toVisit.pop();

						if (childFp == null) {
							// this marks the end of a set of children, so pop
							// the current path
							// and move on to the next one in toVisit
							currentPath.pop();
							continue;
						}

						Vertex child = vertexMap.get(childFp);
						FunctionProfile parentFp = currentPath.peek();

						Vertex parent = vertexMap.get(parentFp);

						// run through the currentPath and see if childFp is in
						// it, if so, this is a backedge
						boolean back = false;
						for (Iterator<FunctionProfile> it = currentPath
								.iterator(); it.hasNext();) {
							if (it.next() == childFp) {
								back = true;
								break;
							}
						}

						if (back) {
							backEdges.add(new BackEdge(parent, child));
						} else {

							boolean found = false;
							for (int j = 0; j < parent.getChildren().size(); j++) {
								if (parent.getChildren().get(j) == child)
									found = true;
							}
							if (!found)
								parent.getChildren().add(child);

							found = false;
							for (int j = 0; j < child.getParents().size(); j++) {
								if (child.getParents().get(j) == parent)
									found = true;
							}
							if (!found)
								child.getParents().add(parent);

							if (child.getVisited() == false) {

								child.setVisited(true);

								currentPath.add(childFp);

								toVisit.add(null);
								for (Iterator<FunctionProfile> it = childFp
										.getChildProfiles(); it.hasNext();) {
									FunctionProfile grandChildFunction = it
											.next();

									toVisit.add(grandChildFunction);
								}
							}

						}
					}
				}
			}
		}
		// now we should have a DAG, now find the roots

		// Find Roots
		List<Vertex> roots = Layout.findRoots(vertexMap);

		// Assigning Levels
		for (int i = 0; i < functionProfileList.size(); i++) {
			FunctionProfile fp = functionProfileList.get(i);
			if (fp == null)
				continue;

			if (!fp.isCallPathFunction()) {
				Vertex vertex = vertexMap.get(fp);

				if (vertex.getLevel() == -1) {
					Layout.assignLevel(vertex);
				}
			}

		}

		// Insert Dummies
		for (int i = 0; i < functionProfileList.size(); i++) {
			FunctionProfile fp = functionProfileList.get(i);
			if (fp == null)
				continue;

			if (!fp.isCallPathFunction()) {
				Vertex vertex = vertexMap.get(fp);
				Layout.insertDummies(vertex);
			}

		}

		// fill level lists
		for (int i = 0; i < functionProfileList.size(); i++) {
			FunctionProfile fp = functionProfileList.get(i);
			if (fp == null)
				continue;

			if (!fp.isCallPathFunction()) {
				Vertex vertex = vertexMap.get(fp);
				vertex.setVisited(false);
			}

		}

		List<List<Vertex>> levels = new ArrayList<List<Vertex>>();

		// Fill Levels
		for (int i = 0; i < roots.size(); i++) {
			Vertex root = roots.get(i);
			Layout.fillLevels(root, levels, 0);
		}

		// Order Levels
		Layout.runSugiyama(levels);
		Layout.assignPositions(levels);
		return levels;
	}

	private List<List<Ornament>> decorateTree(List<List<Vertex>> graphLevels,
			DataSource dataSource, ThreeDeeSettings settings) {
		Map<Vertex, Ornament> omap = new HashMap<Vertex, Ornament>();
		List<List<Ornament>> treeLevels = new ArrayList<List<Ornament>>();

		Thread thread = settings.getSelectedThread();
		if (thread == null) {
			thread = dataSource.getMeanData();
		}

		for (int i = 0; i < graphLevels.size(); i++) {
			List<Vertex> level = graphLevels.get(i);
			List<Ornament> treeLevel = new ArrayList<Ornament>();
			int count = 0;

			for (int j = 0; j < level.size(); j++) {
				Vertex v = (Vertex) level.get(j);
				if (v.getUserObject() != null) {
					count++;
				}
			}

			// System.out.println("count = " + count + ", level.size() = " +
			// level.size());

			int c = 0;
			for (int j = 0; j < level.size(); j++) {
				Vertex v = (Vertex) level.get(j);

				if (v.getUserObject() != null) {
					FunctionProfile fp = (FunctionProfile) v.getUserObject();
					Ornament o = new Ornament(fp.getName(), v);
					float size = (float) (fp.getInclusive(0) / thread
							.getMaxInclusive(0, 0));
					float color = (float) (fp.getExclusive(0) / thread
							.getMaxExclusive(0, 0));
					// float color = (float) (fp.getInclusive(0) /
					// thread.getMaxInclusive(0, 0));
					// float size = (float) (fp.getExclusive(0) /
					// thread.getMaxExclusive(0, 0));
					o.setSize(size);
					o.setColor(color);
					v.setGraphObject(o);
					omap.put(v, o);
					o.setPosition((float) c++ / count);
					treeLevel.add(o);
				} else {
					// dummy node, don't make a graph cell
				}

			}
			treeLevels.add(treeLevel);
		}

		for (int i = 0; i < graphLevels.size(); i++) {
			List<Vertex> level = graphLevels.get(i);

			for (int j = 0; j < level.size(); j++) {
				Vertex v = (Vertex) level.get(j);

				if (v.getUserObject() != null) {
					Ornament a = (Ornament) v.getGraphObject();
					for (Iterator<Vertex> it = v.getChildren().iterator(); it
							.hasNext();) {
						Vertex child = it.next();
						Ornament b = (Ornament) child.getGraphObject();
						if (b != null && b.getUserObject() != null) {
							a.addChild(b);
						} else {
							// while (child.getGraphObject() == null) {
							// child = (Vertex) child.getChildren().get(0);
							// }
							// Ornament c = (Ornament) child.getGraphObject();
							// a.addChild(c);
						}
					}
				} else {
					// dummy node, don't make a graph cell
				}

			}
		}

		return treeLevels;
	}

	private void generateCallGraph(boolean autoSize, ThreeDeeSettings settings) {
		if (plot != null) {
			plot.cleanUp();
		}
		List<List<Vertex>> levels = createGraph(ppTrial.getDataSource(),
				settings);
		List<List<Ornament>> treeLevels = decorateTree(levels,
				ppTrial.getDataSource(), settings);
		XmasTree xmasTree = new XmasTree(treeLevels);
		xmasTree.setColorScale(colorScale);
		plot = xmasTree;
	}

	private void generate3dModel(boolean autoSize, ThreeDeeSettings settings) {

		visRenderer.setCameraMode(VisRenderer.CAMERA_PLOT);
		if (plot != null) {
			plot.cleanUp();
		}

		if (settings.getVisType() == VisType.SCATTER_PLOT) {
			generateScatterPlot(autoSize, settings);
			return;
		}

		if (settings.getVisType() == VisType.TOPO_PLOT) {
			generateGeneralPlot(autoSize, settings);
			return;
		}

		if (settings.getVisType() == VisType.CALLGRAPH) {
			generateCallGraph(autoSize, settings);
			visRenderer.setCameraMode(VisRenderer.CAMERA_STICK);
			return;
		}

		if (triangleMeshPlot == null && barPlot == null) {
			autoSize = true;
		}

		DataSource dataSource = ppTrial.getDataSource();

		int numThreads = dataSource.getNumThreads();
		int numFunctions = 0;

		// get the 'mean' thread's functions to sort by
		List<PPFunctionProfile> list = dataSorter.getFunctionProfiles(ppTrial
				.getDataSource().getMeanData());

		numFunctions = list.size();

		float[][] heightValues = new float[numFunctions][numThreads];
		float[][] colorValues = new float[numFunctions][numThreads];

		boolean addFunctionNames = false;
		if (functionNames == null) {
			functionNames = new ArrayList<String>();
			functions = new ArrayList<Function>();
			addFunctionNames = true;
		}

		if (threadNames == null) {
			threadNames = ppTrial.getThreadNames();
			threads = ppTrial.getThreads();
		}

		maxHeightValue = 0;
		maxColorValue = 0;
		minHeightValue = Float.MAX_VALUE;
		minColorValue = Float.MAX_VALUE;

		int funcIndex = 0;
		for (int i = 0; i < list.size(); i++) {
			PPFunctionProfile ppFunctionProfile = list.get(i);
			Function function = ppFunctionProfile.getFunction();

			// for (Iterator funcIter = ppTrial.getDataSource().getFunctions();
			// funcIter.hasNext();) {
			// Function function = (Function) funcIter.next();

			// if (!ppTrial.displayFunction(function)) {
			// continue;
			// }

			if (addFunctionNames) {
				functionNames.add(ParaProfUtils.getDisplayName(function));
				functions.add(function);
			}
			int threadIndex = 0;
			for (Iterator<Thread> it = ppTrial.getDataSource().getAllThreads()
					.iterator(); it.hasNext();) {
				Thread thread = it.next();
				FunctionProfile functionProfile = thread
						.getFunctionProfile(function);

				if (functionProfile != null) {
					heightValues[funcIndex][threadIndex] = (float) settings
							.getHeightValue().getValue(functionProfile,
									settings.getHeightMetric().getID(),
									ppTrial.getSelectedSnapshot());
					colorValues[funcIndex][threadIndex] = (float) settings
							.getColorValue().getValue(functionProfile,
									settings.getColorMetric().getID(),
									ppTrial.getSelectedSnapshot());

					maxHeightValue = Math.max(maxHeightValue,
							heightValues[funcIndex][threadIndex]);
					maxColorValue = Math.max(maxColorValue,
							colorValues[funcIndex][threadIndex]);
					minHeightValue = Math.min(minHeightValue,
							heightValues[funcIndex][threadIndex]);
					minColorValue = Math.min(minColorValue,
							colorValues[funcIndex][threadIndex]);
				}
				threadIndex++;
			}
			funcIndex++;
		}

		if (autoSize) {
			int plotWidth = 20;
			int plotDepth = 20;
			int plotHeight = 20;

			float ratio = (float) threadNames.size() / functionNames.size();

			if (ratio > 2)
				ratio = 2;
			if (ratio < 0.5f)
				ratio = 0.5f;

			if (ratio > 1.0f) {
				plotDepth = (int) (30 * (1 / ratio));
				plotWidth = 30;

			} else if (ratio < 1.0f) {
				plotDepth = 30;
				plotWidth = (int) (30 * (ratio));

			} else {
				plotWidth = 30;
				plotDepth = 30;
			}
			plotHeight = 6;

			settings.setSize(plotWidth, plotDepth, plotHeight);
			visRenderer.setAim(new Vec(settings.getPlotWidth() / 2, settings
					.getPlotDepth() / 2, 0));
			settings.setRegularAim(visRenderer.getAim());
		}

		if (fullDataPlotAxes == null) {
			fullDataPlotAxes = new Axes();
			fullDataPlotAxes.setHighlightColor(ppTrial.getColorChooser()
					.getHighlightColor());
		}

		setAxisStrings();

		axes = fullDataPlotAxes;

		// axes.setOrientation(settings.getAxisOrientation());

		if (settings.getVisType() == VisType.TRIANGLE_MESH_PLOT) {
			axes.setOnEdge(false);
			if (triangleMeshPlot == null) {
				triangleMeshPlot = new TriangleMeshPlot();
				triangleMeshPlot.initialize(axes, settings.getPlotWidth(),
						settings.getPlotDepth(), settings.getPlotHeight(),
						heightValues, colorValues, colorScale);
				plot = triangleMeshPlot;
			} else {
				triangleMeshPlot.setValues(settings.getPlotWidth(),
						settings.getPlotDepth(), settings.getPlotHeight(),
						heightValues, colorValues);
				plot = triangleMeshPlot;
			}
		} else {
			axes.setOnEdge(true);

			if (barPlot == null) {
				barPlot = new BarPlot(axes, colorScale);
			}
			barPlot.setValues(settings.getPlotWidth(), settings.getPlotDepth(),
					settings.getPlotHeight(), heightValues, colorValues);
			plot = barPlot;

		}
	}

	private void updateSettings(ThreeDeeSettings newSettings) {

		if (oldSettings.getAxisOrientation() != newSettings
				.getAxisOrientation()) {
			axes.setOrientation(newSettings.getAxisOrientation());
		}

		if (oldSettings.getVisType() != newSettings.getVisType()) {
			// I know this is the same as the thing below, but that will
			// probably change, I want this separate for now
			visRenderer.removeShape(plot);
			visRenderer.removeShape(colorScale);
			generate3dModel(false, newSettings);
			visRenderer.addShape(plot);
			visRenderer.addShape(colorScale);

			plot.setSelectedCol(newSettings.getSelections()[1]);
			plot.setSelectedRow(newSettings.getSelections()[0]);

			if (newSettings.getVisType() == VisType.SCATTER_PLOT
					|| newSettings.getVisType() == VisType.TOPO_PLOT) {
				visRenderer.setAim(settings.getScatterAim());
			} else if (newSettings.getVisType() == VisType.TRIANGLE_MESH_PLOT
					|| newSettings.getVisType() == VisType.BAR_PLOT) {
				visRenderer.setAim(settings.getRegularAim());
			}

		} else {

			if (newSettings.getVisType() == VisType.SCATTER_PLOT
					|| newSettings.getVisType() == VisType.TOPO_PLOT) {
				visRenderer.removeShape(plot);
				visRenderer.removeShape(colorScale);
				generate3dModel(false, newSettings);
				visRenderer.addShape(plot);
				visRenderer.addShape(colorScale);
			} else if (newSettings.getVisType() == VisType.TRIANGLE_MESH_PLOT
					|| newSettings.getVisType() == VisType.BAR_PLOT) {

				settings.setSize((int) plot.getWidth(), (int) plot.getDepth(),
						(int) plot.getHeight());

				if (oldSettings.getHeightMetric() != newSettings
						.getHeightMetric()
						|| oldSettings.getHeightValue() != newSettings
								.getHeightValue()
						|| oldSettings.getColorValue() != newSettings
								.getColorValue()
						|| oldSettings.getColorMetric() != newSettings
								.getColorMetric()) {
					generate3dModel(false, newSettings);
				} else {

					// plot.setSize(newSettings.getPlotWidth(),
					// newSettings.getPlotDepth(),
					// newSettings.getPlotHeight());
					// axes.setSize(newSettings.getPlotWidth(),
					// newSettings.getPlotDepth(),
					// newSettings.getPlotHeight());

					plot.setSelectedCol(newSettings.getSelections()[1]);
					plot.setSelectedRow(newSettings.getSelections()[0]);
				}
			} else if (newSettings.getVisType() == VisType.CALLGRAPH) {
				visRenderer.removeShape(plot);
				visRenderer.removeShape(colorScale);
				generate3dModel(false, newSettings);
				visRenderer.addShape(plot);
				visRenderer.addShape(colorScale);
			}
		}

		oldSettings = (ThreeDeeSettings) newSettings.clone();
	}

	public void redraw() {
		jSplitPane.revalidate();
		jSplitPane.validate();
		updateSettings(settings);
		visRenderer.redraw();
	}

	public void resetSplitPane() {
		// We try to get the JSplitPane to reset the divider since the
		// different plots have differing widths of controls
		jSplitPane.revalidate();
		jSplitPane.validate();
		jSplitPane.resetToPreferredSizes();
		updateSettings(settings);
		visRenderer.redraw();
	}

	// private void helperAddRadioMenuItem(String name, String command, boolean
	// on, ButtonGroup group, JMenu menu) {
	// JRadioButtonMenuItem item = new JRadioButtonMenuItem(name, on);
	// item.addActionListener(this);
	// item.setActionCommand(command);
	// group.add(item);
	// menu.add(item);
	// }

	private void setupMenus() {

		JMenuBar mainMenu = new JMenuBar();

		optionsMenu = new JMenu("Options");
		optionsMenu.getPopupMenu().setLightWeightPopupEnabled(false);

		JMenu unitsSubMenu = ParaProfUtils.createUnitsMenu(this, units, true);
		unitsSubMenu.getPopupMenu().setLightWeightPopupEnabled(false);
		optionsMenu.add(unitsSubMenu);

		JMenu sort = ParaProfUtils.createMetricSelectionMenu(ppTrial,
				"Sort by...", true, false, dataSorter, this, false);
		sort.getPopupMenu().setLightWeightPopupEnabled(false);
		optionsMenu.add(sort);

		// now add all the menus to the main menu

		JMenu fileMenu = ParaProfUtils.createFileMenu(this, this, this);
		// JMenu trialMenu = ParaProfUtils.createTrialMenu(ppTrial, this);
		JMenu windowsMenu = ParaProfUtils.createWindowsMenu(ppTrial, this);
		JMenu helpMenu = ParaProfUtils.createHelpMenu(this, this);

		fileMenu.getPopupMenu().setLightWeightPopupEnabled(false);
		// trialMenu.getPopupMenu().setLightWeightPopupEnabled(false);
		windowsMenu.getPopupMenu().setLightWeightPopupEnabled(false);
		helpMenu.getPopupMenu().setLightWeightPopupEnabled(false);

		mainMenu.add(fileMenu);
		mainMenu.add(optionsMenu);
		// mainMenu.add(trialMenu);
		mainMenu.add(windowsMenu);
		mainMenu.add(helpMenu);

		setJMenuBar(mainMenu);
	}

	public int getUnits() {
		return units;
	}

	public void update(Observable o, Object arg) {
		String tmpString = (String) arg;

		if (tmpString.equals("subWindowCloseEvent")) {
			closeThisWindow();
		} else if (tmpString.equals("prefEvent")) {

		} else if (tmpString.equals("colorEvent")) {

			if (fullDataPlotAxes != null) {
				fullDataPlotAxes.setHighlightColor(ppTrial.getColorChooser()
						.getHighlightColor());
				visRenderer.redraw();
			}
			//
			// for (Iterator funcIter = ppTrial.getDataSource().getFunctions();
			// funcIter.hasNext();) {
			// Function function = (Function) funcIter.next();
			// if (function == ppTrial.getHighlightedFunction()) {
			// int index = functions.indexOf(function);
			//
			// }
			// }

		} else if (tmpString.equals("dataEvent")) {
			sortLocalData();
		}

	}

	void thisWindowClosing(java.awt.event.WindowEvent e) {
		closeThisWindow();
	}

	public void closeThisWindow() {
		setVisible(false);
		ppTrial.deleteObserver(this);
		ParaProf.decrementNumWindows();

		if (plot != null) {
			plot.cleanUp();
		}

		if (visRenderer != null) {
			visRenderer.cleanUp();
		}
		// animator.stop();
		// jTimer.stop();
		// jTimer = null;
		visRenderer = null;
		plot = null;

		dispose();
		// System.gc();
	}

	private void sortLocalData() {
		functionNames = null;

		if (settings.getVisType() == VisType.BAR_PLOT
				|| settings.getVisType() == VisType.TRIANGLE_MESH_PLOT) {
			settings.setSize((int) plot.getWidth(), (int) plot.getDepth(),
					(int) plot.getHeight());
			settings.setRegularAim(visRenderer.getAim());
			settings.setRegularEye(visRenderer.getEye());
		} else if (settings.getVisType() == VisType.SCATTER_PLOT
				|| settings.getVisType() == VisType.TOPO_PLOT) {
			// settings.setSize((int) plot.getWidth(), (int) plot.getDepth(),
			// (int) plot.getHeight());
			settings.setScatterAim(visRenderer.getAim());
			settings.setScatterEye(visRenderer.getEye());
		}

		generate3dModel(false, settings);
		controlPanel.dataChanged();
	}

	public void help(boolean display) {
		// Show the ParaProf help window.
		ParaProf.getHelpWindow().clearText();
		if (display) {
			ParaProf.getHelpWindow().setVisible(true);
		}
		ParaProf.getHelpWindow().writeText("This is the 3D Window");
		ParaProf.getHelpWindow().writeText("");
		ParaProf.getHelpWindow()
				.writeText(
						"This window displays profile data in three dimensions through the Triangle Mesh Plot, the Bar Plot, and the ScatterPlot");
		ParaProf.getHelpWindow().writeText("");
		ParaProf.getHelpWindow()
				.writeText(
						"Change between the plots by selecting the desired type from the radio buttons in the upper right.");
		ParaProf.getHelpWindow().writeText("");
		ParaProf.getHelpWindow().writeText(
				"Experiment with the controls at the right.");
		ParaProf.getHelpWindow().writeText("");
	}

	private long lastCall = 0;

	public BufferedImage getImage() {
		return visRenderer.createScreenShot();
	}

	public int print(Graphics g, PageFormat pageFormat, int page) {
		try {
			if (page >= 1) {
				return NO_SUCH_PAGE;
			}

			ParaProfUtils.scaleForPrint(g, pageFormat, visCanvas.getWidth(),
					visCanvas.getHeight());

			BufferedImage screenShot = visRenderer.createScreenShot();

			ImageObserver imageObserver = new ImageObserver() {
				public boolean imageUpdate(Image image, int a, int b, int c,
						int d, int e) {
					return false;
				}
			};

			g.drawImage(screenShot, 0, 0, Color.black, imageObserver);

			// renderIt((Graphics2D) g, false, true, false);

			return Printable.PAGE_EXISTS;
		} catch (Exception e) {
			ParaProfUtils.handleException(e);
			return NO_SUCH_PAGE;
		}
	}

	public void actionPerformed(ActionEvent evt) {
		try {
			Object EventSrc = evt.getSource();

			if (EventSrc instanceof javax.swing.Timer) {
				// the timer has ticked, get progress and post
				if (visRenderer == null) { // if it's been closed, go away
					((javax.swing.Timer) EventSrc).stop();
					return;
				}

				long time = System.currentTimeMillis();

				int numFrames = visRenderer.getFramesRendered();
				if (numFrames != 0) {
					visRenderer.setFramesRendered(0);

					float fps = numFrames / ((time - lastCall) / (float) 1000);

					visRenderer.setFps(fps);

					System.out.println("FPS = " + fps);
					lastCall = time;
				}
				return;
			}

		} catch (Exception e) {
			ParaProfUtils.handleException(e);
		}
	}

	/**
	 * @return Returns the colorScale.
	 */
	public ColorScale getColorScale() {
		return colorScale;
	}

	/**
	 * @return Returns the plot.
	 */
	public Plot getPlot() {
		return plot;
	}

	/**
	 * @param plot
	 *            The plot to set.
	 */
	public void setPlot(Plot plot) {
		this.plot = plot;
	}

	public List<String> getFunctionNames() {
		return functionNames;
	}

	public List<String> getThreadNames() {
		return threadNames;
	}

	public String getFunctionName(int index) {
		if (functionNames == null) {
			return null;
		}
		return functionNames.get(index);
	}

	public String getThreadName(int index) {
		if (threadNames == null) {
			return null;
		}
		return threadNames.get(index);
	}

	public double getMaxHeightValue() {
		return maxHeightValue;
	}

	public double getMaxColorValue() {
		return maxColorValue;
	}

	public double getMinHeightValue() {
		return minHeightValue;
	}

	public double getMinColorValue() {
		return minColorValue;
	}

	public String getHeightUnitLabel() {
		ParaProfMetric ppMetric = (ParaProfMetric) settings.getHeightMetric();
		return getUnitsString(units, settings.getHeightValue(), ppMetric);
	}

	public String getColorUnitLabel() {
		ParaProfMetric ppMetric = (ParaProfMetric) settings.getColorMetric();
		return getUnitsString(units, settings.getColorValue(), ppMetric);
	}

	/**
	 * @return a value between 0 and 1 representing the selected height value in
	 *         the range [min to max]
	 */
	public float getSelectedHeightRatio() {
		if (threads == null || functionNames == null) {
			return -1;
		}

		if (settings.getSelections()[1] < 0 || settings.getSelections()[0] < 0) {
			return -1;
		}

		Thread thread = threads.get(settings.getSelections()[1]);
		Function function = functions.get(settings.getSelections()[0]);
		FunctionProfile fp = thread.getFunctionProfile(function);

		if (fp == null) {
			return -1;
		}

		// int units = this.units;
		ParaProfMetric ppMetric = (ParaProfMetric) settings.getHeightMetric();
		if (!ppMetric.isTimeMetric()
				|| !ValueType.isTimeUnits(settings.getHeightValue())) {
			units = 0;
		}

		double value = settings.getHeightValue().getValue(fp,
				settings.getHeightMetric().getID());
		return (float) (value / maxHeightValue);
	}

	/**
	 * @return a value between 0 and 1 representing the selected color value in
	 *         the range [min to max]
	 */
	public float getSelectedColorRatio() {
		if (threads == null || functionNames == null) {
			return -1;
		}

		if (settings.getSelections()[1] < 0 || settings.getSelections()[0] < 0) {
			return -1;
		}

		Thread thread = threads.get(settings.getSelections()[1]);
		Function function = functions.get(settings.getSelections()[0]);
		FunctionProfile fp = thread.getFunctionProfile(function);

		if (fp == null) {
			return -1;
		}

		// int units = this.units;
		ParaProfMetric ppMetric = (ParaProfMetric) settings.getColorMetric();
		if (!ppMetric.isTimeMetric()
				|| !ValueType.isTimeUnits(settings.getColorValue())) {
			units = 0;
		}

		double value = settings.getColorValue().getValue(fp,
				settings.getColorMetric().getID());
		return (float) (value / maxColorValue);
	}

	public String getSelectedHeightValue() {
		if (threads == null || functionNames == null) {
			return "";
		}

		if (settings.getSelections()[1] < 0 || settings.getSelections()[0] < 0) {
			return "";
		}

		Thread thread = threads.get(settings.getSelections()[1]);
		Function function = functions.get(settings.getSelections()[0]);
		FunctionProfile fp = thread.getFunctionProfile(function);

		if (fp == null) {
			return "no value";
		}

		int units = this.units;
		ParaProfMetric ppMetric = (ParaProfMetric) settings.getHeightMetric();
		if (!ppMetric.isTimeMetric()
				|| !ValueType.isTimeUnits(settings.getHeightValue())) {
			units = 0;
		}

		String retval = UtilFncs.getOutputString(
				units,
				settings.getHeightValue().getValue(fp,
						settings.getHeightMetric().getID()), 6,
				ppMetric.isTimeDenominator()).trim()
				+ getUnitsString(units, settings.getHeightValue(), ppMetric);
		return retval;
	}

	public String getSelectedColorValue() {
		if (threads == null || functionNames == null)
			return "";

		if (settings.getSelections()[1] < 0 || settings.getSelections()[0] < 0)
			return "";

		Thread thread = threads.get(settings.getSelections()[1]);

		Function function = functions.get(settings.getSelections()[0]);
		FunctionProfile fp = thread.getFunctionProfile(function);

		if (fp == null) {
			return "no value";
		}

		int units = this.units;
		ParaProfMetric ppMetric = (ParaProfMetric) settings.getColorMetric();
		if (!ppMetric.isTimeMetric()
				|| !ValueType.isTimeUnits(settings.getColorValue())) {
			units = 0;
		}

		return UtilFncs.getOutputString(
				units,
				settings.getColorValue().getValue(fp,
						settings.getColorMetric().getID()), 6,
				ppMetric.isTimeDenominator()).trim()
				+ getUnitsString(units, settings.getColorValue(), ppMetric);

		// return Double.toString(settings.getColorValue().getValue(fp,
		// settings.getColorMetricID()));

	}

	public String getSelectedMinTopoValue() {
		if (topoPlot == null)
			return "";
		return getSelectedTopoValue(topoPlot.getMinShown());
	}

	public String getSelectedMaxTopoValue() {
		if (topoPlot == null)
			return "";
		return getSelectedTopoValue(topoPlot.getMaxShown());
	}

	public String getStatMean() {
		if (topoPlot != null)
			return getSelectedTopoValue(topoPlot.getStatMean());
		else
			return getSelectedTopoValue(Float.NaN);
	}

	public String getStatMax() {
		if (topoPlot != null)
			return getSelectedTopoValue(topoPlot.getStatMax());
		else
			return getSelectedTopoValue(Float.NaN);
	}

	public String getStatMin() {
		if (topoPlot != null)
			return getSelectedTopoValue(topoPlot.getStatMin());
		else
			return getSelectedTopoValue(Float.NaN);
	}
	
	public String getSelectedThread(){
		int[] show = settings.getTopoVisAxes();
		if(this.threadTopo==null||show[0]<0||show[1]<0||show[2]<0)
			return "\n ";
		
		Thread sel = threadTopo[show[0]][show[1]][show[2]];
		if(sel==null)
			return "\n ";
		
		return "\nN,C,T:"+sel.getNodeID()+","+sel.getThreadID()+","+sel.getContextID();
		
	}

	private String getSelectedTopoValue(float val) {
		// if (threads == null || functionNames == null)
		// return "";

		// if (settings.getSelections()[1] < 0 || settings.getSelections()[0] <
		// 0)
		// return "";

		// Thread thread = threads.get(settings.getSelections()[1]);
		//
		// Function function = functions.get(settings.getSelections()[0]);
		// FunctionProfile fp = thread.getFunctionProfile(function);
		//
		// if (fp == null) {
		// return "no value";
		// }
		
		if(new Float(val).equals(new Float(Float.NaN)))
			return "Invalid Selection";

		int units = this.units;
		
		int dataType = settings.getDataType(3);
		
		if(dataType==0){
		
		ParaProfMetric ppMetric = (ParaProfMetric) settings.getTopoMetric(3);
		if (!ppMetric.isTimeMetric()
				|| !ValueType.isTimeUnits(settings.getTopoValueType(3))) {
			units = 0;
		}

		return UtilFncs.getOutputString(units, val, 6,
				ppMetric.isTimeDenominator()).trim()
				+ getUnitsString(units, settings.getTopoValueType(3), ppMetric);
		}
		else if(dataType==1){
			return val+" counts";
		}
		else if(dataType==2){
			//TODO: metadata support
			return val+" counts";
		}
		return val+" counts";
	}

	private String getUnitsString(int units, ValueType valueType,
			ParaProfMetric ppMetric) {
		return valueType.getSuffix(units, ppMetric);
	}

	// private void setSpatialAxisStrings(){
	//
	// Function[] scatterFunctions = settings.getScatterFunctions();
	// ValueType[] scatterValueTypes = settings.getScatterValueTypes();
	// Metric[] scatterMetricIDs = settings.getScatterMetrics();
	//
	// List<String> axisNames = new ArrayList<String>();
	//
	// axisNames.add("X");
	// axisNames.add("Y");
	// axisNames.add("Z");
	//
	// //for (int f = 0; f < scatterFunctions.length; f++) {
	// int f = 3;
	// if (scatterFunctions[f] != null) {
	// String toDisplay;
	//
	// toDisplay = ParaProfUtils.getDisplayName(scatterFunctions[f]);
	// if (toDisplay.length() > 30) {
	// toDisplay = toDisplay.substring(0, 30) + "...";
	// }
	//
	//
	// // e.g. "MPI_Recv()\n(Exclusive, Time)"
	// if (scatterValueTypes[f] == ValueType.NUMCALLS || scatterValueTypes[f] ==
	// ValueType.NUMSUBR) {
	// axisNames.add(toDisplay + "\n(" + scatterValueTypes[f].toString() + ")");
	// } else {
	// axisNames.add(toDisplay + "\n(" + scatterValueTypes[f].toString() + ", "
	// + scatterMetricIDs[f].getName()
	// + ")");
	// }
	// } else {
	// axisNames.add("none");
	// }
	// //}
	//
	// List<String>[] axisStrings = new List[4];
	//
	// for (int i = 0; i < 4; i++) {
	// if (minScatterValues[i] == Float.MAX_VALUE) {
	// minScatterValues[i] = 0;
	// }
	//
	// axisStrings[i] = new ArrayList<String>();
	// if(i<3){
	// axisStrings[i].add(minScatterValues[i]+"");
	// axisStrings[i].add(minScatterValues[i] + (maxScatterValues[i] -
	// minScatterValues[i]) * .25+"");
	// axisStrings[i].add(minScatterValues[i] + (maxScatterValues[i] -
	// minScatterValues[i]) * .50+"");
	// axisStrings[i].add(minScatterValues[i] + (maxScatterValues[i] -
	// minScatterValues[i]) * .75+"");
	// axisStrings[i].add(minScatterValues[i] + (maxScatterValues[i] -
	// minScatterValues[i]) +"");
	// }
	//
	//
	// if(i==3){
	// ParaProfMetric ppMetric = (ParaProfMetric) scatterMetricIDs[i];
	//
	// int units = scatterValueTypes[i].getUnits(this.units, ppMetric);
	//
	//
	// axisStrings[i].add(UtilFncs.getOutputString(units, minScatterValues[i],
	// 6, ppMetric.isTimeDenominator()).trim());
	// axisStrings[i].add(UtilFncs.getOutputString(units,
	// minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]) * .25,
	// 6, ppMetric.isTimeDenominator()).trim());
	// axisStrings[i].add(UtilFncs.getOutputString(units,
	// minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]) * .50,
	// 6, ppMetric.isTimeDenominator()).trim());
	// axisStrings[i].add(UtilFncs.getOutputString(units,
	// minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]) * .75,
	// 6, ppMetric.isTimeDenominator()).trim());
	// axisStrings[i].add(UtilFncs.getOutputString(units,
	// minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]), 6,
	// ppMetric.isTimeDenominator()).trim());
	// }
	// }
	//
	// ParaProfMetric ppMetric = (ParaProfMetric) scatterMetricIDs[3];
	// int units = scatterValueTypes[3].getUnits(this.units, ppMetric);
	//
	// colorScale.setStrings(UtilFncs.getOutputString(units,
	// minScatterValues[3], 6, ppMetric.isTimeDenominator()).trim(),
	// UtilFncs.getOutputString(units, maxScatterValues[3], 6,
	// ppMetric.isTimeDenominator()).trim(),
	// axisNames.get(3));
	//
	// scatterPlotAxes.setStrings(axisNames.get(0), axisNames.get(1),
	// axisNames.get(2),
	// axisStrings[0], axisStrings[1], axisStrings[2]);
	//
	//
	// }

	private void setTopoAxisStrings() {

		List<String> axisNames = new ArrayList<String>();
		axisNames.add("X");
		axisNames.add("Y");
		axisNames.add("Z");

		@SuppressWarnings("unchecked")
		List<String>[] axisStrings = new List[4];

		for (int i = 0; i < 3; i++) {
			if (minScatterValues[i] == Float.MAX_VALUE) {
				minScatterValues[i] = 0;
			}

			axisStrings[i] = new ArrayList<String>();
			axisStrings[i].add((int) minScatterValues[i] + "");
			axisStrings[i]
					.add((int) (minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]) * .25)
							+ "");
			axisStrings[i]
					.add((int) (minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]) * .50)
							+ "");
			axisStrings[i]
					.add((int) (minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]) * .75)
							+ "");
			axisStrings[i]
					.add((int) (minScatterValues[i] + (maxScatterValues[i] - minScatterValues[i]))
							+ "");
		}

		
		String colorName = "none";
		String low = "none";
		String high = "none";
		
		if (settings.getDataType(3)==0) {//If this is an interval value
			ParaProfMetric ppMetric = (ParaProfMetric) settings
					.getTopoMetric(3);
			int units = settings.getTopoValueType(3).getUnits(this.units,
					ppMetric);

			if (settings.getTopoFunction(3) != null) {
				String toDisplay;
				toDisplay = ParaProfUtils.getDisplayName(settings
						.getTopoFunction(3));
				if (toDisplay.length() > 30) {
					toDisplay = toDisplay.substring(0, 30) + "...";
				}

				// e.g. "MPI_Recv()\n(Exclusive, Time)"
				if (settings.getTopoValueType(3) == ValueType.NUMCALLS
						|| settings.getTopoValueType(3) == ValueType.NUMSUBR) {
					colorName = toDisplay + "\n("
							+ settings.getTopoValueType(3).toString() + ")";
				} else {
					colorName = toDisplay + "\n("
							+ settings.getTopoValueType(3).toString() + ", "
							+ settings.getTopoMetric(3).getName() + ")";
				}
				
				low = UtilFncs.getOutputString(units, minScatterValues[3], 6,
						ppMetric.isTimeDenominator()).trim();
				high = UtilFncs.getOutputString(units, maxScatterValues[3], 6,
						ppMetric.isTimeDenominator()).trim();
				
			} 
		} else if(settings.getDataType(3)==1){//if this is an atomic value
			UserEventValueType colorUEVT = settings.getTopoUserEventValueType(3);
			UserEvent colorAtom = settings.getTopoAtomic(3);
			if(colorAtom!=null){
				String toDisplay = colorAtom.getName();
				if (toDisplay.length() > 30) {
					toDisplay = toDisplay.substring(0, 30) + "...";
				}
				colorName = toDisplay + "\n("
						+ colorUEVT.toString()+ ")";
				low = Float.toString(minScatterValues[3]);
				high = Float.toString(maxScatterValues[3]);
			}
		}
		else if(settings.getDataType(3)==2){			
			MetaDataKey metaKey=settings.getTopoMetadata(3);
		if(metaKey!=null){
			String toDisplay = metaKey.toString();
			if (toDisplay.length() > 30) {
				toDisplay = toDisplay.substring(0, 30) + "...";
			}
			colorName = toDisplay ;//+ "\n("
					//+ colorUEVT.toString()+ ")";
			low = Float.toString(minScatterValues[3]);
			high = Float.toString(maxScatterValues[3]);
		}
			//TODO: Metadata Support
		}

		colorScale.setStrings(low,	high, colorName);

		scatterPlotAxes.setStrings(axisNames.get(0), axisNames.get(1),
				axisNames.get(2), axisStrings[0], axisStrings[1],
				axisStrings[2]);
	}

	@SuppressWarnings("unchecked")
	private void setAxisStrings() {
		if (settings.getVisType() == VisType.TOPO_PLOT) {
			setTopoAxisStrings();
		} else if (settings.getVisType() == VisType.SCATTER_PLOT) {

			Function[] scatterFunctions = settings.getScatterFunctions();
			ValueType[] scatterValueTypes = settings.getScatterValueTypes();
			Metric[] scatterMetricIDs = settings.getScatterMetrics();

			List<String> axisNames = new ArrayList<String>();
			for (int f = 0; f < scatterFunctions.length; f++) {
				if (scatterFunctions[f] != null) {
					String toDisplay;
					if (f == 3) {
						toDisplay = ParaProfUtils
								.getDisplayName(scatterFunctions[f]);
						if (toDisplay.length() > 30) {
							toDisplay = toDisplay.substring(0, 30) + "...";
						}
					} else {
						toDisplay = scatterFunctions[f].getName();
					}
					// e.g. "MPI_Recv()\n(Exclusive, Time)"
					if (scatterValueTypes[f] == ValueType.NUMCALLS
							|| scatterValueTypes[f] == ValueType.NUMSUBR) {
						axisNames.add(toDisplay + "\n("
								+ scatterValueTypes[f].toString() + ")");
					} else {
						axisNames.add(toDisplay + "\n("
								+ scatterValueTypes[f].toString() + ", "
								+ scatterMetricIDs[f].getName() + ")");
					}
				} else {
					axisNames.add("none");
				}
			}

			List<String>[] axisStrings = new List[4];

			for (int i = 0; i < 4; i++) {
				if (minScatterValues[i] == Float.MAX_VALUE) {
					minScatterValues[i] = 0;
				}

				ParaProfMetric ppMetric = (ParaProfMetric) scatterMetricIDs[i];

				int units = scatterValueTypes[i].getUnits(this.units, ppMetric);

				axisStrings[i] = new ArrayList<String>();
				axisStrings[i].add(UtilFncs.getOutputString(units,
						minScatterValues[i], 6, ppMetric.isTimeDenominator())
						.trim());
				axisStrings[i].add(UtilFncs.getOutputString(
						units,
						minScatterValues[i]
								+ (maxScatterValues[i] - minScatterValues[i])
								* .25, 6, ppMetric.isTimeDenominator()).trim());
				axisStrings[i].add(UtilFncs.getOutputString(
						units,
						minScatterValues[i]
								+ (maxScatterValues[i] - minScatterValues[i])
								* .50, 6, ppMetric.isTimeDenominator()).trim());
				axisStrings[i].add(UtilFncs.getOutputString(
						units,
						minScatterValues[i]
								+ (maxScatterValues[i] - minScatterValues[i])
								* .75, 6, ppMetric.isTimeDenominator()).trim());
				axisStrings[i].add(UtilFncs.getOutputString(
						units,
						minScatterValues[i]
								+ (maxScatterValues[i] - minScatterValues[i]),
						6, ppMetric.isTimeDenominator()).trim());
			}

			ParaProfMetric ppMetric = (ParaProfMetric) scatterMetricIDs[3];
			int units = scatterValueTypes[3].getUnits(this.units, ppMetric);

			colorScale.setStrings(
					UtilFncs.getOutputString(units, minScatterValues[3], 6,
							ppMetric.isTimeDenominator()).trim(),
					UtilFncs.getOutputString(units, maxScatterValues[3], 6,
							ppMetric.isTimeDenominator()).trim(), axisNames
							.get(3));

			scatterPlotAxes.setStrings(axisNames.get(0), axisNames.get(1),
					axisNames.get(2), axisStrings[0], axisStrings[1],
					axisStrings[2]);

		} else {

			List<String> zStrings = new ArrayList<String>();
			zStrings.add("0");

			int units;

			ParaProfMetric ppMetric = (ParaProfMetric) settings
					.getHeightMetric();
			units = settings.getHeightValue().getUnits(this.units, ppMetric);

			zStrings.add(UtilFncs.getOutputString(units, maxHeightValue * 0.25,
					6, ppMetric.isTimeDenominator()).trim());
			zStrings.add(UtilFncs.getOutputString(units, maxHeightValue * 0.50,
					6, ppMetric.isTimeDenominator()).trim());
			zStrings.add(UtilFncs.getOutputString(units, maxHeightValue * 0.75,
					6, ppMetric.isTimeDenominator()).trim());
			zStrings.add(UtilFncs.getOutputString(units, maxHeightValue, 6,
					ppMetric.isTimeDenominator()).trim());

			String zAxisLabel = settings.getHeightValue().getSuffix(units,
					ppMetric);

			ppMetric = (ParaProfMetric) settings.getColorMetric();
			units = settings.getColorValue().getUnits(this.units, ppMetric);

			String colorAxisLabel = settings.getColorValue().getSuffix(units,
					ppMetric);

			colorScale.setStrings(
					"0",
					UtilFncs.getOutputString(units, maxColorValue, 6,
							ppMetric.isTimeDenominator()).trim(),
					colorAxisLabel);

			// String zAxisLabel = settings.getHeightValue().toString() + ", " +
			// ppTrial.getMetricName(settings.getHeightMetricID());
			// String zAxisLabel = "";

			String threadLabel = "Thread";
			if (ppTrial.getDataSource().getExecutionType() == DataSource.EXEC_TYPE_MPI) {
				threadLabel = "MPI Rank";
			}

			if (ppTrial.getDataSource().getExecutionType() == DataSource.EXEC_TYPE_HYBRID) {
				threadLabel = "MPI Rank, Thread";
			}

			fullDataPlotAxes.setStrings(threadLabel, "Function", zAxisLabel,
					threadNames, functionNames, zStrings);
		}
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see java.awt.event.KeyListener#keyPressed(java.awt.event.KeyEvent)
	 */
	public void keyPressed(KeyEvent e) {

	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see java.awt.event.KeyListener#keyReleased(java.awt.event.KeyEvent)
	 */
	public void keyReleased(KeyEvent e) {
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see java.awt.event.KeyListener#keyTyped(java.awt.event.KeyEvent)
	 */
	public void keyTyped(KeyEvent e) {
		try {
			// zoom in and out on +/-
			if (e.getKeyChar() == '+') {
				visRenderer.zoomIn();
			} else if (e.getKeyChar() == '-') {
				visRenderer.zoomOut();
			}
		} catch (Exception exp) {
			ParaProfUtils.handleException(exp);
		}

	}

	public void setUnits(int units) {
		this.units = units;
		setAxisStrings();
		controlPanel.dataChanged();
		visRenderer.redraw();
	}

	public void resort() {
		sortLocalData();
	}

	public JFrame getFrame() {
		return this;
	}

	public void createNewCanvas() {
		visCanvas = new VisCanvas(visRenderer);

		visCanvas.addKeyListener(this);

		JPanel panel = new JPanel() {
			/**
			  * 
			  */
			private static final long serialVersionUID = 2151986610100360208L;

			public Dimension getMinimumSize() {
				return new Dimension(10, 10);
			}
		};

		panel.addKeyListener(this);
		panel.setLayout(new GridBagLayout());
		GridBagConstraints gbc = new GridBagConstraints();

		gbc.fill = GridBagConstraints.BOTH;
		gbc.anchor = GridBagConstraints.WEST;
		gbc.weightx = 1.0;
		gbc.weighty = 1.0;
		gbc.gridx = 0;
		gbc.gridy = 0;
		gbc.gridwidth = 1;
		gbc.gridheight = 1;
		panel.add(visCanvas.getActualCanvas(), gbc);
		panel.setPreferredSize(new Dimension(5, 5));

		jSplitPane.setLeftComponent(panel);
	}

	public Component getComponent() {
		return this;
	}

}
