package edu.uoregon.tau.perfdmf;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;

import org.xml.sax.*;
import org.xml.sax.helpers.DefaultHandler;
import org.xml.sax.helpers.XMLReaderFactory;

import edu.uoregon.tau.common.Gzip;
import edu.uoregon.tau.perfdmf.database.DB;

/**
 * Reads a single trial from the database
 *  
 * <P>CVS $Id: DBDataSource.java,v 1.16 2009/09/10 00:25:02 amorris Exp $</P>
 * @author  Robert Bell, Alan Morris
 * @version $Revision: 1.16 $
 */
public class DBDataSource extends DataSource {

    private DatabaseAPI databaseAPI;
    //private volatile boolean abort = false;
    //private volatile int totalItems = 0;
    //private volatile int itemsDone = 0;

    private class XMLParser extends DefaultHandler {
        private StringBuffer accumulator = new StringBuffer();
        private String currentName = "";
        private Thread currentThread;

        public void startElement(String uri, String localName, String qName, Attributes attributes) throws SAXException {
            accumulator = new StringBuffer();
            if (localName.equals("CommonProfileAttributes")) {
                currentThread = null;
            } else if (localName.equals("ProfileAttributes")) {
                int node = Integer.parseInt(attributes.getValue("node"));
                int context = Integer.parseInt(attributes.getValue("context"));
                int threadID = Integer.parseInt(attributes.getValue("thread"));
                currentThread = getThread(node, context, threadID);
            }
        }

        public void endElement(String uri, String localName, String qName) throws SAXException {
            if (localName.equals("name")) {
                currentName = accumulator.toString().trim();
            } else if (localName.equals("value")) {
                String currentValue = accumulator.toString().trim();
                if (currentThread == null) {
                    getMetaData().put(currentName, currentValue);
                } else {
                    currentThread.getMetaData().put(currentName, currentValue);
                    getUncommonMetaData().put(currentName, currentValue);
                }
            }
        }

        public void characters(char[] ch, int start, int length) throws SAXException {
            accumulator.append(ch, start, length);
        }
    }

    public DBDataSource(DatabaseAPI dbAPI) {
        super();
        this.setMetrics(new Vector<Metric>());
        this.databaseAPI = dbAPI;
    }

    public int getProgress() {
        return 0;
        //return DatabaseAPI.getProgress();
    }

    public void cancelLoad() {
        //abort = true;
        return;
    }

    private void fastGetIntervalEventData(Map<Integer, Function> ieMap, Map<Integer, Metric> metricMap) throws SQLException {
        int numMetrics = getNumberOfMetrics();
        DB db = databaseAPI.getDb();

        StringBuffer where = new StringBuffer();

        if (metricMap.size() == 0) {
            return;
        }
            
        where.append(" WHERE p.metric in (");
        for (Iterator<Integer> it = metricMap.keySet().iterator(); it.hasNext();) {
            int metricID = it.next().intValue();
            where.append(metricID);
            if (it.hasNext()) {
                where.append(", ");
            } else {
                where.append(") ");
            }
        }

        // the much slower way
        //        where.append(" WHERE p.interval_event in (");
        //        for (Iterator it = ieMap.keySet().iterator(); it.hasNext();) {
        //            int id = ((Integer) it.next()).intValue();
        //            where.append(id);
        //            if (it.hasNext()) {
        //                where.append(", ");
        //            } else {
        //                where.append(") ");
        //            }
        //        }

        StringBuffer buf = new StringBuffer();
        buf.append("select p.interval_event, p.metric, p.node, p.context, p.thread, ");

        if (db.getDBType().compareTo("oracle") == 0) {
            buf.append("p.inclusive, p.excl, ");
        } else {
            buf.append("p.inclusive, p.exclusive, ");
        }
        if (db.getDBType().compareTo("derby") == 0) {
            buf.append("p.num_calls, ");
        } else {
            buf.append("p.call, ");
        }
        buf.append("p.subroutines ");
        buf.append("from interval_location_profile p ");
        buf.append(where);
        //buf.append(" order by p.interval_event, p.node, p.context, p.thread, p.metric ");
        //System.out.println(buf.toString());

        /*
         1 - interval_event
         2 - metric
         3 - node
         4 - context
         5 - thread
         6 - inclusive
         7 - exclusive
         8 - num_calls
         9 - num_subrs
         */

        // get the results
        long time = System.currentTimeMillis();
        ResultSet resultSet = db.executeQuery(buf.toString());
        time = (System.currentTimeMillis()) - time;
        //System.out.println("Query : " + time);
        //System.out.print(time + ", ");

        time = System.currentTimeMillis();
        while (resultSet.next() != false) {

            int intervalEventID = resultSet.getInt(1);
            Function function = ieMap.get(new Integer(intervalEventID));

            int nodeID = resultSet.getInt(3);
            int contextID = resultSet.getInt(4);
            int threadID = resultSet.getInt(5);

            Thread thread = addThread(nodeID, contextID, threadID);
            FunctionProfile functionProfile = thread.getFunctionProfile(function);

            if (functionProfile == null) {
                functionProfile = new FunctionProfile(function, numMetrics);
                thread.addFunctionProfile(functionProfile);
            }

            int metricIndex = metricMap.get(new Integer(resultSet.getInt(2))).getID();
            double inclusive, exclusive;

            inclusive = resultSet.getDouble(6);
            exclusive = resultSet.getDouble(7);
            double numcalls = resultSet.getDouble(8);
            double numsubr = resultSet.getDouble(9);

            functionProfile.setNumCalls(numcalls);
            functionProfile.setNumSubr(numsubr);
            functionProfile.setExclusive(metricIndex, exclusive);
            functionProfile.setInclusive(metricIndex, inclusive);
        }
        time = (System.currentTimeMillis()) - time;
        //System.out.println("Processing : " + time);
        //System.out.print(time + ", ");

        resultSet.close();
    }

