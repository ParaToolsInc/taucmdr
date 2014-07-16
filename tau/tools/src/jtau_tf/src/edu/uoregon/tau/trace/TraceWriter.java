/*
 *  See TAU License file
 */

/*
 * @author  Wyatt Spear
 */

package edu.uoregon.tau.trace;

import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.DataOutputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
//import java.util.HashSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;
//import java.util.Vector;
import java.util.TreeMap;

public class TraceWriter extends TraceFile {
	
	DataOutputStream Foid;//The trace file output handle
	
	/* -- pcxx tracer events ------------------- */
	private final static int PCXX_EV_INIT = 60000;
	//int PCXX_EV_FLUSH_ENTER = 60001;
	//int PCXX_EV_FLUSH_EXIT  = 60002;
	private final static int PCXX_EV_CLOSE = 60003;
	//int PCXX_EV_INITM       = 60004;
	private final static int PCXX_EV_WALL_CLOCK = 60005;
	//int PCXX_EV_CONT_EVENT  = 60006;
	private final static int TAU_MESSAGE_SEND	= 60007;
	private final static int TAU_MESSAGE_RECV	= 60008;

	        /* -- the following two events are only the ----- */
	        /* -- base numbers, actually both represent ----- */
	        /* -- 64 events (60[1234]00 to 60[1234]64)  ----- */
	//int PCXX_WTIMER_CLEAR = 60199;
	//int PCXX_WTIMER_START = 60100;
	//int PCXX_WTIMER_STOP  = 60200;
	//int PCXX_UTIMER_CLEAR = 60399;
	//int PCXX_UTIMER_START = 60300;
	//int PCXX_UTIMER_STOP  = 60400;
	
	//private static final int TAU_MAX_RECORDS = 64*1024;
	
	private HashSet<Integer> checkInit = new HashSet<Integer>();
	private HashMap<Integer, String> nidTidNames = new HashMap<Integer, String>();
	long lastTimestamp;
	//boolean needsEdfFlush;
	
	//Event[] traceBuffer;
	//int tracePosition;
	
	public TraceWriter( String name, String edf){
		
		FileOutputStream ostream;
		try {
			ostream = new FileOutputStream(name);

		BufferedOutputStream bw = new BufferedOutputStream(ostream);
		Foid = new DataOutputStream(bw);
		//tFile.traceBuffer = new Event[TAU_MAX_RECORDS];
		//tFile.traceBuffer[0]=new Event();
		//tFile.tracePosition = 0; // 0 will be the EV_INIT record
		//tFile.initialized = false;

		


		BufferedWriter out = new BufferedWriter(new FileWriter(edf));
		out.close();

		/* make a copy of the EDF file name */
		EdfFile = edf;

		//tFile.NidTidMap = new HashMap();

		/* Allocate space for maps */
		EventIdMap = new TreeMap<Integer, EventDescr>();//Tree map for output ordered by id.

		IdGroupMap = new HashMap<Integer, String>();

		//tFile.groupNameMap = new HashMap();

		//tFile.needsEdfFlush = true;

		/* initialize clock */
		//tFile.ClkInitialized = false;
		
		/* initialize the first timestamp for the trace */
		//tFile.FirstTimestamp = 0;

		/* define some events */

		EventDescr newEventDesc = new EventDescr(PCXX_EV_INIT,"TRACER","EV_INIT",0,"none");
		/*newEventDesc.Eid = PCXX_EV_INIT;
		newEventDesc.Group = "TRACER";
		newEventDesc.EventName = "EV_INIT";
		newEventDesc.Tag = 0;
		newEventDesc.Param = "none";*/
		EventIdMap.put(new Integer(PCXX_EV_INIT),newEventDesc);//[PCXX_EV_INIT] = newEventDesc;
		
		newEventDesc = new EventDescr(PCXX_EV_CLOSE,"TRACER","FLUSH_CLOSE",0,"none");
		/*newEventDesc.Eid = PCXX_EV_CLOSE;
		newEventDesc.Group = "TRACER";
		newEventDesc.EventName = "FLUSH_CLOSE";
		newEventDesc.Tag = 0;
		newEventDesc.Param = "none";*/
		EventIdMap.put(new Integer(PCXX_EV_CLOSE),newEventDesc);//[PCXX_EV_CLOSE] = newEventDesc;
		
		newEventDesc = new EventDescr(PCXX_EV_WALL_CLOCK,"TRACER","WALL_CLOCK",0,"none");
		/*newEventDesc.Eid = PCXX_EV_WALL_CLOCK;
		newEventDesc.Group = "TRACER";
		newEventDesc.EventName = "WALL_CLOCK";
		newEventDesc.Tag = 0;
		newEventDesc.Param = "none";*/
		EventIdMap.put(new Integer(PCXX_EV_WALL_CLOCK),newEventDesc);//[PCXX_EV_WALL_CLOCK] = newEventDesc;
		
		newEventDesc = new EventDescr(TAU_MESSAGE_SEND,"TAU_MESSAGE","MESSAGE_SEND",-7,"par");
		/*newEventDesc.Eid = TAU_MESSAGE_SEND;
		newEventDesc.Group = "TAU_MESSAGE";
		newEventDesc.EventName = "MESSAGE_SEND";
		newEventDesc.Tag = -7;
		newEventDesc.Param = "par";*/
		
		EventIdMap.put(new Integer(TAU_MESSAGE_SEND),newEventDesc);//[TAU_MESSAGE_SEND] = newEventDesc;
		newEventDesc = new EventDescr(TAU_MESSAGE_RECV,"TAU_MESSAGE","MESSAGE_RECV",-8,"par");
		/*newEventDesc.Eid = TAU_MESSAGE_RECV;
		newEventDesc.Group = "TAU_MESSAGE";
		newEventDesc.EventName = "MESSAGE_RECV";
		newEventDesc.Tag = -8;
		newEventDesc.Param = "par";*/
		EventIdMap.put(new Integer(TAU_MESSAGE_RECV),newEventDesc);//[TAU_MESSAGE_RECV] = newEventDesc;

		} catch (SecurityException e1) {
			e1.printStackTrace();
		} catch (FileNotFoundException e1) {
			e1.printStackTrace();
	    } catch (IOException e1) {
	    	e1.printStackTrace();
		}	
		
	}
	
