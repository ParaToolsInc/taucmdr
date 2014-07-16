package edu.uoregon.tau.perfdmf;

import java.util.*;

import edu.uoregon.tau.common.MetaDataMap;
import edu.uoregon.tau.common.TauRuntimeException;

/**
 * This class represents a Thread.  It contains an array of FunctionProfiles and 
 * UserEventProfiles as well as maximum data (e.g. max exclusive value for all functions on 
 * this thread). 
 *  
 * <P>CVS $Id: Thread.java,v 1.19 2010/05/14 19:42:18 amorris Exp $</P>
 * @author	Robert Bell, Alan Morris
 * @version	$Revision: 1.19 $
 * @see		Node
 * @see		Context
 * @see		FunctionProfile
 * @see		UserEventProfile
 */
public class Thread implements Comparable<Thread> {

    private int nodeID, contextID, threadID;
    private List<FunctionProfile> functionProfiles = new ArrayList<FunctionProfile>();
    private Map<Integer, UserEventProfile> userEventProfiles = new HashMap<Integer, UserEventProfile>();
    private boolean trimmed;
    private boolean relationsBuilt;
    private int numMetrics;

    //private Hashtable foo = new Hashtable();
    
    public static final int MEAN = -1;
    public static final int TOTAL = -2;
    public static final int STDDEV = -3;
    public static final int MIN = -4;
    public static final int MAX = -5;
    public static final int MEAN_ALL = -6;
    public static final int STDDEV_ALL = -7;

    private List<Snapshot> snapshots = new ArrayList<Snapshot>();
//    private Map<String,String> metaData = new TreeMap<String,String>();
    private MetaDataMap metaData = null;

    /**
	 * @param metaData the metaData to set
	 */
	public void setMetaData(MetaDataMap metaData) {
		this.metaData = metaData;
	}

	private boolean firstSnapshotFound;

    // two dimensional, snapshots x metrics
    private ThreadData[][] threadData;

    private long startTime;
    private DataSource dataSource;

    private static class ThreadData {

        public double maxNumCalls;
        public double maxNumSubr;

        public double maxInclusive;
        public double maxInclusivePercent;
        public double maxInclusivePerCall;
        public double maxExclusive;
        public double maxExclusivePercent;
        public double maxExclusivePerCall;

        public double percentDivider;
    }

    public Thread(int nodeID, int contextID, int threadID, int numMetrics, DataSource dataSource) {
        numMetrics = Math.max(numMetrics, 1);
        this.nodeID = nodeID;
        this.contextID = contextID;
        this.threadID = threadID;
        //maxData = new double[numMetrics * METRIC_SIZE];
        this.numMetrics = numMetrics;
        this.dataSource = dataSource;
        if (dataSource == null) {
            throw new TauRuntimeException("Error: dataSource should never be null in Thread constructor");
        }

        recreateData();

        // create the first snapshot
        Snapshot snapshot = new Snapshot("", snapshots.size());
        snapshots.add(snapshot);
    }

    public String toString() {
        if (nodeID == MEAN) {
            return "Mean";
        }
        if (nodeID == TOTAL) {
            return "Total";
        }
        if (nodeID == STDDEV) {
            return "Standard Deviation";
        }
        if (nodeID == MIN) {
            return "Min";
        }
        if (nodeID == MAX) {
            return "Max";
        }
        if (nodeID == MEAN_ALL) {
            return "Mean, All Threads";
        }
        if (nodeID == STDDEV_ALL) {
            return "Standard Deviation, All Threads";
        }
        return "n,c,t " + nodeID + "," + contextID + "," + threadID;
    }

    public int getNodeID() {
        return nodeID;
    }

    public int getContextID() {
        return contextID;
    }

    public int getThreadID() {
        return threadID;
    }

    public int getNumMetrics() {
        return numMetrics;
    }

    public void addMetric() {
        numMetrics++;

        recreateData();

        for (Iterator<FunctionProfile> it = getFunctionProfiles().iterator(); it.hasNext();) {
            FunctionProfile fp = it.next();
            if (fp != null) { // fp == null would mean this thread didn't call this function
                fp.addMetric();
            }
        }
    }

