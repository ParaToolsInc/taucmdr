/**
 * 
 */
package edu.uoregon.tau.perfexplorer.glue.test;

import java.util.List;
import java.util.Map;

import junit.framework.TestCase;
import edu.uoregon.tau.perfdmf.Trial;
import edu.uoregon.tau.perfexplorer.glue.AbstractResult;
import edu.uoregon.tau.perfexplorer.glue.PerformanceAnalysisOperation;
import edu.uoregon.tau.perfexplorer.glue.PerformanceResult;
import edu.uoregon.tau.perfexplorer.glue.TopXEvents;
import edu.uoregon.tau.perfexplorer.glue.TrialResult;
import edu.uoregon.tau.perfexplorer.glue.Utilities;

/**
 * @author khuck
 *
 */
public class TopXEventsTest extends TestCase {

	/**
	 * @param arg0
	 */
	public TopXEventsTest(String arg0) {
		super(arg0);
	}

	/**
	 * Test method for {@link edu.uoregon.tau.perfexplorer.glue.TopXEvents#processData()}.
	 */
	public final void testProcessData() {
		Utilities.setSession("perigtc");
		Trial trial = Utilities.getTrial("GTC", "ocracoke-O2", "64");
		PerformanceResult result = new TrialResult(trial);
		boolean doingMean = false;
//		PerformanceResult result = new TrialMeanResult(trial);
//		PerformanceResult result = new TrialTotalResult(trial);
		for (String metric : result.getMetrics()) {
			System.out.println("\t--- EXCLUSIVE --");
			PerformanceAnalysisOperation top10 = new TopXEvents(result, metric, AbstractResult.EXCLUSIVE, 10);
			List<PerformanceResult> outputs = top10.processData();
			for (PerformanceResult output : outputs) {
				if (doingMean)
					assertEquals(10,output.getEvents().size());
				Map<String, Double> sorted = output.getSortedByValue(metric, AbstractResult.EXCLUSIVE, false);
				for (String event : sorted.keySet()) {
					System.out.println(event + " " + sorted.get(event));
				}
			}
			System.out.println("\t--- INCLUSIVE --");
			top10 = new TopXEvents(result, metric, AbstractResult.INCLUSIVE, 10);
			outputs = top10.processData();
			for (PerformanceResult output : outputs) {
				if (doingMean) 
					assertEquals(10,output.getEvents().size());
				Map<String, Double> sorted = output.getSortedByValue(metric, AbstractResult.INCLUSIVE, false);
				for (String event : sorted.keySet()) {
					System.out.println(event + " " + sorted.get(event));
				}
			}
			System.out.println("\t--- CALLS --");
			top10 = new TopXEvents(result, null, AbstractResult.CALLS, 10);
			outputs = top10.processData();
			for (PerformanceResult output : outputs) {
				if (doingMean) 
					assertEquals(10,output.getEvents().size());
				Map<String, Double> sorted = output.getSortedByValue(metric, AbstractResult.CALLS, false);
				for (String event : sorted.keySet()) {
					System.out.println(event + " " + sorted.get(event));
				}
			}
			System.out.println("\t--- SUBROUTINES ---");
			top10 = new TopXEvents(result, null, AbstractResult.SUBROUTINES, 10);
			outputs = top10.processData();
			for (PerformanceResult output : outputs) {
				if (doingMean) 
					assertEquals(10,output.getEvents().size());
				Map<String, Double> sorted = output.getSortedByValue(metric, AbstractResult.SUBROUTINES, false);
				for (String event : sorted.keySet()) {
					System.out.println(event + " " + sorted.get(event));
				}
			}
		}
	}

}