	/*private String StringPair(int nod,int thd){
		return nod+":"+thd;
	}*/
	
	private int CharPair(int nid, int tid){
		//System.out.println("n: "+nid+ " t: "+tid);
		return (nid << 16)+tid;
	}
	
	/*private void checkFlush() {
		// Write the current trace buffer to file if necessary.
		if (tracePosition >= TAU_MAX_RECORDS) {
			flushTrace();
		}
	}*/

	private int flushEdf() {
		try {
			BufferedWriter out = new BufferedWriter(new FileWriter(EdfFile));

			int numEvents = EventIdMap.size();
			out.write(numEvents+" dynamic_trace_events\n");
			out.write("# FunctionId Group Tag \"Name Type\" Parameters\n");
			Iterator<EventDescr> it = EventIdMap.values().iterator(); //entrySet().iterator();
			int id;
			EventDescr eventDesc;
			while(it.hasNext())
			{
				eventDesc=it.next();
				id = eventDesc.getEventId();
				out.write(id+" "+eventDesc.getGroup()+" "+eventDesc.getTag()+" \""+eventDesc.getEventName()+"\" "+eventDesc.getParameter()+"\n");
			}
			out.close();
		} catch (IOException e) {
			System.out.println("Error opening edf file");
			return -1;
	    }

		//needsEdfFlush = false;
		return 0;
	}
/*
	private int checkInitialized(int nodeToken, int threadToken, long time) {
		// Adds the initialization record
		if (!initialized) {
			
			traceBuffer[tracePosition].setEventID(PCXX_EV_INIT);
			traceBuffer[tracePosition].setNodeID((char)nodeToken);
			traceBuffer[tracePosition].setThreadID((char)threadToken);
			traceBuffer[tracePosition].setTime(time);//(x_uint64)
			traceBuffer[tracePosition].setParameter(3);
			initialized = true;
		}
		return 0;
	}*/

	public int defThread(int nodeToken, int threadToken,String threadName) {
		//char nid = (char)nodeToken;//Integer ..  new Integer(nodeToken);
		//char tid = (char)threadToken;
		Integer nidtid=new Integer(CharPair(nodeToken,threadToken));
		//TODO: Use the thread name somehow?!
		if(!nidTidNames.containsKey(nidtid))
		{
			nidTidNames.put(nidtid, threadName);
		}
	    return 0;
	  }

	  // returns stateGroupToken
	public int defStateGroup(String stateGroupName, int stateGroupToken) {
		IdGroupMap.put(new Integer(stateGroupToken),stateGroupName);
		return 0;
	}

