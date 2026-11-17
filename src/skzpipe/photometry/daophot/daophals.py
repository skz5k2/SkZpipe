###DpAls.py###
import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy
import tempfile, traceback

from ...exceptions import *
from ...parameters import basicpar as bpar
from ...parameters import options as _opt
from ...parameters import daoparameters as daopar
from ...parameters.classes.fileclass import daofile
from ... import functions as funct
from ..photo import *
from . import daofunctions as daofunct
from ... import match



def SetSkZp_Opt(optiondb=None):   #RAISE SkZpipeErr
    """Set SkZp_Opt properly for DAOPhot/Allstar

Parameters
----------
    optiondb : dict, None
        Dictionary with the options. Default is SkZp_Opt

Return
------
    None

""";
    if(optiondb is None): optiondb=_opt.SkZp_Opt;
    for key in ['photo:DAO:pickdeltamag','photo:fittingradius','photo:psf:psfradius','photo:in-outskyradius','photo:psf-inskyradius'] + [ 'photo:thre:'+rt for rt in bpar.SkZp_Par['photo:runtypelist'] ]:
        if(key in optiondb['F']): optiondb['F'][key]= round(optiondb['F'][key], 2);
    optiondb['L']['photo:DAO:varpsf']=[ int(x) for x in optiondb['L']['photo:DAO:varpsf'] ];
    for key in ['photo:DAO:daophot_opt','photo:DAO:photo_opt','photo:DAO:allstar_opt']:
        while('' in optiondb['L'][key]): optiondb['L'][key].remove('');
    for rt in bpar.SkZp_Par['photo:runtypelist']:
        for key in optiondb['L']['photo:Steps:'+rt]:
            if(not key in bpar.SkZp_Par['photo:StepL']):
                key='';
                break;
        if(not key): optiondb['L']['photo:Steps:'+rt]=[];
    
    if(optiondb['S']['progr:path:dir'] and optiondb['S']['progr:path:dir'][-1]!=os.path.sep): optiondb['S']['progr:path:dir']+=os.path.sep;
    if(optiondb['S']['progr:path:DAO'] and optiondb['S']['progr:path:DAO'][-1]!=os.path.sep): optiondb['S']['progr:path:DAO']+=os.path.sep;

    
    if(optiondb['I']['photo:psf:starmin']>=optiondb['I']['photo:psf:starmax'] or optiondb['I']['photo:psf:starmin']>=optiondb['I']['photo:psf:starinit'] or optiondb['I']['photo:psf:starmax']>=optiondb['I']['photo:psf:starinit']):
        raise SkZpipeError("The minimum number of psf stars ({min}) must be lesser than their inital number ({num}) or the maximum number of them to be left after the first psf ({max}), which must be lesser than initial number.".format(min=optiondb['I']['photo:psf:starmin'], max=optiondb['I']['photo:psf:starmax'], num=optiondb['I']['photo:psf:starinit']));
    for psf in [optiondb['S']['photo:DAO:psfdef']]+optiondb['L']['photo:DAO:psfother']:
        if(not psf in daopar.DAO_Par['psfanaltype']):
            raise SkZpipeError("Wrong PSF analytic type function!");

    if(optiondb['Flg']['debugging:full']): optiondb['Flg']['debugging:log']=True;
    
    if(optiondb['L']['photo:aperture']):
        try:
            optiondb['L']['photo:aperture']=[float(x) for x in optiondb['L']['photo:aperture']];
            if(optiondb['L']['photo:aperture'][0]<0):
                optiondb['L']['photo:aperture']=[int(optiondb['L']['photo:aperture'][0])];
            if(optiondb['L']['photo:aperture'][0]==-1): optiondb['L']['photo:aperture']=[daopar.DAO_Par['ApNum']];
            elif(len(optiondb['L']['photo:aperture'])==1 and optiondb['L']['photo:aperture'][0]==0): optiondb['L']['photo:aperture']=[];
        except:
            if(re.search("^N|n|0|F|f",optiondb['L']['photo:aperture'][0])):
                optiondb['L']['photo:aperture']=[];
            elif(':' in optiondb['L']['photo:aperture'][0]):
                tmpl=[float(x) for x in optiondb['L']['photo:aperture'][0].split(':')];
                if(len(tmpl)==2 or tmpl[2]>12): tmpl.append(12);
                else: tmpl[2]=int(tmpl[2]);
                optiondb['L']['photo:aperture']=[];
                step=(tmpl[1]-tmpl[0])/(tmpl[2]-1);
                for ii in range(tmpl[2]):
                    optiondb['L']['photo:aperture'].append(round(tmpl[0]+ii*step,2));
            else: optiondb['L']['photo:aperture']=[12];

    optiondb['DI']['progr:timeout']['daophot']=int( funct.getfloat( optiondb['DI']['progr:timeout'].get('daophot'), bpar.SkZp_Par['timeout']['daophot']) );
    optiondb['DI']['progr:timeout']['allstar']=int( funct.getfloat( optiondb['DI']['progr:timeout'].get('allstar'), bpar.SkZp_Par['timeout']['allstar']) );


############
#DAOp_Proc#
############



class DAOp_Proc(PhotoProc):
    """Class to process an image using DAOPhot. Subclass of PhotoProc (see it also).

Parameters
----------
    data : dict or str
        Dictionary with  information about the image or the basename of the image.
    runtype : str
        Name of the type of processing to apply.
    flag : str
        Flag for
    options : dict
        Dictionary with options as in internal option database

Attributes
----------
    daophot_opt, photo_opt, allstar_opt : list
        List with option to pass to DAOPhot (the addditional dictionaries daophot_optD,photo_optD,allstar_optD are used to clean them).


""";
    daophot_optD,photo_optD,allstar_optD={},{},{};
    daophot_opt, photo_opt, allstar_opt=[],[],[];
    PsfLst=[];
    newstar=False;


    def DAOoptReset(self):
        """Reset the local copy of DAOPhot options.
""";
        self.daophot_optD={};
        self.photo_optD={};
        self.allstar_optD={};
        self.daophot_opt=[];
        self.photo_opt=[];
        self.allstar_opt=[];

    def DAOoptReload(self):
        """Reset the local copy of DAOPhot options.
""";
        self.daophot_opt=["OPT",""]+(list(self.daophot_optD.values()) if(self.daophot_optD) else []);
        self.photo_opt=list(self.photo_optD.values()) if(self.photo_optD) else [];
        self.allstar_opt=list(self.allstar_optD.values()) if(self.allstar_optD) else [];

    def DAOoptClean(self):
        """Clean DAOPhot option leaving only the last version of every option.
""";
        self.daophot_optD={};
        for opt in self.daophot_opt:
            if(opt!='OPT' and opt!=''): daofunct.DAOoptStore(self.daophot_optD, opt, env='daophot');

        self.photo_optD={};
        for opt in self.photo_opt:
            if(opt!='OPT' and opt!=''): daofunct.DAOoptStore(self.photo_optD, opt, env='photo');

        self.allstar_optD={};
        for opt in self.allstar_opt:
            if(opt!='OPT' and opt!=''): daofunct.DAOoptStore(self.allstar_optD, opt, env='allstar');
        
        self.DAOoptReload();


    def DAOoptSetBasic(self):
        """Set options for daophot (daophot.opt).
""";
        self.fitt=self.SkZp_Opt['F']['photo:fittingradius'] if(self.SkZp_Opt['F']['photo:fittingradius']>0) else self.SkZp_Opt['F']['photo:fittingfwhmratio']*self.fwhm;   #fitting radius, according Stetson
        self.psfrad=self.SkZp_Opt['F']['photo:psf:psfradius'];                        #3-4 FWHM, but a value of 15-20 is suggested (check with imexamine where the psf is flat)

        self.firstap=round(self.fitt,2);                #according theory
        self.israd=round(self.psfrad+self.SkZp_Opt['F']['photo:psf-inskyradius'], 3);
        osradmax=round(math.sqrt(daopar.DAO_Par['maxskyarea']/math.pi+self.israd*self.israd)-1, 2);
        self.osrad=self.israd+self.SkZp_Opt['F']['photo:in-outskyradius'];
        if(self.osrad>osradmax):
            self.osrad=osradmax;
            print("!!!Too high osrad ({0:.3f}): put equal to the maximum value ({1:.2f})".format(self.osrad, osradmax), file=self.stdout);
        if((self.osrad-self.israd)<self.SkZp_Opt['F']['photo:inoutradiusmin']):
            raise SkZpipeError("Inner ({inr}) and outer ({outr}) sky radius differ less than {delta}!".format(inr=self.israd, outr=self.osrad, delta=self.SkZp_Opt['F']['photo:inoutradiusmin']), exclocus=self.fn);
        self.osrad=round(self.osrad, 3);
    
        if(self.firstap>self.psfrad):
            raise SkZpipeError("first aperture ({fap}) is greater than the psf radius ({prad})!".format(fap=self.firstap, prad=self.psfrad), exclocus=self.fn);


    def SetDaophotOpt(self):
        """Set options for daophot (daophot.opt).
""";
        optL=[];

        if('photo:DAO:daophot_opt' in self.SkZp_Opt['L'] and self.SkZp_Opt['L']['photo:DAO:daophot_opt']):
            optL.extend(self.SkZp_Opt['L']['photo:DAO:daophot_opt']);
    
        self.DAOoptSetBasic();
      
        optL.extend(["WA=-2", "EX=9"]);  #=>WAtch progress , EXtra psf cleaning passes
    
        optL.append("HI={:.2f}".format(self.hgd));  #=>HIgh good datum (adu)
        optL.append("GA="+str(self.gain));    #=>GAin
        optL.append("RE={:.4f}".format(self.ron/self.gain));  #=>REad out noise
    
        optL.append("FW={:.4f}".format(self.fwhm));    #=>FWHM
        optL.append("FI={:.4f}".format(self.fitt));    #=>FItting radius
    
        thre=self.OptionGet('photo:thre:'+self.runtype, raisexc=False);  #=>THreshold
        if(thre):  optL.append("TH="+str(thre));  #=>THreshold
    
        if(self.runtype=='psfcal'):
            self.psfopt=self.PsfLst[0];
            if(self.psfopt in daopar.DAO_Par['psfanaltype']):
                optL.append("AN="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));  #=>ANalitic function
            else:
                raise SkZpipeError("Wrong PSF analytic type function!", exclocus=self.fn)
    
        optL.append("PS="+str(self.psfrad));   #=>PSf radius
        #if(self.psfrad>daopar.DAO_Par['maxpsfrad']): self.psfrad=daopar.DAO_Par['maxpsfrad']; print("!!!Too high psfrad({:.2f}): put equal to the maximum value ({:2f})".format(self.psfrad, daopar.DAO_Par['maxpsfrad']), file=self.stdout);
        for ii in range(len(optL)):
            opt=daofunct.DAOoptCheck(opt=optL[ii], env='daophot', autofix=self.SkZp_Opt['Flg']['photo:autofix'], raisexc=True);
            if(opt[0]!=None): self.daophot_opt.append(opt[0]);


    def SetPhotoOpt(self):
        """Set options for daophot.photometry (photo.opt).
""";
        optL=[];
        if('photo:DAO:photo_opt' in self.SkZp_Opt['L'] and self.SkZp_Opt['L']['photo:DAO:photo_opt']):
            optL.extend(self.SkZp_Opt['L']['photo:DAO:photo_opt']);
    
        self.DAOoptSetBasic();
        
        self.apL=[];
        if(self.SkZp_Opt['L']['photo:aperture']):
            if(self.SkZp_Opt['L']['photo:aperture'][0]<0):
                stepap=(self.israd-self.firstap)/(-self.SkZp_Opt['L']['photo:aperture'][0]-1);
                if(stepap<.1): stepap=.1;
                for ii in range(self.SkZp_Opt['L']['photo:aperture'][0]):
                    self.apL.append(round(self.firstap+ii*stepap, 2));
            else:
                self.apL=self.SkZp_Opt['L']['photo:aperture'].copy();
            self.apL.append(0);
            if(self.apL[0]==0): self.apL[0]=self.firstap; 
            for ii in range(min(12,len(self.apL))):
                if(self.apL[ii]>self.israd):
                    self.apL[ii]=self.israd;
                    self.apL[ii+1]=0;
                optL.append(hex(161+ii)[2:].upper()+"="+str(self.apL[ii]));   #=> aperture AXX=
                if(self.apL[ii]==0): break;
        else:
            self.apL=[self.firstap];
            optL.extend(["A1="+str(self.firstap),"A2=0"]);   #=> A1=  A2=0
        if(0 in self.apL): self.apL=self.apL[0:self.apL.index(0)];
    
        optL.append("IS="+str(self.israd));  #=> IS Inner Sky radius
        optL.append("OS="+str(self.osrad));  #=> OS Outer Sky radius
        for ii in range(len(optL)):
            opt=daofunct.DAOoptCheck(opt=optL[ii], env='daophot', autofix=self.SkZp_Opt['Flg']['photo:autofix'], raisexc=True);
            if(opt[0]!=None): self.photo_opt.append(opt[0]);

    def SetAllstarOpt(self):
        """Set options for allstar (allstar.opt).
""";
        optL=[];
        if('photo:DAO:allstar_opt' in self.SkZp_Opt['L'] and self.SkZp_Opt['L']['photo:DAO:allstar_opt']):
            optL.extend(self.SkZp_Opt['L']['photo:DAO:allstar_opt']);

        self.DAOoptSetBasic();

        optL.extend(["WA=0", "RE=1"]);
        optL.append("FI={:.4f}".format(self.fitt));   #Seems to have a strong influence on the errror of the brighter stars

        optL.append("IS=1");                  #according to Stetson
        optL.append("OS="+str(self.osrad));
        for ii in range(len(optL)):
            opt=daofunct.DAOoptCheck(opt=optL[ii], env='allstar', autofix=self.SkZp_Opt['Flg']['photo:autofix'], raisexc=True);
            if(opt[0]!=None): self.allstar_opt.append(opt[0]);

