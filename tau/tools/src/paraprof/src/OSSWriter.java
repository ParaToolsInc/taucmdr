package edu.uoregon.tau.paraprof;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import edu.uoregon.tau.common.PrintfFormat;
import edu.uoregon.tau.perfdmf.DataSource;
import edu.uoregon.tau.perfdmf.FunctionProfile;
import edu.uoregon.tau.perfdmf.Metric;
import edu.uoregon.tau.perfdmf.Thread;
import edu.uoregon.tau.perfdmf.Trial;
import edu.uoregon.tau.perfdmf.UtilFncs;

public class OSSWriter {
    public static void writeOSS(DataSource dataSource, boolean summary) {

        Trial trial = new Trial();
        trial.setDataSource(dataSource);
        ParaProfTrial ppTrial = new ParaProfTrial();
        DataSorter ds = new DataSorter(ppTrial);

        int numMetrics = dataSource.getNumberOfMetrics();

        int timeMetric = 0;
        for (int i = 0; i < numMetrics; i++) {
            Metric m = dataSource.getMetric(i);
            if (m.isTimeMetric()) {
                timeMetric = i;
            }
        }

        List<Thread> threads = new ArrayList<Thread>();
        if (!summary) {
            threads = dataSource.getAllThreads();
        }

        if (dataSource.getAllThreads().size() > 1 || summary) {
            // add total and mean meta-threads only if there is more than one actual thread
            threads.add(dataSource.getTotalData());
            threads.add(dataSource.getMeanData());
            threads.add(dataSource.getStdDevData());
            Thread tmp = null;
            tmp = dataSource.getMaxData();
            if(tmp!=null)
            	threads.add(tmp);
            tmp = dataSource.getMinData();
            if(tmp!=null)
            	threads.add(tmp);
            
        }

        for (int i = 0; i < threads.size(); i++) {
            Thread thread = threads.get(i);
            System.out.println("\n-------------------------------------------------------------------------------");

            if (thread.getNodeID() == -2) {
                System.out.println("Thread: " + "Total");
            } else {
                System.out.println("Thread: " + thread);
            }

            System.out.println("-------------------------------------------------------------------------------");

            String header = " excl.secs  excl.%   cum.%";
            for (int m = 0; m < numMetrics; m++) {
                if (m == timeMetric) {
                    continue;
                }
                Metric ppMetric = trial.getDataSource().getMetric(m);
                String metricName = ppMetric.getName();

                int width = Math.max(16, metricName.length() + 2);

                header = header + UtilFncs.lpad(metricName, width);
            }

            header = header + "     calls  function";
            System.out.println(header);

            List<PPFunctionProfile> l = ds.getFunctionProfiles(thread);

            double cumulative = 0;

            for (Iterator<PPFunctionProfile> it = l.iterator(); it.hasNext();) {
                PPFunctionProfile p = it.next();
                FunctionProfile fp = p.getFunctionProfile();

                double exclSec = fp.getExclusive(timeMetric) / 1000 / 1000;
                double exclPercent = fp.getExclusivePercent(timeMetric);
                //double inclPercent = fp.getInclusivePercent(timeMetric);
                cumulative += exclPercent;

                String string = new PrintfFormat("%10.3G ").sprintf(exclSec) + new PrintfFormat("%6.1f%% ").sprintf(exclPercent)
                        + new PrintfFormat("%6.1f%%").sprintf(cumulative);
                //String string = "%10.3G %6.1f%% %6.1f%%" % (exclSec, exclPercent, inclPercent);

                for (int m = 0; m < numMetrics; m++) {
                    if (m == timeMetric) {
                        continue;
                    }
                    double excl = fp.getExclusive(m);
                    Metric ppMetric = trial.getDataSource().getMetric(m);
                    String metricName = ppMetric.getName();
                    string = string + new PrintfFormat("%" + (Math.max(16, metricName.length() + 2)) + ".0f").sprintf(excl);
                    //string = string + ("%" + str(max(16,len(metricName)+2)) + ".0f") % excl

                }
                string = string + new PrintfFormat("%10.0f").sprintf(fp.getNumCalls());
                //string = string + ("%10.0f" % (fp.getNumCalls()))
                string = string + "  " + fp.getName();

                System.out.println(string);
            }

        }

    }
}
