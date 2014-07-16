package edu.uoregon.tau.paraprof;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

import com.graphbuilder.math.Expression;
import com.graphbuilder.math.ExpressionTree;
import com.graphbuilder.math.FuncMap;
import com.graphbuilder.math.VarMap;

import edu.uoregon.tau.perfdmf.Thread;

public class ThreeDeeGeneralPlotUtils {

	static final String BEGIN = "BEGIN_VIZ";
	static final String END = "END_VIZ";

	public static VarMap getEvaluation(int rank,
			int maxRank,
			Thread thread,
			ParaProfTrial pptrial,

			// int node,
			// int context, int thread, int maxNode, int maxContext,
			// int maxThread,
			float[] topoVals, float[] varMins, float varMaxs[],
			float varMeans[], int[] axisDim, Map<String, String> expressions) {// String[]
																				// expressions,
																				// int
																				// rank,
																				// int
																				// maxRank){
																				// float[]
																				// atomValue,
		// System.out.println(rank);
		FuncMap fm = new FuncMap();
		fm.loadDefaultFunctions();
		VarMap vm = new VarMap(false);
		vm.setValue("maxRank", maxRank);
		vm.setValue("rank", rank);
		vm.setValue("color", topoVals[3]);
		vm.setValue("node", thread.getNodeID());
		vm.setValue("context", thread.getContextID());
		vm.setValue("thread", thread.getThreadID());
		vm.setValue("event0.val", topoVals[0]);
		vm.setValue("event1.val", topoVals[1]);
		vm.setValue("event2.val", topoVals[2]);
		vm.setValue("event3.val", topoVals[3]);
		vm.setValue("event0.min", varMins[0]);
		vm.setValue("event1.min", varMins[1]);
		vm.setValue("event2.min", varMins[2]);
		vm.setValue("event3.min", varMins[3]);
		vm.setValue("event0.max", varMaxs[0]);
		vm.setValue("event1.max", varMaxs[1]);
		vm.setValue("event2.max", varMaxs[2]);
		vm.setValue("event3.max", varMaxs[3]);
		vm.setValue("event0.mean", varMeans[0]);
		vm.setValue("event1.mean", varMeans[1]);
		vm.setValue("event2.mean", varMeans[2]);
		vm.setValue("event3.mean", varMeans[3]);
		// vm.setValue("atomic0", atomValue[0]);
		// vm.setValue("atomic1", atomValue[1]);
		// vm.setValue("atomic2", atomValue[2]);
		// vm.setValue("atomic3", atomValue[3]);
		vm.setValue("axisDimX", axisDim[0]);
		vm.setValue("axisDimY", axisDim[1]);
		vm.setValue("axisDimZ", axisDim[2]);

		Expression x;
		double res;

		Iterator<Entry<String, String>> it = expressions.entrySet().iterator();

		while (it.hasNext()) {
			Entry<String, String> e = it.next();

			x = ExpressionTree
					.parse(insertMetaDataValues(e.getValue(), thread));
			res = x.eval(vm, fm);
			// System.out.println(e.getKey()+" "+res);
			vm.setValue(e.getKey(), res);
		}
		return vm;

	}

	private static final String metadata = "metadata(";

	private static String insertMetaDataValues(String s, Thread t) {
		int dex = 0;
		while (dex >= 0) {
			int loc = s.indexOf(metadata, dex);
			if (loc == -1)
				return s;
			int cloc = s.indexOf(')', loc);
			String key = s.substring(loc + 9, cloc);

			String value = t.getMetaData().get(key);

			if (value == null) {
				value=t.getDataSource().getMetaData().get(key);
				if(value==null){
				System.out.println("Metadata key " + key
						+ " not found at top or in node,thread " + t.getNodeID() + ","
						+ t.getThreadID() + ". Using 0");
				value = "0";
			}}
			
			try{
			Double.parseDouble(value);
			}
			catch(NumberFormatException e){
				System.out.println("Metadata key " + key
						+ " is non-numeric in node,thread " + t.getNodeID() + ","
						+ t.getThreadID() + ". Using 0");
				value = "0";
			}
			s=s.substring(0,loc)+value+s.substring(cloc+1);

			dex = cloc;
		}
		return s;
	}

	private static String[] splitEQ(String s) {
		String[] tuple = new String[2];

		int x1 = s.indexOf('=');

		tuple[0] = s.substring(0, x1).trim();
		tuple[1] = s.substring(x1 + 1).trim();
		// System.out.println(s+" "+tuple[0]+" "+tuple[1]);
		return tuple;
	}

