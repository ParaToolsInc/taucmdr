package edu.uoregon.tau.perfdmf.database;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Observable;
import java.util.Observer;
import java.util.Vector;

import javax.swing.BorderFactory;
import javax.swing.DefaultListSelectionModel;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JProgressBar;
import javax.swing.JTextField;
import javax.swing.ListSelectionModel;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;

import edu.uoregon.tau.common.Common;
import edu.uoregon.tau.common.Utility;
import edu.uoregon.tau.common.Wget;
import edu.uoregon.tau.common.Wget.Progress;
import edu.uoregon.tau.common.tar.Tar;
import edu.uoregon.tau.perfdmf.loader.Configure;
import edu.uoregon.tau.perfdmf.loader.ConfigureTest;

public class DatabaseManagerWindow extends JFrame implements ActionListener, Observer, ListSelectionListener, ItemListener,
        ChangeListener {

    /**
     * 
     */

    private static final long serialVersionUID = 1L;
    private String lastDirectory;
    private JList configList = new JList((Vector<String>) ConfigureFiles.getConfigurationNames());
    private JButton saveConfig = new JButton("Save Configuration");
    private JButton removeConfig = new JButton("Remove Configuration");
    private JTextField name = new JTextField(15);
    private JPanel configurations = new JPanel();
    private JPanel editConfiguration = new JPanel();
    private String[] adapters = { "mysql", "postgresql", "oracle", "derby", "db2", "h2", "sqlite" };
    private JComboBox adapter = new JComboBox(adapters);
    private JTextField driver = new JTextField(15);
    private JTextField host = new JTextField(15);
    private JTextField databaseName = new JTextField(15);
    private JTextField databaseUser = new JTextField(15);
    private JPasswordField databasePassword = new JPasswordField(15);
    private JButton jarfileChooser = new JButton("Browse...");
    private JButton schemafileChooser = new JButton("Browse...");
    private JTextField jarfile = new JTextField(15);
    private JTextField port = new JTextField(4);
    private JButton download = new JButton("Download");
    private JProgressBar bar = new JProgressBar();
    private JTextField schema = new JTextField(15);
    private JButton newConfig = new JButton("New Configuration");
    private JButton close = new JButton("Close");
    private JPanel buttons = new JPanel();
    private JCheckBox savePassword = new JCheckBox();

    private JLabel labelAdapter = new JLabel("Database Adapter:");
    private JLabel labelDriver = new JLabel("Database Driver:");
    private JLabel labelHost = new JLabel("Database Host:");
    private JLabel labelDatabaseName = new JLabel("Database Name:");
    private JLabel labelDatabaseUser = new JLabel("Database Username:");
    private JLabel labelDatabasePassword = new JLabel("Database Password:");
    private JLabel labelJarFile = new JLabel("Jar Path:");
    private JLabel labelPort = new JLabel("Database Port:");
    private JLabel labelConfig = new JLabel("Configurations:");
    private JLabel labelName = new JLabel("Name:");
    private JLabel labelBar = new JLabel("Downloading...");
    private JLabel labelSchema = new JLabel("Schema File:");

    private ParseConfig selectedConfig;

    private DBManagerListener mainWindow;

    private String jarLocation;
    private String schemaLocation;
    
    public DatabaseManagerWindow(DBManagerListener mw, String jarLocation, String schemaLocation) {
        mainWindow = mw;
        this.jarLocation = jarLocation;
        this.schemaLocation = schemaLocation;

        if (ConfigureFiles.getConfigurations().size() > 0) {
            selectedConfig = (ConfigureFiles.getConfigurations().get(0));
        } else {
            selectedConfig = null;
        }

        lastDirectory = getUserJarDir();

        jarfileChooser.setText("Browse...");
        jarfileChooser.addActionListener(this);
        jarfileChooser.setActionCommand("jar");
        schemafileChooser.setText("Browse...");
        schemafileChooser.addActionListener(this);
        schemafileChooser.setActionCommand("schema");
        saveConfig.setText("Save Configuration");
        saveConfig.addActionListener(this);
        removeConfig.setText("Remove Configuration");
        removeConfig.addActionListener(this);
        newConfig.setText("New Configuration");
        newConfig.addActionListener(this);
        close.setText("Close");
        close.addActionListener(this);

        download.setText("Download");
        download.addActionListener(this);

        adapter.addItemListener(this);

        //bar.setIndeterminate(false);
        bar.setVisible(false);
        savePassword.setText("Save in cleartext?");

        savePassword.setSelected(true);
        savePassword.addChangeListener(this);

        adapter.setSelectedItem("h2");
        host.setEnabled(false);
        host.setText("");
        databasePassword.setEditable(false);
        databasePassword.setEnabled(true);
        databasePassword.setText("");
        savePassword.setEnabled(false);
        port.setEnabled(false);
        port.setText("");
        download.setEnabled(false);

        name.setText("Default");

        databaseName.setText("perfdmf");

        labelBar.setVisible(false);
        labelBar.setLabelFor(bar);
        labelAdapter.setLabelFor(adapter);
        labelDriver.setLabelFor(driver);
        labelHost.setLabelFor(host);
        labelDatabaseName.setLabelFor(databaseName);
        labelDatabaseUser.setLabelFor(databaseUser);
        labelDatabasePassword.setLabelFor(databasePassword);
        labelJarFile.setLabelFor(jarfile);
        labelPort.setLabelFor(port);
        labelConfig.setLabelFor(configList);
        labelName.setLabelFor(name);
        labelSchema.setLabelFor(schema);

        labelBar.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelAdapter.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelDriver.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelHost.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelDatabaseName.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelDatabaseUser.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelDatabasePassword.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelJarFile.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelPort.setAlignmentY(JLabel.RIGHT_ALIGNMENT);
        labelName.setAlignmentY(JLabel.RIGHT_ALIGNMENT);

        this.setTitle("Manage Database Configurations");

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.anchor = GridBagConstraints.NORTHWEST;
        gbc.weightx = 0.5;
        gbc.weighty = 0.5;

        editConfiguration.setLayout(new GridBagLayout());

        //    	editConfiguration.add(labelAdapter);
        //    	editConfiguration.add(adapter);
        //    	editConfiguration.add(labelHost);
        //    	editConfiguration.add(host);
        //    	editConfiguration.add(labelDatabaseName);
        //    	editConfiguration.add(databaseName);
        //    	editConfiguration.add(labelDatabaseUser);
        //    	editConfiguration.add(databaseUser);
        //    	editConfiguration.add(labelDatabasePassword);
        //    	editConfiguration.add(databasePassword);
        //    	editConfiguration.add(labelPort);
        //    	editConfiguration.add(port);
        //    	editConfiguration.add(labelDriver);
        //    	editConfiguration.add(driver);
        //    	editConfiguration.add(labelJarFile);
        //    	editConfiguration.add(jarfile);

        Utility.addCompItem(editConfiguration, labelName, gbc, 0, 0, 1, 1);
        Utility.addCompItem(editConfiguration, name, gbc, 1, 0, 1, 1);
        Utility.addCompItem(editConfiguration, labelAdapter, gbc, 0, 1, 1, 1);
        Utility.addCompItem(editConfiguration, adapter, gbc, 1, 1, 1, 1);
        Utility.addCompItem(editConfiguration, labelHost, gbc, 0, 2, 1, 1);
        Utility.addCompItem(editConfiguration, host, gbc, 1, 2, 1, 1);
        Utility.addCompItem(editConfiguration, labelDatabaseName, gbc, 0, 3, 1, 1);
        Utility.addCompItem(editConfiguration, databaseName, gbc, 1, 3, 1, 1);
        Utility.addCompItem(editConfiguration, labelDatabaseUser, gbc, 0, 4, 1, 1);
        Utility.addCompItem(editConfiguration, databaseUser, gbc, 1, 4, 1, 1);
        Utility.addCompItem(editConfiguration, labelDatabasePassword, gbc, 0, 5, 1, 1);
        Utility.addCompItem(editConfiguration, databasePassword, gbc, 1, 5, 1, 1);
        Utility.addCompItem(editConfiguration, savePassword, gbc, 2, 5, 2, 1);
        Utility.addCompItem(editConfiguration, labelPort, gbc, 0, 6, 1, 1);
        Utility.addCompItem(editConfiguration, port, gbc, 1, 6, 1, 1);
        Utility.addCompItem(editConfiguration, labelDriver, gbc, 0, 7, 1, 1);
        Utility.addCompItem(editConfiguration, driver, gbc, 1, 7, 1, 1);
        Utility.addCompItem(editConfiguration, labelJarFile, gbc, 0, 8, 1, 1);
        Utility.addCompItem(editConfiguration, jarfile, gbc, 1, 8, 1, 1);
        Utility.addCompItem(editConfiguration, jarfileChooser, gbc, 2, 8, 1, 1);
        // Nothing to download anymore!
        //ParaProfUtils.addCompItem(editConfiguration, download, gbc, 3, 8, 1, 1);
        Utility.addCompItem(editConfiguration, labelSchema, gbc, 0, 9, 1, 1);
        Utility.addCompItem(editConfiguration, schema, gbc, 1, 9, 1, 1);
        Utility.addCompItem(editConfiguration, schemafileChooser, gbc, 2, 9, 1, 1);
        Utility.addCompItem(editConfiguration, labelBar, gbc, 0, 10, 1, 1);
        Utility.addCompItem(editConfiguration, bar, gbc, 1, 10, 2, 1);

        configurations.setLayout(new GridBagLayout());
        DefaultListSelectionModel select = new DefaultListSelectionModel();
        select.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);

        configList.setSelectionModel(select);
        configList.setBorder(BorderFactory.createLoweredBevelBorder());
        configList.addListSelectionListener(this);

        Utility.addCompItem(configurations, labelConfig, gbc, 0, 0, 1, 1);
        Utility.addCompItem(configurations, configList, gbc, 0, 1, 1, 1);
        //ParaProfUtils.addCompItem(configurations, saveConfig, gbc, 0, 2, 1, 1);
        //ParaProfUtils.addCompItem(configurations, removeConfig, gbc, 0, 3, 1, 1);

        buttons.setLayout(new GridBagLayout());
        Utility.addCompItem(buttons, newConfig, gbc, 0, 0, 1, 1);
        Utility.addCompItem(buttons, saveConfig, gbc, 1, 0, 1, 1);
        Utility.addCompItem(buttons, removeConfig, gbc, 2, 0, 1, 1);
        Utility.addCompItem(buttons, close, gbc, 3, 0, 1, 1);
        //this.addFocusListener(this);

        this.getContentPane().setLayout(new GridBagLayout());

        this.setSize(new Dimension(800, 450));

        //configurations.setLayout(new GridBagLayout());
        Utility.addCompItem(this, configurations, gbc, 0, 0, 1, 1);
        //editConfiguration.setLayout(new GridBagLayout());
        Utility.addCompItem(this, editConfiguration, gbc, 1, 0, 1, 1);
        Utility.addCompItem(this, buttons, gbc, 0, 1, 2, 1);
    }

    public void updateFields() {
        name.setText(selectedConfig.getName());
        adapter.setSelectedItem(selectedConfig.getDBType());
        host.setText(selectedConfig.getDBHost());
        databaseName.setText(selectedConfig.getDBName());
        databaseUser.setText(selectedConfig.getDBUserName());
        databasePassword.setText(selectedConfig.getDBPasswd());
        if (selectedConfig.getDBPasswd() == null) {
            savePassword.setSelected(false);
        } else {
            savePassword.setSelected(true);
        }
        port.setText(selectedConfig.getDBPort());
        driver.setText(selectedConfig.getJDBCDriver());
        jarfile.setText(selectedConfig.getJDBCJarFile());
        schema.setText(selectedConfig.getDBSchema());
    }

    public String writeConfig() {
        return writeConfig((String) configList.getModel().getElementAt(configList.getSelectedIndex()));
    }

    public String writeConfig(String name) {
        if (name == "unnamed") {
            name = "";
        }

        Configure config = new Configure("", "");

        File home = new File(System.getProperty("user.home") + "/.ParaProf");
        if (!home.exists()) {
            home.mkdir();
        }

        config.initialize(System.getProperty("user.home") + File.separator + ".ParaProf" + File.separator + "perfdmf.cfg");
        if (name.compareTo("Default") == 0) {
            config.setConfigFileName("");
        } else {
            config.setConfigFileName(name);
        }
        config.setJDBCType((String) (adapter.getSelectedItem()));
        config.setDBHostname(host.getText());
        config.setDBName(databaseName.getText());
        config.setDBUsername(databaseUser.getText());
        if (savePassword.isSelected()) {
            config.setDBPassword(new String(databasePassword.getPassword()));
            config.savePassword();
        }

        config.setDBPortNum(port.getText());
        config.setJDBCDriver(driver.getText());
        config.setJDBCJarfile(jarfile.getText());
        config.setDBSchemaFile(schema.getText());
        return config.writeConfigFile();
    }

    public void actionPerformed(ActionEvent e) {
        try {
            String arg = e.getActionCommand();
            if (arg.equals("jar")) {
                JFileChooser jFileChooser = new JFileChooser(lastDirectory);
                jFileChooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
                jFileChooser.setMultiSelectionEnabled(false);
                jFileChooser.setDialogTitle("Select File");
                jFileChooser.setApproveButtonText("Select");
                if ((jFileChooser.showOpenDialog(this)) != JFileChooser.APPROVE_OPTION) {
                    return;
                }
                lastDirectory = jFileChooser.getSelectedFile().getParent();
                jarfile.setText(jFileChooser.getSelectedFile().getAbsolutePath());
            } else if (arg.equals("schema")) {
                JFileChooser jFileChooser = new JFileChooser(lastDirectory);
                jFileChooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
                jFileChooser.setMultiSelectionEnabled(false);
                jFileChooser.setDialogTitle("Select File");
                jFileChooser.setApproveButtonText("Select");
                if ((jFileChooser.showOpenDialog(this)) != JFileChooser.APPROVE_OPTION) {
                    return;
                }
                lastDirectory = jFileChooser.getSelectedFile().getParent();
                schema.setText(jFileChooser.getSelectedFile().getAbsolutePath());
            } else if (arg.equals("Save Configuration")) {
                //???
                String filename = writeConfig(name.getText());
                configList.clearSelection();
                configList.setListData((Vector<String>) ConfigureFiles.getConfigurationNames());
                ConfigureTest config = new ConfigureTest();
                config.initialize(filename);
                //config.setDBSchemaFile("dbschema." + adapter.getSelectedItem().toString() + ".txt");
                if (!config.checkSchema()) {
                    int response = JOptionPane.showConfirmDialog(this,
                            "This database has not been initalized with PerfDMF.  Would you like to upload the schema?",
                            "Initialize with PerfDMF", JOptionPane.YES_NO_OPTION, JOptionPane.QUESTION_MESSAGE);
                    if (response == JOptionPane.NO_OPTION) {
                        return;
                    }
                }
                config.createDB(false);
                mainWindow.refreshDatabases();
            } else if (arg.equals("Remove Configuration")) {
                String path = selectedConfig.getPath();
                File removeFile = new File(path);
                //System.out.println(removeFile.exists() + "File path: " + removeFile.getAbsolutePath());
                removeFile.delete();
                configList.clearSelection();
                configList.setListData((Vector<String>) ConfigureFiles.getConfigurationNames());
                mainWindow.refreshDatabases();
            } else if (arg.equals("Download")) {
                JFileChooser jFileChooser = new JFileChooser(lastDirectory);
                jFileChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
                jFileChooser.setMultiSelectionEnabled(false);
                jFileChooser.setDialogTitle("Download To This Directory");
                jFileChooser.setApproveButtonText("Download");
                if ((jFileChooser.showOpenDialog(this)) != JFileChooser.APPROVE_OPTION) {
                    return;
                }
               // JProgressBar bar = new JProgressBar();
                //bar.setIndeterminate(true);

                this.bar.setVisible(true);
                this.labelBar.setVisible(true);

                String filename = this.download_jar(jFileChooser.getSelectedFile());
                this.jarfile.setText(filename);
            } else if (arg.equals("New Configuration")) {
                name.setText("");
                adapter.setSelectedItem("h2");
                host.setText("");
                databaseName.setText("perfdmf");
                databaseUser.setText("");
                databasePassword.setText("");
                port.setText("");
                driver.setText("org.h2.Driver");
                jarfile.setText("h2.jar");
                schema.setText("dbschema.h2.txt");
                host.setEnabled(false);
                host.setText("");
                databasePassword.setEditable(false);
                databasePassword.setEnabled(true);
                databasePassword.setText("");
                savePassword.setEnabled(false);
                port.setEnabled(false);
                port.setText("");
                download.setEnabled(false);
            } else if (arg.equals("Close"))
                this.setVisible(false);

        } finally {}
    }

    private String download_jar(File selectedFile) {

        (new File(".perfdmf_tmp")).mkdirs();
        System.setProperty("tar.location", ".perfdmf_tmp");
        String dest = null;
        try {
            String filename = "";
            if (((String) adapter.getSelectedItem()).compareToIgnoreCase("postgresql") == 0) {
                Wget.wget("http://www.cs.uoregon.edu/research/paracomp/tau/postgresql-redirect.html", ".perfdmf_tmp"
                        + File.separator + "redirect.html", false);
                filename = "postgresql.jar";
            } else if (((String) adapter.getSelectedItem()).compareToIgnoreCase("mysql") == 0) {
                Wget.wget("http://www.cs.uoregon.edu/research/paracomp/tau/mysql-redirect.html", ".perfdmf_tmp" + File.separator
                        + "redirect.html", false);
                filename = "mysql.jar";
            } else {
                return null;
            }

            BufferedReader r = new BufferedReader(new InputStreamReader(new FileInputStream(new File(".perfdmf_tmp"
                    + File.separator + "redirect.html"))));

            String URL = null;
            String FILE = null;
            String JAR = null;
            String line = r.readLine();
            while (line != null) {
                if (line.startsWith("URL="))
                    URL = line.substring(4);
                if (line.startsWith("FILE="))
                    FILE = line.substring(5);
                if (line.startsWith("JAR="))
                    JAR = line.substring(4);
                line = r.readLine();
            }
            r.close();

            dest = selectedFile.getAbsolutePath() + File.separator + filename;

            DownloadThread downloadJar = new DownloadThread(bar, labelBar, URL, FILE, JAR, dest);

            downloadJar.start();

            //DownloadProgress prg = new DownloadProgress(bar, labelBar);
            //Wget.wget(URL, dest, true, prg);

        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }

        return dest;
    }

    public class DownloadThread extends Thread {
        private JProgressBar bar;
        //private JLabel label;
        private String url;
        private String destinationFile;
        private String jar;
        private String file;

        public DownloadThread(JProgressBar b, JLabel lab, String u, String file, String jar, String destination) {
            super();
            bar = b;
            //label = lab;
            url = u;
            this.file = file;
            this.jar = jar;
            destinationFile = destination;
        }

        public void run() {
            DownloadProgress prg = new DownloadProgress(bar, labelBar);
            try {
                Wget.wget(url, ".perfdmf_tmp" + File.separator + file, true, prg);
                if (jar != null) {
                    // mysql
                    Tar.guntar(".perfdmf_tmp" + File.separator + file);
                    Common.copy(".perfdmf_tmp" + File.separator + jar, destinationFile);
                } else {
                    Common.copy(".perfdmf_tmp" + File.separator + file, destinationFile);
                }
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }
    }

    public class DownloadProgress implements Progress {
        private JProgressBar bar;
        private JLabel label;

        public DownloadProgress(JProgressBar b, JLabel lab) {
            bar = b;
            label = lab;
        }

        public void reportFininshed(int bytes) {
            bar.setValue(bytes);
            label.setText("Done.");
        }

        public void reportProgress(int bytes) {
            bar.setValue(bytes);
            label.repaint();
        }

        public void reportSize(int bytes) {
            //bar.setIndeterminate(false);
            bar.setMaximum(bytes);
            bar.setValue(0);
            bar.setVisible(true);
            label.setText("Downloading");
            label.setVisible(true);
        }

    }

    public void update(Observable arg0, Object arg1) {
    // TODO Auto-generated method stub

    }

    public void valueChanged(ListSelectionEvent arg0) {
        //configList.clearSelection();
        if (configList.getSelectedIndex() != -1)
            selectedConfig = ConfigureFiles.getConfigurations().get(configList.getSelectedIndex());
        switchAdapter((String) adapter.getSelectedItem());
        this.updateFields();

    }

    private String getUserJarDir() {
        return System.getProperty("user.home") + File.separator + ".ParaProf";
    }

    private void switchAdapter(String newAdapter) {
        this.schema.setText(schemaLocation + File.separator + "dbschema." + newAdapter + ".txt");

        if (newAdapter.compareTo("mysql") == 0) {
            download.setEnabled(true);
            host.setEnabled(true);
            databasePassword.setEditable(true);
            savePassword.setEnabled(true);
            databasePassword.setEnabled(true);
            savePassword.setSelected(true);
            port.setEnabled(true);
            labelDatabaseName.setText("Database Name:");
            this.driver.setText("org.gjt.mm.mysql.Driver");
            this.port.setText("3306");
            this.host.setText("localhost");
            String jarlocation = jarLocation + File.separator + "mysql.jar";
            this.jarfile.setText(jarlocation);
        } else if (newAdapter.compareTo("postgresql") == 0) {
            download.setEnabled(true);
            host.setEnabled(true);
            databasePassword.setEditable(true);
            databasePassword.setEnabled(true);
            savePassword.setEnabled(true);
            savePassword.setSelected(true);
            port.setEnabled(true);
            labelDatabaseName.setText("Database Name:");
            this.driver.setText("org.postgresql.Driver");
            this.port.setText("5432");
            this.host.setText("localhost");
            String jarlocation = jarLocation + File.separator + "postgresql.jar";
            this.jarfile.setText(jarlocation);
            this.schema.setText(schemaLocation + File.separator + "dbschema.txt");
        } else if (newAdapter.compareTo("oracle") == 0) {
            download.setEnabled(false);
            host.setEnabled(true);
            databasePassword.setEditable(true);
            databasePassword.setEnabled(true);
            savePassword.setEnabled(true);
            savePassword.setSelected(true);
            port.setEnabled(true);
            labelDatabaseName.setText("Database Name:");
            this.driver.setText("oracle.jdbc.OracleDriver");
            this.port.setText("1521");
            this.host.setText("localhost");
            this.jarfile.setText("(Please Acquire oracle's JDBC driver)");
        } else if (newAdapter.compareTo("derby") == 0) {
            host.setEnabled(false);
            host.setText("");
            databasePassword.setEditable(false);
            databasePassword.setEnabled(false);
            databasePassword.setText("");
            savePassword.setEnabled(false);
            port.setEnabled(false);
            port.setText("");
            download.setEnabled(false);
            labelDatabaseName.setText("Path to Database:");
            this.driver.setText("org.apache.derby.jdbc.EmbeddedDriver");
            String jarlocation = jarLocation + File.separator + "derby.jar";
            this.jarfile.setText(jarlocation);
        } else if (newAdapter.compareTo("sqlite") == 0) {
            host.setEnabled(false);
            host.setText("");
            databasePassword.setEditable(false);
            databasePassword.setEnabled(false);
            databasePassword.setText("");
            savePassword.setEnabled(false);
            port.setEnabled(false);
            port.setText("");
            download.setEnabled(false);
            labelDatabaseName.setText("Path to Database:");
            this.driver.setText("org.sqlite.JDBC");
            String jarlocation = jarLocation + File.separator + "sqlite.jar";
            this.jarfile.setText(jarlocation);
        } else if (newAdapter.compareTo("h2") == 0) {
            host.setEnabled(false);
            host.setText("");
            databasePassword.setEditable(false);
            databasePassword.setEnabled(false);
            databasePassword.setText("");
            savePassword.setEnabled(false);
            port.setEnabled(false);
            port.setText("");
            download.setEnabled(false);
            labelDatabaseName.setText("Path to Database:");
            this.driver.setText("org.h2.Driver");
            String jarlocation = jarLocation + File.separator + "h2.jar";
            this.jarfile.setText(jarlocation);
        } else if (newAdapter.compareTo("db2") == 0) {
            download.setEnabled(false);
            host.setEnabled(true);
            databasePassword.setEditable(true);
            databasePassword.setEnabled(true);
            savePassword.setEnabled(true);
            savePassword.setSelected(true);
            port.setEnabled(true);
            labelDatabaseName.setText("Database Name:");
            this.driver.setText("com.ibm.db2.jcc.DB2Driver");
            this.port.setText("446");
            this.host.setText("localhost");
            this.jarfile.setText("(Please Acquire db2's JDBC driver)");
        }
    }

    public void itemStateChanged(ItemEvent arg0) {
        if (arg0.getStateChange() == ItemEvent.SELECTED) {
            switchAdapter((String) arg0.getItem());
        }
    }

    public void stateChanged(ChangeEvent arg0) {
        if (savePassword.isSelected()) {
            databasePassword.setEditable(true);
        } else {
            databasePassword.setEditable(false);
        }
    }
}
