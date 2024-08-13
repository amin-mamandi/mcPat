#!/usr/bin/python3
from optparse import OptionParser
import sys
import re
import json
import math
import os
from xml.etree import ElementTree as ET


def parse(source): # pragma: no cover
    # Remove the 'insert_pis' argument as it's not supported in newer versions
    return ET.parse(source, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))

def main():
    global opts, outdir, tempFile
    usage = "usage: %prog [options] <gem5 stats file> <gem5 config file (json)> <mcpat template file>"
    parser = OptionParser(usage=usage)
    parser.add_option("-q", "--quiet", 
        action="store_false", dest="verbose", default=True,
        help="don't print status messages to stdout")
    parser.add_option("-o", "--out", type="string",
        action="store", dest="out", default="./",
        help="output directory (input to McPAT)")
    parser.add_option("-a", "--aggregate", action="store_true",
        help="aggregate all the stats in a periodic dump stat file")
    parser.add_option("-p", "--periodic", action="store_true",
        help="write each period in a separate xml file")
    (opts, args) = parser.parse_args()
    if len(args) != 3:
        parser.print_help() 
        sys.exit(1)
    tempFile = args[2]
    outdir = opts.out
    if (outdir == "./"):
        outdir = os.path.dirname(args[0])
        outdir += "/mcpat-out"

    os.system("mkdir -p %s" % outdir)
    readMcpatFile(args[2])
    readConfigFile(args[1])
    readStatsFile(args[0])
    #readConfigFile(args[1])
    #readMcpatFile(args[2])
    #os.system("mkdir -p %s" %(outdir))
    #dumpMcpatOut(outdir, args[2])

def dumpMcpatOut(itr):
    outDir = outdir
    templateFile = tempFile
    rootElem = templateMcpat.getroot()
    configMatch = re.compile(r'config\.([a-zA-Z0-9_:\.]+)')
    #replace params with values from the GEM5 config file 
    for param in rootElem.iter('param'):
        name = param.attrib['name']
        value = param.attrib['value']
        print(name)
        print(value)
        if 'config' in value:
            allConfs = configMatch.findall(value)
            for conf in allConfs:
                confValue = getConfValue(conf)
                value = re.sub("config."+ conf, str(confValue), value)
            if "," in value:
                exprs = re.split(',', value)
                for i in range(len(exprs)):
                    exprs[i] = str(eval(exprs[i]))
                param.attrib['value'] = ','.join(exprs)
            if "[" in value or "]" in value:
                value_proc = str(value).replace('[', '')
                value_proc = str(value_proc).replace(']', '')
                print(value)
                print(value_proc)
                param.attrib['value'] = str(eval(str(value_proc)))
            else:
                param.attrib['value'] = str(eval(str(value)))

    #replace stats with values from the GEM5 stats file 
    statRe = re.compile(r'stats\.([a-zA-Z0-9_:\.]+)')
    for j in range(period + 1):
        for stat in rootElem.iter('stat'):
            name = stat.attrib['name']
            value = stat.attrib['value']
            if 'stats' in value:
                allStats = statRe.findall(value)
                expr = value
                for i in range(len(allStats)):
                    if allStats[i] in stats[j]:
                        expr = re.sub('stats.%s' % allStats[i], stats[j][allStats[i]], expr)
                    else:
                        expr = re.sub('stats.%s' % allStats[i], "0.0", expr)
                        #print "***WARNING: %s does not exist in stats***" % allStats[i]
                        #print "\t Please use the right stats in your McPAT template file"

                if 'config' not in expr and 'stats' not in expr:
                    if "/ 0.0" in expr:
                        stat.attrib['value'] = str(0)
                    else:
                        stat.attrib['value'] = str(eval(expr))
        #Write out the xml file
        if opts.verbose: print("Writing input to McPAT in: %s" % outDir) 
        templateMcpat.write("%s/mcpat-out-%d.xml" %(outDir, itr))
        #if (itr == 0):
        #    os.system("sed -i 's/<stat name=\"clock_rate\" value=\"[0-9]*\"/<param name=\"clock_rate\" value=\"3100\"/g' %s/mcpat-out-%d.xml" %(outDir, itr))
        #    os.system("sed -i 's/<stat name=\"vdd\" value=\"[01]\.[0-9]*\"/<param name=\"vdd\" value=\"1.225\"/g' %s/mcpat-out-%d.xml" %(outDir, itr))
        #else:
        os.system("sed -i 's/<stat name=\"clock_rate_dvfs\"/<param name=\"clock_rate_dvfs\"/g' %s/mcpat-out-%d.xml" %(outDir, itr))
        os.system("sed -i 's/<stat name=\"vdd_dvfs\"/<param name=\"vdd_dvfs\"/g' %s/mcpat-out-%d.xml" %(outDir, itr))
        os.system("sed -i 's/stat name=\"sim_second/param name=\"sim_second/g' %s/mcpat-out-%d.xml" %(outDir, itr))
        os.system("sed -i 's/stat name=\"sim_ticks/param name=\"sim_ticks/g' %s/mcpat-out-%d.xml" %(outDir, itr))
        readMcpatFile(templateFile)
        rootElem = templateMcpat.getroot()
        configMatch = re.compile(r'config\.([a-zA-Z0-9_:\.]+)')

        for param in rootElem.iter('param'):
            name = param.attrib['name']
            value = param.attrib['value']
            if 'config' in value:
                allConfs = configMatch.findall(value)
                for conf in allConfs:
                    confValue = getConfValue(conf)
                    value = re.sub("config."+ conf, str(confValue), value)
                if "," in value:
                    exprs = re.split(',', value)
                    for i in range(len(exprs)):
                        exprs[i] = str(eval(exprs[i]))
                    param.attrib['value'] = ','.join(exprs)
                    # prevent eval() from making tuple in else
                    continue
                if "[" in value or "]" in value:
                    value_proc = str(value).replace('[', '')
                    value_proc = str(value_proc).replace(']', '')
                    print(value)
                    print(value_proc)
                    param.attrib['value'] = str(eval(str(value_proc)))
                else:
                    print(name)
                    print(value)
                    param.attrib['value'] = str(eval(str(value)))


