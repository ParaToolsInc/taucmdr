import sys
from edu.uoregon.tau.perfdmf import Trial
from rules import RuleHarness
from glue import PerformanceResult
from glue import Utilities
from glue import TrialResult
from glue import BasicStatisticsOperation
from glue import AbstractResult
from glue import ExtractNonCallpathEventOperation
from glue import ExtractEventOperation
from glue import DeriveMetricOperation
from glue import ScaleMetricOperation
from glue import MergeTrialsOperation
from glue import DerivedMetrics
from glue import TopXEvents
from glue import MeanEventFact

###################################################################

True = 1
False = 0
mainEvent = ""

###################################################################

def deriveMetric(input, first, second, oper):
	# derive the metric
	derivor = DeriveMetricOperation(input, first, second, oper)
	derived = derivor.processData().get(0)
	newName = derived.getMetrics().toArray()[0]
	# merge new metric with the trial
	merger = MergeTrialsOperation(input)
	merger.addInput(derived)
	merged = merger.processData().get(0)
	#print "new metric: " + newName
	return merged, newName

def scaleMetric(input, metric, value, oper):
	# derive the metric
	scaler = ScaleMetricOperation(input, metric, value, oper)
	scaled = scaler.processData().get(0)
	newName = scaled.getMetrics().toArray()[0]
	# merge new metric with the trial
	merger = MergeTrialsOperation(input)
	merger.addInput(scaled)
	merged = merger.processData().get(0)
	#print "new metric: " + newName
	return merged, newName

###################################################################

def getPowerModel(input):
	# set some metric names
	totalCycles = "CPU_CYCLES"
	totalInstructions = "IA64_INST_RETIRED_THIS"
	#L1references = "L1_REFERENCES"
	L1references = "PAPI_L1_TCA"
	L2references = "L2_REFERENCES"
	L3references = "L3_REFERENCES"
	global mainEvent

	# derive the CPU Power term
	input, CPUPower = deriveMetric(input, totalInstructions, totalCycles, DeriveMetricOperation.DIVIDE)
	#print mainEvent, totalInstructions, input.getInclusive(0, mainEvent, totalInstructions)
	#print mainEvent, totalCycles, input.getInclusive(0, mainEvent, totalCycles)
	#print mainEvent, CPUPower, input.getInclusive(0, mainEvent, CPUPower)
	input, CPUPower = scaleMetric(input, CPUPower, (0.0459 * 122), ScaleMetricOperation.MULTIPLY)
	#print "\t", mainEvent, CPUPower, input.getInclusive(0, mainEvent, CPUPower)
	# derive the L1 Power term
	#print mainEvent, L1references, input.getInclusive(0, mainEvent, L1references)
	input, L1Power = deriveMetric(input, L1references, totalCycles, DeriveMetricOperation.DIVIDE)
	#print mainEvent, L1Power, input.getInclusive(0, mainEvent, L1Power)
	input, L1Power = scaleMetric(input, L1Power, (0.0017 * 122), ScaleMetricOperation.MULTIPLY)
	#print "\t", mainEvent, L1Power, input.getInclusive(0, mainEvent, L1Power)
	# derive the L2 Power term
	#print mainEvent, L2references, input.getInclusive(0, mainEvent, L2references)
	input, L2Power = deriveMetric(input, L2references, totalCycles, DeriveMetricOperation.DIVIDE)
	#print mainEvent, L2Power, input.getInclusive(0, mainEvent, L2Power)
	input, L2Power = scaleMetric(input, L2Power, (0.0171 * 122), ScaleMetricOperation.MULTIPLY)
	#print "\t", mainEvent, L2Power, input.getInclusive(0, mainEvent, L2Power)
	# derive the L3 Power term
	#print mainEvent, L3references, input.getInclusive(0, mainEvent, L3references)
	input, L3Power = deriveMetric(input, L3references, totalCycles, DeriveMetricOperation.DIVIDE)
	#print mainEvent, L3Power, input.getInclusive(0, mainEvent, L3Power)
	input, L3Power = scaleMetric(input, L3Power, (0.935 * 122), ScaleMetricOperation.MULTIPLY)
	#print "\t", mainEvent, L3Power, input.getInclusive(0, mainEvent, L3Power)

	# sum them all up!
	input, PowerPerProc = deriveMetric(input, CPUPower, L1Power, DeriveMetricOperation.ADD)
	input, PowerPerProc = deriveMetric(input, PowerPerProc, L2Power, DeriveMetricOperation.ADD)
	input, PowerPerProc = deriveMetric(input, PowerPerProc, L3Power, DeriveMetricOperation.ADD)
	input, PowerPerProc = scaleMetric(input, PowerPerProc, 97.66, ScaleMetricOperation.ADD)

	# return the trial, and the new derived metric name
	return input, PowerPerProc

def getEnergy(input, PowerPerProc):
	global mainEvent
	time = "LINUX_TIMERS"

	# convert time to seconds
	#print mainEvent, time, input.getInclusive(0, mainEvent, time)
	input, seconds = scaleMetric(input, time, (1/1000000.0), ScaleMetricOperation.MULTIPLY)
	#print mainEvent, seconds, input.getInclusive(0, mainEvent, seconds)
	input, joules = deriveMetric(input, PowerPerProc, seconds, DeriveMetricOperation.MULTIPLY)
	#print mainEvent, joules, input.getInclusive(0, mainEvent, joules)

	# return the trial, and the new derived metric name
	return input, joules

