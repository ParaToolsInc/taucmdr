package edu.uoregon.tau.perfexplorer.client;

import java.awt.Component;
import java.awt.Container;
import java.awt.Frame;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.FileNotFoundException;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.ListIterator;

import javax.swing.ImageIcon;
import javax.swing.JComponent;
import javax.swing.JFileChooser;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JTree;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;

import org.jfree.data.general.SeriesException;

import edu.uoregon.tau.common.Utility;
import edu.uoregon.tau.common.VectorExport;
import edu.uoregon.tau.perfdmf.Application;
import edu.uoregon.tau.perfdmf.DatabaseAPI;
import edu.uoregon.tau.perfdmf.Experiment;
import edu.uoregon.tau.perfdmf.Metric;
import edu.uoregon.tau.perfdmf.View;
import edu.uoregon.tau.perfdmf.Trial;
import edu.uoregon.tau.perfexplorer.common.AnalysisType;
import edu.uoregon.tau.perfexplorer.common.Console;
import edu.uoregon.tau.perfexplorer.common.PerfExplorerOutput;
import edu.uoregon.tau.perfexplorer.common.RMIPerfExplorerModel;
import edu.uoregon.tau.perfexplorer.common.RMISortableIntervalEvent;
import edu.uoregon.tau.perfexplorer.common.ScriptThread;
import edu.uoregon.tau.perfexplorer.common.TransformationType;
import edu.uoregon.tau.perfexplorer.constants.Constants;
import edu.uoregon.tau.perfexplorer.server.PerfExplorerServer;

public class PerfExplorerActionListener implements ActionListener {

	public static final String PARSE_EXPRESSION = "Parse Expression File";
	public static final String REPARSE_EXPRESSION = "Re-Parse Expression File";
	public final static String DATABASE_CONFIGURATION = "Database Configuration";
	public final static String LOADSCRIPT = "Load Analysis Script";
	public final static String RERUNSCRIPT = "Re-run Analysis Script";
	public final static String SAVE_MAIN = "Save Main Window As Vector Image";
	public final static String CONSOLE = "Open New Console Window";
	public final static String QUIT = "Quit PerfExplorer";
	public final static String QUIT_SERVER = "Quit PerfExplorer (Shutdown Server)";
	public final static String LOOK_AND_FEEL = "Set Look and Feel: ";
	public final static String ABOUT = "About PerfExplorer";
	public final static String LOAD_PROFILE = "Load Profile Data";
	public final static String SEARCH = "Search for help on...";
	// clustering menu items
	public final static String CLUSTERING_METHOD = "Select Clustering Method";
	public final static String DIMENSION_REDUCTION = "Select Dimension Reduction";
	public final static String NORMALIZATION = "Select Normalization Method";
	public final static String NUM_CLUSTERS = "Set Maximum Number of Clusters";
	public final static String DO_CLUSTERING = "Do Clustering";
	public final static String DO_INC_CLUSTERING = "Do Inclusive Clustering";
	public final static String DO_CORRELATION_ANALYSIS = "Do Correlation Analysis";
	public final static String DO_INC_CORRELATION_ANALYSIS = "Do Inclusive Correlation Analysis";
	public final static String DO_CORRELATION_CUBE = "Do 3D Correlation Cube";
	public final static String DO_VARIATION_ANALYSIS = "Show Data Summary";
	public final static String DO_LAUNCH_WEKA = "Launch Weka With This Dataset";
	// chart menu items
	public final static String SET_GROUPNAME = "Set Group Name";
	public final static String SET_PROBLEM_SIZE = "Set Problem Size (Scaling)";
	public final static String SET_METRICNAME = "Set Metric of Interest";
	public final static String SET_TIMESTEPS = "Set Total Number of Timesteps";
	public final static String SET_EVENTNAME = "Set Event of Interest";
	public final static String TIMESTEPS_CHART = "Timesteps Per Second";
	public final static String TOTAL_TIME_CHART = "Total Execution Time";
	public final static String EFFICIENCY_CHART = "Relative Efficiency";
	public final static String EFFICIENCY_EVENTS_CHART = "Relative Efficiency by Event";
	public final static String EFFICIENCY_ONE_EVENT_CHART = "Relative Efficiency for One Event";
	public final static String SPEEDUP_CHART = "Relative Speedup";
	public final static String SPEEDUP_EVENTS_CHART = "Relative Speedup by Event";
	public final static String SPEEDUP_ONE_EVENT_CHART = "Relative Speedup for One Event";
	public final static String COMMUNICATION_CHART = "Group % of Total Runtime";
	public final static String FRACTION_CHART = "Runtime Breakdown";
	public final static String CORRELATION_CHART = "Correlate Events with Total Runtime";
	public final static String STACKED_BAR_CHART = "Stacked Bar Chart";
	public final static String ALIGNED_STACKED_BAR_CHART = "Aligned Stacked Bar Chart";
	// phase chart menu items
	public final static String EFFICIENCY_PHASE_CHART = "Relative Efficiency per Phase";
	public final static String SPEEDUP_PHASE_CHART = "Relative Speedup per Phase";
	public final static String FRACTION_PHASE_CHART = "Phase Fraction of Total Runtime";
	// arbitrary view menu items
	public final static String CREATE_NEW_VIEW = "Create New View";
	public final static String CREATE_NEW_SUB_VIEW = "Create New Sub-View";
	public final static String DELETE_CURRENT_VIEW = "Delete Selected View";
	public final static String DO_IQR_BOXCHART = "Create BoxChart";
	public final static String DO_HISTOGRAM = "Create Histograms";
	public final static String DO_PROBABILITY_PLOT = "Create Normal Probability Plot";
	public static final String DO_CHARTS = "Open Scalability Chart Tool";
	public static final String DO_COMMUNICATION_MATRIX = "Show Communication Matrix";

