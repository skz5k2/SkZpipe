"""Module with class to elaborate photometric images
"""
import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy
import tempfile, traceback

from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters import options as _opt
from ..parameters.classes import bclasses
from ..parameters.classes import fileclass 
from .. import functions as funct




############
#Photo_Proc#
############



class PhotoProc(bclasses.Image):
    """Class to process an image using DAOPhot. Subclass of PhotoProc.

Parameters
----------
    data : dict or str
        Dictionary with  information about the image or the basename of the image
    runtype : str
        Name of the type of processing to apply.
    flag : str
        Flag for
    options : dict
        Dictionary with options as in internal option database

Attributes
----------
    SkZp_Opt : dict
        Dictionary
    fn : str
        Filename
    psfhwhm : tuple of 2 float
        HWHM in X and Y
    offx,offy : float
        Offset in X and Y
    step : str
    runtype: str
        Type of the run
    mstep : bool
        .
    auto : bool
        .
    lockfile : str
        .
    lock : bool
        .
    niter : int
        Number of iterations
    logfile : dict
        .
    oldbkup : str
        .
    stdout, stderr : output
        .
    error : 
        .
    runonram : dict
        .
    psfopt : str
        .
    fitt : float
        .
    firstap : float
        .
    var : int
        .
    maxapmag : float
        .
    PickCounter :  dict
        .
    PsfCounter : dict
        .
    nstar : dict of int value
        {'tot':0, 'psf0':0, 'psf':0}
    newstar=False
        .
    newstarfile=''
        Name of the file with new sources
    suffD : dict of str
        Dictionary of suffix


""";
    SkZp_Opt={}
    fn=None
    psfhwhm=(0,0)
    offx=None
    offy=None
    step=''
    runtype=''
    mstep=False
    auto=True

    lockfile=''
    lock=False
    niter=-1
    logfile={}
    oldbkup=''
    #outxt,runtime,runtimeT=[],[],[]
    stdout=bpar.SkZp_Par['stdout']
    stderr=bpar.SkZp_Par['stderr']
    error=None
    runonram={}
  
    psfopt=''
    fitt=0
    firstap=0
    var=0
    maxapmag=0
    PickCounter={}
    PsfCounter={}
    nstar={'tot':0, 'psf0':0, 'psf':0}
    #PsfLst=[]
    newstar=False
    newstarfile=''
    suffD={}

 ###
    def OptionGet(self, option=None, otype=None, raisexc=True):
        """Method version of options.OptionGet to use the class copy of options""";
        return _opt.OptionGet(option=option, otype=otype, optiondb=self.SkZp_Opt, raisexc=raisexc);

    def OptionPrint(self, option=None, otype=None, verb=True):
        """Method version of options.OptionPrint to use the class copy of options""";
        return _opt.OptionPrint(option=option, otype=otype, verb=verb, optiondb=self.SkZp_Opt);

    def OptionSet(self, option=None, value=None, otype=None, optdict=None):
        """Method version of options.OptionSet to use the class copy of options""";
        return _opt.OptionSet(option=option, value=value, otype=otype, optdict=optdict, optiondb=self.SkZp_Opt);

    def OptionFixCheck(self, raisexc=True):
        """Method version of options.OptionFixCheck to use the class copy of options""";
        return _opt.OptionFixCheck(optiondb=self.SkZp_Opt, raisexc=raisexc);
    def OptionPhotoFix(self, raisexc=True):
        """Method version of options.OptionPhotoFix to use the class copy of options""";
        return _opt.OptionPhotoFix(optiondb=self.SkZp_Opt, raisexc=raisexc);
  
 ###

    def SetLocSkZp_Opt(self, options=None, reset=False):   #RAISE SkZpipeErr
        """Set the local copy of option database

Parameters
----------
    options : dict
        Additional options to be set
    reset : bool
        Flag to reset an already existing class option database

""";
        if(self.SkZp_Opt):
            if(not reset):
                print("Class options already set. Use parameter `reset` to reset them or OptionSet method.", file=self.stdout);
                return;
        self.SkZp_Opt=copy.deepcopy(_opt.SkZp_Opt);
    #Reading options from image_name.opt
        _opt.OptionReadFile(self.fname+".opt", optiondb=self.SkZp_Opt);
    #Reading options passed during creation
        self.OptionSet(optdict=options);
        self.OptionPhotoFix();
      

