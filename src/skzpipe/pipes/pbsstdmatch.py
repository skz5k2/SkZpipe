import sys, re, os, math
import subprocess, numpy

from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters  import options as _opt
from ..parameters  import database as _db
from ..parameters.classes  import bclasses
from .. import functions as funct
from .. import mathfunct as mfunct
from ..photometry.daophot import daophals as DpAls
from ..photometry.standards import stetson as pbs
from . import photopipe 


def PbsStdMatch(inputdata=None, aphext=None, aperture=None, filtertag=None, stdfldtag=None, matchfiles=None, newtag={}, passband=None, select=None, options=None, runlist=None):
    """Pipeline to create photometric data for calibration using Stetson's Photoemtric Database.

Parameters
----------
    inputdata : str
        Input data as the filename or None for default (according to how the code is run).
    aphext : str
        Extension for aperture photometry (with dot). Default option 'photo:ext:aperture'.
    aperture : float
        Size of the aperture for the photometry to calculate the calibration. Default option 'photo:std:aperture'.
    filtertag : str
        Tag used to separate for different filters. Default 'FILTER'.
    stdfldtag : str
        Tag that identifies the standard field of the image. Default the key in option 'image:standard'.
    matchfiles : dict
        Dictionary with for each standard field (from `stdfldtag`) a matching file that can be used to have a starting trasformation coefficients
    newtag : dict
        Dictionary containing the definition for additional tag in input data.
    passband : dict
        Dictionary with the entries:
          'filter' : list 
               List of the standard names of the filters used in the images, ordered by wavelength.
          'passband' : dict
               Dictionary that map each instrumental filter names with its standard passband names (e.g. 'U', 'B', 'V', 'R', 'I').
               If not provide, it will be copied from internal database. Otherwise, The instrumental filter names are supposed to be standard.
          'calibration' : dict
               Dictionary providing for each used filter a two-element tuple of the standard passband used for the color term.
               Default from option 'photo:std:colorcalibration', otherwise first and last filter in 'filter' (maximum difference in wavelength).
    select : str, dict, list of str
        Selection options (input for InputDataSelect, see it). 
    options : dict
        Dictionary with additional options
    runlist : list of str
        list of the entries to process. None for parameter 'runlist'
    
Options
-------
    'photo:std:aperture' : float
        Used by `aperture` input parameter
    'photo:std:colorcalibration' : dict
        Dictionary of tuple
    'image:standard' : str
        Used by `stdfldtag` input parameter

""";
    _name_='PbsStdMatch';
    runlistbkp=None
    if(runlist is None): runlist=bpar.SkZp_Par['runlist']
    if(bpar.SkZp_Par['runlist']):
        if(set(bpar.SkZp_Par['inputlist'])-set(bpar.SkZp_Par['runlist'])): runlistbkp=bpar.SkZp_Par['runlist'].copy();
    if(matchfiles is not None and not isinstance(matchfiles,dict)): raise TypeError(_name_+": `matchfiles	 must be None or a dict");
    if(matchfiles is None): matchfiles={}; 
    if(select is None): select={};
    if('mode' in select):
        if(isinstance(select['mode'],list)):
            select['mode'].append('standard');
        else: select['mode']=[select['mode'], 'standard'];
    else: select['mode']=['standard'];

    try:
        funct.InputDataInitialize(inputdata=inputdata, select=select, options=options);
        funct.InputDataTagUpdate(newtag);
        bpar.SkZp_Par['store4later']['calib_coeff']={}; #After Initialization! It erases 'store4later'
      #Variable initialization post environment initialization
        if(not stdfldtag): stdfldtag=list(_opt.OptionGet('image:standard'))[0];
        if(not filtertag): filtertag='FILTER';
        if(not isinstance(filtertag, str) or not isinstance(stdfldtag, str)): raise TypeError(_name_+": `filtertag` and `stdfldtag` must be a string. <{}> <{}> ".format(filtertag,stdfldtag));
    
        instrL,instrimgD=funct.InputDataSplitByTag(tag='INSTRUMENT', entrylist=runlist);
        oneinstr=True if(len(instrL)==1) else False;
        print(file=bpar.SkZp_Par['stdout']);
