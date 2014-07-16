/**
 * 
 */
package edu.uoregon.tau.perfexplorer.glue;

import java.io.Reader;
import java.io.StringReader;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import edu.uoregon.tau.common.MetaDataMap;
import edu.uoregon.tau.common.MetaDataMap.MetaDataKey;
import edu.uoregon.tau.common.MetaDataMap.MetaDataValue;
import edu.uoregon.tau.perfdmf.Trial;
import edu.uoregon.tau.perfdmf.database.DB;
import edu.uoregon.tau.perfexplorer.server.PerfExplorerServer;
import edu.uoregon.tau.perfexplorer.server.TauNamespaceContext;

/**
 * @author khuck
 *
 */
public class TrialMetadata {
	private Hashtable<String,String> commonAttributes = new Hashtable<String,String>();
	private Hashtable<String,Double> accumulator = new Hashtable<String,Double>();
	private Trial trial = null;
	private PerformanceResult performanceResult = null;

	public TrialMetadata (int id) {
		this.trial = PerfExplorerServer.getServer().getSession().setTrial(id,false);
		getMetadata();
	}
	
	public TrialMetadata (Trial trial) {
		this.trial = trial;
		getMetadata();
	}
	
	public TrialMetadata (PerformanceResult input) {
		this.trial = input.getTrial();
		this.performanceResult = input;
		getMetadata();
	}
	
	private void getMetadata() {
		try {
			// get the common attributes
			MetaDataMap metaData = trial.getMetaData();
			Iterator<MetaDataKey> iter = metaData.keySet().iterator();
			while (iter.hasNext()) {
				// we can safely assume that the name is a string
				MetaDataKey key = iter.next();
				MetaDataValue value = metaData.get(key);
				commonAttributes.put(key.name, value.value.toString());
			}
			
			// add the trial name
			commonAttributes.put("Trial.Name", trial.getName());
			
/*
			// get the metadata strings from the trial
			String[] columns = Trial.getFieldNames(PerfExplorerServer.getServer().getDB());
			for (int index = 0 ; (index < columns.length && index < trial.getNumFields()) ; index++) {
				if (columns[index].equalsIgnoreCase("XML_METADATA") || columns[index].equalsIgnoreCase("XML_METADATA_GZ")) {
					continue;
				}
				if (trial.getField(index) == null) {
					commonAttributes.put(columns[index].toLowerCase(), new String(""));
				} else {
					commonAttributes.put(columns[index].toLowerCase(), trial.getField(index));
				}
			}
			
			// build a factory to build the document builder
			DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
			DocumentBuilder builder = factory.newDocumentBuilder();
			
			/// read the XML
			Reader reader = new StringReader(trial.getField(Trial.XML_METADATA));
			InputSource source = new InputSource(reader);
			Document metadata = builder.parse(source);
	
			// this is the 1.5 way 
			// build the xpath object to jump around in that document
			javax.xml.xpath.XPath xpath = javax.xml.xpath.XPathFactory.newInstance().newXPath();
			xpath.setNamespaceContext(new TauNamespaceContext());
	
			// get the profile attributes from the metadata
			NodeList profileAttributes = (NodeList) xpath.evaluate("/metadata/ProfileAttributes", metadata, javax.xml.xpath.XPathConstants.NODESET);

			// iterate through the "uncommon" profile attributes (different for each thread)
			for (int i = 0 ; i < profileAttributes.getLength() ; i++) {
				NodeList children = profileAttributes.item(i).getChildNodes();
				for (int j = 0 ; j < children.getLength(); j++) {
					Node attributeElement = children.item(j);
					Node name = attributeElement.getFirstChild();
					while (name.getFirstChild() == null || name.getFirstChild().getNodeValue() == null) {
						name = name.getNextSibling();
					}
					Node value = name.getNextSibling();
					while (value != null && (value.getFirstChild() == null || value.getFirstChild().getNodeValue() == null)) {
						value = value.getNextSibling();
					}
					if (value == null) { // if there is no value
					} else {
						String tmp = value.getFirstChild().getNodeValue();
						String tmpName = name.getFirstChild().getNodeValue();
						if (tmp != null && tmpName != null && !tmpName.equals("pid") && !tmpName.toLowerCase().contains("time")) {
							try {
								Double tmpDouble = Double.parseDouble(tmp);
								// The metric name is "metadata"
								Double total = accumulator.get(tmpName);
								if (total == null)
									accumulator.put(tmpName, tmpDouble);
								else 
									accumulator.put(tmpName, total + tmpDouble);
							} catch (NumberFormatException e) { 
								commonAttributes.put(tmpName, tmp);
							}
						}
					}
				}
				for (String key : accumulator.keySet()) {
					commonAttributes.put(key, Double.toString(accumulator.get(key) / profileAttributes.getLength()));
				}
			}
*/
			// if false to disable this block
			if (false && this.performanceResult != null) {
				// get the metadata from the CQoS tables!
				DB db = PerfExplorerServer.getServer().getDB();
				StringBuilder sql = new StringBuilder();
				PreparedStatement statement = null;
				
				try {
					// if this table doesn't exist, then an exception will be thrown.
					sql.append("select interval_event, category_name, parameter_name, ");
					sql.append("parameter_type, parameter_value from metadata_parameters ");
					sql.append("where trial = ? order by 1");
					statement = db.prepareStatement(sql.toString());
					
					statement.setInt(1, trial.getID());
					ResultSet results = statement.executeQuery();
					// if the eventID is null, then this metadata field applies to the whole trial.
					while (results.next() != false) {
/*						Integer eventID = results.getInt(1);
						String eventName = null;
						if (eventID != null)
							// if this is phase profile, this will point to a dynamic phase event.
							// the assumption is that the trial has been split by the
							// SplitTrialPhasesOperation already...
							eventName = this.performanceResult.getEventMap().get(eventID);
*/						String eventName = results.getString(1);
//						if (eventID == null || eventName != null) {
						if (eventName == null || 
								(eventName != null && this.performanceResult.getEvents().contains(eventName)) ||
								(eventName != null && this.performanceResult.getEvents().contains(this.performanceResult.getMainEvent() + "  => " + eventName))) {
//							String categoryName = results.getString(2);
							String parameterName = results.getString(3);
//							String parameterType = results.getString(4);
							String parameterValue = results.getString(5);
							commonAttributes.put(parameterName, parameterValue);
//							if (eventName==null)
//								System.out.println(eventName+":"+parameterName+"="+parameterValue);
						}
					}
					results.close();
					statement.close();
				} catch (SQLException sqle) {
					// This table may not exist, so ignore the exception.
					// System.err.println(sqle.getMessage());
					// sqle.printStackTrace();
				}
			}
		} catch (Exception e) {
			System.err.println(e.getMessage());
			e.printStackTrace();
		}
	}

	/**
	 * @return the commonAttributes
	 */
	public Hashtable<String, String> getCommonAttributes() {
		return commonAttributes;
	}

	/**
	 * @param commonAttributes the commonAttributes to set
	 */
	public void setCommonAttributes(Hashtable<String, String> commonAttributes) {
		this.commonAttributes = commonAttributes;
	}

	/**
	 * @return the trial
	 */
	public Trial getTrial() {
		return trial;
	}

	/**
	 * @param trial the trial to set
	 */
	public void setTrial(Trial trial) {
		this.trial = trial;
	}
	
	public String toString() {
		StringBuilder buf = new StringBuilder();
		Set<String> keys = this.commonAttributes.keySet();
		for (String key : keys) {
			buf.append(key + ": " + this.commonAttributes.get(key) + "\n");
		}
		return buf.toString();
	}
	
}