#####

    def __init__(self, data=None, runtype='photo', flag='', options=None):
        """Initializing an object of Class PhotoProc

""";
        super().__init__(data);

        self.fn=self.fname;
   #deepcopy of SkZp_Opt and set opt for the image
        self.SetLocSkZp_Opt(options=options);

        self.stdout=bclasses.OutputPipe(otype='out');
        self.stderr=bclasses.OutputPipe(otype='err');

        self.suffD={'img':bpar.SkZp_Par['fitsextension'], 'src':None, 'aph':None, 'psf':None, 'fph':None, 'img:s':None, 'psfsrc':None, 
                'photofileclass':fileclass.basefile.PhotoFile, 'psffileclass':fileclass.basefile.PsfFile,}

        if(os.path.exists(self.fn+".SKIP")):
            raise SkZpipeSkip("", exclocus=self.fn);
        if(not os.path.exists(self.fn+self.suffD['img'])):
            raise IOError("!!!ERROR: The image {:}{:} doesn't exist!".format(self.fn, self.suffD['img']));
        if(self.fwhm<=0): raise ValueError(self.fn+" has a no-positive FWHM");
      

        if(re.search(self.suffD['img']+'$', self.fn)): self.fn=self.fn.split(self.suffD['img'])[0];

#    self.fns=self.fn+self.suffD['img:s'];
        self.outxt=[];
        self.runtime=[];
        self.runtimeT=[];
        self.logfile={};
        self.PickCounter={};
        self.PsfCounter={};
        self.nstar={'tot':0, 'psf0':0, 'psf':0};


        if(self.hgd==None): self.hgd=0;
        if(self.gain==None): self.gain=0;
        if(self.ron==None): self.ron=0;


        hgdM,gainM,ronM={},{},{}
        if(self.hgd==0):
            if(self.chip in hgdM):
                self.hgd=hgdM[self.chip]
            elif("{}:{}@{}".format(self.chip,self.filter,self.exptime) in hgdM):
                self.hgd=hgdM["{}:{}@{}".format(self.chip,self.filter,self.exptime)];
        if(self.hgd==0):
            raise SkZpipeError("High good datum has a wrong value <{}>".format(self.hgd), exclocus=self.fn);

        if(self.gain==0):
            if(self.chip in gainM):
                self.gain=gainM[self.chip]
            elif("{}:{}@{}".format(self.chip,self.filter,self.exptime) in gainM):
                self.gain=gainM["{}:{}@{}".format(self.chip,self.filter,self.exptime)];
        if(self.gain==0):
            raise SkZpipeError("Gain has a wrong value <{}>".format(self.gain), exclocus=self.fn);

        if(self.ron==0):
            if(self.chip in ronM):
                self.ron=ronM[self.chip]
            elif("{}:{}@{}".format(self.chip,self.filter,self.exptime) in ronM):
                self.ron=ronM["{}:{}@{}".format(self.chip,self.filter,self.exptime)];
        if(self.ron==0):
            raise SkZpipeError("Ron has a wrong value <{}>".format(self.ron), exclocus=self.fn);
  
    ##STARTING OPT###

        self.lockfile=self.fn+self.OptionGet('locking:ext', otype='S')
        if('force' in flag):
            funct.clean_file([self.lockfile]);
  ###END _INIT_####


