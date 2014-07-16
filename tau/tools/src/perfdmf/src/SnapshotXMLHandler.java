package edu.uoregon.tau.perfdmf;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringTokenizer;

import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;
import org.xml.sax.helpers.DefaultHandler;

/**
 * XML Handler for snapshot profiles, this is where all the work is done
 *
 * <P>CVS $Id: SnapshotXMLHandler.java,v 1.15 2010/04/22 21:49:37 amorris Exp $</P>
 * @author  Alan Morris
 * @version $Revision: 1.15 $
 */
public class SnapshotXMLHandler extends DefaultHandler {

    private SnapshotDataSource dataSource;
    
    //private static final String[] DERIVED_TYPES={"total","mean_all","mean_no_null","stddev_all","stddev_no_null"};
    private static final String TNR=" t\n\r";

    private Map<String, ThreadData> threadMap = new HashMap<String, ThreadData>();
   // private Map<String, ThreadData> entityMap = new HashMap<String, ThreadData>();

    private ThreadData currentThread;
    private Snapshot currentSnapshot;
    //private Date currentDate;

    private int currentMetrics[];

    private StringBuffer accumulator = new StringBuffer();

    private int currentId;
    private String currentName;
    private String currentValue;
    private String currentGroup;
    private long currentTimestamp;
    
    private boolean unified;
    private ThreadData unifiedDefinitions;

    private static class ThreadData {
        public Thread thread;
        public List<Metric> metricMap = new ArrayList<Metric>();
        public List<Function> eventMap = new ArrayList<Function>();
        public List<UserEvent> userEventMap = new ArrayList<UserEvent>();
    }

    public SnapshotXMLHandler(SnapshotDataSource source) {
        this.dataSource = source;
    }

    public void warning(SAXParseException e) throws SAXException {}

    public void error(SAXParseException e) throws SAXException {}

    public void fatalError(SAXParseException e) throws SAXException {
        throw e;
    }

    public void startDocument() throws SAXException {}

    public void endDocument() throws SAXException {}

    private void handleMetric(String name) {
        Metric metric = dataSource.addMetric(name);
        
        while (currentId >= currentThread.metricMap.size()) {
            currentThread.metricMap.add(null);
        }
        currentThread.metricMap.set(currentId, metric);
    }

    private void handleEvent(String name, String groups) {
        int id = currentId;

        Function function = dataSource.addFunction(name);
        dataSource.addGroups(groups, function);
        
        while (id >= currentThread.eventMap.size()) {
            currentThread.eventMap.add(null);
        }
        currentThread.eventMap.set(id, function);
    }

    private void handleUserEvent(String name) {
        int id = currentId;
        UserEvent userEvent = dataSource.addUserEvent(name);
        while (id >= currentThread.userEventMap.size()) {
            currentThread.userEventMap.add(null);
        }
        currentThread.userEventMap.set(id, userEvent);
    }

    private void handleThread(Attributes attributes) {
        String threadName = attributes.getValue(ID);
        int nodeID = Integer.parseInt(attributes.getValue("node"));
        int contextID = Integer.parseInt(attributes.getValue("context"));
        int threadID = Integer.parseInt(attributes.getValue("thread"));

        ThreadData data = new ThreadData();
        if (unified) {
            data.eventMap = unifiedDefinitions.eventMap;
            data.userEventMap = unifiedDefinitions.userEventMap;
            data.metricMap = unifiedDefinitions.metricMap;//TODO: Make sure this works with the older versions
        }
        data.thread = dataSource.addThread(nodeID, contextID, threadID);
        threadMap.put(threadName, data);
        currentThread = data;
    }

