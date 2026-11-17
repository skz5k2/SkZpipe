#!/usr/bin/python3

# Copyright 2006-2010 Francesco 'SkZ' Mauro
#    All the suite of scripts and programs of the SkZ_pipeline is developed from the author/owner for himself and
#    is still growing and under developping
#    All requests for copies of this software, and for permission for further distribution, should be directed to
#    the author at the address skz5k2@gmail.com
#    This restriction is intended:
#    1) to prevent multiple, variously modified versions of the software from circulating in the scientific community
#      under a single name, thereby causing much confusion;
#    2) to ensure direct communication between all users of the software and its primary developer, so that any problems
#      may be immediately addressed and any update and upgrade can be comunicated;
#    3) to assist in the appropriate attribution of credit and blame.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#    READ THE FILE LICENSE FOR THE COMPLETE LIST OF TERMS OF USE
#    USING THIS PIPELINE YOU IMPLICITLY ACCEPT ALL THE TERMS OF USE

import re, os, shutil, sys
import traceback, numpy
import multiprocessing as multiprc

from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters  import database as _db
from ..parameters  import options as _opt
from ..parameters.classes  import bclasses
from ..parameters.classes  import fileclass as fclass

from .. import functions as funct

from .. import match as _match
from .. import stacking as stack
from ..photometry.daophot import daophals as DpAls
from ..photometry.daophot import allframe as Alf
from ..photometry import photofunctions as phfunct

from . import photopipe


