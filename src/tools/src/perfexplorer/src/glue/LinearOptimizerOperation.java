/**
 * 
 */
package edu.uoregon.tau.perfexplorer.glue;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.Set;

import edu.uoregon.tau.perfexplorer.cqos.WekaClassifierWrapper;

/**
 * @author khuck
 *
 */
public class LinearOptimizerOperation extends AbstractPerformanceOperation {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1526009436637311668L;
	public static final String SUPPORT_VECTOR_MACHINE = WekaClassifierWrapper.SUPPORT_VECTOR_MACHINE;
	public static final String NAIVE_BAYES = WekaClassifierWrapper.NAIVE_BAYES;
    public static final String MULTILAYER_PERCEPTRON = WekaClassifierWrapper.MULTILAYER_PERCEPTRON;
    public static final String LINEAR_REGRESSION = WekaClassifierWrapper.LINEAR_REGRESSION;

	private String metric = "Time";
	private Set<String> metadataFields = null;
	private String classLabel = null;
	private WekaClassifierWrapper wrapper = null;
	private String classifierType = LINEAR_REGRESSION;
		
	/**
	 * @param inputs
	 */
	public LinearOptimizerOperation(List<PerformanceResult> inputs, String metric, 
			Set<String> metadataFields, String classLabel) {
		super(inputs);
		this.metric = metric;
		this.metadataFields = metadataFields;
		this.classLabel = metric;
	}

 	public List<PerformanceResult> processData() {
		// create a map to store the UNIQUE tuples
		Map<Hashtable<String,String>,PerformanceResult> tuples = 
			new HashMap<Hashtable<String,String>,PerformanceResult>();
		
		// iterate through the inputs
		for (PerformanceResult input : this.inputs) {
			// create a local Hashtable 
			Hashtable<String,String> localMeta = new Hashtable<String,String>();
			// get the input's metadata
			TrialMetadata tmp = new TrialMetadata(input);
			Hashtable<String,String> meta = tmp.getCommonAttributes();
			// create a reduced hashtable
			if (this.metadataFields != null) {
				for (String key : this.metadataFields) {
					// don't include the class label - we want just the "best" method for that parameter - not all of them
					if (!key.equals(this.classLabel))
						localMeta.put(key, meta.get(key));
				}
			// otherwise, if the user didn't specify a set of properties, use them all (?)
			} else {
				for (String key : meta.keySet()) {
					// don't include the class label - we want just the "best" method for that parameter - not all of them
					if (!key.equals(this.classLabel))
						localMeta.put(key, meta.get(key));
				}				
			}
			localMeta.put(metric, Double.toString(input.getInclusive(0, input.getMainEvent(), metric)));
			// check if the metric is one of the metrics, or a metadata field
			if (!input.getMetrics().contains(metric)) {
				// put the hashtable in the set: if its performance is "better" than the existing one
				// or if it doesn't exist yet.
				PerformanceResult result = tuples.get(localMeta);
				if (result == null) {
					tuples.put(localMeta,input);
				} else {
					if (Double.parseDouble(meta.get(metric)) < 
							Double.parseDouble((new TrialMetadata(result)).getCommonAttributes().get(metric))) {
						tuples.put(localMeta,input);
					}
				}
			} else {
				// put the hashtable in the set: if its performance is "better" than the existing one
				// or if it doesn't exist yet.
				PerformanceResult result = tuples.get(localMeta);
				if (result == null) {
					tuples.put(localMeta,input);
				} else {
					if (input.getInclusive(0, input.getMainEvent(), metric) < 
							result.getInclusive(0, result.getMainEvent(), this.metric)) {
						tuples.put(localMeta,input);					
					}
				}
			}
		}
		
		List<Map<String,String>> trainingData = new ArrayList<Map<String,String>>();

		// ok, we have the set of "optimal" methods for each unique tuple.  Convert them to Instances.
		for (Hashtable<String,String> tmp : tuples.keySet()) {
			Map<String,String> tmpMap = new HashMap<String,String>();
			
			// set the independent parameters
			if (this.metadataFields != null) {
				for (String metaKey : this.metadataFields) {
					tmpMap.put(metaKey, tmp.get(metaKey));
				}
			} else {
				for (String metaKey : tmp.keySet()) {
					tmpMap.put(metaKey, tmp.get(metaKey));
				}
			}
//			tmpMap.put(this.classLabel, (new TrialMetadata(tuples.get(tmp)).getCommonAttributes().get(classLabel)));
			trainingData.add(tmpMap);
			System.out.println(tmpMap.toString());
		}
		
		System.out.println("Total instances for training: " + trainingData.size());
		System.out.println("Using keys: " + this.metadataFields.toString());

		try {
			this.wrapper = new WekaClassifierWrapper (trainingData, this.classLabel);
			this.wrapper.setClassifierType(classifierType);
			this.wrapper.buildClassifier();
		} catch (Exception e) {
			System.err.println(e.getMessage());
			e.printStackTrace();			
		}
		
		return null;
	}
	
	public String getClass(Map<String,String> inputFields) {
		return wrapper.getClass(inputFields);
	}

	public double classifyInstance(Map<String,String> inputFields) {
		return wrapper.classifyInstance(inputFields);
	}

	public double getConfidence() {
		return wrapper.getConfidence();
	}

	public void writeClassifier(String fileName) {
		WekaClassifierWrapper.writeClassifier(fileName, this.wrapper);
	}

	public String getClassifierType() {
		return this.classifierType;
	}

	public void setClassifierType(String classifierType) {
		this.classifierType = classifierType;			
	}
	
	public double[] getCoefficients() {
		return wrapper.getCoefficients();
	}
	
}
