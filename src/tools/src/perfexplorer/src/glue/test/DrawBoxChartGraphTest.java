/**
 * 
 */
package edu.uoregon.tau.perfexplorer.glue.test;

import java.util.ArrayList;
import java.util.List;

import junit.framework.TestCase;
import edu.uoregon.tau.perfdmf.Trial;
import edu.uoregon.tau.perfexplorer.glue.AbstractResult;
import edu.uoregon.tau.perfexplorer.glue.DrawBoxChartGraph;
import edu.uoregon.tau.perfexplorer.glue.DrawGraph;
import edu.uoregon.tau.perfexplorer.glue.ExtractEventOperation;
import edu.uoregon.tau.perfexplorer.glue.ExtractMetricOperation;
import edu.uoregon.tau.perfexplorer.glue.PerformanceAnalysisOperation;
import edu.uoregon.tau.perfexplorer.glue.PerformanceResult;
import edu.uoregon.tau.perfexplorer.glue.TrialResult;
import edu.uoregon.tau.perfexplorer.glue.Utilities;

/**
 * @author khuck
 *
 */
public class DrawBoxChartGraphTest extends TestCase {

	/**
	 * Test method for {@link edu.uoregon.tau.perfexplorer.glue.DrawGraph#processData()}.
	 */
	public final void testProcessData() {
		Utilities.getClient();
		Utilities.setSession("perfdmf_test");
		// get the data
		Trial trial = Utilities.getTrial("gtc_bench", "jaguar.phases", "64");
		PerformanceResult result = new TrialResult(trial);
		
		// extract the phases
	    List<String>events = new ArrayList<String>();
	    for (String event : result.getEvents()) {
	        if (event.startsWith("Iteration   1") && event.contains("CHARGEI")) {
	            events.add(event);
	        }
	    }
	    PerformanceAnalysisOperation extractor = new ExtractEventOperation(result, events);
		PerformanceResult extracted = extractor.processData().get(0);
		
		// extract the metric
	    List<String>metrics = new ArrayList<String>();
        metrics.add("P_WALL_CLOCK_TIME");
	    PerformanceAnalysisOperation extractor2 = new ExtractMetricOperation(extracted, metrics);
		PerformanceResult extracted2 = extractor2.processData().get(0);

		DrawGraph grapher = new DrawBoxChartGraph(extracted2);
        grapher.setTitle("CHARGEI");
        grapher.setCategoryType(DrawGraph.EVENTNAME);
        grapher.setValueType(AbstractResult.INCLUSIVE);
        grapher.processData();
		try {
			java.lang.Thread.sleep(600000);
		} catch (Exception e) {
			System.err.println(e.getMessage());
		}
	}

}
