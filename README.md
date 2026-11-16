
---------------------------
Needed packages for skzpipe
---------------------------
python3
python3-numpy
python3-astropy
python3-setuptools
python3-dev


------------
 To install 
------------
#Create the destination directories (optional)
mkdir $HOME/usr/pythonlib/ $HOME/usr/pythonscript

#in .bashrc:
#add the path for python
export PYTHONPATH="$HOME/usr/pythonlib/"

#add the script directory in PATH
export PATH="$HOME/usr/pythonscript/:$PATH"
#or
if [ -d "~/usr/pythonscript" ] ; then
    echo $PATH | /bin/egrep -q "~/usr/pythonscript" || PATH="~/usr/pythonscript:${PATH}"
fi

python3 ./setup.py install --install-lib ~/usr/pythonlib/ --install-scripts ~/usr/pythonscript


---------------------------
Needed packages for DAOPhot
---------------------------

make
libcfitsio-dev
gfortran

If using the LaPack version (when available)
lapack-dev
liblapack3
liblapacke-dev

------------------------------
Needed changes in DAOphot code
------------------------------

fotometry.f
-----------
A little change with importante effect: the warning message that a star in the ?Star ID file? is not listed in the PSF-fitting photometry file is now shown as the other messages, only for WATCH>0.5
This
      if (watch .GT. 0.5) then
        WRITE (LINE,666) ID
 666    FORMAT ('Star not found in input:', I7)
        CALL STUPID (LINE)
      end if

instead of

      WRITE (LINE,666) ID
 666  FORMAT ('Star not found in input:', I7)
      CALL STUPID (LINE)

This change reduces significantly the output of the command (that can reach several megabytes in several cases: I got a 10MiB output, once). And the message is not so relevant, actually: it is quite common that a .coo file has more sources than a .als, especially when allstar run on .nei file, instead of .ap one.


daomaster95.f
-------------
A little change with importante effect: comment out the " call rdchar" triggered by pause variable after 666 tag, that ask for pressing enter a case-dependant number of time.  This causes problems during the use of daomaster through scripts (and also it is quite annoying to press enter so many times, when you have a lot of frame).


---------
Bug fixes
---------

allframe95.f
-----------
The MODE array must have dimension maxpic, and no more maxpic/3 (line 79). When the backup is read and written the code iterates over 3*npic=maxpic (lines 198-199 and 2304-2305), causing a buffer-overflow, dangerous in the case of writing in a variable (since it changes values in part of the memory where it should not).

C%      INTEGER NOUT(MAXPIC/3), WROTE(MAXPIC/3), MODE(MAXPIC/3)
      INTEGER NOUT(MAXPIC/3), WROTE(MAXPIC/3), MODE(MAXPIC)


daomaster95.f
-------------
at original line 1296
Errata:
      IF (III .EQ. 4) THEN
        CON(5,I) = -FLIP(I)*CON(4,I)
        CON(6,I) = FLIP(I)*CON(3,I)
      END IF
The I is an error: it should be IFRM. The variable I was precedently used in a DO I=1,III 
Corrige:
      IF (III .EQ. 4) THEN
        CON(5,IFRM) = -FLIP(IFRM)*CON(4,IFRM)
        CON(6,IFRM) = FLIP(IFRM)*CON(3,IFRM)
      END IF

mathsubs.f
----------
suroutine MMM
During error management it is not considered the specific case MAXIMM-MINIMM==0 (just if MAXIMM-MINIMM<MINSKY), that cause several variables to be NaN.
At the exit at label 9900 (for error) I have fixed it adding a NaN check to the output variables SKYMN, SKYMED, SKYMOD and if they are NaN, they are  set to -9990.999 (value chosen as default wrong value).

C
C-----------------------------------------------------------------------
C
C An error condition has been detected.
C
 9900 SIGMA=-1.0
      SKEW=0.0
      if(isnan(skymn))  skymn =-9990.999
      if(isnan(skymed)) skymed=-9990.999
      if(isnan(skymod)) skymod=-9990.999


It is a good idea also to add at the beginning an initialization for the output variables SKYMN, SKYMED, SKYMOD, SIGMA, SKEW helps to avoid anomalous output values in some seldom occasions. The values for SIGMA and SKEW are the same ones used when an error condition is detected; the value for SKYMOD is made up according the output format 

C% Default initialization, to avoid random output values
      SKYMN=-9990.999
      SKYMED=-9990.999
      SKYMOD=-9990.999
      SIGMA=-1.0
      SKEW=0.0
