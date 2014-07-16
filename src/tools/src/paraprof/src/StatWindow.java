/*
 * StatWindow.java
 * 
 * Title: ParaProf 
 * Author: Robert Bell 
 * Description:
 */

package edu.uoregon.tau.paraprof;

import java.awt.Component;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Rectangle;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.util.ArrayList;
import java.util.List;
import java.util.Observable;
import java.util.Observer;

import javax.swing.ButtonGroup;
import javax.swing.JCheckBoxMenuItem;
import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JRadioButtonMenuItem;
import javax.swing.JScrollBar;
import javax.swing.JScrollPane;
import javax.swing.JSeparator;
import javax.swing.JTextArea;
import javax.swing.event.MenuEvent;
import javax.swing.event.MenuListener;

import edu.uoregon.tau.paraprof.enums.SortType;
import edu.uoregon.tau.paraprof.enums.UserEventValueType;
import edu.uoregon.tau.paraprof.enums.ValueType;
import edu.uoregon.tau.paraprof.interfaces.ParaProfWindow;
import edu.uoregon.tau.paraprof.interfaces.ScrollBarController;
import edu.uoregon.tau.paraprof.interfaces.SearchableOwner;
import edu.uoregon.tau.paraprof.interfaces.UnitListener;
import edu.uoregon.tau.perfdmf.Function;
import edu.uoregon.tau.perfdmf.Thread;
import edu.uoregon.tau.perfdmf.UtilFncs;

