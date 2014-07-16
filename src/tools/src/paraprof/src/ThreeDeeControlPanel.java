package edu.uoregon.tau.paraprof;

import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.AdjustmentEvent;
import java.awt.event.AdjustmentListener;
import java.io.File;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map.Entry;
import java.util.Set;
import java.util.TreeSet;
import java.util.Vector;

import javax.swing.BorderFactory;
import javax.swing.ButtonGroup;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JScrollBar;
import javax.swing.JScrollPane;
import javax.swing.JSlider;
import javax.swing.JSpinner;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.ScrollPaneConstants;
import javax.swing.SpinnerModel;
import javax.swing.SpinnerNumberModel;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import javax.swing.plaf.basic.BasicComboPopup;
import javax.swing.plaf.basic.ComboPopup;
import javax.swing.plaf.metal.MetalComboBoxUI;

import org.apache.batik.ext.swing.GridBagConstants;

import edu.uoregon.tau.common.MetaDataMap.MetaDataKey;
import edu.uoregon.tau.common.MetaDataMap.MetaDataValue;
import edu.uoregon.tau.common.Utility;
import edu.uoregon.tau.paraprof.enums.UserEventValueType;
import edu.uoregon.tau.paraprof.enums.ValueType;
import edu.uoregon.tau.paraprof.enums.VisType;
import edu.uoregon.tau.perfdmf.Function;
import edu.uoregon.tau.perfdmf.Metric;
import edu.uoregon.tau.perfdmf.Thread;
import edu.uoregon.tau.perfdmf.UserEvent;
import edu.uoregon.tau.perfdmf.UtilFncs;
import edu.uoregon.tau.vis.Plot;
import edu.uoregon.tau.vis.SteppedComboBox;
import edu.uoregon.tau.vis.VisRenderer;

/**
 * This is the control panel for the ThreeDeeWindow.
 *    
 * TODO : ...
 *
 * <P>CVS $Id: ThreeDeeControlPanel.java,v 1.19 2010/01/28 00:27:41 amorris Exp $</P>
 * @author	Alan Morris
 * @version	$Revision: 1.19 $
 */
public class ThreeDeeControlPanel extends JPanel implements ActionListener {

    /**
	 * 
	 */
	private static final long serialVersionUID = -8413853906212906751L;

	private ThreeDeeSettings settings;

    private ThreeDeeWindow window;
    private ParaProfTrial ppTrial;

    private SteppedComboBox heightValueBox, heightMetricBox;
    private SteppedComboBox colorValueBox, colorMetricBox;

    private JScrollPane spane;//subPanel;
    private VisRenderer visRenderer;

    private JTextField heightValueField = new JTextField("");
    private JTextField colorValueField = new JTextField("");
    
    private JTextField minTopoField = new JTextField("");
    private JTextField maxTopoField = new JTextField("");

    private int selectedTab;
    private JTabbedPane tabbedPane; // keep a handle to remember the selected tab
    private ThreeDeeScalePanel scalePanel;

    public class SliderComboBox extends JComboBox {
        /**
		 * 
		 */
		private static final long serialVersionUID = -7178282357180311147L;
		/**
		 * 
		 */


		public SliderComboBox() {
            super();
            setUI(new SliderComboUI());
        }

        public SliderComboBox(Object obj[]) {
            super(obj);
            setUI(new SliderComboUI());
        }

        public class SliderComboUI extends MetalComboBoxUI {
            protected ComboPopup createPopup() {
                BasicComboPopup popup = new BasicComboPopup(comboBox) {
                    /**
					 * 
					 */
					private static final long serialVersionUID = -2126557896237148500L;

					protected JScrollPane createScroller() {
                        return new JScrollPane(list, ScrollPaneConstants.VERTICAL_SCROLLBAR_AS_NEEDED,
                                ScrollPaneConstants.HORIZONTAL_SCROLLBAR_AS_NEEDED);
                    }
                };
                return popup;
            }
        }
    }

    public ThreeDeeControlPanel(ThreeDeeWindow window, ThreeDeeSettings settings, ParaProfTrial ppTrial, VisRenderer visRenderer) {
        this.settings = settings;
        this.window = window;
        this.ppTrial = ppTrial;
        this.visRenderer = visRenderer;

        this.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0;
        gbc.weighty = 0;

        ButtonGroup group = new ButtonGroup();
        JRadioButton jrb = new JRadioButton(VisType.TRIANGLE_MESH_PLOT.toString(),
                settings.getVisType() == VisType.TRIANGLE_MESH_PLOT);
        jrb.addActionListener(this);
        group.add(jrb);
        addCompItem(this, jrb, gbc, 0, 0, 1, 1);

        jrb = new JRadioButton(VisType.BAR_PLOT.toString(), settings.getVisType() == VisType.BAR_PLOT);
        jrb.addActionListener(this);
        group.add(jrb);
        addCompItem(this, jrb, gbc, 0, 2, 1, 1);

        jrb = new JRadioButton(VisType.SCATTER_PLOT.toString(), settings.getVisType() == VisType.SCATTER_PLOT);
        jrb.addActionListener(this);
        group.add(jrb);
        addCompItem(this, jrb, gbc, 0, 3, 1, 1);
        
        //if(this.ppTrial.getTopologyArray()!=null&&ppTrial.getTopologyArray()[0]!=null){
      jrb = new JRadioButton(VisType.TOPO_PLOT.toString(), settings.getVisType() == VisType.TOPO_PLOT);
      jrb.addActionListener(this);
      group.add(jrb);
      addCompItem(this, jrb, gbc, 0, 4, 1, 1);//TODO: Do not enable this
        //}

//                jrb = new JRadioButton(VisType.CALLGRAPH.toString(), settings.getVisType() == VisType.CALLGRAPH);
//                jrb.addActionListener(this);
//                group.add(jrb);
//                addCompItem(this, jrb, gbc, 0, 4, 1, 1);//TODO: Do not enable this

        createSubPanel();

    }

    private void createSubPanel() {
        if (spane != null) {
            this.remove(spane);
        }
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

        JPanel subPanel=null;
        if (settings.getVisType() == VisType.SCATTER_PLOT ) {
            subPanel = createScatterPanel();
        }else if(settings.getVisType() == VisType.TOPO_PLOT){
        	subPanel = createTopoPanel();
        }else if (settings.getVisType() == VisType.CALLGRAPH) {
            subPanel = createCallGraphPanel();
        } else {
            subPanel = createFullDataPanel();
        }
        gbc.fill = GridBagConstraints.BOTH;
        gbc.anchor = GridBagConstraints.CENTER;
        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        Dimension subD = subPanel.getMinimumSize();
        
        subPanel.setPreferredSize(new Dimension((int)subD.getWidth(),(int)subD.getHeight()+100));
        subPanel.setSize(subPanel.getPreferredSize());
        
        spane=new JScrollPane(subPanel);
        addCompItem(this, spane, gbc, 0, 5, 1, 1);
        revalidate();
        validate();
        spane.setMinimumSize(new Dimension((int)subD.getWidth()+25,(int)subD.getHeight()));
        this.setPreferredSize(this.getMinimumSize());
    }

    private JPanel createScatterSelectionPanel(String name, final int index) {
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        //        panel.setBorder(BorderFactory.createLoweredBevelBorder());
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;

        //addCompItem(panel, new JLabel(name), gbc, 0, 0, 1, 2);

        final JTextField functionField;

        String fname = "   <none>";
        if (settings.getScatterFunctions()[index] != null) {
            fname = settings.getScatterFunctions()[index].getName();
        }

        functionField = new JTextField(fname);
        functionField.setToolTipText(fname);
        functionField.setEditable(false);
        functionField.setBorder(BorderFactory.createLoweredBevelBorder());
        functionField.setCaretPosition(0);

        Dimension d;
        final SteppedComboBox valueBox = new SteppedComboBox(ValueType.VALUES);
        d = valueBox.getPreferredSize();
        valueBox.setMinimumSize(new Dimension(50, valueBox.getMinimumSize().height));
        valueBox.setPopupWidth(d.width);

        final SteppedComboBox metricBox = new SteppedComboBox(ppTrial.getMetricArray());
        d = metricBox.getPreferredSize();
        metricBox.setMinimumSize(new Dimension(50, metricBox.getMinimumSize().height));
        metricBox.setPopupWidth(d.width);

        valueBox.setSelectedItem(settings.getScatterValueTypes()[index]);
        metricBox.setSelectedItem(settings.getScatterMetrics()[index]);

        ActionListener metricSelector = new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                try {
                    settings.setScatterValueType((ValueType) valueBox.getSelectedItem(), index);
                    settings.setScatterMetric((Metric) metricBox.getSelectedItem(), index);
                    window.redraw();
                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }
        };

