###allframe.py###
import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy
import tempfile, traceback

from ...exceptions import *
from ...parameters import basicpar as bpar
from ...parameters import options as _opt
from ...parameters import daoparameters as daopar
from ...parameters.classes import bclasses
from ... import functions as funct
from ... import match 
from . import daofunctions as daofunct



class Allframe:
  mch='';
  Match=None;
  base='';
  starlist='';
  backuprecover=True;
  stdout=bpar.SkZp_Par['stdout'];

  def __init__(self, mch=None, starlist=None, backuprecover=True, stdout=None):    
    """Allframe(mch,  starlist, backuprecover)

Parameters
----------
    mch : str
        Name of the .mch file
    starlist : str
        Name of the file with the source list
    backuprecover : bool
        Flag to determine if recover a backup of a died run or not (default True)
    stdout : text stream
        Object with write and flush method
""";
    funct.check_file(mch);

    self.mch=mch;
    self.Match=match.Match(self.mch);
    self.base=mch.split('.')[0];
    self.starlist=starlist if(starlist) else self.base+".mag";
    self.backuprecover=backuprecover;

    self.stdout=stdout if(hasattr(stdout, 'write')) else bclasses.OutputPipe(otype='out');

    osrad=_opt.SkZp_Opt['F']['photo:psf:psfradius']+_opt.SkZp_Opt['F']['photo:psf-inskyradius']+_opt.SkZp_Opt['F']['photo:in-outskyradius'];
    if(osrad>daopar.DAO_Par['alfmaxosrad']):
      osrad=daopar.DAO_Par['alfmaxosrad'];
      print("!!!Too high osrad ({:.2f}): put equal to the maximum value ({:.2f})".format(osrad, daopar.DAO_Par['alfmaxosrad']), file=self.stdout); 
    
    self.allframe_opt=["wa=-2", "ce=6",  "ge=6",  "mi=5",  "ma={:d}".format(_opt.SkZp_Opt['I']['photo:allframe:niter']),  "is=2", "OS={:.3f}".format(osrad), "pe=0.75", "cr=2.5", "pr=5"];

    self.conv, self.disap, self.runtime='','',0;

  def __exit__(self, exc_type, exc_value, exc_tb):
    if(exc_type!=None):
      return False;

  def __enter__(self):
    return self;


  ###############################
  
  def run(self, maxiter=None, verb=True):
    """Run Allframe""";
    if(maxiter and isinstance(maxiter,int)): self.allframe_opt.append("ma={:d}".format(maxiter));
    lock=funct.LockRun(runfile=self.base);
    
    logfile=self.base+".Log_Alf";
    outxt="Allframe({progr}): {mch}".format(progr=_opt.OptionGet('progr:exec:allframe'), mch=self.mch);
    if(verb):  print(outxt, end='', file=self.stdout, flush=True);
  
    if(not self.backuprecover):
      funct.clean_file([self.base+daopar.DAO_Par['allframebackupext']]);
    
    cmd=[self.mch];
    if(not os.path.exists(self.base+daopar.DAO_Par['allframebackupext'])):
      funct.check_file([self.starlist], minline=daopar.DAO_Par['headerlen']+1, namemaxlen=daopar.DAO_Par['namemaxlen']);
      cmd.append(self.starlist);
  
    initime=int(datetime.datetime.now().strftime("%s"))
    tmpext="-tmp";
    with open(logfile+tmpext, 'w') as f_log:
        with subprocess.Popen(_opt.SkZp_Opt['S']['progr:exec:allframe'], shell=False, stdin=subprocess.PIPE, stdout=f_log, stderr=subprocess.STDOUT) as proc:
            for imes in self.allframe_opt+['ex']+cmd:
                imes=str(imes);
                f_log.write('=> '+imes+'\n');
                proc.stdin.write(bytes(imes+'\n','utf-8'));
                proc.stdin.flush();
            f_log.flush();
    
    final='';
    with open(logfile+tmpext) as f_tmp:
      with open(logfile, "w") as f_log:
        for line in f_tmp:
          line=re.sub('[\x00-\x08\x0c-\x1f]', '', line);
          f_log.write(line);
          if('No stars remain' in line): final=line;
    funct.clean_file(logfile+tmpext);
  
    tmpl=re.split(':|,', final);
    if(final and len(tmpl)>3):
      self.conv=tmpl[2].split()[0];
      self.disap=tmpl[3].split()[0];
      self.runtime=int(datetime.datetime.now().strftime("%s"))-initime;
      tmps="  {} C:{} D:{}".format(tmpl[0], self.conv, self.disap);
    else:
      tmps='Error';
    outxt+=tmps;
    if(verb):  print(tmps, "[{:d},{:.2f}]".format(self.runtime,self.runtime/3600), file=self.stdout);
  
    funct.UnLockRun(lock, self.base);
    return outxt;
  
  ###################################
  ###################################
  
  def CheckCoord(self):
    tmch=match.Match(self.base+"_chk.mch");
    tmch.makemch('dao:<p25:;', [self.Match.files[0], self.starlist]);
    tmch.DAOmaster(flag=1, sigma=2, ncoeff=4, mtrad='10,1,.1', output='mch', opt='[1.5');
    return tmch.data[1][1:3];
      
  
