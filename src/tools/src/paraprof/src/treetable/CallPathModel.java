package edu.uoregon.tau.paraprof.treetable;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import edu.uoregon.tau.common.treetable.AbstractTreeTableModel;
import edu.uoregon.tau.common.treetable.TreeTableModel;
import edu.uoregon.tau.paraprof.DataSorter;
import edu.uoregon.tau.paraprof.PPFunctionProfile;
import edu.uoregon.tau.paraprof.ParaProfTrial;
import edu.uoregon.tau.perfdmf.DataSource;
import edu.uoregon.tau.perfdmf.Function;
import edu.uoregon.tau.perfdmf.FunctionProfile;
import edu.uoregon.tau.perfdmf.Group;
import edu.uoregon.tau.perfdmf.Thread;
import edu.uoregon.tau.perfdmf.UtilFncs;

/**
 * Data model for treetable using callpaths
 *    
 * TODO : ...
 *
 * <P>CVS $Id: CallPathModel.java,v 1.12 2010/06/09 01:28:25 amorris Exp $</P>
 * @author  Alan Morris
 * @version $Revision: 1.12 $
 */
public class CallPathModel extends AbstractTreeTableModel {

    private List<TreeTableNode> roots;
    private Thread thread;
    private DataSource dataSource;
    private ParaProfTrial ppTrial;
    private double[] maxValues;

    private int sortColumn;
    private boolean sortAscending;
    private int colorMetric;

    private boolean reversedCallPaths = true;

    private TreeTableWindow window;

    public CallPathModel(TreeTableWindow window, ParaProfTrial ppTrial, Thread thread, boolean reversedCallPaths) {
        super(null);
        this.window = window;
        root = new TreeTableNode(null, this, "root");

        dataSource = ppTrial.getDataSource();
        this.thread = thread;
        this.ppTrial = ppTrial;

        this.reversedCallPaths = reversedCallPaths;
        setupData();

    }

    private void setupData() {

        roots = new ArrayList<TreeTableNode>();
        DataSorter dataSorter = new DataSorter(ppTrial);

        // don't ask the thread for its functions directly, since we want group masking to work
        List<PPFunctionProfile> functionProfileList = dataSorter.getCallPathFunctionProfiles(thread);

        Map<String, String> rootNames = new HashMap<String, String>();

        Group derived = ppTrial.getGroup("TAU_CALLPATH_DERIVED");

        if (window.getTreeMode()) {
        	String checkCallpath = dataSource.getMetaData().get("TAU_CALLPATH");
        	boolean isCallpath=false;
        	if(checkCallpath!=null&&checkCallpath.equals("on"))
        		isCallpath=true;
        		
            for (Iterator<PPFunctionProfile> it = functionProfileList.iterator(); it.hasNext();) {
                // Find all the rootNames (as strings)
                PPFunctionProfile ppFunctionProfile = it.next();
                FunctionProfile fp = ppFunctionProfile.getFunctionProfile();

                boolean showInTree=false;
                
                if(isCallpath)
                {
                	showInTree=(fp != null && fp.isCallPathFunction());
                }
                else{
                	String groups = fp.getFunction().getGroupString();
                	showInTree=(fp != null && (fp.isCallPathFunction() || !groups.contains("TAU_SAMPLE")));
                }
                
                if (showInTree) {
                    String rootName;
                    if (reversedCallPaths) {
                        rootName = UtilFncs.getRevLeftSide(fp.getFunction().getReversedName());
                    } else {
                        if (fp.getFunction().isGroupMember(derived)) {
                            continue;
                        }
                        rootName = UtilFncs.getLeftSide(fp.getName());
                    }

                    if (rootNames.get(rootNames) == null) {
                        rootNames.put(rootName, "1");
                    }
                }
            }
            for (Iterator<String> it = rootNames.keySet().iterator(); it.hasNext();) {
                // now go through the strings and get the actual functions
                String rootName = it.next();
                Function function = dataSource.getFunction(rootName);

                TreeTableNode node;

                if (function == null) {
                    node = new TreeTableNode(null, this, rootName);
                } else {

                    FunctionProfile fp = thread.getFunctionProfile(function);
                    if (fp == null) {
                        node = new TreeTableNode(null, this, rootName);
                    } else {
                        node = new TreeTableNode(fp, this, null);
                    }
                }

                roots.add(node);
            }

        } else {
            for (Iterator<PPFunctionProfile> it = functionProfileList.iterator(); it.hasNext();) {
                PPFunctionProfile ppFunctionProfile = it.next();
                FunctionProfile fp = ppFunctionProfile.getFunctionProfile();

                if (fp != null && ppTrial.displayFunction(fp.getFunction())) {
                    //String fname = fp.getName();

                    TreeTableNode node = new TreeTableNode(fp, this, null);
                    roots.add(node);
                }

            }
        }

        Collections.sort(roots);
        computeMaximum();
    }

    public void computeMaximum() {
        int numMetrics = window.getPPTrial().getNumberOfMetrics();
        maxValues = new double[numMetrics];

        for (int i = 0; i < numMetrics; i++) {
            // there are two ways to do this (cube brings up a window to ask you which way you 
            // want to compute the max value for the color)

            //maxValue[i] = Math.max(maxValue[i], fp.getInclusive(i));
            maxValues[i] += thread.getMaxInclusive(i, ppTrial.getSelectedSnapshot());
        }
    }

    public int getColumnCount() {
        return 1 + window.getColumns().size();
    }

    public String getColumnName(int column) {
        if (column == 0) {
            return "Name";
        }
        return window.getColumns().get(column - 1).toString();
    }

    public Object getValueAt(Object node, int column) {

        if (node == root) {
            return null;
        }

        TreeTableNode treeTableNode = (TreeTableNode) node;

        return treeTableNode;
    }

    /**
     * Returns the class for the particular column.
     */
    @SuppressWarnings({ "rawtypes", "unchecked" })
	public Class getColumnClass(int column) {
        if (column == 0)
            return TreeTableModel.class;
        return window.getColumns().get(column - 1).getClass();
    }

    public int getChildCount(Object parent) {
        if (parent == root) {
            return roots.size();
        }

        if (window.getTreeMode()) {
            TreeTableNode node = (TreeTableNode) parent;
            return node.getNumChildren();
        } else {
            return 0;
        }
    }

    public Object getChild(Object parent, int index) {
        if (parent == root) {
            return roots.get(index);
        }

        TreeTableNode node = (TreeTableNode) parent;

        return node.getChildren().get(index);
    }

    public Thread getThread() {
        return thread;
    }

    public double[] getMaxValues() {
        return maxValues;
    }

    public int getSortColumn() {
        return sortColumn;
    }

    public boolean getSortAscending() {
        return sortAscending;
    }

    public void sortColumn(int index, boolean ascending) {
        super.sortColumn(index, ascending);
        sortColumn = index;
        sortAscending = ascending;

        Collections.sort(roots);
        for (Iterator<TreeTableNode> it = roots.iterator(); it.hasNext();) {
            TreeTableNode node = it.next();
            node.sortChildren();
        }

    }

    public TreeTableWindow getWindow() {
        return window;
    }

    public ParaProfTrial getPPTrial() {
        return ppTrial;
    }

    public boolean getReversedCallPaths() {
        return reversedCallPaths;
    }

    public void setReversedCallPaths(boolean reversedCallPaths) {
        this.reversedCallPaths = reversedCallPaths;
    }

    public int getColorMetric() {
        return colorMetric;
    }

    public void setColorMetric(int colorMetric) {
        this.colorMetric = colorMetric;
    }

}
