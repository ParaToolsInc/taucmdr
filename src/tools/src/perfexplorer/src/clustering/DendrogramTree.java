package edu.uoregon.tau.perfexplorer.clustering;

import java.util.ArrayList;
import java.util.List;


/**
 * This class specifies the nodes in a dendrogram representing the results
 * of a hierarchical clustering.  This dendrogram is a simple binary tree.
 *
 * <P>CVS $Id: DendrogramTree.java,v 1.8 2009/11/18 10:17:31 khuck Exp $</P>
 * @author khuck
 * @version 0.1
 * @since   0.1
 *
 */
public class DendrogramTree {

    private DendrogramTree left = null;
    private DendrogramTree right = null;
    private int id = 0;
	private double height = 0.0;
    private int maxDepth = 0;

    /**
     * Constructor to create a node in the tree.
     * 
     * @param id The node identifier in the tree
     * @param height The distance from this node and its parent node.
     */
    public DendrogramTree (int id, double height) {
        this.id = id;
        this.height = height;
    }
    
    /**
     * This method adds a left subtree to this node.
     * 
     * @param left
     */
    public void setLeft(DendrogramTree left) {
        this.left = left;
        if ((this.right == null) || (left.getDepth() > right.getDepth()))
            maxDepth = left.getDepth() + 1;
        else
            maxDepth = right.getDepth() + 1;
    }
    
    /**
     * This method adds a right subtree to this node.
     * 
     * @param right
     */
    public void setRight(DendrogramTree right) {
        this.right = right;
        if ((this.left == null) || (right.getDepth() > left.getDepth()))
            maxDepth = right.getDepth() + 1;
        else
            maxDepth = left.getDepth() + 1;
    }
    
    /**
     * This method adds two subtrees to this node.
     * 
     * @param left
     * @param right
     */
    public void setLeftAndRight(DendrogramTree left, DendrogramTree right) {
        this.left = left;
        this.right = right;
        if (right.getDepth() > left.getDepth())
            maxDepth = right.getDepth() + 1;
        else
            maxDepth = left.getDepth() + 1;
    }
    
    /**
     * Check to see if there are leaf nodes on this subtree node.  If not, this 
     * is a leaf node.
     * 
     * @return
     */
    public boolean isLeaf() {
        return (left == null && right == null) ? true : false;
    }
    
    /**
     * Get the left subtree below this node.
     * 
     * @return
     */
    public DendrogramTree getLeft() {
        return left;
    }
    
    /**
     * Get the right subtree below this node.
     * 
     * @return
     */
    public DendrogramTree getRight() {
        return right;
    }
    
    /**
     * Get the height of the dendrogram at this node.  The height represents
     * the "distance" between this node and its parent.  The height is the
     * distance calculation done by the hierarchical clustering.
     * 
     * @return
     */
    public double getHeight() {
        return height;
    }
    
    /**
     * This method finds ideal representatives for clusters in this tree.
     * The tree is traversed to find the "count" deepest leaf nodes in
     * the tree, and returns them to the user.  
     * 
     * @param count The number of centers to find.
     * @return
     */
    public int[] findCenters(int count) {
        int[] centers = new int[count];
        if (count == 1) {
                centers[0] = getRepresentative();
        }else if (count == 2) {
                centers[0] = left.getRepresentative();
                centers[1] = right.getRepresentative();
        }else {
            List<DendrogramTree> clusters = new ArrayList<DendrogramTree>(count);
            clusters.add(left);
            clusters.add(right);
            DendrogramTree current = null;
            while (clusters.size() < count) {
                DendrogramTree winner = clusters.get(0);
                for (int i = 0 ; i < clusters.size() ; i++) {
                    current = clusters.get(i);
                    if (current.getHeight() > winner.getHeight())
                        winner = current;
                }
                clusters.remove(winner);
                clusters.add(winner.getLeft());
                clusters.add(winner.getRight());
            }
            for (int i = 0 ; i < clusters.size() ; i++) {
                current = clusters.get(i);
                centers[i] = current.getRepresentative();
            }
        }
        return centers;
    }
    
    /**
     * This recursive function finds the deepest leaf node below the "this"
     * node.
     * 
     * @return
     */
    public int getRepresentative() {
        if (isLeaf())
            return java.lang.Math.abs(id);
        else if (left.getDepth() == right.getDepth())
            if (left.getHeight() < right.getHeight())
                return left.getRepresentative();
            else
                return right.getRepresentative();
        else if (left.getDepth() > right.getDepth())
            return left.getRepresentative();
        else
            return right.getRepresentative();
    }
    
    /**
     * Return the depth of the subtrees below this node in the tree.
     * 
     * @return
     */
    public int getDepth() {
        return maxDepth;
    }
    
    /**
     * Useful method for debugging.
     * 
     * @return
     */
    public String toString() {
        StringBuilder buf = new StringBuilder();
        if (!isLeaf()) {
            buf.append(left.toString());
            buf.append(right.toString());
            buf.append("node [" + id + "] " + left.id + ", " + right.id + ": " + height + "\n");
        } else {
            buf.append("leaf [" + id + "] \n" );     	
        }
        return buf.toString();
    }

    /**
     * Returns the instance index (ID) of the data at this node in the tree
     * 
     * @return
     */
    public int getID() {
    	// could be negative...
		return Math.abs(id);
	}

    /**
     * Returns a list of indexes for the instances in this tree
     * 
     * @return List<Integer>
     */
    public List<Integer> getIndexes() {
    	List<Integer> list = new ArrayList<Integer>();
    	if (left != null) {
        	list.addAll(left.getIndexes());
    	}
    	if (right != null) {
        	list.addAll(right.getIndexes());
    	}
        if (isLeaf())
            list.add(new Integer(Math.abs(id)-1));
    	return list;
    }

}

