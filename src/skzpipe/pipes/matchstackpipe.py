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

import re, os, shutil, sys, traceback
import numpy

from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters  import options as _opt
from ..parameters.classes  import bclasses

from .. import match as match
from .. import functions as funct
from ..photometry.daophot import daophals as DpAls
from ..photometry.daophot import allframe as Alf
from .. import stacking as stack

###############
## DAOMASTER ##
###############
def daomasterpipe(stdout=None):

    startime=funct.startime();
    
    (pathscript, scriptname, scriptsubtype)=funct.scriptdefine();
    
    startime+=funct.WaitStop([scriptname]);
    
    runtype='';
    
    #START
    _opt.OptionRead([scriptname+".opt"]);
    
    funct.errorlist();
    for line in fileinput.input():
        prewait=0;
        tmpl=line.split();
        try:
            with match.Match(tmpl[0], stadout=stdout) as mchfile:
                startime+=funct.WaitStop([mchfile.base, scriptname]);
                midtime=funct.startime(verb=False);
    
            #STARTING
                mchfile.DAOmaster(flag=tmpl[1], sigma=float(tmpl[2]), ncoeff=int(tmpl[3]), radius=tmpl[4], output=tmpl[5]);
    
        except (SkZpipeException,OSError) as err:
            print(err);
            bpar.SkZp_Par['errorlist'].append(tmpl[0]);
    
    
    funct.endtime(startime, verb=True, error=True);
    

##############
## STACKING ##
##############
pathscript, scriptname, scriptsubtype = None,None,None;
_stk_prefix=None;
_int_param0={'flag':'2,.8,4', 'ncoeff':12, 'radius':'10', 'magperc0':[25,50,90,90,90], 'sharpcut0':[1,1.5,2,2,2], 'FWHM':0};