public class StatWindow extends JFrame implements ActionListener, MenuListener, Observer, SearchableOwner, ScrollBarController,
        KeyListener, ParaProfWindow, UnitListener {

    /**
	 * 
	 */
	private static final long serialVersionUID = 1176775089369369534L;
	//Instance data.
    private ParaProfTrial ppTrial = null;
    private DataSorter dataSorter;
    private Function phase;

    private int nodeID = -1;
    private int contextID = -1;
    private int threadID = -1;
    private boolean userEventWindow;

    private JMenu optionsMenu = null;
    private JMenu unitsSubMenu = null;
    private boolean sortByName;

    private JCheckBoxMenuItem descendingOrder = null;
    //private JCheckBoxMenuItem showPathTitleInReverse = null;
    private JCheckBoxMenuItem showMetaData = null;
	private JCheckBoxMenuItem showTotal = null;
    private JCheckBoxMenuItem showFindPanelBox;

    private JScrollPane jScrollpane = null;
    private StatWindowPanel panel = null;

    private List<PPUserEventProfile> uepList = new ArrayList<PPUserEventProfile>();
    private List<PPFunctionProfile>  fpList = new ArrayList<PPFunctionProfile>();

    private int units = ParaProf.preferences.getUnits();

    private SearchPanel searchPanel;

    private Thread thread;

    public StatWindow(ParaProfTrial ppTrial, Thread thread, boolean userEventWindow, Function phase, Component invoker) {
        this.ppTrial = ppTrial;
        this.phase = phase;
        ppTrial.addObserver(this);

        this.dataSorter = new DataSorter(ppTrial);
        dataSorter.setPhase(phase);
        this.userEventWindow = userEventWindow;
        this.thread = thread;

        setSize(ParaProfUtils.checkSize(new Dimension(1000, 600)));

        setLocation(WindowPlacer.getNewLocation(this, invoker));

        nodeID = thread.getNodeID();
        contextID = thread.getContextID();
        threadID = thread.getThreadID();

        String title;
        //Now set the title.
        if (nodeID == -1 || nodeID == -6) {
            title = "TAU: ParaProf: Mean Data Statistics: ";
        } else if (nodeID == -2) {
            title = "TAU: ParaProf: Total Statistics: ";
        } else if (nodeID == -3 || nodeID == -7) {
            title = "TAU: ParaProf: Standard Deviation Statistics: ";
        } else {
            title = "TAU: ParaProf: "+ ParaProfUtils.getThreadLabel(thread);//n,c,t, " + nodeID + "," + contextID + "," + threadID;
        }

        title = title + " - " + ppTrial.getTrialIdentifier(ParaProf.preferences.getShowPathTitleInReverse());

        if (phase != null) {
            this.setTitle(title + " Phase: " + phase.getName());
        } else {
            this.setTitle(title);
        }
        ParaProfUtils.setFrameIcon(this);

        addKeyListener(this);

        //Add some window listener code
        addWindowListener(new java.awt.event.WindowAdapter() {
            public void windowClosing(java.awt.event.WindowEvent evt) {
                thisWindowClosing(evt);
            }
        });

        //Set the help window text if required.
        if (ParaProf.getHelpWindow().isVisible()) {
            this.help(false);
        }

        //####################################
        //Code to generate the menus.
        //####################################
        JMenuBar mainMenu = new JMenuBar();

        mainMenu.addKeyListener(this);
        JMenu subMenu = null;
        //JMenuItem menuItem = null;

        //######
        //Options menu.
        //######
        optionsMenu = new JMenu("Options");

        //JCheckBoxMenuItem box = null;
        ButtonGroup group = null;
        JRadioButtonMenuItem button = null;

        showFindPanelBox = new JCheckBoxMenuItem("Show Find Panel", false);
        showFindPanelBox.addActionListener(this);
        optionsMenu.add(showFindPanelBox);

        showMetaData = new JCheckBoxMenuItem("Show Meta Data in Panel", true);
        showMetaData.addActionListener(this);
        optionsMenu.add(showMetaData);

		// if (userEventWindow) {
		// showTotal = new JCheckBoxMenuItem("Show Total", true);
		// showTotal.addActionListener(this);
		// optionsMenu.add(showTotal);
		// }

        optionsMenu.add(new JSeparator());

        descendingOrder = new JCheckBoxMenuItem("Descending Order", true);
        descendingOrder.addActionListener(this);
        optionsMenu.add(descendingOrder);

        //Units submenu.

        if (!userEventWindow) {
            unitsSubMenu = ParaProfUtils.createUnitsMenu(this, units, true);
        } else {
            unitsSubMenu = new JMenu("Select Units");
        }
        optionsMenu.add(unitsSubMenu);

        //Set the value type options.
        subMenu = new JMenu("Sort By");
        group = new ButtonGroup();

        if (userEventWindow) {
            button = new JRadioButtonMenuItem("Name", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Total", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);
            
            button = new JRadioButtonMenuItem("Number of Samples", true);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Min. Value", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Max. Value", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Mean Value", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Standard Deviation", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

        } else {
            button = new JRadioButtonMenuItem("Name", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Exclusive", true);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Inclusive", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Number of Calls", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Number of Child Calls", false);
            button.addActionListener(this);
            group.add(button);
            subMenu.add(button);

            button = new JRadioButtonMenuItem("Inclusive Per Call", false);
            button.addActionListener(this);
            group.add(button);
        }
        subMenu.add(button);
        optionsMenu.add(subMenu);
        //End - Set the value type options.

        optionsMenu.addMenuListener(this);
        //######
        //End - Options menu.
        //######

        //####################################
        //End - Code to generate the menus.
        //####################################

        //####################################
        //Create and add the components.
        //####################################
        //Setting up the layout system for the main window.
        Container contentPane = getContentPane();
        GridBagLayout gbl = new GridBagLayout();
        contentPane.setLayout(gbl);
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);

        //######
        //Panel and ScrollPane definition.
        //######
        panel = new StatWindowPanel(ppTrial, this, userEventWindow);
        jScrollpane = new JScrollPane(panel);

        JScrollBar jScrollBar = jScrollpane.getVerticalScrollBar();
        jScrollBar.setUnitIncrement(35);

        this.setHeader();
        //######
        //End - Panel and ScrollPane definition.
        //######

        //Sort the local data.
        sortLocalData();

        //Now add the components to the main screen.
        gbc.fill = GridBagConstraints.BOTH;
        gbc.anchor = GridBagConstraints.CENTER;
        gbc.weightx = 1;
        gbc.weighty = 1;
        addCompItem(jScrollpane, gbc, 0, 0, 1, 1);
        //####################################
        //End - Create and add the components.
        //####################################

        //Now, add all the menus to the main menu.
        mainMenu.add(ParaProfUtils.createFileMenu(this, panel, panel));
        mainMenu.add(optionsMenu);
        //mainMenu.add(ParaProfUtils.createTrialMenu(ppTrial, this));
        mainMenu.add(ParaProfUtils.createWindowsMenu(ppTrial, this));
        mainMenu.add(ParaProfUtils.createHelpMenu(this, this));

        setJMenuBar(mainMenu);

        ParaProf.incrementNumWindows();
    }

    public void actionPerformed(ActionEvent evt) {
        try {
            Object EventSrc = evt.getSource();

            if (EventSrc instanceof JMenuItem) {
                String arg = evt.getActionCommand();
                if (arg.equals("Name")) {
                    sortByName = true;
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Show Find Panel")) {
                    if (showFindPanelBox.isSelected())
                        showSearchPanel(true);
                    else
                        showSearchPanel(false);
                } else if (arg.equals("Descending Order")) {
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Exclusive")) {
                    sortByName = false;
                    dataSorter.setValueType(ValueType.EXCLUSIVE);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Inclusive")) {
                    sortByName = false;
                    dataSorter.setValueType(ValueType.INCLUSIVE);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Number of Calls")) {
                    sortByName = false;
                    dataSorter.setValueType(ValueType.NUMCALLS);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Number of Child Calls")) {
                    sortByName = false;
                    dataSorter.setValueType(ValueType.NUMSUBR);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Inclusive Per Call")) {
                    sortByName = false;
                    dataSorter.setValueType(ValueType.INCLUSIVE_PER_CALL);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Exclusive Per Call")) {
                    sortByName = false;
                    dataSorter.setValueType(ValueType.EXCLUSIVE_PER_CALL);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Total")) {
                    sortByName = false;
                    dataSorter.setUserEventValueType(UserEventValueType.TOTAL);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();    
                } else if (arg.equals("Number of Samples")) {
                    sortByName = false;
                    dataSorter.setUserEventValueType(UserEventValueType.NUMSAMPLES);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Min. Value")) {
                    sortByName = false;
                    dataSorter.setUserEventValueType(UserEventValueType.MIN);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Max. Value")) {
                    sortByName = false;
                    dataSorter.setUserEventValueType(UserEventValueType.MAX);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Mean Value")) {
                    sortByName = false;
                    dataSorter.setUserEventValueType(UserEventValueType.MEAN);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Standard Deviation")) {
                    sortByName = false;
                    dataSorter.setUserEventValueType(UserEventValueType.STDDEV);
                    this.setHeader();
                    sortLocalData();
                    panel.repaint();
                } else if (arg.equals("Show Meta Data in Panel")) {
                    this.setHeader();
				} else if (arg.equals("Show Total")) {
					panel.setShowTotal(showTotal.isSelected());
					panel.repaint();
                }
            }
        } catch (Exception e) {
            ParaProfUtils.handleException(e);
        }
    }

    public void menuSelected(MenuEvent evt) {
        try {
            if (ppTrial.isTimeMetric() && !userEventWindow)
                unitsSubMenu.setEnabled(true);
            else
                unitsSubMenu.setEnabled(false);

        } catch (Exception e) {
            ParaProfUtils.handleException(e);
        }
    }

    public void menuDeselected(MenuEvent evt) {}

    public void menuCanceled(MenuEvent evt) {}

    public void update(Observable o, Object arg) {
        String tmpString = (String) arg;
        if (tmpString.equals("prefEvent")) {
        	if(nodeID>=0){
        		String phaseName="";
        		 if (phase != null) {
        	            phaseName= " Phase: " + phase.getName();
        	        }
        	this.setTitle("TAU: ParaProf: Context Events for: " + ParaProfUtils.getThreadLabel(thread)+ " - "
                    + ppTrial.getTrialIdentifier(ParaProf.preferences.getShowPathTitleInReverse())+phaseName);
        	}
        	
            this.setHeader();
            panel.repaint();
        }
        if (tmpString.equals("colorEvent")) {
            //Just need to call a repaint on the ThreadDataWindowPanel.
            panel.repaint();
        } else if (tmpString.equals("dataEvent")) {
            if (!(ppTrial.isTimeMetric())) {
                units = 0;
            }
            dataSorter.setSelectedMetric(ppTrial.getDefaultMetric());
            sortLocalData();
            this.setHeader();
            panel.repaint();
        } else if (tmpString.equals("subWindowCloseEvent")) {
            closeThisWindow();
        }
    }

    public void help(boolean display) {
        //Show the ParaProf help window.
        ParaProf.getHelpWindow().clearText();
        if (display) {
            ParaProf.getHelpWindow().setVisible(true);
        }
        ParaProf.getHelpWindow().writeText("This is the statistics window");
        ParaProf.getHelpWindow().writeText("");
        ParaProf.getHelpWindow().writeText("This window shows you textual statistics.");
        ParaProf.getHelpWindow().writeText("");
        ParaProf.getHelpWindow().writeText("Use the options menu to select different ways of displaying the data.");
        ParaProf.getHelpWindow().writeText("");
        ParaProf.getHelpWindow().writeText("Right click on any line within this window to bring up a popup");
        ParaProf.getHelpWindow().writeText("menu. In this menu you can change or reset the default color");
        ParaProf.getHelpWindow().writeText(", or to show more details about the Function / User Event.");
        ParaProf.getHelpWindow().writeText("You can also left click any line to highlight it in the system.");
    }

    //Helper functionProfiles.
    private void addCompItem(Component c, GridBagConstraints gbc, int x, int y, int w, int h) {
        gbc.gridx = x;
        gbc.gridy = y;
        gbc.gridwidth = w;
        gbc.gridheight = h;
        getContentPane().add(c, gbc);
    }

    public DataSorter getDataSorter() {
        return dataSorter;
    }

    //Updates this window's data copy.
    private void sortLocalData() {
        if (sortByName) {
            dataSorter.setSortType(SortType.NAME);
        } else {
            dataSorter.setSortType(SortType.VALUE);
        }

        dataSorter.setDescendingOrder(descendingOrder.isSelected());

        if (userEventWindow) {
            uepList = dataSorter.getUserEventProfiles(thread);
        } else {
            fpList = dataSorter.getFunctionProfiles(thread);
        }

        panel.resetStringSize();
    }

    public List<PPFunctionProfile> getFunctionProfileData() {
        return fpList;
    }
    
    public List<PPUserEventProfile> getUserEventProfileData() {
        return uepList;
    }

    public int units() {
        if (ppTrial.isTimeMetric())
            return units;
        return 0;
    }

    public Dimension getViewportSize() {
        return jScrollpane.getViewport().getExtentSize();
    }

    public Rectangle getViewRect() {
        return jScrollpane.getViewport().getViewRect();
    }

    //######
    //Panel header.
    //######
    //This process is separated into two functionProfiles to provide the option
    //of obtaining the current header string being used for the panel
    //without resetting the actual header. Printing and image generation
    //use this functionality for example.
    public void setHeader() {
        if (showMetaData.isSelected()) {
            JTextArea jTextArea = new JTextArea();
            jTextArea.setLineWrap(true);
            jTextArea.setWrapStyleWord(true);
            jTextArea.setMargin(new Insets(3, 3, 3, 3));
            jTextArea.setEditable(false);
            jTextArea.addKeyListener(this);
            //PreferencesWindow p = 
            	ppTrial.getPreferencesWindow();
            jTextArea.setFont(ParaProf.preferencesWindow.getFont());
            jTextArea.append(this.getHeaderString());
            jScrollpane.setColumnHeaderView(jTextArea);
        } else
            jScrollpane.setColumnHeaderView(null);
    }

    public String getHeaderString() {
        if (userEventWindow) {
            return "Sorted By: " + dataSorter.getUserEventValueType() + "\n";
        } else {

            if (phase != null) {
                return "Phase: " + phase.getName() + "\nMetric: " + ppTrial.getDefaultMetric().getName() + "\n" + "Sorted By: "
                        + dataSorter.getValueType() + "\n" + "Units: "
                        + UtilFncs.getUnitsString(units, ppTrial.isTimeMetric(), ppTrial.isDerivedMetric()) + "\n";
            } else {
                return "Metric: " + ppTrial.getDefaultMetric().getName() + "\n" + "Sorted By: " + dataSorter.getValueType()
                        + "\n" + "Units: " + UtilFncs.getUnitsString(units, ppTrial.isTimeMetric(), ppTrial.isDerivedMetric())
                        + "\n";
            }
        }
    }

    //Respond correctly when this window is closed.
    void thisWindowClosing(java.awt.event.WindowEvent e) {
        closeThisWindow();
    }

    public void closeThisWindow() {
        try {
            setVisible(false);
            ppTrial.deleteObserver(this);
            ParaProf.decrementNumWindows();
        } catch (Exception e) {
            // do nothing
        }
        dispose();
    }

    public void showSearchPanel(boolean show) {
        if (show) {
            if (searchPanel == null) {
                searchPanel = new SearchPanel(this, panel.getSearcher());
                GridBagConstraints gbc = new GridBagConstraints();
                gbc.insets = new Insets(5, 5, 5, 5);
                gbc.fill = GridBagConstraints.HORIZONTAL;
                gbc.anchor = GridBagConstraints.CENTER;
                gbc.weightx = 0.10;
                gbc.weighty = 0.01;
                addCompItem(searchPanel, gbc, 0, 3, 2, 1);
                searchPanel.setFocus();
            }
        } else {
            getContentPane().remove(searchPanel);
            searchPanel = null;
        }
        showFindPanelBox.setSelected(show);
        validate();
    }

    public void setVerticalScrollBarPosition(int position) {
        JScrollBar scrollBar = jScrollpane.getVerticalScrollBar();
        scrollBar.setValue(position);
    }

    public void setHorizontalScrollBarPosition(int position) {
        JScrollBar scrollBar = jScrollpane.getHorizontalScrollBar();
        scrollBar.setValue(position);
    }

    public Dimension getThisViewportSize() {
        return this.getViewportSize();
    }

    public void keyPressed(KeyEvent e) {
        if (e.isControlDown() && e.getKeyCode() == KeyEvent.VK_F) {
            showSearchPanel(true);
        }
    }

    public void keyReleased(KeyEvent e) {
    // TODO Auto-generated method stub

    }

    public void keyTyped(KeyEvent e) {
    // TODO Auto-generated method stub

    }

    public void setUnits(int units) {
        this.units = units;
        this.setHeader();
        panel.repaint();
    }

    public Function getPhase() {
        return phase;
    }

    public JFrame getFrame() {
        return this;
    }
}