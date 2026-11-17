"""Module with definitions of the basic paramenters of the packege and the funtions to manage them.
"""

import os, re, collections, sys, time
from copy import deepcopy

from ..exceptions import *

########################
##  READING FUNCTIONS ##
########################
def RF_dict_obj(txt='', vobj=str, kobj=str):
    tmpd=dict( tuple(y.split(':')) for y in re.split(";|,",txt) );
    retd={};
    for key,val in tmpd.items():
        retd[kobj(key)]=vobj(val);
    return retd;

def isnumber(x):
    try:
        float(x);
        return True;
    except (ValueError,TypeError):
        return False;


_default_hardreset_=None

##################
##  PARAMETERS  ##
##################
#Declarations
SkZp_Par={'_name_':'SkZp_Par'};   SkZp_Par['_doc_']={'_name_':'SkZp_Par:_doc_'};
#SkZp_ParDef={'_name_':'SkZp_ParDef'}; SkZp_ParDef['_doc_']={'_name_':'SkZp_ParDef:_doc_'}; 
#SkZp_ParTxT={'_name_':'SkZp_ParTxT'}; SkZp_ParTxT['_doc_']={'_name_':'SkZp_ParTxT:_doc_'}; 

SkZp_Par['_skeys_']=['_funct_', '_name_', '_doc_', '_keys_', '_type_', '_list_'];


DAO_Par={'_name_':'DAO_Par'};  DAO_Par['_doc_']={'_name_':'DAO_Par:_doc_'};
DAO_Par['_skeys_']=SkZp_Par['_skeys_'].copy()


#LIST OF PARAMETERS :: REMENBER TO UPDATE IT WHAN ADDING A NEW PARAMETER
SkZp_Par['_list_']=['datatag0', 'datatag0missing', 'def:datatag', 'datatag', 'datatagtype', 
        'entrytypelist', 'inputdata', 'def:dataframe', 'inputlist', 'runlist', 'inputfiles', 'initializingflag', 'instruments', 
        #'select', 'extractkey', 
        'stdout', 'stderr', 'ramfolder',
        'saferunbit', 'script', 'counter', 'store4later', 
        'optfilenames', 'optfilelist', 'optfiledata', 'optfile', 
        'errorlist', 'errorhistory', 
        'mp:nproc', 'mp:availmemfrac', 
        'FITSextension', 'image_extension', 'mosaic_extension', 'chipheaderext', 'mosheaderext', 
        'charconversion', 'commentpattern', 'headerfilepattern', 'maxnamelength',
        'checksleepbreak', 'runtimewarn', 'timeout', 
        'photo:StepL', 'photo:Steps', 'photo:runtypelist', 'photo:hgdcorrection', 'stdfield', 'stdstar', 
        'sourcesperpixel',
        ]

#####
#####
def ParameterCheck(paramdb=None):
    """Check for integrity and correct setting of parameters.
  
Parameters
----------
    paramdb : as SkZp_Par
        Database of the parameters. Default SkZp_Par
  """
    _name_='ParameterCheck'
    if(paramdb is None): paramdb=SkZp_Par
    if('fitsextension' in paramdb and not paramdb['fitsextension'].startswith('.')): 
        raise SkZpipeError("it has to start with a dot '.'.", exclocus="parameter 'fitsextension'")
    if('chipheaderext' in paramdb and not paramdb['chipheaderext'].startswith('.')): 
        raise SkZpipeError("it has to start with a dot '.'.", exclocus="parameter 'chipheaderext'")
    if('mosheaderext'  in paramdb and not paramdb['mosheaderext'].startswith('.')):  
        raise SkZpipeError("it has to start with a dot '.'.", exclocus="parameter 'mosheaderext'")
    if('photo:hgdcorrection' in paramdb): 
        if(not isinstance(paramdb['photo:hgdcorrection'], float) or paramdb['photo:hgdcorrection']>1  or paramdb['photo:hgdcorrection']<=0.1):
            raise SkZpipeError("it has to be a float greater than 0.1 and less or equal to 1.", exclocus="parameter 'photo:hgdcorrection'")
        if(paramdb['photo:hgdcorrection']<=0.5): print("!!!WARNING!!! Parameter 'photo:hgdcorrection' is less than 0.5")
    if('sourcesperpixel' in paramdb and ( not isinstance(paramdb['sourcesperpixel'], float) or paramdb['sourcesperpixel']>0.25) ):
        raise SkZpipeError("it is the number of sources per pixel square. It should be less than 1/2^2 to be reasonable.", exclocus="parameter 'sourcesperpixel'")