def stackmatchcreate(mchfile=None, files=None, makemode=None, daom_param=None, magperc=[], sharpcut=[]):
    """Create the basic .mch file for the stacking.
Prameters
---------
    mchfile : match.Match
        Match object to create a first coordinate-transformation set of coefficients.
    files : list of str
        List of file to be metched in `mchfile`
    makemode : list
        List with sequence of mode for Match method 'makemch'.
    daom_param : list of dict
        List with, for each run of Match.DAOmaster, parameters to use to refine the transformations.
          'flag', 'sigma', 'ncoeff' same in Match.DAOmaster.
          'radius' (starting value only), 
          'minradius' (from parameter radius: final matching radius),
          'step' (from parameter radius: step of the decrease),
        Use option 'stack:match:refineparam' if undefined.
        If a parameter is missing, the one of the previous run is used, or from default values.
        For each element of the list, Match.DAOmaster is run.
        Default: [{'flag':'2,.8,4', 'ncoeff':12, 'radius':'20'}, {}, {}]
    magperc : list
        Sequence of percentile for the cut in magnitude. Default [25, 50, 90]
    sharpcut : list
        Sequence of values for the cut in sharp. Default [1, 1.5, 2]


""";
    _name_="stackmatchcreate";
    if(not isinstance(mchfile, match.Match)): raise TypeError(_name_+": `mchfile` must be a match.Match object <{}>".format(mchfile.__class__)); 
    if(not isinstance(files, list)): raise TypeError(_name_+": `files` must be a list <{}>".format(files.__class__)); 
    if(makemode is None): makemode=_opt.SkZp_Opt['L"']['stack:match:makemode'];
    if(daom_param):
        if(not isinstance(daom_param,list)): raise TypeError(_name_+": `daom_param` must be a list of dictionaries.");
        for run in daom_param:
            if(not isinstance(run,dict)): raise TypeError(_name_+": `daom_param` must be a list of dictionaries.");
    if(not isinstance(magperc,list)): raise TypeError(_name_+": `magperc` must be a list.");
    if(not isinstance(sharpcut,list)): raise TypeError(_name_+": `sharpcut` must be a list.");
    if(not files): raise ValueError(_name_+": `files` is empty"); 

  #REMINDER _int_param0={'flag':'2,.8,4', 'ncoeff':12, 'radius':'10', 'FWHM': <X>, 'magperc':[25,50,90], 'sharpcut':[1,1.5,2]};
  #DEFAULT values
    if(len(magperc)==0): magperc=_int_param0['magperc0'];
    elif(len(magperc)==1): magperc.extend(_int_param0['magperc0'][1:]);
    elif(len(magperc)==2): magperc.extend(_int_param0['magperc0'][2:]);

    if(len(sharpcut)==0): sharpcut=_int_param0['sharpcut0'];
    elif(len(sharpcut)==1): sharpcut.extend(_int_param0['sharpcut0'][1:]);
    elif(len(sharpcut)==2): sharpcut.extend(_int_param0['sharpcut0'][2:]);
    
    flag0, ncoeff0, radius0, minradius0, step0=_int_param0['flag'], _int_param0['ncoeff'], _int_param0['radius'], .25*_int_param0['FWHM'], .2*_int_param0['FWHM'];
    daom_param_opt=_opt.OptionGet('stack:match:refineparam');
    if(not daom_param): 
        if( daom_param_opt ): 
            daom_param=daom_param_opt;
            daom_param_last=daom_param_opt[-1];
        else: daom_param=[_int_param0, {}, {}];
    
    #first after creation
    daom_param[0].setdefault('flag', flag0);
    daom_param[0].setdefault('ncoeff', 6); daom_param[0]['ncoeff']=min(6,daom_param[0]['ncoeff']);
    daom_param[0].setdefault('radius', 2*radius0);
    daom_param[0].setdefault('minradius', round(0.9*_int_param0['FWHM'],1));
    daom_param[0].setdefault('step', -20); #to have 20 steps
    daom_param[0].setdefault('magperc', magperc[0]);
    daom_param[0].setdefault('sharpcut', sharpcut[0]);


    nrun=2;
    for ii in range(1,len(daom_param)):
        daom_param[ii].setdefault('flag', flag0);
        daom_param[ii].setdefault('ncoeff', ncoeff0);
        daom_param[ii].setdefault('radius', radius0);
        daom_param[ii].setdefault('minradius', minradius0);
        daom_param[ii].setdefault('step', step0);
        daom_param[ii].setdefault('magperc', magperc[ii]);
        daom_param[ii].setdefault('sharpcut', sharpcut[ii]);

        flag0, ncoeff0, radius0, minradius0, step0=daom_param[ii]['flag'], daom_param[ii]['ncoeff'], daom_param[ii]['radius'], daom_param[ii]['minradius'], daom_param[ii]['step'];



    #Check if mch file is congruent with list of files
    mcheck=mchfile.checkfiles(files);
    
    if(mcheck==False):
        instrset=funct.InputDataTagValueSet(tag='INSTRUMENT', entrylist=[x.rsplit('.',1)[0] for x in files]);
        if(len(instrset)<1): raise SkZpipeError("Set of 'INSTRUMENT' values is empty! Not possible.", exclacus=_name_);
        for mode in makemode:
            failed=False;
            modeoption= {'fixfov':True} if('dao' in mode and len(instrset)==1) else None;
            if( not mchfile.makemch(mode, files, modeoption=modeoption)): break;
            failed=True;
        if(failed): raise SkZpipeError('It was not possible to create  .mch file {mchn} with all the frames'.format(mchn=mchfile.mch), exclocus=_name_);

#    funct.flush_out();
        waittime=funct.WaitStop([_name_]);

      #if matching file already exists, it is not usefull losing time with loosing refining: already refined before.
        mchfile.DAOmaster(flag=daom_param[0]['flag'], sigma=1,  ncoeff=daom_param[0]['ncoeff'], radius=(daom_param[0]['radius'],daom_param[0]['minradius'],daom_param[0]['step']), output='mch', selopt={'mag':daom_param[0]['magperc'], 'sharp':daom_param[0]['sharpcut']}); 

    if(mcheck==False or _opt.OptionGet('stack:match:refineforce')):
        for ii in range(1,min(nrun, len(daom_param))):
            mchfile.DAOmaster(flag=daom_param[ii]['flag'], sigma=1,  ncoeff=daom_param[ii]['ncoeff'], radius=(daom_param[ii]['radius'],daom_param[ii]['minradius'],daom_param[ii]['step']), output='mch', selopt={'mag':daom_param[ii]['magperc'], 'sharp':daom_param[ii]['sharpcut']});

      #####Do it only if the transformation are new or .mag file is missing
        if(mcheck==False or DpAls.daofunct.Dao_check_file(mchfile.base+'.mag', raisexc=False)):
            flag=  daom_param_last.get('flag', flag0);
            ncoeff=daom_param_last.get('ncoeff', ncoeff0);
            radius=daom_param_last.get('radius', radius0);
            minradius=daom_param_last.get('minradius', minradius0);
            step=  daom_param_last.get('step', step0);

            mtrad=(radius, minradius, step);
