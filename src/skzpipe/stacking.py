#!/usr/bin/python3
import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy, glob, itertools
from astropy import wcs 

from .exceptions import *
from .parameters import basicpar as bpar
from .parameters import daoparameters as daopar
from .parameters import options as _opt
from . import functions as funct
from . import match
from . import fits


#_opt.SkZp_Opt['I']['dummy']=50;


class Stacking:
  """Class to create stack images

Attributes
----------
 

Parameters
----------
    mch : str
        Filename of the file with the coordinate trasformation among the images to stack.
    minframe : int
        Minimum number of images a pixel should appear in before it is included.
    maxframe : int
        Maximum number of images to be used (montage2).
    perc : float
        Percentile of the values of the pixels of the images that should make up in the stack image.
    skyoverlap : bool
        Flag to determine the sky using the overlapping areas of the images
    xlim : str
        Range of values for x. 'e' for no limits.
    ylim : str
        Range of values for y. 'e' for no limits.
    expf : float
    expandingfactor : float
        Expanding factor for the stack image, to change the pixel scale.
    sky0 : float
        Sky value to be added at the end
    suff : str
        Suffix for the mage basenames to create an additional stack image from this second set.
    stdout, stderr : file object
        Standard output and standard error for the object
    verb : bool
        Verbosity flag

""";
  mch='';
  base='';
  suff='';
  suffL=[''];
  bases=[''];
  stacked=[''];
  data={}
  fwhm={}
  sky={};
  minframe=2;
  maxframe=13;
  perc=0.5;
  skyoverlap=True;
  xlim='e';
  ylim='e';
  expf=1;
  sky0=0;
  offx=0;
  offy=0;
  nxny=();
  logmnt2='';
  frames=[];
  files=[];
  nfr=0;
  bestpsf='';
  bestchi2=0;
  avsm='';
  stdout=bpar.SkZp_Par['stdout'];
  stderr=bpar.SkZp_Par['stderr'];

  def __init__(self, mch=None, minframe=2, maxframe=13, perc=.5, skyoverlap=True, xlim=None, ylim=None, expf=1, sky0=None, suff='', expandingfactor=None, stdout=None, stderr=None, verb=False): 
    """Initialization of Stack class

""";
    _name_='Object Stacking';
    err_data_msg=""; #" It needs ";
    if(not mch): raise SkZpipeError("no valid mch filename!"+err_data_msg, exclocus=_name_);
    self.mch=mch.strip();
    if(not self.mch):  raise SkZpipeError("no correct data!"+err_data_msg);
    funct.check_file([self.mch]);
    if(isinstance(suff,str)):
      self.suffL=[str(suff).strip()] if(suff) else [''];
    elif(isinstance(suff,list) and len(suff)>0 and len(suff)<=2):
      if(len(suff)==1 and suff[0]):
        self.suffL=['', str(suff[0]).strip()]
      elif(len(suff)==2 and '' in suff):
        self.suffL=sorted(suff);
      else:
        raise SkZpipeError("suff must be a string or a list of 1 not empty string");
    else:
      raise SkZpipeError("suff must be a string or a list of 1 not empty string");
    self.minframe=int(minframe) if(minframe) else 1;
    self.maxframe=int(maxframe) if(maxframe) else 1;
    self.perc=funct.getfloat(perc,0.5);
    if(self.perc<=0 or self.perc>=1): self.perc=0.5;
    if(self.perc<0 or perc>1): raise SkZpipeError(" wrong value for percentile", exclocus=_name_);
    if(isinstance(skyoverlap, bool)):
      self.skyoverlap='y' if(skyoverlap) else 'n';
    elif(isinstance(skyoverlap, str)):
      self.skyoverlap='n' if(re.search('n', skyoverlap, re.I)) else 'y';
    else:
      self.skyoverlap='y' if(bool(skyoverlap)) else 'n';
    self.xlim=xlim if(xlim) else 'e';
    self.ylim=ylim if(ylim) else 'e';
    if(expandingfactor): expf=expandingfactor;
    self.expf=funct.getfloat(expf, 1);
    self.sky0=funct.getfloat(sky0);

    self.stdout=stdout if(stdout) else bpar.SkZp_Par['stdout'];
    self.stderr=stderr if(stderr) else bpar.SkZp_Par['stderr'];

    #delete files

    with match.Match(self.mch, stdout=self.stdout) as omch:
      self.base=omch.base;
      self.frames=omch.frames;
      self.files=omch.files;
      self.nfr=omch.nfr;

    if(self.nfr==2): print("Warning: Using just 2 images!!!", file=self.stderr);

    self.bases=[];
    for sf in self.suffL:
      self.bases.append(self.base+sf);
    self.stacked=self.bases.copy(); #  self.stacked0=self.stacked+"0";
    (self.offx, self.offy, self.scale)=(0, 0, 1);
    (self.sky, self.fwhm)=({}, {});
 
    self.output='';

    #delete files
    self.nxny=(0,0);