	private PerfExplorerClient mainFrame;

	private String scriptName = null;
	private String scriptDir = null;
	private String expressionFilename;

	public PerfExplorerActionListener (PerfExplorerClient mainFrame) {
		super();
		this.mainFrame = mainFrame;
	}

	public void actionPerformed (ActionEvent event) {
		try {
			Object EventSrc = event.getSource();
			if(EventSrc instanceof JMenuItem) {
				String arg = event.getActionCommand();
			// file menu items
				if(arg.equals(QUIT)) {
					System.exit(0);
				} else if(arg.equals(QUIT_SERVER)) {
					//PerfExplorerConnection server = PerfExplorerConnection.getConnection();
					//server.stopServer();
					System.exit(0);
				} else if (arg.startsWith(LOOK_AND_FEEL)) {
					UIManager.LookAndFeelInfo[] info = UIManager.getInstalledLookAndFeels();
					for (int i = 0 ; i < info.length ; i++) {
						if (arg.endsWith(info[i].getName())) {
							try {
								PerfExplorerClient frame = PerfExplorerClient.getMainFrame();
								UIManager.setLookAndFeel(info[i].getClassName());
								Frame[] frames = Frame.getFrames();
								for (int x = 0 ; x < frames.length ; x++) {
									Component[] comps = frame.getComponents();
									for (int y = 0 ; y < comps.length ; y++) {
										updateAll((Container)comps[y]);
									}
									frames[x].repaint();
								}
							} catch (UnsupportedLookAndFeelException e) {
								PerfExplorerOutput.println(e.getMessage());
							}
						}
					}
				} else if (arg.equals(DATABASE_CONFIGURATION)) {
					databaseConfiguration();
				} else if (arg.equals(PARSE_EXPRESSION)) {
					parseExpression();
				} else if (arg.equals(REPARSE_EXPRESSION)) {
					reparseExpression();
				} else if (arg.equals(LOAD_PROFILE)) {
					loadProfile();
				} else if (arg.equals(LOADSCRIPT)) {
					loadScript();
				} else if (arg.equals(RERUNSCRIPT)) {
					runScript();
				} else if (arg.equals(SAVE_MAIN)) {
					saveMain();
				} else if (arg.equals(CONSOLE)) {
					new Console();
				} 
				else if (arg.equals(ABOUT)) {
					createAboutWindow();
				} else if (arg.equals(SEARCH)) {
					createHelpWindow();
			// clustering items
				} else if (arg.equals(CLUSTERING_METHOD)) {
					createMethodWindow();
				} else if (arg.equals(DIMENSION_REDUCTION)) {
					createDimensionWindow();
				} else if (arg.equals(NORMALIZATION)) {
					createNormalizationWindow();
				} else if (arg.equals(NUM_CLUSTERS)) {
					createClusterSizeWindow();
				} else if (arg.equals(DO_CLUSTERING)) {
					if (validAnalysisSelection()) {
						PerfExplorerModel.getModel().setClusterValueType("exclusive");
						createDoClusteringWindow();
					}
				} else if (arg.equals(DO_INC_CLUSTERING)) {
					if (validAnalysisSelection()) {
						createDoClusteringWindow();
						PerfExplorerModel.getModel().setClusterValueType("inclusive");
					}
				} else if (arg.equals(DO_CORRELATION_ANALYSIS)) {
					if (validCorrelationSelection()) {
						PerfExplorerModel.getModel().setClusterValueType("exclusive");
						createDoCorrelationWindow();
					}
				} else if (arg.equals(DO_INC_CORRELATION_ANALYSIS)) {
					if (validCorrelationSelection()) {
						PerfExplorerModel.getModel().setClusterValueType("inclusive");
						createDoCorrelationWindow();
					}
			// data display items
				} else if (arg.equals(DO_CORRELATION_CUBE)) {
					if (valid3DSelection())
						PerfExplorerCube.doCorrelationCube();
				} else if (arg.equals(DO_LAUNCH_WEKA)) {
					if (valid3DSelection())
						PerfExplorerWekaLauncher.launch();
				} else if (arg.equals(DO_IQR_BOXCHART)) {
					if (valid3DSelection())
						PerfExplorerBoxChart.doIQRBoxChart();
				} else if (arg.equals(DO_HISTOGRAM)) {
					if (validDistributionSelection())
						PerfExplorerHistogramChart.doHistogram();
				} else if (arg.equals(DO_VARIATION_ANALYSIS)) {
					if (valid3DSelection())
						PerfExplorerVariation.doVariationAnalysis();
				} else if (arg.equals(DO_PROBABILITY_PLOT)) {
					if (validDistributionSelection())
						PerfExplorerProbabilityPlot.doProbabilityPlot();
				} else if (arg.equals(DO_COMMUNICATION_MATRIX)) {
					if (validCommunicationMatrixSelection()) {
						CommunicationMatrix mat = new CommunicationMatrix();
						mat.doCommunicationMatrix();
					}
			// chart items
				} else if (arg.equals(DO_CHARTS)) {
					createChartDialogBox();
				} else if (arg.equals(SET_PROBLEM_SIZE)) {
					checkAndSetProblemSize(true);
				} else if (arg.equals(SET_GROUPNAME)) {
					checkAndSetGroupName(true);
				} else if (arg.equals(SET_METRICNAME)) {
					checkAndSetMetricName(true);
				} else if (arg.equals(SET_EVENTNAME)) {
					checkAndSetEventName(true);
				} else if (arg.equals(SET_TIMESTEPS)) {
					checkAndSetTimesteps(true);
				} else if (arg.equals(TIMESTEPS_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetTimesteps(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doTimestepsChart();
						}
				} else if (arg.equals(TOTAL_TIME_CHART)) {
					if (checkAndSetMetricName(false)) {
						ChartGUI.checkScaling();
						PerfExplorerChart.doTotalTimeChart();
					}
				} else if (arg.equals(EFFICIENCY_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doEfficiencyChart();
						}
				} else if (arg.equals(EFFICIENCY_EVENTS_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doEfficiencyEventsChart();
						}
				} else if (arg.equals(EFFICIENCY_ONE_EVENT_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetEventName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doEfficiencyOneEventChart();
						}
				} else if (arg.equals(SPEEDUP_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doSpeedupChart();
						}
				} else if (arg.equals(SPEEDUP_EVENTS_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doSpeedupEventsChart();
						}
				} else if (arg.equals(STACKED_BAR_CHART)) {
					if (checkAndSetMetricName(false))
						PerfExplorerChart.doStackedBarChart();
				} else if (arg.equals(ALIGNED_STACKED_BAR_CHART)) {
					if (checkAndSetMetricName(false))
						PerfExplorerChart.doAlignedStackedBarChart();
				} else if (arg.equals(SPEEDUP_ONE_EVENT_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetEventName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doSpeedupOneEventChart();
						}
				} else if (arg.equals(COMMUNICATION_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetGroupName(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doCommunicationChart();
						}
				} else if (arg.equals(FRACTION_CHART)) {
					if (checkAndSetMetricName(false)) {
						ChartGUI.checkScaling();
						PerfExplorerChart.doFractionChart();
					}
				} else if (arg.equals(CORRELATION_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doCorrelationChart();
						}
				} else if (arg.equals(EFFICIENCY_PHASE_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doEfficiencyPhasesChart();
						}
				} else if (arg.equals(SPEEDUP_PHASE_CHART)) {
					if (checkAndSetMetricName(false))
						if (checkAndSetProblemSize(false)) {
							ChartGUI.checkScaling();
							PerfExplorerChart.doSpeedupPhasesChart();
						}
				} else if (arg.equals(FRACTION_PHASE_CHART)) {
					if (checkAndSetMetricName(false)) {
						ChartGUI.checkScaling();
						PerfExplorerChart.doFractionPhasesChart();
					}
			// view items
				} else if (arg.equals(CREATE_NEW_VIEW)) {
					int parent = 0; // no parent
					PerfExplorerViews.createNewView(mainFrame, parent);
				} else if (arg.equals(CREATE_NEW_SUB_VIEW)) {
					PerfExplorerViews.createNewSubView(mainFrame);
				} else if (arg.equals(DELETE_CURRENT_VIEW)) {
					PerfExplorerViews.deleteCurrentView(mainFrame);
				} else {
					System.out.println("unknown event! " + arg);
				}
			}
		} catch (SeriesException e) {
			// this shouldn't happen, but if it does, handle it gracefully.
			StringBuilder sb = new StringBuilder();
			sb.append("Two or more trials in this selection have the same total number of threads of execution, and an error occurred.\n");
			sb.append("To create a scalability chart, please ensure the trials selected have different numbers of threads.\n");
			sb.append("To create a different parametric chart, please use the custom chart interface.");			
			JOptionPane.showMessageDialog(PerfExplorerClient.getMainFrame(), sb.toString(),
					"Selection Warning", JOptionPane.ERROR_MESSAGE);
		} catch (Exception e) {
			System.err.println("actionPerformed Exception: " + e.getMessage());
			e.printStackTrace();
		} 
	}

	private void createChartDialogBox() {
		System.out.println("Opening Dialog Box to create charts");
		//JFrame dialogBox = 
			ChartGUI.getInstance(true);
	}

	private void updateAll (Container container) {
		Component[] comps = container.getComponents();
		for (int y = 0 ; y < comps.length ; y++) {
			if (comps[y] instanceof Container) {
				updateAll((Container)comps[y]);
			}
			if (comps[y] instanceof JComponent) {
				JComponent comp = (JComponent)comps[y];
				comp.updateUI();
			}
			if (comps[y] instanceof JTree) {
				JTree tree = (JTree)comps[y];
				tree.updateUI();
			}
		}
		container.repaint();
	}

    public static String getVersionString() {
		return new String(Constants.VERSION);
	}

	public void createAboutWindow() {
		long memUsage = (Runtime.getRuntime().totalMemory() -
			Runtime.getRuntime().freeMemory()) / 1024;

		StringBuilder buf = new StringBuilder();
		//for (java.util.Enumeration e = System.getProperties().propertyNames(); e.hasMoreElements() ;) {
		    //System.out.println(e.nextElement());
		//}
		buf.append("\njava.home : " + System.getProperty("java.home"));
		buf.append("\njava.vendor : " + System.getProperty("java.vendor"));
		buf.append("\njava.vendor.url : " + System.getProperty("java.vendor.url"));
		buf.append("\njava.version : " + System.getProperty("java.version"));
		buf.append("\nos.arch : " + System.getProperty("os.arch"));
		buf.append("\nos.name : " + System.getProperty("os.name"));
		buf.append("\nos.version : " + System.getProperty("os.version"));
		buf.append("\nuser.dir : " + System.getProperty("user.dir"));
		buf.append("\nuser.home : " + System.getProperty("user.home"));
		buf.append("\nuser.name : " + System.getProperty("user.name"));
		buf.append("\nuser.country : " + System.getProperty("user.country"));
		buf.append("\nuser.timezone : " + System.getProperty("user.timezone"));
		buf.append("\nuser.language : " + System.getProperty("user.language"));
		String message = new String("PerfExplorer 2.0\n" +
					getVersionString() + "\nJVM Heap Size: " + memUsage
					+ "kb\n" + buf.toString());
		ImageIcon icon = createImageIcon(Utility.getResource("tau-large.png"));
		JOptionPane.showMessageDialog(mainFrame, message, 
			"About PerfExplorer", JOptionPane.INFORMATION_MESSAGE, icon);
	}

	public void databaseConfiguration() {
		(new DatabaseManagerWindow(PerfExplorerClient.getMainFrame())).setVisible(true);
	}
	public void deriveMetric() {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		PerfExplorerConnection server = PerfExplorerConnection.getConnection();
		
		Application app = null;
		Experiment exp = null;
		Trial trial = null;
		
		Object selection = theModel.getCurrentSelection();
		if(selection instanceof Application){
			app = (Application) selection;
		}else if(selection instanceof Experiment){
			exp = (Experiment) selection;
			ListIterator<Application> apps = server.getApplicationList();
			while(apps.hasNext()){
				app = apps.next();
				if(app.getID()==exp.getApplicationID()){
					break;
				}
			}
		}else if(selection instanceof Trial){
			trial = (Trial)selection;
			ListIterator<Application> apps = server.getApplicationList();
			while(apps.hasNext()){
				app = apps.next();
				if(app.getID()==trial.getApplicationID()){
					break;
				}
			}
			ListIterator<Experiment> experiments = server.getExperimentList(trial.getApplicationID());
			while(experiments.hasNext()){
				exp = experiments.next();
				if(exp.getID()==trial.getExperimentID()){
					break;
				}
			}
		}

		if(app != null){

			DerivedMetricWindow window = new DerivedMetricWindow(PerfExplorerClient.getMainFrame(),
					app,exp,trial);
			window.setVisible(true);
		}else{
			JOptionPane.showMessageDialog(mainFrame, "Please select an Application, Experiment or Trial.",
					"Selection Error", JOptionPane.ERROR_MESSAGE);
		}
	}

	/** Returns an ImageIcon, or null if the path was invalid. */
	protected static ImageIcon createImageIcon(java.net.URL imgURL) {
		if (imgURL != null) {
			return new ImageIcon(imgURL);
		} else {
			System.err.println("Couldn't find file: " + imgURL);
			return null;
		}
	}

	public void createHelpWindow() {
		ImageIcon icon = createImageIcon(Utility.getResource("tau-large.png"));
		JOptionPane.showMessageDialog(mainFrame, 
			"Internal help not implemented.\nFor the most up-to-date documentation, please see\n<html><a href='http://www.cs.uoregon.edu/research/tau/'>http://www.cs.uoregon.edu/research/tau/</a></html>",
			"PerfExplorer Help", JOptionPane.INFORMATION_MESSAGE, icon);
	}

	public void createMethodWindow() {
		Object[] options = AnalysisType.getClusterMethods();
		AnalysisType reply = (AnalysisType)JOptionPane.showInputDialog (mainFrame,
			"Select a cluster method:",
			"Cluster Method",
			JOptionPane.PLAIN_MESSAGE,
			null,
			options,
			PerfExplorerModel.getModel().getClusterMethod());
		PerfExplorerModel.getModel().setClusterMethod(reply);
	}

	public void createDimensionWindow() {
		Object[] options = TransformationType.getDimensionReductions();
		Object obj = JOptionPane.showInputDialog (mainFrame,
			"Select a dimension reduction method:",
			"Dimension Reduction",
			JOptionPane.PLAIN_MESSAGE,
			null,
			options,
			TransformationType.NONE);
        TransformationType reply = (TransformationType)obj;
		PerfExplorerModel.getModel().setDimensionReduction(reply);
		if (reply!=TransformationType.NONE&&reply!=null&&PerfExplorerModel.getModel().getDimensionReduction().equals(reply)) {
			String reply2 = (String)JOptionPane.showInputDialog (mainFrame,
				"Only select events with exclusive time % greater than X:\n(where 0 <= X < 100)",
				"Minimum Percentage", JOptionPane.PLAIN_MESSAGE);
			if (reply2 != null && !reply2.equals(""))
				PerfExplorerModel.getModel().setXPercent(reply2);
		}
	}

	public void createNormalizationWindow() {
		Object[] options = TransformationType.getNormalizations();
		TransformationType reply = (TransformationType)JOptionPane.showInputDialog (mainFrame,
			"Select a normalization method:",
			"Normalization",
			JOptionPane.PLAIN_MESSAGE,
			null,
			options,
			TransformationType.NONE);
		PerfExplorerModel.getModel().setNormalization(reply);
	}

	public void createClusterSizeWindow() {
		String numClusters = (new Integer(PerfExplorerModel.getModel().getNumberOfClusters())).toString();
		String reply = (String)JOptionPane.showInputDialog (mainFrame,
			"Enter the max number of clusters (<= " + numClusters + "):",
			"Max Clusters", JOptionPane.PLAIN_MESSAGE);
		if (reply != null && !reply.equals(""))
			PerfExplorerModel.getModel().setNumberOfClusters(reply);
	}

	public void createDoClusteringWindow() {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		String status = null;
		if (selection instanceof Application) {
			int reply = getConfirmation(theModel);
			if (reply == 1) {
				Application application = (Application)selection;
				PerfExplorerConnection server = PerfExplorerConnection.getConnection();
				ListIterator<Experiment> experiments = server.getExperimentList(application.getID());
				Experiment experiment = null;
				boolean failed = false;
				while (experiments.hasNext() && !failed) {
					experiment = experiments.next();
					theModel.setCurrentSelection(experiment);
					ListIterator<Trial> trials = server.getTrialList(experiment.getID(),false);
					Trial trial = null;
					while (trials.hasNext() && !failed) {
						trial = trials.next();
						theModel.setCurrentSelection(trial);
						List<Metric> metrics = trial.getMetrics();
						for (int i = 0; i < metrics.size(); i++) {
							Object metric = metrics.get(i);
							theModel.setCurrentSelection(metric);
							// request some analysis!
							RMIPerfExplorerModel modelCopy = theModel.copy();
							status = server.requestAnalysis(modelCopy, true);
							if (!status.endsWith("Request accepted.")) {
								JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
									"Request Status", JOptionPane.ERROR_MESSAGE);
								failed = true;
								break;
							}
						}
					}
                    // set the selection back to experiment
					theModel.setCurrentSelection(experiment);
				}
				// set the selection back to application
				theModel.setCurrentSelection(application);
				if (status.endsWith("Request accepted.")) {
					JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
						"Request Status", JOptionPane.PLAIN_MESSAGE);
				}
			}
		} else if (selection instanceof Experiment) {
			int reply = getConfirmation(theModel);
			if (reply == 1) {
				Experiment experiment = (Experiment)selection;
				PerfExplorerConnection server = PerfExplorerConnection.getConnection();
				ListIterator<Trial> trials = server.getTrialList(experiment.getID(),false);
				Trial trial = null;
				boolean failed = false;
				while (trials.hasNext() && !failed) {
					trial = trials.next();
					theModel.setCurrentSelection(trial);
					List<Metric> metrics = trial.getMetrics();
					for (int i = 0; i < metrics.size(); i++) {
						Object metric = metrics.get(i);
						theModel.setCurrentSelection(metric);
						// request some analysis!
						RMIPerfExplorerModel modelCopy = theModel.copy();
						status = server.requestAnalysis(modelCopy, true);
						if (!status.endsWith("Request accepted.")) {
							JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
								"Request Status", JOptionPane.ERROR_MESSAGE);
							failed = true;
							break;
						}
					}
				}
				if (status.endsWith("Request accepted.")) {
					JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
						"Request Status", JOptionPane.PLAIN_MESSAGE);
				}
                // set the selection back to experiment
				theModel.setCurrentSelection(experiment);
			}
		} else if (selection instanceof Trial) {
		/*
			JOptionPane.showMessageDialog(mainFrame, "Please select a Metric.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
				*/
			int reply = getConfirmation(theModel);
			if (reply == 1) {
				PerfExplorerConnection server = PerfExplorerConnection.getConnection();
				RMIPerfExplorerModel modelCopy = theModel.copy();
				status = server.requestAnalysis(modelCopy, true);
				Trial trial = (Trial)selection;
				List<Metric> metrics = trial.getMetrics();
				for (int i = 0; i < metrics.size(); i++) {
					modelCopy = theModel.copy();
					Object metric = metrics.get(i);
					modelCopy.setCurrentSelection(metric);
					// request some analysis!
					status = server.requestAnalysis(modelCopy, true);
					if (!status.endsWith("Request accepted.")) {
						JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
							"Request Status", JOptionPane.ERROR_MESSAGE);
						break;
					}
				}
				if (status.endsWith("Request accepted.")) {
					JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
						"Request Status", JOptionPane.PLAIN_MESSAGE);
				}
			}
		} else if (selection instanceof Metric) {
			int reply = getConfirmation(theModel);
			if (reply == 1) {
				// request some analysis!
				PerfExplorerConnection server = PerfExplorerConnection.getConnection();
				status = server.requestAnalysis(PerfExplorerModel.getModel(), true);
				if (status.endsWith("Request accepted.")) {
					JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
						"Request Status", JOptionPane.PLAIN_MESSAGE);
				} else {
					JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
						"Request Status", JOptionPane.ERROR_MESSAGE);
				}
			}
		}
		return;
	}

	public void createDoCorrelationWindow() {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		String status = null;
		if ((selection instanceof Trial) || (selection instanceof Metric)) {
//			String tmp = theModel.getClusterMethod();
			RMIPerfExplorerModel modelCopy = theModel.copy();
			modelCopy.setClusterMethod(AnalysisType.CORRELATION_ANALYSIS);
			int reply = getConfirmation(modelCopy);
			if (reply == 1) {
				// request some analysis!
				PerfExplorerConnection server = PerfExplorerConnection.getConnection();
				status = server.requestAnalysis(modelCopy, true);
				if (status.endsWith("Request accepted.")) {
					JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
						"Request Status", JOptionPane.PLAIN_MESSAGE);
				} else {
					JOptionPane.showMessageDialog(mainFrame, "Request Status: \n" + status,
						"Request Status", JOptionPane.ERROR_MESSAGE);
				}
			}
		}
		return;
	}

	private int getConfirmation(RMIPerfExplorerModel theModel) {
		Object [] options = { "No, not yet" , "Yes, do analysis" };
		StringBuilder buf = new StringBuilder();
		buf.append("Analysis method: " + theModel.getClusterMethod());
		buf.append("\nDimension Reduction: " + theModel.getDimensionReduction());
		if (theModel.getDimensionReduction().equals(TransformationType.OVER_X_PERCENT)) 
			buf.append("\n\t\t Minimum percentage: " + theModel.getXPercent());
		buf.append("\nNormalization: " + theModel.getNormalization());
		if (!theModel.getClusterMethod().equals(AnalysisType.CORRELATION_ANALYSIS))
			buf.append("\nMax Clusters: " + theModel.getNumberOfClusters());
		buf.append("\nTrial: " + theModel.toString());
		buf.append("\n\nPerform " + theModel.getClusterMethod() + " with the these options?");
		int reply = JOptionPane.showOptionDialog(mainFrame, buf.toString(),
			"Confirm Analysis",
			JOptionPane.YES_NO_OPTION, 
			JOptionPane.PLAIN_MESSAGE,
			null, 
			options, 
			options[1]);
		return reply;
	}

	private boolean validCorrelationSelection () {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		// allow Experiments or Trials or 1 view
		if (!(selection instanceof Trial) && !(selection instanceof Metric)) {
			JOptionPane.showMessageDialog(mainFrame, "Please select a Trial or Metric.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		// check multi-selections, to make sure they are homogeneous
		return true;
	}

	private boolean validAnalysisSelection () {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		// allow Experiments or Trials or 1 view
		if (!(selection instanceof Experiment) && !(selection instanceof Trial) && !(selection instanceof Application) && !(selection instanceof Metric)) {
			JOptionPane.showMessageDialog(mainFrame, "Please select an Application, Experiment, Trial or Metric.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		// check multi-selections, to make sure they are homogeneous
		return true;
	}

	private boolean validSelection (PerfExplorerModel theModel) {
		Object selection = theModel.getCurrentSelection();
/*		// allow Experiments or Trials or 1 view
		if (!(selection instanceof Experiment) && !(selection instanceof Trial) && !(selection instanceof RMIView)) {
			JOptionPane.showMessageDialog(mainFrame, "Please select one or more Experiments or Trials.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
*/		// allow Experiments or 1 view
		if (!(selection instanceof Experiment) && !(selection instanceof View)) {
		// allow Experiments or 1 view
		// if (!(selection instanceof Experiment) && !(selection instanceof RMIView)) {
			JOptionPane.showMessageDialog(mainFrame, "Please select one or more Experiments or one View.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		// check multi-selections, to make sure they are homogeneous
		return true;
	}

	private boolean valid3DSelection () {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		// allow only Metrics
		if ((selection == null) || !(selection instanceof Metric)) {
			JOptionPane.showMessageDialog(mainFrame, "Please select a Metric.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		return true;
	}

	private boolean validDistributionSelection () {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		// allow only Metrics or IntervalEvents
		if ((selection == null) || 
			(!(selection instanceof Metric) && 
			 !(selection instanceof RMISortableIntervalEvent))) {
			JOptionPane.showMessageDialog(mainFrame, 
				"Please select an Metrics or one or more Events.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		return true;
	}

	private boolean validCommunicationMatrixSelection () {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		// allow only Trials
		if ((selection == null) || !(selection instanceof Trial)) {
			JOptionPane.showMessageDialog(mainFrame, 
				"Please select one Trial.",
				"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		return true;
	}

	private boolean checkAndSetMetricName (boolean forceIt) {
		//TODO - MAKE SURE THE METRIC EXISTS IN THE SELECTED TRIALS!
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		if (!validSelection(theModel))
			return false;
		String metric = theModel.getMetricName();
		if (forceIt || (metric == null)) {
			PerfExplorerConnection server = PerfExplorerConnection.getConnection();
			List<String> metrics = server.getPotentialMetrics(theModel);
			Object[] options = metrics.toArray();
			if (options.length > 0) {
				if (options.length == 1) {
					metric = (String)options[0];
				} else {
					metric = (String)JOptionPane.showInputDialog (mainFrame,
						"Please enter the metric of interest",
						"Metric of interest", JOptionPane.PLAIN_MESSAGE,
						null, options,options[0]);
				}
				theModel.setMetricName(metric);
			}
		}
		return (!forceIt && metric == null) ? false : true;
	}

	private boolean checkAndSetGroupName (boolean forceIt) {
		//TODO - MAKE SURE THE GROUP EXISTS IN THE SELECTED TRIALS!
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		String group = theModel.getGroupName();
		if (forceIt || group == null) {
			PerfExplorerConnection server = PerfExplorerConnection.getConnection();
			List<String> metrics = server.getPotentialGroups(theModel);
			Object[] options = metrics.toArray();
			if (options.length > 0) {
				if (options.length == 1) {
					group = (String)options[0];
				} else {
					group = (String)JOptionPane.showInputDialog (mainFrame,
						"Please enter the group of interest",
						"Group of interest", JOptionPane.PLAIN_MESSAGE,
						null, options, options[0]);
				}
				theModel.setGroupName(group);
			}
		}
		return (!forceIt && group == null) ? false : true;
	}

	private boolean checkAndSetEventName (boolean forceIt) {
		//TODO - MAKE SURE THE EVENT EXISTS IN THE SELECTED TRIALS!
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		String event = theModel.getEventName();
		if (forceIt || event == null) {
			PerfExplorerConnection server = PerfExplorerConnection.getConnection();
			List<String> events = server.getPotentialEvents(theModel);
			List<String> callpath = server.getPotentialCallPathEvents(theModel);
			for(String cp: callpath){
				events.add(cp);
			}
			
			
			Object[] options = events.toArray();
			if (options.length > 0) {
				if (options.length == 1) {
					event = (String)options[0];
				} else {
					event = (String)JOptionPane.showInputDialog (mainFrame,
						"Please enter the event of interest",
						"Event of interest", JOptionPane.PLAIN_MESSAGE,
						null, options, options[0]);
				}
				theModel.setEventName(event);
			}
		}
		return (!forceIt && event == null) ? false : true;
	}

	private boolean checkAndSetTimesteps (boolean forceIt) {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		String timesteps = theModel.getTotalTimesteps();
		if (forceIt || timesteps == null) {
			timesteps = (String)JOptionPane.showInputDialog (mainFrame,
				"Please enter the total number of timesteps for the experiment",
				"Total Timesteps", JOptionPane.PLAIN_MESSAGE);
			theModel.setTotalTimesteps(timesteps);
		}
		return (!forceIt && timesteps == null) ? false : true;
	}

	private boolean checkAndSetProblemSize (boolean forceIt) {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Boolean constantProblem = theModel.getConstantProblem();
		if (forceIt || constantProblem == null) {
			List<String> answers = new ArrayList<String>();
			answers.add("The problem size remains constant. (strong scaling)");
			answers.add("The problem size increases as the processor count increases. (weak scaling)");
			Object[] options = answers.toArray();
			String response = (String)JOptionPane.showInputDialog (mainFrame,
				"Please select the problem scaling:",
				"Problem Scaling", JOptionPane.PLAIN_MESSAGE,
				null, options, options[0]);
			if (response != null) {
				theModel.setConstantProblem(response.startsWith("The problem size remains") ? true : false);
				constantProblem = theModel.getConstantProblem();
			}
		}
		return (!forceIt && constantProblem == null) ? false : true;
	}

	public static int setSession (String name) {
		try {
			PerfExplorerConnection server = PerfExplorerConnection.getConnection();
			List<String> configNames = server.getConfigNames();
			int i = 0;
			for (String configName : configNames) {
//				System.out.println(server.getConnectionString());
				if (configName.equals(name)) {
					server.setConnectionIndex(i);
					return i;
				}
				i++;
			}
		} catch (Exception e) {}
		return 0;
	}
	
	private boolean loadProfile () {
		// the default session is the last session, which is the perfexplorer working database.
//		setSession(Constants.PERFEXPLORER_WORKING_CONFIG);

		Application app = new Application();
		Experiment exp = new Experiment();
		// create new application, experiment
		try {
			app.setName("New Application");
			app.setID(app.saveApplication(PerfExplorerServer.getServer().getDB()));
			PerfExplorerModel.getModel().setCurrentSelection(app);
			exp.setApplicationID(app.getID());
			exp.setName("New Experiment");
			exp.setID(exp.saveExperiment(PerfExplorerServer.getServer().getDB()));
			PerfExplorerModel.getModel().setCurrentSelection(exp);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		LoadTrialWindow ltw = new LoadTrialWindow(mainFrame, this, app, exp, true, true);
		ltw.setVisible(true);

		return true;
	}

	private boolean loadScript () {
		JFileChooser fc = null;
		// open a file chooser dialog
		if (scriptDir == null) {
			fc = new JFileChooser(System.getProperty("user.dir"));
		} else {
			fc = new JFileChooser(scriptDir);
		}
		int returnVal = fc.showOpenDialog(mainFrame);
		if (returnVal == JFileChooser.APPROVE_OPTION) {
			scriptName = fc.getSelectedFile().getAbsolutePath();
			// save where we were
			scriptDir = fc.getSelectedFile().getParent();
			runScript();
			return true;
		}
		return false;
	}



	private boolean parseExpression() {
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Object selection = theModel.getCurrentSelection();
		if(selection==null){
			JOptionPane.showMessageDialog(mainFrame, "Please select an Application, Experiment or Trial.",
					"Selection Error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		
		JFileChooser fc = null;
		// open a file chooser dialog
		if (scriptDir == null) {
			fc = new JFileChooser(System.getProperty("user.dir"));
		} else {
			fc = new JFileChooser(scriptDir);
		}
		int returnVal = fc.showOpenDialog(mainFrame);
		if (returnVal == JFileChooser.APPROVE_OPTION) {
			expressionFilename = fc.getSelectedFile().getAbsolutePath();
			// save where we were
			scriptDir = fc.getSelectedFile().getParent();
			reparseExpression();
			return true;
		}
		return false;

	}
	public boolean reparseExpression() {
		
		PerfExplorerModel theModel = PerfExplorerModel.getModel();
		Application a = theModel.getApplication();
		Experiment ex = theModel.getExperiment();
		Trial t = theModel.getTrial();
		String app =null,exp=null,trial=null;
		if(a!=null)app = a.getName();
		if(ex!=null)exp = ex.getName();
		if(t!=null)trial = t.getName();
		if (expressionFilename == null) {
			// make sure a script file has been loaded first
			JOptionPane.showMessageDialog(mainFrame, 
					"Please load an expression file first.",
					"Expression File Not Found", JOptionPane.ERROR_MESSAGE);
			return false;
		} else {
			if(app != null){
			String script;
			try {
				script = new PerfExplorerExpression().getScriptFromFile(app,exp,trial,expressionFilename);
				//ScriptThread runner = 
					new ScriptThread(script,true);
			} catch (FileNotFoundException e) {
				JOptionPane.showMessageDialog(mainFrame, 
						"",
						"Script File Not Found", JOptionPane.ERROR_MESSAGE);
			} catch (ParsingException e) {
				JOptionPane.showMessageDialog(mainFrame, 
						"",
						"Unable to Parse Expression", JOptionPane.ERROR_MESSAGE);
			}
			return true;
			}else{
				JOptionPane.showMessageDialog(mainFrame, "Please select an Application, Experiment or Trial.",
						"Selection Error", JOptionPane.ERROR_MESSAGE);
				return false;
			}
		}
	}

	public boolean runScript() {
		if (scriptName == null) {
			// make sure a script file has been loaded first
			JOptionPane.showMessageDialog(mainFrame, 
				"Please load a script first.",
				"Script File Not Found", JOptionPane.ERROR_MESSAGE);
			return false;
		} else {
			// run the script
			//PythonInterpreterFactory.defaultfactory.getPythonInterpreter().execfile(scriptName);
			//ScriptThread runner = 
				new ScriptThread(scriptName);
			return true;
		}
	}

    public void saveMain() {
        //System.out.println("Daemon come out!");
        try {
            VectorExport.promptForVectorExport (mainFrame, "PerfExplorer");
        } catch (Exception e) {
            System.out.println("File Export Failed!");
        }
        return;
    }

	/**
	 * @return the scriptName
	 */
	public String getScriptName() {
		return scriptName;
	}

	/**
	 * @param scriptName the scriptName to set
	 */
	public void setScriptName(String scriptName) {
		this.scriptName = scriptName;
	}

    public void handleDelete(Object clickedOnObject) {
    	try {
            DatabaseAPI databaseAPI = PerfExplorerServer.getServer().getSession();
            if (clickedOnObject instanceof Application) {
	            Application application = (Application) clickedOnObject;
	            if (databaseAPI != null) {
	                databaseAPI.deleteApplication(application.getID());
	                //treeModel.removeNodeFromParent(application.getDMTN());
	            }
	        } else if (clickedOnObject instanceof Experiment) {
	            Experiment experiment = (Experiment) clickedOnObject;
	            if (databaseAPI != null) {
	                databaseAPI.deleteExperiment(experiment.getID());
                    //treeModel.removeNodeFromParent(experiment.getDMTN());
	            }	
	        } else if (clickedOnObject instanceof Trial) {
	        	Trial ppTrial = (Trial) clickedOnObject;
                if (databaseAPI != null) {
                    databaseAPI.deleteTrial(ppTrial.getID());
                    //treeModel.removeNodeFromParent(ppTrial.getDMTN());
                }
	        }
        } catch (Exception e) {
        	System.out.print(e.getMessage());
        	e.printStackTrace();
        }
    }
}