######
#INIT#
######

    def __init__(self, data=None, runtype='psfcal', flag='', options=None):   #RAISE SkZpipeErr IOError SkZpipeWarn
        """Initializing an object of Class DAOp_Proc

""";

        if(runtype is None or runtype in bpar.SkZp_Par['photo:runtypelist']):
            self.runtype=runtype;
        else:
            raise SkZpipeError("Wrong runtype <{}>. Valid values are {}".format(runtype, ", ".join(bpar.SkZp_Par['photo:runtypelist'])));
        err_data_msg=" It needs the tags: NAME, FWHM, [CHIP, HIGH, RON, GAIN, FILTER, EXPTIME, [AV,SM, STKOFF]]";
  ####
        super().__init__(data=data, options=options) #the __init__ of Image  will check and retrieve the data as dict
  ####
        self.fn=self.fname;
        self.suffD.update(daopar.DAO_Par['suffix'])
        self.suffD['photofileclass']=daofile.DAOPhotoFile
        self.suffD['psffileclass']  =daofile.DAOPsfFile
  ####

        if(re.search(self.suffD['img']+'$', self.fn)): self.fn=self.fn.split(self.suffD['img'])[0];
        print("\nInitializing image {img}  at {date}".format(img=self.fn, date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), file=self.stdout);

        self.fns=self.fn+self.suffD['img:s'];


        if(abs(self.bitpix)!=32):
            raise SkZpipeSkip("Wrong bitpix data type for DAOPhot!", exclocus=self.fn);
        if(len(self.fn+self.suffD['img'])>daopar.DAO_Par['namemaxlen']):
            raise SkZpipeError("{} is too long! Maximum allowed length is {:d} characters.".format(self.fn, daopar.DAO_Par['namemaxlen']-1-4), exclocus=self.fn);
      


        if(self.dataframe['AV,SM']): self.SkZp_Opt['S']['photo:averagedsummed']=self.dataframe['AV,SM'];
        if("srclst" in runtype):
            if(self.dataframe['STKOFF']!=None):
                (self.offx, self.offy)= tuple([int(off) for off in self.dataframe['STKOFF'].split(',')]);
            else:
                (self.offx, self.offy)= (0,0);

        hgdM,gainM,ronM={},{},{}
        if(self.hgd==0):
            if(self.chip in hgdM):
                self.hgd=hgdM[self.chip]
            elif("{}:{}@{}".format(self.chip,self.filter,self.exptime) in hgdM):
                self.hgd=hgdM["{}:{}@{}".format(self.chip,self.filter,self.exptime)];
        if(self.hgd==0):
            raise ValueError(self.fn+": High good datum has a wrong value <{hgd}>".format(hgd=self.hgd));

        if(self.gain==0):
            if(self.chip in gainM):
                self.gain=gainM[self.chip]
            elif("{}:{}@{}".format(self.chip,self.filter,self.exptime) in gainM):
                self.gain=gainM["{}:{}@{}".format(self.chip,self.filter,self.exptime)];
        if(self.gain==0):
            raise ValueError(self.fn+":Gain has a wrong value <{gain}>".format(gain=self.gain));

        if(self.ron==0):
            if(self.chip in ronM):
                self.ron=ronM[self.chip]
            elif("{}:{}@{}".format(self.chip,self.filter,self.exptime) in ronM):
                self.ron=ronM["{}:{}@{}".format(self.chip,self.filter,self.exptime)];
        if(self.ron==0):
            raise ValueError(self.fn+": RON has a wrong value".format(ron=self.ron));
  
    ##STARTING OPT###

        if(self.runtype=='psfcal'):
            self.PsfLst=[self.SkZp_Opt['S']['photo:DAO:psfdef']];
            self.PsfLst.extend(self.SkZp_Opt['L']['photo:DAO:psfother']);
        else:
            self.PsfLst=[];

        self.DAOoptReset();
        self.DAOoptReload();

   #DAOPHOTO.OPT
        self.SetDaophotOpt();

   #PHOTO.OPT
        self.SetPhotoOpt();
  
   #ALLSTAR.OPT
        self.SetAllstarOpt();
   ##ENDING OPT###

        self.lockfile=self.fn+self.OptionGet('locking:ext', otype='S')
        if('force' in flag):
            funct.clean_file([self.lockfile]);
  #################
  ###END _INIT_####
  #################

    def UpdateStoreFile(self):  #OUTXT
        with open(self.fn+self.SkZp_Opt['S']['SkZp_log'], "a") as f_tmp:    #SkZpLOG 
            chi2=0;
            if(self.runtype=='psfcal'):
                chi2=self.PsfCounter['chi2'];
            now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f_tmp.write(f"Photo {self.runtype:5} {self.step:8} {self.niter:3d}   {chi2:6.5f}   {now}\n")
      
    def SetVar(self):
        self.var=0 if(self.step=="Ground") else 1;
        if(len(self.SkZp_Opt['L']['photo:DAO:varpsf'])>self.niter):
            self.var=self.SkZp_Opt['L']['photo:DAO:varpsf'][self.niter];
        elif(self.SkZp_Opt['L']['photo:DAO:varpsf']):
            self.var=self.SkZp_Opt['L']['photo:DAO:varpsf'][-1];
        self.daophot_opt.append("VAR="+str(self.var));
    
    def SetOptIter(self):
        if(self.runtype=='psfcal'):
            self.SetVar();
            self.psfopt=self.PsfLst[0];
            if(self.psfopt in daopar.DAO_Par['psfanaltype']):
                self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));
            else:
                raise SkZpipeError("Wrong PSF analytic type function!", exclocus=self.fn)
        if(self.step=="Ground"):
            pass;
        elif(self.step=="AddCoo"):
            pass;
        elif(self.step=="AddFph"):
            pass;
        elif(self.step=="ChkAdd"):
            pass;
        elif(self.step=="Refine"):
            pass;

    def check_psffile(self, var=-1, raisexc=True):   #RAISE SkZpipeErr
        psfile=self.fn+self.suffD['psf'];
        if(psfile):
            size=funct.get_num_lines(psfile);
            if(size<daopar.DAO_Par['psfheader'] or (var>=0 and size==daopar.DAO_Par['psfheader'])):  #here it create the psf, so var is always reffered to the psf in use
                if(raisexc):
                    raise SkZpipeError("file {psffile} has some problems with size <{size}>!".format(psffile=psfile, size=size), exclocus=self.fn);
                else:
                    return 1;
            elif(raisexc==False):
                return 0;
          

    def StartStep(self):   #RAISE SkZpipeErr
        if(self.step in bpar.SkZp_Par['photo:StepL']):
            self.LockRun()
            #self.setrunonram()

            self.error=None;
            if(self.step=='Ground'):
                self.niter=0;
            elif(self.step in ('GetFph', 'GetAph')):
                self.niter=0;
            elif(self.niter>=0):
                self.niter+=1;
            else:
                if(not os.path.exists(self.fn+self.SkZp_Opt['S']['SkZp_log'])):     #SkZpLOG
                    raise SkZpipeError("!!!The SkZpipeline log-file doesn't exists!", exclocus=self.fn);
                with open(self.fn+self.SkZp_Opt['S']['SkZp_log']) as f_tmp:
                    self.niter=int(f_tmp.readlines()[-1].split()[1])+1;
            self.runtime=[];
            
            daofunct.DAOoptFileInitialize();
            
            outxt="==>  {:} {:.2f} {:10}   i:{:d} ".format(self.fn, self.fwhm, self.step, self.niter);
            funct.clean_file([self.fns+self.suffD['psf'], self.fns+self.suffD['fph']]);
            if("Ground" in self.step):
                if(self.runtype=='psfcal'):
                    funct.clean_file([self.fn+self.suffD['psfsrc'], self.fn+self.suffD['psf'], self.fn+self.suffD['fph'], self.fns+self.suffD['img']]);
                elif(self.runtype=='srclst'):
                    pass;
                    #funct.clean_file([]);
            else:
                if(self.runtype=='psfcal'):
                    daofunct.Dao_check_file([self.fn+".lst", self.fn+".als", self.fns+self.suffD['img']]);
                    self.check_psffile();
                elif(self.runtype=='srclst'):
                    if(self.step=='GetFph'): self.check_psffile();   #;daofunct.Dao_check_file([self.fn+".als", self.fns+".fits"]);
                