    private boolean mSet=false;
    private boolean mNNSet=false;
    private boolean tSet=false;
    private boolean sDSet=false;
    private boolean sDNNSet=false;
    private boolean unknownDerivedProfile=false;
    private void handleDerivedEntity(Attributes attributes){
    	String entityName = attributes.getValue(ID);
    	if(entityName.equals("mean_all")){
    		ThreadData data = new ThreadData();
    		//It is unified so:
    		{
    			data.eventMap = unifiedDefinitions.eventMap;
                data.userEventMap = unifiedDefinitions.userEventMap;
                data.metricMap = unifiedDefinitions.metricMap;
    		}
    		data.thread = dataSource.meanDataAll = new Thread(-6, -6, -6, dataSource.getNumberOfMetrics(), dataSource); //dataSource.addThread(-1, -1, -1);
            threadMap.put(entityName, data);
            currentThread = data;
            mSet=true;
    	}
    	else if(entityName.equals("mean_no_null")){
    		ThreadData data = new ThreadData();
    		//It is unified so:
    		{
    			data.eventMap = unifiedDefinitions.eventMap;
                data.userEventMap = unifiedDefinitions.userEventMap;
                data.metricMap = unifiedDefinitions.metricMap;
    		}
    		data.thread = dataSource.meanDataNoNull = new Thread(-1, -1, -1, dataSource.getNumberOfMetrics(), dataSource); //dataSource.addThread(-1, -1, -1);
            threadMap.put(entityName, data);
            currentThread = data;
            mNNSet=true;
    	}
    	else
    	if(entityName.equals("total")){
    		ThreadData data = new ThreadData();
    		//It is unified so:
    		{
    			data.eventMap = unifiedDefinitions.eventMap;
                data.userEventMap = unifiedDefinitions.userEventMap;
                data.metricMap = unifiedDefinitions.metricMap;
    		}
    		data.thread = dataSource.totalData = new Thread(-2, -2, -2, dataSource.getNumberOfMetrics(), dataSource); //dataSource.addThread(-2, -2, -2);
            threadMap.put(entityName, data);
            currentThread = data;
            tSet=true;
    	}
    	else
        	if(entityName.equals("stddev_all")){
        		ThreadData data = new ThreadData();
        		//It is unified so:
        		{
        			data.eventMap = unifiedDefinitions.eventMap;
                    data.userEventMap = unifiedDefinitions.userEventMap;
                    data.metricMap = unifiedDefinitions.metricMap;
        		}
        		data.thread = dataSource.stddevDataAll = new Thread(-7, -7, -7, dataSource.getNumberOfMetrics(), dataSource); //dataSource.addThread(-3, -3, -3);
                threadMap.put(entityName, data);
                currentThread = data;
                sDSet=true;
        	}
        	else
            	if(entityName.equals("stddev_no_null")){
            		ThreadData data = new ThreadData();
            		//It is unified so:
            		{
            			data.eventMap = unifiedDefinitions.eventMap;
                        data.userEventMap = unifiedDefinitions.userEventMap;
                        data.metricMap = unifiedDefinitions.metricMap;
            		}
            		data.thread = dataSource.stddevDataNoNull = new Thread(-3, -3, -3, dataSource.getNumberOfMetrics(), dataSource); //dataSource.addThread(-3, -3, -3);
                    threadMap.put(entityName, data);
                    currentThread = data;
                    sDNNSet=true;
            	}
            	else
                	if(entityName.equals("min_no_null")){
                		ThreadData data = new ThreadData();
                		//It is unified so:
                		{
                			data.eventMap = unifiedDefinitions.eventMap;
                            data.userEventMap = unifiedDefinitions.userEventMap;
                            data.metricMap = unifiedDefinitions.metricMap;
                		}
                		data.thread = dataSource.minData = new Thread(-4, -4, -4, dataSource.getNumberOfMetrics(), dataSource); //dataSource.addThread(-3, -3, -3);
                        threadMap.put(entityName, data);
                        currentThread = data;
                        sDNNSet=true;
                	}
    	else
    	if(entityName.equals("max_no_null")){
    		ThreadData data = new ThreadData();
    		//It is unified so:
    		{
    			data.eventMap = unifiedDefinitions.eventMap;
                data.userEventMap = unifiedDefinitions.userEventMap;
                data.metricMap = unifiedDefinitions.metricMap;
    		}
    		data.thread = dataSource.maxData = new Thread(-5, -5, -5, dataSource.getNumberOfMetrics(), dataSource); //dataSource.addThread(-3, -3, -3);
            threadMap.put(entityName, data);
            currentThread = data;
            sDNNSet=true;
    	}
//            	else{
//            		unknownDerivedEntity=true;
//            	}
    	if(mSet&&tSet&&sDSet&&sDNNSet&&mNNSet)
    		dataSource.derivedProvided=true;
    }
    
    
    private void handleDefinitions(Attributes attributes) {
        String threadID = attributes.getValue("thread");
        if (threadID.equals("*")) {
	    //            System.out.println("Unified format found!");
            unified = true;
            unifiedDefinitions = new ThreadData();
            currentThread = unifiedDefinitions;
        } else {
            currentThread = threadMap.get(threadID);
        }
    }