#    mchfile.DAOmaster(flag, 1, ncoeff, mtrad, 'mag', '|p{pmag},[{sharp:.1f}'.format(pmag=magperc[2], sharp=sharpcut[2]));
            mchfile.DAOmaster(flag, 1, ncoeff, mtrad, 'mag', );

#####
def _stackimproveposwith_allframe(mchold=None, mchstk=None, daom_param=None, stdout=None):
    """Function to improve the positions for stack using allframe.

Parameters
----------
    mchold : Match object
        Match object with old trasformation
    mchstk : str
        Name for the .mch file for stacking
    daom_param : dict
        Dictionary with parameters for Match.DAOmaster to refine coordinates transformations
    stdout : 
        Standard output
""";
    _name_='_stackimproveposwith_allframe';
    if(not isinstance(mchold, match.Match)): raise TypeError(_name_+": `mchold` must be a match.Match object <{}>".format(mchold));
    if(not isinstance(mchstk, str)): raise TypeError(_name_+": `mchstk` must be a string <{}>".format(mchstk));
    if(daom_param is not None and not isinstance(daom_param,dict)): raise TypeError(_name_+": `daom_param` must be a dict or None <{}>".format(daom_param));


    alfext='.alf';
    waittime=0;
    fnL=[ ff+alfext for ff in mchold.frames ];
    runprogr=False;
    mode=_opt.SkZp_Opt['I']['stack:match:improvepos:mode'];
    if(_opt.OptionGet('speedup')>0): mode=-1; #Not redoing if .alf exist
    elif(_opt.OptionGet('speedup')<0): mode=1; #redo anyway
  #####
    if( mode<0 ):
        if(os.path.exists(mchold.base+'.bck')): #if allframe was interrupt
            runprogr=True;
        elif(DpAls.daofunct.Dao_check_file(fnL, raisexc=False)):
            runprogr=True;
    elif( mode>0 ):
        runprogr=True;
    print("Run Allframe?", runprogr, file=stdout);
    if(runprogr):  
        waittime=funct.WaitStop(['Allframe']);
        Alfr=Alf.Allframe(mch=mchold.mch, stdout=stdout);
        Alfr.run(maxiter=_opt.SkZp_Opt['D']['stack:match:improvepos:param']['allframe']['niter'], verb=True);
    
  ######
    DpAls.daofunct.Dao_check_file(fnL);
    default={'flag':"2,.8,3", 'sigma':1, 'ncoeff':12, 'radius':5*_int_param0['FWHM'], 'minradius':0.25*_int_param0['FWHM'], 'step':0.25*_int_param0['FWHM'], 'magperc':33, 'sharpcut':1.5};
    if(not daom_param): daom_param={};
    daom_param_opt=_opt.OptionGet('stack:match:improvepos:refineparam');
    for key in default:
        if(daom_param_opt and key in daom_param_opt): daom_param.setdefault(key, daom_param_opt[key]);
        daom_param.setdefault(key, default[key]);
    improvedmch=re.sub(_opt.SkZp_Opt['S']['stack:match:suff']+'$', _opt.SkZp_Opt['S']['stack:match:improvepos:suff'], mchold.base)+_opt.SkZp_Opt['S']['match:extension']; 
    with match.Match( improvedmch, stdout=stdout) as mchnew:
#    if(mchnew.checkfiles(fnL)==False):
      #If redoing Allframe, always redo the matching file, not reusing the old
      #
        if(runprogr or not mchnew.exists or DpAls.daofunct.Dao_check_file(mchnew.base+'.mag', raisexc=False) ):
            mchnew.makemch('copy:'+mchold.mch, '.alf'); #copying the trasformations used by allframe changing the extension
            mchnew.DAOmaster(flag=daom_param['flag'], sigma=daom_param['sigma'], ncoeff=daom_param['ncoeff'], radius=(daom_param['radius'],daom_param['minradius'],daom_param['step']), output='mag', selopt={'mag':daom_param['magperc'], 'sharp':daom_param['sharpcut']});
#    funct.flush_out();
        shutil.copy(mchnew.mch, mchstk);
        shutil.copy(mchnew.base+'.mag', re.sub(r'\.mch$','.mag',mchstk));
    
    return waittime;

##########
##case-loop through dict
_stackimproveposwithD={'allframe' :_stackimproveposwith_allframe,
}

bytagL,bytagD=[],{};
####################################