#####################
#####################


  def __enter__(self):
    return self;

  def goodclose(self, exc_type=None):
    """Finalization of the Stacking object if stacking has finalized without problems.
""";
    self.avsm='{:.3f},{:.3f}'.format(.666*self.nfr,1);
    
    #get the chi square of the psf
    #look for the best psf comparing chi2 value
    chi2={};
    (key, X2min)=(self.frames[0], 9e9);
    for frm in self.frames:
      chif=frm+_opt.SkZp_Opt['S']['photo:psf:done'];
      funct.check_file(files=[chif], minline=0);
      funct.check_file(files=[frm+".psf"], minline=2);
      with open(chif) as chi_f:        
        chi2[frm]=float(chi_f.readline().strip());
      if(X2min>chi2[frm]):
        X2min=chi2[frm];
        key=frm;
    del chi2;
    self.bestpsf=key+".psf"; self.bestchi2=X2min;
    outxt="\t{fpsf} is the best PSF with Chi2={chi:.4f}".format(fpsf=self.bestpsf, chi=self.bestchi2);
    print(outxt, file=self.stdout);
    
    #create the psf file for montage2
    funct.check_file([self.bestpsf], 2)
    for fn in self.bases:
      funct.clean_file([fn+".psf", fn+".chi2", fn+_opt.SkZp_Opt['S']['photo:psf:done']]);
      shutil.copy(self.bestpsf, fn+".psf");
      shutil.copy(key+_opt.SkZp_Opt['S']['photo:psf:done'],  fn+_opt.SkZp_Opt['S']['photo:psf:done']);
      funct.clean_file( fn+".chi2" );
      os.symlink(fn+_opt.SkZp_Opt['S']['photo:psf:done'],  fn+".chi2");
    if(exc_type==None and self.mch and len(self.suffL)>0):
      for stacked in self.stacked:
        data={};
        data['ENTRYTYPE']='stack-image';
        data['STKOFF']='{:d},{:d}'.format(self.offx, self.offy);
        data['AV,SM']=self.avsm;
        data['NX']=self.nxny[0];
        data['NY']=self.nxny[1];
        if(self.frames[0] in bpar.SkZp_Par['inputlist']):
          funct.InputDataEntryAdd(new=stacked, old=self.frames[0]);
        else:
          funct.InputDataEntryAdd(new=stacked);
          data['FWHM']=self.fwhm[stacked];
          data['GAIN']=1;
          data['RON']=1.0001;
          data['HIGH']=75000;
        funct.InputDataEntryUpdate(entry=stacked, newdata=data);
         
    self.mch='';

  def close(self, exc_type=None):
    """Finalization of the Stacking object.
""";
    self.goodclose(exc_type=exc_type);