def getConfValue(confStr):
    spltConf = re.split('\.', confStr) 
    currConf = config
    currHierarchy = ""
    for x in spltConf:
        currHierarchy += x
        if x not in currConf:
            if isinstance(currConf, list):
                # this is mostly for system.cpu* as system.cpu is an array
                if len(currConf) > 0 and isinstance(currConf[0], dict) and x not in currConf[0]:
                    print(f"***WARNING: {currHierarchy} does not exist in config***")
                    print("Current config structure:")
                    print(json.dumps(currConf, indent=2))
                    return 0
                elif isinstance(currConf[0], dict):
                    currConf = currConf[0][x]
                else:
                    print(f"***WARNING: {currHierarchy} does not exist in config***")
                    print("Current config structure:")
                    print(json.dumps(currConf, indent=2))
                    return 0
            else:
                print(f"***WARNING: {currHierarchy} does not exist in config***")
                print("Current config structure:")
                print(json.dumps(currConf, indent=2))
                return 0
        else:
            currConf = currConf[x]
            if currHierarchy == "system.cpu_clk_domain.clock":
                if isinstance(currConf, list) and len(currConf) > 0 and isinstance(currConf[0], (int, float)):
                    currConf = currConf[0] / 1000000000000.0
                else:
                    currConf = 0
        currHierarchy += "."
    return currConf

    

def readStatsFile(statsFile):
    global stats, period
    stats = {}
    period = 0
    if opts.verbose: print("Reading GEM5 stats from: %s" %  statsFile)
    with open(statsFile, 'r') as F:
        ignores = re.compile(r'^---|^$')
        statLine = re.compile(r'([a-zA-Z0-9_\.:+-]+)\s+([-+]?[0-9]+\.[0-9]+|[-+]?[0-9]+|nan|inf)')
        count = 0
        itr = 0
        for line in F:
            if not ignores.match(line):
                count += 1
                match = statLine.match(line)
                if match:
                    statKind = match.group(1)
                    statValue = match.group(2)
                    if statValue == 'nan':
                        statValue = '0.0'
                    if period not in stats:
                        stats[period] = {}
                    if not opts.periodic and statKind in stats[period]:
                        stats[period][statKind] = str(float(stats[period][statKind]) + float(statValue))
                    else:
                        stats[period][statKind] = statValue

            if "End Simulation Statistics" in line:
                if not opts.aggregate:
                    dumpMcpatOut(itr)
                    break
                if opts.periodic:
                    dumpMcpatOut(itr)
                    itr += 1
        if not opts.periodic:
            dumpMcpatOut(itr)

def readConfigFile(configFile):
    global config
    if opts.verbose: print("Reading config from: %s" % configFile)
    with open(configFile, 'r') as F:
        config = json.load(F)

def readMcpatFile(templateFile):
    global templateMcpat 
    if opts.verbose: print("Reading McPAT template from: %s" % templateFile)
    templateMcpat = parse(templateFile)

if __name__ == '__main__':
    main()