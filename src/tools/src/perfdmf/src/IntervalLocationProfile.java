package edu.uoregon.tau.perfdmf;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.List;
import java.util.Vector;

import edu.uoregon.tau.perfdmf.database.DB;

/**
 * Holds all the data for a interval location profile in the database.
 * This object is returned by the DataSession class and all of its subtypes.
 * The IntervalLocationProfile contains all the information associated with
 * an interval_event location instance from which the TAU performance data has been generated.
 * A interval_event location is associated with one node, context, thread, interval_event, trial, 
 * experiment and application, and has data for all selected metrics in it.
 * <p>
 * An IntervalLocationProfile has information
 * related to one particular interval_event location in the trial, including the ID of the interval_event,
 * the node, context and thread that identify the location, and the data collected for this
 * location, such as inclusive time, exclusive time, etc.  If there are multiple metrics recorded
 * in the trial, and no metric filter is applied when the IntervalLocationProfile is requested, then
 * all metric data for this location will be returned.  The index of the metric needs to be
 * passed in to get data for a particular metric.  If there is only one metric, then no metric
 * index need be passed in.
 *
 * <P>CVS $Id: IntervalLocationProfile.java,v 1.6 2009/02/19 20:53:44 amorris Exp $</P>
 * @author	Kevin Huck, Robert Bell
 * @version	0.1
 * @since	0.1
 * @see		DataSession#getIntervalEventData
 * @see		DataSession#setIntervalEvent
 * @see		DataSession#setNode
 * @see		DataSession#setContext
 * @see		DataSession#setThread
 * @see		DataSession#setMetric
 * @see		IntervalEvent
 */
public class IntervalLocationProfile extends Object {
    private int node;
    private int context;
    private int thread;
    private int eventID;
    private double[] doubleList;
    private double numCalls;
    private double numSubroutines;
    private static int fieldCount = 5;

    /**
     * Base constructor.
     *
     */
    public IntervalLocationProfile() {
        super();
        doubleList = new double[fieldCount];
    }

    /**
     * Alternative constructor.
     *
     * @param metricCount specifies how many metrics are expected for this trial.
     */
    public IntervalLocationProfile(int metricCount) {
        super();
        int trueSize = metricCount * fieldCount;
        doubleList = new double[trueSize];
    }

    /**
     * Returns the node for this data location.
     *
     * @return the node index.
     */
    public int getNode() {
        return this.node;
    }

    /**
     * Returns the context for this data location.
     *
     * @return the context index.
     */
    public int getContext() {
        return this.context;
    }

    /**
     * Returns the thread for this data location.
     *
     * @return the thread index.
     */
    public int getThread() {
        return this.thread;
    }

    /**
     * Returns the unique ID for the interval_event that owns this data
     *
     * @return the eventID.
     * @see		IntervalEvent
     */
    public int getIntervalEventID() {
        return this.eventID;
    }

    /**
     * Returns the inclusive percentage value for the specified metric at this location.
     *
     * @param	metricIndex the index of the metric desired.
     * @return	the inclusive percentage.
     */
    public double getInclusivePercentage(int metricIndex) {
        return getDouble(metricIndex, 0);
    }

    /**
     * Returns the inclusive percentage value for the first (or only) metric at this location.
     *
     * @return	the inclusive percentage.
     */
    public double getInclusivePercentage() {
        return getDouble(0, 0);
    }

    /**
     * Returns the inclusive value for the specified metric at this location.
     *
     * @param	metricIndex the index of the metric desired.
     * @return	the inclusive percentage.
     */
    public double getInclusive(int metricIndex) {
        return getDouble(metricIndex, 1);
    }

    /**
     * Returns the inclusive value for the first (or only) metric at this location.
     *
     * @return	the inclusive percentage.
     */
    public double getInclusive() {
        return getDouble(0, 1);
    }

    /**
     * Returns the exclusive percentage value for the specified metric at this location.
     *
     * @param	metricIndex the index of the metric desired.
     * @return	the exclusive percentage.
     */
    public double getExclusivePercentage(int metricIndex) {
        return getDouble(metricIndex, 2);
    }

    /**
     * Returns the exclusive percentage value for the first (or only) metric at this location.
     *
     * @return	the exclusive percentage.
     */
    public double getExclusivePercentage() {
        return getDouble(0, 2);
    }

    /**
     * Returns the exclusive value for the specified metric at this location.
     *
     * @param	metricIndex the index of the metric desired.
     * @return	the exclusive percentage.
     */
    public double getExclusive(int metricIndex) {
        return getDouble(metricIndex, 3);
    }

    /**
     * Returns the exclusive value for the first (or only) metric at this location.
     *
     * @return	the exclusive percentage.
     */
    public double getExclusive() {
        return getDouble(0, 3);
    }

    /**
     * Returns the inclusive value per call for the specified metric at this location.
     *
     * @param	metricIndex the index of the metric desired.
     * @return	the inclusive percentage.
     */
    public double getInclusivePerCall(int metricIndex) {
        return getDouble(metricIndex, 4);
    }

