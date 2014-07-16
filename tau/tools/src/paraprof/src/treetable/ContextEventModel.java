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
import edu.uoregon.tau.paraprof.PPUserEventProfile;
import edu.uoregon.tau.paraprof.ParaProfTrial;
import edu.uoregon.tau.paraprof.ParaProfUtils;
import edu.uoregon.tau.perfdmf.Thread;
import edu.uoregon.tau.perfdmf.UserEventProfile;
import edu.uoregon.tau.perfdmf.UtilFncs;

public class ContextEventModel extends AbstractTreeTableModel {

    private static String[] cNames = { "Name", "Total", "NumSamples", "MaxValue", "MinValue", "MeanValue", "Std. Dev." };
	private static String[] cNamesNoTotal = { "Name", "NumSamples", "MaxValue",
			"MinValue", "MeanValue", "Std. Dev." };
    private static Class<?>[] cTypes = { TreeTableModel.class, Double.class, Double.class, Double.class, Double.class, Double.class,
            Double.class };
	private static Class<?>[] cTypesNoTotal = { TreeTableModel.class,
			Double.class, Double.class, Double.class, Double.class,
			Double.class };

    private List<ContextEventTreeNode> roots;

    private ParaProfTrial ppTrial;
    private Thread thread;

    private ContextEventWindow window;

    private int sortColumn;
    private boolean sortAscending;
    DataSorter dataSorter;
	private boolean showTotal = true;

    public ContextEventModel(ContextEventWindow window, ParaProfTrial ppTrial, Thread thread, boolean reversedCallPaths) {
        super(null);
        this.ppTrial = ppTrial;
        this.thread = thread;
        this.window = window;

        root = new ContextEventTreeNode("root", this);

        setupData();
    }

    public Thread getThread() {
        return thread;
    }

	public void showTotal(boolean show) {
		this.showTotal = show;
	}

    private void setupData() {

        roots = new ArrayList<ContextEventTreeNode>();
        dataSorter = new DataSorter(ppTrial);

        // don't ask the thread for its functions directly, since we want group masking to work
        List<PPUserEventProfile> uepList = dataSorter.getUserEventProfiles(thread);

        Map<String,Integer> rootNames = new HashMap<String,Integer>();

        if (window.getTreeMode()) {
            for (Iterator<PPUserEventProfile> it = uepList.iterator(); it.hasNext();) {
                // Find all the rootNames (as strings)
                PPUserEventProfile ppUserEventProfile = it.next();
                UserEventProfile uep = ppUserEventProfile.getUserEventProfile();

                if (uep.getUserEvent().isContextEvent()) {
                    String rootName;

					rootName = UtilFncs.getContextEventRoot(
							ParaProfUtils.getUserEventDisplayName(uep
									.getUserEvent())).trim();

                    rootNames.put(rootName, 1);

                } else {
                    ContextEventTreeNode node = new ContextEventTreeNode(uep, this, null);
                    roots.add(node);
                }
            }
         
            for (Iterator<String> it = rootNames.keySet().iterator(); it.hasNext();) {
                // now go through the strings and get the actual functions

                String possibleRoot = it.next();

                ContextEventTreeNode node = new ContextEventTreeNode(possibleRoot, this);
                roots.add(node);
            }

        } else {
            //            for (Iterator it = functionProfileList.iterator(); it.hasNext();) {
            //                PPFunctionProfile ppFunctionProfile = (PPFunctionProfile) it.next();
            //                FunctionProfile fp = ppFunctionProfile.getFunctionProfile();
            //
            //                if (fp != null && ppTrial.displayFunction(fp.getFunction())) {
            //                    String fname = fp.getName();
            //
            //                    TreeTableNode node = new TreeTableNode(fp, this, null);
            //                    roots.add(node);
            //                }
            //
            //            }
        }

        Collections.sort(roots);
        //computeMaximum();
    }

    public String getColumnName(int column) {
		if (showTotal) {
			return cNames[column];
		} else
			return cNamesNoTotal[column];
    }

    @SuppressWarnings({ "rawtypes", "unchecked" })
	public Class getColumnClass(int column) {
		if (showTotal) {
			return cTypes[column];
		} else
			return cTypesNoTotal[column];
    }

    public int getColorMetric() {
        return 0;
    }

    public int getColumnCount() {
		if (showTotal) {
			return cNames.length;
		} else
			return cNamesNoTotal.length;
    }

    public Object getValueAt(Object node, int column) {
        ContextEventTreeNode cnode = (ContextEventTreeNode) node;
        UserEventProfile uep = cnode.getUserEventProfile();
		if (!showTotal) {
			column++;
		}
        if (uep == null) {
            return null;
        } else {
            switch (column) {
            case 1:
				if (uep.getName()
						.startsWith("Memory Utilization (heap, in KB)")
						|| uep.getName().contains("/s)")
						|| !uep.getUserEvent().isShowTotal()) { // rates are
																// ignored for
																// total
                    return null;
                } else {
                    return new Double(uep.getNumSamples(dataSorter.getSelectedSnapshot())
                            * uep.getMeanValue(dataSorter.getSelectedSnapshot()));
                }
            case 2:
                return new Double(uep.getNumSamples(dataSorter.getSelectedSnapshot()));
            case 3:
                return new Double(uep.getMaxValue(dataSorter.getSelectedSnapshot()));
            case 4:
                return new Double(uep.getMinValue(dataSorter.getSelectedSnapshot()));
            case 5:
                return new Double(uep.getMeanValue(dataSorter.getSelectedSnapshot()));
            case 6:
                return new Double(uep.getStdDev(dataSorter.getSelectedSnapshot()));
            default:
                return null;
            }

        }
    }

    public Object getChild(Object parent, int index) {
        if (parent == root) {
            return roots.get(index);
        }

        ContextEventTreeNode node = (ContextEventTreeNode) parent;

        return node.getChildren().get(index);
    }

    public int getChildCount(Object parent) {
        if (parent == root) {
            return roots.size();
        }

        if (window.getTreeMode()) {
            ContextEventTreeNode node = (ContextEventTreeNode) parent;
            return node.getNumChildren();
        } else {
            return 0;
        }
    }

    public int getSortColumn() {
        return sortColumn;
    }

    public void sortColumn(int index, boolean ascending) {
        super.sortColumn(index, ascending);
        sortColumn = index;
        sortAscending = ascending;

        Collections.sort(roots);
        for (Iterator<ContextEventTreeNode> it = roots.iterator(); it.hasNext();) {
            ContextEventTreeNode node = it.next();
            node.sortChildren();
        }
    }

    public boolean getSortAscending() {
        return sortAscending;
    }
}