def CatalogPhoto(inputdata=None, photo=None, apcorr=None, cleaning=None, calib=None, matching=None, select=None, runlist=None, nproc=None, instr=None, options=None):
  """Procedure to produce the photometry for the final catalog.

Parameters
----------
    inputdata : str, None
        Name of the input file (None for standard input) or list of lines
    photo : dict
        Dictionary with parameters to obtain catalog photometry
            'method' : str, None
                Method to produce the catalog photometry
            'skip' : bool
                The procedure has to be skipped if the photometry is already available (if files do not exist, the procedure will be run).
                The method is initialized anyway, only the image set are non elaborated.
            'ext' : str
                The extension of the files with catalog photometry. Default according the method.
    apcorr : dict
        Dictionary with parameters about aperture correction procedure
            'method' : str, None
                Method to calculate aperture correction. Default option 'photo:apcorr:method'
            'radius' : float
                Size of the aperture for the aperture correction. Default value option 'photo:std:aperture' or first value in option 'photo:aperture'.
            'ap0_ext' : str
                Extension of the file as reference for  aperture correction (with the aperture photometry on which the catalog photometry is based onto )
            'coord_ext' : str
                Extension of the file with coordinates for the aperture photometry. Default the output of the catalog photometry.
            'fph_ext' : str
                Extension of the file with psf-fitting photometry eventually used for the aperture photometry. Default the output of the catalog photometry.
            'calcmode' : str
                How to calculate the aperture correction:
                  'dao' to use DAOmaster calculation.
                  'lsq' to use least square root
                Default option 'photo:apcorr:calc'
    cleaning : dict
        Dictionary with parameters about spurious-source cleaning procedure.
        The parameters are the same for Photofile.cleaning() method (see `setting` for Photofile.cleaning), the name of the attributes of the photometric source class.
        Typical attibutes are: 'x', 'y', 'mag', 'emag', 'sky', 'niter', 'chi2', sharp'. The key 'area' is to select 2D parts.
        For each attribute is given a dictionary that use as keys 'max', 'range'.
    calib : dict
        Dictionary with parameters about calibration procedure
            'nparam' : dict of dicts
               Dictionary with the calibration parameter for each night; night numbers as keys and,
               as values, dictionaries with calibration parameters.
               Each night entry provides for each filter (used as key) a dictionary with air-extintion
               and calibration coefficients, and the pair of filters used for the color relation.
               For each filter, the available entries are:
                 'am' : tuple of floats
                      Atmospheric extintion coefficient and its error.
                 'coeff' : list/tuple of tuples
                      The coefficinets are provided as tuple/list of tuples of values in pairs: (value, error).
                      The order of the coefficients follows the degree of the color expression (constant, linrat, quadratic, ...).
                 'color' : tuple of str
                      The pair of filter name used for the color, in order. It can be omitted if 'color' is given in `calib` or there are just two filters.
               Example of 'nparam': { 1:{'B':{ 'coeff':((5.20, 0.001), (-0.02, 0.001)), 'am':(0.25, 0.002), 'color':('B','V')},
                                         'V':{ 'coeff':((5.20, 0.001), (+0.02, 0.001)), 'am':(0.15, 0.002), 'color':('B','V')},
                                        }, }
            'color' : tuple of str
               The pair of filters used for the color. This value is used as default if it is not provided in 'ncoeff'. 
            'applyto' : str
               What to calibrate: the filter-matched catalog ('catalog') or the photometry output ('photo', not yet implemented).
    matching : dict
        Dictionary with the parameter for the matching refine.
          'mode' : str
             Mode to build the catalog:
               'night/filter' : each night is matched separately for each filter. Each night/filter
                   subset is identified by a string with the number of the night follow by the filter (e.g '4V').
          'param' : dict
             Dictionary with parameters for each entry of the mode to refine the match.
             To make:
               'make' with as value the value for 'mode' in Match.makemch.
             To refine:
               'flag', sigma', ncoeff', radius' as for Match.refine.
          'minframe' : int
             Global value as minimum number of frame of 'flag' of Match.refine
               
    select : str, dict
        Selection criteria. See InputDataSelect.
    runlist : None, list
        list of the entries to process. None for parameter 'runlist'.
    nproc : int
        Number of the process to use in parallel.
    instr : str, None. Default: None
        Name of the instrument
    options : dict
        Dictionary with additional options
 
ging

""";
  _name_='CatalogPhoto';
  if(inputdata is not None and not isinstance(inputdata, str)): raise TypeError(_name_+": `inputdata` must be a str or None.");
  if(photo     is not None and not isinstance(photo, dict)): raise TypeError(_name_+": `photo` must be a dict or None.");
  if(apcorr    is not None and not isinstance(apcorr, dict)): raise TypeError(_name_+": `apcorr` must be a dict or None.");

  if(select    is not None and not isinstance(select, (str,list,dict))): raise TypeError(_name_+": `select` must be a str, list, dict or None (see InputDataSelect). <{}>".format(select));
  if(runlist   is not None and not isinstance(runlist, list)): raise TypeError(_name_+": `runlist` must be a list or None.");
  if(nproc     is not None and not isinstance(nproc, int)): raise TypeError(_name_+": `nproc` must be an integer or None.");
  if(instr     is not None and not isinstance(instr, str)): raise TypeError(_name_+": `instr` must be a str or None.");


  (pathscript, scriptname, scriptsubtype)=funct.scriptdefine(auto=True);
  if(scriptname==None): scriptname=_name_;
  startime=funct.startime();
  
  if(select is None): select='framephoto';
  
  startime+=funct.WaitStop([scriptname]);
  
  #START
  funct.InputDataInitialize(inputdata=inputdata, optfiles=[scriptname+".opt"], instr=instr, select=select, readheader=False, options=options);
  DpAls.SetSkZp_Opt();
  prewait=0; 

  if(runlist is None): runlist=bpar.SkZp_Par['runlist'].copy();

  if(photo is None ):
    photo={'method':_opt.OptionGet('photo:ctlg:method'), 'skip':_opt.OptionGet('photo:ctlg:skip'), };
  else:
    photo.setdefault('method', _opt.OptionGet('photo:ctlg:method'));
    if('method' in photo and not isinstance(photo['method'], str)): raise TypeError(_name_+": 'method' of `photo` must be a str");
    photo.setdefault('skip', _opt.OptionGet('photo:ctlg:skip'));
    if('ext' in photo and not isinstance(photo['ext'], str)): raise TypeError(_name_+": 'ext' of `photo` must be a str");
  
 #PHOTOMETRY
  if(photo['method'].startswith('DAO')):
    loopstep=Alf.loopstep;
    method='DAOallframe';
    if(not photo.get('ext')): photo['ext']='.alf';
    headerlen=Alf.daopar.DAO_Par['headerlen'];
  elif(method==''):
    if(not photo.get('ext')): raise SkZpipeError("Without giving the method, you must give the extension.", exclocus='_name_');
  else: raise SkZpipeError("Wrong method for catalog photometry", exclocus=_name_);

  ###  
  reqmemL=[];
  framelist=[];
  runlistp=[];
  if(photo['method']):
      for stkfrm in runlist:
        with _match.Match(stkfrm+_opt.OptionGet('match:extension')) as mchf:
          imgsizeL=[];
          framelist.extend(mchf.frames);
          if(photo['skip']):
            if(not funct.check_file([fn+photo['ext'] for fn in mchf.frames], minline=headerlen+1,raisexc=False)): continue;
    
          runlistp.append(stkfrm);
          for frm in mchf.frames:
            imgsize=round(os.stat(frm+bpar.SkZp_Par['fitsextension']).st_size/(1<<20), 3);
            imgsize=max(imgsize,0.001);
            imgsizeL.append(imgsize);
          listsize=round(os.stat(mchf.base+_opt.OptionGet('photo:ext:srclst')).st_size/(1<<20), 3);
        listsize=max(listsize,0.001);
        reqmemL.append( funct.ProcedureRequiredMemory(method, {'images':imgsizeL, 'other':listsize}) );
    
      if(runlistp):
        funct.seterrorlist();
        with bclasses.MProc(nproc=nproc, narg=len(runlistp), method='pool', memreq=reqmemL) as mpobj:   #Only method=pool
            if(mpobj.nproc):
                #MULTIPROCESSING
                print("MultiProcessing of {narg} arguments with {np} processes. (mem: {mem})".format(np=mpobj.nproc, narg=len(runlistp), mem=reqmemL), flush=True, file=bpar.SkZp_Par['stdout']);
                retval=mpobj.pool.map(func=loopstep, iterable=runlistp);
                for ret in retval:
                    if(ret[1]): bpar.SkZp_Par['errorlist'].append(ret[0]);
        
            else:
                #NORMAL
                for stkfrm in runlistp:
                    loopstep(stkfrm);

  #####################################
  #  CONFIG
  #########
  # APERTURE CORRECTION
