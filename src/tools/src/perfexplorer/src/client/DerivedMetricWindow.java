package edu.uoregon.tau.perfexplorer.client;


import java.awt.Component;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Point;
import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.StringSelection;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.KeyEvent;
import java.awt.event.MouseEvent;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.List;
import java.util.ListIterator;
import java.util.Observable;
import java.util.Observer;
import java.util.Scanner;

import javax.swing.DefaultListModel;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JList;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.JTextPane;
import javax.swing.KeyStroke;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
import javax.swing.plaf.basic.BasicComboBoxRenderer;

import edu.uoregon.tau.perfdmf.Application;
import edu.uoregon.tau.perfdmf.Experiment;
import edu.uoregon.tau.perfdmf.Trial;
import edu.uoregon.tau.perfexplorer.common.ScriptThread;



public class DerivedMetricWindow extends JFrame implements ActionListener, Observer, ListSelectionListener, ItemListener,
ChangeListener {

	private static final long serialVersionUID = 1L;

	private static Application selectApp = new Application();
	private static Experiment selectExp = new Experiment();
	private static Trial selectTrial = new Trial();

	private JButton derive = new JButton("Apply");

	private JPanel input = new JPanel();
	private JPanel selectButtons = new JPanel();
	private JPanel newExpression = new JPanel();
	private JPanel buttons = new JPanel();

	private DefaultListModel expressionList = new DefaultListModel();
	private JButton add = new JButton("Add");
	private JButton edit = new JButton("Edit");
	private JButton remove = new JButton("Remove");
	private JButton selectAll = new JButton("Select All");
	private JButton deselect = new JButton("Deselect All");

	private JFileChooser fc = new JFileChooser(System.getProperty("user.dir"));
	private JMenuBar mb = new JMenuBar();
	private JMenuItem open = new JMenuItem("Load from File");
	private JMenuItem save = new JMenuItem("Save");
	private JMenuItem saveas = new JMenuItem("Save As");
	private JMenuItem copy = new JMenuItem("Save As");
	private JMenuItem paste = new JMenuItem("Save As");
	private JMenuItem cut = new JMenuItem("Save As");

	private JTextField addExpression = new JTextField(25);
	private JButton leftParen = new JButton("(");
	private JButton rightParen = new JButton(")");
	private JButton plus = new JButton("+");
	private JButton minus = new JButton("-");
	private JButton times = new JButton("*");
	private JButton divide = new JButton("/");
	private JButton clear = new JButton("Clear");
	private JButton equals = new JButton("=");
	private JButton insert = new JButton("Insert");

	private JComboBox metrics = new JComboBox();

	JList expression;

	private PerfExplorerClient mainWindow;

	JTextPane textPane;

	public static void main(String args[]){
		PerfExplorerConnection server = PerfExplorerConnection.getConnection();
		ListIterator<Application> array  = server.getApplicationList();

		Application selectApp= array.next();
		ListIterator<Experiment> exps  = server.getExperimentList(selectApp.getID());
		Experiment selectExp = exps.next();
		ListIterator<Trial> trials  = server.getTrialList(selectExp.getID(), false);
		Trial selectTrial = trials.next();


		(new DerivedMetricWindow(PerfExplorerClient.getMainFrame(),selectApp,selectExp,selectTrial)).setVisible(true);
	}

	public DerivedMetricWindow(PerfExplorerClient mainFrame, Application app,Experiment exp, Trial trial) {
		this(mainFrame);
		selectApp = app;
		selectExp = exp;
		selectTrial = trial;
	}


	public DerivedMetricWindow(PerfExplorerClient mw) {
		GridBagConstraints gbc = new GridBagConstraints();
		gbc.insets = new Insets(5, 5, 5, 5);
		gbc.fill = GridBagConstraints.NONE;
		gbc.anchor = GridBagConstraints.NORTHWEST;
		gbc.weightx = 0.5;
		gbc.weighty = 0.5;

		this.getContentPane().setLayout(new GridBagLayout());

		int windowWidth = 650;
		int windowHeight = 563;
		this.setSize(new Dimension(windowWidth, windowHeight));

		// put it in the center of the screen
		//Grab the screen size.
		Toolkit tk = Toolkit.getDefaultToolkit();
		Dimension screenDimension = tk.getScreenSize();
		int screenHeight = screenDimension.height;
		int screenWidth = screenDimension.width;

		Point savedPosition = null; //ParaProf.preferences.getManagerWindowPosition();

		if (savedPosition == null || (savedPosition.x + windowWidth) > screenWidth
				|| (savedPosition.y + windowHeight > screenHeight)) {

			//Find the center position with respect to this window.
			int xPosition = (screenWidth - windowWidth) / 2;
			int yPosition = (screenHeight - windowHeight) / 2;

			//Offset a little so that we do not interfere too much with
			//the main window which comes up in the center of the screen.
			if (xPosition > 50)
				xPosition = xPosition - 50;
			if (yPosition > 50)
				yPosition = yPosition - 50;

			this.setLocation(xPosition, yPosition);
		} 
//		else {
//			this.setLocation(savedPosition);
//		}


		//**********************************************************************	

		this.setTitle("Expression Window");

		mainWindow = mw;     

		//Menu
		JMenu fileMenu = new JMenu("File");
		open = new JMenuItem("Load from File");
		open.addActionListener(this);
		fileMenu.add(open);
		save = new JMenuItem("Save");
		save.addActionListener(this);
		fileMenu.add(save);
		saveas = new JMenuItem("Save Selected");
		saveas.addActionListener(this);
		fileMenu.add(saveas);

		JMenu editMenu = new JMenu("Edit");
		cut = new JMenuItem("Cut");
		cut.setAccelerator(
				KeyStroke.getKeyStroke(KeyEvent.VK_X, ActionEvent.CTRL_MASK));
		cut.setMnemonic(KeyEvent.VK_T);
		cut.addActionListener(this);
		editMenu.add(cut);

		copy = new JMenuItem("Copy");
		copy.addActionListener(this);
		copy.setAccelerator(
				KeyStroke.getKeyStroke(KeyEvent.VK_C, ActionEvent.CTRL_MASK));
		copy.setMnemonic(KeyEvent.VK_C);
		editMenu.add(copy);

		paste = new JMenuItem("Paste");
		paste.setAccelerator(
				KeyStroke.getKeyStroke(KeyEvent.VK_V, ActionEvent.CTRL_MASK));
		paste.setMnemonic(KeyEvent.VK_P);
		paste.addActionListener(this);
		editMenu.add(paste);

		mb = new JMenuBar();
		mb.add(fileMenu);
		mb.add(editMenu);
		// mb.add(styleMenu);
		setJMenuBar(mb);


		//List of Expressions
		input.setLayout(new GridBagLayout());

		expression = new JList(expressionList)
		{//This allows the tool tip to display the expression
			/**
			 * 
			 */
			private static final long serialVersionUID = -789541234065276141L;

			//the mouse is over.
			public String getToolTipText(MouseEvent e) {
				int index = locationToIndex(e.getPoint());
				if (-1 < index) {
					String line = expressionList.get(index).toString();
					String wrap = "<html>",end="<html>";
					char[] array = line.toCharArray();
					for(int i=0;i<array.length;i++){	
						wrap +=array[i];
						end =wrap;
						if(i%80==0&&i!=0) wrap +="<br>";
					}         
					return end.trim();
				} else {
					return null;
				}
			}
		};
		

		expression.addListSelectionListener(this);	

		JScrollPane expressionScroll = new JScrollPane(expression);
		expressionScroll.setPreferredSize(new Dimension(400, 350));

		derive.addActionListener(this);
		add.addActionListener(this);

		addCompItem(input, expressionScroll, gbc, 0, 1, 475, 350);
		addCompItem(this, input, gbc, 1, 1, 500, 500);

		//Selection Options
		selectButtons.setLayout(new GridBagLayout());
		selectAll.addActionListener(this);
		deselect.addActionListener(this);
		remove.addActionListener(this);
		edit.addActionListener(this);

		addCompItem(selectButtons,edit,gbc,0,2,1,1);
		addCompItem(selectButtons,remove,gbc,0,3,1,1);
		addCompItem(selectButtons,selectAll,gbc,0,0,1,1);
		addCompItem(selectButtons,deselect,gbc,0,1,1,1);
		addCompItem(selectButtons,derive,gbc,0,4,1,1);
		addCompItem(this, selectButtons, gbc, 501,2,1,1);

		saveas.setEnabled(false);
		derive.setEnabled(false);
		edit.setEnabled(false);
		remove.setEnabled(false);
		cut.setEnabled(false);
		copy.setEnabled(false);

		expression.setToolTipText("Expressions");

		//Operations
		buttons.setLayout(new GridBagLayout());
		Dimension dim = new Dimension(4,25);
		equals.addActionListener(this);
		plus.addActionListener(this);
		minus.addActionListener(this);
		times.addActionListener(this);
		divide.addActionListener(this);
		leftParen.addActionListener(this);
		rightParen.addActionListener(this);

		equals.setPreferredSize(dim);
		plus.setPreferredSize(dim);
		minus.setPreferredSize(dim);
		times.setPreferredSize(dim);
		divide.setPreferredSize(dim);
		leftParen.setPreferredSize(dim);
		rightParen.setPreferredSize(dim);


		addCompItem(buttons,plus,gbc,0,0,1,1);
		addCompItem(buttons,minus,gbc,1,0,1,1);
		addCompItem(buttons,divide,gbc,2,0,1,1);
		addCompItem(buttons,times,gbc,3,0,1,1);
		addCompItem(buttons,leftParen,gbc,4,0,1,1);
		addCompItem(buttons,rightParen,gbc,5,0,1,1);
		addCompItem(buttons,equals,gbc,6,0,1,1);
		addCompItem(this, buttons, gbc, 1,503,1,1);


		//Creating a new Expression
		newExpression.setLayout(new GridBagLayout());
		addExpression.addActionListener(this);
		addExpression.setSize(20, 1);
		metrics = new JComboBox();
		metrics.setRenderer(new MyComboBoxRenderer());
		metrics.addActionListener(this);
		metrics.setPreferredSize(new Dimension(10,22));


		clear.addActionListener(this);
		insert.addActionListener(this);

		addCompItem(newExpression,addExpression,gbc,1,1,25,1);
		addCompItem(newExpression,insert,gbc,0,0,1,1);
		addCompItem(newExpression,metrics,gbc,1,0,1,1);
		addCompItem(newExpression,add,gbc,0,1,1,1);
		addCompItem(newExpression,clear,gbc,26,1,1,1);
		addCompItem(this, newExpression, gbc, 1,502,1,1);

		loadMetrics();

	}
	private void setClipboard(String in){
		StringSelection stringSelection = new StringSelection( in );
		Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
		clipboard.setContents( stringSelection, stringSelection );
	}
	private String getFromClipboard(){
		String result = "";
		Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
		Transferable contents = clipboard.getContents(null);
		boolean hasTransferableText =
			(contents != null) &&
			contents.isDataFlavorSupported(DataFlavor.stringFlavor);
		if ( hasTransferableText ) {
			try {
				result = (String)contents.getTransferData(DataFlavor.stringFlavor);
			}
			catch (UnsupportedFlavorException ex){
				//highly unlikely since we are using a standard DataFlavor
				System.out.println(ex);
				ex.printStackTrace();
			}
			catch (IOException ex) {
				System.out.println(ex);
				ex.printStackTrace();
			}
		}
		return result;

	}

	public void actionPerformed(ActionEvent e) {
		try {
			Object arg = e.getSource();

			if(arg.equals(selectAll)){
				int[] ind =new int[expressionList.getSize()];
				for (int i=0;i<expressionList.getSize();i++){
					ind[i]=i;
				}
				expression.setSelectedIndices(ind);

			}else if(arg.equals(deselect)){
				expression.getSelectionModel().clearSelection();
			}else if(arg.equals(copy)){
				copy();
			}else if(arg.equals(cut)){
				cut();
			}else if(arg.equals(paste)){
				paste();
			}else if(arg.equals(add)){
				addExpression();
			}else if(arg.equals(open)){
				openFile();
			}else if(arg.equals(save)){
				saveFile();
			}else if(arg.equals(saveas)){
				saveSelected();
			}else if(arg.equals(derive)){
				if(expression.isSelectionEmpty()){
					JOptionPane.showMessageDialog(this,
							"Please select an expression.",
							"Warning",
							JOptionPane.WARNING_MESSAGE);
				}else
					deriveMetric();
			}else if(arg.equals(edit)){
				if(expression.isSelectionEmpty()){
					JOptionPane.showMessageDialog(this,
							"Please select an expression.",
							"Warning",
							JOptionPane.WARNING_MESSAGE);
				}else{
					edit(expression.getSelectedValue().toString());
				}
			}else if(arg.equals(remove)){
				remove();
			}else if(arg.equals(insert)){
				insertExpression("\""+metrics.getSelectedItem().toString()+"\"");
			}else if(arg.equals(plus)){
				insertExpression("+");
			}else if(arg.equals(minus)){
				insertExpression("-");
			}else if(arg.equals(times)){
				insertExpression("*");
			}else if(arg.equals(divide)){
				insertExpression("/");
			}else if(arg.equals(leftParen)){
				insertExpression("(");
			}else if(arg.equals(rightParen)){
				insertExpression(")");
			}else if(arg.equals(equals)){
				insertExpression("=");
			}else if(arg.equals(clear)){
				addExpression.setText("");
				addExpression.requestFocusInWindow();
			}else{
			}			
		} catch (FileNotFoundException ex) {
			// TODO Auto-generated catch block
			ex.printStackTrace();
		} catch (IOException ex) {
			// TODO Auto-generated catch block
			ex.printStackTrace();
		} finally {}
	}
	private void insertExpression(String string) {

		addExpression.replaceSelection(string);//puts string at point of cursor
		addExpression.requestFocusInWindow();
		//de-select the text
		int pos=addExpression.getSelectionStart();
		addExpression.setCaretPosition(pos);
		if(addExpression.getText().length()==pos){
			addExpression.setText(addExpression.getText()+" ");
			addExpression.setCaretPosition(pos);
		}
	}
	private void loadMetrics(){
		PerfExplorerConnection server = PerfExplorerConnection.getConnection();

		List<String> array = server.getPotentialMetrics(PerfExplorerModel.getModel());
		if(array.size()>0){
			for (Object item: array)
				metrics.addItem(item);
			metrics.setSelectedIndex(0);

		}
	}

	private void remove() {
		if(expression.isSelectionEmpty()){
			JOptionPane.showMessageDialog(this,
					"Please select an expression.",
					"Warning",
					JOptionPane.WARNING_MESSAGE);
		}else{
			while(!expression.isSelectionEmpty())
				expressionList.removeElementAt(expression.getSelectedIndex());
		}
	}
	private void edit(String expr) {
		String s = (String)JOptionPane.showInputDialog(
				this, "Edit Expression:\n","Edit",
				JOptionPane.PLAIN_MESSAGE,null,null,expr);
		if(s!=null){
			boolean isValid = validate(s);
			if(isValid){
				int index = expression.getSelectedIndex();
				expressionList.removeElementAt(index);
				expressionList.add(index, s);
			}else{
				edit(s);
			}
		}
	}

	private boolean validate(String expression){
		boolean result = PerfExplorerExpression.validate(expression);
		if(!result){
			JOptionPane.showMessageDialog(this,
					"The expression you entered is not valid.",
					"Invalid Expression",
					JOptionPane.ERROR_MESSAGE);

		}
		return result;
	}
	private void cut (){
		copy();
		remove();
	}

	private void addExpression(){
		addExpression("");
	}
	private void addExpression(String expression) {
		String text = addExpression.getText();

		if(text == null){			JOptionPane.showMessageDialog(this,
				"You cannot add a blank expression.",
				"Warning",JOptionPane.WARNING_MESSAGE);
		}
		else if(text.trim().equals("")){
			JOptionPane.showMessageDialog(this,
					"You cannot add a blank expression.",
					"Warning",JOptionPane.WARNING_MESSAGE);
		}else{
			boolean isvalid = validate(text);
			if(isvalid){
				expressionList.addElement(text.trim());
			}
		}
	}
	private void copy(){
		Object[] selectedExp = expression.getSelectedValues();
		String expressions="";
		for(Object express:selectedExp)	{
			expressions+=express+"\n";
		}
		setClipboard(expressions);
	}
	private void paste(){
		String clip = getFromClipboard();
		addExpressions(new Scanner(clip));
	}
	private void openFile() throws FileNotFoundException {
		int returnVal = fc.showOpenDialog(this);
		if (returnVal == JFileChooser.APPROVE_OPTION) {
			addExpressions (new Scanner(fc.getSelectedFile()));
		}

	}
	private void addExpressions(Scanner scan){
		while(scan.hasNextLine()){
			String line = scan.nextLine().trim();
			if(!line.equals("")){
				if(Expression.validate(line))
					expressionList.addElement(line);
				else
					addExpression(line);
			}
		}
	}
	private void saveFile() throws IOException {
		if(getFiletoSave()){
			File savefile =  fc.getSelectedFile();
			FileOutputStream write =new FileOutputStream(savefile);
			String out = "";

			for(Object i: expressionList.toArray()){
				out += i.toString() + "\n";
			}
			write.write(out.getBytes());
		}

	}
	private boolean getFiletoSave() {
		int returnVal = fc.showSaveDialog(this);
		if (returnVal == JFileChooser.APPROVE_OPTION) {
			File savefile =  fc.getSelectedFile();
			if(savefile.exists()){
				int result = 	JOptionPane.showOptionDialog(this, 
						"\""+savefile.getName()+"\" already exists. Do you want to replace it? ", "Replace File"
						,JOptionPane.YES_NO_OPTION,JOptionPane.WARNING_MESSAGE, null, null, null);
				if(result ==JOptionPane.NO_OPTION) 
					return getFiletoSave();
			}
			return true;
		}else 
			return false;//user hit cancel 
	}

	private void saveSelected() throws IOException {
		if(expression.isSelectionEmpty()){
			JOptionPane.showMessageDialog(this,
					"Please select an expression.",
					"Warning",
					JOptionPane.WARNING_MESSAGE);
			return;
		}

		if(getFiletoSave()){
			File savefile =  fc.getSelectedFile();
			FileOutputStream write =new FileOutputStream(savefile);
			String out = "";
			int[] indexs = expression.getSelectedIndices();
			for(int i: indexs){
				out += expressionList.get(i) + "\n";
			}
			write.write(out.getBytes());
		}
	}
	private void deriveMetric() {

		String message = "Are you sure you want to apply the selected expressions to \n";
		if(selectTrial !=null){
			message += "the \""+selectTrial.getName() +"\" trial from the \""+selectExp.getName()
			+"\" experiment from the \""+selectApp.getName()+"\" application?";
		}else if(selectExp !=null){
			message += "all the trials in the \""+selectExp.getName()
			+"\" experiment in the \""+selectApp.getName()+"\" application?";
		}else if(selectApp !=null){
			message += "all the trials in the all of the expriments in the \"" +selectApp.getName()+"\" application?";
		}

		int result = 	JOptionPane.showOptionDialog(this, 
				message, "Confirm Trials"
				,JOptionPane.YES_NO_OPTION,JOptionPane.WARNING_MESSAGE, null, null, null);
		if(result ==JOptionPane.NO_OPTION) 
			return;

		Object[] selectedExp = expression.getSelectedValues();
		String expressions="";
		for(Object express:selectedExp)	{
			expressions+=express+"\n";
		}
		try{
			PerfExplorerExpression exp = new PerfExplorerExpression();
			String script;
			String app=null,ex=null,trial=null;
			if(selectApp != null)  app = selectApp.getName();
			if(selectExp != null)  ex = selectExp.getName();
			if(selectTrial != null)  trial = selectTrial.getName();
			script = exp.getScriptFromExpressions(app,ex,trial,expressions);	
			new ScriptThread(script,true);
		}catch(ParsingException ex){

			JOptionPane.showMessageDialog(mainWindow, 
					"The expression did not parse correctly.\n"+ex.getMessage(),
					"Parse Error", JOptionPane.ERROR_MESSAGE);
		}
	}
	public void addCompItem(JFrame frame, Component c, GridBagConstraints gbc, int x, int y, int w, int h) {
		gbc.gridx = x;
		gbc.gridy = y;
		gbc.gridwidth = w;
		gbc.gridheight = h;
		frame.getContentPane().add(c, gbc);
	}

	public void addCompItem(Container container, Component c, GridBagConstraints gbc, int x, int y, int w, int h) {
		gbc.gridx = x;
		gbc.gridy = y;
		gbc.gridwidth = w;
		gbc.gridheight = h;
		gbc.fill = GridBagConstraints.HORIZONTAL;
		container.add(c, gbc);
	}
	public void update(Observable o, Object arg) {
		// TODO Auto-generated method stub

	}
	public void valueChanged(ListSelectionEvent e) {
		if (e.getValueIsAdjusting() == false) {
			if (expression.isSelectionEmpty()) {
				saveas.setEnabled(false);
				derive.setEnabled(false);
				edit.setEnabled(false);
				remove.setEnabled(false);
				cut.setEnabled(false);
				copy.setEnabled(false);
			} else {
				saveas.setEnabled(true);
				derive.setEnabled(true);
				edit.setEnabled(true);
				remove.setEnabled(true);
				cut.setEnabled(true);
				copy.setEnabled(true);
			}
		}
	}
	public void itemStateChanged(ItemEvent e) {
		// TODO Auto-generated method stub

	}
	public void stateChanged(ChangeEvent e) {
		// TODO Auto-generated method stub

	}
}
class MyComboBoxRenderer extends BasicComboBoxRenderer {
	/**
	 * 
	 */
	private static final long serialVersionUID = -1788895816143895038L;

	public Component getListCellRendererComponent(JList list, Object value,
			int index, boolean isSelected, boolean cellHasFocus) {

		if (isSelected) {
			setBackground(list.getSelectionBackground());
			setForeground(list.getSelectionForeground());
			if (-1 < index) {
				String line = list.getSelectedValue().toString();
				//  Pattern p = Pattern.compile( "(.{0,80}\\b\\s*)|(.{80}\\B)" ); 
				//Matcher m = p.matcher(line);
				String wrap = "<html>",end="<html>";
				//while (m.find()) {
				char[] array = line.toCharArray();
				for(int i=0;i<array.length;i++){	
					wrap +=array[i];
					end =wrap;
					if(i%80==0&&i!=0) wrap +="<br>";
					//end = wrap +line.substring(m.start(), m.end());
					//  wrap +=line.substring(m.start(), m.end())+"<br>";
				}         
				list.setToolTipText(end.trim());

			}
		} else {
			setBackground(list.getBackground());
			setForeground(list.getForeground());
		}
		setFont(list.getFont());
		setText((value == null) ? "" : value.toString());

		return this;
	}
}




