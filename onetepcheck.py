#!/usr/bin/env python3

import os
import sys
import argparse
from collections import Counter


def onetepcheck(file):
    """ Reads said dat file and determines if the neccessary things that are required for the onetep calc to run are present.
    Checks: NGWF < SIMCELL, Task, Lattice, species, species_pot, if file 'includefile' exists.
    """

    if "/" in file:
        os.chdir("./".join(file.split("/")[:-1]))  # dir change and reinit variable
        file = file.split("/")[-1]
        print('*DEBUG* location of dat file : ' + os.getcwd())
    else:
        print("*DEBUG* .dat in current dir")
    specs = []
    datlist = []
    lc = []
    with open(file, "r") as f:
        for line in f:
            datlist.append(line)

    # Check if 'task' exists and its type
    print('\n----------- Checking task type -----------\n')
    v = [s.split()[-1] for s in datlist if "task" in s]
    if len(v) > 1:
        print("\tMULTIPLE TASK LINES CHECK .DAT")

    elif len(v) == 0:
        print("\tNO TASK LINE - ONETEP DEFAULTS TO SINGLEPOINT")
    else:
        if v[0].upper() in 'SINGLEPOINT, COND ' ', PROPERTIES , PROPERTIES_COND ' ', GEOMETRYOPTIMIZATION ,' \
                           ' MOLECULARDYNAMICS ,TRANSITIONSTATESEARCH, PHONON':
            print("\t{} ✔".format(v[0].upper()))
        else:
            print("\tWARNING - TASK TYPE {} NOT FOUND - CHECK FOR TYPOS".format(v[0].upper()))
    v = [s for s in datlist if "cutoff_energy" in s][0]
    t_num = str([int(s) for s in v.split() if s.isdigit()][0])
    t_unit = v[v.index(t_num) + len(t_num):]

    print("\n--------- Checking cutoff energy ---------\n")
    s = "\tcutoff energy of {} {} found ✔".format(t_num.strip(), t_unit.strip())
    if t_unit.upper().strip() == "EV":
        if int(t_num) > 300:
            print(s)
        else:
            print(s[:-1] + " care this is quite small ✕")
    elif t_unit.upper().strip() == "HA":
        if int(t_num) > 11:
            print(s)
        else:
            print(s[:-1] + " care this is quite small ✕")
    else:
        print("\tWARNING unrecognised unit - {}, assume you know what you're doing".format(t_unit.strip()))

    l_ = [x.lower() for x in datlist]
    test = '%block lattice_cart\n'.lower()
    test_end = '%endblock lattice_cart\n'.lower()
    if test in [x.lower() for x in datlist]:
        print('\tlattice cart block found ✔')
        lc = datlist[l_.index(test.lower()):l_.index(test_end.lower()) + 1]
        bignum = []
        for i in lc[-4:-1]:
            l2 = [float(x) for x in i.split()]
            l2.sort()
            bignum.append(l2[-1])
        if str(lc[1]).startswith('a'):
            print("\tlattice block is in angstrom form.")
            maxbohr = round(min(bignum))
        else:
            print("\tlattice block is in bohr form")
            maxbohr = round(min(bignum) * 0.4)
    else:
        print("WARNING BLOCK LATTICE CART NOT FOUND ✕")
        maxbohr = 0

    test = '%block species\n'.lower()
    test_end = '%endblock species\n'.lower()
    if test in [x.lower() for x in datlist]:
        lc = datlist[l_.index(test.lower()) + 1:l_.index(test_end.lower())]
        t = [x.split() for x in lc]
        specs = []
        for i in t:
            specs.append(i[0])
            if len(i) != 5:
                print(" ".join(i))
                print(" WARNING THIS SPECIES doesnt have 5 inputs - check docs ✕")
                if float(i[4]) > maxbohr:
                    print(
                        "WARNING THIS SPECIES LINE [{}] may be too large for the simulation cell ✕".format(" ".join(i)))

    test = '%block species_pot\n'.lower()
    test_end = '%endblock species_pot\n'.lower()
    if test in [x.lower() for x in datlist]:
        lc = datlist[l_.index(test.lower()) + 1:l_.index(test_end.lower())]
    # TODO Check the file exists
    filelocations = []
    for i in lc:
        filelocations.append(i.split()[1])
        specs.append(i.split()[0])
    a = dict(Counter(specs))

    for i in a.items():
        if i[1] != 2:
            print("WARNING ELEMENT {} MAY NOT BE PRESENT IN SPECIES AND SPECIES_POT  ✕".format(i[0]))

    test = '%block positions_abs\n'.lower()
    test_end = '%endblock positions_abs\n'.lower()
    if test in [x.lower() for x in datlist]:
        print("\tBlock positions found ✔")
        lc = datlist[l_.index(test.lower()) + 1:l_.index(test_end.lower())]
        for i in lc:
            if i.startswith("includefile"):
                filelocations.append(i.split()[1])
    else:
        print("\tWARNING NO BLOCK POSITIONS_ABS FOUND ✕")

    print("\n---------- Checking files exist ----------\n")
    for i in filelocations:
        try:
            f = open(i.replace('"', ''))
            # Do something with the file
            print("\tFile {} found ✔".format(i))
        except IOError:
            print("\tFile {} NOT FOUND ✕".format(i))
        finally:
            f.close()

    print("\n-------------- Exiting  now --------------\n")


if __name__ == "__main__":
    onetepcheck(sys.argv[1])