        valueBox.addActionListener(metricSelector);
        metricBox.addActionListener(metricSelector);

        JButton functionButton = new JButton("...");
        functionButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                try {

                    FunctionSelectorDialog fSelector = new FunctionSelectorDialog(window, true,
                            ppTrial.getDisplayedFunctions().iterator(), settings.getScatterFunctions()[index], true, false);

                    if (fSelector.choose()) {
                        Function selectedFunction = (Function) fSelector.getSelectedObject();
                        settings.setScatterFunction(selectedFunction, index);

                        String fname = "   <none>";
                        if (settings.getScatterFunctions()[index] != null) {
                            fname = ParaProfUtils.getDisplayName(settings.getScatterFunctions()[index]);
                        }
                        functionField.setText(fname);
                        functionField.setToolTipText(fname);
                        window.redraw();
                    }

                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }
        });

        JPanel subPanel = new JPanel();
        subPanel.setLayout(new GridBagLayout());

        gbc.insets = new Insets(1, 1, 1, 1);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(subPanel, functionField, gbc, 0, 0, 1, 1);
        gbc.weightx = 0.0;
        gbc.weighty = 0.0;
        gbc.fill = GridBagConstraints.NONE;
        addCompItem(subPanel, functionButton, gbc, 1, 0, 1, 1);

        gbc.insets = new Insets(5, 5, 5, 5);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(panel, subPanel, gbc, 1, 0, 2, 1);
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;
        addCompItem(panel, valueBox, gbc, 1, 1, 1, 1);
        addCompItem(panel, metricBox, gbc, 2, 1, 1, 1);

        return panel;
    }
