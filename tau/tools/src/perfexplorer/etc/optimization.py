from edu.uoregon.tau.perfexplorer.glue import *
from edu.uoregon.tau.perfexplorer.client import PerfExplorerModel
from edu.uoregon.tau.perfdmf import Trial
from java.util import HashSet
from java.util import ArrayList

True = 1
False = 0
config = "proper"
inApp = "sweep3d_gnu"
inExp = "mpi-pdt_2008-08-15_15:34:07"
inTrial = ""

def load():
	print "loading data..."
	parameterMap = PerfExplorerModel.getModel().getScriptParameters()
	keys = parameterMap.keySet()
	for key in keys:
		print key, parameterMap.get(key)
	config = parameterMap.get("config")
	inApp = parameterMap.get("app")
	inExp = parameterMap.get("exp")
	Utilities.setSession(config)
	trials = Utilities.getTrialsForExperiment(inApp, inExp)
	print "...done."
	return trials

def extractMain(inputs):
	events = ArrayList()
	events.add(inputs.get(0).getMainEvent())

	print "extracting main event..."
	extractor = ExtractEventOperation(inputs, events)
	extracted = extractor.processData()
	print "...done."

	return extracted

def getTop3(inputs):
	print "extracting top 3 events..."
	reducer = TopXEvents(inputs, "Time", AbstractResult.EXCLUSIVE, 3)
	reduced = reducer.processData()
	return reduced

def drawGraph(results, inclusive):
	print "drawing charts..."
	for metric in results.get(0).getMetrics():
		grapher = DrawGraph(results)
		metrics = HashSet()
		metrics.add(metric)
		grapher.set_metrics(metrics)
		grapher.setLogYAxis(False)
		grapher.setShowZero(False)
		grapher.setTitle(inApp + ": " + inExp + ": " + metric)
		grapher.setSeriesType(DrawGraph.EVENTNAME)
		grapher.setUnits(DrawGraph.SECONDS)
		grapher.setCategoryType(DrawGraph.METADATA)
		grapher.setMetadataField("BUILD:Optimization Level")
		grapher.setXAxisLabel("Optimization Level")
		if inclusive == True:
			grapher.setValueType(AbstractResult.INCLUSIVE)
			grapher.setYAxisLabel("Inclusive " + metric + " (seconds)")
		else:
			grapher.setValueType(AbstractResult.EXCLUSIVE)
			grapher.setYAxisLabel("Exclusive " + metric + " (seconds)")

		grapher.processData()
	print "...done."

	return

print "--------------- JPython test script start ------------"

trials = load()
results = ArrayList()
for trial in trials:
	loaded = TrialMeanResult(trial)
	results.add(loaded)

extracted = extractMain(results)
drawGraph(extracted, True)
extracted = getTop3(results)
drawGraph(extracted, False)

print "---------------- JPython test script end -------------"
