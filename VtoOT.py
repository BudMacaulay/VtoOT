#!/usr/bin/env python3

import sys
from ase.io import read, write
import os, argparse, logging
import re
from mendeleev import element
from dir2cart import dir2cart
import json


# TODO - setup the arg parser - im way too lazy
# TODO - Do the math to convert poscars that are currently in Direct format immediately into Cartesian format
#  so you dont need a script before hand
# TODO - consider a better way to check for T/S's (perhaps some regex is needed.)
# TODO - Add a ngwf_num / ngwf_rad Auto filler just for convienience

def VtoOT(argv):
    """Converts a vasp POSCAR (including Ts/F's to a onetep xyz + a onetep dynblock (located in a file called [
    atomgeo]))  dyna ==True is not yet used and also it currently doesnt use.

    As of current please only use on files that are POSCARs
    that are Cartesian AND dynamic since i have no limitted error handling. It miiight work if its not dynamic
    in which it'll force all atoms to be so
    """
    ############################################ ARGUMENT PARSER #######################################################
    # Create the parser
    parser = argparse.ArgumentParser(description='A tool to create .dat files')

    # Add the arguments
    parser.add_argument("POSCARfile",
                        default="POSCAR", type=str,
                        help='Set input POSCAR file, Default POSCAR [in current dir.]')

    # Optional arguments
    parser.add_argument('-o', '--output',
                        dest="OUTdir",
                        help="The output directory -if none given defaults to the POSCAR directory")

    parser.add_argument('-c', '--config',
                        type=str, dest="CONfile",
                        help="Path to a .config file")

    parser.add_argument('-s', '--startdat',
                        type=str, dest="STARTdat",
                        help="Path to a starting .dat file [i.e jobtype/ENCUT etc]")

    # Execute the parse_args() method
    args = parser.parse_args()

    #  Setting args
    if args.POSCARfile.endswith("POSCAR"):
        print("READING POS")
        input_pos = args.POSCARfile
    else:
        print("ONLY POSCARS ALLOWED")
        exit()

    if args.CONfile:
        print("CONFIG json has been given")
        with open('VtoOTconf.json', 'r') as f:
            config2_dict = json.load(f)
    else:
        print("No CONFIG json - using defaults.")
        config2_dict = {"dynamic": False}  # Load an empty config (says "no settings - cause this is smart")

    if args.OUTdir:
        print("output directory detected dumping there")
        outputdir = args.OUTdir
    else:
        print("no output directory detected - dumping in POSCAR directory")
        outputdir = "/".join(sys.argv[1].split("/")[:-1])

    if args.STARTdat:
        print("Starting Dat wanted")
        initialdat = []
        with open(args.STARTdat, "r") as startdat:
            for line in startdat:
                initialdat.append(line)
    else:
        initialdat = []

    ############################################### END ARGUMENT PARSER ################################################


    # I do my own file parsing because im a masochist
    readlines = []
    with open(input_pos, "r") as inputpos:
        for line in inputpos:
            readlines.append(line)

    # Random saving of variables from the POSCAR cause i print out a lot at the moment.
    totnumb = readlines[6].split()
    numblist = [int(x) for x in totnumb]
    totnumb = sum(numblist)  # Total number of atoms.
    print(str(totnumb) + " ATOMS FOUND in POS")
    atomslist = readlines[5].split()  # Small list to iterate over and set right flags

    # Make the thing to iterate over.
    merged_list = [(atomslist[i], numblist[i]) for i in range(0, len(atomslist))]
    merged = [[x] * y for x,y in merged_list]
    merged = [val for sublist in merged for val in sublist]

    write(outputdir + "/ATOMsites.xyz", read(input_pos))  # Saves an XYZ quickly since its good to do so.
    # INITIAL CHECK - WILL REWORK TO DO MATH HERE AND AUTOCONV TO CART.
    if readlines[8].startswith("C") or readlines[8].startswith("c"):
        print("COOL. Read the input POSCAR as cartesian")
    else:
        print("Direct POSCAR found - This will break my parser if continued")
        if input("Shall i update your poscar to be cartesian? - THIS HAS NOT BEEN EXTENSIVE TESTED: Y/N").lower() == "y":
            dir2cart(input_pos)
            print("Poscar updated. - Check for POSCAR_cart in the submit directory")
            exit()
        else:
            exit()
            print("Poscar not updated. - Exiting now.")

    # FINAL CHECK HERE! - If there wasn't an "Selective dynamics line it'll do its best"
    if readlines[7].startswith("S") or readlines[7].startswith("s"):
        print("dynamic vasp system detected creating correct BLOCK SPECIES.")
    else:
        print("no dyn line found - doing the best i can - expect bigprintouts.")

    latticeblock = ['%BLOCK LATTICE_CART\n', 'ang\n']
    for i in range(0, 3):
        stringer = str(read(input_pos).cell.T[i].round(6))  # lattice dims
        for k in (('[', ''), (']', '')):
            stringer = stringer.replace(*k)
        latticeblock.append('  ' + stringer + '\n')
    latticeblock.append('%ENDBLOCK LATTICE_CART\n')

    posblock = []
    for i in readlines[-totnumb:]:  # This loop checks if each line ends in "T or F" pretty much
        if "T" in i[-10:]:
            posblock.append("_T {} \n".format(" ".join(i.split()[0:3])))
        elif "F" in i[-10:]:
            posblock.append("_F {}\n".format(" ".join(i.split()[0:3])))
        else:
            print("Line {} is not parsable, is there something other than F F F/T T T? at the end of the file")
            print("Saving as T anyway")
            posblock.append("_F {} \n".format(" ".join(i.split()[0:3])))

    posblock2 = [i + j for i, j in zip(merged, posblock)] #dumping back inside
    posblock2 = ['%BLOCK POSITIONS_ABS\n', 'ang\n', *posblock2, '%ENDBLOCK POSITIONS_ABS\n']

    # Two important blocks remain - The constraints and the species they are both similar so piled together
    allspecies = []
    for i in posblock2[2:-1]:
        allspecies.append(i[0:4].strip())  # Pull the first 4 letters(this is the upper limit for onetep labels anyway)
    allspecies = list(set(allspecies))  # The list of the set of all atoms observed in POSCAR
    speciesblock = ["%BLOCK SPECIES\n"]
    constblock = ["%BLOCK SPECIES_CONSTRAINTS\n"]
    for spec in allspecies:
        if "_T" in spec:
            constblock.append("{} NONE\n".format(spec))
        elif "_F" in spec:
            constblock.append("{} FIXED\n".format(spec))  #

        if config2_dict.get("Guess_NGWF") is True:  # As of current this does nothing. Will add a mini periodictable.
            speciesblock.append("{0} {1} {2} ngwf_num ngwf_rad\n".format(spec, spec[:-2],
                                                                         element(spec[:-2]).atomic_number))
        else:
            speciesblock.append("{0} {1} {2} ngwf_num ngwf_rad\n".format(spec, spec[:-2],
                                                                         element(spec[:-2]).atomic_number))

    speciesblock.append("%ENDBLOCK SPECIES\n")
    constblock.append("%ENDBLOCK SPECIES_CONSTRAINTS\n")

    completeblock = [latticeblock, "\n", speciesblock, "\n", constblock, "\n", posblock2]
    completeblock = [val for sublist in completeblock for val in sublist]

    # Checking JSON FLAGS FOR ADDITIONAL THINGS.
    if config2_dict.get("HubbardU") is True:
        print("HubbardU flag switched on saving a U block in the .dat")
        Ublock = ["%BLOCK HUBBARD\n"]
        if config2_dict.get("GuessHubbardU") is True:
            for el in allspecies:
                Ublock.append("{0} l^2 U(eV) J(eV) Z(-10) a(addforce) sig(spin)\n".format(el))
        else:
            for el in allspecies:
                Ublock.append("{0} l^2 U(eV) J(eV) Z(-10) a(addforce) sig(spin)\n".format(el))

        Ublock.append("%ENDBLOCK HUBBARD\n")
    else:
        Ublock = []  # too ensure no dead block is added

    completeblock = [initialdat, "\n", latticeblock, "\n", speciesblock, "\n",
                     constblock, "\n", Ublock, "\n", posblock2]
    completeblock = [val for sublist in completeblock for val in sublist]

    if config2_dict.get("dynamic") is False:
        print("Dynamic flag not switched on - making another simple dat file. ")
        posblock2_simp = [x.replace("T", "F") for x in posblock2]
        speciesblock_simp = [x for x in speciesblock if not re.search("_T", x)]  # Remove the T lines
        constblock_simp = [x for x in constblock if not re.search("_T", x)]  # Remove the T lines -
        Ublock_simp = [x for x in Ublock if not re.search("_T", x)]
        completeblock_simp = [latticeblock, "\n", speciesblock_simp, "\n", constblock_simp, "\n", Ublock_simp, "\n", posblock2_simp]
        completeblock_simp = [val for sublist in completeblock_simp for val in sublist]

        with open(outputdir + "/ATOMsites_noDYN.dat", "w+") as out:
            for line in completeblock_simp:
                out.write(line)

    with open(outputdir + "/ATOMsites.dat", "w+") as outfile:
        for line in completeblock:
            outfile.write(line)


if __name__ == "__main__":  # Parser testing.
    VtoOT(sys.argv[1:])

