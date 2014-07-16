package edu.uoregon.tau.paraprof;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.sql.SQLException;
import java.util.Iterator;
import java.util.List;
import java.util.StringTokenizer;

import edu.uoregon.tau.common.MetaDataMap;
import edu.uoregon.tau.common.MetaDataMap.MetaDataKey;
import edu.uoregon.tau.perfdmf.*;
import edu.uoregon.tau.perfdmf.taudb.TAUdbDatabaseAPI;

public class ExternalController {

    static public void runController() {
        try {
            System.out.println("Control Mode Active!");

            BufferedReader stdin = new BufferedReader(new InputStreamReader(System.in));

            String input = stdin.readLine();

            while (input != null) {
                System.out.println("got input: " + input);

                if (input.startsWith("control ")) {
                    processCommand(input.substring(8));
                }
                input = stdin.readLine();
            }

            exitController();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    static public void exitController() {
        System.out.println("Control Mode Complete!");
        System.exit(0);

    }

    static public void processCommand(String command) throws Exception {
        System.out.println("processing command: " + command);
        if (command.equals("open manager")) {
            ParaProf.paraProfManagerWindow.setVisible(true);
        } else if (command.equals("list databases")) {
            listDatabases();
        } else if (command.startsWith("list applications")) {
            listApplications(command.substring("list applications".length() + 1));
        } else if (command.startsWith("list experiments")) {
            listExperiments(command.substring("list experiments".length() + 1));
        } else if (command.startsWith("list trials")) {
            listTrials(command.substring("list trials".length() + 1));
        } else if (command.startsWith("load")) {
            loadDBTrial(command.substring("load".length() + 1));
        } else if (command.startsWith("upload")) {
            uploadTauTrial(command.substring("upload".length() + 1));
        } else if (command.equals("exit")) {
            exitController();
        }
    }

    static public void loadDBTrial(String command) throws Exception {
        StringTokenizer tokenizer = new StringTokenizer(command, " ");
        int dbID = Integer.parseInt(tokenizer.nextToken());
        int trialID = Integer.parseInt(tokenizer.nextToken());

        DatabaseAPI databaseAPI = new DatabaseAPI();
        databaseAPI.initialize(Database.getDatabases().get(dbID));
		if (databaseAPI.db().getSchemaVersion() > 0) {
			// copy the DatabaseAPI object data into a new TAUdbDatabaseAPI object
			databaseAPI = new TAUdbDatabaseAPI(databaseAPI);
		}

        databaseAPI.setTrial(trialID, false);
        DBDataSource dbDataSource = new DBDataSource(databaseAPI);
        dbDataSource.load();
        
        Trial trial = new Trial();
        trial.setDataSource(dbDataSource);
        trial.setID(trialID);
        
        ParaProfTrial ppTrial = new ParaProfTrial(trial);
        ppTrial.finishLoad();
        ppTrial.setID(trial.getID());
        ppTrial.showMainWindow();
    }

    static public void uploadTauTrial(String command) throws Exception {
        StringTokenizer tokenizer = new StringTokenizer(command, " ");

        String location = tokenizer.nextToken();
        int dbID = Integer.parseInt(tokenizer.nextToken());
        String appName = tokenizer.nextToken();
        String expName = tokenizer.nextToken();
        String trialName = tokenizer.nextToken();

        File file = new File(location);
        File[] files = new File[1];
        files[0] = file;
        int type = DataSource.TAUPROFILE;
        if(!file.isDirectory())
        {	
        	type = UtilFncs.identifyData(file);
        }
        DataSource dataSource = UtilFncs.initializeDataSource(files, type, false);
        dataSource.load();

        Trial trial = new Trial();
        trial.setDataSource(dataSource);

        DatabaseAPI databaseAPI = new DatabaseAPI();
        databaseAPI.initialize(Database.getDatabases().get(dbID));

        trial.setName(trialName);
        if(databaseAPI.db().getSchemaVersion()==0){
        Experiment exp = databaseAPI.getExperiment(appName, expName, true);
        trial.setExperimentID(exp.getID());
        }else{
        	MetaDataMap map = trial.getMetaData();
        	MetaDataKey key = map.newKey("Application");
        	map.put(key , appName);
        	key = map.newKey("Experiment");
        	map.put(key , expName);
        }
        int trialID = databaseAPI.uploadTrial(trial, false);
        outputCommand("return " + trialID);
        outputCommand("endreturn");

    }

    static public void listApplications(String databaseID) throws SQLException {
        int id = Integer.parseInt(databaseID);
        List<Database> databases = Database.getDatabases();
        

        DatabaseAPI databaseAPI = new DatabaseAPI();
        databaseAPI.initialize(databases.get(id));
        if(databaseAPI.db().getSchemaVersion() >0){
        	System.out.println("This is a TAUdbDatabase which no longer supports applications.");
        	outputCommand("return "+0+" default");
        }
        else{
        List<Application> apps = databaseAPI.getApplicationList();
        for (Iterator<Application> it = apps.iterator(); it.hasNext();) {
            Application app = it.next();
            outputCommand("return " + app.getID() + " " + app.getName());
        }
        }
        outputCommand("endreturn");
    }

    static public void listExperiments(String ids) throws SQLException {

        StringTokenizer tokenizer = new StringTokenizer(ids, " ");

        int dbID = Integer.parseInt(tokenizer.nextToken());
        int appID = Integer.parseInt(tokenizer.nextToken());

        DatabaseAPI databaseAPI = new DatabaseAPI();
        databaseAPI.initialize(Database.getDatabases().get(dbID));
        databaseAPI.setApplication(appID);
        if(databaseAPI.db().getSchemaVersion() >0){
        	System.out.println("This is a TAUdbDatabase which no longer supports Experiments.");
        	outputCommand("return "+0+" default");
        }else{
        List<Experiment> exps = databaseAPI.getExperimentList();
        for (Iterator<Experiment> it = exps.iterator(); it.hasNext();) {
            Experiment exp = it.next();
            outputCommand("return " + exp.getID() + " " + exp.getName());
        }
        }
        outputCommand("endreturn");
    }

    static public void listTrials(String ids) throws SQLException {

        StringTokenizer tokenizer = new StringTokenizer(ids, " ");

        int dbID = Integer.parseInt(tokenizer.nextToken());
        int expID = Integer.parseInt(tokenizer.nextToken());

        DatabaseAPI databaseAPI = new DatabaseAPI();
        databaseAPI.initialize(Database.getDatabases().get(dbID));
		if (databaseAPI.db().getSchemaVersion() > 0) {
			// copy the DatabaseAPI object data into a new TAUdbDatabaseAPI object
			databaseAPI = new TAUdbDatabaseAPI(databaseAPI);
		}else{
			databaseAPI.setExperiment(expID);
		}
        List<Trial> trials = databaseAPI.getTrialList(false);
        for (Iterator<Trial> it = trials.iterator(); it.hasNext();) {
            Trial trial = it.next();
            outputCommand("return " + trial.getID() + " " + trial.getName());
        }
        outputCommand("endreturn");
    }

    static public void listDatabases() {
        List<Database> databases = Database.getDatabases();
        int id = 0;
        for (Iterator<Database> it = databases.iterator(); it.hasNext();) {
            Database db = it.next();
            outputCommand("return " + id + " " + db.getName());
            id++;
        }
        outputCommand("endreturn");

    }

    static public void outputCommand(String command) {
        System.out.println("control " + command);
    }

}