//    
//    private JPanel createTopoAtomicSelectionPanel(String name, final int i) {
//        JPanel panel = new JPanel();
//        panel.setLayout(new GridBagLayout());
//        //        panel.setBorder(BorderFactory.createLoweredBevelBorder());
//        GridBagConstraints gbc = new GridBagConstraints();
//
//        gbc.fill = GridBagConstraints.NONE;
//        gbc.anchor = GridBagConstraints.WEST;
//        gbc.weightx = 0.1;
//        gbc.weighty = 0.1;
//
//        //addCompItem(panel, new JLabel(name), gbc, 0, 0, 1, 2);
//
//        final JTextField functionField;
//
//        String fname = "   <none>";
//        if (settings.getTopoAtomic(i) != null) {
//            fname = settings.getTopoAtomic(i).getName();
//        }
//
//        functionField = new JTextField(fname);
//        functionField.setToolTipText(fname);
//        functionField.setEditable(false);
//        functionField.setBorder(BorderFactory.createLoweredBevelBorder());
//        functionField.setCaretPosition(0);
//
//        Dimension d;
//        final SteppedComboBox valueBox = new SteppedComboBox(UserEventValueType.VALUES);
//        d = valueBox.getPreferredSize();
//        valueBox.setMinimumSize(new Dimension(50, valueBox.getMinimumSize().height));
//        valueBox.setPopupWidth(d.width);
//
////        final SteppedComboBox metricBox = new SteppedComboBox(ppTrial.getMetricArray());
////        d = metricBox.getPreferredSize();
////        metricBox.setMinimumSize(new Dimension(50, metricBox.getMinimumSize().height));
////        metricBox.setPopupWidth(d.width);
//
//        valueBox.setSelectedItem(settings.getTopoUserEventValueType(i));
////        metricBox.setSelectedItem(settings.getTopoMetric());
//
//        ActionListener metricSelector = new ActionListener() {
//            public void actionPerformed(ActionEvent evt) {
//                try {
//                    settings.setTopoUserEventValueType((UserEventValueType) valueBox.getSelectedItem(), i);
//                    //settings.setTopoMetric((Metric) metricBox.getSelectedItem());
//                    window.redraw();
//                    //minTopoField.setText(window.getSelectedMinTopoValue());
//                    //maxTopoField.setText(window.getSelectedMaxTopoValue());
//                    //topoValField.setText(window.getStatMean());
//                } catch (Exception e) {
//                    ParaProfUtils.handleException(e);
//                }
//            }
//        };
//
//        valueBox.addActionListener(metricSelector);
//        //metricBox.addActionListener(metricSelector);
//
//        JButton functionButton = new JButton("...");
//        functionButton.addActionListener(new ActionListener() {
//            public void actionPerformed(ActionEvent evt) {
//                try {
//
//                    FunctionSelectorDialog fSelector = new FunctionSelectorDialog(window, true,
//                    		ppTrial.getDataSource().getUserEvents(), settings.getTopoAtomic(i), true, false);
//
//                    if (fSelector.choose()) {
//                        UserEvent selectedFunction = (UserEvent) fSelector.getSelectedObject();
//                        settings.setTopoAtomic(selectedFunction,i);
//
//                        String fname = "   <none>";
//                        if (settings.getTopoAtomic(i) != null) {
//                            fname = settings.getTopoAtomic(i).getName();//ParaProfUtils.getDisplayName(settings.getTopoAtomic());
//                        }
//                        functionField.setText(fname);
//                        functionField.setToolTipText(fname);
//                        window.redraw();
//                        //minTopoField.setText(window.getSelectedMinTopoValue());
//                        //maxTopoField.setText(window.getSelectedMaxTopoValue());
//                        //topoValField.setText(window.getStatMean());
//                    }
//
//                } catch (Exception e) {
//                    ParaProfUtils.handleException(e);
//                }
//            }
//        });
//
//        JPanel subPanel = new JPanel();
//        subPanel.setLayout(new GridBagLayout());
//
//        gbc.insets = new Insets(1, 1, 1, 1);
//
//        gbc.weightx = 1.0;
//        gbc.weighty = 1.0;
//        gbc.fill = GridBagConstraints.HORIZONTAL;
//        addCompItem(subPanel, functionField, gbc, 0, 0, 1, 1);
//        gbc.weightx = 0.0;
//        gbc.weighty = 0.0;
//        gbc.fill = GridBagConstraints.NONE;
//        addCompItem(subPanel, functionButton, gbc, 1, 0, 1, 1);
//
//        gbc.insets = new Insets(5, 5, 5, 5);
//
//        gbc.weightx = 1.0;
//        gbc.weighty = 1.0;
//        gbc.fill = GridBagConstraints.HORIZONTAL;
//        addCompItem(panel, subPanel, gbc, 1, 0, 2, 1);
//        gbc.weightx = 0.5;
//        gbc.weighty = 0.5;
//        addCompItem(panel, valueBox, gbc, 1, 1, 1, 1);
//        //addCompItem(panel, metricBox, gbc, 2, 1, 1, 1);
//
//        return panel;
//    }
//    
    private JPanel createTopoIntervalSelectionPanel(String name, final int dex) {
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        //        panel.setBorder(BorderFactory.createLoweredBevelBorder());
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;
        
        Object[] profDataTypes={"Timer","Atomic","Metadata"};
        
        final JComboBox atomic = new JComboBox(profDataTypes);
        atomic.setToolTipText("Select type of values to use for this axis");
        //addCompItem(panel, new JLabel(name), gbc, 0, 0, 1, 2);

        final JTextField functionField;

        String fname = "   <none>";
        //String fname = "   <none>";
        if(settings.getTopoFunction(dex)==null&&settings.getScatterFunctions()[dex] != null){
        	settings.setTopoFunction(settings.getScatterFunctions()[dex], dex);
        }
        
        if (settings.getTopoFunction(dex) != null) {
            fname = settings.getTopoFunction(dex).getName();
        }
//        if (settings.getTopoFunction(i) != null) {
//            fname = settings.getTopoFunction(i).getName();
//        }

        functionField = new JTextField(fname);
        functionField.setToolTipText(fname);
        functionField.setEditable(false);
        functionField.setBorder(BorderFactory.createLoweredBevelBorder());
        functionField.setCaretPosition(0);

        Dimension d;
        final SteppedComboBox valueBox = new SteppedComboBox(ValueType.VALUES);
        d = valueBox.getPreferredSize();
        valueBox.setMinimumSize(new Dimension(50, valueBox.getMinimumSize().height));
        valueBox.setPopupWidth(d.width);

        final SteppedComboBox metricBox = new SteppedComboBox(ppTrial.getMetricArray());
        d = metricBox.getPreferredSize();
        metricBox.setMinimumSize(new Dimension(50, metricBox.getMinimumSize().height));
        metricBox.setPopupWidth(d.width);

        valueBox.setSelectedItem(settings.getTopoValueType(dex));
        //System.out.println(settings.getTopoValueType(dex));
        metricBox.setSelectedItem(settings.getTopoMetric(dex));
        //final int dex = i;
        ActionListener metricSelector = new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
            	
                try {
                	Object si=valueBox.getSelectedItem();
                	if(si==null)
                	{
                		return;
                	}
                	
                	if(atomic.getSelectedIndex()==0&&si instanceof ValueType){//!atomic.isSelected()){

                    settings.setTopoValueType((ValueType) valueBox.getSelectedItem(),dex);
                    settings.setTopoMetric((Metric) metricBox.getSelectedItem(),dex);
                    settings.intervalETDex[dex]=valueBox.getSelectedIndex();
                	
                	}
                	else if(atomic.getSelectedIndex()==1 && si instanceof UserEventValueType){
                		 settings.setTopoUserEventValueType((UserEventValueType) valueBox.getSelectedItem(), dex);
                		 settings.atomicETDex[dex]=valueBox.getSelectedIndex();
                	}
                	else if(atomic.getSelectedIndex()==2){
                		//settings.setTopoMetadata(valueBox.getSelectedItem(),dex);
                		//settings.metadataETDex[dex]=valueBox.getSelectedIndex();
                		//TODO: Make sure we don't need to set anything else here.
                	}
                	 window.redraw();
                     minTopoField.setText(window.getSelectedMinTopoValue());
                     maxTopoField.setText(window.getSelectedMaxTopoValue());
                     topoValField.setText(window.getStatMean()+window.getSelectedThread());
                    
                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }
        };

        valueBox.addActionListener(metricSelector);
        metricBox.addActionListener(metricSelector);

        atomic.addActionListener(new ActionListener(){
        	public void actionPerformed(ActionEvent evt){
        		
        		String fname=null;
        		
        		if(atomic.getSelectedIndex()==1){
        			
        			int numUE = ppTrial.getDataSource().getNumUserEvents();
        			if(numUE<1){
        				atomic.setSelectedIndex(0);//.setSelected(false);
        				return;
        			}
        			
        			metricBox.setEnabled(false);
        			valueBox.setEditable(true);
        			valueBox.removeAllItems();
        			for(int i=0;i<UserEventValueType.VALUES.length;i++){
        				valueBox.addItem(UserEventValueType.VALUES[i]);
        			}
        			valueBox.setSelectedIndex(settings.atomicETDex[dex]);
        			if(settings.getTopoAtomic(dex)==null){
        				
        				UserEvent tmpUE = ppTrial.getDataSource().getUserEventIterator().next();
        				settings.setTopoAtomic(tmpUE, dex);
        			}
        			fname=settings.getTopoAtomic(dex).getName();
        		}
        		else if(atomic.getSelectedIndex()==0){
        			metricBox.setEnabled(true);
        			valueBox.setEditable(true);
        			valueBox.removeAllItems();
        			for(int i=0;i<ValueType.VALUES.length;i++){
        				valueBox.addItem(ValueType.VALUES[i]);
        			}
        			valueBox.setSelectedIndex(settings.intervalETDex[dex]);
        			fname = ParaProfUtils.getDisplayName(settings.getTopoFunction(dex));
        		}
        		else if(atomic.getSelectedIndex()==2){
        			metricBox.setEnabled(false);
        			valueBox.removeAllItems();
        			valueBox.setEditable(false);
        			MetaDataKey mdk=settings.getTopoMetadata(dex);
        			
        			if(mdk==null){
        				Thread t = ppTrial.getDataSource().getThread(0, 0, 0);
                		if(t==null){
                			t=ppTrial.getDataSource().getThreads().get(0);
                		}
                		mdk=t.getMetaData().keySet().iterator().next();
                		
                		settings.setTopoMetadata(mdk, dex);
        			}
        			
        			fname=mdk.toString();
        			//valueBox.setSelectedIndex(settings.meticETDex[dex]);
        			//fname = settings.getTopoMetric(dex);
        			//TODO: Metadata support
        		}
        		
        		
        		settings.setDataType(atomic.getSelectedIndex(), dex);
        		
        		functionField.setText(fname);
                functionField.setToolTipText(fname);
            	window.redraw();
                minTopoField.setText(window.getSelectedMinTopoValue());
                maxTopoField.setText(window.getSelectedMaxTopoValue());
                topoValField.setText(window.getStatMean()+window.getSelectedThread());
        		
        		
        	}
        });
        
        
        JButton functionButton = new JButton("...");
        functionButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                try {
                	
                	String fname = functionField.getText();
                	if(fname==null||fname.length()==0) 
                		fname = "   <none>";
                	
                	if(atomic.getSelectedIndex()==0){
                	
                    FunctionSelectorDialog fSelector = new FunctionSelectorDialog(window, true,
                            ppTrial.getDisplayedFunctions().iterator(), settings.getTopoFunction(dex), true, false);

                    if (fSelector.choose()) {
                        Function selectedFunction = (Function) fSelector.getSelectedObject();
                        settings.setTopoFunction(selectedFunction,dex);

                        //String fname = "   <none>";
                        if (settings.getTopoFunction(dex) != null) {
                            fname = ParaProfUtils.getDisplayName(settings.getTopoFunction(dex));
                        }
                        

                    }
                    
                	}
                	else if(atomic.getSelectedIndex()==1){
                        FunctionSelectorDialog fSelector = new FunctionSelectorDialog(window, true,
                        		ppTrial.getDataSource().getUserEventIterator(), settings.getTopoAtomic(dex), true, false);

                        if (fSelector.choose()) {
                            UserEvent selectedFunction = (UserEvent) fSelector.getSelectedObject();
                            settings.setTopoAtomic(selectedFunction,dex);

                            //String fname = "   <none>";
                            if (settings.getTopoAtomic(dex) != null) {
                                fname = settings.getTopoAtomic(dex).getName();//ParaProfUtils.getDisplayName(settings.getTopoAtomic());
                            }

                            
                        }
                	}
                	else if(atomic.getSelectedIndex()==2){
                		Thread t = ppTrial.getDataSource().getThread(0, 0, 0);
                		if(t==null){
                			t=ppTrial.getDataSource().getThreads().get(0);
                		}
                		
                		Set<MetaDataKey> mdkSet= new TreeSet<MetaDataKey>();
                		mdkSet.addAll(t.getMetaData().keySet());
                		mdkSet.addAll(ppTrial.getDataSource().getMetaData().keySet());
                		         		
                		//t.getMetaData().keySet().iterator();
                		FunctionSelectorDialog fSelector = new FunctionSelectorDialog(window, true,
                				mdkSet.iterator(), settings.getTopoMetadata(dex), true, false);
                		
                		if (fSelector.choose()) {
                            MetaDataKey metadataKey = (MetaDataKey) fSelector.getSelectedObject();
                            settings.setTopoMetadata(metadataKey,dex);

                            //String fname = "   <none>";
                            if (settings.getTopoMetadata(dex) != null) {
                                fname = settings.getTopoMetadata(dex).toString();
                            }

                		}
                		//TODO: metadata support
                	}
                	functionField.setText(fname);
                    functionField.setToolTipText(fname);
                	window.redraw();
                    minTopoField.setText(window.getSelectedMinTopoValue());
                    maxTopoField.setText(window.getSelectedMaxTopoValue());
                    topoValField.setText(window.getStatMean()+window.getSelectedThread());

                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }
        });

        JPanel subPanel = new JPanel();
        subPanel.setLayout(new GridBagLayout());

        gbc.insets = new Insets(1, 1, 1, 1);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(subPanel, functionField, gbc, 0, 0, 1, 1);
        gbc.weightx = 0.0;
        gbc.weighty = 0.0;
        gbc.fill = GridBagConstraints.NONE;
        addCompItem(subPanel, functionButton, gbc, 1, 0, 1, 1);

        gbc.insets = new Insets(5, 5, 5, 5);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        
        addCompItem(panel,new JLabel(name),gbc,1,0,1,1);
        addCompItem(panel,atomic,gbc,2,0,1,1);
        
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(panel, subPanel, gbc, 1, 1, 2, 1);
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;
        addCompItem(panel, valueBox, gbc, 1, 2, 1, 1);
        addCompItem(panel, metricBox, gbc, 2, 2, 1, 1);

        return panel;
    }

    private SteppedComboBox topoComboBox;// = new SteppedComboBox();
    private int customTopoDex=-1;
    private int selectedTopoDex=0;
    
    private void updateTopoList(){
    	int maxDex = topoComboBox.getItemCount()-1;
    	for(int i=maxDex;i>customTopoDex+1;i--)
    	{
    		topoComboBox.removeItemAt(i);
    	}
    	
    	String defFile = settings.getTopoDefFile();
    	if(defFile!=null){
    		List<String> tnames = ThreeDeeGeneralPlotUtils.getCustomTopoNames(defFile);
    		for(int i =0;i<tnames.size();i++){
    			topoComboBox.addItem(tnames.get(i));
    		}
    	}
    }
    
    private boolean checkDisableTopoWidgets(String topo){
    	boolean b = (topo.equals("Custom")||topo.equals("BGQ")||topo.equals("Map")||topo.startsWith("Topo"));
    	return !b;
    	
    }
    
    private void switchTopoSelectPanels(boolean active){
    	for(int i =0;i<3;i++){
    		if(topoSelectPanels[i]!=null)
    		{
    			topoSelectPanels[i].setEnabled(active);
    			Component[] ca = topoSelectPanels[i].getComponents();
    			for(int j=0;j<ca.length;j++){
    				ca[j].setEnabled(active);
    				if(ca[j] instanceof JPanel){
    					Component[] cb=((JPanel)ca[j]).getComponents();
    					for(int k=0;k<cb.length;k++){
    						cb[k].setEnabled(active);
    					}
    				}
    			}
    		}
    		
    	}
    }
    
    private static final String CUSTOM="Custom";
    private JPanel createTopoSelectionPanel(String name) {
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        //        panel.setBorder(BorderFactory.createLoweredBevelBorder());
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;
        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        //addCompItem(panel, new JLabel(name), gbc, 0, 0, 1, 2);

       

        Dimension d;
        
        Vector<String> topos = ppTrial.getTopologyArray();
        
        //String[] a = new String[topos.size()];
        topos.add(CUSTOM);
        customTopoDex=topos.size()-1;
        topos.add("Map");
		//return topos;//topos.toArray(a);
        
        topoComboBox = new SteppedComboBox(topos);
        

        //topoComboBox.addItem("Custom");
        //valueBox.addItem("Sphere");
        if(selectedTopoDex<topoComboBox.getItemCount())
        	topoComboBox.setSelectedIndex(selectedTopoDex);
        d = topoComboBox.getPreferredSize();
        topoComboBox.setMinimumSize(new Dimension(100, topoComboBox.getMinimumSize().height));
        topoComboBox.setPopupWidth(d.width);
        
        updateTopoList();
        
        settings.setTopoCart((String)topoComboBox.getSelectedItem());

        //topoComboBox.setSelectedItem(settings.getTopoValueType());gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.weightx = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;

        ActionListener topoSelector = new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                try {
                    settings.setTopoCart((String)topoComboBox.getSelectedItem());//TODO: Reset topo labels when this changes!
                    boolean useCustom=topoComboBox.getSelectedIndex()>customTopoDex+1;
                    settings.setCustomTopo(useCustom);
                    
                    switchTopoSelectPanels(checkDisableTopoWidgets((String)topoComboBox.getSelectedItem()));
                    
                    boolean useMap=topoComboBox.getSelectedIndex()==customTopoDex+1;
                    if(useMap){
                    	String s = settings.getTopoMapFile();
                    	if(s==null){
                    		topoComboBox.setSelectedIndex(selectedTopoDex);
                    		System.out.println("Select a valid map file");//TODO: use a real error message.
                    		return;
                    	}
                    }
                    
                    
                    selectedTopoDex=topoComboBox.getSelectedIndex();
                    resetTopoAxisSliders(true);
                    window.redraw();
                    resetTopoAxisSliders(true);
                    
                    for(int i=0;i<customAxisSpinners.length;i++)
                    {
                    	if(customAxisSpinners[i]!=null)
                    		customAxisSpinners[i].setEnabled(settings.getTopoCart().equals("Custom"));
                    }
                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }
        };

        topoComboBox.addActionListener(topoSelector);
        if(selectedTopoDex<topoComboBox.getItemCount())
        	topoComboBox.setSelectedIndex(selectedTopoDex);
        
        JButton topoFileButton = new JButton("...");
        
        ActionListener topoFileSelector = new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                try {
                	JFileChooser tsDialog = new JFileChooser("Select a topology definition file");
                	if(ParaProf.schemaLocation!=null){
                		File topoDir = new File(ParaProf.schemaLocation+File.separatorChar+"topology");
                		if (topoDir.canRead()){
                			tsDialog.setCurrentDirectory(topoDir);
                		}
                	}
                	//tsDialog.setVisible(true);
                    tsDialog.showOpenDialog(window);
                    File dFile = tsDialog.getSelectedFile();
                    if(dFile!=null&&dFile.exists()&&dFile.canRead()){
                    String path = dFile.getAbsolutePath();
                    settings.setTopoDefFile(path);
                    updateTopoList();}
                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }
        };
        
        topoFileButton.addActionListener(topoFileSelector);

        