    private void handleProfile(Attributes attributes) {
        String threadID = attributes.getValue("thread");
        currentThread = threadMap.get(threadID);
        currentSnapshot = currentThread.thread.addSnapshot("");
    }
    
    private void handleDerivedProfile(Attributes attributes) {
        String threadID = attributes.getValue(DERIVEDENTITY);
        currentThread = threadMap.get(threadID);
        if(currentThread==null)
        {
        	unknownDerivedProfile=true;
        	return;
        }
        currentSnapshot = currentThread.thread.addSnapshot("");
    }

    private void handleIntervalData(Attributes attributes) {
        String metrics = attributes.getValue("metrics");

        StringTokenizer tokenizer = new StringTokenizer(metrics, TNR);

        currentMetrics = new int[tokenizer.countTokens()];
        int index = 0;
        while (tokenizer.hasMoreTokens()) {
            int metricID = Integer.parseInt(tokenizer.nextToken());
            currentMetrics[index++] = metricID;
        }
    }

    private void handleAtomicDataEnd() {
        String data = accumulator.toString();

        StringTokenizer tokenizer = new StringTokenizer(data, TNR);

        while (tokenizer.hasMoreTokens()) {
            int eventID = Integer.parseInt(tokenizer.nextToken());
            if(eventID<0||eventID>currentThread.userEventMap.size()-1)
            {	
            	System.out.println("Skipping undefined atomic event, id# "+eventID);
            	return;
            }
            UserEvent userEvent = currentThread.userEventMap.get(eventID);

            UserEventProfile uep = currentThread.thread.getUserEventProfile(userEvent);
            if (uep == null) {
                uep = new UserEventProfile(userEvent, currentThread.thread.getSnapshots().size());
                currentThread.thread.addUserEventProfile(uep);
            }

            double numSamples = Double.parseDouble(tokenizer.nextToken());
            double max = Double.parseDouble(tokenizer.nextToken());
            double min = Double.parseDouble(tokenizer.nextToken());
            double mean = Double.parseDouble(tokenizer.nextToken());
            double sumSqr = Double.parseDouble(tokenizer.nextToken());
            uep.setNumSamples(numSamples);
            uep.setMaxValue(max);
            uep.setMinValue(min);
            uep.setMeanValue(mean);
            uep.setSumSquared(sumSqr);
        }
    }

    private void handleIntervalDataEnd() {
        String data = accumulator.toString();

        StringTokenizer tokenizer = new StringTokenizer(data, TNR);

        while (tokenizer.hasMoreTokens()) {
            int eventID = Integer.parseInt(tokenizer.nextToken());
            
            if(eventID<0||eventID>currentThread.eventMap.size()-1){
            	System.out.println("Skipping undefined interval event, id# "+eventID);
            	return;
            }

            Function function = currentThread.eventMap.get(eventID);

            FunctionProfile fp = currentThread.thread.getFunctionProfile(function);
            if (fp == null) {
                fp = new FunctionProfile(function, dataSource.getNumberOfMetrics(), currentThread.thread.getSnapshots().size());
                currentThread.thread.addFunctionProfile(fp);
            }

            double numcalls = Double.parseDouble(tokenizer.nextToken());
            double numsubr = Double.parseDouble(tokenizer.nextToken());

            for (int i = 0; i < currentMetrics.length; i++) {
                int metricID = currentMetrics[i];
                Metric metric = currentThread.metricMap.get(metricID);
                double exclusive = Double.parseDouble(tokenizer.nextToken());
                double inclusive = Double.parseDouble(tokenizer.nextToken());
                fp.setExclusive(metric.getID(), exclusive);
                fp.setInclusive(metric.getID(), inclusive);
            }

            fp.setNumCalls(numcalls);
            fp.setNumSubr(numsubr);
        }
    }
    
    
    private static final String THREAD="thread";
    private static final String ID="id";
    private static final String DERIVEDENTITY="derivedentity";
    private static final String DERIVEDPROFILE="derivedprofile";