def getFlopsPerJoule(input, EnergyPerProc):
	global mainEvent
	#fpOps = "FP_OPS_RETIRED"
	fpOps = "PAPI_FP_OPS"

	#print mainEvent, fpOps, input.getInclusive(0, mainEvent, fpOps)
	input, flopsPerJoule = deriveMetric(input, fpOps, EnergyPerProc, DeriveMetricOperation.DIVIDE)
	#print mainEvent, flopsPerJoule, input.getInclusive(0, mainEvent, flopsPerJoule)

	# return the trial, and the new derived metric name
	return input, flopsPerJoule

###################################################################

def main():
	global mainEvent
	global True
	global False
	
	print "--------------- JPython test script start ------------"
	print "--- Calculating Power Models --- "

	# create a rulebase for processing
	#print "Loading Rules..."
	#ruleHarness = RuleHarness.useGlobalRules("openuh/OpenUHRules.drl")

	# load the trial
	print "loading the data..."

	# check to see if the user has selected a trial
	tmp = Utilities.getCurrentTrial()
	if tmp != None:
		trial = TrialResult(tmp)
		print 
	else:
		# remove these two lines to bypass this and use the default trial
		print "No trial selected - script exiting"
		return

		Utilities.setSession("openuh")

		# load just the average values across all threads, input: app_name, exp_name, trial_name
		#trial = TrialResult(Utilities.getTrial("msap_parametric.optix.static", "size.400", "16.threads"))
		#trial = TrialResult(Utilities.getTrial("Fluid Dynamic - Unoptimized", "rib 45", "1_8"))

	# extract the non-callpath events from the trial
	print "extracting non-callpath..."
	extractor = ExtractNonCallpathEventOperation(trial)
	extracted = extractor.processData().get(0)

	# print "extracting event..."
	# extractor = ExtractEventOperation(trial, "MAIN__")
	# extracted = extractor.processData().get(0)

	# get basic statistics
	print "computing mean..."
	statMaker = BasicStatisticsOperation(extracted, True)
	stats = statMaker.processData()
	means = stats.get(BasicStatisticsOperation.MEAN)

	# get main event
	mainEvent = means.getMainEvent()
	print "Main Event: ", mainEvent

	# calculate all derived metrics
	print "Deriving power metrics..."
	derived, PowerPerProc = getPowerModel(means)

	# get the top 10 "power dense" events
	top10er = TopXEvents(derived, PowerPerProc, AbstractResult.EXCLUSIVE, 10)
	top10 = top10er.processData().get(0)

	# just one thread
	thread = 0

	# iterate over events, output inefficiency derived metric
	print "Top 10 Average", PowerPerProc, "values per thread for this trial:"
	for event in top10er.getSortedEventNames():
		print event, top10.getExclusive(thread, event, PowerPerProc)
	print
	print mainEvent, "INCLUSIVE: ", derived.getInclusive(thread, mainEvent, PowerPerProc)
	print

	# compute the energy consumed by each event
	print "Computing joules consumed..."
	derived, EnergyPerProc = getEnergy(derived, PowerPerProc)

	# get the top 10 "power dense" events
	top10er = TopXEvents(derived, EnergyPerProc, AbstractResult.EXCLUSIVE, 10)
	top10 = top10er.processData().get(0)

	# iterate over events, output inefficiency derived metric
	print "Top 10 Average", EnergyPerProc, "values per thread for this trial:"
	for event in top10er.getSortedEventNames():
		print event, top10.getExclusive(thread, event, EnergyPerProc)
		#print event, top10.getExclusive(thread, event, "LINUX_TIMERS")
		#print event, top10.getExclusive(thread, event, "(LINUX_TIMERS*1.0E-6)")
	print
	print mainEvent, "INCLUSIVE: ", derived.getInclusive(thread, mainEvent, EnergyPerProc)
	#print mainEvent, derived.getExclusive(thread, event, "LINUX_TIMERS")
	#print mainEvent, derived.getExclusive(thread, event, "(LINUX_TIMERS*1.0E-6)")
	print

	# compute the floating point operations per joule per event
	print "Computing FP_OPS/joule..."
	derived, FlopsPerJoule = getFlopsPerJoule(derived, EnergyPerProc)

	# get the top 10 "power dense" events
	top10er = TopXEvents(derived, FlopsPerJoule, AbstractResult.EXCLUSIVE, 10)
	top10 = top10er.processData().get(0)

	# iterate over events, output inefficiency derived metric
	print "Top 10 Average", FlopsPerJoule, "values per thread for this trial:"
	for event in top10er.getSortedEventNames():
		print event, top10.getExclusive(thread, event, FlopsPerJoule)
	print
	print mainEvent, "INCLUSIVE: ", derived.getInclusive(thread, mainEvent, FlopsPerJoule)
	print

	# process the rules
	#RuleHarness.getInstance().processRules()

	print "---------------- JPython test script end -------------"

if __name__ == "__main__":
	main()