JButton mapFileButton = new JButton("map");
        
        ActionListener mapFileSelector = new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                try {
                	JFileChooser tsDialog = new JFileChooser("Select a topology map file");
//                	if(ParaProf.schemaLocation!=null){
//                		File topoDir = new File(ParaProf.schemaLocation+File.separatorChar+"topology");
//                		if (topoDir.canRead()){
//                			tsDialog.setCurrentDirectory(topoDir);
//                		}
//                	}
                	//tsDialog.setVisible(true);
                    tsDialog.showOpenDialog(window);
                    File dFile = tsDialog.getSelectedFile();
                    if(dFile!=null&&dFile.exists()&&dFile.canRead()){
                    String path = dFile.getAbsolutePath();
                    settings.setTopoMapFile(path);
                    //updateTopoList();
                    }
                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }
        };
        
        mapFileButton.addActionListener(mapFileSelector);
        
        
        JPanel subPanel = new JPanel();
        subPanel.setLayout(new GridBagLayout());

        gbc.insets = new Insets(1, 1, 1, 1);



        gbc.insets = new Insets(5, 5, 5, 5);

        gbc.weightx = 0.5;
        gbc.weighty = 0.5;

        addCompItem(panel, new JLabel("Topology"), gbc, 0, 1, 1, 1);
        gbc.weighty = 1.0;
        gbc.weightx = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(panel, topoComboBox, gbc, 1, 1, 1, 1);
        gbc.weighty = 0.0;
        gbc.weightx = 0.0;
        gbc.fill = GridBagConstraints.NONE;
        addCompItem(panel, topoFileButton, gbc, 2, 1, 1, 1);
        addCompItem(panel, mapFileButton, gbc, 3, 1, 1, 1);
        
        gbc.weighty = 0;
        gbc.weightx = 0;
        addCompItem(panel, customAxisLabels [0]=new JLabel("X Axis"), gbc, 0, 3, 1, 1);
        addCompItem(panel, createTopoCustomSliderPanel(0), gbc, 1, 3, 1, 1);
        gbc.weightx = 0;
        addCompItem(panel, customAxisLabels [1]=new JLabel("Y Axis"), gbc, 0, 4, 1, 1);
        addCompItem(panel, createTopoCustomSliderPanel(1), gbc, 1, 4, 1, 1);
        gbc.weightx = 0;
        addCompItem(panel, customAxisLabels [2]=new JLabel("Z Axis"), gbc, 0, 5, 1, 1);
        addCompItem(panel, createTopoCustomSliderPanel(2), gbc, 1, 5, 1, 1);

        return panel;
    }
    
