package edu.uoregon.tau.perfexplorer.server;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.StringTokenizer;

import edu.uoregon.tau.perfdmf.DatabaseAPI;
import edu.uoregon.tau.perfdmf.Metric;
import edu.uoregon.tau.perfdmf.database.DB;
import edu.uoregon.tau.perfexplorer.clustering.RawDataInterface;
import edu.uoregon.tau.perfexplorer.clustering.weka.AnalysisFactory;
import edu.uoregon.tau.perfexplorer.common.PerfExplorerException;
import edu.uoregon.tau.perfexplorer.common.PerfExplorerOutput;
import edu.uoregon.tau.perfexplorer.common.RMIPerfExplorerModel;
import edu.uoregon.tau.perfexplorer.common.TransformationType;

public class DataUtils {
	/**
	 * This method gets the raw performance data from the database.
	 * 
	 * @throws PerfExplorerException
	 */
	public static RawDataInterface getRawData (DatabaseAPI session, RMIPerfExplorerModel modelData) throws PerfExplorerException {
		//PerfExplorerServer server = 
			PerfExplorerServer.getServer();
		PerfExplorerOutput.print("Getting raw data...");
	    //int numRows = 0;
	    int numTotalThreads = 0;
	    int numEvents = 0;
	    int nodes = 0;
	    int contexts = 0;
	    int threads = 0;
	    RawDataInterface rawData = null;
	    double maximum = 0.0;
	    List<String> eventIDs = null;
	    String clusterType=modelData.getClusterValueType();
		//String clusterPerType="inclusive_percentage";

/* for TAUdb schema, do this query:

select count(tcdo.id) from timer_call_data tcdo inner join thread ho on tcdo.thread = ho.id inner join timer_callpath tcpo on tcdo.timer_callpath = tcpo.id where ho.node_rank > -1 and tcpo.id in (select tcp.id from timer_value tv inner join timer_call_data tcd on tv.timer_call_data = tcd.id inner join timer_callpath tcp on tcd.timer_callpath = tcp.id inner join thread h on tcd.thread = h.id where h.node_rank = -1 and h.trial = 78 and tv.metric = 215 and tv.exclusive_percent > 1.0 and tcp.parent is null);

*/
		
		PerfExplorerOutput.print("Getting constants...");
		try {
			DB db = session.db();
			
			if(clusterType.compareTo("inclusive")!=0){
				if (db.getDBType().compareTo("oracle") == 0) {
					clusterType="excl";
				}
				else{
					clusterType="exclusive";
				}
				//clusterPerType="exclusive_percentage";
			}
			
			PreparedStatement statement = null;
			// First, get the total number of rows we are expecting
			StringBuilder sql = new StringBuilder();
			
            if (db.getDBType().compareTo("oracle") == 0) {
                sql.append("select count(p.excl) ");
            } else {
                sql.append("select count(p.inclusive) ");
            }

			sql.append("from interval_event e ");
			sql.append("left outer join interval_location_profile p ");
			sql.append("on e.id = p.interval_event ");
			if (modelData.getDimensionReduction().equals(TransformationType.OVER_X_PERCENT)) {
				sql.append("inner join interval_mean_summary s ");
				sql.append("on e.id = s.interval_event and s.metric = p.metric ");
				sql.append("and s.exclusive_percentage > ");
				sql.append("" + modelData.getXPercent() + "");	
			//} else if (modelData.getCurrentSelection() instanceof Metric) {
				//sql.append("inner join interval_mean_summary s ");
				//sql.append("on e.id = s.interval_event and s.metric = p.metric ");
			}
			sql.append("where e.trial = ?");
			sql.append(" and (e.group_name is null or e.group_name not like '%TAU_CALLPATH%') ");
			if (modelData.getCurrentSelection() instanceof Metric) {
				sql.append(" and p.metric = ?");
			}
			statement = db.prepareStatement(sql.toString());
			statement.setInt(1, modelData.getTrial().getID());
			if (modelData.getCurrentSelection() instanceof Metric) {
				statement.setInt(2, ((Metric)(modelData.getCurrentSelection())).getID());
			}
			//PerfExplorerOutput.println(statement.toString());
			ResultSet results = statement.executeQuery();
			if (results.next() != false) {
				//numRows = results.getInt(1);
			}
			results.close();
			statement.close();

			if (modelData.getCurrentSelection() instanceof Metric) {
				// Next, get the event names, and count them
				sql = new StringBuilder();
				sql.append("select e.id, e.name from interval_event e ");
				if (modelData.getDimensionReduction().equals(TransformationType.OVER_X_PERCENT)) {
					sql.append("inner join interval_mean_summary s on ");
					sql.append("e.id = s.interval_event ");
					sql.append("and s.exclusive_percentage > ");
					sql.append("" + modelData.getXPercent() + "");
					sql.append(" where e.trial = ? ");
					if (modelData.getCurrentSelection() instanceof Metric) {
						sql.append(" and s.metric = ? ");
					}
				} else {
					sql.append("where e.trial = ?");
				}
			sql.append(" and (e.group_name is null or e.group_name not like '%TAU_CALLPATH%') ");
				sql.append(" order by 1");
				statement = db.prepareStatement(sql.toString());
				statement.setInt(1, modelData.getTrial().getID());
				if (modelData.getDimensionReduction().equals(TransformationType.OVER_X_PERCENT)) {
					if (modelData.getCurrentSelection() instanceof Metric) {
						statement.setInt(2, ((Metric)(modelData.getCurrentSelection())).getID());
					}
				}
				//PerfExplorerOutput.println(statement.toString());
				results = statement.executeQuery();
				numEvents = 0;
				eventIDs = new ArrayList<String>();
				while (results.next() != false) {
					numEvents++;
					eventIDs.add(shortName(results.getString(2)));
				}
				results.close();
				statement.close();
			} else {

				// Next, get the metric names, and count them
				sql = new StringBuilder();
				sql.append("select m.id, m.name from metric m ");
				sql.append("where m.trial = ?");
				sql.append(" order by 1");
				statement = db.prepareStatement(sql.toString());
				statement.setInt(1, modelData.getTrial().getID());
				//PerfExplorerOutput.println(statement.toString());
				results = statement.executeQuery();
				numEvents = 0;
				eventIDs = new ArrayList<String>();
				while (results.next() != false) {
					numEvents++;
					eventIDs.add(results.getString(2));
				}
				results.close();
				statement.close();
			}

			// get the number of threads
			sql = new StringBuilder();
			sql.append("select max(node), max(context), max(thread) ");
			sql.append("from interval_location_profile ");
			sql.append("inner join interval_event ");
			sql.append("on interval_event.id = interval_event where trial = ? ");
			if (modelData.getCurrentSelection() instanceof Metric) {
				sql.append(" and metric = ? ");
			}
			statement = db.prepareStatement(sql.toString());
			statement.setInt(1, modelData.getTrial().getID());
			if (modelData.getCurrentSelection() instanceof Metric) {
				statement.setInt(2, ((Metric)(modelData.getCurrentSelection())).getID());
			}
			//PerfExplorerOutput.println(statement.toString());
			results = statement.executeQuery();
			if (results.next() != false) {
				nodes = results.getInt(1) + 1;
				contexts = results.getInt(2) + 1;
				threads = results.getInt(3) + 1;
				numTotalThreads = nodes * contexts * threads;
			}
			results.close();
			statement.close();
		} catch (SQLException e) {
			String error = "ERROR: Couldn't the constant settings from the database!";
			System.err.println(error);
            System.err.println(e.getMessage());
			e.printStackTrace();
			throw new PerfExplorerException(error, e);
		}
		/*
		PerfExplorerOutput.println("\nnumRows: " + numRows);
		PerfExplorerOutput.println("numCenterRows: " + numCenterRows);
		PerfExplorerOutput.println("nodes: " + nodes);
		PerfExplorerOutput.println("contexts: " + contexts);
		PerfExplorerOutput.println("threads: " + threads);
		PerfExplorerOutput.println("numTotalThreads: " + numTotalThreads);
		PerfExplorerOutput.println("numEvents: " + numEvents);
		PerfExplorerOutput.println(" Done!");
		*/
		rawData = AnalysisFactory.createRawData("Cluster Test", eventIDs, numTotalThreads, numEvents, null);
		ResultSet results = null;
		int currentFunction = 0;
		int functionIndex = -1;
		int rowIndex = 0;
		int threadIndex = 0;
		maximum = 0.0;
		try {
			DB db = session.db();
			PreparedStatement statement = null;
			StringBuilder sql = new StringBuilder();
			if (modelData.getDimensionReduction().equals(TransformationType.OVER_X_PERCENT)) {
				sql.append("select e.id, (p.node*");
				sql.append(contexts * threads);
				sql.append(") + (p.context*");
				sql.append(threads);
                
				//TODO: This will request the data that gets used for clustering
//				if(clusterType.compareTo("inclusive")==0)
//				{
//					sql.append(") + p.thread as thread, p.metric as metric, p.inclusive/1000000, ");
//				}
//				else{
//                if (db.getDBType().compareTo("oracle") == 0) {
//                    sql.append(") + p.thread as thread, p.metric as metric, p.excl/1000000, ");
//                } else {
//                    sql.append(") + p.thread as thread, p.metric as metric, p.exclusive/1000000, ");
//                }}
				
				sql.append(") + p.thread as thread, p.metric as metric, p."+clusterType+"/1000000, ");
				
				sql.append("p.inclusive/1000000, s.inclusive_percentage, s.exclusive_percentage ");
				sql.append("from interval_event e ");
				sql.append("inner join interval_mean_summary s ");
				sql.append("on e.id = s.interval_event and (s.exclusive_percentage > ");
				sql.append(modelData.getXPercent());
				sql.append("or s.inclusive_percentage = 100.0) ");
				sql.append(" left outer join interval_location_profile p ");
				sql.append("on e.id = p.interval_event ");
				sql.append("and p.metric = s.metric where e.trial = ? ");
			} else {
				sql.append("select e.id, (p.node*" + (contexts * threads) + "");
				sql.append(") + (p.context*" + threads + "");
                
				//TODO: This will request the data that gets used for clustering
//				if(clusterType.compareTo("inclusive")==0)
//				{
//					sql.append(") + p.thread as thread, p.metric as metric, p.inclusive, ");
//				}
//				else{
//					if (db.getDBType().compareTo("oracle") == 0) {
//						sql.append(") + p.thread as thread, p.metric as metric, p.excl, ");
//					} else {
//						sql.append(") + p.thread as thread, p.metric as metric, p.exclusive, ");
//					}
//				}
				sql.append(") + p.thread as thread, p.metric as metric, p."+clusterType+", ");
				
				sql.append("p.inclusive/1000000, p.inclusive_percentage ");
				sql.append("from interval_event e ");
				sql.append("left outer join interval_location_profile p ");
				sql.append("on e.id = p.interval_event where e.trial = ? ");
			}
			if (modelData.getCurrentSelection() instanceof Metric) {
				sql.append(" and p.metric = ? ");
			}
			sql.append(" and (e.group_name is null or e.group_name not like '%TAU_CALLPATH%') ");
			sql.append(" order by 3,1,2 ");
			statement = db.prepareStatement(sql.toString());
			statement.setInt(1, modelData.getTrial().getID());
			if (modelData.getCurrentSelection() instanceof Metric) {
				statement.setInt(2, ((Metric)(modelData.getCurrentSelection())).getID());
			}
			//PerfExplorerOutput.println(statement.toString());
			results = statement.executeQuery();

			// if we are getting data for one metric, we are focussed on the events.
			// if we are getting data for all metrics, we are focussed on the metrics.
			int importantIndex = (modelData.getCurrentSelection() instanceof Metric) ? 1 : 3 ;

			// get the rows
			while (results.next() != false) {
				if (!(modelData.getDimensionReduction().equals(
					TransformationType.OVER_X_PERCENT)) || 
					(results.getDouble(7) > modelData.getXPercent())) {
					if (currentFunction != results.getInt(importantIndex)) {
						functionIndex++;
					}
					currentFunction = results.getInt(importantIndex);
					threadIndex = results.getInt(2);
					rawData.addValue(threadIndex, functionIndex, results.getDouble(4));
					if (maximum < results.getDouble(4))
						maximum = results.getDouble(4);
				} 
				// if this is the main method, save its values
				if (results.getDouble(6) == 100.0) {
					rawData.addMainValue(threadIndex, functionIndex, results.getDouble(5));
				}
				rowIndex++;
			}
			results.close();
			statement.close();
		} catch (SQLException e) {
			String error = "ERROR: Couldn't the raw data from the database!";
			System.err.println(error);
            System.err.println(e.getMessage());
			e.printStackTrace();
			throw new PerfExplorerException(error, e);
		} catch (ArrayIndexOutOfBoundsException e2) {
            System.err.println(e2.getMessage());
			e2.printStackTrace();
			PerfExplorerOutput.println("\ncurrentFunction: " + currentFunction);
			PerfExplorerOutput.println("functionIndex: " + functionIndex);
			PerfExplorerOutput.println("rowIndex: " + rowIndex);
			PerfExplorerOutput.println("threadIndex: " + threadIndex);
			System.exit(1);
		}
		PerfExplorerOutput.println(" Done!");
		return rawData;
	}

    public static String shortName(String longName) {
        String shorter = null;
		// strip off instrumentation info
    	StringTokenizer st = new StringTokenizer(longName, "[");
    	try {
        	shorter = st.nextToken();
        	if (shorter.length() < longName.length()) {
            	shorter = shorter.trim() + "()";
        	}
    	} catch (NoSuchElementException e) {
        	shorter = longName;
    	}
		// strip off parameters
    	st = new StringTokenizer(longName, "(");
    	try {
        	shorter = st.nextToken();
        	if (shorter.length() < longName.length()) {
            	shorter = shorter.trim() + "()";
        	}
    	} catch (NoSuchElementException e) {
        	shorter = longName;
    	}
		//System.out.println(longName + " is now: " + shorter);
        return shorter;
    }

}