    /**
     * Returns the inclusive per call value for the first (or only) metric at this location.
     *
     * @return	the inclusive percentage.
     */
    public double getInclusivePerCall() {
        return getDouble(0, 4);
    }

    /**
     * Returns the number of calls to this interval_event at this location.
     *
     * @return	the number of calls.
     */
    public double getNumCalls() {
        return this.numCalls;
    }

    /**
     * Returns the number of subroutines for this interval_event at this location.
     *
     * @return	the number of subroutines.
     */
    public double getNumSubroutines() {
        return this.numSubroutines;
    }

    private void incrementStorage() {
        int currentLength = doubleList.length;
        double[] newArray = new double[currentLength + fieldCount];
        for (int i = 0; i < currentLength; i++) {
            newArray[i] = doubleList[i];
        }
        doubleList = newArray;
    }

    private void insertDouble(int dataValueLocation, int offset, double inDouble) {
        int actualLocation = (dataValueLocation * fieldCount) + offset;
        if (actualLocation >= doubleList.length)
            incrementStorage();
        try {
            doubleList[actualLocation] = inDouble;
        } catch (Exception e) {
            // do something
        }
    }

    private double getDouble(int dataValueLocation, int offset) {
        int actualLocation = (dataValueLocation * fieldCount) + offset;
        try {
            return doubleList[actualLocation];
        } catch (Exception e) {
            // do something
        }
        return -1;
    }

    /**
     * Sets the node of the current location that this data object represents.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	node the node for this location.
     */
    public void setNode(int node) {
        this.node = node;
    }

    /**
     * Sets the context of the current location that this data object represents.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	context the context for this location.
     */
    public void setContext(int context) {
        this.context = context;
    }

    /**
     * Sets the thread of the current location that this data object represents.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	thread the thread for this location.
     */
    public void setThread(int thread) {
        this.thread = thread;
    }

    /**
     * Sets the unique interval_event ID for the interval_event at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	eventID a unique interval_event ID.
     */
    public void setIntervalEventID(int eventID) {
        this.eventID = eventID;
    }

    /**
     * Sets the inclusive percentage value for the specified metric at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	metricIndex the index of the metric
     * @param	inclusivePercentage the inclusive percentage value at this location
     */
    public void setInclusivePercentage(int metricIndex, double inclusivePercentage) {
        insertDouble(metricIndex, 0, inclusivePercentage);
    }

    /**
     * Sets the inclusive value for the specified metric at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	metricIndex the index of the metric
     * @param	inclusive the inclusive value at this location
     */
    public void setInclusive(int metricIndex, double inclusive) {
        insertDouble(metricIndex, 1, inclusive);
    }

    /**
     * Sets the exclusive percentage value for the specified metric at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	metricIndex the index of the metric
     * @param	exclusivePercentage the exclusive percentage value at this location
     */
    public void setExclusivePercentage(int metricIndex, double exclusivePercentage) {
        insertDouble(metricIndex, 2, exclusivePercentage);
    }

    /**
     * Sets the exclusive value for the specified metric at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	metricIndex the index of the metric
     * @param	exclusive the exclusive value at this location
     */
    public void setExclusive(int metricIndex, double exclusive) {
        insertDouble(metricIndex, 3, exclusive);
    }

    /**
     * Sets the inclusive per call value for the specified metric at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	metricIndex the index of the metric
     * @param	inclusivePerCall the inclusive per call value at this location
     */
    public void setInclusivePerCall(int metricIndex, double inclusivePerCall) {
        insertDouble(metricIndex, 4, inclusivePerCall);
    }

    /**
     * Sets the number of times that the interval_event was called at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	numCalls the number of times the interval_event was called
     */
    public void setNumCalls(double numCalls) {
        this.numCalls = numCalls;
    }

    /**
     * Sets the number of subroutines the interval_event has at this location.
     * <i> NOTE: This method is used by the DataSession object to initialize
     * the object.  Not currently intended for use by any other code.</i>
     *
     * @param	numSubroutines the number of subroutines the interval_event has at this location.
     */
    public void setNumSubroutines(double numSubroutines) {
        this.numSubroutines = numSubroutines;
    }



    public void saveMeanSummary(DB db, int intervalEventID, Hashtable<Integer, Integer> newMetHash, int saveMetricIndex)
            throws SQLException {
        // get the IntervalEvent details
        int i = 0;
        Integer newMetricID = newMetHash.get(new Integer(i));
        while (newMetricID != null) {
            if (saveMetricIndex < 0 || i == saveMetricIndex) {
                PreparedStatement statement = null;
                if (db.getDBType().compareTo("oracle") == 0) {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_mean_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, excl, call, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                } else if (db.getDBType().compareTo("derby") == 0) {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_mean_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, exclusive, num_calls, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                } else if (db.getDBType().compareTo("mysql") == 0) {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_mean_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, exclusive, `call`, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                } else {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_mean_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, exclusive, call, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                }
                
                statement.setInt(1, intervalEventID);
                statement.setInt(2, newMetricID.intValue());
                statement.setDouble(3, getInclusivePercentage(i));
                statement.setDouble(4, getInclusive(i));
                statement.setDouble(5, getExclusivePercentage(i));
                statement.setDouble(6, getExclusive(i));
                statement.setDouble(7, getNumCalls());
                statement.setDouble(8, getNumSubroutines());
                statement.setDouble(9, getInclusivePerCall(i));
                statement.executeUpdate();
                statement.close();
            }
            newMetricID = newMetHash.get(new Integer(++i));
        }
    }