##
  def __exit__(self, exc_type, exc_value, exc_tb):
    if(exc_type!=None): return False;
    else: self.goodclose(exc_type=exc_type);
  
  
  ############  
  ############  
 
  ######
  def Cleanfiles(self):
    """Delete files connected to the stack image to produce.
""";
    print("Deleting files for", ", ".join(self.bases), file=self.stdout);
    for fn in self.bases:
      funct.clean_file([fn+bpar.SkZp_Par['fitsextension'], fn+"0"+bpar.SkZp_Par['fitsextension']]+ glob.glob(fn+"s.*")+ glob.glob(fn+".als*")+ glob.glob(fn+".ap*")+ glob.glob(fn+".?oo*"));


  ######

  def RunMontage(self,  suff_idx=2, minframe=None, maxframe=None, perc=None, xlim=None, ylim=None, sky0=None, mask=True, verb=False):
    """Run montage2 on the .mch file

Parameters
----------
    minframe : int
        Minimum number of frames where a pixel must appear
    maxframe : int
        Minimum number of frames to be used
    perc : float
        Percentile for the pixel values
    xlim : tuple
        Coordinate range in X to be used
    ylim : tuple
        Coordinate range in Y to be used
    sky0 : float
        Background value to be added to the stack image
    mask : bool
        Masking flag, to reduce pixel-value range (Montage2 sets to 1e19 pixels with unknown value). Default True.
    verb : bool
        Verbosity flag. Default False.

""";
    _name_='Stacking.RunMontage';

    if(suff_idx<0 or suff_idx>2 or (suff_idx==1 and  len(self.suffL)==1)): raise SkZpipeError(_name_+": suff_idx can be 0, 1 or 2 with 2 given suffixes, otherwise 0.");
    idxI=range(len(self.suffL)) if(suff_idx==2) else range(suff_idx,suff_idx+1);
    
    if(minframe is None): minframe=self.minframe;
    if(maxframe is None): maxframe=self.maxframe;
    if(  perc is None):   perc=self.perc;
    if(  xlim is None):   xlim=self.xlim;
    if(  ylim is None):   ylim=self.ylim;
    if(  sky0 is None):   sky0=self.sky0;

    if(minframe>self.nfr): minframe=self.nfr;
    outxt='';
    for idx in idxI:
        outxtmp="Montage2 on {mch} (#frame:{nfr}({maxfr}) suff:{suff} {minfr:d},{perc:.3f} limit:{xlim},{ylim} exp_fact:{expf:.3f} sky_from_overlap:{skyovr}): ".format(mch=self.mch, nfr=self.nfr, suff=self.suffL[idx], minfr=minframe, maxfr=maxframe, perc=perc, xlim=xlim, ylim=ylim, expf=self.expf, skyovr=self.skyoverlap);
        if(_opt.SkZp_Opt['Flg']['debug'] or verb): print(outxtmp, end='', file=self.stdout);
        outxt+=outxtmp;
  
        funct.clean_file([self.stacked[idx]+'0'+bpar.SkZp_Par['fitsextension'], self.stacked[idx]+bpar.SkZp_Par['fitsextension']]);
        logfile=self.bases[idx]+".Log_mnt2";
        self.logmnt2=self.bases[idx]+'.mnt2';
        with open(logfile, 'w') as f_log:
            f_log.write(funct.FramedText(_opt.SkZp_Opt['S']['progr:exec:montage2'])+'\n');
            funct.tell_progr(_opt.SkZp_Opt['S']['progr:exec:montage2'], [self.mch, self.suffL[idx], "{:d},{:.3f}".format(minframe,perc), xlim, ylim, self.expf, self.skyoverlap, self.stacked[idx]+bpar.SkZp_Par['fitsextension']], f_log);
        if(_opt.SkZp_Opt['Flg']['debug'] or verb): print("done", end='',file=self.stdout);
        outxt+="done";
        #############################################
        
        (skyd, fwhmd, weightd, self.offx, self.offy, self.scale)=({}, {}, {}, 0, 0, 1);
        (self.sky[self.stacked[idx]], self.fwhm[self.stacked[idx]], fullwt)=(0, 0, 0);
        if(not fits.testimage(self.stacked[idx]+bpar.SkZp_Par['fitsextension'])): raise SkZpipeError("The image seems not valid!!!", exclocus=self.stacked[idx]+bpar.SkZp_Par['fitsextension']);
        with open(self.logmnt2, 'w') as f_out:
            f_out.write(self.mch+" : "+self.stacked[idx]+bpar.SkZp_Par['fitsextension']+"\n\n");
            f_out.write("#Minimum number of frames, percentile\n");  
            f_out.write("{:d} {:.3f}\n\n".format(minframe, perc));
            with open(logfile) as f_log:
                for line in f_log:
                    if('Offsets' in line):
                        (self.offx, self.offy, self.scale)=tuple(line.split('=')[1].split()); #get X and Y offset
                    elif(re.search('Sky.+seeing.+weight', line)):
                        (sky,fwhm,wfr)=tuple(line.split(',')); #get sky and fwhm (seeing)
                        (weight,frame)=tuple(wfr.split('for')); #then get weight and frame name
                        frame=frame.strip();
                        sky=float(sky.split('=')[1]);        #clean sky var
                        fwhm=float(fwhm.split('=')[1]);        #clean fwhm var
                        weight=float(weight.split('=')[1]);        #clean weight var
                        skyd[frame]=sky;        #store sky
                        fwhmd[frame]=fwhm;        #store fwhm
                        weightd[frame]=weight;        #store weight
                        self.sky[self.stacked[idx]] += sky*weight;
                        self.fwhm[self.stacked[idx]] += fwhm*weight;
                        fullwt += weight;
        
            self.offx=int(self.offx); self.offy=int(self.offy); self.scale=float(self.scale); 
            if(_opt.SkZp_Opt['Flg']['debug'] or verb): print("   Offset: {offx} {offy}".format(offx=self.offx, offy=self.offy),file=self.stdout);
            outxt+="   Offset: {offx} {offy}\n".format(offx=self.offx, offy=self.offy);
            f_out.write("#frame:    \tsky\t   fwhm\t   weight\n"); # and print data
            for frm in sorted(self.frames):
                frm+=self.suffL[idx];
                f_out.write("{}  {:8.2f}  {:8.3f}  {:10.4f}\n".format(frm, skyd[frm], fwhmd[frm], weightd[frm]));
        
            f_out.write("\nWeighted sky, fwhm\n"); #calculate weighted value for sky and fwhm
            self.sky[self.stacked[idx]] =round(self.sky[self.stacked[idx]]/fullwt, 3);
            self.fwhm[self.stacked[idx]]=round(self.fwhm[self.stacked[idx]]/fullwt, 3);
            f_out.write("{:8.2f}  {:8.3f}\n\n".format(self.sky[self.stacked[idx]], self.fwhm[self.stacked[idx]]));
            
              
            f_out.write("#Offset\n");        #print offset
            f_out.write("{:10d} {:10d}  {:f}\n".format(self.offx, self.offy, self.scale));
          
        funct.clean_file([logfile+"_tmp"]);
        funct.flush_out();
        
        if(sky0 is None): self.sky0=self.sky[self.stacked[idx]];
        self.sky0=round(self.sky0,2);
        statimg=fits.statimage(self.stacked[idx]+bpar.SkZp_Par['fitsextension'],   minval=-daopar.DAO_Par['montage2fill']/1e2, maxval=daopar.DAO_Par['montage2fill']/1e2);
        self.nxny=(statimg['nx'], statimg['ny']);
  
        if(mask):
            (lowerlim, upperlim, fillval)=_opt.SkZp_Opt['F']['stack:mask:low'],_opt.SkZp_Opt['F']['stack:mask:high'],_opt.SkZp_Opt['F']['stack:mask:fill'];
            upperlim=max(upperlim, statimg['max']*1.1);
            if(fillval<0): fillval*=-1*_opt.SkZp_Opt['F']['stack:mask:high'];
            outxt+="low {} ; up {} ; fill {} \n".format(lowerlim,upperlim, fillval);
            shutil.move(self.stacked[idx]+bpar.SkZp_Par['fitsextension'], self.stacked[idx]+'Tm'+bpar.SkZp_Par['fitsextension']);
            fits.maskval(self.stacked[idx]+'Tm'+bpar.SkZp_Par['fitsextension'], lowerlim, upperlim, (lowerlim,None,upperlim),  self.stacked[idx]+bpar.SkZp_Par['fitsextension']);  
            if(not _opt.SkZp_Opt['Flg']['debug']): funct.clean_file([self.stacked[idx]+'Tm'+bpar.SkZp_Par['fitsextension']]);
  
        if(self.sky0):
            outmp="Fix-sky({:.2f})".format(self.sky0);
            if(_opt.SkZp_Opt['Flg']['debug'] or verb): print(outmp, file=self.stdout);
            outxt+=outmp;
            shutil.move(self.stacked[idx]+bpar.SkZp_Par['fitsextension'], self.stacked[idx]+'Ts'+bpar.SkZp_Par['fitsextension']);
            fits.arith(elem1=self.stacked[idx]+"Ts"+bpar.SkZp_Par['fitsextension'], oper='a', elem2=self.sky0, output=self.stacked[idx]+bpar.SkZp_Par['fitsextension']);
            if(not _opt.SkZp_Opt['Flg']['debug']): funct.clean_file([self.stacked[idx]+'Ts'+bpar.SkZp_Par['fitsextension']]);
    
        funct.check_file([self.stacked[idx]+bpar.SkZp_Par['fitsextension']]);
  
        for hext in [bpar.SkZp_Par['chipheaderext'], bpar.SkZp_Par['mosheaderext']]:
            if(os.path.exists(self.frames[0]+hext)):
                shutil.copy(self.frames[0]+hext, self.stacked[idx]+hext);
  
        fits.correctcrpix(self.stacked[idx]+bpar.SkZp_Par['fitsextension'], (self.offx, self.offy));
  
        fits.headeredit(image=self.stacked[idx]+bpar.SkZp_Par['fitsextension'], values={'EXTNAME':None, 'CCDSIZE':None, 'CCDSEC':None, 'DATASEC':None} );
      
    return outxt; 
  

  ###########
  def stack(self, substacktag=None, verb=False, mask=True):
    """Do the stacking

Parameters
----------
    substacktag : str
        Tag in internal input database to use for substacking
    verb : bool
        Verbosity flag. Default False.
    mask : bool
        Masking flag, to reduce pixel-value range (Montage2 sets to 1e19 pixels with unknown value). Default True.

Raises
------
    TypeError
      `substacktag` not a string
    SkZpipeError
      Just 1 substack
      Problems opening images
""";
    _name_='Stacking.stack';
    outxt='';
    if(substacktag is None): substacktag=_opt.SkZp_Opt['S']['stack:substacktag'];
    #delete files
    self.Cleanfiles();
    if(substacktag):