#####
def ParameterList(paramdb=None, viewer=None):
    """Return a text list of all the paramenters and their descriptions (mainly it uses a internal list).
  
Parameters
----------
    paramdb : as SkZp_Par
        Database of the parameters. Default SkZp_Par
    viewer ; str or None
        How to visualize the information. None (default) or 'pager' to use the pager (from pydoc.pager),
        'print' to use built-in function print, 'return' to return the text.
"""
    _name_='ParameterList'
    from pydoc import pager
    if(paramdb is None): paramdb=SkZp_Par
    outxt=""
    paramL=paramdb.get('_list_')
    if(not paramL):
        paramL=[x for x in paramdb if(x not in paramdb['_skeys_'] or not x.startswith('_'))]
    for par in paramL:
        if(par.startswith('_')): continue
        outxt+=f"{'-'*len(par)}\n{par}\n"
        if(par in paramdb['_doc_']): outxt+='\t'+paramdb['_doc_'][par]+'\n'
        outxt+=f'==>{paramdb[par]}\n\n'
  
    if(viewer is None or viewer=='pager'):
        pager(outxt);
    elif(viewer=='print'):
        print(outxt)
    elif(viewer=='return'): 
        return outxt
    else: raise ValueError(_name_+": wrong value for `viewer` (None/'pager', 'print', or 'return')")
  
#####
def ParameterHelp(param=None, viewer=None, paramdb=None):
    """Return info about paramenters
  
Parameters
----------
    param : str
        Name of the parameter
    viewer ; str or None
        How to visualize the information. None (default) or 'pager' to use the pager (from pydoc.pager),
        'print' to use built-in function print, 'return' to return the text.
    paramdb : as SkZp_Par
        Database of the parameters. Default SkZp_Par

"""
    _name_='ParameterHelp'
    from pydoc import pager
    if(paramdb is None): paramdb=SkZp_Par
    outxt=''
    if(param in paramdb):
        if(param.startswith('_')):
            outxt=f"{param} : special key for the parameter database, not a parameter"
        else:
            outxt=f"{param}" +(f" \t  {paramdb['_doc_'].get(param)}"if('_doc_' in paramdb)else '')+'\n'
            outxt+=f"=>{paramdb[param]}\n"
  
    if(viewer is None or viewer=='pager'):
        pager(outxt);
    elif(viewer=='print'):
        print(outxt)
    elif(viewer=='return'): 
        return outxt
    else: raise ValueError(_name_+": wrong value for `viewer` (None/'pager', 'print', or 'return')")
   
  #####
