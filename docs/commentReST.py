#! /usr/bin/env python

import argparse,glob
quote3='\"\"\"'

def main():
  parser = argparse.ArgumentParser(description='Comment dosctring header with fix for TAU\'d headers.')
 
  parser.add_argument('-f','--filename', default=None,
                      help='Name of file to readjust comments.')

  parser.add_argument('-dir','--directory', default=None,
                      help='directory where py files live.') #not done

  args = parser.parse_args()


  fileList=[]

 
  if (args.filename): 
    fileList.append(args.filename)
  elif (args.directory):
    for fname in glob.glob(args.directory + '*.py'):
      fileList.append(fname)


  for myfile in fileList:
    with open(myfile) as f:
      file_lines = f.readlines()

    whereIs3quotes = [i for i,val in enumerate(file_lines) if (quote3 in val)]
    first2quotes=[whereIs3quotes[0:1]]


    a=whereIs3quotes[0:2]


    for index,line in enumerate(file_lines[a[0]:a[1]+1]):
      if ('2013' in line):
        file_lines[index]="#" + line.replace('2013','2015')
      elif ('TAU Performance' in line):
        file_lines[index]="#" + line.replace('the TAU Performance System','TAU Commander')
      else:
        file_lines[index]="#" + line

    with open(myfile,'w') as f:
        for line in file_lines:
          f.write(line)


if __name__ == "__main__":
   main()