####### SUBSTACKING : Final stack= average of several substack images ###########
      if(not isinstance(substacktag, str)): raise TypeError("stacking.Stacking.stack: `substacktag` must be a string <{val}>".format(val=substacktag));
      print('    Substacking using tag:{tag}\n'.format(tag=substacktag), file=self.stdout);
      (xmn,xmx, ymn,ymx,  mult)=(1e9,-1e9, 1e9,-1e9,  0);
      with match.Match(self.mch, stdout=self.stdout) as omch:
        smchD=omch.split(tag=substacktag);
        master=omch.frames[0];
      with fits.pyfits.open(master+bpar.SkZp_Par['fitsextension']) as ms_img:
        wcs0=wcs.WCS(ms_img[0].header);
      substacktagL=sorted(smchD.keys())
      if(len(substacktagL)<2): raise SkZpipeError(_name_+": Substacking with {num} groups {slist}".format(num=len(substacktagL), slist=substacktagL));

      (lowerlim,upperlim, fillval)=_opt.SkZp_Opt['F']['stack:mask:low'],_opt.SkZp_Opt['F']['stack:mask:high'],_opt.SkZp_Opt['F']['stack:mask:fill'];
      if(fillval<0): fillval*=-1*_opt.SkZp_Opt['F']['stack:mask:high'];
      
      fitsD, maxvalD={},{};
      offxmn, offymn,   maxx, maxy, maxval= 1e9, 1e9,   -1e9,-1e9,   0;
      for idx in range(len(self.suffL)):
        for tagv in substacktagL:
          funct.WaitStop(tagv);
          fitsD[tagv]=Stacking(mch=smchD[tagv].mch, suff=self.suffL[idx], minframe=1, perc=self.perc, skyoverlap=self.skyoverlap, xlim='e', ylim='e', expf=1, sky0=0);
          print(fitsD[tagv].RunMontage(suff_idx=2, verb=verb, mask=False), file=self.stdout);


          with fits.pyfits.open(fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension'], 'update') as image:
            if(image):
              newobj="{card} tag:{tag}".format(card=image[0].header['OBJECT'].split('scale')[0], tag=tagv);
              if(_opt.SkZp_Opt['Flg']['stack:wcsfix']):
                image[0].header.update(wcs0.to_header())
              image[0].verify(option="fix+warn" if( _opt.SkZp_Opt['Flg']['debug']) else "silentfix");
            else: raise SkZpipeError("Problems opening image {:} !!!".format(fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension']), exclocus=self.stacked[idx]+bpar.SkZp_Par['fitsextension']);
            image.close(output_verify="fix+warn" if( _opt.SkZp_Opt['Flg']['debug']) else "silentfix");


          if(_opt.SkZp_Opt['Flg']['stack:wcsfix']):
            fits.headeredit(  image=fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension'], values={'OBJECT':newobj, 'CD1_1':None, 'CD1_2':None, 'CD2_1':None, 'CD2_2':None});
          else:
            fits.headeredit(  image=fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension'], values={'OBJECT':newobj});
          fits.correctcrpix(image=fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension'], shift=(fitsD[tagv].offx, fitsD[tagv].offy) );


          if(offxmn>fitsD[tagv].offx): offxmn=fitsD[tagv].offx;
          if(offymn>fitsD[tagv].offy): offymn=fitsD[tagv].offy;

          if(maxx<fitsD[tagv].offx+fitsD[tagv].nxny[0]): maxx=fitsD[tagv].offx+fitsD[tagv].nxny[0];
          if(maxy<fitsD[tagv].offy+fitsD[tagv].nxny[1]): maxy=fitsD[tagv].offy+fitsD[tagv].nxny[1];

          statimg=fits.statimage(image=fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension'], minval=-daopar.DAO_Par['montage2fill']/1e2, maxval=daopar.DAO_Par['montage2fill']/1e2);
          maxvalD[tagv]=statimg['max'];
          if(maxval<statimg['max']): maxval=statimg['max'];
          if(not fits.testimage(fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension'])): raise SkZpipeError("The image seems not valid end cicle!!!", exclocus=fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension']);   #@@@


        self.stdout.flush();
        self.offx, self.offy = offxmn, offymn;
        self.nxny=(maxx-offxmn, maxy-offymn);
        
        upperlim=max(upperlim, 1.1*maxval);
        print("Offset: {xoff} {yoff}\nSize: {nx} {ny}".format(xoff=self.offx, yoff=self.offy, nx=self.nxny[0], ny=self.nxny[1]), file=self.stdout);
       #Resizing substack to be all the same size
        for tagv in substacktagL:
          fits.resize(fitsD[tagv].stacked[idx]+bpar.SkZp_Par['fitsextension'],  (offxmn-fitsD[tagv].offx+1, offymn-fitsD[tagv].offy+1), (self.nxny[0],self.nxny[1]), None, -1e4, 1, fitsD[tagv].stacked[idx]+"R"+bpar.SkZp_Par['fitsextension']);
          fits.correctcrpix(fitsD[tagv].stacked[idx]+"R"+bpar.SkZp_Par['fitsextension'], (offxmn-fitsD[tagv].offx+1, offymn-fitsD[tagv].offy+1) );
            
        self.stdout.flush();
       #Averaging substacks
        funct.WaitStop(self.stacked[idx]);
        fits.average((lowerlim,upperlim, fillval), [fitsD[tagv].stacked[idx]+"R"+bpar.SkZp_Par['fitsextension'] for tagv in substacktagL], self.stacked[idx]+'0'+bpar.SkZp_Par['fitsextension']);  
        self.stdout.flush();

       #Sky addition
        fits.arith(self.stacked[idx]+"0"+bpar.SkZp_Par['fitsextension'], 'a', self.sky0, self.stacked[idx]+bpar.SkZp_Par['fitsextension']);
        if(not _opt.SkZp_Opt['Flg']['debug']): funct.clean_file([self.stacked[idx]+'0'+bpar.SkZp_Par['fitsextension']]);
  
    else:
####### NO SUBSTACKING ###########
      print(self.RunMontage(suff_idx=2, verb=verb, mask=mask), file=self.stdout);
    
    
  
