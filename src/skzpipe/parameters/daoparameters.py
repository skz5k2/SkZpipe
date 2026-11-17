###daoparameters.py###
from .basicpar  import DAO_Par
#from .classes.fileclass.daofile   import *


###################
#DAOPHOT parameter#
###################
#DAO_Par={'_name_':'DAO_Par'}
DAO_Par['namemaxlen']=40;

#Header
DAO_Par['headerlen']=3;
DAO_Par['HeaderTxt']=" NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD\n";
DAO_Par['HeaderFormat']={'in':(int, int, int, float, float, float, float, float, float, float), 'out':"{:3d}{:6d}{:6d}{:8.1f}{:8.1f}{:8.3f}{:8.3f}{:8.3f}{:8.3f}{:8.3f}", 'split':(3,6,6,8,8,8,8,8,8,8), '#N':10};

#Files
DAO_Par['suffix']={'img':'.fits', 'src':'.coo', 'aph':'.ap', 'psfsrc':'.lst', 'psf':'.psf', 'fph':'.als', 'img:s':'s'};

DAO_Par['IdLen']= 7;
DAO_Par['IdTxt']= "{:7d}";
DAO_Par['DataLen']= 9;
DAO_Par['DataPrec']= 3;
DAO_Par['ErrPrec']= 4;
DAO_Par['DataTxt']= "{{:{:d}.{:d}f}}".format(DAO_Par['DataLen'],DAO_Par['DataPrec']);
DAO_Par['ErrTxt']= "{{:{:d}.{:d}f}}".format(DAO_Par['DataLen'],DAO_Par['ErrPrec']);
DAO_Par['DataErrTxt']=DAO_Par['DataTxt']+DAO_Par['ErrTxt'];
DAO_Par['LineLen']= 300;
DAO_Par['ApNum']=12;




DAO_Par['maxskyarea']=10000;
#"the maximum number of pixels that will be used in any sky determination" (from daophot.f)


DAO_Par['alfmaxosrad']=50;
DAO_Par['allframebackupext']=".bck";

#PSF
DAO_Par['psfheader']=2;
#the number of lines of the header of .psf file

DAO_Par['maxpsfrad']=51;
#"the largest acceptable PSF radius" (from allstar.f and daophot.f from MAXPSF=207=2*[2*PSFMAX+1]+1)

#list of anal type used by daophot. (See in mathsub.f)
DAO_Par['psfanaltypeL']=["",   #first must be empty so the first has index 1
                 "GAUSSIAN",
                 "MOFFAT15",
                 "MOFFAT25",
                 "MOFFAT35",
                 "LORENTZ",
                 "PENNY1",
                 "PENNY2"];
DAO_Par['psfanaltype']=dict(zip( DAO_Par['psfanaltypeL'], range(len(DAO_Par['psfanaltypeL'])) ))
DAO_Par['psfanaltype']["ALLPSF"]=-len(DAO_Par['psfanaltypeL'])+1;   #option for the search of the best fit trying all the type.

DAO_Par['psfpattWi']=[r"*", r"?", r"#"];
#patterns used to mark problematic sources (Wi=with chi square value, Wo=without it)

DAO_Par['psfpattWo']=["saturated", "defective", r"\*\*\*\*\*\*\* \*"];
#see psf.f  Remember to put the double\ before symbols

DAO_Par['permittedoptionvalue']={'daophot':{'RE':(1.e-30, 1.e30), 'GA':(1.e-30, 1.e30),  'LO':(0, 1.e30), 'HI':(0, 9999999),  'FW':(0.2, 35), 'TH':(0, 1.e30),  'LS':(0, 1), 'HS':(0.6, 2.),  'LR':(-2, 0.), 'HR':(0, 2.),  'WA':(-3, 3.), 'FI':(1., 30.), 'PS':(.5, DAO_Par['maxpsfrad']), 'VA':(-1.5, 3.5),  'SK':(-0.5, 3.5),  'AN':(-7.49, 7.49), 'EX':(0., 9.5), 'US':(0., 1.),  'PE':(0., 100), 'PR':(0., 100)},
                                    'photo':{'A1':(1.e-30, 1.e30), 'A2':(0., 1.e30), 'A3':(0., 1.e30), 'A4':(0., 1.e30), 'A5':(0., 1.e30), 'A6':(0., 1.e30), 'A7':(0., 1.e30), 'A8':(0., 1.e30), 'A9':(0., 1.e30), 'AA':(0., 1.e30), 'AB':(0., 1.e30), 'AC':(0., 1.e30), 'IS':(0., 1.e30), 'OS':(1., 1.e30)},
                                    'allstar':{'FI':(1.0, 31.0), 'CE':(0.0, 8.0), 'RE':(0.0, 1.0), 'CR':(0.0, 10.), 'WA':(0.0, 2.0), 'MA':(1.0, 100), 'PE':(0.0, 100), 'PR':(0.0, 100), 'IS':(0.0, 35), 'OS':(0.0, 100)},
                                    'allframe':{},
   };


#option for daomatch/daomaster to filter according data in columns: symbol:n_col in als/alf files (1..9)
DAO_Par['DMT_Opt1']={'<':4, '|':5, '%':8, '[':9, 'mag':4, 'emag':5, 'chi2':8, 'sharp':9};  ##'%<[|*'; 
#options ['all', 'flag', 'with optional value', 'with value']
DAO_Par['DMT_OptN']=[';/', ';', '/', ''];    ##'!*;/^'; 

DAO_Par['DMSext1']=[".mag",".cor",".raw",".mch",".tfr"];  DAO_Par['_doc_']['DMSext1']="""Extensions of the DAOmaster global output""";
DAO_Par['DMSext1Flg']=[True, True, True, True, False];    DAO_Par['_doc_']['DMSext1Flg']="""Flag about the presence of the DAOmaster global output""";
DAO_Par['DMSext2']=[".coo",".mtr"];                       DAO_Par['_doc_']['DMSext2']="""Extensions of the DAOmaster frame output""";
DAO_Par['DMSext2Flg']=[True, False];                      DAO_Par['_doc_']['DMSext2Flg']="""Flag about the presence of the DAOmaster frame output""";
DAO_Par['DMSoutput']=['reid']+[x[1:] for x in DAO_Par['DMSext1']+DAO_Par['DMSext2']];  DAO_Par['_doc_']['DMSoutput']="""ID of the DAOmaster output""";

#Montage2
DAO_Par['montage2fill']=1e19;