#  def UpdateStoreFile(self):  #OUTXT
#    with open(self.fn+self.SkZp_Opt['S']['SkZp_log'], "a") as f_tmp:    #SkZpLOG 
#      if(self.runtype=='psfcal'):
#        f_tmp.write("{:8} {:d}   {:f}   {}\n".format(self.step, self.niter, self.PsfCounter['chi2'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')));
#      elif(self.runtype=='srclst'):
#        f_tmp.write("{:8} {:d}   {:f}   {}\n".format(self.step, self.niter,                       0, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')));
      
    
    def LockRun(self):
        if(self.lock): return
        if(os.path.exists(self.lockfile)):
            raise SkZpipeError("it seems that there is already a SkZp_pipeline running for the file {}!".format(self.fn), exclocus=self.fn);
        with open(self.lockfile, "w") as f_tmp:
            self.lock=True;
            f_tmp.write("1");
    
    def UnlockRun(self):
        if(self.lock):
            funct.clean_file([self.lockfile]);  ### MULTISTEP
            self.lock=False;

    def StoreLog(self):
        if(self.logfile):
            list_log=[];
            for tag in self.logfile:
                if(os.path.exists(self.logfile[tag])): list_log.append(self.logfile[tag]);
            if(list_log):
                if(self.error or self.SkZp_Opt['Flg']['debugging:log']):
                    now=datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    with tarfile.open(f"Log.{self.fn}.{self.runtype}_{self.step}{self.niter:02d}_{now}.tar.bz2", 'w:bz2') as tarlog:
                        for logf in list_log:
                            tarlog.add(logf)
                funct.clean_file(list_log);
            self.logfile.clear();
  
    def unsetrunonram(self):
        pass #redefined later

    def close(self):
        if(self.fn):
            self.StoreLog();
            runtime=sum(self.runtimeT);
            print(runtime,":",self.runtimeT, file=self.stdout)
            ####
            self.unsetrunonram()
            ####
            self.UnlockRun();
        self.fn=None;
        self.stdout.close();
        self.stderr.close();

    def exit_right(self):
        """Exit with success
""";
        if(self.fn):
            if(self.runtype == 'psfcal'):
                if(self.psfhwhm[0]>0 and self.psfhwhm[1]>0):
                    if('PSFFWHM'  in bpar.SkZp_Par['datatag']):
                        funct.InputDataEntryUpdate(entry=self.fn, newdata={'PSFFWHM': round(sum(self.psfhwhm),4) })
                    if('PSFELLIP' in bpar.SkZp_Par['datatag']):
                        funct.InputDataEntryUpdate(entry=self.fn, newdata={'PSFELLIP':round(1-min(self.psfhwhm)/max(self.psfhwhm), 6) }) 
                    if(abs(sum(self.psfhwhm)-self.fwhm)/self.fwhm > 0.2):
                        print(f">> WARNING: Initial FWHM extimation and calculated value differ more than 20%!   init:{self.fwhm:.2f}; psf:{sum(self.psfhwhm):.2f}", file=self.stdout); 
                if(not os.path.exists(self.fn+self.SkZp_Opt['S']['photo:psf:done'] )):
                    with open(self.fn+self.SkZp_Opt['S']['photo:psf:done'], 'w') as f_tmp:
                        f_tmp.write("{}\n".format(self.PsfCounter.get('chi2')));
            elif(self.runtype == 'srclst'):
                shutil.copy2(self.fn+self.suffD['fph'], self.fn+self.SkZp_Opt['S']['photo:ext:srclst']);
                if(not os.path.exists(self.fn+self.SkZp_Opt['S']['photo:srclst:done'] )):
                    with open(self.fn+self.SkZp_Opt['S']['photo:srclst:done'], 'w') as f_tmp:
                        f_tmp.write("{lenf}\n".format(lenf=funct.get_num_lines(self.fn+self.SkZp_Opt['S']['photo:ext:srclst'])));

    def exit_wrong(self):
        """Exit with failure
""";
        if(self.fn):
            if(self.SkZp_Opt['Flg']['debug']): print("CHECK RUNTYPE", self.runtype,  "\nCHECK STEP", self.step, file=self.stdout)
            if(self.runtype=='psfcal'): #If to calculate PSF
                funct.clean_file([(self.fn,self.suffD['fph']), (self.fn,self.suffD['psf'])], suff='_dbg' if(self.SkZp_Opt['Flg']['debug']) else None);
            elif(self.runtype=='srclst'): #if to calculate source list
                funct.clean_file([(self.fn,self.SkZp_Opt['S']['photo:ext:srclst'])], suff='_dbg' if(self.SkZp_Opt['Flg']['debug']) else None);
            elif(self.runtype=='photo'): #if to obtain photometry
                if(self.step=='GetFph'):                #psf-fitting
                    funct.clean_file([(self.fn,self.SkZp_Opt['S']['photo:ext:fitting'])], suff='_dbg' if(self.SkZp_Opt['Flg']['debug']) else None);
                elif(self.step=='GetAph'):              #aperture
                    funct.clean_file([(self.fn,self.SkZp_Opt['S']['photo:ext:aperture'])], suff='_dbg' if(self.SkZp_Opt['Flg']['debug']) else None);


    def __exit__(self, exc_type, exc_value, exc_tb):
        if(exc_type!=None):
            self.exit_wrong();
            self.close();
            return False;
        else:
            self.exit_right();
            self.close();

    def __enter__(self):
        return self;

