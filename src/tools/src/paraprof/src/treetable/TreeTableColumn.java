package edu.uoregon.tau.paraprof.treetable;

import java.awt.Color;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.text.DecimalFormat;
import java.text.NumberFormat;

import javax.swing.Icon;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTable;
import javax.swing.table.DefaultTableCellRenderer;
import javax.swing.table.TableCellRenderer;

import edu.uoregon.tau.paraprof.ParaProf;
import edu.uoregon.tau.perfdmf.Function;
import edu.uoregon.tau.perfdmf.FunctionProfile;
import edu.uoregon.tau.perfdmf.UtilFncs;

/**
 * Defines the columns of the treetable.
 * 
 * This is starting to get messy and should be rethought
 *
 * <P>CVS $Id: TreeTableColumn.java,v 1.6 2010/03/16 02:16:28 amorris Exp $</P>
 * @author  Alan Morris
 * @version $Revision: 1.6 $
 */
abstract public class TreeTableColumn {
    protected TreeTableWindow window;

    abstract public String toString();

    abstract public Object getValueFor(TreeTableNode node, boolean forSorting);

    abstract public TableCellRenderer getCellRenderer();

    public TreeTableColumn(TreeTableWindow window) {
        this.window = window;
    }

    
    protected Object getValueString(double value) {
        if (window.getDecimals() == -2) {
            return Double.toString(value); 
        } else if (window.getDecimals() == -1) {
            return new Double(value);
        } else {
            DecimalFormat format = null;
            if (window.getDecimals() == 0) {
                format = new DecimalFormat("#,###");
            } else if (window.getDecimals() == 1) {
                format = new DecimalFormat("#,##0.0");
            } else if (window.getDecimals() == 2) {
                format = new DecimalFormat("#,##0.00");
            } else if (window.getDecimals() == 3) {
                format = new DecimalFormat("#,##0.000");
            } else if (window.getDecimals() == 4) {
                format = new DecimalFormat("#,##0.0000");
            }
            String retval = format.format(value);
            return retval;
        }
        //System.out.println("String for " + value + " is " + retval);
    }
    
    protected Object adjustForUnits(double value, int metricID, boolean forSorting) {
        if (forSorting) {
            return new Double(value);
        }

        if (window.getPPTrial().getMetric(metricID).isTimeMetric()) {

            if (window.getPPTrial().getMetric(metricID).isTimeDenominator()) {
                if (window.getUnits() >= 3) {
                    return UtilFncs.getOutputString(3, value, ParaProf.defaultNumberPrecision,
                            window.getPPTrial().getMetric(metricID).isTimeDenominator()).trim();
                } else {
                    for (int i = 0; i < window.getUnits(); i++) {
                        value *= 1000;
                    }
                }
            } else {
                if (window.getUnits() >= 3) {
                    return UtilFncs.getOutputString(3, value, ParaProf.defaultNumberPrecision,
                            window.getPPTrial().getMetric(metricID).isTimeDenominator()).trim();
                } else {
                    for (int i = 0; i < window.getUnits(); i++) {
                        value /= 1000;
                    }
                }
            }
        }
        
        //return new Double(value);
        return getValueString(value);
    }

    public static class ColorIcon implements Icon {

        private Color color = Color.black;
        private int size = 12;

        public ColorIcon() {}

        public int getIconHeight() {
            return size;
        }

        public int getIconWidth() {
            return size;
        }

        public void paintIcon(Component c, Graphics g, int x, int y) {
            g.setColor(color);
            g.fillRect(x, y, size, size);
            g.setColor(Color.black);
            g.drawRect(x, y, size, size);
        }

        public void setColor(Color color) {
            this.color = color;
        }

    }

    static class ParaProfCellRenderer extends DefaultTableCellRenderer {
        /**
		 * 
		 */
		private static final long serialVersionUID = 5459926803089862887L;
		private NumberFormat formatter;
        private TreeTableWindow window;

        public ParaProfCellRenderer(TreeTableWindow window) {
            super();
            this.window = window;
        }

        public Component getTableCellRendererComponent(JTable table, Object value, boolean isSelected, boolean hasFocus, int row,
                int column) {
            // TODO Auto-generated method stub

            Component c = super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column);

            // URL url = ParaProfTreeCellRenderer.class.getResource("green-ball.gif");
            //this.setIcon(new ImageIcon(url));

            if (value instanceof TreeTableNode) {
                //this.setIcon(((TreeTableNode) value).getIcon());
            }

            column = table.convertColumnIndexToModel(column) - 1;
            TreeTableColumn ttColumn = window.getColumns().get(column);
            Object result = ttColumn.getValueFor((TreeTableNode) value, false);

            setHorizontalAlignment(JLabel.RIGHT);

            if (result instanceof Double) {
                //              setHorizontalAlignment(JLabel.RIGHT);

                if (formatter == null) {
                    formatter = NumberFormat.getInstance();
                }
                setText((result == null) ? "" : formatter.format(result));
            } else {
                //                setHorizontalAlignment(JLabel.LEFT);
                setText((result == null) ? "" : result.toString());
            }

