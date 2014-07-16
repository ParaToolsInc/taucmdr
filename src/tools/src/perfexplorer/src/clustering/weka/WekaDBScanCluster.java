/*
 * Created on Mar 16, 2005
 *
 */
package edu.uoregon.tau.perfexplorer.clustering.weka;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import weka.clusterers.DBScan;
import weka.core.Instance;
import weka.core.Instances;
import edu.uoregon.tau.perfexplorer.clustering.ClusterDescription;
import edu.uoregon.tau.perfexplorer.clustering.ClusterException;
import edu.uoregon.tau.perfexplorer.clustering.DBScanClusterInterface;
import edu.uoregon.tau.perfexplorer.clustering.DistanceMatrix;
import edu.uoregon.tau.perfexplorer.clustering.RawDataInterface;
import edu.uoregon.tau.perfexplorer.common.PerfExplorerOutput;


/**
 * This class is used as a list of names and values to describe 
 * a cluster created during some type of clustering operation.
 * 
 * <P>CVS $Id: WekaDBScanCluster.java,v 1.3 2009/11/25 09:15:34 khuck Exp $</P>
 * @author khuck
 * @version 0.2
 * @since 0.2
 *
 */
public class WekaDBScanCluster extends WekaAbstractCluster implements DBScanClusterInterface {

	// the error to use
	private double e = 0;
	private DBScan dbscan = null;
	private int[] clusterSizes = null;
	private List<Integer>[] clusterIndexes = null;
	private int minPoints = 4;
	
	/**
	 * Default constructor - package protected
	 */
	WekaDBScanCluster() {
		super();
		reset();
	}