#  def __del__(self):
#    self.close();

    def flush_out(self):
        self.stdout.flush();
        self.stderr.flush();
  ##END Special Methods###

#ON-RAM METHOD
    ####
    def setrunonram(self,*, flag=None, needed=None):
        """Method to prepared everything to run the photometric procedure in a filesystem on RAM.
    It create the directory for the image and copy the basic files listed in attribute 'suffD'.

Parameters
----------
    flag : bool
        If to run the procedure on RAM. Default value from option 'speedingup:ramdisk'.
    needed : list or tuple
        List of files or extensions of files (starting with dot) that the procedure needs.

"""
        _name_='PhotoProc.setrunonram'
        if(self.runonram): return self.runonram #already done: skip
        if(flag is None): flag=self.OptionGet('speedingup:ramdisk', otype='Flg')
        if(not flag): return #NO, skip
        if(not needed): needed=[]

        tocopy=[]
        for key,suff in self.suffD.items():
            if(isinstance(suff,str)):
                fname=self.fn+suff
                if(suff[0]!='.'):
                    fname+=self.suffD[ key.split(':', maxsplit=1)[0] ]
                tocopy.append(fname)

        self.runonram=funct.setrunonram(procedure=self.fn, flag=flag, needed=tocopy+needed)
        if(self.OptionGet('debug', otype='Flg')): 
            print(f"### {self.fn} is going on RAM: {os.getcwd()}\n{flag} ; {tocopy}+{needed} ; {self.runonram}", file=bpar.SkZp_Par['stdout'], flush=True)

        return self.runonram

    ####
    def unsetrunonram(self):
        """Method to undo the environment used to run the photometric procedure in a filesystem on RAM

        """
        _name_='PhotoProc.unsetrunonram'
        if(self.runonram):
            funct.unsetrunonram(self.runonram)

            self.runonram={}



    ####
    def SetOutput(self, output=None, default=None):
        """Return filename according two rules: 
    if `output` is not given, `default` is used; 
    if output starts with a dot ('.'), it will be used as extension and concatenate to the image name.

Parameters
----------
    output : str, None
        String with the filename or the extension.
    default : str, None
        String with the default value for filename or extension.

Return
------
    x : str
        Filename.
""";
        _name_='PhotoProc.SetOutput';
        if(output is None): output=default;
        if(not isinstance(output, str)): raise TypeError(_name_+": output must be  the filename or the extension with initial dot (e.g. .als)");
        if(output[0]=='.'): output=self.fn+output;
        return output;

    ####
    def ChangeRuntype(self, runtype=None):
        if(runtype):
            self.runtype=runtype;
            print("runtype set to", runtype, file=self.stdout);
            return self.runtype;

    ####
    def applymagcorr(self, suff=None, ftype=None, exptime=False, apcorr=False, atmext=(0,0), extra=(0,0), output='', outsuff=''):
        """Apply all the classical magnitude correction: exposure time, airmass correction, aperture correction. It is possible to apply an additional extra correction.

Parameters
----------
    suff : str
        Suffix of the file to which applying the corrections (this has to be given. 
    ftype : 
        File type (if the extension is not standard).
    exptime : bool
        Flag to determine if to apply exposure time correction (value obtain from tag:EXPTIME)
    apcorr : bool
        Flag to determine if to apply aperture correction (value obtain from tag:APCORR)
    atmext : float, tuple of float
        Atmospheric extinction coefficient and its error to be used for the airmass correction (0 for no correction).
    extra : float, tuple of float
        Additional correction that is add to the source magnitude
    output : str
        Name of the file where store the corected photometry.
    outsuff : str
        Suffix add to the input name if `output` is not provide. Default `suff`+'_0'
""";
        _name_='PhotoProc.applycorrection';
        if(not isinstance(suff, str)): raise TypeError(_name_+": `suff` must be a string <{}>".format(repr(suff)));
