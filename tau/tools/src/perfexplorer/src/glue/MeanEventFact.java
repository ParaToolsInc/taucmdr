/**
 * 
 */
package edu.uoregon.tau.perfexplorer.glue;

import java.text.DecimalFormat;
import java.util.HashSet;
import java.util.Set;

import edu.uoregon.tau.perfexplorer.rules.RuleHarness;


/**
 * @author khuck
 *
 */
public class MeanEventFact {

	public static final int NONE = 0;
	public static final int BETTER = 1;
	public static final int WORSE = 2;
	public static final int HIGHER = 3;
	public static final int LOWER = 4;
	private int betterWorse = BETTER;
	private String metric = null;
	private String meaningfulMetricName = null;
	private double mainValue = 0.0;
	private double eventValue = 0.0;
	private double severity = 0.0;
	private String eventName = null;
	private String factType = null;
	
	/**
	 * 
	 */
	private MeanEventFact(String factType, int betterWorse, String metric, String meaningfulMetricName, double mainValue, double eventValue, String eventName, double severity) {
		this.factType = factType;
		this.betterWorse = betterWorse;
		this.metric = metric;
		this.meaningfulMetricName = meaningfulMetricName;
		this.mainValue = mainValue;
		this.eventValue = eventValue;
		this.eventName = eventName;
		this.severity = severity;
	}

	public static void compareEventToMain(PerformanceResult mainInput, String mainEvent, PerformanceResult eventInput, String event) {
		compareEventToMain(mainInput, mainEvent, eventInput, event, mainInput.getTimeMetric());
	}
	
	public static void compareEventToMain(PerformanceResult mainInput, String mainEvent, PerformanceResult eventInput, String event, String timeMetric) {
		// don't compare main to self
		if (mainEvent.equals(event)) {
			return;
		}
		
		double mainTime = mainInput.getInclusive(0, mainEvent, timeMetric);
		double eventTime = mainInput.getExclusive(0, event, timeMetric);
		double eventIncTime = mainInput.getInclusive(0, event, timeMetric);
		double severity = eventTime / mainTime;
		double severityInc = eventIncTime / mainTime;
		//System.out.println(timeMetric + " " + mainTime + " " + eventTime + " " + severity);
		for (String metric : mainInput.getMetrics()) {
			double mainValue = mainInput.getInclusive(0, mainEvent, metric);
			double eventValue = eventInput.getExclusive(0, event, metric);
			double eventIncValue = eventInput.getInclusive(0, event, metric);
			/*if (metric.equals("((L3_MISSES-DATA_EAR_CACHE_LAT128)/L3_MISSES)")) {
				System.out.println(event + " " + metric + " " + mainValue + " " + eventValue + " ");
			}*/
			if (metric.equals(DerivedMetrics.L1_HIT_RATE)) {
				// L1 cache hit rate
				if (mainValue > eventValue) {
					// this event has poor memory access
					RuleHarness.assertObject(new MeanEventFact("Compared to Main", WORSE, metric, "L1 cache hit rate", mainValue, eventValue, event, severity));
				}
			} else if (metric.equals(DerivedMetrics.L2_HIT_RATE)) {
				// L2 cache hit rate
				if (mainValue > eventValue) {
					// this event has poor memory access
					RuleHarness.assertObject(new MeanEventFact("Compared to Main", WORSE, metric, "L2 cache hit rate", mainValue, eventValue, event, severity));
				}
			} else if (metric.equals(DerivedMetrics.MFLOP_RATE)) {
				// FLOP rate
				if (mainValue < eventValue) {
					// this event has higher than average FLOP rate
					RuleHarness.assertObject(new MeanEventFact("Compared to Main", BETTER, metric, "MFLOP/s", mainValue, eventValue, event, severity));
				}
			} else if (metric.equals(DerivedMetrics.L1_CACHE_HITS)) {
				// L1 cache hits
			} else if (metric.equals(DerivedMetrics.MEM_ACCESSES)) {
				// L1 cache access rate (aka memory accesses)
				if (mainValue > eventValue) {
					// this event has higher than average memory accesses
					RuleHarness.assertObject(new MeanEventFact("Compared to Main", WORSE, metric, "L1 cache access rate", mainValue, eventValue, event, severity));
				}
			} else if (metric.equals(DerivedMetrics.L2_CACHE_HITS)) {
				// L2 cache hits
			} else if (metric.equals(DerivedMetrics.L2_ACCESSES)) {
				// L2 cache access rate
			} else if (metric.equals(DerivedMetrics.TOT_INS_RATE)) {
				// Total instruction rate
			} else { 
				// any other metric combination
				if (mainValue < eventValue) {
					RuleHarness.assertObject(new MeanEventFact("Compared to Main", HIGHER, metric, metric, mainValue, eventValue, event, severity));
				} else { //if (mainValue > eventValue) {
					RuleHarness.assertObject(new MeanEventFact("Compared to Main", LOWER, metric, metric, mainValue, eventValue, event, severity));
				}
				if (mainValue < eventIncValue) {
					RuleHarness.assertObject(new MeanEventFact("Inclusive compared to Main", HIGHER, metric, metric, mainValue, eventIncValue, event, severityInc));
				} else { //if (mainValue > eventIncValue) {
					RuleHarness.assertObject(new MeanEventFact("Inclusive compared to Main", LOWER, metric, metric, mainValue, eventIncValue, event, severityInc));
				}
			}
				
		}
	}
	
	public static void evaluateLoadBalance(PerformanceResult means, PerformanceResult ratios, String event) {
		evaluateLoadBalance(means, ratios, event, null, AbstractResult.EXCLUSIVE);
	}