    private void downloadMetaData() {
        try {
            DB db = databaseAPI.getDb();
            StringBuffer joe = new StringBuffer();
            if (db.getDBType().compareTo("sqlite") == 0)
                joe.append("select " + Trial.XML_METADATA);
            else
            	joe.append(" SELECT " + Trial.XML_METADATA_GZ);
            joe.append(" FROM TRIAL WHERE id = ");
            joe.append(databaseAPI.getTrial().getID());
            ResultSet resultSet = db.executeQuery(joe.toString());
            resultSet.next();
            String metaDataString = null;
            if (db.getDBType().compareTo("sqlite") == 0) {
            	metaDataString = resultSet.getString(1);
            } else {
	            InputStream compressedStream = resultSet.getBinaryStream(1);
	            metaDataString = Gzip.decompress(compressedStream);
            }
            if (metaDataString != null) {
                XMLReader xmlreader = XMLReaderFactory.createXMLReader("org.apache.xerces.parsers.SAXParser");
                XMLParser parser = new XMLParser();
                xmlreader.setContentHandler(parser);
                xmlreader.setErrorHandler(parser);
                ByteArrayInputStream input = new ByteArrayInputStream(metaDataString.getBytes());
                xmlreader.parse(new InputSource(input));
            }
        } catch (IOException e) {
            // oh well, no metadata
        } catch (SAXException e) {
            // oh well, no metadata
        } catch (SQLException e) {
            // oh well, no metadata
        }
    }

    public void load() throws SQLException {

        //System.out.println("Processing data, please wait ......");
        long time = System.currentTimeMillis();
        databaseAPI.getTrial().setDataSource(this);
        DB db = databaseAPI.getDb();
        StringBuffer joe = new StringBuffer();
        joe.append("SELECT id, name ");
        joe.append("FROM " + db.getSchemaPrefix() + "metric ");
        joe.append("WHERE trial = ");
        joe.append(databaseAPI.getTrial().getID());
        joe.append(" ORDER BY id ");

        Map<Integer, Metric> metricMap = new HashMap<Integer, Metric>();

        ResultSet resultSet = db.executeQuery(joe.toString());
        int numberOfMetrics = 0;
        while (resultSet.next() != false) {
            int id = resultSet.getInt(1);
            String name = resultSet.getString(2);
            Metric metric = this.addMetricNoCheck(name);
            metric.setDbMetricID(id);
            metricMap.put(new Integer(id), metric);
            numberOfMetrics++;
        }
        resultSet.close();

        // map Interval Event ID's to Function objects
        Map<Integer, Function> ieMap = new HashMap<Integer, Function>();

        // iterate over interval events (functions), create the function objects and add them to the map
        ieMap = databaseAPI.getIntervalEvents(this, numberOfMetrics);

        //getIntervalEventData(ieMap);
        fastGetIntervalEventData(ieMap, metricMap);

        // map Interval Event ID's to Function objects
        databaseAPI.getAtomicEvents();
        databaseAPI.getAtomicEventData(this);

        downloadMetaData();

        databaseAPI.terminate();
        time = (System.currentTimeMillis()) - time;
        //System.out.println("Time to download file (in milliseconds): " + time);
        //System.out.println(time);

        // We actually discard the mean and total values by calling this
        // But, we need to compute other statistics anyway
        generateDerivedData();
    }
}
