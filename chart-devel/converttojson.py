import json
import fnmatch
import os

files = [];

# Find all profile files
for file in os.listdir('.'):
	if fnmatch.fnmatch(file, 'profile.*.*.*.json'):
		os.remove(file)

# Find all profile files
for file in os.listdir('.'):
	if fnmatch.fnmatch(file, 'profile.*.*.*'):
		files.append(file)

for f in files:
	txt = open(f,'r');
	outfile = open(f + '.json', 'w');
        node = f.split('.')[1]
        thread = f.split('.')[3]

	line = txt.readline()
	numfunc = int(line.split(' ')[0])
	print numfunc
	line = txt.readline()
	outfile.write('[')
        json.dump({'node' : node, 'thread' : thread}, outfile, indent=4)
        outfile.write(',\n')
	for i in range(0,numfunc):
		line = txt.readline()
		funcName = line.split('"')[1]
		calls = (line.split('"')[2]).split(' ')[1]
		subr = (line.split('"')[2]).split(' ')[2]
		exc = (line.split('"')[2]).split(' ')[3]
		inc = (line.split('"')[2]).split(' ')[4]
		prfcalls = (line.split('"')[2]).split(' ')[5]
		grp = line.split('GROUP="')[1][:-3]
		print funcName, calls, subr, exc, inc, prfcalls, grp
		json.dump({'Function Name' : funcName, '#Calls' : calls, '#Subrs' : subr, 'Exclusive (msec)': exc, 'Inclusive (msec)' : inc}, outfile, indent=4)
		if(i < numfunc - 1):
			outfile.write(',\n')
		else:
			outfile.write('\n')
	outfile.write(']');

	txt.close()
	outfile.close()