####################################
def _loopstep(tagv):
    """Internal function to operate the procedure for each stack image""";
    global _int_param0;
    errst=False;
    with bclasses.OutputPipe(otype='out') as stdout:
        
            print("\n>>Stack", "for value {tagv}".format(tagv=tagv) if(tagv is not None )else '', "with {nfrm} frames".format(nfrm=len(bytagD[tagv])), file=stdout);
            ###
            try:
                    idname=_stk_prefix if(_stk_prefix) else _opt.OptionGet('inputdata:workname');
                    stackname='_'.join((idname, str(tagv))) if(tagv is not None) else idname;
                    with match.Match( base=stackname+_opt.SkZp_Opt['S']['stack:match:suff'], stdout=stdout) as mchpos:
                            waitime=funct.WaitStop([scriptname, mchpos.base]);
                            midtime=funct.startime(verb=False);
                    
                    
                            fnposL=[ff+_opt.SkZp_Opt['S']['stack:match:srcext'] for ff in bytagD[tagv]];
                            try:
                                    _int_param0['FWHM']=numpy.array(funct.InputDataTagValueList(tag='PSFFWHM', entrylist=bytagD[tagv])).mean();
                            except:
                                    _int_param0['FWHM']=numpy.array(funct.InputDataTagValueList(tag='FWHM', entrylist=bytagD[tagv])).mean();
                            stackmatchcreate(mchfile=mchpos, files=fnposL);
            #        mchpos.stdout.discharge();
                            #funct.flush_out();
                    
                            stkmch=re.sub(_opt.SkZp_Opt['S']['stack:match:suff']+'$', _opt.SkZp_Opt['S']['stack:suff'], mchpos.base)+_opt.SkZp_Opt['S']['match:extension'];
                            stackimproveposwith=_stackimproveposwithD.get(_opt.SkZp_Opt['S']['stack:match:improvepos:with']);
                            if(callable(stackimproveposwith)):
                                    stackimproveposwith(mchpos, stkmch, stdout=stdout);
                            else:
                                    shutil.copy(mchpos.mch, stkmch);
                                    shutil.copy(mchpos.base+'.mag', re.sub(r'\.mch$','.mag',stkmch));
      
                    minframe=_opt.OptionGet('stack:tagpar:minframe').get(tagv);
                    if(not minframe): minframe= _opt.OptionGet('stack:par:minframe');
                    maxframe=_opt.OptionGet('stack:tagpar:maxframe').get(tagv);
                    if(not maxframe): maxframe= _opt.OptionGet('stack:par:maxframe');
                    perc=_opt.OptionGet('stack:tagpar:percentile').get(tagv);
                    if(not perc): perc=_opt.OptionGet('stack:par:percentile');
                    with stack.Stacking(mch=stkmch, suff='', minframe=minframe, maxframe=maxframe, perc=perc, skyoverlap=True, xlim=None, ylim=None, expf=1, sky0=_opt.OptionGet('stack:sky0'),   stdout=stdout, verb=True) as stackimg:
                            stackimg.stack(substacktag=_opt.SkZp_Opt['S']['stack:substacktag']);
                            stackedL=stackimg.stacked;
    #        funct.flush_out();
                    
            except (KeyboardInterrupt, SystemExit) as err:
                    errst=True;
                    bpar.SkZp_Par['errorlist'].append(stackname);
                    runtime=funct.endtime(midtime, verb=True, error=True);
                    raise;
            except (SkZpipeException,OSError, TypeError, ValueError, KeyError) as err:
                    errst=True;
                    bpar.SkZp_Par['errorlist'].append(stackname);
                    runtime=funct.endtime(midtime, verb=False);
                    print(err, file=bpar.SkZp_Par['stderr']);
                    if(_opt.SkZp_Opt['Flg']['debug']): traceback.print_exc();
                    return {'id':stackname, 'status':errst, 'runtime':runtime, 'idletime':waitime, 'new':[]};
            except:
                    errst=True;
                    if(_opt.SkZp_Opt['Flg']['debug']): traceback.print_exc();
                    raise;
            else:
                    errst=False;
        
            runtime=funct.endtime(midtime, verb=False);
            print('[', runtime, ']\n', file=stdout);

    return {'id':stackname, 'status':errst, 'runtime':runtime, 'idletime':waitime, 'new':stackedL, 'newdata':{stk:bpar.SkZp_Par['inputdata'][stk] for stk in stackedL}};