    public Snapshot addSnapshot(String name) {
        if (!firstSnapshotFound) {
            firstSnapshotFound = true;
            Snapshot snapshot = snapshots.get(0);
            snapshot.setName(name);
            return snapshot;
        }
        Snapshot snapshot = new Snapshot(name, snapshots.size());
        snapshots.add(snapshot);

        if (snapshots.size() > 1) {
            for (Iterator<FunctionProfile> e6 = functionProfiles.iterator(); e6.hasNext();) {
                FunctionProfile fp = e6.next();
                if (fp != null) { // fp == null would mean this thread didn't call this function
                    fp.addSnapshot();
                }
            }
            for (Iterator<UserEventProfile> it = userEventProfiles.values().iterator(); it.hasNext();) {
                UserEventProfile uep = it.next();
                if (uep != null) {
                    uep.addSnapshot();
                }
            }
        }

        recreateData();
        return snapshot;
    }

    public void addSnapshots(int max) {
        firstSnapshotFound = true;
        while (snapshots.size() < max) {
            addSnapshot("UNKNOWN");
        }
    }

    private void recreateData() {
        threadData = new ThreadData[getNumSnapshots()][getNumMetrics()];
        for (int s = 0; s < getNumSnapshots(); s++) {
            for (int m = 0; m < getNumMetrics(); m++) {
                threadData[s][m] = new ThreadData();
            }
        }
    }

    public List<Snapshot> getSnapshots() {
        return snapshots;
    }

    public int getNumSnapshots() {
        return Math.max(1, snapshots.size());
    }

    public void addFunctionProfile(FunctionProfile fp) {
        int id = fp.getFunction().getID();
        // increase the size of the functionProfiles list if necessary
        while (id >= functionProfiles.size()) {
            functionProfiles.add(null);
        }

        functionProfiles.set(id, fp);
        fp.setThread(this);
    }

    public void deleteFunctionProfile(FunctionProfile fp) {
        int id = fp.getFunction().getID();
        functionProfiles.set(id, null);
    }

    public void addUserEventProfile(UserEventProfile uep) {
        int id = uep.getUserEvent().getID();
        // increase the size of the userEventProfiles list if necessary
        userEventProfiles.put(new Integer(id), uep);

    }

    public FunctionProfile getFunctionProfile(Function function) {
        if ((functionProfiles != null) && (function.getID() < functionProfiles.size())) {
            return functionProfiles.get(function.getID());
        }
        return null;
    }

    public FunctionProfile getOrCreateFunctionProfile(Function function, int numMetrics) {
        FunctionProfile fp = getFunctionProfile(function);
        if (fp == null) {
            fp = new FunctionProfile(function, numMetrics);
            addFunctionProfile(fp);
            return fp;
        } else {
            return fp;
        }
    }

    public List<FunctionProfile> getFunctionProfiles() {
        return functionProfiles;
    }

    public Iterator<FunctionProfile> getFunctionProfileIterator() {
        return functionProfiles.iterator();
    }

    public UserEventProfile getUserEventProfile(UserEvent userEvent) {
        return userEventProfiles.get(new Integer(userEvent.getID()));
    }

    public Iterator<UserEventProfile> getUserEventProfiles() {
        return userEventProfiles.values().iterator();
    }

    // Since per thread callpath relations are built on demand, the following four functions tell whether this
    // thread's callpath information has been set yet.  This way, we only compute it once.
    public void setTrimmed(boolean b) {
        trimmed = b;
    }

    public boolean trimmed() {
        return trimmed;
    }

    public void setRelationsBuilt(boolean b) {
        relationsBuilt = b;
    }

    public boolean relationsBuilt() {
        return relationsBuilt;
    }

    public int compareTo(Thread obj) {
        return threadID -  obj.getThreadID();
    }

    public void setThreadData(int metric) {
        setThreadValues(metric, metric, 0, getNumSnapshots() - 1);
    }

    public void setThreadDataAllMetrics() {
        setThreadValues(0, this.getNumMetrics() - 1, 0, getNumSnapshots() - 1);
    }