def ParameterSet(param=None, value=None, paramdb=None):
    """Return info about paramenters
  
Parameters
----------
    param : str, dict
        Name of the parameter. Or a dictionary as {'param':value}
    value ; str or None
        Value for the parameter
    paramdb : as SkZp_Par
        Database of the parameters. Default (None) SkZp_Par; 'DAO' for DAOPhot parameters

"""
    _name_='ParameterSet'
    if(paramdb is None): paramdb=SkZp_Par
    elif(isinstance(paramdb, str)):
        if('DAO' in paramdb.upper()): paramdb=DAO_Par
        else: raise SkZpipeError(f"Wrong ID for parameter database <{paramdb}>", exclocus=_name_)
    else: raise SkZpipeError(f"Wrong parameter database <{paramdb}>", exclocus=_name_)
  
    if(isinstance(param, str) ): param={param:value}
    if(not isinstance(param, dict) ): raise TypeError(f"{_name_}: `param` must be a string or a dictionary <{param.__class__}>")
    notp=set(param)-set(paramdb)
    if(notp): raise SkZpipeError(f"Parameters {notp} don't exist", exclocus=_name_)
    for par,value in param.items():
        if(par in ('stdout', 'stderr')):
            if(any(not hasattr(value, x) for x in ('write','flush') )): #check if new value has the neeeded attributes
                raise SkZpipeError(f"parameter '{par}' has wrong type <{value.__class__}>. It should have a 'write' and 'flush' attribute", exclocus=_name_)
        elif(not isinstance(value, paramdb[par].__class__)): 
            raise SkZpipeError(f"parameter '{par}' has wrong type <{value.__class__}>. It should be {paramdb[par].__class__}", exclocus=_name_)
        else:
            param[par]=deepcopy(value)
    ParameterCheck(param)
    paramdb.update(param)

      

#########################


#Definitions

SkZp_Par['datatag0']=['NAME', 'FWHM', 'ENTRYTYPE'];   SkZp_Par['_doc_']['datatag0']="Fundamental tags" 
SkZp_Par['datatag0missing']=set();                    SkZp_Par['_doc_']['datatag0missing']="Fundamental tags that are missing" ##@@ ????? It is needed?
SkZp_Par['def:datatag']=SkZp_Par['datatag0']+['HIGH', 'GAIN', 'RON', 'CHIP', 'EXPTIME', 'FILTER', 'PSFFWHM', 'PSFELLIP', 'AIRMASS', 'SKY', 'MJD', 'NIGHT', 'DATE', 'TIME', 'RA', 'DEC', 'OBJECT', 'INSTRUMENT', 'MAGZPT', 'NX', 'NY', 'BITPIX', 'EXPID', 'IMGQUAL', 'OBSSET', 'SCALE', 'TELESCOPE', 'SITENAME', 'SITEALT', 'SITELAT', 'SITELONG', 'EQUINOX', 'STKOFF', 'AV,SM', 'DATASEC', 'OVERSCAN', 'IMGSTAT', 'APCORR', 'SKZP_FLG'];

#list of tag of data and documentation (description of each one)
SkZp_Par['datatag']=[];    SkZp_Par['_doc_']['datatag']="""List of tag used in 'inputdata'
  Usable tags:
Mandatory:
  NAME       = name of the image witout extension .fits (This has to be present)
  FWHM       = seeing/fwhm (This has to be present)
  ENTRYTYPE  = type of the entry ( see parameter 'entrytypelist')
Following:
  HIGH       = High Good Datum
  GAIN       = gain
  RON        = read-out noise in e-
  CHIP       = number of the sensor
  EXPTIME    = exposure time in sec
  FILTER     = filter
  PSFFWHM    = FWHM measured with PSF calculation
  PSFELLIP   = Ellipticity (1-b/a) measured with PSF calculation
  AIRMASS    = airmass
  SKY        = Sky level
  MJD        = Julian date
  NIGHT      = number of observation night
  DATE       = observation date
  TIME       = observation time
  RA         = right ascension of the pointing
  DEC        = declination of the pointing
  OBJECT     = Description of the observation, object of the observation (check to remove the filter name, since it is stored with its tag)
  INSTRUMENT = instrument used
  MAGZPT     = magnitude zero point
  NX         = number of columns (FITS header)
  NY         = number of rows (FITS header)
  BITPIX     = Bitpix of the image (FITS header)
  EXPID      = identification of the exposure
  IMGQUAL    = quality of the image
  OBSSET     = Name of the set of observation (some observations are subgrouped in subset, like VVV)
  SCALE      = Scale "/pix of the image in both axes. (Input: 1 value or 2 values separated by semicolon)
  TELESCOPE  = Name of the telescope
  SITENAME   = Name of the site
  SITEALT    = Altitude of the site
  SITELAT    = Latitude of the site
  SITELONG   = Longitude of the site
  EQUINOX    = Epoch of the coordinates
  STKOFF     = stack offset from master frame
  AV,SM      = averaged,summed value for DAOPhot:find
  DATASEC    = From DATASEC card in FITS header
  OVERSCAN   = Info about overscan
  IMGSTAT    = Statistic of the image: median, mean, standard deviation
  APCORR     = Aperture correction for the image and error (tuple).
  SKZP_FLG   = Flag
"""
#default list of tag
SkZp_Par['_doc_']['def:datatag']=SkZp_Par['_doc_']['datatag']