#        shutil.copy(self.fn+".coo", self.fn+".coo."+str(self.niter));   #BACKUP old list
#        shutil.copy(self.fn+".als", self.fn+".als."+str(self.niter));   #BACKUP old list
                if('AddFph' in self.step):
                    self.SkZp_Opt['S']['newsrcto']='fph';
                elif('AddCoo' in self.step):
                    self.SkZp_Opt['S']['newsrcto']='src';
        
            funct.clean_file(glob.glob(self.fn+".Log"+"*"));
            if(self.runtype=='psfcal'):
                if(self.niter>0):
                    ochi2=self.PsfCounter['chi2'];
                self.PsfCounter={'chi2':-1, 'chi0':-1, 'countpsf':0, 'failedpsf':0, 'nes':False, 'flag':1, 'firstgoodpsf':99}
                self.PickCounter={'pickmag':20, 'pps':self.SkZp_Opt['I']['photo:psf:starinit'], 'mxps':self.SkZp_Opt['I']['photo:psf:starmax'], 'iter':0, 'flag':True}
                if(self.niter>0):
                    self.PsfCounter['chi0']=ochi2;
            self.SetOptIter();
            self.flush_out();
            self.outxt.append(outxt);
            return outxt;
        else:
            return -1;
        
    
    def GoodEndStep(self):
        if(self.oldbkup):
            funct.clean_file([self.oldbkup]);
        bkuplst=[];
        bkuplst0=[self.fn+self.suffD['src'], self.newstarfile, self.fn+self.suffD['aph'], self.fn+self.suffD['fph'], self.fn+self.suffD['psf'], self.fn+self.SkZp_Opt['S']['SkZp_log']];
        if(self.runtype=='psfcal'):
            bkuplst0.extend([self.fn+".lst"])
        for fnm in bkuplst0:
            if(os.path.exists(fnm) and not fnm in bkuplst): bkuplst.append(fnm)
        if(self.SkZp_Opt['Flg']['backup:image']): 
            for fnm in [self.fns+self.suffD['img']]:
                if(os.path.exists(fnm) and not fnm in bkuplst): bkuplst.append(fnm)
        if(bkuplst):
            fn_bkuptar=f'Bkup.{self.fn}.{self.runtype}_{self.step}{self.niter:02d}.tar.bz2'
            with tarfile.open(fn_bkuptar, 'w:bz2') as bkuptar: 
                for fnm in bkuplst:
                    bkuptar.add(fnm);
            self.oldbkup=fn_bkuptar;
        with daofile.DAOPsfFile(self.fn+self.suffD['psf']) as psffile:
            self.psfhwhm = (psffile.xhwhm, psffile.yhwhm);
        self.UpdateStoreFile();

    def EndStep(self):
        self.StoreLog();
        if(not "Ground" in self.step):
            #deleting source-substracted image for psf
            funct.clean_file([ self.fn+self.SkZp_Opt['S']['photo:DAO:psfsubsuff']+self.suffD['img'] ]);
        if(not self.mstep): self.UnlockRun();
        self.DAOoptClean();
      #Total runtime of the closing step
        self.runtimeT.append(sum(self.runtime));
        print(' ',self.runtimeT[-1],":",self.runtime, file=self.stdout);
  

  ##END Special Methods###


    def RunDaoPhot(self, cmd=None, command=None, image=None, mesg=None, addopt=None, logfile=None, logmode='w'):  #Return RunningTime   #RAISE SkZpipeErr
        """Run DAOPhot

Parameters
----------
    cmd : 

    command : 

    image : str, None

    mesg : list

    addopt : list, dict
        Additional options
    logfile : str
        Filename of the logfile
    logmode : str
        Mode for the opening of the logfile

""";
        _name_='RunDaoPhot';
        initime=funct.startime(verb=False);
        if(not os.path.exists('daophot.opt')):   daofunct.DAOoptFileInitialize();
        if(not mesg): mesg=[];
        with open(logfile, logmode) as f_log:
            lim=self.OptionGet('progr:maxlogsize');
            initime0=initime;
            if(self.OptionGet('output:verbose') and self.OptionGet('output:verbosity')>3): print("{n_opt}+{n_mesg}: ".format(n_opt=len(self.daophot_opt), n_mesg=len(mesg)), self.daophot_opt+['']+mesg+["exit"], file=self.stdout);
            daoprogr=funct.fixpathprogram(progr=self.SkZp_Opt['S']['progr:exec:daophot'], pathdir=self.SkZp_Opt['S']['progr:path:DAO']);
            with subprocess.Popen(daoprogr, shell=False, stdin=subprocess.PIPE, stdout=f_log, stderr=subprocess.PIPE, bufsize=0, universal_newlines=True) as proc:
                for imes in self.daophot_opt+['']+mesg+["exit"]:
                    imes=str(imes);
                    f_log.write('=> '+imes+'\n');
                    proc.stdin.write(imes+'\n');
                proc.stdin.flush();

                stder='';
                while(self.OptionGet('progr:runtimecheck') and proc.poll() is None):
                    f_log.flush();
                    fsize=os.stat(logfile).st_size;
                    if(fsize > (lim<<20)):
                        proc.terminate();
                        raise SkZpipeError("Log file {logf} is becoming too much big ({size}>{maxsize} MiB)!".format(logf=logfile, size=fsize, maxsize=lim), exclocus=self.fn);

                    if(0<self.OptionGet('progr:timeout').get('daophot',-1)< (time.time()-initime) ):
                        proc.terminate();
                        raise SkZpipeError("DAOphot is taking too much time ({runtime:.0f}>{timelim}): killing it!".format(runtime=time.time()-initime, timelim=self.OptionGet('progr:timeout')['daophot']), exclocus=self.fn);
                    if(0<bpar.SkZp_Par['runtimewarn']['daophot']< (time.time()-initime0)):
                        print("Warning: DAOPhot exceeded {:}s step".format(bpar.SkZp_Par['runtimewarn']['daophot']), file=self.stderr)
                        initime0=time.time();
                    try:
                        stder=proc.communicate(timeout=bpar.SkZp_Par['checksleepbreak']['daophot'])[1];
                    except subprocess.TimeoutExpired:
                        pass;
                    except:
                        if(self.SkZp_Opt['Flg']['debug']): raise;
                    if(isinstance(stder, str)): self.stderr.write(stder);

        return funct.endtime(initime, verb=False);
    

  #ADDSTAR#####################################
    def Addstar(self, img=None, infile=None, output=None, gain=None, magmax=None, magmin=None, nstar=None, nframe=None, seed=None):   #RAISE SkZpipeErr  #OUTXT
        """

""";
        self.check_psffile();
        if(img is None): img=self.fn;
        daofunct.Dao_check_file([img+self.suffD['img']]);
        if(output is None): output=self.fn+'AS';
        if(seed is None): seed=int(time.time());
        if(nframe is None): nframe=1;
        if(gain is None): gain=self.gain;
        outxt="addstar";
        tag='ADD'
        self.logfile[tag]=self.fn+".Log_add";
        if(infile is None):
            if(magmax is None or magmin is None or nstar is None): raise SkZpipeError("Addstar: wrong values!", exclocus=self.fn);
            self.runtime.append(self.RunDaoPhot(mesg=["at {}".format(img+self.suffD['img']), "addstar", self.fn+self.suffD['psf'], seed, gain, "", "{:.2f},{:.2f}".format(magmin, magmax), nstar, nframe, output], logfile=self.logfile[tag]));
        else:
            daofunct.Dao_check_file([infile]);
            self.runtime.append(self.RunDaoPhot(mesg=["at {}".format(img+self.suffD['img']), "addstar", self.fn+self.suffD['psf'], seed, gain, infile, output, ''], logfile=self.logfile[tag]));
            daofunct.Dao_check_file([output+self.suffD['img'] ]);
        self.outxt.append(outxt);
        return outxt;

        
    def Substar(self, infile=None, output=None, leftstar=None):   #RAISE SkZpipeErr  #OUTXT 
        if(infile is None or output is None): raise SkZpipeError("Substar: wrong values!", exclocus=self.fn);
        daofunct.Dao_check_file([infile]);
        self.check_psffile();
        funct.clean_file([output]);
        outxt="substar";
        tag='SUBS'
        self.logfile[tag]=self.fn+".Log_subs";
        if(leftstar is None):
            self.runtime.append(self.RunDaoPhot(mesg=["at {}.fits".format(self.fn), "substar", self.fn+self.suffD['psf'], infile, "n", output ], logfile=self.logfile[tag]));
        else:
            daofunct.Dao_check_file([leftstar]);
            self.runtime.append(self.RunDaoPhot(mesg=["at {}.fits".format(self.fn), "substar", self.fn+self.suffD['psf'], infile, "y", leftstar, output ], logfile=self.logfile[tag]));
        daofunct.Dao_check_file([output+".fits" ]);

        self.outxt.append(outxt);
        return outxt;



  #FIND#####################################
    def RunDaoPhot_find(self, suff=None, fname=None, findtype='dao'):   #RAISE SkZpipeErr  #OUTXT
        """Run find or use .coooo file to produce 'src' file.

Parameters
----------
    suff : str
        Suffix of the output file.
    fname :  str, None
        Name of the image. Default (None) is the basename of the current image 
    findtype : str
        Type of method to find stars: dao,file""";

        if(not isinstance(findtype,str)): raise TypeError('Find: findtype must be a string.', exclocus=self.fn);
        if(suff is None): suff=self.suffD['src'];
        findtype=findtype.lower();
        if(fname is None): fname=self.fn;
        self.newstar=False;
        if("Ground" in self.step):
            findtype=self.SkZp_Opt['S']['photo:initialsrclist'].lower();
        elif("Refine" in self.step): return '';
##    elif("Intra" in self.step):
        else:
            fname=self.fns;
            if("Add" in self.step):
                suff=".sco";
            else:
                findtype='file';