	public static void evaluateLoadBalance(PerformanceResult means, PerformanceResult ratios, String event, String testMetric) {
		evaluateLoadBalance(means, ratios, event, testMetric, AbstractResult.EXCLUSIVE);
	}

	public static void evaluateLoadBalance(PerformanceResult means, PerformanceResult ratios, String event, String testMetric, int type) {
		String mainEvent = means.getMainEvent();
		
		// don't compare main to self
		if (mainEvent.equals(event)) {
			return;
		}
		
		String timeMetric = means.getTimeMetric();
		if (timeMetric == null || timeMetric.equals("")) {
			timeMetric = testMetric;
		}
		double mainTime = means.getInclusive(0, mainEvent, timeMetric);
		double eventTime = means.getExclusive(0, event, timeMetric);
		double severity = eventTime / mainTime;
		
		Set<String> metrics = new HashSet<String>();
		if (testMetric != null) {
			metrics.add(testMetric);
		} else {
			metrics = ratios.getMetrics();
		}

		for (String metric : metrics) {
			double eventRatio = ratios.getDataPoint(0, event, metric, type);
			double eventValue = means.getDataPoint(0, event, metric, type);
			double mainRatio = ratios.getDataPoint(0, mainEvent, metric, type);
			// any other metric combination
			//System.out.println("Main Ratio: " + mainRatio);
			if (mainRatio < eventRatio) {
				RuleHarness.assertObject(new MeanEventFact("Load Imbalance", HIGHER, metric, metric, eventRatio, eventValue, event, severity));
			} else if (mainRatio < eventRatio) {
				RuleHarness.assertObject(new MeanEventFact("Load Imbalance", LOWER, metric, metric, eventRatio, eventValue, event, severity));
			} else {
				RuleHarness.assertObject(new MeanEventFact("Load Imbalance", NONE, metric, metric, eventRatio, eventValue, event, severity));
			}
		}
	}
	
	public static void evaluateMetric(PerformanceResult means, String event, String testMetric) {
		String mainEvent = means.getMainEvent();
		
		// don't compare main to self
		if (mainEvent.equals(event)) {
			return;
		}
		
		String timeMetric = means.getTimeMetric();
		if (timeMetric == null || timeMetric.equals("")) {
			timeMetric = testMetric;
		}
		double mainTime = means.getInclusive(0, mainEvent, timeMetric);
		double eventTime = means.getExclusive(0, event, timeMetric);
		double severity = eventTime / mainTime;
		
		Set<String> metrics = new HashSet<String>();
		if (testMetric != null) {
			metrics.add(testMetric);
		} else {
			metrics = means.getMetrics();
		}

		for (String metric : metrics) {
			double eventValue = means.getExclusive(0, event, metric);
			// any other metric combination
			RuleHarness.assertObject(new MeanEventFact("Metric", NONE, metric, metric, 0.0, eventValue, event, severity));
		}
	}
	
	
	public String toString () {
		// TODO: MAKE THIS PRETTY!
		StringBuilder buf = new StringBuilder();
		if (betterWorse == BETTER) {
			buf.append("Better ");
		} else if (betterWorse == WORSE) {
			buf.append("Worse ");
		} else if (betterWorse == HIGHER) {
			buf.append("Higher ");
		} else { // if (betterWorse == LOWER) {
			buf.append("Lower ");
		}
		//buf.append(meaningfulMetricName + " ");
		buf.append(mainValue + " ");
		buf.append(eventValue + " ");
		buf.append(eventName + " ");
		buf.append(metric + " ");
		buf.append(severity + " ");
		
		return buf.toString();
	}

	/**
	 * @return the betterWorse
	 */
	public int isBetterWorse() {
		return betterWorse;
	}

	/**
	 * @param betterWorse the betterWorse to set
	 */
	public void setBetterWorse(int betterWorse) {
		this.betterWorse = betterWorse;
	}

	/**
	 * @return the eventValue
	 */
	public double getEventValue() {
		return eventValue;
	}

	/**
	 * @param eventValue the eventValue to set
	 */
	public void setEventValue(double eventValue) {
		this.eventValue = eventValue;
	}

	/**
	 * @return the mainValue
	 */
	public double getMainValue() {
		return mainValue;
	}

	/**
	 * @param mainValue the mainValue to set
	 */
	public void setMainValue(double mainValue) {
		this.mainValue = mainValue;
	}

	/**
	 * @return the meaningfulMetricName
	 */
	public String getMeaningfulMetricName() {
		return meaningfulMetricName;
	}

	/**
	 * @param meaningfulMetricName the meaningfulMetricName to set
	 */
	public void setMeaningfulMetricName(String meaningfulMetricName) {
		this.meaningfulMetricName = meaningfulMetricName;
	}

	/**
	 * @return the metric
	 */
	public String getMetric() {
		return metric;
	}

	/**
	 * @param metric the metric to set
	 */
	public void setMetric(String metric) {
		this.metric = metric;
	}

	/**
	 * @return the severity
	 */
	public double getSeverity() {
		return severity;
	}

	/**
	 * @param severity the severity to set
	 */
	public void setSeverity(double severity) {
		this.severity = severity;
	}

	/**
	 * @return the eventName
	 */
	public String getEventName() {
		return eventName;
	}

	/**
	 * @param eventName the eventName to set
	 */
	public void setEventName(String eventName) {
		this.eventName = eventName;
	}
	
	public String getPercentage(Double value) {
		DecimalFormat format = new DecimalFormat("00.00%");
		String p = format.format(value);
		return p;
	}
	
	public String getPercentage() {
		return getPercentage(this.severity);
	}

	/**
	 * @return the factType
	 */
	public String getFactType() {
		return factType;
	}

	/**
	 * @param factType the factType to set
	 */
	public void setFactType(String factType) {
		this.factType = factType;
	}
}