    public void saveTotalSummary(DB db, int intervalEventID, Hashtable<Integer, Integer> newMetHash, int saveMetricIndex)
            throws SQLException {
        // get the interval_event details
        int i = 0;
        Integer newMetricID = newMetHash.get(new Integer(i));
        while (newMetricID != null) {
            if (saveMetricIndex < 0 || i == saveMetricIndex) {
                PreparedStatement statement = null;

                if (db.getDBType().compareTo("oracle") == 0) {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_total_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, excl, call, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                } else if (db.getDBType().compareTo("derby") == 0) {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_total_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, exclusive, num_calls, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                } else if (db.getDBType().compareTo("mysql") == 0) {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_total_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, exclusive, `call`, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                } else {
                    statement = db.prepareStatement("INSERT INTO "
                            + db.getSchemaPrefix()
                            + "interval_total_summary (interval_event, metric, inclusive_percentage, inclusive, exclusive_percentage, exclusive, call, subroutines, inclusive_per_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                }
                statement.setInt(1, intervalEventID);
                statement.setInt(2, newMetricID.intValue());
                statement.setDouble(3, getInclusivePercentage(i));
                statement.setDouble(4, getInclusive(i));
                statement.setDouble(5, getExclusivePercentage(i));
                statement.setDouble(6, getExclusive(i));
                statement.setDouble(7, getNumCalls());
                statement.setDouble(8, getNumSubroutines());
                statement.setDouble(9, getInclusivePerCall(i));
                statement.executeUpdate();
                statement.close();
            }
            newMetricID = newMetHash.get(new Integer(++i));
        }
    }

    public static FunctionProfile getIntervalEventDetail(DB db, Function function, String whereClause)
            throws SQLException {
        // create a string to hit the database
        StringBuffer buf = new StringBuffer();
    	if (db.getSchemaVersion() > 0) {
    		buf.append("select tcd.timer_callpath, ");
    		buf.append("tv.inclusive_percent, tv.inclusive_value, ");
    		buf.append("tv.exclusive_percent, tv.exclusive_value, ");
    		buf.append("tcd.calls, tcd.subroutines, ");
    		buf.append("tv.metric from ");
    		buf.append(db.getSchemaPrefix() + "timer_value tv left outer join ");
    		buf.append(db.getSchemaPrefix() + "timer_call_data tcd on tv.timer_call_data = tcd.id ");
    		buf.append("left outer join " + db.getSchemaPrefix() + "thread h on tcd.thread = h.id ");
	        buf.append(whereClause);
	        if (whereClause.length() > 3) {
	        	buf.append(" and h.thread_index = -1 ");
	        } else {
	        	buf.append(" where h.thread_index = -1 ");
	        }
	        buf.append(" order by tcd.timer_callpath, tv.metric");
    	} else {
	        buf.append("select ms.interval_event, ");
	        buf.append("ms.inclusive_percentage, ms.inclusive, ");
	
	        if (db.getDBType().compareTo("oracle") == 0) {
	            buf.append("ms.exclusive_percentage, ms.excl, ");
	        } else {
	            buf.append("ms.exclusive_percentage, ms.exclusive, ");
	        }
	
	        if (db.getDBType().compareTo("derby") == 0) {
	            buf.append("ms.num_calls, ");
	        } else if (db.getDBType().compareTo("mysql") == 0) {
	            buf.append("ms.`call`, ");
	        } else {
	            buf.append("ms.call, ");
	        }
	        buf.append("ms.subroutines, ms.inclusive_per_call, ");
	        buf.append("ms.metric ");
	        buf.append("from " + db.getSchemaPrefix() + "interval_mean_summary ms ");
	        buf.append(whereClause);
	        buf.append(" order by ms.interval_event, ms.metric");
    	}
        // System.out.println(buf.toString());

        // get the results
        ResultSet resultSet = db.executeQuery(buf.toString());
        int metricIndex = 0;
        List<Double> inclusives = new ArrayList<Double>();
        List<Double> exclusives = new ArrayList<Double>();
        double calls = 0;
        double subroutines = 0;
        while (resultSet.next() != false) {
            inclusives.add(resultSet.getDouble(3));
            exclusives.add(resultSet.getDouble(5));
            calls = resultSet.getDouble(6);
            subroutines = resultSet.getDouble(7);
            metricIndex++;
        }
        resultSet.close();
        FunctionProfile eMS = new FunctionProfile(function, metricIndex);
        eMS.setNumCalls(calls);
        eMS.setNumSubr(subroutines);
        for (int j = 0 ; j < metricIndex ; j++) {
            eMS.setInclusive(j, inclusives.get(j));
            eMS.setExclusive(j, exclusives.get(j));
        }
        return eMS;
    }

}