//    private JPanel createTopoDimSelectionPanel(String name, final int index) {
//        JPanel panel = new JPanel();
//        panel.setLayout(new GridBagLayout());
//        GridBagConstraints gbc = new GridBagConstraints();
//
//        gbc.fill = GridBagConstraints.NONE;
//        gbc.anchor = GridBagConstraints.WEST;
//        gbc.weightx = 0.1;
//        gbc.weighty = 0.1;
//
//        final JSlider topoValue = new JSlider(JSlider.HORIZONTAL,1,50,10);
//
//        topoValue.setValue(settings.getTopoValues()[index]);
//        ChangeListener topoSelector = new ChangeListener() {
//  
//
//			public void stateChanged(ChangeEvent e) {
//				 try {
//	                    settings.setTopoValues(topoValue.getValue(), index);
//	                    window.redraw();
//	                } catch (Exception evt) {
//	                    ParaProfUtils.handleException(evt);
//	                }
//				
//			}
//        };
//        
//        topoValue.addChangeListener(topoSelector);
//
//        gbc.insets = new Insets(1, 1, 1, 1);
//
//        gbc.weightx = 1.0;
//        gbc.weighty = 1.0;
//        gbc.fill = GridBagConstraints.HORIZONTAL;
//        addCompItem(panel, topoValue, gbc, 0, 0, 1, 1);
//
//        return panel;
//    }
    boolean mySlide=false;
    int lockDiff=0;
    JSlider minTopoSlider;
    private JPanel createTopoMinRangeSelectionPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;
        
        minTopoSlider = new JSlider(JSlider.HORIZONTAL,0,100,0);
        minTopoField.setEditable(false);

     
        	minTopoSlider.setValue(settings.getMinTopoRange());
        ChangeListener topoSelector = new ChangeListener() {
			public void stateChanged(ChangeEvent e) {
				if(mySlide)
					return;
				 try {					 
					 if(lockBox.isSelected()){

						 mySlide=true;
						 maxTopoSlider.setValue(minTopoSlider.getValue()+lockDiff);
						 settings.setMaxTopoRange(maxTopoSlider.getValue());
						 mySlide=false;
					 }
	                    settings.setMinTopoRange(minTopoSlider.getValue());
					 
	                    window.redraw();
	                    minTopoField.setText(window.getSelectedMinTopoValue());
	                    maxTopoField.setText(window.getSelectedMaxTopoValue());
	                } catch (Exception evt) {
	                    ParaProfUtils.handleException(evt);
	                }
			}
        };
        
        minTopoSlider.addChangeListener(topoSelector);

        gbc.insets = new Insets(1, 1, 1, 1);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(panel, minTopoSlider, gbc, 0, 0, 1, 1);
        addCompItem(panel,minTopoField,gbc,0,1,1,1);

        return panel;
    }
    
    JSlider maxTopoSlider;
    private JPanel createTopoMaxRangeSelectionPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;


        
        maxTopoSlider = new JSlider(JSlider.HORIZONTAL,0,100,100);
        maxTopoField.setEditable(false);


        	maxTopoSlider.setValue(settings.getMaxTopoRange());
        ChangeListener topoSelector = new ChangeListener() {
			public void stateChanged(ChangeEvent e) {
				if(mySlide)
					return;
				 try {
					 if(lockBox.isSelected()){

						 mySlide=true;
						 minTopoSlider.setValue(maxTopoSlider.getValue()-lockDiff);
						 settings.setMinTopoRange(minTopoSlider.getValue());
						 mySlide=false;
					 }
						 settings.setMaxTopoRange(maxTopoSlider.getValue());
					 
	                    window.redraw();
	                    minTopoField.setText(window.getSelectedMinTopoValue());
	                    maxTopoField.setText(window.getSelectedMaxTopoValue());
	                    
	                } catch (Exception evt) {
	                    ParaProfUtils.handleException(evt);
	                }
				
			}
        };
        
        maxTopoSlider.addChangeListener(topoSelector);

        gbc.insets = new Insets(1, 1, 1, 1);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(panel, maxTopoSlider, gbc, 0, 0, 1, 1);
        addCompItem(panel,maxTopoField,gbc,0,1,1,1);

        return panel;
    }
    
    JLabel[] customAxisLabels = new JLabel[3];
    JSpinner[] customAxisSpinners = new JSpinner[3]; 
    
    JLabel[] selectAxisLabels = new JLabel[3];
    JSlider[] selectAxisSliders = new JSlider[3];
    private static final String[] topoLabelStrings = {"X Axis", "Y Axis", "Z Axis"};
    boolean firstSet=false;
    private JPanel createTopoAxisSelectionPanel(int dex){
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;
        
        selectAxisSliders[dex] = new JSlider(JSlider.HORIZONTAL,-1,100,-1);

        final int idex = dex;
//        final String labelString;
//        if(dex==0)labelString="X Axis";
//        else if(dex==1)labelString="Y Axis";
//        else if(dex==2)labelString="Z Axis";
//        else labelString="Axis";
        selectAxisSliders[dex].setValue(settings.getTopoVisAxis(dex));
        ChangeListener topoSelector = new ChangeListener() {
			public void stateChanged(ChangeEvent e) {

				 try {
					 if(!firstSet){
						 int val = selectAxisSliders[idex].getValue();
						 settings.setTopoVisAxis(val,idex);
	                    window.redraw();
	                    if(val==-1){
	                    	selectAxisLabels[idex].setText(topoLabelStrings[idex]);
	                    }else selectAxisLabels[idex].setText(topoLabelStrings[idex]+": "+val);
	                    
	                    topoValField.setText(window.getStatMean()+window.getSelectedThread());
	                    if(allAxesOn()){
	                    	topoValLabel.setText(CV);
	                    }else topoValLabel.setText(ACV);
	                    		//"Min: "+window.getStatMin()+" Max: "+window.getStatMax()+" Mean: "+window.getStatMean());
					 
					 }
					 else
						 firstSet=false;
	                    
	                } catch (Exception evt) {
	                    ParaProfUtils.handleException(evt);
	                }
			}
        };
        
        selectAxisSliders[dex].addChangeListener(topoSelector);

        gbc.insets = new Insets(1, 1, 1, 1);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(panel, selectAxisSliders[dex], gbc, 0, 0, 1, 1);
//TODO: Fix these: Proper activation and length
        return panel;
    }
    
    
    private JPanel createTopoCustomSliderPanel(int dex){
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;
        
        customAxisSpinners[dex] = new JSpinner();
        SpinnerModel model = new SpinnerNumberModel(20, //initial value
                                   0, //min
                                   1000, //max
                                   1);                //step
        customAxisSpinners[dex].setModel(model);
        customAxisSpinners[dex].setEnabled(((String)topoComboBox.getSelectedItem()).equals("Custom"));

        final int idex = dex;
        int v = settings.getCustomTopoAxis(dex);
        if(v>0)
        	customAxisSpinners[dex].setValue(settings.getCustomTopoAxis(dex));
        else{
        	settings.setCustomTopoAxis(50, dex);
        }
        ChangeListener topoSelector = new ChangeListener() {
			public void stateChanged(ChangeEvent e) {

				 try {
					 //if(!firstSet){
						 int val = (Integer) customAxisSpinners[idex].getModel().getValue();
						 settings.setCustomTopoAxis(val,idex);
						 resetTopoAxisSliders(true);
	                    window.redraw();
						 resetTopoAxisSliders(true);
//	                    if(val==-1){
//	                    	selectAxisLabels[idex].setText(topoLabelStrings[idex]);
//	                    }else selectAxisLabels[idex].setText(topoLabelStrings[idex]+": "+val);
//	                    
//	                    topoValField.setText(window.getStatMean());
//	                    if(allAxesOn()){
//	                    	topoValLabel.setText(CV);
//	                    }else topoValLabel.setText(ACV);
	                    		//"Min: "+window.getStatMin()+" Max: "+window.getStatMax()+" Mean: "+window.getStatMean());
					 
//					 }
//					 else
//						 firstSet=false;
	                    
	                } catch (Exception evt) {
	                    ParaProfUtils.handleException(evt);
	                }
			}
        };
        
        customAxisSpinners[dex].addChangeListener(topoSelector);

        gbc.insets = new Insets(1, 1, 1, 1);

        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        addCompItem(panel, customAxisSpinners[dex], gbc, 0, 0, 1, 1);

        return panel;
    }
    
    private JPanel createCallGraphPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        panel.setBorder(BorderFactory.createRaisedBevelBorder());

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

        addCompItem(panel, new JLabel("Thread"), gbc, 0, 0, 1, 1);

        List<Thread> threadList = new ArrayList<Thread>();

        threadList.add(ppTrial.getDataSource().getMeanData());
        threadList.add(ppTrial.getDataSource().getStdDevData());

        threadList.addAll(ppTrial.getDataSource().getAllThreads());

        final SliderComboBox threadComboBox = new SliderComboBox(threadList.toArray());

        threadComboBox.addActionListener(new ActionListener() {

            public void actionPerformed(ActionEvent e) {
                settings.setSelectedThread((Thread) threadComboBox.getSelectedItem());
                System.out.println("bargle");
                window.redraw();
            }
        });

        addCompItem(panel, threadComboBox, gbc, 1, 0, 1, 1);

        tabbedPane = new JTabbedPane();
        Plot plot = window.getPlot();
        tabbedPane.addTab(plot.getName(), plot.getControlPanel(visRenderer));
        tabbedPane.addTab("ColorScale", window.getColorScale().getControlPanel(visRenderer));
        tabbedPane.addTab("Render", visRenderer.getControlPanel());
        tabbedPane.setMinimumSize(new Dimension(300, 250));
        tabbedPane.setSelectedIndex(0);

        gbc.fill = GridBagConstraints.BOTH;
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;

        addCompItem(panel, tabbedPane, gbc, 0, 1, 2, 1);
        return panel;

    }

    private JPanel createScatterPanel() {

        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        panel.setBorder(BorderFactory.createRaisedBevelBorder());

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

        gbc.fill = GridBagConstraints.NONE;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;

        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;

        gbc.weightx = 0;
        addCompItem(panel, new JLabel("Width"), gbc, 0, 0, 1, 1);
        addCompItem(panel, createScatterSelectionPanel("Width", 0), gbc, 1, 0, 1, 1);
        gbc.weightx = 0;
        addCompItem(panel, new JLabel("Depth"), gbc, 0, 1, 1, 1);
        addCompItem(panel, createScatterSelectionPanel("Depth", 1), gbc, 1, 1, 1, 1);
        gbc.weightx = 0;
        addCompItem(panel, new JLabel("Height"), gbc, 0, 2, 1, 1);
        addCompItem(panel, createScatterSelectionPanel("Height", 2), gbc, 1, 2, 1, 1);
        gbc.weightx = 0;
        addCompItem(panel, new JLabel("Color"), gbc, 0, 3, 1, 1);
        addCompItem(panel, createScatterSelectionPanel("Color", 3), gbc, 1, 3, 1, 1);

        tabbedPane = new JTabbedPane();

        Plot plot = window.getPlot();
        tabbedPane.addTab(plot.getName(), plot.getControlPanel(visRenderer));
        tabbedPane.addTab("Axes", plot.getAxes().getControlPanel(visRenderer));
        tabbedPane.addTab("ColorScale", window.getColorScale().getControlPanel(visRenderer));
        tabbedPane.addTab("Render", visRenderer.getControlPanel());
        tabbedPane.setMinimumSize(new Dimension(300, 250));
        selectedTab = Math.min(selectedTab, tabbedPane.getTabCount()-1);
        tabbedPane.setSelectedIndex(selectedTab);

        gbc.fill = GridBagConstraints.BOTH;
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;

        addCompItem(panel, tabbedPane, gbc, 0, 4, 2, 1);

        return panel;

    }
    
    JCheckBox lockBox;// = new JCheckBox();
    JTextArea topoValField;
    JLabel topoValLabel;
    
    private JPanel createTopoSettingsPanel(){
    	JPanel panel = new JPanel();
    	panel.setLayout(new GridBagLayout());
        panel.setBorder(BorderFactory.createRaisedBevelBorder());
    	
    	 GridBagConstraints gbc = new GridBagConstraints();
         gbc.insets = new Insets(5, 5, 5, 5);

//         gbc.fill = GridBagConstraints.NONE;
//         gbc.anchor = GridBagConstraints.WEST;
//         gbc.weightx = 0.1;
//         gbc.weighty = 0.1;

         gbc.fill = GridBagConstraints.HORIZONTAL;
         gbc.anchor = GridBagConstraints.WEST;
         gbc.weightx = 0.1;
         gbc.weighty = 0.1;

         //gbc.weightx = 0;
//         addCompItem(panel, new JLabel("Width/X"), gbc, 0, 0, 1, 1);
//         addCompItem(panel, createTopoDimSelectionPanel("Width", 0), gbc, 1, 0, 1, 1);
         gbc.weightx = 0;
         addCompItem(panel, new JLabel("Minimum Visible"), gbc, 0, 0, 1, 1);
         gbc.weightx = 0.1;
         addCompItem(panel, createTopoMinRangeSelectionPanel(), gbc, 1, 0, 1, 1);
         gbc.weightx = 0;
         addCompItem(panel, new JLabel("Maximum Visible"), gbc, 0, 1, 1, 1);
         gbc.weightx = 0.1;
         addCompItem(panel, createTopoMaxRangeSelectionPanel(), gbc, 1, 1, 1, 1);
         addCompItem(panel, lockBox=new JCheckBox("Lock Range"),gbc,0,2,1,1);
         
         
         ChangeListener lockSelector = new ChangeListener() {
 			public void stateChanged(ChangeEvent e) {
 				if(lockBox.isSelected()){
 					lockDiff=maxTopoSlider.getValue()-minTopoSlider.getValue();
 				}
 				else{
 					lockDiff=0;
 				}
 			}
         };
         
         lockBox.addChangeListener(lockSelector);
         
         gbc.weightx = 0;
         addCompItem(panel, selectAxisLabels [0]=new JLabel("X Axis"), gbc, 0, 3, 1, 1);
         gbc.weightx = 0.1;
         addCompItem(panel, createTopoAxisSelectionPanel(0), gbc, 1, 3, 1, 1);
         gbc.weightx = 0;
         addCompItem(panel, selectAxisLabels [1]=new JLabel("Y Axis"), gbc, 0, 4, 1, 1);
         gbc.weightx = 0.1;
         addCompItem(panel, createTopoAxisSelectionPanel(1), gbc, 1, 4, 1, 1);
         gbc.weightx = 0;
         addCompItem(panel, selectAxisLabels [2]=new JLabel("Z Axis"), gbc, 0, 5, 1, 1);
         gbc.weightx = 0.1;
         addCompItem(panel, createTopoAxisSelectionPanel(2), gbc, 1, 5, 1, 1);
         gbc.weightx = 0;
         addCompItem(panel,topoValLabel=new JLabel("Average Color Value: "),gbc,0,6,1,2);
         gbc.weightx = 0.1;
         
         
         
         addCompItem(panel,topoValField=new JTextArea(),gbc,1,6,1,2);
         topoValField.setRows(2);
         topoValField.setEditable(false);
         topoValField.setText(window.getStatMean()+window.getSelectedThread());
         if(allAxesOn()){
         	topoValLabel.setText(CV);
         }else topoValLabel.setText(ACV);
         //topoValField.setText("Min: "+window.getStatMin()+" Max: "+window.getStatMax()+" Mean: "+window.getStatMean());
         
         gbc.weightx = 0.1;
         //addCompItem(panel, new JLabel("Topology"), gbc, 0, 8, 1, 1);
         addCompItem(panel, createTopoSelectionPanel("Topology"), gbc, 0, 8, 2, 1);
         if(topoComboBox.getItemCount()>this.selectedTopoDex)
        	 this.topoComboBox.setSelectedIndex(this.selectedTopoDex);
         else
        	 this.topoComboBox.setSelectedIndex(0);
    	
         return panel;
    	
    }
    
    private JPanel[] topoSelectPanels=new JPanel[4];
    
    private JPanel createTopoSelectPanel(){
    	JPanel panel = new JPanel();
    	panel.setLayout(new GridBagLayout());
        panel.setBorder(BorderFactory.createRaisedBevelBorder());
    	GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

//        gbc.fill = GridBagConstraints.NONE;
//        gbc.anchor = GridBagConstraints.WEST;
//        gbc.weightx = 0.1;
//        gbc.weighty = 0.1;

        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;
    	
        
        //gbc.weightx = 0;
        //addCompItem(panel, new JLabel("event0"), gbc, 0, 0, 1, 1);
        gbc.weightx = 0.1;
        topoSelectPanels[0]=createTopoIntervalSelectionPanel("event0", 0);
        addCompItem(panel, topoSelectPanels[0], gbc, 0, 0, 2, 1);
        
//        gbc.weightx = 0;
//        addCompItem(panel, new JLabel("event1"), gbc, 0, 1, 1, 1);
        gbc.weightx = 0.1;
        topoSelectPanels[1]=createTopoIntervalSelectionPanel("event1", 1);
        addCompItem(panel, topoSelectPanels[1], gbc, 0, 1, 2, 1);
        
//        gbc.weightx = 0;
//        addCompItem(panel, new JLabel("event2"), gbc, 0, 2, 1, 1);
        gbc.weightx = 0.1;
        topoSelectPanels[2]=createTopoIntervalSelectionPanel("event2", 2);
        addCompItem(panel, topoSelectPanels[2], gbc, 0, 2, 2, 1);
        
//    	 gbc.weightx = 0;
//         addCompItem(panel, new JLabel("event3 (Color)"), gbc, 0, 3, 1, 1);
         gbc.weightx = 0.1;
         topoSelectPanels[3]=createTopoIntervalSelectionPanel("event3 (Color)", 3);
         addCompItem(panel, topoSelectPanels[3], gbc, 0, 3, 2, 1);
         
//         gbc.weightx = 0;
//         addCompItem(panel, new JLabel("atomic0"), gbc, 0, 4, 1, 1);
//         gbc.weightx = 0.1;
//         addCompItem(panel, createTopoAtomicSelectionPanel("atomic0", 0), gbc, 1, 4, 1, 1);
//         
//         gbc.weightx = 0;
//         addCompItem(panel, new JLabel("atomic1"), gbc, 0, 5, 1, 1);
//         gbc.weightx = 0.1;
//         addCompItem(panel, createTopoAtomicSelectionPanel("atomic1", 1), gbc, 1, 5, 1, 1);
//         
//         gbc.weightx = 0;
//         addCompItem(panel, new JLabel("atomic2"), gbc, 0, 6, 1, 1);
//         gbc.weightx = 0.1;
//         addCompItem(panel, createTopoAtomicSelectionPanel("atomic2", 2), gbc, 1, 6, 1, 1);
//         
//         gbc.weightx = 0;
//         addCompItem(panel, new JLabel("atomic3"), gbc, 0, 7, 1, 1);
//         gbc.weightx = 0.1;
//         addCompItem(panel, createTopoAtomicSelectionPanel("atomic3", 3), gbc, 1, 7, 1, 1);
         
         
         return panel;
         
    }
    private boolean topoCreated=false;
    private JPanel createTopoPanel() {

        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());
        panel.setBorder(BorderFactory.createRaisedBevelBorder());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

