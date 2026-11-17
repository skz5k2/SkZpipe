import sys, os, re
import traceback
import multiprocessing as multiprc

from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters  import options as _opt
from ..parameters.classes  import bclasses
from .. import functions as funct
from ..photometry.daophot import daophals as DpAls



def PhotoPipe(inputdata=None, method=None, runtype=None, steps=None, runlist=None, nproc=None, instr=None, readheader=None, readdatabase=None, options=None):
    """Running photometric procedure on images (DOAPhot/Allstar). 

Parameters
----------
    inputdata : str, Default: None
        Name of the input file
    method : str, None
        Method for the photometric procedure: DAOphot
    runtype : str, None, Default: None
        Type of the run (see parameter 'photo:runtypelist')
    steps : list of str. Default: None
        List of the steps to use.
    runlist : None, list
        list of the entries to process. None for 'runlist' parameter.
    nproc : int
        Number of the process to use in parallel.
    instr : str, None. Default: None
        Name of the instrument
    readheader: bool
        If initialization procedure will read data from image headers
    readdatabase: bool
        If initialization procedure will read data from internal database
    options : dict
        Dictionary with values of option to be passed.
    
Functions
---------
    functions.scriptdefine
    functions.startime
    functions.InputDataInitialize
    functions.InputDataInitWrite
""";
    _name_='PhotoPipe';

  #About name of the script
    (pathscript, scriptname, scriptsubtype)=funct.scriptdefine(auto=True);
    if(scriptname==None): scriptname=_name_;

    startime=funct.startime();

  ####
    if(scriptname):
        for rt in bpar.SkZp_Par['photo:runtypelist']:
            if(rt in scriptname):
                if(not runtype):
                    runtype=rt;
                elif(runtype!=rt):
                    raise SkZpipeErr("More than one runtype is present.");

        tmpl=[];
        for key in bpar.SkZp_Par['photo:StepL']:
            if(key in scriptname):
                tmpl.append(key);
        if(tmpl):
            steps=tmpl;
    if( runtype not in bpar.SkZp_Par['photo:runtypelist']): raise SkZpipeError("Wrong runtype {:} ({:}).".format(str(runtype), ', '.join(bpar.SkZp_Par['photo:runtypelist'])));
    bpar.SkZp_Par['script']['runtype']=runtype;
  ####
        
    if(runtype == 'srclst'): readheader, readdatabase = (False, False);
    if(_opt.SkZp_Opt['Flg']['debug']):
        funct.InputDataInitWrite(inputdata=inputdata, select=runtype, optfiles=['DpAls'+runtype+".opt"], instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);
    else:
        funct.InputDataInitialize(inputdata=inputdata, select=runtype, optfiles=['DpAls'+runtype+".opt"], instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);

    if(runlist is None): runlist=bpar.SkZp_Par['runlist'];
    if(not isinstance(runlist, list)): raise TypeError(_name_+": `runlist` must be a list.");
    if(len(runlist)==0): raise ValueError(_name_+": `runlist` is empty!");


    if(bpar.SkZp_Par['script']['scriptname']):
        startime+=funct.WaitStop([bpar.SkZp_Par['script']['scriptname']]);

    funct.seterrorlist()
    if(_opt.SkZp_Opt['Flg']['debug']): print(">>> Starting the photometric procedure", flush=True, file=bpar.SkZp_Par['stdout'])
    with bclasses.MProc(nproc=nproc, narg=len(runlist), method='pool') as mpobj:   #Only method=pool
      #Setting loopstep according to method and system setting
        if(method.startswith('DAO')):
            loopstep=DpAls.DAOp_loopstep;
            DpAls.SetSkZp_Opt();
    
            if(not steps): steps=_opt.SkZp_Opt['L']['photo:Steps:'+runtype];
    
        else: raise SkZpipeError("Wrong method for catalog photometry", exclocus=_name_);

        if(mpobj.nproc):
                #MULTIPROCESSING: >1
            print(f"MultiProcessing with {mpobj.nproc} processes of {len(runlist)} arguments.", flush=True, file=bpar.SkZp_Par['stdout']);


            retval=mpobj.pool.map(func=loopstep, iterable=[ {'NAME':img, 'OPT':options, 'STEPS':steps} for img in runlist]);
            #here retval is needed, because _loopstep modify only a local copy of global values
            for ret in retval:
                if(ret['status']):
                    bpar.SkZp_Par['errorlist'].append(ret['id']);
                else:
                    funct.InputDataEntryUpdate(entry=ret['id'], newdata=ret['dataframe']);  #To UPDATE INFO OBTAINS DURING PSF CALCULATION. During paralization each subrun has a copy of the enviroment, cannot modify it directcly
                
            
        else:
            #Normal
            if(_opt.SkZp_Opt['Flg']['debug']): print(">>> No multiprocessing", flush=True, file=bpar.SkZp_Par['stdout'])
            for image in runlist:
                loopstep({'NAME':image, 'OPT':options, 'STEPS':steps});
    ###
    funct.endtime(startime, verb=True, error=True);

    funct.InputDataWrite_wfailed(outfile='+_'+runtype, mode='w', style='all');
    return None;



  ###############################
  ###############################