#FOR EACH INSTRUMENT
        for instr in instrL:
            print("Instrument:", instr, file=bpar.SkZp_Par['stdout']);
            nightL,nitimgD=funct.InputDataSplitByTag('NIGHT', entrylist=runlist);
            onenit=True if(len(nightL)==1) else False;
      #FOR EACH NIGHT
            for night in nightL:
                print("  Night number:", night, file=bpar.SkZp_Par['stdout']); 
              #######################################################################
              #SET runlist
                runlist=nitimgD[night];
            #Setting passbandD for the current night
                if(passband):
                    passbandD=passband;
                else:
                    passbandD={'filter':[], 'passband':{}}; #'filter'= list of filters, 'passband'= list od standard passbands
                    ftrL=funct.InputDataTagValueSet('FILTER', entrylist=nitimgD[night]);  #Filters used in that night
                    if(instr in _db.SkZp_DB['passbands']): #the instrument is in the DB
                        for flt in ftrL:
                            if(flt in _db.SkZp_DB['passbands'][instr]): 
                                passbandD['filter'].append(_db.SkZp_DB['passbands'][instr][flt]); #Add the translation to standard name
                            else:
                                passbandD['filter'].append(flt); #Add directly, since it is already the standard name
                        passbandD['passband']=_db.SkZp_DB['passbands'][instr].copy(); #to translate instr filter to standard filter
                    else: #the instrument is NOT in the DB: Supposed to be already in standard name
                        for flt in _db.SkZp_DB['passbands'][None]:
                            if(flt in ftrL): passbandD['filter'].append(flt); #wavelength order
                passbandD['filter']=funct.sortbyfilter(iterable=passbandD['filter']); #standard names of used filters ordered by lambda
                passbandD.setdefault('calibration',{});
                opt=_opt.OptionGet('photo:std:colorcalibration');
                for flt in passbandD['filter']: #Setting default values for color calibration
                    passbandD['calibration'].setdefault(flt, opt.get(flt));
                    if(not passbandD['calibration'][flt]):
                        passbandD['calibration'][flt]=(passbandD['filter'][0],passbandD['filter'][-1]);

                calibcoeffD={'atm_coeff':{}, 'mag_coeff':{}}
                calibcoeffD['atm_coeff'].update(dict( (x,[]) for x in passbandD['filter']  ));
                calibcoeffD['mag_coeff'].update(dict( (x,[0,0]) for x in passbandD['filter']  ));
            
            #Get Aperture Photometry
                print(">>  Producing aperture photometry  for standard fields corrected for exposure time", file=bpar.SkZp_Par['stdout']);
                if(not aperture or not isinstance(aperture, list)):
                    if(not aperture): aperture=_opt.OptionGet('photo:std:aperture'); 
                    if(isinstance(aperture, (float,int))): aperture=[aperture];
                    else: raise TypeError(_name_+": `aperture` must be a list or a number <{}>".format(aperture)); 
                if(not aphext): aphext=_opt.OptionGet('photo:ext:aperture');
                #there is a calculated PSF?
                psfdone=_opt.OptionGet('photo:psf:done');
                missing=[img for img in runlist if(not os.path.exists(img+psfdone) )]; #Checking if an images has not a psf calculated
                if( missing ): #Checking if an images has not a psf calculated
                    tryit=True;
                    if(_opt.OptionGet('speedup')>1):
                        if(len(missing)<len(runlist)/10): tryit=False;
                    if(tryit):
                        print("    Some images don't have a PSF: calculationg it", file=bpar.SkZp_Par['stdout']);
                        photopipe.DAOPipe(runtype='psfcal', runlist=missing, options={});
                funct.InputDataSelect(select={'mode':'psfdone', 'tag':{'PSFELLIP': (lambda x: x<_opt.OptionGet('photo:std:maxellipt')) }}, entrylist=runlist)
                missing=[img for img in runlist if(not os.path.exists(img+aphext) )]; #Checking if an images has no aperture photometry
                photopipe.DAO_GetAph(options={'photo:aperture':aperture, 'photo:ext:aperture':aphext, 'photo:ext:coord':'.als', 'photo:ext:fitting':'.als', 'photo:exptimecorr':True});
                
          #####################################
            #Get Mean magnitudes
                print("\n>>  Mean imagnitude for each field/filter", file=bpar.SkZp_Par['stdout']);
                (tagL, tagD)=funct.InputDataSplitByTag(tag=[stdfldtag, filtertag], sep='_{}_'.format(night), entrylist=runlist)    
                catstdD={};
                for tag in tagL:
                    print("    field/filter:", tag, tagD[tag], file=bpar.SkZp_Par['stdout']);
                    fld,fltr=tag.split('_{}_'.format(night));
                    if(len(tagD[tag])>1):
                        with pbs.match.Match(tag+_opt.SkZp_Opt['S']['match:extension'], mode='w') as mch:
                            if(fld in matchfiles):
                                mch.makemch(mode='use:'+matchfiles[fld]+'@6', files=[x+aphext+'0' for x in tagD[tag]]);
                            elif(mch.exist and _opt.OptionGet('speedup')>=1):
                                pass;
                            else:
                                #mch.makemch('1', files=[x+aphext+'0' for x in tagD[tag]]);
                                mch.makemch('dao:<p50', files=[x+aphext+'0' for x in tagD[tag]]);
                            mch.DAOmaster('2,.5,2', 1, 4, 20, 'mch');
                            mch.DAOmaster('2,.5,2', 1, 6, 20, 'magI');
                            mch.DAOmaster('2,.5,2', 1, 6, 10, 'magI');
                            funct.InputDataEntryAdd(new=mch.base, old=mch.frames[0], entrytype='cat:std');
                            funct.clean_file(mch.base+'.als');
                            os.symlink(mch.frames[0]+'.als', mch.base+'.als');
                            catstdD[tag]=mch.base;
    #            magt0=2.5*math.log(bpar.SkZp_Par['inputdata'][mch.frames[0]]['EXPTIME'], 10);
                            am0=bpar.SkZp_Par['inputdata'][mch.frames[0]]['AIRMASS'];
                            print("Frame                   mag_shift   delta_AM   atm_coeff_extim  err", file=bpar.SkZp_Par['stdout']); 
                            atmcoeffL, errL=[], [];
                            for fn,tdm in zip(mch.frames[1:], mch.deltamag()):
                                am=bpar.SkZp_Par['inputdata'][fn]['AIRMASS'];
                                atmcoeffL.append(round(-tdm[0]/(am-am0),4) if(am!=am0 and abs(tdm[0])>0.01) else None );
                                errL.append(round(math.sqrt((tdm[1]/(am-am0))**2+(2*tdm[0]*0.001/(am-am0)**2)**2),6) if(am!=am0 and abs(tdm[0])>0.01) else None );
                                print("{:20}    {:6f}    {:6f}   {}     {}".format(fn, -tdm[0], round(am-am0,4), atmcoeffL[-1], errL[-1]), file=bpar.SkZp_Par['stdout']); 
                            atmcoeffA=[x for x in atmcoeffL if(x and 0<x<2)];
                            if(len(atmcoeffA)>1):
                                atmcoeffA=numpy.array(atmcoeffA);
                                ac_mean, ac_std=round(atmcoeffA.mean(),4), round(atmcoeffA.std(),5);
                                ac_mstd=round(ac_std/numpy.sqrt(len(atmcoeffA)),5);
                            elif(len(atmcoeffA)==1): ac_mean, ac_std, ac_mstd=atmcoeffA[0], 0,0
                            else: ac_mean, ac_std, ac_mstd= 0, 0, 0;
                    else:
                        shutil.copy(tagD[tag][0]+aphext, tag+'.mag');
                        os.symlink(tagD[tag][0]+'.als', tag+'.als');
                        funct.InputDataEntryAdd(new=tag, old=tagD[tag][0], entrytype='cat:std');
                        catstdD[tag]=tag;
                        ac_mean, ac_std, ac_mstd= 0, 0, 0;

                    if(ac_mean>0):
                        calibcoeffD['atm_coeff'][fltr].append( (ac_mean, ac_mstd )  );
                        print("Atmospheric coefficient for filter {fltr} is {mean} +-{std:.5f} {std_mean:.5f}\n".format(fltr=fltr, mean=ac_mean, std=ac_std, std_mean=ac_mstd), file=bpar.SkZp_Par['stdout']); 
                    else:
                        print("Not enough data to calculate atmospheric coefficient for filter {fltr}\n", file=bpar.SkZp_Par['stdout']); 
                    funct.flush_out()
                            
            #####################################
              #Get Standard for each field/filter
                print("\n>>  Creating standard list and standard catalog for each night/field/filter group", file=bpar.SkZp_Par['stdout']);
                pbs.GetStandard(tag=stdfldtag, files=tagL, addpassband=passbandD['filter'], match_ext=['.mag', '.als']);
                funct.flush_out()
                                                                                  
                print("\nWrite down inputdata", file=bpar.SkZp_Par['stdout']);
                funct.InputDataWrite(outfile='+-std');
                
                funct.flush_out()
            #####################################
                print("\n>>  Create global standard data & fit", file=bpar.SkZp_Par['stdout']);
                (filterL, filterID)=funct.InputDataSplitByTag(tag=filtertag, entrylist=tagL);   #return with instrument Filter name, not standard 
                if(passbandD.get('passband')):
                    filterD={};
                    for flt,imgL in filterID.items():
                        filterD[passbandD['passband'][flt]]=imgL; #translating the names to standard
                else: filterD=filterID;
                for fltr in passbandD['filter']: #standard names of used filters ordered by lambda
                    acoef,eacoeff=0,0;
                    if(calibcoeffD['atm_coeff'][fltr]):
                        if(len(calibcoeffD['atm_coeff'][fltr])==1): acoeff,eacoeff=calibcoeffD['atm_coeff'][fltr][0];
                        else:
                            for coef, err in calibcoeffD['atm_coeff'][fltr]:
                                if(err>0):
                                    acoeff+=coef/err;
                                    eacoeff+=1/err;
                            eacoeff=1/eacoeff;
                            acoeff*=eacoeff;
                    print('\n  >> Filter:',fltr, "  Atmospheric coefficient: {} +- {}".format(acoeff,eacoeff) if(eacoeff>0) else "No known atmospheric coefficient", file=bpar.SkZp_Par['stdout'])
                    fn_out='std{nit}_{fltr}.2fit'.format(nit=night, fltr=fltr);
                    tcol=passbandD['calibration'].get(fltr, tuple());
                    print('Calibration color:', tcol, file=bpar.SkZp_Par['stdout']);
                    nfld=len(filterD[fltr]);
                    ydata,erry,xdata=[],[],[]

                    for ii in range(nfld):
                        with open(filterD[fltr][ii]+'-std.out') as fin:
                            for line in fin:
                                    if('#' in line):
                                        continue;
                                    tmpl=[float(x) for x in line.split()];
                                    x,y, am=tmpl[1], tmpl[2], tmpl[-1]
                                    delta, edelta=tmpl[3]-tmpl[5]-acoeff*bpar.SkZp_Par['inputdata'][mch.frames[0]]['AIRMASS'], math.sqrt(tmpl[4]**2+tmpl[6]**2+(eacoeff*bpar.SkZp_Par['inputdata'][mch.frames[0]]['AIRMASS'])**2); #m-M err(m-M)
                                    if(tcol):
                                        col1,col2= 7+2*passbandD['filter'].index(tcol[0]), 7+2*passbandD['filter'].index(tcol[1]);
                                    else: col1,col2=7, len(tmpl)-5;
                                    col, ecol=tmpl[col1]-tmpl[col2], math.sqrt(tmpl[col1+1]**2+tmpl[col2+1]**2);
                                    ydata.append(delta)
                                    erry.append(edelta)
                                    xdata0=[1, col, am, col*col]
                                    for jj in range(nfld):
                                        xdata0.append( 1 if(jj==ii) else 0);
                                    xdata.append(xdata0)
                    ydata=numpy.array(ydata)
                    erry= numpy.array(erry)
                    xdata=numpy.array(xdata)
                    datafitD=None
                    if(nfld>1):
                        print('Linear fit: m-M=c1+c2*col+c3*am', file=bpar.SkZp_Par['stdout']);
                        outD=mfunct.fudgedlinearfit(ydata=ydata, erry=erry, xdata=xdata[:,(0,1,2)], fudge=None, guess=None, options=None)
                        print(outD, file=bpar.SkZp_Par['stdout']);
                        if(False):datafitD=outD

                        print('with additional weight (usually better)', file=bpar.SkZp_Par['stdout']);
                        outD=mfunct.fudgedlinearfit(ydata=ydata, erry=erry, xdata=xdata[:,(0,1,2)], fudge={'pbs':{'a':2, 'b':4}}, guess=None, options=None)
                        print(outD, file=bpar.SkZp_Par['stdout']);
                        if(True):datafitD=outD

                        print('Quadratic fit: m-M=c1+c2*col+c3*am+c4*col^2', file=bpar.SkZp_Par['stdout']);
                        outD=mfunct.fudgedlinearfit(ydata=ydata, erry=erry, xdata=xdata[:,(0,1,2, 3)], fudge=None, guess=None, options=None)
                        print(outD, file=bpar.SkZp_Par['stdout']);
                        if(False):datafitD=outD
                    else:
                        print('Linear fit: m-M=a[01]+a[02]*col', file=bpar.SkZp_Par['stdout']);
                        outD=mfunct.fudgedlinearfit(ydata=ydata, erry=erry, xdata=xdata[:,(0,1)], fudge=None, guess=None, options=None)
                        print(outD, file=bpar.SkZp_Par['stdout']);
                        if(False):datafitD=outD

                        print('with additional weight (usually better)', file=bpar.SkZp_Par['stdout']);
                        outD=mfunct.fudgedlinearfit(ydata=ydata, erry=erry, xdata=xdata[:,(0,1)], fudge={'pbs':{'a':2, 'b':4}}, guess=None, options=None)
                        print(outD, file=bpar.SkZp_Par['stdout']);
                        if(True):datafitD=outD

                        print('Quadratic fit: m-M=a[01]+a[02]*col+a[03]*col^2', file=bpar.SkZp_Par['stdout']);
                        outD=mfunct.fudgedlinearfit(ydata=ydata, erry=erry, xdata=xdata[:,(0,1,3)], fudge=None, guess=None, options=None)
                        print(outD, file=bpar.SkZp_Par['stdout']);
                        if(False):datafitD=outD

                    calibcoeffD['mag_coeff'][fltr]=list( zip(datafitD['coeff'], datafitD['error']) )
                    funct.flush_out()
              ####################################################################### 
                for flt in passbandD['filter']:
                        if(len(calibcoeffD['atm_coeff'][flt])==1): calibcoeffD['atm_coeff'][flt]=calibcoeffD['atm_coeff'][flt][0];
                        else:
                            ac0,eac0=0,0;
                            for ac,eac in calibcoeffD['atm_coeff'][flt]:
                                ac0+=ac/eac;
                                eac0+=1/eac;
                            ac0/=eac0;
                            calibcoeffD['atm_coeff'][flt]=(ac0,1/eac0);
                print("Night: {nit}\nAtmospheric coefficients:\n\t".format(nit=night), calibcoeffD['atm_coeff'], file=bpar.SkZp_Par['stdout']); 
                print("Calibration coefficient:\n\t", calibcoeffD['mag_coeff'], file=bpar.SkZp_Par['stdout']); 
                nparam={night:{}};
                for flt in passbandD['filter']:
                    nparam[night][flt]={'am':calibcoeffD['atm_coeff'][flt], 'coeff':calibcoeffD['mag_coeff'][flt], 'color':passbandD['calibration'][flt]}
                print("'nparam': {}   ".format(night), nparam, file=bpar.SkZp_Par['stdout']);
                bpar.SkZp_Par['store4later']['calib_coeff'][night]=nparam;
                with open(_opt.OptionGet('photo:std:storefile')+"_{}".format(night), 'w') as fout:
                    for flt in passbandD['filter']:
                        fout.write("{}   {} {}".format(flt, calibcoeffD['atm_coeff'][flt][0],  calibcoeffD['atm_coeff'][flt][1] ));
                        fout.write("  {},{} ".format(passbandD['calibration'][flt][0], passbandD['calibration'][flt][1]));
                        for cc in calibcoeffD['mag_coeff'][flt]:
                            if(not isinstance(cc,tuple)): cc=(0,0);
                            fout.write("   {} {}".format(cc[0], cc[1] ));
                        fout.write('\n');
                
