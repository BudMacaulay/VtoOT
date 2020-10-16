#!/usr/bin/env python3

import sys
from ase.io import read, write
import os, argparse, logging
import re
from ase import atoms
from mendeleev import element


def VtoOT(input_pos, outputdir):
    """Converts a vasp POSCAR (including Ts/F's to a onetep xyz + a onetep dynblock (located in a file called [
    atomgeo]))  dyna ==True is not yet used and also it currently doesnt use.

    As of current please only use on files that are POSCARs
    that are Cartesian AND dynamic since i have no limitted error handling. It miiight work if its not dynamic
    in which it'll force all atoms to be so
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

    # I do my own file parsing because im a masochist
    readlines = []
    with open(input_pos, "r") as inputpos:
        for line in inputpos:
            readlines.append(line)

    totnumb = readlines[6].split()
    totnumb = [int(x) for x in totnumb]
    totnumb = sum(totnumb) # Total number of atoms.
    print(str(totnumb) + " ATOMS FOUND in POS")
    atomslist = readlines[5].split() # Small list to iterate over and set right flags
    write(outputdir + "/ATOMsites.xyz",read(input_pos)) # Saves an XYZ quickly since its good to do so.

    # INITIAL CHECK - WILL REWORK TO DO MATH HERE AND AUTOCONV TO CART.
    if readlines[8].startswith("C") or readlines[8].startswith("c"):
        print("COOL")
    else:
        print(" ENSURE LINE 8 is 'CARTESIAN' and atom co-ords are too!")
        #exit()


    # FINAL CHECK HERE! - If there wasn't an "Selective dynamics line it'll do its best"
    if readlines[7].startswith("S") or readlines[7].startswith("s"):
        print("dynamic vasp system detected creating correct BLOCK SPECIES.")
    else:
        print("no dyn line found - doing the best i can - expect bigprintouts.")


    latticeblock = ['%BLOCK LATTICE_CART\n', 'ang\n']
    for i in range(0, 3):
        stringer = str(read(input_pos).cell.T[i])  # lattice dims
        for k in (('[', ''), (']', '')):
            stringer = stringer.replace(*k)
        latticeblock.append('  ' + stringer + '\n')
    latticeblock.append('%ENDBLOCK LATTICE_CART\n')


    posblock = []
    for i in readlines[-totnumb:]: # This loop checks if each line ends in "T or F" pretty much
        if "T" in i[-10:]:
            posblock.append("_T {} \n".format(" ".join(i.split()[0:3])))
        elif "F" in i[-10:]:
            posblock.append("_F {}\n".format(" ".join(i.split()[0:3])))
        else:
            print("Line {} is not parsable, is there something other than F F F/T T T? at the end of the file")
            print("Saving as T anyway")
            posblock.append("_F {} \n".format(i[:-7]))

    posblock2 = []
    for i in range(0, len(atomslist)):
        for line in posblock:
            posblock2.append(atomslist[i] + line)

    posblock2 = ['%BLOCK POSITIONS_ABS\n', 'ang\n', *posblock2, '%ENDBLOCK POSITIONS_ABS\n']


    # Two important blocks remain - The constraints and the species they are both similar so piled together
    allspecies = []
    for i in posblock2[2:-1]:
        allspecies.append(i[0:4].strip()) # Pull the first 4 letters(this is the upper limit for onetep labels anyway)
    allspecies = list(set(allspecies)) # The list of the set of all atoms observed in POSCAR
    speciesblock = ["%BLOCK SPECIES\n"]
    constblock = ["%BLOCK SPECIES_CONSTRAINTS\n"]
    for spec in allspecies:
        if "_T" in spec:
            constblock.append("{} NONE\n".format(spec))
        elif "_F" in spec:
            constblock.append("{} FIXED\n".format(spec))
        speciesblock.append("{0} {1} {2} ngwf_num ngwf_rad\n".format(spec, spec[:-2], element(spec[:-2]).atomic_number)) # I have a mini json file that will strip atom numbers e.t.c.

    speciesblock.append("%ENDBLOCK SPECIES\n")
    constblock.append("%ENDBLOCK SPECIES_CONSTRAINTS\n")

    completeblock = [latticeblock, "\n", speciesblock, "\n", constblock, "\n", posblock2]
    completeblock = [val for sublist in completeblock for val in sublist]



    with open(outputdir + "/ATOMsites.dat", "w+") as outfile:
        for line in completeblock:
            outfile.write(line)


if __name__ == "__main__": #Stuff below here is here until I can come up with an adequate parser
    if len(sys.argv) == 2:
        VtoOT(input_pos=sys.argv[1], outputdir="/".join(sys.argv[1].split("/")[:-1]))

    elif len(sys.argv) == 3:
        VtoOT(input_pos=sys.argv[1], outputdir=sys.argv[2])