	public int defState(int stateToken, String stateName, int stateGroupToken){
		
		if(!IdGroupMap.containsKey(new Integer(stateGroupToken))){
			//throw new Exception("Ttf_DefState: Have not seen"+stateGroupToken+"stateGroupToken before, please define it first\n");
			return -1;
		}

		EventDescr newEventDesc = new EventDescr(stateToken,IdGroupMap.get(new Integer(stateGroupToken)),stateName,0,"EntryExit");
		/*newEventDesc.Eid = stateToken;
		newEventDesc.Group = (String)groupNameMap.get(new Integer(stateGroupToken));
		newEventDesc.EventName = stateName;
		newEventDesc.Tag = 0;
		newEventDesc.Param = "EntryExit";*/

		EventIdMap.put(new Integer(stateToken),newEventDesc);

		//needsEdfFlush = true;

		return 0;
	}

	public int writeEvent(int eventID, char nodeID, char threadID, long parameter, long time){
		
		try {
			//nidtid=CharPair(subject.getNodeID(),subject.getThreadID());
			if(checkInit.add(new Integer(CharPair(nodeID,threadID))))
			{
				//checkInit.add(nidtid);
				Foid.writeInt(PCXX_EV_INIT);
				Foid.writeChar(nodeID);
				Foid.writeChar(threadID);
				Foid.writeLong(3);
				Foid.writeLong(time);
			}

    		//evt=tFile.traceBuffer[i];
			Foid.writeInt(eventID);
			Foid.writeChar(nodeID);
			Foid.writeChar(threadID);
			Foid.writeLong(parameter);
			Foid.writeLong(time);
    	} catch (IOException e) {
			e.printStackTrace();
		}
    	
    	return 0;
	}
	
	/*public int flushTrace(){
		int events = tracePosition;
		//if(events>1)
		//	checkInitialized(traceBuffer[1].getNodeID(),traceBuffer[1].getThreadID(), traceBuffer[1].getTime());
		//else
		//	checkInitialized(0,0,0);
		// reset trace position
		tracePosition = 0;
		// must write out edf file first
		if (needsEdfFlush) {
			if (flushEdf() != 0) {
				return -1;
			}
		}

		//Event evt;
		Event subject=null;
		//boolean needInit = false;
		//CharPair 
		//String nidtid=null;
		for(int i=0; i<events;i++)
		{
			subject=traceBuffer[i];
			try {
				//nidtid=CharPair(subject.getNodeID(),subject.getThreadID());
				if(checkInit.add(new Integer(CharPair(subject.getNodeID(),subject.getThreadID()))))
				{
					//checkInit.add(nidtid);
					Foid.writeInt(PCXX_EV_INIT);
					Foid.writeChar(subject.getNodeID());
					Foid.writeChar(subject.getThreadID());
					Foid.writeLong(3);
					Foid.writeLong(subject.getTime());
				}

	    		//evt=tFile.traceBuffer[i];
				Foid.writeInt(subject.getEventID());
				Foid.writeChar(subject.getNodeID());
				Foid.writeChar(subject.getThreadID());
				Foid.writeLong(subject.getParameter());
				Foid.writeLong(subject.getTime());
	    	} catch (IOException e) {
				e.printStackTrace();
			}
	    }
	    return 0;
	  }*/