#'method'    : str, None    Method to calculate aperture correction. Default option 'photo:apcorr:method'
#'radius'    : float        Aperture radius
#'ap0_ext'   : str    Extension of the file as reference for  aperture correction (with the aperture photometry on which the catalog photometry is based onto )
#'coord_ext' : str    Extension of the file with coordinates for the aperture photometry. Default the output of the catalog photometry.
#'fph_ext'   : str    Extension of the file with psf-fitting photometry eventually used for the aperture photometry. Default the output of the catalog photometry.
#'calcmode'  : str    How to calculate the aperture correction: dao, lsq
  if(apcorr is None ):
    apcorr={'method':_opt.OptionGet('photo:apcorr:method'), };
  else:
    apcorr.setdefault('method', _opt.OptionGet('photo:ctlg:method'));
    if('method' in apcorr and not isinstance(apcorr['method'], str)): raise TypeError(_name_+": 'method' of `apcorr` must be a str");
    apcorr.setdefault('skip', _opt.OptionGet('photo:ctlg:skip'));

    apcorr.setdefault('radius', _opt.OptionGet('photo:std:aperture'));
    if(not apcorr['radius']):
      apcorr['radius']=_opt.OptionGet('photo:aperture');
      if(not apcorr['radius']): apcorr['radius']=0.;
      elif(isinstance(apcorr['radius'], list)): apcorr['radius']=apcorr['radius'][0];
      else: raise SkZpipeError("'radius' in `apcorr` from option 'photo:aperture' is incorrect <{}>".format(repr(apcorr['radius'])), exclocus=_name_);
    if(not apcorr['radius']): apcorr['radius']=0.;
    if(not isinstance(apcorr['radius'], float)): raise TypeError(_name_+": 'radius' of `apcorr` must be a float");
    apcorr.setdefault('ap0_ext', _opt.OptionGet('photo:apcorr:ap0'));
    if(not isinstance(apcorr['ap0_ext'], str)): raise TypeError(_name_+": 'ap0_ext' of `apcorr` must be a str");
    apcorr.setdefault('fph_ext', _opt.OptionGet('photo:apcorr:fph'));
    if(not isinstance(apcorr['fph_ext'], str)): raise TypeError(_name_+": 'fph_ext' of `apcorr` must be a str");
    apcorr.setdefault('coord_ext', _opt.OptionGet('photo:apcorr:coord'));
    if(not isinstance(apcorr['coord_ext'], str)): raise TypeError(_name_+": 'coord_ext' of `apcorr` must be a str");

    if(not apcorr['fph_ext']):   apcorr['fph_ext']=photo['ext'];
  ###################
  # CALIBRATION