    public void startElement(String uri, String localName, String qName, Attributes attributes) throws SAXException {
    	if(unknownDerivedProfile){
        	return;
        }
    	
        //System.out.println("startElement: uri:" + uri + ", localName:"+localName+", qName:"+qName);

        if (localName.equals(THREAD)) {
            handleThread(attributes);
        } else if (localName.equals("name")) {
            accumulator = new StringBuffer();
        } else if (localName.equals("value")) {
            accumulator = new StringBuffer();
        } else if (localName.equals("group")) {
            accumulator = new StringBuffer();
        } else if (localName.equals("utc_date")) {
            accumulator = new StringBuffer();
        } else if (localName.equals("timestamp")) {
            accumulator = new StringBuffer();
        } else if (localName.equals("definitions")) {
            handleDefinitions(attributes);
        } else if (localName.equals("metric")) {
            currentId = Integer.parseInt(attributes.getValue(ID));
        } else if (localName.equals("event")) {
            currentId = Integer.parseInt(attributes.getValue(ID));
        } else if (localName.equals("userevent")) {
            currentId = Integer.parseInt(attributes.getValue(ID));
        } else if (localName.equals("profile")) {
            handleProfile(attributes);
        } else if (localName.equals("interval_data")||localName.equals("derivedinterval_data")) {
            handleIntervalData(attributes);
            accumulator = new StringBuffer();
        } else if (localName.equals("atomic_data")||localName.equals("derivedatomic_data")) {
            accumulator = new StringBuffer();
        } else if(localName.equals(DERIVEDENTITY)){
        	handleDerivedEntity(attributes);
        }else if(localName.equals(DERIVEDPROFILE)){
        	handleDerivedProfile(attributes);
        }

    }

    public void endElement(String uri, String localName, String qName) throws SAXException {
    	
    	
        if(unknownDerivedProfile){
        	if(localName.equals(DERIVEDPROFILE)){
        		unknownDerivedProfile=false;
        	}
        	return;
        }
    	
        //System.out.println("endElement: uri:" + uri + ", localName:"+localName+", qName:"+qName);
        if (localName.equals("thread_definition")) {
            currentThread = null;
        } else if (localName.equals("name")) {
            currentName = accumulator.toString();
        } else if (localName.equals("value")) {
            currentValue = accumulator.toString();
        } else if (localName.equals("utc_date")) {
            try {
                //currentDate = 
                	DataSource.dateTime.parse(accumulator.toString());
            } catch (java.text.ParseException e) {}
        } else if (localName.equals("timestamp")) {
            currentTimestamp = Long.parseLong(accumulator.toString());
        } else if (localName.equals("group")) {
            currentGroup = accumulator.toString();
        } else if (localName.equals("profile")) {
            currentSnapshot.setName(currentName);
            currentSnapshot.setTimestamp(currentTimestamp);
        } else if (localName.equals("metric")) {
            handleMetric(currentName);
        } else if (localName.equals("event")) {
            handleEvent(currentName, currentGroup);
        } else if (localName.equals("userevent")) {
            handleUserEvent(currentName);
        } else if (localName.equals("attribute")) {
            currentThread.thread.getMetaData().put(currentName, currentValue);
        } else if (localName.equals("interval_data")||localName.equals("derivedinterval_data")) {
            handleIntervalDataEnd();
        } else if (localName.equals("atomic_data")) {
            handleAtomicDataEnd();
        }
        else if (localName.equals("derivedatomic_data")){
        	handleAtomicDataEnd();
        	dataSource.derivedAtomicProvided=true;
        }

    }

    public void characters(char[] ch, int start, int length) throws SAXException {
        accumulator.append(ch, start, length);
    }
}