//        gbc.fill = GridBagConstraints.NONE;
//        gbc.anchor = GridBagConstraints.WEST;
//        gbc.weightx = 0.1;
//        gbc.weighty = 0.1;

        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.1;
        gbc.weighty = 0.1;
       

        JTabbedPane topTabs = new JTabbedPane();

        topTabs.addTab("Layout", createTopoSettingsPanel());
        topTabs.addTab("Events", createTopoSelectPanel());
        
        tabbedPane = new JTabbedPane();

        Plot plot = window.getPlot();
        tabbedPane.addTab(plot.getName(), plot.getControlPanel(visRenderer));
        tabbedPane.addTab("Axes", plot.getAxes().getControlPanel(visRenderer));
        tabbedPane.addTab("ColorScale", window.getColorScale().getControlPanel(visRenderer));
        tabbedPane.addTab("Render", visRenderer.getControlPanel());
        tabbedPane.setMinimumSize(new Dimension(300, 250));
        selectedTab = Math.min(selectedTab, tabbedPane.getTabCount()-1);
        tabbedPane.setSelectedIndex(selectedTab);

        gbc.fill = GridBagConstraints.BOTH;
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;
        
        addCompItem(panel, topTabs, gbc, 0,0,1,1);

        addCompItem(panel, tabbedPane, gbc, 0, 1, 1, 1);
        
        this.maxTopoField.setText(window.getSelectedMaxTopoValue());
        this.minTopoField.setText(window.getSelectedMinTopoValue());
        
        resetTopoAxisSliders(false);

        switchTopoSelectPanels(checkDisableTopoWidgets((String)topoComboBox.getSelectedItem()));
        topoCreated=true;
        return panel;

    }
    
    private void resetTopoAxisSliders(boolean full){
        if(window.tsizes!=null){
        	for(int i=0;i<3;i++)
        	{
        		firstSet=true;
        		this.selectAxisSliders[i].setMaximum(window.tsizes[i]);
        		if(window.tsizes[i]<1){
        			selectAxisSliders[i].setEnabled(false);
        		}else
        			selectAxisSliders[i].setEnabled(true);
        		
        		if(full){
        			selectAxisSliders[i].setValue(-1);
        			settings.setTopoVisAxis(-1, i);
        			selectAxisLabels[i].setText(topoLabelStrings[i]);
        		}
        	}
        }
    }

    private JPanel createSelectorPanel(int min, int max, final List<String> names, final int index) {

        JPanel panel = new JPanel();
        panel.setLayout(new GridBagLayout());

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

        settings.getSelections()[index] = Math.min(settings.getSelections()[index], max);
        settings.getSelections()[index] = Math.max(settings.getSelections()[index], min);

        final JScrollBar scrollBar = new JScrollBar(JScrollBar.HORIZONTAL, settings.getSelections()[index], 1, min, max);
        scrollBar.setBlockIncrement((max - min) / 10);

        final JTextField textField = new JTextField("<none>");

        textField.setHorizontalAlignment(JTextField.CENTER);

        if (settings.getSelections()[index] >= 0) {
            if (names != null) {
                textField.setText(names.get(settings.getSelections()[index]));
            }
        }

        textField.setEditable(false);
        textField.setCaretPosition(0);

        scrollBar.addAdjustmentListener(new AdjustmentListener() {
            public void adjustmentValueChanged(AdjustmentEvent e) {
                int selection = scrollBar.getValue();
                settings.setSelection(index, selection);
                if (selection >= 0 && names != null) {
                    textField.setText(names.get(selection));
                } else {
                    textField.setText("<none>");
                }
                textField.setCaretPosition(0);

                heightValueField.setText(window.getSelectedHeightValue());
                colorValueField.setText(window.getSelectedColorValue());

                scalePanel.setPosition(0, window.getSelectedHeightRatio());
                scalePanel.setPosition(1, window.getSelectedColorRatio());

                window.redraw();
            }
        });

        gbc.fill = GridBagConstraints.BOTH;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;

        Utility.addCompItem(panel, textField, gbc, 1, 0, 1, 1);
        Utility.addCompItem(panel, scrollBar, gbc, 1, 1, 1, 1);

        return panel;
    }

    private String getScaleString(double value, Metric metric, ValueType valueType) {
        int units = window.getUnits();

        if (!metric.isTimeMetric() || !ValueType.isTimeUnits(valueType)) {
            units = 0;
        }
        return UtilFncs.getOutputString(units, value, 6, metric.isTimeDenominator()).trim();
    }

    private void updateScalePanel() {
        String mins[] = new String[2];
        String maxs[] = new String[2];

        mins[0] = "0";
        mins[1] = "0";
        maxs[0] = getScaleString(window.getMaxHeightValue(), settings.getHeightMetric(), settings.getHeightValue());
        maxs[1] = getScaleString(window.getMaxColorValue(), settings.getColorMetric(), settings.getColorValue());

        String labels[] = { "height", "color" };
        String unitLabels[] = { window.getHeightUnitLabel(), window.getColorUnitLabel() };
        scalePanel.setRanges(mins, maxs, labels, unitLabels);

        scalePanel.setPosition(0, window.getSelectedHeightRatio());
        scalePanel.setPosition(1, window.getSelectedColorRatio());

    }

    private JPanel createScalePanel() {
        if (scalePanel == null) {
            scalePanel = ThreeDeeScalePanel.CreateScalePanel();
            updateScalePanel();
        }
        return scalePanel.getJPanel();
    }

    private JPanel createFullDataPanel() {

        JPanel regularPanel = new JPanel();
        regularPanel.setLayout(new GridBagLayout());
        regularPanel.setBorder(BorderFactory.createLoweredBevelBorder());

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

        ActionListener metricChanger = new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                try {

                    Plot plot = window.getPlot();

                    settings.setHeightMetric((Metric) heightMetricBox.getSelectedItem());
                    settings.setColorMetric((Metric) colorMetricBox.getSelectedItem());
                    settings.setHeightValue((ValueType) heightValueBox.getSelectedItem());
                    settings.setColorValue((ValueType) colorValueBox.getSelectedItem());

                    settings.setSize((int) plot.getWidth(), (int) plot.getDepth(), (int) plot.getHeight());
                    settings.setRegularAim(visRenderer.getAim());
                    settings.setRegularEye(visRenderer.getEye());

                    heightValueField.setText(window.getSelectedHeightValue());
                    colorValueField.setText(window.getSelectedColorValue());

                    window.redraw();

                    updateScalePanel();

                } catch (Exception e) {
                    ParaProfUtils.handleException(e);
                }
            }

        };

        Dimension d;

        heightValueBox = new SteppedComboBox(ValueType.VALUES);
        d = heightValueBox.getPreferredSize();
        heightValueBox.setMinimumSize(new Dimension(50, heightValueBox.getMinimumSize().height));
        heightValueBox.setPopupWidth(d.width);
        heightValueBox.setSelectedItem(settings.getHeightValue());
        heightValueBox.addActionListener(metricChanger);

        colorValueBox = new SteppedComboBox(ValueType.VALUES);
        d = colorValueBox.getPreferredSize();
        colorValueBox.setMinimumSize(new Dimension(50, colorValueBox.getMinimumSize().height));
        colorValueBox.setPopupWidth(d.width);
        colorValueBox.setSelectedItem(settings.getColorValue());
        colorValueBox.addActionListener(metricChanger);

        heightMetricBox = new SteppedComboBox(ppTrial.getMetricArray());
        d = heightMetricBox.getPreferredSize();
        heightMetricBox.setMinimumSize(new Dimension(50, heightMetricBox.getMinimumSize().height));
        heightMetricBox.setPopupWidth(d.width);
        heightMetricBox.setSelectedItem(settings.getHeightMetric());
        heightMetricBox.addActionListener(metricChanger);

        colorMetricBox = new SteppedComboBox(ppTrial.getMetricArray());
        d = colorMetricBox.getPreferredSize();
        colorMetricBox.setMinimumSize(new Dimension(50, colorMetricBox.getMinimumSize().height));
        colorMetricBox.setPopupWidth(d.width);
        colorMetricBox.setSelectedItem(settings.getColorMetric());
        colorMetricBox.addActionListener(metricChanger);

        tabbedPane = new JTabbedPane();
        Plot plot = window.getPlot();
        tabbedPane.setTabLayoutPolicy(JTabbedPane.SCROLL_TAB_LAYOUT);
        tabbedPane.addTab("Scales", createScalePanel());
        //        tabbedPane.addTab(plot.getName(), plot.getControlPanel(visRenderer));
        tabbedPane.addTab("Plot", plot.getControlPanel(visRenderer));
        tabbedPane.addTab("Axes", plot.getAxes().getControlPanel(visRenderer));
        tabbedPane.addTab("Color", window.getColorScale().getControlPanel(visRenderer));
        tabbedPane.addTab("Render", visRenderer.getControlPanel());
        tabbedPane.setMinimumSize(new Dimension(300, 200));
        tabbedPane.setSelectedIndex(selectedTab);

        JPanel functionSelectorPanel = createSelectorPanel(-1, window.getFunctionNames().size(), window.getFunctionNames(), 0);
        JPanel nodeSelectorPanel = createSelectorPanel(0, ppTrial.getDataSource().getNumThreads(), window.getThreadNames(), 1);

        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.weightx = 0.0;
        gbc.weighty = 0.0;

        addCompItem(regularPanel, new JLabel("Height Metric"), gbc, 0, 0, 2, 1);
        addCompItem(regularPanel, new JLabel("Color Metric"), gbc, 0, 2, 2, 1);
        gbc.weightx = 0.5;
        addCompItem(regularPanel, heightValueBox, gbc, 0, 1, 1, 1);
        addCompItem(regularPanel, heightMetricBox, gbc, 1, 1, 1, 1);
        addCompItem(regularPanel, colorValueBox, gbc, 0, 3, 1, 1);
        addCompItem(regularPanel, colorMetricBox, gbc, 1, 3, 1, 1);

        JPanel selectionPanel = new JPanel();
        selectionPanel.setLayout(new GridBagLayout());
        //        selectionPanel.setBorder(BorderFactory.createLoweredBevelBorder());

        heightValueField.setEditable(false);
        colorValueField.setEditable(false);

        gbc.fill = GridBagConstraints.NONE;
        gbc.weightx = 0.0;
        addCompItem(selectionPanel, new JLabel("Function"), gbc, 0, 0, 1, 1);
        addCompItem(selectionPanel, new JLabel("Thread"), gbc, 0, 1, 1, 1);
        addCompItem(selectionPanel, new JLabel("Height value"), gbc, 0, 2, 1, 1);
        addCompItem(selectionPanel, new JLabel("Color value"), gbc, 0, 3, 1, 1);

        gbc.fill = GridBagConstraints.BOTH;
        gbc.weightx = 1.0;
        addCompItem(selectionPanel, functionSelectorPanel, gbc, 1, 0, 1, 1);
        addCompItem(selectionPanel, nodeSelectorPanel, gbc, 1, 1, 1, 1);
        addCompItem(selectionPanel, heightValueField, gbc, 1, 2, 1, 1);
        