#     #######
#  #Get Aperture Photometry
#    print(">>  Producing aperture photometry for science images", file=bpar.SkZp_Par['stdout']);
#    funct.InputDataSelect(select='catalog'); #It will get the other selection option from Options
#    tmpl=[];
#    for instr in instrimgD:
#      tmpl.extend(instrimgD[instr]);
#    bpar.SkZp_Par['runlist']=[x for x in bpar.SkZp_Par['runlist'] if(x not in tmpl)];
#    
#    #there is a calculated PSF?
#    #missing=[img for img in bpar.SkZp_Par['runlist'] if(not os.path.exists(img+aphext) )]; #Checking if an images has no aperture photometry
#    DpAlsPipe(runtype='photo', steps='GetAph', options={'photo:aperture':aperture, 'photo:ext:aperture':aphext, 'photo:ext:coord':'.alf', 'photo:ext:fitting':'.alf'});
#    ap_corr={};
#    for img in bpar.SkZp_Par['runlist']:
#      with pbs.match.Match(img+'_apcor'+_opt.SkZp_Opt['S']['match:extension'], mode='w') as mch:
#        mch.makemch('1', files=[img+'.ap', img+aphext]);
#        mch.DAOmaster('2,1,2', 1, 2, 20, 'mch');
#        mch.DAOmaster('2,1,2', 1, 2, 10, 'raw');
#        ap_corr[img]=mch.deltamag()[0];
#        funct.flush_out()
#    for img in bpar.SkZp_Par['runlist']:
#        print("AP-AP(std) for",img, ap_corr[img], file=bpar.SkZp_Par['stdout']);
        
    except:
        raise;
    finally:
        if(runlistbkp): bpar.SkZp_Par['runlist']=runlistbkp;