	public static Map<String, String> getExpressions(String fileLoc,
			String expName) {
		BufferedReader br;
		Map<String, String> expressions = new LinkedHashMap<String, String>();
		try {
			br = new BufferedReader(new FileReader(new File(fileLoc)));

			String s;

			boolean foundExp = false;

			while ((s = br.readLine()) != null) {

				if (!foundExp && s.startsWith(BEGIN)) {
					if (splitEQ(s)[1].equals(expName)) {
						foundExp = true;
						continue;
					}
				}

				if (foundExp) {
					if (s.equals(END))
						break;
					if (!s.contains("=") || s.startsWith("#"))
						continue;

					String[] tuple = splitEQ(s);

					expressions.put(tuple[0], tuple[1]);
				}

			}

		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
		return expressions;
	}

	public static boolean checkSet(VarMap vm, String var) {
		String[] names = vm.getVariableNames();
		for (int i = 0; i < names.length; i++) {
			if (names[i].equals(var)) {
				return true;// vm.getValue(var)!=0;
			}
		}
		return false;
	}

	public static int getPointsPerRank(VarMap vm) {
		int ppm = 0;
		boolean has = checkSet(vm, "x");
		// System.out.println(has);
		if (!has) {
			has = true;
			while (has) {
				// System.out.println(ppm);
				has = checkSet(vm, "x" + ppm);
				if (has)
					ppm++;
				else
					break;
			}
		}

		return ppm;
	}

	public static double[][] getRankCoordinate(VarMap vm, int maxpoint,
			boolean multiColor) {
		double[][] coords = null;
		// boolean has=checkSet(vm,"x");
		if (maxpoint == 0) {
			coords = new double[1][4];
			coords[0][0] = vm.getValue("x");
			coords[0][1] = vm.getValue("y");
			coords[0][2] = vm.getValue("z");
			coords[0][3] = vm.getValue("color");
		} else {
			coords = new double[maxpoint][4];
			maxpoint--;
			for (int i = 0; i <= maxpoint; i++) {
				coords[i][0] = vm.getValue("x" + i);
				coords[i][1] = vm.getValue("y" + i);
				coords[i][2] = vm.getValue("z" + i);
				if (multiColor)
					coords[i][3] = vm.getValue("color" + i);
				else
					coords[i][3] = vm.getValue("color");
				// System.out.println(coords[i][0]+" "+coords[i][1]+" "+coords[i][2]+" "+coords[i][3]);
			}
		}
		// System.out.println(coords[0][0]+" "+coords[0][1]+" "+coords[0][2]+" "+coords[0][3]);
		return coords;
	}

	public static int[] parseMPIProcName(String pname) {

		String s = pname.substring(pname.indexOf('('), pname.indexOf(')') + 1);

		return (parseTuple(s));

	}

	public static int[] parseTuple(String tuple) {

		tuple = tuple.substring(1, tuple.length() - 1);
		String[] tmp = tuple.split(",");
		int tmplen = tmp.length;
		if (tmplen < 3) {
			tmplen = 3;
		}
		int[] tres = new int[tmplen];
		for (int i = 0; i < tmplen; i++) {
			if (i < tmp.length)
				tres[i] = Integer.parseInt(tmp[i]);
			else
				tres[i] = 0;
		}
		return tres;
	}

	public static List<String> getCustomTopoNames(String fileLoc) {
		List<String> names = new ArrayList<String>();
		BufferedReader br;

		try {
			br = new BufferedReader(new FileReader(new File(fileLoc)));

			String s;

			while ((s = br.readLine()) != null) {

				if (s.startsWith(BEGIN)) {

					int x1 = s.indexOf('=');
					// int x2 = s.indexOf('"', x1 + 1);

					// String id = s.substring(0,x1);
					String name = s.substring(x1 + 1);
					names.add(name);// expressions.put(id, exp);
				}

			}

		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		return names;
	}

	static class CoordMap {
		public CoordMap(int[] min, int[] max, int[][] coords) {
			this.min = min;
			this.max = max;
			this.coords = coords;
		}

		public int[] getMin() {
			return min;
		}

		public void setMin(int[] min) {
			this.min = min;
		}

		public int[] getMax() {
			return max;
		}

		public void setMax(int[] max) {
			this.max = max;
		}

		public int[][] getCoords() {
			return coords;
		}

		public void setCoords(int[][] coords) {
			this.coords = coords;
		}

		int[] min;
		int[] max;
		int[][] coords;
	}
	
	public static int[] parseCrayNodeID(String nodename){
		//TODO: only run this once per node
		int[] nodeCoords = new int[5];
		
		int dash = nodename.indexOf('-');
		int cdex = nodename.indexOf('c',dash);
		int sdex = nodename.indexOf('s',cdex);
		int ndex = nodename.indexOf('n',sdex);
		nodeCoords[0]=Integer.parseInt(nodename.substring(1,dash));//cabinet x
		nodeCoords[1]=Integer.parseInt(nodename.substring(dash+1,cdex));//cabinet y
		nodeCoords[2]=Integer.parseInt(nodename.substring(cdex+1, sdex));//cage
		nodeCoords[3]= Integer.parseInt(nodename.substring(sdex+1,ndex));//slot
		nodeCoords[4]=Integer.parseInt(nodename.substring(ndex+1));//node
		
		return nodeCoords;
	}

	public static CoordMap parseMapFile(String fileLoc) {
		BufferedReader br;
		int[][] coords = null;
		boolean gotCores = false;
		int ranks = 0;
		try {
			br = new BufferedReader(new FileReader(new File(fileLoc)));

			String s;
			List<String> nodes = new ArrayList<String>();
			while ((s = br.readLine()) != null) {
				if (!gotCores) {
					ranks = Integer.parseInt(s);
					coords = new int[ranks][4];
					gotCores = true;
					// System.out.println(ranks);
					continue;
				}

				if (s.indexOf('[') == 0) {
					int start = s.indexOf('_') + 1;
					int end = s.indexOf(']');
					String num = s.substring(start, end);
					int rank = Integer.parseInt(num);
					// System.out.println("Rank: "+rank);
					start = s.indexOf('=') + 2;
					end = s.length();
					// System.out.println(start+" "+end);
					num = s.substring(start, end);
					// System.out.println("|"+num+"|");
					int core = num.indexOf('1');
					// System.out.println("Core: "+ core);
					coords[rank][3] = core;
				} else {
					String[] duo = s.split(":");
					int rank = Integer.parseInt(duo[0]);
					int place = nodes.indexOf(duo[1]);

					if (place == -1) {
						nodes.add(duo[1]);
						place = nodes.size() - 1;
					}
					// nodes.insert(rank,duo[1]);
					coords[rank][0] = place % 10;
					coords[rank][1] = (place / 10) % 8;
					coords[rank][2] = (place / 10 / 8);
				}

				// if (s.indexOf(',') > 0) {
				// String[] corexyz = s.split(",");
				// //
				// System.out.println(corexyz[0]+", "+corexyz[1]+", "+corexyz[2]+", "+corexyz[3]);
				// int core = Integer.parseInt(corexyz[0]);
				// for (int i = 0; i < 3; i++) {
				// coords[core][i] = Integer.parseInt(corexyz[i + 1]);
				// }
			}

			// int x1 = s.indexOf('=');
			// //int x2 = s.indexOf('"', x1 + 1);
			//
			// //String id = s.substring(0,x1);
			// String name= s.substring(x1+1);
			// names.add(name);//expressions.put(id, exp);
			// }

			// }

		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		// System.out.println(coords);

		int[] min = new int[3];
		int[] max = new int[3];
		int[] coremax = { 2, 3, 4 };
		int space = 2;
		int[][] done = new int[ranks][3];
		for (int i = 0; i < ranks; i++) {
			int node = coords[i][3];
			for (int j = 0; j < 3; j++) {
				int sub = 1;
				if (j == 1)
					sub = 2;
				if (j == 2)
					sub = 6;
				int cc = (node / sub) % coremax[j];
				// int cy=node%cymax;
				// int cz=node%czmax;
				int c = cc + coords[i][j] * (coremax[j] + space);
				// int y=cy+coords[i][1]*(cymax+space);
				// int z=cz+coords[i][2]*(czmax+space);
				done[i][j] = c;
				if (i == 0) {
					max[j] = c;
					min[j] = c;
				} else {
					max[j] = Math.max(max[j], c);
					min[j] = Math.min(min[j], c);
				}
				// done[i][1]=y;
				// done[i][2]=z;
			}
			System.out.println(i + ": " + done[i][0] + "," + done[i][1] + ","
					+ done[i][2]);
		}
		System.out.println("min: " + min[0] + "," + min[1] + "," + min[2]);
		System.out.println("max: " + max[0] + "," + max[1] + "," + max[2]);

		return new CoordMap(min, max, done);
	}
}