            return c;
        }

        public void setValue(Object value) {
            return;

            //TreeTableColumn column = window.getColumns().get(
            //value = ((TreeTableNode)value).get

        }
    }

    static class RegularMetricCellRenderer extends JPanel implements TableCellRenderer {
        /**
		 * 
		 */
		private static final long serialVersionUID = -4911710251628231833L;
		private NumberFormat formatter;
        private TreeTableWindow window;

        private JLabel iconLabel = new JLabel();
        private JLabel textLabel = new JLabel();
        private ColorIcon colorIcon = new ColorIcon();

        public RegularMetricCellRenderer(TreeTableWindow window) {
            super();
            this.window = window;
            iconLabel.setHorizontalAlignment(JLabel.LEFT);
            textLabel.setHorizontalAlignment(JLabel.RIGHT);
            iconLabel.setIcon(colorIcon);
            this.setLayout(new GridBagLayout());

            GridBagConstraints gbc = new GridBagConstraints();

            gbc.fill = GridBagConstraints.BOTH;
            gbc.anchor = GridBagConstraints.WEST;
            gbc.insets = new Insets(0, 5, 0, 0);
            gbc.weightx = 0.5;
            gbc.weighty = 0.5;
            this.add(iconLabel, gbc);

            gbc.anchor = GridBagConstraints.EAST;
            this.add(textLabel, gbc);
        }

        public Component getTableCellRendererComponent(JTable table, Object value, boolean isSelected, boolean hasFocus, int row,
                int column) {

            column = table.convertColumnIndexToModel(column) - 1;

            textLabel.setFont(table.getFont());

            TreeTableNode node = (TreeTableNode) value;

            RegularMetricColumn ttColumn = (RegularMetricColumn) window.getColumns().get(column);

            Color color = node.getColor(ttColumn.getMetricID());

            if (node.getModel().getPPTrial().getNumberOfMetrics() == 1) {
                iconLabel.setIcon(null);
            } else {
                iconLabel.setIcon(colorIcon);
            }

            iconLabel.setVisible(color != null);
            if (color != null) {
                colorIcon.setColor(color);
            }

            Object result = ttColumn.getValueFor(node, false);

            if (result instanceof Double) {

                if (formatter == null) {
                    formatter = NumberFormat.getInstance();
                }

                textLabel.setText((result == null) ? "" : formatter.format(result));
            } else {
                textLabel.setText((result == null) ? "" : result.toString());
            }

            return this;
        }

    }

    static class RegularMetricColumn extends TreeTableColumn {
        private int metricID;

        public RegularMetricColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public String toString() {
            return window.getPPTrial().getMetricName(metricID);
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();

            if (fp == null) {
                return null;
            }
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (node.getExpanded()) {
                return adjustForUnits(fp.getExclusive(snapshot, metricID), metricID, forSorting);
            } else {
                return adjustForUnits(fp.getInclusive(snapshot, metricID), metricID, forSorting);
            }
        }

        public TableCellRenderer getCellRenderer() {
            return new RegularMetricCellRenderer(window);
        }

        public int getMetricID() {
            return metricID;
        }

    }

    static class RegularPercentMetricColumn extends RegularMetricColumn {
        private int metricID;

        public RegularPercentMetricColumn(TreeTableWindow window, int metricID) {
            super(window, metricID);
            this.metricID = metricID;
        }

        public String toString() {
            return window.getPPTrial().getMetricName(metricID) + " %";
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            if (forSorting) {
                if (node.getExpanded()) {
                    return new Double(fp.getExclusivePerCall(snapshot, metricID));
                } else {
                    return new Double(fp.getInclusivePerCall(snapshot, metricID));
                }
            }

            DecimalFormat dF = new DecimalFormat("##0.0");
            if (node.getExpanded()) {
                return dF.format(fp.getExclusivePercent(snapshot, metricID)) + "%";
            } else {
                return dF.format(fp.getInclusivePercent(snapshot, metricID)) + "%";
            }
        }

        public TableCellRenderer getCellRenderer() {
            return new RegularMetricCellRenderer(window);

            //            return new ParaProfCellRenderer(window);
        }

        public int getMetricID() {
            return metricID;
        }

    }

    static class RegularPerCallMetricColumn extends RegularMetricColumn {
        private int metricID;

        public RegularPerCallMetricColumn(TreeTableWindow window, int metricID) {
            super(window, metricID);
            this.metricID = metricID;
        }

        public String toString() {
            return window.getPPTrial().getMetricName(metricID) + " / Call";
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            if (node.getExpanded()) {
                return adjustForUnits(fp.getExclusivePerCall(snapshot, metricID), metricID, forSorting);
            } else {
                return adjustForUnits(fp.getInclusivePerCall(snapshot, metricID), metricID, forSorting);
            }
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

        public int getMetricID() {
            return metricID;
        }

    }

    static class InclusivePercentColumn extends TreeTableColumn {
        private int metricID;

        public InclusivePercentColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public String toString() {
            return "Inclusive " + window.getPPTrial().getMetricName(metricID) + " %";
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            if (forSorting) {
                return new Double(fp.getInclusivePercent(snapshot, metricID));
            }

            DecimalFormat dF = new DecimalFormat("##0.0");
            return dF.format(fp.getInclusivePercent(metricID)) + "%";
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

        public int getMetricID() {
            return metricID;
        }

    }

    static class ExclusivePercentColumn extends TreeTableColumn {
        private int metricID;

        public ExclusivePercentColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public String toString() {
            return "Exclusive " + window.getPPTrial().getMetricName(metricID) + " %";
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            if (forSorting) {
                return new Double(fp.getExclusivePercent(snapshot, metricID));
            }

            DecimalFormat dF = new DecimalFormat("##0.0");
            return dF.format(fp.getExclusivePercent(metricID)) + "%";
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

        public int getMetricID() {
            return metricID;
        }

    }

    static class InclusiveColumn extends TreeTableColumn {
        private int metricID;

        public InclusiveColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public String toString() {
            return "Inclusive " + window.getPPTrial().getMetricName(metricID);
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            return adjustForUnits(fp.getInclusive(snapshot, metricID), metricID, forSorting);
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

    }

    static class InclusivePerCallColumn extends TreeTableColumn {
        private int metricID;

        public InclusivePerCallColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public String toString() {
            return "Inclusive " + window.getPPTrial().getMetricName(metricID) + " / Call";
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            return adjustForUnits(fp.getInclusivePerCall(snapshot, metricID), metricID, forSorting);
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

    }

    static class ExclusiveColumn extends TreeTableColumn {
        private int metricID;

        public ExclusiveColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public String toString() {
            return "Exclusive " + window.getPPTrial().getMetricName(metricID);
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();

            if (fp == null) {
                return null;
            }

            int snapshot = window.getPPTrial().getSelectedSnapshot();
            return adjustForUnits(fp.getExclusive(snapshot, metricID), metricID, forSorting);
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

    }

    static class ExclusivePerCallColumn extends TreeTableColumn {
        private int metricID;

        public ExclusivePerCallColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public String toString() {
            return "Exclusive " + window.getPPTrial().getMetricName(metricID) + " / Call";
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            return adjustForUnits(fp.getExclusivePerCall(snapshot, metricID), metricID, forSorting);
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

    }

    static class NumSubrColumn extends TreeTableColumn {
        public String toString() {
            return "Child Calls";
        }

        public NumSubrColumn(TreeTableWindow window) {
            super(window);
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            if (node == null) {
                return null;
            }
            FunctionProfile fp = node.getFunctionProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            if (fp == null) {
                return null;
            }

            return new Double(fp.getNumSubr(snapshot));
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }

    }

    static class NumCallsColumn extends TreeTableColumn {
        public String toString() {
            return "Calls";
        }

        public NumCallsColumn(TreeTableWindow window) {
            super(window);
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();

            if (fp == null) {
                return null;
            }

            int snapshot = window.getPPTrial().getSelectedSnapshot();
            return new Double(fp.getNumCalls(snapshot));
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }
    }

    static class StdDevColumn extends TreeTableColumn {

        private int metricID;

        public String toString() {
            return "Std Dev";
        }

        public StdDevColumn(TreeTableWindow window, int metricID) {
            super(window);
            this.metricID = metricID;
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            FunctionProfile fp = node.getFunctionProfile();

            if (fp == null) {
                return null;
            }

            Function f = fp.getFunction();
            fp = f.getStddevProfile();
            int snapshot = window.getPPTrial().getSelectedSnapshot();

            return new Double(fp.getExclusive(snapshot, metricID));
        }

        public TableCellRenderer getCellRenderer() {
            return new ParaProfCellRenderer(window);
        }
    }

    static class MiniHistogramCellRenderer implements TableCellRenderer {
        private TreeTableWindow window;

        public MiniHistogramCellRenderer(TreeTableWindow window) {
            this.window = window;
        }

        public Component getTableCellRendererComponent(JTable table, Object value, boolean isSelected, boolean hasFocus, int row,
                int column) {

            column = table.convertColumnIndexToModel(column) - 1;
            TreeTableNode node = (TreeTableNode) value;

            MiniHistogramColumn col = (MiniHistogramColumn) window.getColumns().get(column);

            Function f = (Function) col.getValueFor(node, false);

            if (f == null) {
                return new JLabel("");
            }
            return new MiniHistogram(window.getPPTrial(), f);

        }
    }

    public static class MiniHistogramColumn extends TreeTableColumn {

        public MiniHistogramColumn(TreeTableWindow window) {
            super(window);
        }

        public String toString() {
            return "Histogram";
        }

        public Object getValueFor(TreeTableNode node, boolean forSorting) {
            if (node.getFunctionProfile() == null) {
                return null;
            }
            return node.getFunctionProfile().getFunction();
        }

        public TableCellRenderer getCellRenderer() {
            return new MiniHistogramCellRenderer(window);
        }

    }

}