#    if(not isinstance(ftype)): raise TypeError(_name_+": `` must be a <{}>".format());
        if(not isinstance(exptime, bool)): raise TypeError(_name_+": `exptime` must be a bool <{}>".format(repr(exptime)));
        if(not isinstance(apcorr, bool)): raise TypeError(_name_+": `apcorr` must be a bool <{}>".format(repr(apcorr)));
        if(not isinstance(atmext, (float, tuple))): raise TypeError(_name_+": `atmext` must be a float or a tuple of two floats <{}>".format(repr(atmext)));
        if(isinstance(atmext, float)): atmext=(atmext,0.);
        if(not isinstance(extra, (int,float, tuple))): raise TypeError(_name_+": `extra` must be a float or a tuple of two floats <{}>".format(repr(extra)));
        if(isinstance(extra, float)): extra=(extra,0.);
        if(output is not None and not isinstance(output, str)): raise TypeError(_name_+": `output` must be a string <{}>".format(repr(output)));
        if(not isinstance(outsuff, str)): raise TypeError(_name_+": `outsuff` must be a string <{}>".format(repr(outsuff)));

        if(not output):  output=self.fn+(outsuff if(outsuff) else suff+'_0');

        error=0;
        if(exptime):
            if(not self.exptime or not isinstance(self.exptime, float)): raise ValueError(_name_+": 'exptime' has wrong value <{}>".format(self.exptime), exclocus=self.fname);
            exptime= 1;
        else: exptime= 0;
        if(apcorr):
            if(not self.apcorr or not isinstance(self.apcorr, tuple)): raise SkZpipeError(_name_+": 'apcorr' has wrong value<{}>".format(self.apcorr), exclocus=self.fname);
            apcorr= 1;
        else: apcorr= 0;
        corr=exptime*2.5*math.log(self.exptime, 10) + apcorr*self.apcorr[0]  -atmext[0]*self.airmass +extra[0];
        error=extra[1];

        with self.suffD['photofileclass'](ftype=ftype, fname=self.fn+suff) as phofile:
            phofile.read();
            phofile.magshift(magshift=corr, error=error);
            phofile.writefile(output, overwrite=True);
        print("applying mag corr for:", 
            f"exptime {2.5*math.log(self.exptime, 10):.6f};" if(exptime) else '', 
            f"apcorr {self.apcorr[0]};" if(apcorr) else '', 
            f"airmass {-atmext[0]*self.airmass};" if(atmext) else '', 
            "others {extra[0]};" if(extra[0]) else'', file=self.stdout);

####################
####################

    def RunStepGround(self):
        raise SkZpipeError(f"This subclass has not defined the step `Ground`", exclocus=self.fn)
    def RunStepRefinePSF(self):
        raise SkZpipeError(f"This subclass has not defined the generic step `RefinePSF`", exclocus=self.fn)
    def RunStepGetFph(self):
        raise SkZpipeError(f"This subclass has not defined the step `GetFph`", exclocus=self.fn)
    def RunStepGetAph(self):
        raise SkZpipeError(f"This subclass has not defined the step `GetAph`", exclocus=self.fn)
