/*
 * Created on Mar 16, 2005
 *
 */
package edu.uoregon.tau.perfexplorer.clustering;


 /**
  * This interface is used to define the methods to implement a hierarchical 
  * clustering class.
  *
  * <P>CVS $Id: ClusterInterface.java,v 1.2 2009/11/18 17:45:16 khuck Exp $</P>
  * @author khuck
  * @version 0.1
  * @since   0.1
  *
  */
public interface ClusterInterface {

    /**
     * This method performs the K means clustering
     * 
     * @throws ClusterException
     */
    public void findClusters() throws ClusterException;

    /**
     * This method gets the ith ClusterDescription object
     * 
     * @param i
     * @return a ClusterDescription
     * @throws ClusterException
     */
    public ClusterDescription getClusterDescription(int i) 
        throws ClusterException;
   
    /**
     * Sets the input data for the clustering operation.
     * 
     * @param inputData
     */

    public void setInputData(RawDataInterface inputData);

    /**
     * Method to get the cluster centroids (averages).
     * 
     * @return
     */
    public RawDataInterface getClusterCentroids();

    /**
     * Method to get the cluster minimum values.
     * 
     * @return
     */
    public RawDataInterface getClusterMinimums();

    /**
     * Method to get the cluster maximum values.
     * 
     * @return
     */
    public RawDataInterface getClusterMaximums();
    
    /**
     * Method to get the cluster standard deviation values.
     * 
     * @return
     */
    public RawDataInterface getClusterStandardDeviations();

    /**
     * Reset method, for resetting the cluster.  If a user loads
     * this object with data, and then does several clusterings
     * with several K values, then we need a reset method.
     *
     */
    public void reset();
    
    /**
     * Method to get the number of individuals in each cluster.
     * 
     * @return
     */
    public int[] getClusterSizes();
    
    /**
     * Method to get the cluster ID for the cluster that contains
     * individual "i".
     * 
     * @param i
     * @return
     */

    public int[] clusterInstances();
     /**
     * Method to get the cluster IDs for the cluster that contains
     * each individual "i" in the set of individuals.
     * 
     * @param i
     * @return
     */
    public int clusterInstance(int i);
    
    /**
     * Get the number of individuals that we are clustering.
     * 
     * @return
     */
    public int getNumInstances();
    
}
