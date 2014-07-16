package edu.uoregon.tau.perfdmf;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.StringTokenizer;

import edu.uoregon.tau.common.TrackerInputStream;

public class ParaverDataSource extends DataSource {

	//private int linenumber = 0;
	//private int currentProcess = 0;
	//private int currentThread = 0;
	private File file = null;
    
    private volatile long totalBytes = 0;
    private volatile TrackerInputStream tracker;
	//private double beginTime = 0.0;
	//private double endTime = 0.0;
	private double duration = 0.0;
	private double exclusiveDuration = 0.0;
	private double durationMicrosecondsPercent = 0.0;
	private String fileIndex = "";
	private String metricName = "";
	private String selectedFunction = "";
	//private String windowName = "";
	private String shortMetric = null;
	private int metricIndex = 0;
	private boolean doingBursts = false;
	private boolean doingInclusive = false;
	private NumberFormat nfDLocal = NumberFormat.getNumberInstance();
	private NumberFormat nfScientific = new DecimalFormat("0.0E0");
	private static final double NANOSECONDS = 0.001; // to convert to microseconds
	private static final double MICROSECONDS = 1.000; // to convert to microseconds
	private static final double MILLISECONDS = 1000.0; // to convert to microseconds
	private static final double SECONDS = 1000000.0; // to convert to microseconds
	private static final double HOURS = 3600000000.0; // to convert to microseconds

	private List<String> functionNames = null;
	//private TreeMap functions = new TreeMap();

    public ParaverDataSource(File[] files) {
        super();
        this.files = files;
		System.out.println("Processing " + this.files.length + " files...");
    }

    private File files[];

    public ParaverDataSource(File file) {
        super();
		this.files[0] = file;
    }

    public void cancelLoad() {
        return;
    }

    public int getProgress() {
        if (totalBytes != 0) {
            return (int) ((float) tracker.byteCount() / (float) totalBytes * 100);
        }
        return 0;
    }

