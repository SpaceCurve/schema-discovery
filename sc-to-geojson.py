#!/usr/bin/python

import os
import re
import sys
import csv

from optparse
import OptionParser

linecleaner = re.compile('\[\{.+\},(\{.+\})\]')

def parseargs():
    """ Parse command line arguments """
    parser = OptionParser()
    parser.add_option('-i', '--in', dest = "in_file", type = "string", default = None, help = "name of input file to process")
    parser.add_option('-o', '--out', dest = "out_file", type = "string", default = None, help = "name of output file to write")
    opt, arg = parser.parse_args()
    if not(opt.in_file or opt.out_file):
        print "Error: must specify an --in and an --out file"
        sys.exit(1)
    return opt, arg

if __name__ == "__main__":
    options, args = parseargs()
    infh = open(options.in_file, 'r')
    outfh = open(options.out_file, 'w')
    outfh.write('{"type": "FeatureCollection", "features": [\r\n')
    for line in infh.readlines():
        m = linecleaner.match(line)
        if m:
            templine = m.groups()[0]
        else:
            templine = line.rstrip()
        outfh.write(templine + ',\r\n')
    outfh.write('] }')