def loopstep(imgroup=None, **kwarg):
  """Image group processing procedure. Return: (group name, error status, run time,  the time wasted waiting).""";
  Alfrm=None;
  errst=False;
  if(imgroup is None): raise TypeError("AllframePipe: Wrong value for 'imgroup' in the loop");

  try:
    with bclasses.OutputPipe(otype='out') as stdout:
      print('', file=stdout);
      waitime=funct.WaitStop([imgroup, bpar.SkZp_Par['script']['scriptname']]) if(bpar.SkZp_Par['script']['scriptname']) else 0;
      midtime=funct.startime(verb=False);
      base=re.sub(_opt.SkZp_Opt['S']['stack:suff']+'$','', imgroup);
      with match.Match(base+_opt.SkZp_Opt['S']['allframe_mchsuff']+_opt.SkZp_Opt['S']['match:extension'], stdout=stdout) as mchalf: 
        mchalf.makemch(mode='copy:'+imgroup+".mch", files=_opt.SkZp_Opt['S']['stack:match:srcext']);
        mchalf=mchalf.mch;
        with Alf.Allframe(mchalf, stdout=stdout) as Alfrm:
          (offx, offy)=tuple(bpar.SkZp_Par['inputdata'][imgroup]['STKOFF'].split(','));
          DpAls.daofunct.applyOffset(imgroup+".als", (offx, offy), Alfrm.starlist, _opt.SkZp_Opt['I']['allframe_id0']);
      #      (x0,y0)=Alfrm.CheckCoord();
      #      print(x0, y0, flush=True);
      #    if(abs(x0)>1 or abs(y0)>1): raise SkZpipeErr("Still present a shift ({:.2f};{:.2f})".format(x0,y0))
          Alfrm.run()
       #NOT WORKING
#        if(False and _opt.SkZp_Opt['Flg']['catpostalf']):
#          mchall=match.Match(base+'_alfC.mch', stdout=stdout);
#          mchall.makemch('copy:'+Alfrm.mch, '.alf');
#          mchall.DAOmaster('2,.9,4', 1, 12, '20,1', 'mch', '<14,[1'); 
#          mchall.DAOmaster('2,.9,4', 1, 12, '10,1,.1', 'cat', '<14,[1');
#          bytagL=funct.InputDataTagValueSet(tag='FILTER', entrylist=mchall.frames);  ##ERROR@@@@ NO input-data!!!
#          if(len(bytagL)>1):
#            mchL=mchall.split(bytag='FILTER');
#            for mfltr in mchL:
#              mfltr.DAOmaster('2,.9,3', 1, 12, '20,1', 'mch', '<14,[1'); 
#              mfltr.DAOmaster('2,.9,3', 1, 12, '10,1,.1', 'mag', '<14,[1');
#            mchcat=match.Match(base+'_cat.mch', stdout=stdout);
#            files=[mm.base+".mag" for mm in mchL];
#            if(mchcat.checkfiles(files)==False):
#              mchcat.makemch('dao:<14:;', files);
#              mchcat.DAOmaster('2,.9,3', 1, 6, '20,2,2', 'mch', '<14,[1');
          
        
  except (KeyboardInterrupt, SystemExit):
    bpar.SkZp_Par['errorlist'].append(imgroup);
    print("\nError count:", len(bpar.SkZp_Par['errorlist']), bpar.SkZp_Par['errorlist']);
    errst=True;
    raise;
  except (SkZpipeException,OSError,TypeError,ValueError,KeyError) as err:
    runtime=funct.endtime(midtime, verb=False);
    print('\n',err);
    errst=True;
    bpar.SkZp_Par['errorlist'].append(imgroup);
    if(_opt.SkZp_Opt['Flg']['debug']): traceback.print_exc();
    return (imgroup, errst, runtime, waitime);
  except:
    errst=True;
    raise;
  else:
    errst=False;

    
  runtime=funct.endtime(midtime, verb=False);
  print('[', runtime, ']', flush=True, file=bpar.SkZp_Par['stdout']);
  return (imgroup, errst, runtime, waitime);


  
