# VtoOT

A Small Tool to convert vasp POSCARs into a ONETEP ready .dat file (posblock e.t.c) Where the user can then attach the new upto dat positions onto a starting .dat file with the calculation details.

## TODO:
1. Actually get some information on what the "Guesses" should be and save in a seperate .json for initialisation. Would save me alot of time. 
As of current the [config.json flags "Guess{flag} do nothing]
2. Incorp the parser directly as variables cause atm it's a bit silly but working.


## Prerequisites:
1. This full directory (since dir2cart is used on POSCAR files to convert them to "cartesian mode" since that's the most common way POSCAR's are saved)
2. Mendeleev: `pip install mendeleev`
3. ASE: `pip install ase`



## Features:
1. Reads a POSCAR (in direct mode) and makes an .xyz and .dat file for you
2. If in direct mode offers a method to convert into a cartesian format for you. (Using previously written dir2cart [ I WROTE THIS A WHILE AGO TEST IT FIRST ])
3. Can be used alongside a .json file to further tailor the print out information. (Check the json for a list of possible tailored style)
4. If using the "Guess modes" there is a pre-written Guess.json file which I added some common elements that you may use and their expected NGWF Numbers / Radii. ( This is mostly based on 0 knowledge so if you KNOW it to be wrong just change the json and tell me)
5. If used outside of "Guess mode" It'll instead not guess and just print some information in the relevant blocks. 
6. Will output to a target directory 

-----
## Usage:
`VtoOT.py [INPUT_POSCAR]`

outputs an .xyz and a .dat into the same directory as the INPUT_POSCAR

`VtoOT.py [INPUT_POSCAR] -o [OUTPUT_DIRECTORY]`

outputs an .xyz and a .dat into the directory OUTPUT_DIRECTORY

`vtoOT.py [INPUT_POSCAR] -c [JSON FILE]` 
outputs an .xyz and a .dat into the directory stated.


If you have any issues do let me know it should be simple-ish. 