	public int closeTrace(){
		Set<Integer> keyset = nidTidNames.keySet();// .iterator();
		Iterator<Integer> it=keyset.iterator();
		int nidtid;
		char first;
		char second;
		while(it.hasNext())
		{
			nidtid=it.next().intValue();
			//System.out.println(nidtid.first().getClass().getSimpleName());
			first=(char)(nidtid>>>16);//  (char)Integer.parseInt(nidtid.substring(0, nidtid.indexOf(':'))); //first();//(((Integer)nidtid.first()).intValue());
			second=(char)nidtid;//(char)Integer.parseInt(nidtid.substring(nidtid.indexOf(':')+1));//nidtid.second();//(((Integer)nidtid.second()).intValue());
			//checkFlush();
			//int pos = tracePosition;
			writeEvent(PCXX_EV_CLOSE, first, second, 0, lastTimestamp);//char
			/*evt.ev = PCXX_EV_CLOSE;
			evt.nid = (char)first;
			evt.tid = (char)second;
			evt.ti = lastTimestamp;
			evt.par = 0;*/
			//traceBuffer[pos]=(evt);//pos,
			//tracePosition++;
	      
			//pos = tracePosition;
			writeEvent(PCXX_EV_WALL_CLOCK, first, second, 0, lastTimestamp);//char
			/*evt.ev = PCXX_EV_WALL_CLOCK;
			evt.nid = (char)first;
			evt.tid = (char)second;
			evt.ti = lastTimestamp;
			evt.par = 0;*/
			//traceBuffer[pos]=evt;//pos,
			//tracePosition++;
		}
		//flushTrace();
		flushEdf();
		try {
			Foid.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
		return 0;
	}

	private int enterExit(long time, 
			int nodeToken, int threadToken, 
			int stateToken, int parameter) {//time formerly (x_uint64)
		//Ttf_fileT *tFile = (Ttf_fileT*)file;

		//checkFlush();
		//int pos = tracePosition;
		//System.out.println(pos);
		writeEvent(stateToken,(char)nodeToken,(char)threadToken,parameter,time);
		/*evt.ev = stateToken;
		evt.nid = (char)nodeToken;
		evt.tid = (char)threadToken;
		evt.ti = time;
		evt.par = parameter;*/
		//traceBuffer[pos]=evt;//pos,
		//tracePosition++;
		lastTimestamp = time;
		return 0;
	}

	public int enterState(long time, 
			int nodeToken, int threadToken, 
			int stateToken) {//time formerly (x_uint64)
		return enterExit(time, nodeToken, threadToken, stateToken, 1); // entry
	}

	public int leaveState(long time, 
			int nodeToken, int threadToken, int stateToken) {//time formerly (x_uint64)
		return enterExit(time, nodeToken, threadToken, stateToken, -1); // exit
	}

	public int defClkPeriod(double clkPeriod) {
		return 0;
	}

	private int sendRecv(long time, int sourceNodeToken,
			int sourceThreadToken,
			int destinationNodeToken,
			int destinationThreadToken,
			int messageSize,
			int messageTag,
			int messageComm, int eventId) {
		long parameter;
		long xother, xtype, xlength, xcomm;
	    xother = destinationNodeToken;
	    xtype = messageTag;
	    xlength = messageSize;
	    xcomm = messageComm;

		parameter = (xlength >> 16 << 54 >> 22) |
		((xtype >> 8 & 0xFF) << 48) |
		((xother >> 8 & 0xFF) << 56) |
		(xlength & 0xFFFF) | 
		((xtype & 0xFF)  << 16) | 
		((xother & 0xFF) << 24) |
		(xcomm << 58 >> 16);

		//checkFlush();
		//int pos = tracePosition;
		writeEvent(eventId,(char)sourceNodeToken,(char)sourceThreadToken,parameter,time);
		/*evt.ev = eventId;
		evt.nid = (char)sourceNodeToken;
		evt.tid = (char)sourceThreadToken;
		evt.ti = time;
		evt.par = parameter;*/
		//traceBuffer[pos]=evt;//pos,
		//tracePosition++;
		lastTimestamp = time;

		return 0;
	}

	public int sendMessage(long time, int sourceNodeToken,
			int sourceThreadToken,
			int destinationNodeToken,
			int destinationThreadToken,
			int messageSize,
			int messageTag,
			int messageComm) {
	return sendRecv(time, sourceNodeToken, sourceThreadToken, destinationNodeToken, 
			destinationThreadToken, messageSize, messageTag, messageComm, TAU_MESSAGE_SEND);
		//return 0;
	}

	public int recvMessage(long time, int sourceNodeToken,
			int sourceThreadToken,
			int destinationNodeToken,
			int destinationThreadToken,
			int messageSize,
			int messageTag,
			int messageComm) {
		return sendRecv(time, destinationNodeToken, 
				destinationThreadToken, sourceNodeToken, sourceThreadToken, 
				messageSize, messageTag, messageComm, TAU_MESSAGE_RECV);
		//return 0;
	}

	public int defUserEvent(int userEventToken,String userEventName, int monotonicallyIncreasing) {
		EventDescr newEventDesc=new EventDescr(userEventToken,"TAUEVENT",userEventName,monotonicallyIncreasing,"TriggerValue");
		/*newEventDesc.Eid = userEventToken;
		newEventDesc.Group = "TAUEVENT";
		newEventDesc.EventName = userEventName;
		newEventDesc.Tag = monotonicallyIncreasing;
		newEventDesc.Param = "TriggerValue";*/

		EventIdMap.put(new Integer(userEventToken),newEventDesc);

		//needsEdfFlush = true;
		return 0;
	}

	public int eventTrigger(long time, 
			int nodeToken,
			int threadToken,
			int userEventToken,
			long userEventValue) {
		//checkFlush();
		//int pos = tracePosition;
		writeEvent(userEventToken,(char)nodeToken,(char)threadToken,userEventValue,time);
		/*evt.ev = userEventToken;
		evt.nid = (char)nodeToken;
		evt.tid = (char)threadToken;
		evt.ti = time;
		evt.par = userEventValue;*/
		//traceBuffer[pos]=evt;//pos,
		//tracePosition++;
		lastTimestamp = time;
		return 0;
	}
}

