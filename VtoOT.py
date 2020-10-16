#!/usr/bin/env python3

import sys
from ase.io import read, write
import os, argparse, logging


def VtoOT(input_pos, outputdir):
    """Converts a vasp POSCAR (including Ts/F's to a onetep xyz + a onetep dynblock (located in a file called [
    atomgeo]))  dyna ==True is not yet used and also it currently doesnt use.

    As of current please only use on files that are POSCARs that are direct AND dynamic since i have no error handling.
    """


    #-------------------------------------------------------------------------------
    # Argument parser
    #-------------------------------------------------------------------------------
    #parser = argparse.ArgumentParser(description=vtoOT.__doc__,
    #                                 epilog="BM151020")
    # Positional arguments
    #parser.add_argument('inputpos',
    #                    default="POSCAR",
    #                    type=str, nargs='?',
    #                    help='set input POSCAR. Default is the one in this directory;')
    # Optional args
    #parser.add_argument('--output',
    #                    type=str,
    #                    action="store_true", dest=outputdir,
    #                    help='set an outputdirectory. Default is here too probably')

    #args = parser.parse_args(argv)

    listofchanged = []
    if input_pos.endswith("POSCAR"):
        print("READING POS")
    else:
        print("ONLY POSCARS ALLOWED")
        exit()

    AS = read(input_pos)
    write(outputdir + "/ATOMsites.xyz",read(input_pos)) # Saves an XYZ quickly since its good to do so.

    # A block that converts the XYZ of a vasp POSCAR into a onetep block. This WORKS!
    latticeblock = ['%BLOCK LATTICE_CART\n', 'ang\n']
    for i in range(0, 3):
        stringer = str(read(input_pos).cell.T[i])  # lattice dims
        for k in (('[', ''), (']', '')):
            stringer = stringer.replace(*k)
        latticeblock.append('  ' + stringer + '\n')
    latticeblock.append('%ENDBLOCK LATTICE_CART\n')


    # A block that reads the input_pos and converts the atoms with T/F into the correct format.
    dynablock = ['BLOCK SPECIES_CONSTRAINTS\n']
    readlines = []
    with open(input_pos, "r") as inputpos:
        for line in inputpos:
            readlines.append(line)
    if readlines[7].startswith("S") or readlines[7].startswith("s"):
        print("dynamic vasp system detected creating correct BLOCK SPECIES.")

    totnumb = readlines[6].split()
    totnumb = [int(x) for x in totnumb]
    totnumb = sum(totnumb)

    print(str(totnumb) + " ATOMS FOUND in POS")
    atomslist = readlines[5].split()

    posblock = []
    for i in readlines[-totnumb:]: # This loop checks if each line ends in "T or F" pretty much:wq
        if "T" in i[-10:]:
            posblock.append("_T {} \n".format(i[:-7]))
        elif "F"in i[-10:]:
            posblock.append("_F {}".format(i[:-7]))
        else:
            print("Line {} is not parsable, is there something other than F F F/T T T? at the end of the file")
            print("Saving as T anyway")
            posblock.append("_F {} \n".format(i[:-7]))

    posblock2 = []
    for i in range(0,len(atomslist)):
        print(i)
        for line in posblock:
            posblock2.append(atomslist[i] + line)

    if readlines[8].startswith("C") or readlines[8].startswith("c"):
        posblock2 = ['%BLOCK POSITIONS_ABS\n', 'ang\n', *posblock2, '%ENDBLOCK POSITIONS_ABS\n']
    else:
        print(" ENSURE LINE 8 is 'CARTESIAN' and atom co-ords are too!")
        exit()

    completeblock = [latticeblock, "\n", posblock2]
    completeblock = [val for sublist in completeblock for val in sublist]

    with open(outputdir + "/ATOMsites.dat", "w+") as outfile:
        for line in completeblock:
            outfile.write(line)


if __name__ == "__main__": #Stuff below here is here until I can come up with an adequate parser
    if len(sys.argv) == 2:
        VtoOT(input_pos=sys.argv[1], outputdir="/".join(sys.argv[1].split("/")[:-1]))

    elif len(sys.argv) == 3:
        VtoOT(input_pos=sys.argv[1], outputdir=sys.argv[2]):