#    elif("GetFph" in self.step): findtype='file';

        self.newstarfile=fname+suff;
        if(findtype[:3] == 'dao'):
            txt=str(self.SkZp_Opt['F']['photo:thre:'+self.runtype]);
            tag='FIND';
            self.logfile[tag]=self.fn+".Log_find_"+self.step;
            funct.clean_file([self.newstarfile]);
            self.runtime.append(self.RunDaoPhot(mesg=["at {}.fits".format(fname), "find", self.SkZp_Opt['S']['photo:averagedsummed'], self.newstarfile, "y"], logfile=self.logfile[tag]));
            self.newstar=True;
        elif(findtype[:4]=='file' or findtype[0]=='.'):
            txt="from file";
            if(self.step=="Ground"):
                fext= findtype if(findtype[0]=='.') else '.coooo'
                daofunct.Dao_check_file([fname+fext]);
                shutil.copy(fname+".coooo", self.newstarfile);
                self.newstar=True;
            else:
                if(funct.get_num_lines(self.newstarfile)>daopar.DAO_Par['headerlen']+1):
                    self.newstar=True;
        if(self.newstar):
            daofunct.Dao_check_file([self.newstarfile]);
            outxt="find({})[".format(txt);
            self.nstar['tot']=funct.get_num_lines(self.newstarfile)-daopar.DAO_Par['headerlen'];
            outxt+=str(self.nstar['tot'])+"]";
            if(self.SkZp_Opt['Flg']['photo:reg:pos']):
                funct.regfromcat(self.newstarfile, nhdr=3, datpos=2, size1=fwhm, un_flg=1, colf_flg='green', shp_flg='circle', regfile=self.newstarfile+'.reg');
            starden=self.nstar['tot']*self.fwhm**2/(self.nx*self.ny);
            if(starden>self.SkZp_Opt['F']['photo:find:maxdensity']): raise SkZpipeError("\nERROR: Finding too much sources! The field seems to be too crowded ({den:.2f} src/fwhm^2) respect what it should be ({maxden:.2f})".format(den=starden, maxden=self.SkZp_Opt['F'  ]['photo:find:maxdensity']), exclocus=self.fn, outxt=outxt);
        else:
            outxt="No adding stars";

        self.outxt.append(outxt);
        return outxt;

    def RunDaoPhot_find4thre(self, threrange=None):   #RAISE SkZpipeErr  #OUTXT
        """Method to determine the determine the most resonable value for threshold in source-finding produce.

Parameters
----------
    threrange : dict
        Dictionary of float (keys: 'min', 'max', 'step') with the values. Default 'photo:thre:range' option.
""";
        _name_='RunDaoPhot_find4thre';
        if(not threrange): threrange=self.OptionGet('photo:thre:range');
        if(not isinstance(threrange,dict)): raise TypeError(_name_+": `threrange` must be a dictionary (keys:  'min', 'max', 'step') <{val}>".format(val=threrange));
        tmin, tmax, tstp=threrange.get('min'), threrange.get('max'), threrange.get('step');
        if(not tmin or tmin<0): tmin=0.5;
        if(not tmax): tmax=daopar.DAO_Par['permittedoptionvalue']['daophot']['TH'][1];
        if(not tstp or tstp<0): tstp=1;
        niter=int((tmax-tmin)/tstp+0.5);
        outfile=self.fn+'.thco';
        print(f"# {self.fn}", file=self.stdout);
        print(f"# {tmin:3.2f} {tmax:3.2f} {tstp:3.2f}  {niter:3d}", file=self.stdout);
        print(f"# thre #source   abs(der)", file=self.stdout);
        funct.clean_file([self.fn+".Log_find4thre"]);
        thre=tmin;  ii=0; maxflag=True;
        threA=[]; ader=0;
        while(thre<= tmax):
            funct.clean_file([outfile]);
            self.daophot_opt.append("THRE="+str(thre));
            runtime=self.RunDaoPhot(mesg=["at {}.fits".format(self.fn), "find", self.SkZp_Opt['S']['photo:averagedsummed'], outfile, "y"], logfile=self.fn+".Log_find4thre", logmode='a');
            daofunct.Dao_check_file([outfile]);
            nums=funct.get_num_lines(outfile)-daopar.DAO_Par['headerlen'];

            threA.append([thre, nums, -1]);
            ader= 0 if(ii==0) else abs( (threA[-1][1]-threA[-2][1])/tstp );
            threA[-1][2]=ader;
            if(maxflag and ii>1 and ader<threA[-2][2]):
                maxflag=False;
                newmax=3*thre;
                if(newmax>tmax or tmax>100): tmax=newmax;

            print("{thre:6.2f} {nsrc:8d}    {ader:.3f}".format(thre=thre, nsrc=nums, ader=ader), file=self.stdout);
            thre+=tstp; ii+=1;
        if(not self.SkZp_Opt['Flg']['debug']): funct.clean_file([outfile]);
        meanslope=abs( (threA[-1][1]-threA[0][1])/(threA[-1][0]-threA[0][0]) );
        for ii in range(1,len(threA)):
            if(threA[ii][2]<=meanslope<threA[ii-1][2]):
                print("#Probable value\n# {thre:6.2f} {nsrc:8d}    {ader:.3f}".format(thre=threA[ii][0], nsrc=threA[ii][1], ader=threA[ii][2]), file=self.stdout);
                break;
        print("#Warning!\n#If the probable value is really high (greater than 5-7) probably the sky level is too low.", file=self.stdout);
      

  #UPDATE#####################################
    def UpdateCoord(self, suffoldcoo=None, suffnewcoo=None, suffout='.cupd', rejectnonew=False, maxshift=0):  #OUTXT
        """Update Coordinates"""
        if(suffoldcoo is None): suffoldcoo=self.suffD['src']; 
        if(suffnewcoo is None): suffnewcoo=self.suffD['fph']; 
        outxt="";
        daofunct.Dao_check_file([self.fn+suffoldcoo, self.fn+suffnewcoo]);
        if(maxshift<0): maxshift*=-1*self.fwhm;
        tag='UPDATE';
        self.logfile[tag]=self.fn+".Log_updt";
        lstmp=daofunct.coordupdate(fname=self.fn+suffoldcoo, newcoord=self.fn+suffnewcoo, output=self.fn+suffout, rej_nonew=rejectnonew, maxshift=maxshift);
        with open(self.logfile[tag], 'a') as f_log:
            f_log.write(str(lstmp));
        outxt+='{}:{};{}:{}={}:{}'.format(suffoldcoo, lstmp[0], suffnewcoo, lstmp[1], suffout, lstmp[2]);
        return outxt;

  ###
    def UpdateCoordSteps(self, updateonly=False):  #OUTXT
        """Update coordinates of list of sources using psf-fitting photometry"""
        if(self.step=="Ground"): return '';
        
        outxt="update_coord[";
        daofunct.Dao_check_file([self.fn+self.suffD['src'], self.fn+self.suffD['fph'] ]);
    ##COO
        flag_nonew=True if(not updateonly and self.SkZp_Opt['S']['photo:newsrcto'] == 'fph') else False;
        if(self.SkZp_Opt['Flg']['photo:postfitfix']):
            txtmp=self.UpdateCoord(suffoldcoo=self.suffD['src'], suffnewcoo=self.suffD['fph'], suffout='.cupd', rejectnonew=flag_nonew, maxshift=0);
        else:
          #maxshift: reject sources that move more than this (>0 value in pxl, <0 value es multiple of FWHM
            txtmp=self.UpdateCoord(suffoldcoo=self.suffD['src'], suffnewcoo=self.suffD['fph'], suffout='.cupd', rejectnonew=flag_nonew, maxshift=self.SkZp_Opt['F']['photo:rejectmovedby:src'] if(self.SkZp_Opt['Flg']['photo:rejectmoved']) else 0);
        lstmp=re.split('[;=]',txtmp);
        txtmp=lstmp[0]+"="+lstmp[2].split(':')[1];
        outxt+=txtmp;
        shutil.move(self.fn+".cupd", self.fn+self.suffD['src']);

    ##PSF SOURCES
        outxt+="]";
        if(self.runtype=='psfcal'):
            daofunct.Dao_check_file([self.fn+".lst"]);
            outxt+=" & [";
            txtmp=self.UpdateCoord(suffoldcoo=".lst", suffnewcoo=self.suffD['fph'], suffout='.lstmp', rejectnonew=True, maxshift=self.SkZp_Opt['F']['photo:rejectmovedby:psf']);
            lstmp=re.split('[;=]',txtmp);
            txtmp=lstmp[0]+":"+lstmp[2].split(':')[1];
            outxt+=txtmp+']';
            if(os.path.exists(self.fn+".exlst")):
                nrej=daofunct.listselect(fname=self.fn+".lstmp", liststar=self.fn+".exlst", radius=fwhm, remaining=self.fn+".lst", selected=self.fn+".lst_rej", keepid=True);
                if(nrej>0):
                    outxt+="[rej:{:d}]".format(daopar.DAO_Par['headerlen']-nrej);
            else:
                shutil.move(self.fn+".lstmp", self.fn+".lst");
        
    
        self.outxt.append(outxt);
        return outxt;
    

  #PHOTO#####################################
    def RunDaoPhot_photo_gen(self, aperture=[], coofile=None, suffOut=".ap", withpsf=False, fitfile=None, onsubtract=False):    #RAISE SkZpipeErr  #OUTXT
        daofunct.Dao_check_file(coofile);
        if(withpsf):
            self.check_psffile();
            daofunct.Dao_check_file(fitfile);
        tp="Wpsf" if(withpsf) else '-S' if(onsubtract)else ''; 
        outxt="photo{:}{:}({:},{:})".format(tp,str(self.apL).replace(' ',''), str(self.israd), str(self.osrad));
        tag='PHOTO'+tp
        self.logfile[tag]=self.fn+".Log_photo"+tp;
        fn=self.fns if(onsubtract) else self.fn;
        daofunct.Dao_check_file(fn+".fits");

        funct.clean_file([self.fn+suffOut]);
        if(onsubtract or (not withpsf and self.check_psffile(raisexc=False)) ):
            self.runtime.append(self.RunDaoPhot(mesg=["at {}.fits".format(fn), "photo", ""]+self.photo_opt+["ex",      coofile, self.fn+suffOut], logfile=self.logfile[tag]));
        else:
            self.runtime.append(self.RunDaoPhot(mesg=["at {}.fits".format(fn), "photo", ""]+self.photo_opt+["ex", fitfile if(withpsf) else 'e', coofile, self.fn+suffOut], logfile=self.logfile[tag]));
        self.lastoutxt=outxt;
        daofunct.Dao_check_file(self.fn+suffOut);

        nout=funct.get_num_lines(self.fn+suffOut)-daopar.DAO_Par['headerlen'];
        if(nout>1):
            self.maxapmag=daofunct.apmaxmag( self.fn+suffOut, 9);
            outxt+="[{0:.3f}]{{{1:d}:{2:d}}}".format(self.maxapmag, funct.get_num_lines(coofile)-daopar.DAO_Par['headerlen'], nout//3);
        else:
            self.maxapmag=-1;

        self.outxt.append(outxt);
        return outxt;
  ###
    def RunDaoPhot_photo_nopsf(self, aperture=[], suffCoo=None, suffOut=None):    #RAISE SkZpipeErr  #OUTXT
        if(suffCoo is None): suffCoo=self.suffD['src']; 
        if(suffOut is None): suffOut=self.suffD['aph']; 
        return self.RunDaoPhot_photo_gen(coofile=self.fn+suffCoo, suffOut=suffOut, withpsf=False);
  ###
    def RunDaoPhot_photo_psf(self, aperture=[], suffFit=None, suffCoo=None, suffOut=None):   #RAISE SkZpipeErr  #OUTXT
        if(suffFit is None): suffFit=self.suffD['fph']; 
        if(suffCoo is None): suffCoo=self.suffD['src']; 
        if(suffOut is None): suffOut=self.suffD['aph']; 
        return self.RunDaoPhot_photo_gen(coofile=self.fn+suffCoo, suffOut=suffOut, withpsf=True, fitfile=self.fn+suffFit)
  ###
    def RunDaoPhot_photo_s(self, aperture=[], coofile=None, suffOut=".ap_s"):    #RAISE SkZpipeErr  #OUTXT
        if(coofile is None): coofile=self.newstarfile;
        return self.RunDaoPhot_photo_gen(coofile=coofile, suffOut=suffOut, onsubtract=True)
  ###
    def SortAp(self, suffIn=".ap0", suffOut=".ap"):
        """Sort DAOPhot:photo output"""
        daofunct.Dao_check_file([self.fn+suffIn]);
        outxt="&sort";
        tag='SORTAP'
        self.logfile[tag]=self.fn+".Log_sortap";
        funct.clean_file(self.fn+suffOut);
        self.runtime.append(self.RunDaoPhot(mesg=["sort", "4", self.fn+suffIn, self.fn+suffOut, "n"], logfile=self.logfile[tag]));
        daofunct.Dao_check_file([self.fn+suffOut]);

        self.outxt.append(outxt);
        return outxt;

 #PHOTO in STEPS
    def RunDaoPhot_photo_Ground(self, aperture=[], suffCoo=None, suffOut=None):   #RAISE SkZpipeErr  #OUTXT
        if(suffCoo is None): suffCoo=self.suffD['src']; 
        if(suffOut is None): suffOut=self.suffD['aph']; 
        funct.clean_file([self.fn+suffOut, self.fn+".ap0"]);
        outxt=self.RunDaoPhot_photo_nopsf(aperture=aperture, suffCoo=suffCoo, suffOut=suffOut);   # NOpsf because no fitfile!
        if(self.runtype=='psfcal'):
            shutil.move(self.fn+suffOut, self.fn+".ap0");
            if(self.maxapmag<0):
                raise SkZpipeError("\nERROR: problems in the aperture photometry!", exclocus=self.fn, outxt=outxt);
            outxt+=self.SortAp(suffIn=".ap0", suffOut=suffOut);
        return outxt;
      
  ###
    def RunDaoPhot_photo_Steps(self, aperture=[], suffFit=None, suffCoo=None, suffOut=None):   #RAISE SkZpipeErr  #OUTXT
        if(suffFit is None): suffFit=self.suffD['fph']; 
        if(suffCoo is None): suffCoo=self.suffD['src']; 
        if(suffOut is None): suffOut=self.suffD['aph']; 
        if(self.step=="Ground"): return RunDaoPhot_photo_Ground(suffCoo=suffCoo, suffOut=suffOut);

        funct.clean_file([self.fn+suffOut, self.fn+".apsf", self.fn+".ap_s", self.fn+".ap0", self.fn+".apm",  self.fn+".noap"]);

        try:
            outxt=self.RunDaoPhot_photo_psf(aperture=aperture, suffFit=suffFit, suffCoo=suffCoo, suffOut=".apsf");
        except OSError:
            outxt=self.lastoutxt+"[99.999]{{{:d}:0}}".format(funct.get_num_lines(self.fn+suffCoo)-daopar.DAO_Par['headerlen']);
            print('> >',outxt, end='< < ', file=self.stdout);
        except:
            if(self.SkZp_Opt['Flg']['debug']): raise;

        if(self.newstar):
            self.lastoutxt=self.RunDaoPhot_photo_s(aperture=aperture, coofile=self.newstarfile, suffOut=".ap_s");
            outxt+=self.lastoutxt;
          ## ADD NEW STARS to COO
            idx=daofunct.appendfiles(self.fn+suffCoo, self.newstarfile, self.fn+".coo_updt");
            daofunct.appendfiles(self.fn+".apsf", self.fn+".ap_s", self.fn+".ap0", idx[1], nl=2);
            shutil.move(self.fn+".coo_updt", self.fn+suffCoo);
        else:
            shutil.copy(self.fn+".apsf", self.fn+".ap0");

      #Some star have no photometry?
        missingstar=daofunct.compareCooAp(self.fn+suffCoo, self.fn+".ap0", self.fn+".noap"); 

        if(missingstar>0):
            outxt+=self.RunDaoPhot_photo_nopsf(aperture=aperture, suffCoo=".noap", suffOut=".apm");
            daofunct.fileupdate(self.fn+".ap0", self.fn+".apm", self.fn+suffOut);
        else:
            shutil.copy(self.fn+".ap0", self.fn+suffOut);

        daofunct.Dao_check_file([self.fn+suffOut]);
        self.maxapmag=round(daofunct.apmaxmag( self.fn+suffOut, 9),2);
        if(self.maxapmag<0):
            #self.outxt.append(outxt);
            raise SkZpipeError("problems in the aperture photometry!", exclocus=self.fn, outxt=outxt);
        #Deleteing not more useful files, if not debugging
        if(not self.SkZp_Opt['Flg']['debug']):
            funct.clean_file([self.fn+suf for suf in (".apsf", ".ap_s", ".ap0", ".apm",  ".noap", '.a4p')]);

        #self.outxt.append(outxt);
        return outxt;

  ###
    def RunDaoPhot_photo(self, aperture=[], suffCoo=None, suffFit=None, suffOut=None):
        """Procedure to run DAOPhot:photometry
""";
        if(suffFit is None): suffFit=self.suffD['fph']; 
        if(suffCoo is None): suffCoo=self.suffD['src']; 
        if(suffOut is None): suffOut=self.suffD['aph']; 
        if("Ground" in self.step or self.check_psffile(raisexc=False)):
            return self.RunDaoPhot_photo_Ground(aperture=aperture, suffCoo=suffCoo, suffOut=suffOut);
        else:
            return self.RunDaoPhot_photo_Steps(aperture=aperture, suffCoo=suffCoo, suffFit=suffFit, suffOut=suffOut);

  #PICK###############################
    def GetNumPsfStar(self):
        if(self.runtype=='psfcal'):
            self.nstar['psf']=funct.get_num_lines(self.fn+".lst")-daopar.DAO_Par['headerlen'];
        else:
            self.nstar['psf']=0;
 
    def RunDaoPhot_pick(self):   #RAISE SkZpipeErr  #OUTXT
        """Run pick from DAOPhot

""";
        if(self.runtype!='psfcal'): raise SkZpipeError(" Trying to run pick for a no 'psfcal' runtype", exclocus=self.fn, outxt=outxt);
        daofunct.Dao_check_file([self.fn+".ap"]);
        funct.clean_file([self.fn+".lst"]);

        self.PickCounter['pickmag']=self.maxapmag-self.SkZp_Opt['F']['photo:DAO:pickdeltamag'] if(self.maxapmag) else 20;
        outxt="pick";
        tag='PICK';
        self.logfile[tag]=self.fn+".Log_pick";

        if(not os.path.exists(self.fn+'.a4p') or self.PickCounter['iter']==0):
            funct.clean_file([self.fn+'.a4p']);
            shutil.copy(self.fn+".ap", self.fn+".a4p");
            for suff in (".bpm",".npz"):
                if(os.path.exists(self.fn+suff)):              #If there is $fn.npz with the list of badpixels (same format for Iraf/badpiximage) psf stars too close to these will be removed
                    outxt+="[clean-{}]".format(suff);
                    shutil.copy(self.fn+".a4p", self.fn+".a4p0");
                    daofunct.areaclean(fname=self.fn+".a4p0", areas=self.fn+suff, mindist=self.SkZp_Opt['F']['photo:psf:psfradius'], output=self.fn+".a4p");
                    funct.clean_file(self.fn+".a4p0");

        self.runtime.append(self.RunDaoPhot(mesg=["at {}.fits".format(self.fn), "pick", self.fn+".a4p", str(self.PickCounter['pps'])+','+str(self.PickCounter['pickmag']), self.fn+".lst"], logfile=self.logfile[tag]));
        daofunct.Dao_check_file([self.fn+".lst"]);
        self.nstar['psf0']=funct.get_num_lines(self.fn+".lst")-daopar.DAO_Par['headerlen'];
        if(self.nstar['psf0']==self.PickCounter['pps']):
            self.PickCounter['flag']=True;
            lst0='';
        else:
            self.PickCounter['flag']=False;
            lst0="!{:d}!".format(self.nstar['psf0']);
        self.PickCounter['iter']+=1;
        self.PsfCounter['flag']=1;

        self.GetNumPsfStar();
        outxt+="({0:d}/{1}{2:};{3:.3f})".format(self.nstar['psf'], self.PickCounter['pps'], lst0, self.PickCounter['pickmag']);

        self.outxt.append(outxt);
        return outxt;

    def ReducePsfStar(self, num=0):   #RAISE SkZpipeErr  #OUTXT
        if(num<=0): num=self.PickCounter['mxps'];
        daofunct.Dao_check_file([self.fn+".lst"]);
        if(num<funct.get_num_lines(self.fn+".lst")-daopar.DAO_Par['headerlen']):       #if you want only $mxps of the $nlst stars used to calculate PSF
            shutil.move(self.fn+".lst", self.fn+".lst.tmp");
            with open(self.fn+".lst.tmp") as f_tmp:
                with open(self.fn+".lst", 'w') as f_lst:
                    f_lst.write(f_tmp.readline());
                    f_lst.write(f_tmp.readline());
                    f_lst.write(f_tmp.readline());
                    for nlst in range(num):
                        f_lst.write(f_tmp.readline());
                    nlst+=1;
            funct.clean_file(self.fn+".lst.tmp");
            self.nstar['psf']=nlst;
            return " [PSF stars are now {:d}] ".format(nlst);
        else:
            return '';

    def RunDaoPhot_pickmore(self):   #RAISE SkZpipeErr
        if(self.PickCounter['iter']>self.SkZp_Opt['I']['photo:psf:starsel_itermax']): raise SkZpipeError("Too many iteration of pick! There is a problem!", exclocus=self.fn);
        self.PickCounter['pps']+=self.SkZp_Opt['I']['photo:psf:starinit'];
        self.PickCounter['mxps']+=self.SkZp_Opt['I']['photo:psf:starinit']>>1;
        return self.RunDaoPhot_pick();
    


  ##SUBSTAR FOR PSF################
    def SubstarPsf(self):   #RAISE SkZpipeErr  #OUTXT 
        if(self.runtype!='psfcal' or self.step=="Ground"): raise SkZpipeError("Wrong function/step!", exclocus=self.fn);
        return self.Substar(infile=self.fn+".als", output=self.fn+self.SkZp_Opt['S']['photo:DAO:psfsubsuff'] , leftstar=self.fn+".lst");


  ##PSF############################
  #PRE#
    def PreRunPsf(self):   #RAISE SkZpipeErr  #OUTXT 
        if(self.runtype!='psfcal'): raise SkZpipeError("Wrong function/step!", exclocus=self.fn);
        tag='PSF';
        outxt='';
        if(tag in self.logfile and os.path.exists(self.logfile[tag])):
            cntr=".{:d}".format(self.PsfCounter['countpsf']-1);
            shutil.move(self.logfile[tag], self.logfile[tag]+cntr);
            self.logfile[tag+cntr]=self.logfile[tag]+cntr;
        self.GetNumPsfStar();
        self.PsfCounter['countpsf']+=1;
        if(self.PsfCounter['countpsf']>self.SkZp_Opt['I']['photo:psf:itermax']):
            raise SkZpipeError("Too much iteration ({:d}/{:d}) to calculate PSF! There is some problem.".format(self.PsfCounter['countpsf'], self.SkZp_Opt['I']['photo:psf:itermax']), exclocus=self.fn);

        if(self.nstar['psf']<self.SkZp_Opt['I']['photo:psf:starmin']):  ## or (self.PsfCounter['flag']<0 and self.PsfCounter['nes'])):
            outxt="Too few stars left ({:d}/{:d}) for psf calculation".format(self.nstar['psf'], self.SkZp_Opt['I']['photo:psf:starmin']);
            raise  SkZpipePsfErr(outxt);
        
        self.outxt.append(outxt);
        return outxt;

    def RunDaoPhot_psf(self):    #RAISE SkZpipeErr  #OUTXT
        if('psfcal' != self.runtype): raise SkZpipeError("You are trying to modify the PSF file during a run not to calculate the PSF!", exclocus=self.fn);

        tag='PSF';
        self.logfile[tag]=self.fn+".Log_psf";
        outxt="psf{:d}".format(self.PsfCounter['countpsf']);
        fnimg=self.fn+".fits" if(self.step=="Ground") else self.fn+self.SkZp_Opt['S']['photo:DAO:psfsubsuff']+".fits";
        daofunct.Dao_check_file([self.fn+".ap", self.fn+".lst", fnimg]);
        funct.clean_file([self.fn+self.suffD['psf'], self.fn+".nei"]);

        self.runtime.append(self.RunDaoPhot(mesg=["at "+fnimg, "psf", self.fn+self.suffD['aph'], self.fn+self.suffD['psfsrc'], self.fn+self.suffD['psf']], logfile=self.logfile[tag]));
        
        outxt+="({:d};{:d};{:.2f})[{}".format(self.nstar['psf'], self.var, self.SkZp_Opt['F']['photo:psf:psfradius'], self.psfopt);

        self.outxt.append(outxt);
        return outxt;

  #CHECK#
    def CheckPsf(self):   #RAISE SkZpipePsfErr  #OUTXT
        """Check the results of the PSF procedure"""
    #flag exit values:
    #  -1 => Failed,NES for all: redo pick
    #   2 => Failed,NES for some: try another (or die)
    #   4 => Failed,no psf: try another (or die)
    #   0 => Chi2 enough: terminate
    #   8 => Bad stars: redo with defaulf
    #  16 => No bad stars,default failed,no other: redo the first good (or die)
    #  32 => No bad stars,default failed: try another
    #   0 => All Good! Stop
    #
    #Commented
    #  32 => All good,reducing stars: redo
    #
        tag='PSF';
        (psfused, bestpsf)=('', 0);
        (outxt, chi2, psfallchiL, psfallchiM, badlst, foundbad)=("", 0, [], {}, [], False);

    #Not Enough Stars Err
        with open(self.logfile[tag]) as f_log:
            for line in f_log:
                if("Not enough PSF stars" in line):
                    outxt+=":FAILED for Not Enough Stars!]";
                    self.PsfCounter['failedpsf']+=1;
                    if(self.PsfCounter['failedpsf']==len(self.PsfLst)):
                        self.PsfCounter['nes']=True;
                        self.outxt.append(outxt);
                        self.PsfCounter['flag']=-1;
                        return outxt;            ###RETURN  NES for all. Need more
                    self.psfopt=self.PsfLst[self.PsfCounter['failedpsf']];
                    self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));
    
                    self.outxt.append(outxt);
                    self.PsfCounter['flag']=+1<<1;
                    return outxt;            ###RETURN  NES but trying with other

    ####################
        def _failingmanager():
            self.PsfCounter['failedpsf']+=1;
            if(self.PsfCounter['failedpsf']==len(self.PsfLst)):
                if(self.PsfCounter['firstgoodpsf']<=self.SkZp_Opt['I']['photo:DAO:psfothergood']):
                    self.PsfCounter['failedpsf']=-1;
                    self.psfopt=self.PsfLst[self.PsfCounter['firstgoodpsf']];
                    self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));
    
                    self.outxt.append(outxt);
                    self.PsfCounter['flag']= 1<<4;
                    return outxt;            ###RETURN  Default failed, but another usable funct was good. redo with it
                else:
                    self.outxt.append(outxt);
                    raise SkZpipePsfErr(outxt+" :: PSF calculation failed! There is some problem.");
            self.psfopt=self.PsfLst[self.PsfCounter['failedpsf']];
            self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));

            self.outxt.append(outxt);
            self.PsfCounter['flag']=1<<2;
    ####################

    #CHECKING PSF FILE
        if(self.check_psffile(raisexc=False)):
            outxt+=":FAILED]";
            _failingmanager();
            return outxt;            ###RETURN  FAILED
        else:
        #CHECKING on calculated HWHM
            with daofile.DAOPsfFile(fname=self.fn+self.suffD['psf']) as psffile:
        #Check if parameters do not make sense: (PSF:XHWHM+PSF:YHWHM)/FWHM > psffwhmratio
                if(psffile.xhwhm<=0 or psffile.yhwhm<=0):
                    outxt+=f":WrongHWHM({psffile.xhwhm};{psffile.yhwhm})]"
                    _failingmanager();
                    return outxt;            ###RETURN  FAILED
                rfwhm=(psffile.xhwhm+psffile.yhwhm)/self.fwhm;
                ellip=1-min(psffile.xhwhm,psffile.yhwhm)/max(psffile.xhwhm,psffile.yhwhm);
                if(rfwhm>self.SkZp_Opt['F']['photo:psf:fwhmratio']):
                    outxt+=f":AnomalousHWHM({psffile.xhwhm};{psffile.yhwhm})]".format(xhwhm=psffile.xhwhm, yhwhm=psffile.yhwhm);
                    _failingmanager();
                    return outxt;            ###RETURN  FAILED
                elif(ellip>self.SkZp_Opt['F']['photo:psf:maxellipticity']):
                    outxt+=":AnomalousEllipticity({psffile.xhwhm};{psffile.yhwhm})]".format(xhwhm=psffile.xhwhm, yhwhm=psffile.yhwhm);
                    _failingmanager();
                    return outxt;            ###RETURN  FAILED
                else:
                    self.psfhwhm = (psffile.xhwhm, psffile.yhwhm);

      

        if(daopar.DAO_Par['psfanaltype'][self.psfopt]<0): #If to try several psf up to given one
            bestpsf=daopar.DAO_Par['psfanaltype'][psfused];
            outxt+=","+psfused;
        else:
            bestpsf=1;

        with open(self.logfile[tag]) as f_log:
            line=funct.read_until(f_log, "Chi");
            if(daopar.DAO_Par['psfanaltype'][self.psfopt]>0): 
                line=funct.read_until(f_log, ">>");
            else:
                line=funct.read_until(f_log, ["{:.5f}".format(self.psfhwhm[0]), "{:.5f}".format(self.psfhwhm[1])]);
