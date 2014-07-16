package edu.uoregon.tau.perfexplorer.client;

import java.util.List;

import javax.swing.JTree;
import javax.swing.event.TreeExpansionEvent;
import javax.swing.event.TreeExpansionListener;
import javax.swing.event.TreeWillExpandListener;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.DefaultTreeModel;
import javax.swing.tree.TreeModel;
import javax.swing.tree.TreePath;

import edu.uoregon.tau.perfdmf.Application;
import edu.uoregon.tau.perfdmf.Experiment;
import edu.uoregon.tau.perfdmf.IntervalEvent;
import edu.uoregon.tau.perfdmf.Metric;
import edu.uoregon.tau.perfdmf.View;
import edu.uoregon.tau.perfdmf.Trial;


public class PerfExplorerTreeExpansionListener implements TreeExpansionListener, TreeWillExpandListener {

	private JTree tree;
	public PerfExplorerTreeExpansionListener(JTree tree) {
		super();
		this.tree = tree;
	}

	public void treeWillExpand (TreeExpansionEvent e) {

		TreePath path = e.getPath();
		if (path == null)
			return;
		DefaultMutableTreeNode node = (DefaultMutableTreeNode) path.getLastPathComponent();
		if (!node.isRoot()) {
			node.removeAllChildren();
			TreeModel model = tree.getModel();
			if (model instanceof DefaultTreeModel) {
				DefaultTreeModel dModel = (DefaultTreeModel)model;
				dModel.reload(node);
            }
		}

		Object object = node.getUserObject();
		if (node.isRoot()) {
			PerfExplorerJTree.refreshDatabases();
		} else if (node.toString() != null && node.toString().startsWith("jdbc:")) {
			// get the schema version for the connection
			int index = PerfExplorerJTree.getConnectionIndex(node);
			int schemaVersion = PerfExplorerConnection.getConnection().getSchemaVersion(index);
			if (object instanceof ConnectionNodeObject) {
				ConnectionNodeObject tmp = (ConnectionNodeObject)object;
				tmp.setString(PerfExplorerConnection.getConnection().getConnectionStrings().get(index));
				PerfExplorerJTree.nodeChanged(node);
			}
            if (schemaVersion < 1) {
            	PerfExplorerJTree.addApplicationNodes(node, false);
            	PerfExplorerJTree.getTree().addViewNode(node);
            } else {
				PerfExplorerJTree.addTAUdbViewNodes (node, 0);            	
            }
		} else if (node.toString() != null && node.toString().equals("Views")) {
			PerfExplorerJTree.addViewNodes(node, 0);
		} else {
			if (object instanceof Application) {
				Application app = (Application)object;
				PerfExplorerJTree.addExperimentNodes (node, app, true);
			} else if (object instanceof Experiment) {
				Experiment exp = (Experiment)object;
				PerfExplorerJTree.addTrialNodes (node, exp);
			} else if (object instanceof Trial) {
				Trial trial = (Trial)object;
				PerfExplorerJTree.addMetricNodes (node, trial);
			} else if (object instanceof Metric) {
				Metric metric = (Metric)object;
				// get the trial
				DefaultMutableTreeNode pNode = (DefaultMutableTreeNode)node.getParent();
				object = pNode.getUserObject();
				Trial trial = (Trial)object;
				// find the metric index
				List<Metric> metrics = trial.getMetrics();
				for (int i = 0; i < metrics.size() ; i++) {
					Metric m = metrics.get(i);
					if (m.getID() == metric.getID()) {
						PerfExplorerJTree.addEventNodes (node, trial, i);
						break;
					}
				}
			} else if (object instanceof IntervalEvent) {
				// do nothing
			} else if (object instanceof View) {
				View view = (View) object;
				PerfExplorerJTree.addViewNodes(node, view.getID());
			} else {
				System.out.println("unknown!");
			}
		}
	}

	public void treeExpanded(TreeExpansionEvent e) {
	}

	public void treeWillCollapse (TreeExpansionEvent e) {
	/*
		TreePath path = e.getPath();
		if (path == null)
			return;
		DefaultMutableTreeNode node = (DefaultMutableTreeNode) path.getLastPathComponent();
		if (!node.isRoot()) {
			node.removeAllChildren();
		}
		*/
	}

	public void treeCollapsed(TreeExpansionEvent e) {
	}
}