def _str2tuple(x,x2=None):
    if(isinstance(x,str)):
        if(x.startswith('(') and x.endswith(')')):
            return tuple(float(y) for y in x[1:-1].split(', '))
        elif(';' in x): return tuple(float(y) for y in x.split(';'))
        elif(x2 is None): return (float(x), float(x))
        else:  return (float(x), x2)
    elif(isinstance(x,tuple)): return x
    elif(isinstance(x,(float,int))):
        if(x2 is None): return (x, x)
        else:  return (x, x2)

#type/class for the object of the tag value
SkZp_Par['datatagtype']={**dict( (tag,str)   for tag in ('NAME', 'ENTRYTYPE', 'CHIP', 'FILTER', 'DATE', 'TIME', 'AV,SM', 'INSTRUMENT', 'STKOFF', 'EXPID', 'OBJECT', 'OBSSET', 'TELESCOPE', 'SITENAME', 'EQUINOX', 'DATASEC', 'IMGSTAT') ),
                         **dict( (tag,float) for tag in ('FWHM', 'GAIN', 'RON', 'HIGH', 'EXPTIME', 'PSFFWHM', 'PSFELLIP', 'AIRMASS', 'SKY', 'MJD', 'MAGZPT', 'RA', 'DEC', 'SITEALT', 'SITELAT', 'SITELONG' )),
                         **dict( (tag,int)    for tag in ('NX', 'NY', 'BITPIX', 'IMGQUAL', 'NIGHT') ),
                         **dict( (tag,tuple)   for tag in ('OFFSET', 'OFFSETXY', 'SCALE', 'OVERSCAN', 'APCORR') ),
                        }
#callable for the convertion from string to data
SkZp_Par['datatagconvert']={
                         **dict( (tag,lambda x: int(float(x)) ) for tag in ('NX', 'NY', 'BITPIX', 'IMGQUAL', 'NIGHT') ),
                         **dict( (tag,lambda x: _str2tuple(x,x2=None) )   for tag in ('OFFSET', 'OFFSETXY', 'SCALE',) ),
                         **dict( (tag,lambda x:  _str2tuple(x,x2=0) )   for tag in ('OVERSCAN', 'APCORR') ),
                        }
for tag in SkZp_Par['datatagtype']:
    SkZp_Par['datatagconvert'].setdefault(tag, SkZp_Par['datatagtype'][tag])
#   rounding  ('FWHM':3, 'GAIN':6, 'RON':6, 'HIGH':6, 'EXPTIME':6, 'PSFFWHM':6, 'PSFELLIP':6, 'AIRMASS':6, 'SKY':6, 'MJD':6, 'MAGZPT':6, 'RA':6, 'DEC':6, 'SITEALT':6, 'SITELAT':6, 'SITELONG':6)),

SkZp_Par['_doc_']['datatagtype']="""Dictionary with for each tagname with the object type/class"""
SkZp_Par['_doc_']['datatagcovert']="""Dictionary with for each tagname with information to produce the tag value:
    string : the tag value will be processed with str.format method.
    callable : the tag value will be processed as parameter.""";