	/**
	 * Reset method, for resetting the cluster.  If a user loads
	 * this object with data, and then does several clusterings
	 * with several error values, then we need a reset method.
	 */
	public void reset() {
		this.clusterCentroids = null;
		this.clusterMaximums = null;
		this.clusterMinimums = null;
		this.clusterStandardDeviations = null;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanClusterInterface#setInputData(RawDataInterface)
	 */
	public void setInputData(RawDataInterface inputData) {
		this.instances = (Instances) inputData.getData();
		this.inputData = inputData;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanCluster#findClusters()
	 */
	public void findClusters() throws ClusterException {
		//assert instances != null : instances;
		try {
			this.dbscan = new DBScan();
			this.dbscan.setMinPoints(this.minPoints); // minimum of 4 points per cluster
			this.dbscan.setEpsilon(e); // the maximum distance between points in a cluster
			Instances localInstances = null;
			localInstances = this.instances;
			dbscan.buildClusterer(localInstances);
			generateStats();
			evaluateCluster();
		} catch (Exception e) {
			e.printStackTrace();
			System.err.println(e.getMessage());
		}
	}

	public int guessEpsilonIndex() {
		double[] kDistances = getKDistances();
		// start at the next-to-last one
		int index = kDistances.length - 2;
		// find "inflection" point
		for (int i = index ; i > 1 ; i--) {
			// average the three values
			double avg = (kDistances[i-1] + kDistances[i] + kDistances[i+1]) / 3.0;
			if (avg < kDistances[i]) {
				index = i+1; // take the worst one of the three, to be conservative
				break;
			}
		}
		return index;
	}

	public double guessEpsilon() {
		double[] kDistances = getKDistances();
		return kDistances[guessEpsilonIndex()];
	}

	public double[] getKDistances() {
		RawDataInterface localData = inputData;
		DistanceMatrix distances = new DistanceMatrix(localData.numVectors());
		distances.solveCartesianDistances(localData);
		// for each point:
		double[] finalPoints = new double[localData.numVectors()];
		for (int i = 0 ; i < localData.numVectors() ; i++) {
			// sort distances
			double[] tmpPoints = new double[localData.numVectors()];
			for (int j = 0 ; j < localData.numVectors() ; j++) {
				tmpPoints[j] = distances.elementAt(i, j);
			}
			Arrays.sort(tmpPoints);
			// get k-th nearest distance - add one to ignore distance to self
			finalPoints[i] = tmpPoints[this.minPoints];
		}
		// sort the n k-th nearest distances
		Arrays.sort(finalPoints);
		return finalPoints;
	}

	@SuppressWarnings("unchecked")
	private void generateStats() throws Exception {
		if (this.instances == null) {
			this.instances = (Instances)this.inputData.getData();
		}
		clusterCentroids = new Instances(instances, dbscan.numberOfClusters());
		clusterMaximums = new Instances(instances, dbscan.numberOfClusters());
		clusterMinimums = new Instances(instances, dbscan.numberOfClusters());
		clusterStandardDeviations = new Instances(instances, dbscan.numberOfClusters());

		// we will create an extra cluster for "noise"
		clusterIndexes = new List[dbscan.numberOfClusters()];
		for (int i = 0 ; i < dbscan.numberOfClusters() ; i++) {
			clusterIndexes[i] = new ArrayList<Integer>();
		}
		for (int i = 0 ; i < instances.numInstances() ; i++) {
			try {
				int myIndex = dbscan.clusterInstance(instances.instance(i));
				clusterIndexes[myIndex].add(new Integer(i));
			} catch (Exception e) {
				// do nothing.  In their infinite wisdom, "clusterInstance" throws
				// an exception if this point is noise.
			}
		}
		this.clusterSizes = new int[dbscan.numberOfClusters()];
		for (int i = 0 ; i < dbscan.numberOfClusters() ; i++) {
			this.clusterSizes[i] = clusterIndexes[i].size();
		}
		
		for (int i = 0 ; i < dbscan.numberOfClusters() ; i++) {
			int numAttr = this.instances.firstInstance().numAttributes();
			double[] wekasucks = new double[numAttr];
			Instance total = new Instance(1.0, wekasucks);
			Instance min = new Instance(1.0, wekasucks);
			Instance max = new Instance(1.0, wekasucks);
			Instance avg = new Instance(1.0, wekasucks);
			Instance stddev = new Instance(1.0, wekasucks);
			// iterate over the instances in the cluster
			boolean first = true;
			for (Integer index : clusterIndexes[i]) {
				Instance tmp = this.instances.instance(index.intValue());
				// iterate over the attributes for each dimension
				for (int attr = 0 ; attr < numAttr ; attr++) {
					double tmpVal = tmp.value(attr);
					total.setValue(attr, total.value(attr) + tmpVal);
					max.setValue(attr, Math.max(max.value(attr), tmpVal));
					if (first) {
						min.setValue(attr, tmpVal);
					} else {
						min.setValue(attr, Math.min(min.value(attr), tmpVal));
					}
				}
				first = false;
			}
			for (int attr = 0 ; attr < numAttr ; attr++) {
				avg.setValue(attr, total.value(attr) / this.clusterSizes[i]);
			}
			clusterCentroids.add(avg);
			clusterMaximums.add(max);
			clusterMinimums.add(min);
			// iterate over the instances in the cluster for stddev
			for (Integer index : clusterIndexes[i]) {
				Instance tmp = this.instances.instance(index.intValue());
				// iterate over the attributes for each dimension
				for (int attr = 0 ; attr < numAttr ; attr++) {
					double tmpVal = tmp.value(attr);
					stddev.setValue(attr, (stddev.value(attr) + (Math.pow(avg.value(attr) - tmpVal, 2.0))));
				}
			}
			for (int attr = 0 ; attr < numAttr ; attr++) {
				stddev.setValue(attr, Math.sqrt(stddev.value(attr)));
			}
			clusterStandardDeviations.add(stddev);
		}
	}
	
	/* (non-Javadoc)
	 * @see clustering.DBScanCluster#getClusterDescription(int)
	 */
	public ClusterDescription getClusterDescription(int i)
			throws ClusterException {
		return null;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanCluster#setError(int)
	 */
	public void setError(double e) {
		this.e = e;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanCluster#getK()
	 */
	public double getError() {
		return this.e;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanCluster#setMinPoints(int)
	 */
	public void setMinPoints(int minPoints) {
		this.minPoints = minPoints;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanCluster#getMinPoints()
	 */
	public int getMinPoints() {
		return this.minPoints;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanCluster#setInitialCenters(int[])
	 */
	public void setInitialCenters(int[] indexes) {
		// TODO Auto-generated method stub
		
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanClusterInterface#getClusterCentroids()
	 */
	public RawDataInterface getClusterCentroids() {
		WekaRawData centroids = new WekaRawData(clusterCentroids);
		return centroids;
	}

	public RawDataInterface getClusterMaximums() {
		WekaRawData maximums = new WekaRawData(clusterMaximums);
		return maximums;
	}

	public RawDataInterface getClusterMinimums() {
		WekaRawData minimums = new WekaRawData(clusterMinimums);
		return minimums;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanClusterInterface#getClusterStandardDeviations()
	 */
	public RawDataInterface getClusterStandardDeviations() {
		WekaRawData deviations = new WekaRawData(clusterStandardDeviations);
		return deviations;
	}
	
	public int[] getClusterSizes() {
		return this.clusterSizes;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanClusterInterface#clusterInstance(int)
	 */
	public int clusterInstance(int i) {
		int retval = 0;
		try {
			retval = dbscan.clusterInstance(instances.instance(i));
		} catch (Exception e) {
			retval = -1;
		}
		return retval;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanClusterInterface#clusterInstance(Instance)
	 */
	public int clusterInstance(Instance instance) throws Exception {
		int retval = 0;
		try {
			retval = dbscan.clusterInstance(instance);
		} catch (Exception e) {
			retval = -1;
		}
		return retval;
	}

	/* (non-Javadoc)
	 * @see clustering.DBScanClusterInterface#getNumInstances()
	 */
	public int getNumInstances() {
		return instances.numInstances();
	}

	// this method is by Calinski & Harabasz(1974)
	protected void evaluateCluster() {
		try {
/*			double betweenError = kmeans.getBetweenError();
			//PerfExplorerOutput.println("Between Squared Error: " + betweenError);
			double withinError = kmeans.getSquaredError();
			//PerfExplorerOutput.println("Within Squared Error: " + withinError);
			//PerfExplorerOutput.println("k-1: " + (k-1));
			//PerfExplorerOutput.println("n-k: " + (instances.numInstances()-k));
			double maximizeMe = (betweenError * (k-1)) / 
				(withinError * (instances.numInstances() - k));
			//PerfExplorerOutput.println("Maximize Me: " + maximizeMe);
*/		} catch (Exception e) {
			PerfExplorerOutput.println ("EXCEPTION: " + e.getMessage());
			e.printStackTrace();
		}
	}

	@Override
	protected double getSquaredError() {
		// TODO Auto-generated method stub
		return 0;
	}

	/**
	 * Testing method...
	 * @param args
	 */
	public static void main(String[] args) {
		int dimensions = 2;
		int k = 2;
		int vectors = 10*k;
		
		// generate some raw data
		List<String> attrs = new ArrayList<String>(vectors);
		attrs.add("x");
		attrs.add("y");
//		attrs.add("z");
		RawDataInterface data = new WekaRawData("test", attrs, vectors, dimensions, null);
		for (int i = 0 ; i < vectors ; i++) {
			int modval = (i % k);
			System.out.print("modval: " + modval);
			for (int j = 0 ; j < dimensions ; j++) {
				double val = (0.5 + (Math.random()/10.0) + modval);
				System.out.print(" val[" + j + "]: " + val);
				data.addValue(i, j, val);
			}
			System.out.println("");
		}
		
		DBScanClusterInterface clusterer = AnalysisFactory.createDBScanEngine();
		clusterer.setInputData(data);

		double epsilon = clusterer.guessEpsilon();
		clusterer.setError(epsilon);
		System.out.println("Using Epsilon: " + epsilon);
		
		try {
			clusterer.findClusters();
		} catch (ClusterException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		int[] clusters = clusterer.clusterInstances();
		for (int i = 0 ; i < vectors ; i++) {
			System.out.println("Instance " + i + " is in cluster: " + clusters[i]);
		}
		clusters = clusterer.getClusterSizes();
		for (int i = 0 ; i < clusters.length ; i++) {
			System.out.println("Cluster " + i + " has " + clusters[i] + " members.");
		}

		
		System.out.println("Total clusters: " + clusterer.getClusterCentroids().numVectors());
		
	}

}