#      for ii in range(bestpsf):
#        line=funct.read_until(f_log, ">>");

            chi2, xhwhm, yhwhm=(float(x) for x in line.split()[1:4]);
            outxt+=":{chi2:}]".format(chi2=chi2);
            self.PsfCounter['chi2']=chi2;
    #Chi2 enough small?    
            if(self.PsfCounter['failedpsf']==0 and self.PsfCounter['chi2']<=self.SkZp_Opt['F']['photo:psf:chi2lim']):
                outxt+=" Chi2 enough good! Terminating...";

                self.outxt.append(outxt);
                self.PsfCounter['flag']= 0;
                return outxt;            ###RETURN  CHI2 enough good, Finish!

        #Looking for bad stars
            line=funct.read_until(f_log, "Profile errors");
            f_log.readline();
            psfallpattWi="["+"".join(daopar.DAO_Par['psfpattWi'])+"]";
            psfallpattWo="|".join(daopar.DAO_Par['psfpattWo']);

            for line in f_log:
                if(not line.strip()): break;
                line=re.sub('(.{7})(.{10})',r'\1 \2', line);

                if(re.search(psfallpattWi+"|"+psfallpattWo,line)):
                    badlst.extend(re.findall(r'\s+(\d+)\s+\d+\.\d+\s+'+psfallpattWi, line));
                    psfallchiL.extend(re.findall(r'\s+(\d+\s+\d+\.\d+\s+'+psfallpattWi+')', line));
                    line=re.sub(r'\s+(\d+\s+\d+\.\d+\s+'+psfallpattWi+')', '', line)

                    badlst.extend(    re.findall(r'\s+(\d+)\s+(?:'+psfallpattWo+')', line));
                    psfallchiL.extend(re.findall(r'\s+(\d+\s+(?:'+psfallpattWo+'))', line));
                    line=re.sub(r'\s+(\d+\s+('+psfallpattWo+'))', '', line);
                psfallchiL.extend(re.findall(r'\s+(\d+\s+\d+\.\d+)\s', line));

            for line in psfallchiL:
                tmpl=line.split();
                psfallchiM[tmpl[0]]="\t".join(tmpl[1:]);
            with open(self.fn+".psfchi2", 'w') as f_chi2:
                tmpl=list(psfallchiM.keys())
                tmpl.sort(key=int)
                for line in tmpl:
                    f_chi2.write("{}\t{}\n".format(line, psfallchiM[line]));

        if(self.PsfCounter['failedpsf']>0 and daopar.DAO_Par['psfanaltype'][self.psfopt]>0 and self.PsfCounter['firstgoodpsf']>self.PsfCounter['failedpsf']): #based on the used psf type, i.e. the default one
            self.PsfCounter['firstgoodpsf']=self.PsfCounter['failedpsf'];

        if(badlst):
            foundbad=True;
            badlst.sort(key=int);
            outxt+="{"+str(len(badlst))+": "+";".join(badlst)+"}";
            self.flush_out();

            self.nstar['psf']-=len(badlst);
            if(self.nstar['psf']<self.SkZp_Opt['I']['photo:psf:starmin']):
                self.outxt.append(outxt);
                raise SkZpipePsfErr(outxt+" :: Number of PSF stars will be less than the minimum ({:d})".format(self.SkZp_Opt['I']['photo:psf:starmin']));
            shutil.move(self.fn+".lst", self.fn+".lst.tmp");
            with open(self.fn+".lst.tmp" ) as f_tmp:
                with open(self.fn+".lst", 'w') as f_lst:
                    f_lst.write(f_tmp.readline());
                    f_lst.write(f_tmp.readline());
                    f_lst.write(f_tmp.readline());
                    for line in f_tmp:
                        idx=line.split()[0];
                        if(badlst):
                            ii=0;
                            for iidx in badlst:
                                if(idx==iidx): break
                                ii+=1;
                            if(idx==iidx):
                                badlst.pop(ii)
                            else:
                                f_lst.write(line);
                        else:
                            f_lst.write(line);
            funct.clean_file(self.fn+".lst.tmp");

            if(self.PsfCounter['failedpsf']):
                self.PsfCounter['failedpsf']=0;
                self.PsfCounter['firstgoodpsf']=99;
        #self.PsfCounter['redowithdef']+=1;
                self.psfopt=self.PsfLst[0];
                self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));

            self.outxt.append(outxt);
            self.PsfCounter['flag']= 1<<3;
            return outxt;            ###RETURN  BAD STAR CLEAN
      #end badlst#
        else:
            foundbad=False;
    #End bad stars

    #After a failed default psf and no found bad stars
        if(self.PsfCounter['failedpsf']>0):
            self.PsfCounter['failedpsf']+=1;
            if(self.PsfCounter['failedpsf']==len(self.PsfLst) or ( self.PsfCounter['failedpsf']>2 and self.PsfCounter['failedpsf']>self.SkZp_Opt['I']['photo:DAO:psfothergood'] )):
                if(self.PsfCounter['firstgoodpsf']<=self.SkZp_Opt['I']['photo:DAO:psfothergood']):
                    self.PsfCounter['failedpsf']=-1;
                    self.psfopt=self.PsfLst[self.PsfCounter['firstgoodpsf']];
                    self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));
    
                    self.outxt.append(outxt);
                    self.PsfCounter['flag']= 1<<4;
                    return outxt;            ###RETURN  Default failed, but another usable funct was good. redo with it
                else:
                    self.outxt.append(outxt);
                    raise SkZpipePsfErr(outxt+"::PSF calculation failed and alternative psfs don't find problematic stars! There is some problem.\nIt could be fixed with options 'photo:DAO:psfother' and 'photo:DAO:psfothergood', permitting other PSF to be used for the final PSF.");
            self.psfopt=self.PsfLst[self.PsfCounter['failedpsf']];
            self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));

            self.outxt.append(outxt);
            self.PsfCounter['flag']= 1<<5;
            return outxt;            ###RETURN Default failed and following found no bad stars. Trying with next

    #All good, reducing stars
        if(self.SkZp_Opt['Flg']['photo:psf:starprereduce']):
            if(self.PsfCounter['nes']):
                outxt+=" [skipping reducing psf stars since daophot had problems] ";
            else:
                otxt=self.ReducePsfStar(self.PickCounter['mxps']+5);
                if(otxt):
                    outxt+=otxt;
                    self.outxt.append(outxt);
                    self.PsfCounter['flag']= 1<<6;
                    return outxt;            ###RETURN last run, hopefully

        self.outxt.append(outxt);
        self.PsfCounter['flag']= 0;
        return outxt;            ###RETURN  Finished!

  #POST#
    def PostPsf(self):  #OUTXT
        """Procedure after the cycle for PSF"""
        outxt=''
        if(self.PsfCounter['nes']):
            outxt+=" [skipping reducing psf stars since daophot had problems] ";
        else:
            outxt=self.ReducePsfStar();
        if(self.niter>0):
            if(self.mstep):
                outxt+="Delta Chi2={:.5f}".format(self.PsfCounter['chi2']-self.PsfCounter['chi0'])
            else:
                if(os.path.exists(self.fn+self.SkZp_Opt['S']['SkZp_log'])):
                    with open(self.fn+self.SkZp_Opt['S']['SkZp_log']) as f_tmp:    #SkZpLOG 
                        for line in f_tmp:
                            pass;
                        outxt+="Delta Chi2={:.5f}".format(self.PsfCounter['chi2']-float(line.split()[2]))
                elif(os.path.exists(self.fn+".chi2")):
                    with open(self.fn+".chi2") as f_tmp:
                        outxt+="Delta Chi2={:.5f}".format(self.PsfCounter['chi2']-float(f_tmp.readline()))
                    with open(self.fn+".chi2", 'w') as f_tmp:
                        f_tmp.write(str(self.PsfCounter['chi2']));
  
        if(self.runtype=='psfcal'):
            if(self.SkZp_Opt['Flg']['photo:reg:psf']):
                funct.regfromcat(self.fn+'.lst', nhdr=3, datpos=2, size1=fwhm, un_flg=1, colf_flg='red', shp_flg='circle', regfile=self.fn+'.lst.reg');
  
            if(daofunct.Dao_check_file([self.fn+".nei"], minline=self.nstar['psf']+3)):
                daofunct.makenei(self.fn+".lst", self.fn+".ap", self.fn+".nei", round(1.5*self.psfrad+2*self.fitt+1, 3), round(2*self.fitt+1,3));
                outxt+="+nei";
  
        self.outxt.append(outxt);
        return outxt;
  
  #Run a PSF Cycle
    def Cycle4Psf(self):
        print(self.PreRunPsf(),      end='',    file=self.stdout, flush=True);
        print(self.RunDaoPhot_psf(), end='',    file=self.stdout, flush=True);
        print(self.CheckPsf(),       end=' - ', file=self.stdout, flush=True);
        self.flush_out();
        
  
    def Cycling4Psf(self):   #RAISE SkZpipeWarn 
        self.PsfCounter['flag']=1;
        self.PsfCounter['failedpsf']=0;
        while(self.PsfCounter['flag']):
            prewait=funct.WaitStop([self.fn], suff="PSF");
            if(os.path.exists(self.fn+".SKIP")):
                raise SkZWarn("Order to skip.");
    #      startime+=prewait;   ??KEEP?
    #      midtime+=prewait;   ??KEEP?

            try:
                self.Cycle4Psf();
            except SkZpipePsfErr as err:
                errtxt=str(err); oldtxt='';
                if('::' in errtxt): (oldtxt,errtxt)=tuple(x.strip() for x in errtxt.split('::',1))
                if("Ground" in self.step and self.PickCounter['flag']):
                    if(self.auto):
                        outxt=str(err)+" Trying again with more stars.";
                        print(outxt, file=self.stdout);
                        print(self.RunDaoPhot_pickmore(),end=' - ', file=self.stdout, flush=True);
              
                        self.PsfCounter['failedpsf']=0;
                        self.psfopt=self.PsfLst[0];
                        self.daophot_opt.append("ANAL="+str(daopar.DAO_Par['psfanaltype'][self.psfopt]));
                    else:
            ##for no automatic retry! So raise Exception to quit
                        raise SkZpipeError(errtxt+" Try and rerun pick with greater number or use a lower minimum number of stars for PSF!", exclocus=self.fn, outxt=oldtxt);
                else:
                ##for no more star available! So raise Exception to quit
                    raise SkZpipeError(errtxt, exclocus=self.fn, outxt=oldtxt);
            except SkZpipeError as err:
                    raise err;
            except:
      #  if(self.SkZp_Opt['Flg']['debug']):
                    raise;
            self.flush_out()


  ##ALLSTAR############################
    def AllstarFixId(self, alsfile=None, apfile=None, fwhm=None):
        if(alsfile is None): alsfile=self.fn+".als";
        if(apfile is None): apfile=self.fn+".ap";
        if(fwhm is None): fwhm=self.fwhm;
        dbg=1 if(self.SkZp_Opt['Flg']['debug']) else 0;

          #fixidals(alsfile, apfile, fwhm, outfile,    fwhmfrac, debugflag)
        outl=daofunct.fixidals(alsfile, apfile, fwhm, self.fn+".alsF", 0, dbg)  #=> C program 

        if(not daofunct.Dao_check_file([self.fn+".als_R"], raisexc=False)):
            self.Addstar(img=self.fns, infile=self.fn+".als_R", output=self.fns+'2', gain=1e9) #readd sources throw away by the fix
            shutil.move(self.fns+"2.fits", self.fns+".fits") #replace the old source-substracted fits with the new one
        outxt="-FixID[{fixed},{magsh:.3f}]".format(fixed=outl[2], magsh=outl[-1])
        if(dbg): shutil.move(self.fn+".als", self.fn+f".als_{self.niter}")
        shutil.move(self.fn+".alsF", self.fn+".als");
        return outxt;
   
    def RunAllstar(self, photoinput=None, output=None, suff=None):   #RAISE SkZpipeErr  #OUTXT
        """Run Allstar.

Parameters
----------
    photoinput : str
        the filename of the input file or the suffix starting with a '.'. 
    output : str
        the filename of the output file or the suffix starting with a '.'. 
    suff : str
        A suffix for additional run of Allstar
"""
        if(output is None): output=self.SetOutput(output, default='.als');
        if(photoinput is None):
            if(self.runtype=='srclst' or not "Add" in self.step):
                photoinput=self.fn+'.ap';
            else:
                photoinput=self.fn+'.'+self.SkZp_Opt['S']['photo:DAO:allstarinput'];
        suff='' if(suff is None) else '0';
        tag='ALS'+suff;
        self.logfile[tag]=self.fn+".Log_als"+suff;
        outxt="Allstar{}[".format(suff);
  
    
        daofunct.Dao_check_file([photoinput]);
        self.check_psffile();
        funct.clean_file([output]);
        self.newstar=False;
      
        initime=time.time();
        with open(self.logfile[tag], 'w') as f_log:
            lim=self.OptionGet('progr:maxlogsize');
            initime0=initime;
            alsprogr=funct.fixpathprogram(progr=self.SkZp_Opt['S']['progr:exec:allstar'], pathdir=self.SkZp_Opt['S']['progr:path:DAO']);
            with subprocess.Popen(alsprogr, shell=False, stdin=subprocess.PIPE, stdout=f_log, stderr=subprocess.PIPE, bufsize=0, universal_newlines=True) as proc:
                for imes in self.allstar_opt+['ex']+[self.fn+".fits", self.fn+self.suffD['psf'], photoinput, output, self.fns]+["exit"]:
                    imes=str(imes);
                    f_log.write('=> '+imes+'\n');
                    proc.stdin.write(imes+'\n');
                proc.stdin.flush();

                stder='';
                while(self.OptionGet('progr:runtimecheck') and proc.poll() is None):
                    f_log.flush();
                    fsize=os.stat(self.logfile[tag]).st_size;
                    if(fsize > (lim<<20)):
                        proc.terminate();
                        raise SkZpipeError("Log file {logf} is becoming too much big ({size}>{maxsize} MiB)!".format(logf=self.logfile[tag], size=fsize, maxsize=lim), exclocus=self.fn, outxt=outxt);

                    if(0<self.OptionGet('progr:timeout').get('allstar',-1)<time.time()-initime):
                        proc.terminate();
                        raise SkZpipeError("Allstar is taking too much time ({runtime:.0f}>{timelim}): killing it!".format(runtime=time.time()-initime, timelim=self.OptionGet('progr:timeout')['allstar']), exclocus=self.fn, outxt=outxt);
                    if(0<bpar.SkZp_Par['runtimewarn']['allstar']<time.time()-initime0):
                        print("Warning: Allstar exceeded {:}s step".format(bpar.SkZp_Par['runtimewarn']['allstar']), file=self.stderr)
                        initime0=time.time();
                    try:
                        stder=proc.communicate(timeout=bpar.SkZp_Par['checksleepbreak']['allstar'])[1];
                    except subprocess.TimeoutExpired:
                        pass;
                    except:
                        if(self.SkZp_Opt['Flg']['debug']): raise;
                    if(isinstance(stder, str)): self.stderr.write(stder);

        self.runtime.append(funct.endtime(initime, verb=False));
    
        daofunct.Dao_check_file([self.fns+".fits", self.fn+".als"]);
    
        with open(self.logfile[tag]) as f_log:
            old=["", ""];
            for line in f_log:
                if("Finished" in line): break;
                old.append(line.strip())
                old.pop(0)
        leg=["I", "R", "D", "C"];
        outals=old[0].split();
        outxt+="{}:{};{}:{};{}:{};{}:{}]".format(leg[0], outals[0], leg[1], outals[1], leg[2], outals[2], leg[3], outals[3]);

        if(self.SkZp_Opt['Flg']['photo:postfitfix']):  outxt+=self.AllstarFixId();
      
        if(self.SkZp_Opt['Flg']['photo:reg:fph']):   funct.regfromcat(self.fn+'.als', nhdr=3, datpos=2, size1=(0,1,20), un_flg=1, colf_flg='blue', shp_flg='circle', regfile=self.fn+'.als.reg');
    
        self.outxt.append(outxt);
        return outxt;

  ###################################

    
  ##RUN STEP ########################