    // compute max values and percentages for threads (not mean/total)
    private void setThreadValues(int startMetric, int endMetric, int startSnapshot, int endSnapshot) {

        // the recreateData() call wipes out all the threadData structures, so we have to recreate all of them for now.
        startMetric = 0;
        endMetric = getNumMetrics() - 1;

        if (getMetaData() != null) {
	        String startString = (String) getMetaData().get("Starting Timestamp");
	        if (startString != null) {
	            setStartTime(Long.parseLong(startString));
	        }
        }

        for (int snapshot = startSnapshot; snapshot <= endSnapshot; snapshot++) {
            for (int metric = startMetric; metric <= endMetric; metric++) {
                ThreadData data = threadData[snapshot][metric];
                double maxInclusive = 0;
                double maxExclusive = 0;
                double maxInclusivePerCall = 0;
                double maxExclusivePerCall = 0;
                double maxNumCalls = 0;
                double maxNumSubr = 0;

                for (Iterator<FunctionProfile> it = this.getFunctionProfileIterator(); it.hasNext();) {
                    FunctionProfile fp = it.next();
                    if (fp == null) {
                        continue;
                    }
                    if (fp.getFunction().isPhase()) {
                        maxExclusive = Math.max(maxExclusive, fp.getInclusive(snapshot, metric));
                        maxExclusivePerCall = Math.max(maxExclusivePerCall, fp.getInclusivePerCall(snapshot, metric));
                    } else {
                        maxExclusive = Math.max(maxExclusive, fp.getExclusive(snapshot, metric));
                        maxExclusivePerCall = Math.max(maxExclusivePerCall, fp.getExclusivePerCall(snapshot, metric));
                    }
                    maxInclusive = Math.max(maxInclusive, fp.getInclusive(snapshot, metric));
                    maxInclusivePerCall = Math.max(maxInclusivePerCall, fp.getInclusivePerCall(snapshot, metric));
                    maxNumCalls = Math.max(maxNumCalls, fp.getNumCalls(snapshot));
                    maxNumSubr = Math.max(maxNumSubr, fp.getNumSubr(snapshot));
                }

                data.maxExclusive = maxExclusive;
                data.maxInclusive = maxInclusive;
                data.maxExclusivePerCall = maxExclusivePerCall;
                data.maxInclusivePerCall = maxInclusivePerCall;
                data.maxNumCalls = maxNumCalls;
                data.maxNumSubr = maxNumSubr;

                // Note: Assumption is made that the max inclusive value is the value required to calculate
                // percentage (ie, divide by). Thus, we are assuming that the sum of the exclusive
                // values is equal to the max inclusive value. This is a reasonable assumption. This also gets
                // us out of sticky situations when call path data is present (this skews attempts to calculate
                // the total exclusive value unless checks are made to ensure that we do not 
                // include call path objects).
                if (this.getNodeID() >= 0) { // don't do this for mean/total
                    data.percentDivider = data.maxInclusive / 100.0;
                }

                double maxInclusivePercent = 0;
                double maxExclusivePercent = 0;
                for (Iterator<FunctionProfile> it = this.getFunctionProfileIterator(); it.hasNext();) {
                    FunctionProfile fp = it.next();
                    if (fp == null) {
                        continue;
                    }
                    maxExclusivePercent = Math.max(maxExclusivePercent, fp.getExclusivePercent(snapshot, metric));
                    maxInclusivePercent = Math.max(maxInclusivePercent, fp.getInclusivePercent(snapshot, metric));
                }

                data.maxExclusivePercent = maxExclusivePercent;
                data.maxInclusivePercent = maxInclusivePercent;
            }
        }
    }

    public MetaDataMap getMetaData() {
    	if (metaData == null) {
    		metaData = new MetaDataMap();
    	}
        return metaData;
    }

    public double getMaxInclusive(int metric, int snapshot) {
        if (snapshot == -1) {
            snapshot = getNumSnapshots() - 1;
        }
        return threadData[snapshot][metric].maxInclusive;
    }

    public double getMaxExclusive(int metric, int snapshot) {
        return threadData[snapshot][metric].maxExclusive;
    }

    public double getMaxInclusivePercent(int metric, int snapshot) {
        return threadData[snapshot][metric].maxInclusivePercent;
    }

    public double getMaxExclusivePercent(int metric, int snapshot) {
        return threadData[snapshot][metric].maxExclusivePercent;
    }

    public double getMaxInclusivePerCall(int metric, int snapshot) {
        return threadData[snapshot][metric].maxInclusivePerCall;
    }

    public double getMaxExclusivePerCall(int metric, int snapshot) {
        return threadData[snapshot][metric].maxExclusivePerCall;
    }

    public void setPercentDivider(int metric, int snapshot, double divider) {
        threadData[snapshot][metric].percentDivider = divider;
    }

    public double getPercentDivider(int metric, int snapshot) {
        //double val = threadData[snapshot][metric].percentDivider;
        return threadData[snapshot][metric].percentDivider;
    }

    public double getMaxNumCalls(int snapshot) {
        return threadData[snapshot][0].maxNumCalls;
    }

    public double getMaxNumSubr(int snapshot) {
        return threadData[snapshot][0].maxNumSubr;
    }

    public long getStartTime() {
        return startTime;
    }

    public void setStartTime(long startTime) {
        this.startTime = startTime;
    }

    public DataSource getDataSource() {
        return dataSource;
    }

}