SkZp_Par['entrytypelist']=['raw', 'image', 'image:sci', 'image:std','stack', 'mosaic', 'bias', 'dark', 'cat:photo', 'cat:std'];
SkZp_Par['_doc_']['entrytypelist']="List of valid values for 'ENTRYTYPE' tag";

SkZp_Par['def:dataframe']=dict(zip(SkZp_Par['def:datatag'], [None]*len(SkZp_Par['def:datatag'])));
SkZp_Par['_doc_']['def:dataframe']="Dictionary with the default values of tag in parameter 'def:datatag'";

#inputdata,inputlist,runlist={},[],[];
SkZp_Par['inputdata']={};                         SkZp_Par['_doc_']['inputdata']="Dataframe with the input data for each image. It is a dictionary of dictionaries";
SkZp_Par['inputpanda']={};                         SkZp_Par['_doc_']['inputpanda']="Panda Dataframe with the input data for each image";
SkZp_Par['inputlist']=[];                         SkZp_Par['_doc_']['inputlist']="Ordered list of the entries in 'inputdata'";
SkZp_Par['runlist']=[];                           SkZp_Par['_doc_']['runlist']="Ordered list of the images to process (subset of 'inputlist')";

SkZp_Par['inputfiles']=[];                         SkZp_Par['_doc_']['inputfiles']="Ordered list of tuple containing filenames of the read inputfiles, the number of header (only for the first file) and data lines. Set by functions.InputDataExternalLoad. It is reset by functions.InputDataInitialize during initialization process.";
SkZp_Par['not2update']=[];                         SkZp_Par['_doc_']['entries2update']="List of the entries that doesn't have to be updated (for example, because retrived from an existing database)."
SkZp_Par['inputdatastyle']={'MR':('txt', 'csv','xlsx',), 'UR':('html','txt', 'csv')}
SkZp_Par['_doc_']['inputdatastyle']="Dictionary with list of possible style for machine-readable ('MR') or user-readable ('UR' inputdata files. Some styles are only available for pandas.Dataframe"

SkZp_Par['initializingflag']=False;               SkZp_Par['_doc_']['initializingflag']="""If the data have been initialized. To avoid a second initialization""";
SkZp_Par['instruments']={};                       SkZp_Par['_doc_']['instruments']="Dictionary with the name of the instruments used for the data and the number of images associated to them";
SkZp_Par['saferunbit']=1;                    SkZp_Par['_doc_']['saferunbit']="""Bit-flag for safety of the run, calculated from option 'saferun'.""";
#SkZp_Par['select']={};   SkZp_Par['_doc_']['select']=""".""";
#SkZp_Par['extractkey']=['##', 'area', 'part'];   SkZp_Par['_doc_']['extractkey']="""Keys used in the chip-extraction procedure""";


SkZp_Par['airmasscoeff']={'YI67':(0.0012,),'DR-1': (664.210,), 'HK76':(1.50668e-3,), 'Ra-2':(1.71289e-3,6.48613e-2), 'He-3':(1.07597e-3, 3.93441e-3, 9.58484e-2), 
        'He-4':(1.03605e-3, 2.19641e-3, 7.90946e-3, 1.42208e-1), 'He-5':(1.03146e-3, 2.02572e-3, 3.94105e-3, 1.60400e-2, 2.09689e-1)}
SkZp_Par['_doc_']['airmasscoeff']="""Coefficients for airmass methods (Rapp-Arraras & Domingo-Santos, 2011)""";

SkZp_Par['startime']=time.time()
SkZp_Par['_doc_']['startime']="""Set by functions.startime and used by functions.endtime""";


##############
SkZp_Par['script']={'pathscript':None, 'scriptname':None, 'mode':None, 'scriptsubtype':None, 'runtype':None, 'steps':None}; 
SkZp_Par['_doc_']['script']="""Information from the script name: path, name, subtype, runtype""";

SkZp_Par['counter']={'db_retr':0};                SkZp_Par['_doc_']['counter']="Dictionary of counters";

