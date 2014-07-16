/**
 * 
 */
package edu.uoregon.tau.perfexplorer.glue.test;

import junit.framework.TestCase;
import edu.uoregon.tau.perfdmf.Trial;
import edu.uoregon.tau.perfexplorer.glue.DeriveMetricOperation;
import edu.uoregon.tau.perfexplorer.glue.PerformanceResult;
import edu.uoregon.tau.perfexplorer.glue.TrialResult;
import edu.uoregon.tau.perfexplorer.glue.Utilities;


/**
 * @author khuck
 *
 */
public class DeriveMetricOperationTest extends TestCase {

	/**
	 * Test method for {@link edu.uoregon.tau.perfexplorer.glue.DeriveMetricOperation#processData()}.
	 */
	public final void testProcessData() {
	    Utilities.setSession("perfdmf_test");
		Trial trial = Utilities.getTrial("gtc_bench", "superscaling.jaguar", "64");
		PerformanceResult result = new TrialResult(trial);
	    DeriveMetricOperation derive = new DeriveMetricOperation(result, "PAPI_FP_OPS", "P_WALL_CLOCK_TIME", DeriveMetricOperation.DIVIDE);
	    PerformanceResult output = derive.processData().get(0);
		for (String event : result.getEvents()) {
			for (Integer thread : result.getThreads()) {
				double tmp = result.getInclusive(thread, event, "P_WALL_CLOCK_TIME");
				assertEquals((tmp == 0.0 ? 0.0 : (result.getInclusive(thread, event, "PAPI_FP_OPS") / tmp)),
					output.getInclusive(thread, event, "PAPI_FP_OPS/P_WALL_CLOCK_TIME"));
				tmp = result.getExclusive(thread, event, "P_WALL_CLOCK_TIME");
				assertEquals((tmp == 0.0 ? 0.0 : (result.getExclusive(thread, event, "PAPI_FP_OPS") / tmp)),
					output.getExclusive(thread, event, "PAPI_FP_OPS/P_WALL_CLOCK_TIME"));
			}
		}
	}

}