    public void load() throws FileNotFoundException, IOException {
        //Record time.
        long time = System.currentTimeMillis();

        Thread thread = null;

		for(int i = 0; i < this.files.length ; i++) {
			file = files[i];

		//System.out.println("Processing " + file + ", please wait ......");
		fileIndex="[" + Integer.toString(i) + "]";
		getMetaData().put("Data File Name" + fileIndex, file.getAbsolutePath());
		FileInputStream fileIn = new FileInputStream(file);
		tracker = new TrackerInputStream(fileIn);
		InputStreamReader inReader = new InputStreamReader(tracker);
		BufferedReader br = new BufferedReader(inReader);
		
		totalBytes = file.length();

		// process the global section, and do what's necessary
		processGlobalSection(br);
		//System.out.println("Num Tasks: " + globalData.numTasks);

		String inputString = null;
		String tmp = null;
		doingBursts = false;
		doingInclusive = false;
		while((inputString = br.readLine()) != null){
			inputString = inputString.trim();
			if (inputString.trim().length() == 0) {
				// ignore blank lines
			} else if (inputString.startsWith("Objects/Intervals")) {
				// process the function names
				functionNames = new ArrayList<String>();
        		StringTokenizer st = new StringTokenizer(inputString, " \t\n\r");
        		tmp = st.nextToken(); // Objects/Intervals
				while (st.hasMoreTokens()) {
        			tmp = st.nextToken(); // function name
					functionNames.add(tmp);
				}
			} else if (inputString.startsWith("THREAD")) {
				// reset the exclusive Duration timer for this thread
				exclusiveDuration = duration;

				// process the function data.
        		Function function = null;
        		FunctionProfile fp = null;

				// process thread data
        		StringTokenizer st = new StringTokenizer(inputString, " \t\n\r");

				// do we have units or not?
				int numFunctions = functionNames.size();
				int numTokens = st.countTokens();
				boolean haveUnits = false;
				if (numTokens == (numFunctions * 2) + 2)
					haveUnits = true;
				double unitConversion = MICROSECONDS; // default unit for Paraver

        		tmp = st.nextToken(); // THREAD
        		tmp = st.nextToken(); // 1.1.1, 1.2.1, etc
        		StringTokenizer st2 = new StringTokenizer(tmp, ".");
        		tmp = st2.nextToken(); // ignore
        		tmp = st2.nextToken(); // process
          		int node = Integer.parseInt(tmp)-1;
        		tmp = st2.nextToken(); // thread
           		thread = this.addThread(node, 0, Integer.parseInt(tmp)-1);
           		figureOutMetricName();
				int j = 0;
				while (st.hasMoreTokens()) {
        			tmp = st.nextToken(); // function value
					double value = 0.0;
					try {
						// Because Java doesn't have an explicit method for parsing
						// scientific notation...
						StringTokenizer st3 = new StringTokenizer(tmp.toUpperCase(), "E+");
   						if (st3.countTokens() == 2) {
							// this is scientific notation - parse each part and combine
							double parsed = nfScientific.parse(st3.nextToken()).doubleValue();
							double power = nfScientific.parse(st3.nextToken()).doubleValue();
							value = parsed * (Math.pow(10.0, power));
						} else {
							// this is a regular number
							value = nfDLocal.parse(tmp).doubleValue();
						}
					} catch (ParseException pe2) {/*System.err.println("Error parsing: " + tmp);*/ continue;}
					if (haveUnits) {
        				String units = st.nextToken(); // units value
						if (units.equalsIgnoreCase("ns"))
							unitConversion = NANOSECONDS;
						else if (units.equalsIgnoreCase("us"))
							unitConversion = MICROSECONDS;
						else if (units.equalsIgnoreCase("ms"))
							unitConversion = MILLISECONDS;
						else if (units.equalsIgnoreCase("s"))
							unitConversion = SECONDS;
						else if (units.equalsIgnoreCase("h"))
							unitConversion = HOURS;
						else if (units.equalsIgnoreCase("%"))
							// the unit is percent, so convert from the total duration,
							// which is in nanoseconds, to microseconds
							unitConversion = durationMicrosecondsPercent;
					} // assume nanoseconds, the Paraver default

					// for this function, create a function
					String name = functionNames.get(j);
					if (!name.equalsIgnoreCase("End")) {
						exclusiveDuration = exclusiveDuration - value;
						value = value * unitConversion;
						function = this.addFunction(name, this.metrics.size()); // ,1?
						fp = thread.getFunctionProfile(function);
						if (fp == null) {
							fp = new FunctionProfile(function, this.metrics.size());
							thread.addFunctionProfile(fp);
						}
	
						// set the values for each metric
						if (name.startsWith("MPI"))
							function.addGroup(this.addGroup("MPI"));
						else
							function.addGroup(this.addGroup("TAU_DEFAULT"));
						
						if (doingInclusive) {
							fp.setInclusive(metricIndex, value); // we do have this value!
						} else if (doingBursts) {
							fp.setNumCalls(value);  // we do have this value!
						} else {
							fp.setNumCalls(1);  // we don't have this value
							fp.setNumSubr(0);  // we don't have this value
							if (!(fp.getInclusive(metricIndex) > 0.0))
								fp.setInclusive(metricIndex, value); // we don't have this value
							fp.setExclusive(metricIndex, value);
						}
					}
					j++;
				}
				// create the "main" function
				function = this.addFunction(".TAU application", this.metrics.size()); // ,1?
				fp = thread.getFunctionProfile(function);
				if (fp == null) {
					fp = new FunctionProfile(function, this.metrics.size());
					thread.addFunctionProfile(fp);
				}
				function.addGroup(this.addGroup("TAU_DEFAULT"));
				fp.setNumCalls(1);  // we don't have this value
				fp.setNumSubr(0);  // we don't have this value
				// no need to convert these units, already in microseconds
				if (!doingBursts) {
					fp.setInclusive(metricIndex, duration);
					double tmpExclusive = fp.getExclusive(metricIndex);
					if (tmpExclusive > 0.0) {
						fp.setExclusive(metricIndex, Math.max(duration - (tmpExclusive + exclusiveDuration),1.0));
					} else {
						fp.setExclusive(metricIndex, Math.max(exclusiveDuration,0.0));					
					}
				}
			}
		}

		time = (System.currentTimeMillis()) - time;
        //System.out.println("Done parsing data!");
        //System.out.println("Time to process (in milliseconds): " + time);
        fileIn.close();
		}
		this.generateDerivedData();
		this.aggregateMetaData();
		this.buildXMLMetaData();
		setGroupNamesPresent(true);
    }