SkZp_Par['store4later']={'calib_coeff':{}, 'inputdata':()};
SkZp_Par['_doc_']['store4later']="""Dictionary with as key  a identifier (e.g. 'calib_coeff', 'inputdata', or the name of the variable), 
as value the object associated to that identifier.
A store to avoid to recalculate periodically certain objects. It is reset at each full initialization. 
It is reset by InputDataInitialize during initialization process.""";

### OPTION FILES ##
SkZp_Par['optfilenames']=["SkZpipe.opt", "skzpipe.opt", "SkZ_pipeline.opt"];   SkZp_Par['_doc_']['optfilenames']="List with the filenames of the basic files with options";
SkZp_Par['optfilelist']=[];                       SkZp_Par['_doc_']['optfilelist']="List with the names option files in reading order.";
SkZp_Par['optfiledata']={};                       SkZp_Par['_doc_']['optfiledata']="Dictionary with the option inside the read option files.";
SkZp_Par['_doc_']['optfile']="""Example of option file""";
SkZp_Par['optfile']="""
#debug=1
#optfiles=[ADDITIONAL OPTFILE]
#output:stderr:hide=1

#mp:nproc=0

#inputdata:instrument=None

#inputdata:readdatabase=0
#inputdata:readheader=0
#inputdata:onlyloaddb=1


#image:extract:select=area:ra,dec,radius

#photo:thre:psfcal=3
#photo:thre:srclst=4
#photo:thre:photo=3
#photo:Steps:psfcal=Ground,AddFph,AddFph,AddFph,Refine
#photo:Steps:srclst=Ground,AddFph,AddFph,AddFph,Refine
#photo:Steps:photo=GetFph
#timeout=allstar:36000

#photo:psf:starinit=400
#photo:psf:starmax=200
#photo:psf:starmin=50
#photo:psf:psfradius=15
#photo:DAO:varpsf=-1,1,2,3
#photo:DAO:psfdef=MOFFAT35
#photo:DAO:psfother=MOFFAT25,PENNY1,MOFFAT15,PENNY2,GAUSSIAN,ALLPSF
#photo:DAO:psfothergood=2

#allstarinput=nei
#workname=%d

#stackbytag=[TAG]
#tackmatchcreate=[MODE]
""";
#####

### OUTPUT ##
SkZp_Par['errorlist']=[];    SkZp_Par['_doc_']['errorlist']="""List of entries that had problems during the last procedure""";
SkZp_Par['errorhistory']={};    SkZp_Par['_doc_']['errorhistory']="""Record of old 'errorlist' parameters""";

SkZp_Par['stdout']=sys.stdout;    SkZp_Par['_doc_']['stdout']="""Object used as standard output""";
SkZp_Par['stderr']=sys.stderr;    SkZp_Par['_doc_']['stderr']="""Object used as standard error""";
SkZp_Par['ramfolder']=('/run/user', os.getuid, 'SkZpipeRAM');    SkZp_Par['_doc_']['ramfolder']="""Tuple with: 
    the parent directory on a ramfs/tmpfs; 
    a callable that return the subdirectory usable by the user; 
    the name of subdirectory where to create the ones for the single procedures""";

SkZp_Par['mp:nproc']=0;    SkZp_Par['_doc_']['mp:nproc']="""number of used processors""";
SkZp_Par['mp:availmemfrac']=0.85;   SkZp_Par['_doc_']['mp:availmemfrac']="""Fraction of available memory to use""";