#calib
#'nparam'  : dict          {#night:{f1:{'am': (v,err), 'coeff':((c0,err), (c1,err)), 'color':(f1,f2) },
#                                   f2:{'am': (v,err), 'coeff':((c0,err), (c1,err)), 'color':(f1,f2) }     }}
#'color'   : tuple of str  The pair of filters used for the color. This value is used as default if it is not provided in 'ncoeff'. 
#'applyto' : str           What to calibrate: the filter-matched catalog ('catalog') or the photometry output ('photo', not yet implemented).
  if(calib):
    calib.setdefault('applyto', 'catalog');
    if(not isinstance(calib['applyto'], str)): raise TypeError(_name_+": 'applyto' of `calib` must be a string");
    color0=calib.get('color');
    if(color0 is not None):
      if(not isinstance(color0, tuple)): raise TypeError(_name_+": 'color' of `calib` must be a tuple of two string");
      if(not all(isinstance(flt, str) for flt in color0 )): raise TypeError(_name_+": 'color' of `calib` must be a tuple of two string");
    if(not calib.get('nparam')): raise SkZpipeError("`calib` is defined but not 'nparam': impossible to calibrate", exclocus=_name_);
    for nit,npar in calib['nparam'].items(): # for each night, values are dict
      fltrs=sorted(npar, key=_db.SkZp_DB['passbands'][None].index);
      nfltr=len(fltrs);
      color1=tuple(fltrs) if(not color0 and nfltr==2) else None;
      for flt in fltrs:
        npar[flt].setdefault('color', color0 if(color0) else color1);
        if(not npar[flt]['color']): raise SkZpipeError("Filter {filter} of night {night} in  'nparam' of `calib` has no 'color' defined: impossible to calibrate".format(filter=flt, night=nit), exclocus=_name_);
  ###################
  # MATCH
  if(matching is None): matching={'mode':'night/filter'};
  matching.setdefault('param',{});
  ###################
  #  CONFIG  END
  ######################################
      
  ###################
  #CLEANING
  if(cleaning):
      for fn in framelist:
        with DpAls.daofile.DAOPhotoFile(fn+photo['ext']) as phfile:
          print("Cleaning", phfile.fname, ":", phfile.cleaning(setting=cleaning, copy=True, cleanfile=None, rejfile=None), file=bpar.SkZp_Par['stdout']);
        os.rename(fn+photo['ext']+'-Kp', fn+photo['ext']); #It should be done by cleaning with copy=False and cleanfile='', but need to be fixed, and tested.


  ###################
  #APERTURE CORRECTION   
  if(apcorr['method'] and apcorr['radius']):
    if(apcorr['method'].upper().startswith('DAO')):
      if(not apcorr['ap0_ext']):   apcorr['ap0_ext']='.ap';
      if(not apcorr['coord_ext']): apcorr['coord_ext']='.alf';
      photopipe.DAO_GetAph(inputdata=None, runlist=framelist, options={'photo:aperture':[apcorr['radius']], 'photo:ext:coord':apcorr['coord_ext'], 'photo:ext:fitting':apcorr['fph_ext'], 'photo:apcorr:ap0':apcorr['ap0_ext']});
   #Applying apcorr and exptime corr to photometry output
      for fn in framelist:
        with photopipe.DpAls.DAOp_Proc(bpar.SkZp_Par['inputdata'][fn], runtype='photo') as img:
          if(calib):
            atmext=calib['nparam'].get(img.night,{}).get(img.filter, {}).get('am', (0,0));
          else: atmext=0;
          img.applymagcorr(suff=photo['ext'], exptime=True, apcorr=True, atmext=atmext, output=fn+photo['ext']+'0')
    else: raise SkZpipeError("Wrong method for aperture correction <{}>".format(apcorr['method']), exclocus=_name_);
  else:
    for fn in framelist:
      os.symlink(fn+photo['ext'], fn+photo['ext']+'0');


      
  
  ##################
  #MATCHING
  for stkfrm in runlist:
    newbase=re.sub(_opt.OptionGet('stack:suff')+'$','_',stkfrm);
    with _match.Match(stkfrm+_opt.OptionGet('match:extension')) as mchf:
      catframeL=mchf.frames;
    nightL,nightD=funct.InputDataSplitByTag('NIGHT', entrylist=catframeL);
    for nit,frmL in nightD.items():
      print("Matching for night", nit, file=bpar.SkZp_Par['stdout']);
      filterL,filterD=funct.InputDataSplitByTag('FILTER', entrylist=frmL);
      filterL=sorted(filterL, key=_db.SkZp_DB['passbands'][None].index)
      magmasterL,magmasterD,magfilterD, radiusL=[], {},{},[]
      for fltr in filterL:
        idm="{nit}{filter}".format(nit=nit,filter=fltr);
        matching['param'].setdefault(idm,{});
        with _match.Match(newbase+idm+_opt.OptionGet('match:extension')) as mchf:
          makemode=matching['param'][idm].get('make');
          if(makemode):
            mchf.makemch(mode=makemode, files=photo['ext']+'0', bytag={'NIGHT':nit, 'FILTER':fltr});
          else:
            mchf.makemch(mode='copy:'+stkfrm+_opt.OptionGet('match:extension'), files=photo['ext']+'0', bytag={'NIGHT':nit, 'FILTER':fltr});
          flag=matching['param'][idm].get('flag', '2,.8,3');
          sigma=matching['param'][idm].get('sigma', 1);
          ncoeff=matching['param'][idm].get('ncoeff', 12);
          radius=matching['param'][idm].get('radius');
          if(not radius):
            fwhm=numpy.array(funct.InputDataTagValueList(tag='PSFFWHM', entrylist=mchf.frames)).mean();
            prec=2-int(numpy.log10(fwhm)); #estimation of the needed precision
            radius=(round(3*fwhm,prec), round(fwhm/5,prec), -20);
            radiusL.append(list(radius));
          if(mchf.nfr>1):
            mchf.DAOmaster(flag=flag, sigma=sigma, ncoeff=ncoeff, radius=radius, output='mch', selopt=None);
            mchf.DAOmaster(flag=flag, sigma=sigma, ncoeff=ncoeff, radius=radius, output='mag', selopt=None);
          else: shutil.copy(mchf.files[0], mchf.base+'.mag');  #WRONG!!!!!! APPLY TRANSFORMATIONS
          magmasterL.append(mchf.base+'.mag');
          magmasterD[mchf.frames[0]]=mchf.base+'.mag';
          magfilterD[mchf.base+'.mag']=fltr;
        print(file=bpar.SkZp_Par['stdout']);
          

      print("\n  Matching ", filterL, "to catalog", file=bpar.SkZp_Par['stdout']);
      with _match.Match(newbase+str(nit)+_opt.OptionGet('match:extension')) as mchf:
#        mchf.makemch(mode='use:'+stkfrm+_opt.OptionGet('match:extension')+'@6', files=magmasterD);
        mchf.makemch(mode='1', files=magmasterL);
        mchf.sort(method='list', param={'files':sorted(mchf.files, key=(lambda x : _db.SkZp_DB['passbands'][None].index(magfilterD[x])) )}, write=True);
        nits=str(nit);
        matching['param'].setdefault(nits,{});
        flag=matching['param'][nits].get('flag', '1');
        sigma=matching['param'][nits].get('sigma', 3);
        ncoeff=matching['param'][nits].get('ncoeff', 12);
        radius=matching['param'][nits].get('radius');
        if(not radius):
          radius=tuple(numpy.array(radiusL).mean(axis=0));
        mchf.DAOmaster(flag=flag, sigma=sigma, ncoeff=ncoeff, radius=radius, output='mch', selopt=None);
        mchf.DAOmaster(flag=flag, sigma=sigma, ncoeff=ncoeff, radius=radius, output='raw', selopt=None);
#        outxt=subprocess.run(['raw_calib', mchf.base+'.raw', '0', str(mchf.nfr), '3'], capture_output=True).stdout.decode('utf-8')
      print("\n", file=bpar.SkZp_Par['stdout']);
     #calib
      if(calib['applyto'].lower().startswith('cat')):
        phfunct.filecalib(filein=None, fileformat=None, param=None, fileout='daophot', amcorr=False)

        




 ######
  funct.endtime(startime, tformat='h');
    