##
    def RunStepGround(self):   #RAISE SkZpipeErr   
        """Run the intitial step for the calculation of the PSF (Grounz 0).

  """;
        self.step="Ground";
        if(self.runtype=='psfcal'):   funct.clean_file([self.fn+self.SkZp_Opt['S']['photo:psf:done']]);
        elif(self.runtype=='srclst'): funct.clean_file([self.fn+self.SkZp_Opt['S']['photo:srclst:done']]);
        print(self.StartStep(), file=self.stdout);
        try:
            print(self.RunDaoPhot_find(),  end=' - ', file=self.stdout, flush=True);
            print(self.RunDaoPhot_photo(), end=' - ', file=self.stdout, flush=True);
            if(self.runtype=='psfcal'):
                print(self.RunDaoPhot_pick(), end=' - ', file=self.stdout);
                self.Cycling4Psf();
                print(self.PostPsf(), end="\n\t", file=self.stdout, flush=True);
            self.flush_out();
            print(self.RunAllstar(), file=self.stdout, flush=True);
            self.GoodEndStep();
        except (SkZpipeException,OSError) as Exp:
            if(self.runtype=='psfcal'):
                funct.clean_file([self.fn+self.suffD['psf']]);
            print(Exp, file=self.stderr);
            self.error="Step"+self.step;
        except:
            if(self.SkZp_Opt['Flg']['debug']): raise;
        self.EndStep();
        self.flush_out();