	private void figureOutMetricName() {
		Metric metric = null;
		if (selectedFunction.replaceAll("%", "").trim().equalsIgnoreCase("time")) {
			this.metricName = "Time";
			metric = this.addMetric(metricName);
		} else if (selectedFunction.equalsIgnoreCase("# Bursts")) {
			// this file has the number of calls value.
			doingBursts = true;
			if (this.metrics == null || this.metrics.size() == 0) {
				this.metricName = "Time";
				metric = this.addMetric(metricName);
			}
		} else {
			if (shortMetric != null) {
				metric = this.addMetric(shortMetric);
			} else {
				metric = this.addMetric(metricName);
			}
		}
		if (metric != null) {
			this.metricIndex = metric.getID();
		}
	}

	private void processGlobalSection(BufferedReader br) {
		String inputString = null;
		String tmp = null;
		metricName = new String();
		try {
			while((inputString = br.readLine()) != null){
				inputString = inputString.trim();
				if (inputString.startsWith("Paraver 2D histogram")) {
					// do nothing
				} else if (inputString.startsWith("Paraver 3D histogram")) {
					// do nothing
				} else if (inputString.startsWith("Trace File:")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Trace
        			tmp = st.nextToken(); // File
        			tmp = st.nextToken(); // "filename"
					tmp = tmp.replaceAll("\"","");
					getMetaData().put("Trace File" + fileIndex, tmp);
				} else if (inputString.startsWith("Selected Function:")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Selected
        			tmp = st.nextToken(); // Function
        			tmp = st.nextToken(); // "functionname"
					boolean endString = false;
					if (tmp.endsWith("\"")) {
						endString = true;
					}
					String value = tmp.replaceAll("\"","");
					while (st.hasMoreTokens() && !endString) {
        				tmp = st.nextToken(); // "value"
						if (tmp.endsWith("\"")) {
							endString = true;
							tmp = tmp.replaceAll("\"","");
						}
						value = value + " " + tmp;
					}
					getMetaData().put("Selected Function" + fileIndex, value);
					this.selectedFunction = value;
					metricName = metricName + value + " ";
				} else if (inputString.startsWith("Begin Time")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Begin
        			tmp = st.nextToken(); // Time
        			tmp = st.nextToken(); // value, microseconds
					getMetaData().put("Begin Time" + fileIndex, tmp);
					try {
						//beginTime = 
							nfDLocal.parse(tmp).doubleValue();
					} catch (ParseException pe) {System.err.println("Error parsing: " + tmp);}
        			tmp = st.nextToken(); // End
        			tmp = st.nextToken(); // Time
        			tmp = st.nextToken(); // value, microseconds
					getMetaData().put("End Time" + fileIndex, tmp);
					try {
						//endTime = 
							nfDLocal.parse(tmp).doubleValue();
					} catch (ParseException pe) {System.err.println("Error parsing: " + tmp);}
        			tmp = st.nextToken(); // Duration
        			tmp = st.nextToken(); // value, microseconds
					getMetaData().put("Duration" + fileIndex, tmp);
					try {
						// convert from nanoseconds to microseconds
						duration = nfDLocal.parse(tmp).doubleValue() * 0.001;
						// convert from microseconds to percent
						durationMicrosecondsPercent = duration* 0.01;
					} catch (ParseException pe) {System.err.println("Error parsing: " + tmp);}
				} else if (inputString.startsWith("Control Window")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Control
        			tmp = st.nextToken(); // Window
        			tmp = st.nextToken(); // "value"
					boolean endString = false;
					if (tmp.endsWith("\"")) {
						endString = true;
					}
					String value = tmp.replaceAll("\"","");
					while (st.hasMoreTokens() && !endString) {
        				tmp = st.nextToken(); // "value"
						if (tmp.endsWith("\"")) {
							endString = true;
							tmp = tmp.replaceAll("\"","");
						}
						value = value + " " + tmp;
					}
					getMetaData().put("Control Window" + fileIndex, value);
					metricName = metricName + value + " ";
				} else if (inputString.startsWith("Data Window")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Data
        			tmp = st.nextToken(); // Window
        			tmp = st.nextToken(); // "value"
					boolean endString = false;
					if (tmp.endsWith("\"")) {
						endString = true;
					}
					String value = tmp.replaceAll("\"","");
					while (st.hasMoreTokens() && !endString) {
        				tmp = st.nextToken(); // "value"
						if (tmp.endsWith("\"")) {
							endString = true;
							tmp = tmp.replaceAll("\"","");
						}
						value = value + " " + tmp;
					}
					getMetaData().put("Data Window" + fileIndex, value);
					metricName = metricName + value + " ";
				} else if (inputString.startsWith("Window name")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Data
        			tmp = st.nextToken(); // Window
        			tmp = st.nextToken(); // "value"
					boolean endString = false;
					if (tmp.endsWith("\"")) {
						endString = true;
					}
					String value = tmp.replaceAll("\"","");
					//String newMetric = null;
					while (st.hasMoreTokens() && !endString) {
        				tmp = st.nextToken(); // "value"
						if (tmp.endsWith("\"")) {
							endString = true;
							tmp = tmp.replaceAll("\"","");
						}
						value = value + " " + tmp;
						if (tmp.startsWith("(") && tmp.endsWith(")")) {
							shortMetric = new String(tmp.substring(1, tmp.length()-1));
						}
					}
					getMetaData().put("Window name" + fileIndex, value);
				} else if (inputString.startsWith("Config File")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Data
        			tmp = st.nextToken(); // Window
        			tmp = st.nextToken(); // "value"
					boolean endString = false;
					if (tmp.endsWith("\"")) {
						endString = true;
					}
					String value = tmp.replaceAll("\"","");
					while (st.hasMoreTokens() && !endString) {
        				tmp = st.nextToken(); // "value"
						if (tmp.endsWith("\"")) {
							endString = true;
							tmp = tmp.replaceAll("\"","");
						}
						value = value + " " + tmp;
						if (tmp.equalsIgnoreCase("inclusive")) {
							doingInclusive = true;
						}
					}
					getMetaData().put("Config File" + fileIndex, value);
				} else if (inputString.startsWith("Extra Control Window")) {
        			StringTokenizer st = new StringTokenizer(inputString, " \t\n\r:");
        			tmp = st.nextToken(); // Extra
        			tmp = st.nextToken(); // Control
        			tmp = st.nextToken(); // Window
        			tmp = st.nextToken(); // "value"
					boolean endString = false;
					if (tmp.endsWith("\"")) {
						endString = true;
					}
					String value = tmp.replaceAll("\"","");
					while (st.hasMoreTokens() && !endString) {
        				tmp = st.nextToken(); // "value"
						if (tmp.endsWith("\"")) {
							endString = true;
							tmp = tmp.replaceAll("\"","");
						}
						value = value + " " + tmp;
					}
					getMetaData().put("Extra Control Window" + fileIndex, value);
					metricName = metricName + value + " ";
        			tmp = st.nextToken(); // Fixed
        			tmp = st.nextToken(); // Value
        			tmp = st.nextToken(); // "value"
					endString = false;
					if (tmp.endsWith("\"")) {
						endString = true;
					}
					value = tmp.replaceAll("\"","");
					while (st.hasMoreTokens() && !endString) {
        				tmp = st.nextToken(); // "value"
						if (tmp.endsWith("\"")) {
							endString = true;
							tmp = tmp.replaceAll("\"","");
						}
						value = value + " " + tmp;
					}
					getMetaData().put("Fixed Value" + fileIndex, value);
					metricName = metricName + value + " ";
				} else if (inputString.trim().length() == 0) {
					// there are two blank lines after the global section.
					break;
				} else { // anything else
					// ignore this line
				}
			}
			metricName = metricName.trim();
		} catch (IOException e) {
			System.out.println(e.getMessage());
			e.printStackTrace();
		}
		return;
	}
}