//        GridBagConstraints gbcCF=(GridBagConstraints) gbc.clone();
//        
//        gbcCF.fill = GridBagConstraints.NONE;
//        gbcCF.weightx = 0.0;
        addCompItem(selectionPanel, colorValueField, gbc, 1, 3, 1, 1);
        //gbc.fill = GridBagConstraints.BOTH;
        //gbc.weightx = 1.0;

        addCompItem(regularPanel, selectionPanel, gbc, 0, 4, 2, 1);

        gbc.fill = GridBagConstraints.BOTH;
        gbc.anchor = GridBagConstraints.SOUTH;
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;

        addCompItem(regularPanel, tabbedPane, gbc, 0, 5, 2, 1);

        return regularPanel;
    }

    public void actionPerformed(ActionEvent evt) {
        try {
            Object EventSrc = evt.getSource();

            if (EventSrc instanceof JRadioButton) {

                selectedTab = tabbedPane.getSelectedIndex();
                selectedTab = 0; // they don't match anymore, so always reset to 0

                String arg = evt.getActionCommand();
                Plot plot = window.getPlot();

                if (settings.getVisType() == VisType.BAR_PLOT || settings.getVisType() == VisType.TRIANGLE_MESH_PLOT) {
                    settings.setSize((int) plot.getWidth(), (int) plot.getDepth(), (int) plot.getHeight());
                    settings.setRegularAim(visRenderer.getAim());
                    settings.setRegularEye(visRenderer.getEye());
                } else if (settings.getVisType() == VisType.SCATTER_PLOT || settings.getVisType() == VisType.TOPO_PLOT) {
                    //                    settings.setSize((int) plot.getWidth(), (int) plot.getDepth(), (int) plot.getHeight());
                    settings.setScatterAim(visRenderer.getAim());
                    settings.setScatterEye(visRenderer.getEye());
                }

                if (arg.equals(VisType.BAR_PLOT.toString())) {
                    settings.setVisType(VisType.BAR_PLOT);
                } else if (arg.equals(VisType.TRIANGLE_MESH_PLOT.toString())) {
                    settings.setVisType(VisType.TRIANGLE_MESH_PLOT);
                } else if (arg.equals(VisType.SCATTER_PLOT.toString())) {
                    settings.setVisType(VisType.SCATTER_PLOT);
                } else if (arg.equals(VisType.CALLGRAPH.toString())) {
                    settings.setVisType(VisType.CALLGRAPH);
                }else if (arg.equals(VisType.TOPO_PLOT.toString())) {
                    settings.setVisType(VisType.TOPO_PLOT);}

                window.resetSplitPane();
                createSubPanel();
            }
        } catch (Exception e) {
            ParaProfUtils.handleException(e);
        }
    }

    public void dataChanged() {
        window.redraw();
        updateScalePanel();
        createSubPanel();
        heightValueField.setText(window.getSelectedHeightValue());
        colorValueField.setText(window.getSelectedColorValue());
        
        if(topoCreated){
        minTopoField.setText(window.getSelectedMinTopoValue());
        maxTopoField.setText(window.getSelectedMaxTopoValue());
        topoValField.setText(window.getStatMean()+window.getSelectedThread());
        if(allAxesOn()){
        	topoValLabel.setText(CV);
        }else topoValLabel.setText(ACV);
        }
    }
    private static final String CV = "Color Value: ";
    private static final String ACV ="Avg Color Value: ";
    private boolean allAxesOn(){
    	int numdis=0;
    	int numSet=0;
    	for(int i=0;i<selectAxisSliders.length;i++){
    		if(!selectAxisSliders[i].isEnabled())
    			numdis++;//continue;
    		if(selectAxisSliders[i].getValue()>-1)
    			numSet++;//return false;
    	}

    	if(numdis==selectAxisSliders.length)return true;
    	if(numSet==0)return false;
    	if(selectAxisSliders.length-numdis==numSet)
    		return true;
    	return false;
    }

    private void addCompItem(JPanel jPanel, Component c, GridBagConstraints gbc, int x, int y, int w, int h) {
        gbc.gridx = x;
        gbc.gridy = y;
        gbc.gridwidth = w;
        gbc.gridheight = h;
        jPanel.add(c, gbc);
    }

}
