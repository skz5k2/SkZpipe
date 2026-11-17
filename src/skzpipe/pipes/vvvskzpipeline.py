import sys, os, re

from ..exceptions import *
from .. import functions as funct
from . import photopipe
from . import matchstackpipe as mstpipe
from . import catalogpipe as ctlgpipe 
  

###  
def VVVGetImgInfo(inputdata=None, options=None):
  """Pipeline for VVV survey to extract chip and information from pawprints

Parameters
----------
    x : 
        Object to be converted in float.
    x0 : 
        Return value if an error occurs (default None).

Return
------
    None
""";
  _name_='VVVGetImgInfo';
  funct.InputDataInitWrite(inputdata=inputdata, taglist=None, options=options, mode='w', select=None, instr='VIRCAM:VVV', readheader=True, readdatabase=True, forceMJD=False, style='all', verb=False)


###
def VVVImgdataWrite2Old():
  """Write image data loaded in memory in the old format (VVV-SkZ_pipeline).

Return
------
    files
        Create 'VVV-imgdata' and 'VVV-imgdata.html'
""";# ,'VVV-imgdata_oldformat.html'

  _name_='VVVImgdataWrite2Old';
  oldname='VVV-imgdata';
  htmlname=oldname+'_oldformat.html';
  funct.InputDataWrite(outfile=oldname, mode='w', style='all', select='catalog', entrylist=None, dataframe=None, datatag=['NAME','FWHM','CHIP','GAINCOR','FILTER','EXPTIME','AIRMASS','SKY','HIGH','DIT','NDIT','ELLIPTIC','MAGZPT','MJD','DATE','RA','DEC','EQUINOX','SUBSECT','OBNAME','TILE','OFFSET','STATUS'], newtag={'STATUS': (lambda data : ":".join([ str(x) for x in (data['CASUVERS'],data['ESOGRADE'],data['OBSTATUS']) ])) });
#  funct.backupfile(htmlname, keep=False);
#  os.rename(oldname+'.html', htmlname); 


###
def VVVImgdataTransl2Old():
  """Read image data and write them in the old format (VVV-SkZ_pipeline).

Return
------
    files
        Create 'VVV-imgdata' and 'VVV-imgdata_oldformat.html'
""";

  _name_='VVVImgdataTransl2Old';
  oldname='VVV-imgdata';
  htmlname=oldname+'_oldformat.html';
  funct.InputDataInitWrite(outfile=oldname, action='info', mode='w', style='all', select='catalog', datatag=['NAME','FWHM','CHIP','GAINCOR','FILTER','EXPTIME','AIRMASS','SKY','HIGH','DIT','NDIT','ELLIPTIC','MAGZPT','MJD','DATE','RA','DEC','EQUINOX','SUBSECT','OBNAME','TILE','OFFSET','STATUS'], newtag={'STATUS': (lambda data : ":".join([ str(x) for x in (data['CASUVERS'],data['ESOGRADE'],data['OBSTATUS']) ])) }, readjustfile=True);
  funct.backupfile(htmlname, keep=False);
  os.rename(oldname+'.html', htmlname); 



##################
def VVVPhotoPipe(inputdata=None, runtype=None, steps=None, options=None):
  """Daophot/Allstar pipeline for VVV survey

Parameters
----------
    inputdata : str
        File with input data
    runtype : str
        Type of photometric procedure
    steps : list of str
        List of steps to be run
    options : dict
        Dictionary with values of option to be passed.

Return
------
    None

Functions
---------
  PhotoPipe
""";
  _name_='VVVPhotoPipe';
  photopipe.PhotoPipe(inputdata=inputdata, runtype=runtype, steps=steps, instr='VIRCAM:VVV', options=options);

  
###
def VVVPhoto_psfcal(inputdata=None, options=None):
  """Daophot/Allstar pipeline to calculate PSF for VVV survey. Wrapper for VVVPhotoPipe with `runtype`='psfcal', `steps`=["Ground", "AddCoo", "AddFph", "ChkAdd", "Refine"].

Parameters
----------
    inputdata : str
        File with input data
    options : dict
        Dictionary with values of option to be passed.

Return
------
    None
""";
  _name_='VVVPhoto_psfcal'
  VVVPhotoPipe(inputdata=inputdata, runtype='psfcal', steps=["Ground", "AddCoo", "AddFph", "ChkAdd", "Refine"], options=options);
  
###
def VVVPhoto_srclst(inputdata=None, options=None):
  """Daophot/Allstar pipeline to produce source list for VVV survey. Wrapper for VVVPhotoPipe with `runtype`='srclst', `steps`=["Ground", "AddFph", "AddFph", "Refine"

Parameters
----------
    inputdata : str
        File with input data
    options : dict
        Dictionary with values of option to be passed.

Return
------
    None
""";
  _name_='VVVPhoto_srclst';
  VVVPhotoPipe(inputdata=inputdata, runtype='srclst', steps=["Ground", "AddFph", "AddFph", "Refine"], options=options);
  


##################
def VVVMakeStack(options=None):
  """Pipe to create a stack image starting from the existing .als to create a preliminary match and allframe for a better one.

Parameters
----------
    options : dict
        Dictionary with values of option to be passed.

Return
------
    None
""";
  _name_='VVVMakeStack';
  return mstpipe.MakeStack(tag='FOV', instr='VIRCAM:VVV', options=options);
  

#Alias
VVVAllframeMntg=VVVMakeStack;


##################
def VVVCtlgCheck():
  """Pipe to analyze catalogs of clusters.

Parameters
----------
    x : 
        Object to be converted in float.
    x0 : 
        Return value if an error occurs (default None).

Return
------
    None
""";
  _name_='VVVCtlgCheck';
  return mstpipe.CtlgCheck();



def VVVCtlgPhoto(options=None):
  """Run Allframe
""";
  ctlgpipe.CatalogPhoto();