##
    def RunStepAddCoo(self):
        """Run the step to obtain  

Parameters
----------
"""
        self.step="AddCoo"
        self.RunStepRefinePSF()

##
    def RunStepAddFph(self):
        """Run the step to obtain  

Parameters
----------
"""
        self.step="AddFph"
        self.RunStepRefinePSF()

##
    def RunStepChkAdd(self):
        """Run the step to obtain  

Parameters
----------
"""
        self.step="ChkAdd"
        self.RunStepRefinePSF()

##
    def RunStepRefine(self):
        """Run the step to refine psf calculation and preliminary psf-fitting photometry with Allstar

"""
        self.step="Refine"
        self.RunStepRefinePSF()

    #######
    def RunStep(self, Step=None):   #RAISE SkZpipeErr
        """Run the given step

Parameters
----------
    Step : str, None
        Name of the step.
"""
        _name_='PhotoProc.RunStep'
        if(Step!=None or self.SkZp_Opt['L']['photo:Steps:'+self.runtype]):
            if(Step is None):
                self.step=self.SkZp_Opt['L']['photo:Steps:'+self.runtype].pop(0);
            else:
                self.step=Step;
            if(self.step=="Ground"): return self.RunStepGround();
            elif(self.step=="AddCoo"): return self.RunStepAddCoo();
            elif(self.step=="AddFph"): return self.RunStepAddFph();
            elif(self.step=="ChkAdd"): return self.RunStepChkAdd();
            elif(self.step=="Refine"): return self.RunStepRefine();
            elif(self.step=="GetFph"): return self.RunStepGetFph();
            elif(self.step=="GetAph"): return self.RunStepGetAph();
            else: raise SkZpipeError(f"{_name_}: Wrong step name", exclocus=self.fn);
        else: return -1;

    #######
    def RunSteps(self, steps=None):   #RAISE SkZpipeErr
        """Run the given list of steps

Parameters
----------
    steps : list, None
        List of steps.
"""
        _name_='PhotoProc.RunSteps'
        if(steps):
            if(not isinstance(steps, list)):
                if(isinstance(steps, str)): steps=[steps];
                else: raise TypeError(f"{_name_}: wrong type for `steps`. It must be a list of strings or string with the name of the step(s).   < {steps} >")
            self.SkZp_Opt['L']['photo:Steps:'+self.runtype]=steps.copy();
        self.mstep=True;
        print('==>',self.SkZp_Opt['L']['photo:Steps:'+self.runtype],'<==', file=self.stdout)

        #check for PSF already calculated: 'photo:psf:done', 'photo:psf:keep' 
        if(self.runtype=='psfcal' and os.path.exists(self.fn+self.OptionGet('photo:psf:done', otype='S')) and self.OptionGet('photo:psf:keep', otype='Flg')):
            if(not os.path.exists(self.fn+self.suffD['psf'])): 
                raise SkZpipeError("The image {img} should have already a valid PSF calculated previously, but it is missing!", exclocus=self.fname);
            print(f"The image {self.fn} has already a valid PSF calculated previously. The option for the protection of the result ('photo:psf:keep') is active.", file=self.stdout)
            #get PSF data
            with self.suffD['psffileclass'](self.fn+self.suffD['psf']) as psffile:
                self.psfhwhm = (psffile.xhwhm, psffile.yhwhm)

        #check for source-list already calculated: 'photo:psf:done', 'photo:psf:keep' 
        elif(self.runtype=='srclst' and os.path.exists(self.fn+self.SkZp_Opt['S']['photo:srclst:done']) and self.SkZp_Opt['Flg']['photo:srclst:keep']):
            print(f"The image {self.fn} has already a valid source list calculated previously. The option for the protection of the result ('photo:srclst:keep') is active.", file=self.stdout)

        else:     
            self.LockRun()
            self.setrunonram()
            while(self.SkZp_Opt['L']['photo:Steps:'+self.runtype]):
                self.RunStep()

        self.mstep=False