def DAOPipe(inputdata=None, runtype=None, steps=None, runlist=None, nproc=None, instr=None, readheader=None, readdatabase=None, options=None):
    return PhotoPipe(inputdata=inputdata, method='DAO', runtype=runtype, steps=steps, runlist=runlist, nproc=nproc, instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);
    
def DAO_psfcal(inputdata=None, steps=None, runlist=None, nproc=None, instr=None, readheader=None, readdatabase=None, options=None):
    return DAOPipe(inputdata=inputdata, runtype='psfcal', steps=steps, runlist=runlist, nproc=nproc, instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);
DpAls_psfcal=DAO_psfcal;

def DAO_srclst(inputdata=None, steps=None, runlist=None, nproc=None, instr=None, readheader=None, readdatabase=None, options=None):
    return DAOPipe(inputdata=inputdata, runtype='srclst', steps=steps, runlist=runlist, nproc=nproc, instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);
DpAls_srclst=DAO_srclst;
        
def DAO_photo(inputdata=None, steps=None, runlist=None, nproc=None, instr=None, readheader=None, readdatabase=None, options=None):
    return DAOPipe(inputdata=inputdata, runtype='photo', steps=steps, runlist=runlist, nproc=nproc, instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);
DpAls_srclst=DAO_srclst;
    
def DAO_GetAph(inputdata=None, runlist=None, nproc=None, instr=None, readheader=None, readdatabase=None, options=None):
    return DAO_photo(inputdata=inputdata, steps='GetAph', runlist=runlist, nproc=nproc, instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);
DpAls_srclst=DAO_srclst;
    
def DAO_GetFph(inputdata=None, runlist=None, nproc=None, instr=None, readheader=None, readdatabase=None, options=None):
    return DAO_photo(inputdata=inputdata, steps='GetFph', runlist=runlist, nproc=nproc, instr=instr, readheader=readheader, readdatabase=readdatabase, options=options);
DpAls_srclst=DAO_srclst;
    
    
  
  #####################################################
  ##################################################### 
  
def DAO_FindThre():
    """Procedure to find the threshold for DAOPhot:find
    """
    _name_='DAO_FindThre'
    startime=funct.startime();
    (pathscript, scriptname, scriptsubtype)=funct.scriptdefine(auto=True);
    
    startime+=funct.WaitStop([scriptname]);
    
    funct.InputDataInitialize(select='exist', optfiles=[scriptname+".opt"]);
    DpAls.SetSkZp_Opt();
    
    
    
    #START
    funct.seterrorlist();
    def _ImgProc(image):
        try:
            waitime=funct.WaitStop([scriptname]);
            midtime=funct.startime(verb=False);
    
            with DpAls.DAOp_Proc(bpar.SkZp_Par['inputdata'][image], runtype='psfcal') as img:
            
            #STARTING
                img.RunDaoPhot_find4thre();
      
        except (SkZpipeException,OSError) as err:
            print(err, flush=True);
            bpar.SkZp_Par['errorlist'].append(image);
        
        runtime=funct.endtime(midtime, verb=False);
        print('[', runtime, ']');
        return (runtime, waitime);
    ###
    for image in bpar.SkZp_Par['runlist']:
        _ImgProc(image);
    
    funct.endtime(error=True, verb=True);