def MakeStack(tag=None, stackprefix=None, select=None, instr=None, nproc=None, options=None):  
    """Create a stack image starting from the existing photometry and positions. It creates a preliminary match and it can run an additional program to improve the source positiona for a better one.

Parameters
----------
    tag :  str
        Tag to be used to select the images to create the stack
    stackprefix : str, None
        Prefix for the name of the stack image. Default option 'inputdata:workname'.
    select : dict, None
        Dictionary with selection parameters (see functions.InputDataSelect).
    instr : str, None
        Name of the instrument to use
    nproc : int
        Number of process to run the paralization.
    options : dict
        Dictionary with values of option to be passed.

Return
------
    None

""";
    _name_='MakeStack';
    global pathscript, scriptname, scriptsubtype;
    global bytagL, bytagD, _stk_prefix;

    startime=funct.startime();
    (pathscript, scriptname, scriptsubtype)=funct.scriptdefine();
    if(scriptname==None): scriptname=_name_;
    
    startime+=funct.WaitStop([scriptname]);
    
    #START
    if(select):
            if(isinstance(select,str)): select={'mode':['stack',select]};
            elif(isinstance(select,list)): select={'mode':['stack']+select};
            elif(isinstance(select,dict)):
                    if('mode' in select):
                            if(isinstance(select['mode'],str)): select['mode']=['stack',select['mode']];
                            elif(isinstance(select['mode'],list)): select['mode']=['stack']+select['mode'];
                    else: select['mode']=['stack'];
    else: select={'mode':['stack']};
    funct.InputDataInitialize(optfiles=[scriptname+".opt"], select=select, options=options);
    DpAls.SetSkZp_Opt();
    prewait=0; 

    if(not tag): tag=_opt.OptionGet('stack:bytag');
    (bytagL, bytagD)=funct.InputDataSplitByTag(tag=tag, entrylist=bpar.SkZp_Par['runlist']);
    if(stackprefix): _stk_prefix=stackprefix;
    startime+=funct.WaitStop([scriptname]);
        
    funct.seterrorlist();
    if(tag):
            print("""\nStack based on tag "{tag}" : """.format(tag=tag), end='', file=bpar.SkZp_Par['stdout']);
            for tagv in bytagL:
                    print(" {tagv} => {n} ;".format(tagv=tagv, n=len(bytagD[tagv])), end='', file=bpar.SkZp_Par['stdout']);
            print("\n", file=bpar.SkZp_Par['stdout']);
            
    else:
            print("""\nSingle stack  => {n}\n""".format(tag=tag, tagv=bytagL[0], n=len(bytagD[bytagL[0]])), file=bpar.SkZp_Par['stdout']);

#  funct.flush_out();

    reqmemL=[];
    for tag in bytagL:
        imgsizeL,listsizeL=[],[];
        for frm in bytagD[tag]:
            imgsize=round(os.stat(frm+'.fits').st_size/(1<<20), 3);
            imgsize=max(imgsize,0.001);
            imgsizeL.append(imgsize)

            listsize=round(os.stat(frm+_opt.SkZp_Opt['S']['stack:match:srcext']).st_size/(1<<20), 3);
            listsize=max(listsize,0.001);
            listsizeL.append(listsize)

        reqmemL.append( funct.ProcedureRequiredMemory('stack', {'images':imgsizeL.copy(), 'lists':listsizeL.copy(), 'improvepos':_opt.SkZp_Opt['S']['stack:match:improvepos:with']}) );


    with bclasses.MProc(nproc=nproc, narg=len(bytagL), method='pool') as mpobj:
        if(mpobj.nproc):
          #MultiProcessing
            print("MultiProcessing with {nproc} processes of {narg} arguments (mem: {mem})".format(nproc=mpobj.nproc, narg=len(bytagL), mem=", ".join( "{:.2f}".format(x) for x in reqmemL ) ), flush=True, file=bpar.SkZp_Par['stdout']);
            retval=mpobj.pool.map(func=_loopstep, iterable=bytagL);
            #here retval is needed, because _loopstep modify only a local copy of global values
            for ret in retval:
                if(ret['status']):
                    bpar.SkZp_Par['errorlist'].append(ret['id']);
                else:
                    for stacked in ret['new']:
                        funct.InputDataEntryAdd(new=stacked);
                        funct.InputDataEntryUpdate(entry=stacked, newdata=ret['newdata'][stacked]);

        else:
          #Normal
            for tagv in bytagL:
                retval=_loopstep(tagv);
                #here retval not used, because _loopstep can modify global values

            
    funct.InputDataWrite(outfile='+_stk', mode='w', style='all');
    funct.endtime(startime, verb=True, error=True);
      