##
    def RunStepRefinePSF(self):
        """Run the psf refining step

"""
        print(self.StartStep(), file=self.stdout);
        try:
            if('Add' in self.step):
                print(self.RunDaoPhot_find(),end=' - ', file=self.stdout);
                self.flush_out();
                print(self.UpdateCoordSteps(),end=' - ', file=self.stdout);
                self.flush_out();
                print(self.RunDaoPhot_photo(),end=' - ', file=self.stdout);
                self.flush_out();
                print(self.RunAllstar(suff='0'), file=self.stdout);
                self.flush_out();
            print(self.UpdateCoordSteps(updateonly=True),end=' - ', file=self.stdout);
            self.flush_out();
            print(self.RunDaoPhot_photo(),end=' - ', file=self.stdout);
            self.flush_out();
            if(self.runtype=='psfcal'):
                print(self.SubstarPsf(),end=' - ', file=self.stdout);
                self.flush_out();
                self.Cycling4Psf();
                print(self.PostPsf(),end="\n\t", file=self.stdout);
            self.flush_out();
            print(self.RunAllstar(), file=self.stdout);
            self.flush_out();
            self.GoodEndStep();
        except (SkZpipeException,OSError) as Exp:
            if(self.runtype=='psfcal'):
                funct.clean_file([self.fn+self.suffD['psf']])
            print(Exp, file=self.stderr);
            self.error="StepRefine";
        except:
            if(self.SkZp_Opt['Flg']['debug']): raise;
        self.EndStep();
        self.flush_out();