SkZp_Par['FITSextension']=('.fits', '.fits', '.fts');   SkZp_Par['_doc_']['FITSextension']="""Tuple of extensions for FITS files (starting with a dot '.', as pathlib)""";
SkZp_Par['image_extension']='.fits';   SkZp_Par['_doc_']['imageextension']="""Extension of single-image FITS file (starting with a dot '.', as pathlib)""";
SkZp_Par['mosaic_extension']='.fit';   SkZp_Par['_doc_']['mosaicextension']="""Extension of FITS mosaic (starting with a dot '.', as pathlib)""";
SkZp_Par['chipheaderext']='.chdr';   SkZp_Par['_doc_']['chipheaderext']="""Extension for header of the chip (starting with a dot '.', as pathlib)""";
SkZp_Par['mosheaderext'] ='.mhdr';   SkZp_Par['_doc_']['mosheaderext']="""Extension for header of the mosaic (starting with a dot '.', as pathlib)""";


SkZp_Par['charconversion']={'.':'_', ' ':'_', '%d': lambda :os.path.basename(os.getcwd()) };       SkZp_Par['_doc_']['charconversion']="""For names: map to trasform certain characters or patterns""";



SkZp_Par['commentpattern']='#';   SkZp_Par['_doc_']['commentpattern']="""Pattern to mark a commented line in a file""";
SkZp_Par['headerfilepattern']=SkZp_Par['commentpattern'];   SkZp_Par['_doc_']['headerfilepattern']="""Pattern to mark a header line in a file""";

SkZp_Par['maxnamelength']=255;   SkZp_Par['_doc_']['maxnamelength']="""Maximum length of filename (generally 255)""";


#Running programs
SkZp_Par['checksleepbreak']={'daophot':2,       'allstar':10};         SkZp_Par['_doc_']['checksleepbreak']="""Dictionary with default values for time interval for the check of the programs (parameters for sleep)""";
SkZp_Par['runtimewarn']=    {'daophot':3600,    'allstar':86400};      SkZp_Par['_doc_']['runtimewarn']="""Dictionary with default values for runtime interval after which a warning is shown""";
SkZp_Par['timeout']=        {'daophot':3600<<5, 'allstar':86400<<2};   SkZp_Par['_doc_']['timeout']="""Dictionary with default values for time interval after which stop the program""";



#PHOTO
SkZp_Par['photo:StepL']=["Ground", "AddCoo", "AddFph", "ChkAdd", "Refine", "GetFph", "GetAph"];  SkZp_Par['_doc_']['photo:StepL']="""List of steps for photometric procedures""";
SkZp_Par['photo:Steps']=dict(zip(SkZp_Par['photo:StepL'], range(len(SkZp_Par['photo:StepL']))));  SkZp_Par['_doc_']['photo:Steps']="""Dictionary  of steps for photometric procedures and their index""";

SkZp_Par['photo:runtypelist']=['psfcal', 'photo','srclst'];  SkZp_Par['_doc_']['photo:runtypelist']="""List of types of photometric runs""";

SkZp_Par['photo:hgdcorrection']=0.8;                    SkZp_Par['_doc_']['photo:hgdcorrection']="The high good value will be multiplied by this value to avoid fluctuations due to flat correction , for example";

SkZp_Par['stdfield']=None;   SkZp_Par['_doc_']['stdfield']="""Class to manage standard fields. It is set by photometry.standards submodules""";
SkZp_Par['stdstar']=None;   SkZp_Par['_doc_']['stdstar']="""Class to manage standard stars. It is set by photometry.standards submodules""";

SkZp_Par['sourcesperpixel']=1./5.**2;   SkZp_Par['_doc_']['sourcesperpixel']="""Extimation of maximum number of sources per pixel square (=1/minimum area per source). Used to estimate 
the maximum numer of sources in a image""";




##################
##################
##################
ParameterCheck()
if(_default_hardreset_ is None):
    _default_hardreset_={}
    for par in SkZp_Par['_list_']:
        try:
            _default_hardreset_[par]=deepcopy(SkZp_Par[par])
        except:
            _default_hardreset_[par]=SkZp_Par[par]
def _hardreset_(flag=False):
    if(flag):
        for par in _default_hardreset_:
            try:
                SkZp_Par[par]=deepcopy(_default_hardreset_[par])
            except:
                SkZp_Par[par]=_default_hardreset_[par]

