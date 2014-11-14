package edu.uoregon.tau.perfdmf.database;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Serializable;
import java.net.URL;

/* This class is intended to read in config.txt file and parse the parameters. */

public class ParseConfig implements Serializable {
    /**
	 *
	 */
	private static final long serialVersionUID = -22449977900556139L;
	private String perfdmfHome;
    private String jdbcJarFile;
    private String jdbcDriver;
    private String dbType;
    private String dbHost;
    private String dbPort;
    private String dbName;
    private String dbSchemaPrefix = "";
    private String dbUserName;
    private String dbPasswd;
    private String dbSchema;
    private boolean dbUseSSL = false;

    private String dbKeystore;
    private String dbKeystorePasswd;

    private String dbTruststore;;
    private String dbTruststorePasswd;

    private String xmlSAXParser;
    private String path;
    private String name;

    /**
     * acceptable values for booleans in config file.
     */
    private boolean stringToBool(String value) {
        return (value != null &&
                ("yes".equalsIgnoreCase(value)
                 || "y".equalsIgnoreCase(value)
                 || "true".equalsIgnoreCase(value)));
    }


    public ParseConfig(String configLoc) {

        path = configLoc;
        String[] split = configLoc.split("\\.");
        name = split[split.length - 1];
        if (name.compareTo("cfg") == 0)
            name = "Default";
        String inputString;
        String name;
        String value;

        try {
            BufferedReader reader;
            if (configLoc.toLowerCase().startsWith("http:")) {
                // When it gets converted from a String to a File http:// turns into http:/
                String url_string = "";
                if (configLoc.toLowerCase().startsWith("http://")) {
                    url_string = "http://" + configLoc.toString().substring(7).replace('\\', '/');
                } else if (configLoc.toLowerCase().startsWith("http:/")) {
                    url_string = "http://" + configLoc.toString().substring(6).replace('\\', '/');
                }
                URL url = new URL(url_string);
                InputStream iostream = url.openStream();
                InputStreamReader ireader = new InputStreamReader(iostream);
                reader = new BufferedReader(ireader);
            } else {
                reader = new BufferedReader(new FileReader(new File(configLoc)));
            }

            // The following is for reading perfdmf.cfg out of the jar file for Java Web Start
            //        URL url = ParseConfig.class.getResource("/perfdmf.cfg");
            //
            //        if (url == null) {
            //        }
            //            throw new IOException("Couldn't get perfdmf.cfg from the jar");
            //        BufferedReader reader = new BufferedReader(new InputStreamReader(url.openStream()));
            //

            while ((inputString = reader.readLine()) != null) {
                inputString = inputString.trim();
                if (inputString.startsWith("#") || inputString.equals("")) {
                    continue;
                } else {
                    name = getNameToken(inputString).toLowerCase();
                    value = getValueToken(inputString);
                    if (name.equals("perfdmf_home"))
                        perfdmfHome = value;
                    else if (name.equals("jdbc_db_jarfile"))
                        jdbcJarFile = value;
                    else if (name.equals("jdbc_db_driver"))
                        jdbcDriver = value;
                    else if (name.equals("jdbc_db_type"))
                        dbType = value;
                    else if (name.equals("db_hostname"))
                        dbHost = value;
                    else if (name.equals("db_portnum"))
                        dbPort = value;
                    else if (name.equals("db_dbname"))
                        dbName = value;
                    else if (name.equals("db_schemaprefix"))
                        dbSchemaPrefix = value;
                    else if (name.equals("db_username"))
                        dbUserName = value;
                    else if (name.equals("db_use_ssl"))
                        dbUseSSL = stringToBool(value);
                    else if (name.equals("db_keystore"))
                        dbKeystore = value;
                    else if (name.equals("db_keystore_password"))
                        dbKeystorePasswd = value;
                    else if (name.equals("db_truststore"))
                        dbTruststore = value;
                    else if (name.equals("db_truststore_password"))
                        dbTruststorePasswd = value;
                    else if (name.equals("db_password"))
                        dbPasswd = value;
                    else if (name.equals("db_schemafile"))
                        dbSchema = value;
                    else if (name.equals("xml_sax_parser"))
                        xmlSAXParser = value;
                    else {
                        System.out.println(name + " is not a valid configuration item.");
                    }
                }
            }
            reader.close();
        } catch (Exception e) {
            // wrap it up in a runtime exception

            e.printStackTrace();
            //throw new TauRuntimeException("Unable to parse \"" + configLoc + "\"", e);
        }
    }

    public String getNameToken(String aLine) {
        int i = aLine.indexOf(":");
        if (i > 0) {
            return aLine.substring(0, i).trim();
        } else {
            return null;
        }

    }

    public String getConnectionString() {
        String connectionString;
        if (getDBType().equals("derby")) {
            connectionString = "jdbc:" + getDBType() + ":" + getDBName();
        } else if (getDBType().equals("sqlite")) {
            connectionString = "jdbc:" + getDBType() + ":" + getDBName();
		}
		/*
		 * The default connect string URL is necessary for successfully
		 * connecting to mysql databases via the portal
		 */
		// else if (getDBType().equals("mysql")) {
		// connectionString = "jdbc:" + getDBType() + ":" + getDBName();
		// }
		else if (getDBType().equals("h2")) {
            connectionString = "jdbc:" + getDBType() + ":" + getDBName() + ";AUTO_SERVER=TRUE";
        } else {
            if (getDBType().equals("oracle")) {
                connectionString = "jdbc:oracle:thin:@//" + getDBHost() + ":" + getDBPort() + "/" + getDBName();
            } else {
                connectionString = "jdbc:" + getDBType() + "://" + getDBHost() + ":" + getDBPort() + "/" + getDBName();
            }
        }
        return connectionString;
    }

    public String getValueToken(String aLine) {
        int i = aLine.indexOf(":");
        if (i > 0) {
            return aLine.substring(i + 1).trim();
        } else {
            return null;
        }
    }

    public String getPerfDMFHome() {
        return perfdmfHome;
    }

    public String getJDBCJarFile() {
        return jdbcJarFile;
    }

    public String getJDBCDriver() {
        return jdbcDriver;
    }

    public String getDBType() {
        return dbType;
    }

    public String getDBHost() {
        return dbHost;
    }

    public String getDBPort() {
        return dbPort;
    }

    public String getDBName() {
        return dbName;
    }

    public String getDBSchemaPrefix() {
        return dbSchemaPrefix;
    }

    public String getDBUserName() {
        return dbUserName;
    }

    public boolean getDBUseSSL() {
        return dbUseSSL;
    }

    public String getDBKeystore() {
        return dbKeystore;
    }

    public String getDBKeystorePasswd() {
        return dbKeystorePasswd;
    }

    public String getDBTruststore() {
        return dbTruststore;
    }

    public String getDBTruststorePasswd() {
        return dbTruststorePasswd;
    }

    public String getDBPasswd() {
        return dbPasswd;
    }

    public String getDBSchema() {
        return dbSchema;
    }

    public String getXMLSAXParser() {
        return xmlSAXParser;
    }

    public String getName() {
        return name;
    }

    public String getPath() {
        return path;
    }
}