##
    def RunStepGetAph(self, aperture=[], suffCoo=None, suffFit=None, suffOut=None, suffLst='.lsrc', ap1line=None):
        """Run the step to obtain aperture photometry. 

Parameters
----------
    aperture : float, list of float
        Aperture radius to use
    suffCoo : str, None
        Suffix of the source list. Default value: option 'photo:ext:coord' .
    suffFit : str, None
        Suffix of an existing psf-fitting photometry. Optional, used to remove nearby stars. Default value: option 'photo:ext:fitting' ('.fph').
    suffOut : str, None
        Suffix of the output file. Default value: option 'photo:ext:aperture' ('.aph').
    suffLst : str, None
        Suffix of an additional source list to be appended to the main one. Optional, it can be used if source list and psf-fitting photometry are the same file. Default value: '.lsrc'.
"""
        self.step="GetAph";
        if(not isinstance(aperture, (float,list))): raise TypeError(_name_+": `aperture` must be a float or a list of floats. <{}>".format(aperture))
        if(aperture and not isinstance(aperture, list)): aperture=[aperture];
        else: aperture=[];
        if(aperture):
            self.OptionSet('photo:aperture',aperture);
        else:
            if(self.OptionGet('photo:apcorr:ap0')):
                self.OptionSet('photo:aperture',[self.OptionGet('photo:std:aperture')]);
    
        if(not suffCoo): suffCoo=self.OptionGet('photo:ext:coord');
        if(not suffFit): suffFit=self.OptionGet('photo:ext:fitting');
        if(not suffOut): suffOut=self.OptionGet('photo:ext:aperture');
        if(ap1line is None): ap1line=self.OptionGet('photo:ap1line');
    
        if(_opt.OptionGet('speedup')>=0):
            if(self.apcorr and isinstance(self.apcorr, tuple)):
                if(self.apcorr[0]>0):
                    print('ApCorr already calculated:', self.apcorr, file=self.stdout);
                    return;
        print(self.StartStep(), file=self.stdout); 
        try:
            if(not isinstance(suffCoo, str)): raise TypeError("RunStep{step}: `suffCoo` must be a string <{val}>".format(step=self.step, val=suffCoo));
            self.newstar=False;
            daofunct.Dao_check_file([self.fn+suffCoo, self.fn+suffFit]);
            outxt="{:}[{:d}]".format(suffCoo, funct.get_num_lines(self.fn+suffCoo)-daopar.DAO_Par['headerlen']);
            suffOld=suffCoo;
            suffCoo+='u';
            funct.clean_file(self.fn+suffCoo);
            if(os.path.exists(self.fn+suffLst)):
                outxt+='+{:}({:d},{:d})'.format(suffLst, funct.get_num_lines(self.fn+suffLst)-daopar.DAO_Par['headerlen'], daofunct.listselect(self.fn+suffOld, self.fn+suffLst, self.fwhm));
                daofunct.appendfiles(self.fn+suffOld, self.fn+suffLst, self.fn+suffCoo, id0=-1);
            else:
                os.symlink(self.fn+suffOld, self.fn+suffCoo);
            print(outxt, end=' - ', file=self.stdout);
            print(self.RunDaoPhot_photo(suffCoo=suffCoo, suffFit=suffFit, suffOut=suffOut), flush=True, file=self.stdout);
            fnout=self.SetOutput(suffOut);
            if(self.OptionGet('photo:apcorr:ap0')):
                deltamag=None
                mode=self.OptionGet('photo:apcorr:calc');
                if(mode.lower().startswith('dao')):
                    selopt=mode[4:] if(':' in mode) else '<p50,|p50';
                    with match.Match(self.fname+'_apc'+self.OptionGet('match:extension'), stdout=self.stdout if(self.OptionGet('output:verbose')) else 'null') as mfile:
                        # deltama=photo(master)-photo(frame) : First the standard-aperture photometry
                        mfile.makemch(mode='1', files=[self.fname+suffOut,  self.fname+self.OptionGet('photo:apcorr:ap0')]);
                        mfile.DAOmaster(flag=1, sigma=1, ncoeff=2, radius=(round(1.5*self.fwhm,1),round(.25*self.fwhm,1),round(.25*self.fwhm,1)), output='raw', selopt=selopt);
                        deltamag=mfile.deltamag()[0];
        
                print('ApCorr:', deltamag, file=self.stdout);
                if(deltamag):
                    if('APCORR'  in bpar.SkZp_Par['datatag']): funct.InputDataEntryUpdate(entry=self.fn, newdata={'APCORR': deltamag })
                    self.apcorr=deltamag;

            elif(self.OptionGet('photo:exptimecorr') and self.exptime>0):
                self.applymagcorr(suff=suffOut, ftype='ap', exptime=True, output=fnout+'0');
                if(ap1line):
                    daofunct.ap1line(apfile=fnout+'0', outfile=fnout+'0_1l');
            if(ap1line):
                daofunct.ap1line(apfile=fnout, outfile=fnout+'_1l');
#           if(os.path.exists(self.fn+suffLst)):
#               print('({:d},{:d})'.format(daofunct.listselect(fnout, self.fn+suffLst, self.fwhm, selected=fnout+suffLst.replace('.','_')), daofunct.listselect(fnout, self.fn+suffLst, -1) ), file=self.stdout);
      #
            self.GoodEndStep();
        except (SkZpipeException,OSError):
            self.EndStep();
            self.error=self.step;
            raise;
        except:
            if(self.SkZp_Opt['Flg']['debug']): raise;
        self.EndStep();
        self.flush_out();

 ####
    def RunStepGetFph(self, suffCoo=None, suffFit=None, suffOut=None, suffLst='.lsrc'):
        """Run the step to obtain  

Parameters
----------
    suffCoo : str, None
        Suffix of the source list. Default value: option 'photo:ext:coord'.
    suffFit : str, None
        Suffix of a pre-existing psf-fitting photometry. Optional, used to remove nearby stars for the aperture photometry. Default value: option 'photo:ext:fitting' ('.fph').
    suffOut : str, None
        Suffix of the output file. Default value: option 'photo:ext:aperture' ('.aph').
    suffLst : str, None
        Suffix of an additional source list to be appended to the main one. Optional, can be used if source list and psf-fitting photometry are the same file. Default value: '.lsrc'.
""";
        self.step="GetFph";
        if(not suffOut): suffOut='.alz';
        if(not suffFit): suffFit=self.SkZp_Opt['S']['photo:ext:fitting'];
        if(not suffCoo): suffCoo=self.SkZp_Opt['S']['photo:ext:coord'];
        print(self.StartStep(), file=self.stdout);
        try:
            if(not isinstance(suffCoo, str)): raise TypeError("RunStep{}: suffCoo must be a string".format(self.step));
            self.newstar=False;
            daofunct.Dao_check_file([self.fn+suffCoo]);
            outxt="{:}[{:d}]".format(suffCoo, funct.get_num_lines(self.fn+suffCoo)-daopar.DAO_Par['headerlen']);
            suffOld=suffCoo;
            suffCoo+='u';
            funct.clean_file(self.fn+suffCoo);
            if(os.path.exists(self.fn+suffLst)):
                outxt+='+{:}({:d},{:d})'.format(suffLst, funct.get_num_lines(self.fn+suffLst)-daopar.DAO_Par['headerlen'], daofunct.listselect(self.fn+suffOld, self.fn+suffLst, self.fwhm));
                daofunct.appendfiles(self.fn+suffOld, self.fn+suffLst, self.fn+suffCoo, id0=-1);
            else:
                os.symlink(self.fn+suffOld, self.fn+suffCoo);
            print(outxt, end=' - ', file=self.stdout);
            print(self.RunDaoPhot_photo(suffCoo=suffCoo, suffFit=suffFit),end=' - ', flush=True, file=self.stdout);
            print(self.RunAllstar(output=output), flush=True, file=self.stdout);
            fnout=self.fn+output if(output[0]=='.') else output;
            if(self.OptionGet('photo:exptimecorr') and self.exptime>0):
                fphfile=daofile.DAOPhotoFile(ftype='als', fname=fnout)
                for src in fphfile.srcL:
                        src.m+=2.5*math.log(self.exptime, 10);
                fphfile.write(fnout+'0');
            if(os.path.exists(self.fn+suffLst)):
                print('({:d},{:d})'.format(daofunct.listselect(fnout, self.fn+suffLst, self.fwhm, selected=fnout+suffLst.replace('.','_')), daofunct.listselect(fnout, self.fn+suffLst, -1) ), file=self.stdout);
      #
            self.GoodEndStep();
        except (SkZpipeException,OSError) as Exp:
            print(Exp, flush=True, file=self.stdout);
            self.error=self.step;
        except:
            if(self.SkZp_Opt['Flg']['debug']): raise;
        self.EndStep();
        self.flush_out();


###############
###############
#Not strictly related to the DAOp_Proc class, but connected with it
def DAOp_loopstep(imgdata=None):
    """Image processing procedure (This procedure can have just 1 parameter because it can be run by multiprocessing.pool). 

Parameters
----------
     imgdata : dict
         Dictionary with:
           'NAME' : entryname of the image (its basename)
           'OPT' : additional options
Return
------
    tuple :   (image name, error status, run time,  the time wasted waiting).""";
    img=None;
    errst=False;
    if(imgdata is None): raise TypeError("DpAlsRun: Wrong value for 'imgdata' in the loop");

    image=imgdata['NAME'];
    options=imgdata.get('OPT');
    steps=imgdata.get('STEPS')
    try:
        waitime=funct.WaitStop([ image, bpar.SkZp_Par['script']['scriptname'] ]) if(bpar.SkZp_Par['script']['scriptname']) else 0;
        midtime=funct.startime(verb=False);

        with DAOp_Proc(bpar.SkZp_Par['inputdata'][image], runtype=bpar.SkZp_Par['script']['runtype'], options=options) as img:
    #DOING
            img.RunSteps(steps);

    except (KeyboardInterrupt, SystemExit):
        errst=True;
        bpar.SkZp_Par['errorlist'].append(image);
        funct.endtime(verb=True, error=True);
        print("\nInterrupt in ", image, flush=True, file=bpar.SkZp_Par['stdout']);
        raise;
    except (SkZpipeException,OSError,TypeError,ValueError,KeyError) as err:
        runtime=funct.endtime(midtime, verb=False);
        errst=True;
        bpar.SkZp_Par['errorlist'].append(image);
        if(_opt.SkZp_Opt['Flg']['debug']): traceback.print_exc();
        if(isinstance(img, DAOp_Proc)):
            img.exit_wrong();
            img.close();
        print('\n',err, file=bpar.SkZp_Par['stdout'])
#if(_opt.SkZp_Opt['Flg']['debug']): raise
        return {'id':image, 'status':errst, 'runtime':runtime, 'idletime':waitime, 'dataframe':bpar.SkZp_Par['inputdata'][image]};
    except:
        errst=True;
        raise;
    else:
        errst=False;

    runtime=funct.endtime(midtime, verb=False);
    return {'id':image, 'status':errst, 'runtime':runtime, 'idletime':waitime, 'dataframe':bpar.SkZp_Par['inputdata'][image]}; 


