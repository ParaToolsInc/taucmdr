package edu.uoregon.tau.perfdmf;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

public class GoogleDataSource extends DataSource {

    //    private int indexStart = 0;
    //    private int percentStart = 0;
    //    private int selfStart = 0;
    //    private int descendantsStart = 0;
    //    private int calledStart = 0;
    //    private int nameStart = 0;
    private int linenumber = 0;
    //private boolean fixLengths = true;

    //private String currentFile;
    public static void main(String[] args){
	String prefix = "/Users/somillstein/Desktop/irs_benchmark_code_google_perftools_output/irs_cpuprofile_0000";
	String suffix = ".out.txt";
	File[] files = new File[8];
	for(int i=0; i<8;i++){
	    files[i] = new File(prefix+i+suffix);
	}
	GoogleDataSource ds = new GoogleDataSource(files);
	try {
	    ds.load();
	} catch (FileNotFoundException e) {
	    // TODO Auto-generated catch block
	    e.printStackTrace();
	} catch (IOException e) {
	    // TODO Auto-generated catch block
	    e.printStackTrace();
	}
    }

    public GoogleDataSource(File[] files) {
	super();
	if(files ==null ){
	    this.files = findTxtFiles();
	}else{ 
	    if(files.length ==0)
		this.files = findTxtFiles();
	    else
		this.files = files;
	}
    }

    private File[] findTxtFiles() {
	  //Look in the current directory of *.txt files.
	    String currentdir = System.getProperty("user.dir");	
	    File dir = new File(currentdir);
	    String[] fileName = dir.list();
	    ArrayList<File> filelist = new ArrayList<File>();
	    for(String file: fileName){
		if(file.endsWith(".txt")){
		    filelist.add(new File(file));
		}
	    }
	    File[] files= new File[filelist.size()];
	    return  (File[]) filelist.toArray(files);
    }

    private File files[];

    public void cancelLoad() {
	return;
    }

    public int getProgress() {
	return 0;
    }

    public void load() throws FileNotFoundException, IOException {
	//Record time.
	long time = System.currentTimeMillis();

	//######
	//Frequently used items.
	//######
	Function function = null;
	FunctionProfile functionProfile = null;

	Node node = null;
	Context context = null;
	edu.uoregon.tau.perfdmf.Thread thread = null;
	int nodeID = -1;

	String inputString = null;

	//Function callPathFunction = null;

	//######
	//End - Frequently used items.
	//######

	for (int fIndex = 0; fIndex < files.length; fIndex++) {
	    File file = files[fIndex];
	    //currentFile = files[fIndex].toString();

	    //System.out.println("Processing " + file + ", please wait ......");
	    FileInputStream fileIn = new FileInputStream(file);
	    InputStreamReader inReader = new InputStreamReader(fileIn);
	    BufferedReader br = new BufferedReader(inReader);
	    

	    inputString = br.readLine();
	    if(inputString.indexOf("Total:")!=-1){

		// Since this is google perftools output, there will only be one node, context, and thread per file
		node = this.addNode(++nodeID);
		context = node.addContext(0);
		thread = context.addThread(0);

		// Time is the only metric tracked with google perftools.
		this.addMetric("Time");

		//fixLengths = true;
		linenumber = 2; //Already read in the first line
		while ((inputString = br.readLine()) != null) {

		    int length = inputString.length();
		    if (length != 0) {
			
			    LineData self  = getLineData(inputString);
			    //242  61.7%  61.7%      242  61.7% rmatmult3
			    function = this.addFunction(self.s0, 1);
			    function.addGroup(addGroup("TAU_DEFAULT"));

			    functionProfile = new FunctionProfile(function);
			    thread.addFunctionProfile(functionProfile);
			    functionProfile.setInclusive(0, self.d1);
			    functionProfile.setExclusive(0, self.d0);
			    functionProfile.setNumCalls(1);
			
		    }
		    linenumber++;
		} // while lines in file
	    }
	} // for elements in vector v

	this.generateDerivedData();

	time = (System.currentTimeMillis()) - time;
	//System.out.println("Done processing data!");
	//System.out.println("Time to process (in milliseconds): " + time);
    }


    private LineData getLineData(String string) {
	LineData lineData = new LineData();
	StringTokenizer st = new StringTokenizer(string, " \t\n\r%");

	/**
	 * 242  61.7%  61.7%      242  61.7% rmatmult3
	 * Number of profiling samples in this function
	 * Percentage of profiling samples in this function
	 * Percentage of profiling samples in the functions printed so far
	 * Number of profiling samples in this function and its callees
	 * Percentage of profiling samples in this function and its callees
	 * Function name
	 */

	//Number of profiling samples in this function
	//Exclusive 
	lineData.d0 =10.0* Double.parseDouble(st.nextToken());

	//Percentage of profiling samples in this function
	st.nextToken();

	// Percentage of profiling samples in the functions printed so far
	st.nextToken();

	// Number of profiling samples in this function and its callees
	//Inclusive
	lineData.d1 =10.0* Double.parseDouble(st.nextToken());

	//Percentage of profiling samples in this function and its callees
	st.nextToken();

	// Function name

	lineData.s0 = st.nextToken(); //Name

	return lineData;
    }



}