###########################################

def metricselect(files=None, option=None, badpixelarea=None, badpixelmode='all', selectmode='full', stdcat=None, dataframe=None, instr=None):
  """Apply metrization and select sources to exclude spuriois detection.

Parameters
----------
    files : sequence of str
        Iterable with names of the photometric file to elaborate.
    option :  dict
        Dictionary with option about astrometrization and selection.
          badpixelmode : str
              How to use the list of bad pixel areas: 'all', to reject all the bad pixel areas; 'bad', to reject only the 'bad' sub-set.
          metrmode : str
              Method to astrometrize the coordinates:
               'wcs' to transform 
          selectmode : str
              How to manage the source selection procedure: 'full', using all the methods; 'sigma', using only sigma clipping.

    badpixelarea : dict
        Dictionary with the bad pixel areas for each chip (same format as 'badpixelarea' database).
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']


""";
  _name_='metricselect';
#  if( not isinstance(, )): raise TypeError(_name_+": '' must be a ");
#  if( is not None and not isinstance(, )): raise TypeError(_name_+": '' must be a ");

  if( not isinstance(files, (list,tuple))): raise TypeError(_name_+": 'files' must be a list or tuple");
  if(option is None): option={};
  if( not isinstance(option, dict)): raise TypeError(_name_+": 'option' must be a dict or None");
  if(badpixelarea is not None and not isinstance(badpixelarea, dict)): raise TypeError(_name_+": 'badpixelarea' must be a dict");
  if('badpixelmode' in option and not isinstance(option['badpixelmode'], str)): raise TypeError(_name_+": option 'badpixelmode' must be a string");
  if('selectmode' in option and not isinstance( option['selectmode'], str)): raise TypeError(_name_+": option 'selectmode' must be a string");

  if( badpixelarea is None): badpixelarea=bpar.SkZp_DB['badpixelarea'][instr];

  phfilesL=[];
  for phfile in files:
    fclass=funct.FileGetType(phfile);
    if("DAO" == fclass[0]):
      phfilesL.append(fclass.DAOPhotoFile(name=phfile, ftype=fclass[1])); 








