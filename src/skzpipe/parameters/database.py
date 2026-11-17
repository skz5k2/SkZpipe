import os, re, math, io, numpy;
from copy import deepcopy;
from collections import ChainMap

#from .basicpar import SkZp_ParDef
from .basicpar import *
from . import options  as _opt;

################
##  DATABASE  ##
################
SkZp_DB={'_name_':'SkZp_DB', '_doc_':{}};
SkZp_DB['listofinstruments']=['GSAOI', 'IMACS_Short-Camera', 'IMACS_Long-Camera', 'VIRCAM', 'VIRCAM:VVV', 'Direct/4Kx4K-4', 'DECam', 'Tucan'];

SkZp_DB['headerkey']={};      #Which cards read from headers and how
SkZp_DB['namepattern']={};    #How use format to generate name for extracted images or workname
SkZp_DB['chipselect']={};     #Info for chip selection
SkZp_DB['orientation']={};    #Spacial orientation of the camera
SkZp_DB['nopsfzone']={};      #Part of sensors not to use for PSF calculation
SkZp_DB['badpixelarea']={};   #part of the sensor with bap pixeles
SkZp_DB['passbands']={};      #List of passband of the cameras
SkZp_DB['alias']={};          #alias: for passbands, chip names, ...
SkZp_DB['gainronhigh']={};    #Gain, RON and high good values
SkZp_DB['SkZp_Opt']={};       #Option for specific instrument
SkZp_DB['obs_set_check']={};  #Check for data set (to avoid incomplete data subset)

###############
## HEADERKEY ##
###############
SkZp_DB['_doc_']['headerkey']="""Provide information about how to derive the values of the tags in the inputdata internal database using information in FITS header cards for a specific instrument.
  'None' entry is for the default values; the entries with the names of the instrument is for the 
  variations and aditional tags.
  For each instrument entry:
   -Two keys are for the headerkey groups:
       'mos' : data stored in the header of the HDU 0 of the mosaic (they are the more generic ones 
               about the overall observation: instrument, date/time, exposure time, filter, ...)
       'chip': data stored in the header of the chips (they are more specific about the sensors: size, 
               binning, internal offset, ...)
    They are given as a dictionary where the key is the tag name and the value is the way to determine 
    the tag value from header information.
    Card key names have to be without 'HIERARCH' prefix, that is automatically eliminated by pyfits/internal 
    functions.
    Callable input is the header dict (the keys are the card names, not the tags).
    If the instrument returns a file for each sensor, both 'mos' and 'chip' will be use together.
   -Two keys are for the menangment:
       'output' : The tipe of output of the instrument: 'mosaic' or 'chip'
       'datatag': Ordered list of additional tags for that instrument


Format for the value
--------------------
  - a string with the name of the header card key to be read.
  - a callable
  - a dictionary with:
    'cards' : list of str
        A list of cards to use
    'rej' : list 
        A list of values to reject card values.
    'eval' : str or callable
        A callable, that use the header dictionary ['cards' list] as input to produce the final value;
        A string that describe the action, as:
               'mean' for the mean of the values from 'cards'.
    'round' : int
        Number of decimal digit to leave for the rounding.
    'join' : str
        A character(string) that will be used to join the card values.
    'def'  : default values.

""";

def headerkeyread(tag=None, card=None, hdrinfo=None):
    """Transform the info from header data to value for tags in inputdata.

Parameters
----------
    tag : str
        Name of the tag
    card : dict or str or callable
        Information on manage the header data (see below for details about format)
    hdrinfo : dict
        Header data

Returns
-------
    output : value
        Ruturn the value to be store in the tag. None for no value.

`card` provides information about how to elaborate the information in FITS header cards to obtain the final values of the tags in the inputdata dataframe.
  They are given as a dictionary where the key is the tag name and the value the way to determine the tag value from header information.
  They are grouped in 'mos' and 'chip', according to if they are present in the header of the chips or the hdu 0 (actually they will read toghether, so the separation is not really important).
  Card key names have to be without HIERARCH prefix, that is automatically eliminated by pyfits/internal functions.
  Callables must have as input the header dict, so the keys must be the card names, not the tags.

Format for the value of `card`
------------------------------
  - a string with the name of the header dard key to be read.
  - a callable
  - a dictionary with:
    'cards' : list of str
        A list of cards to use
    'rej' : list 
        A list of values to reject card values.
    'eval' : str or callable
        A callable applied on each header info from ['cards' list] to produce the input for the final value
        A string that describe the action, as:
               'mean' for the mean of the values from 'cards'.
    'round' : int
        Number of decimal digit to leave for the rounding.
    'join' : str
        A character(string) that will be used to join the card values.
    'def'  : default values.

"""
    _name_='database.headerkeyread'

    #from free format to dict format
    if(callable(card)): card={'eval':card}
    elif(isinstance(card, str)): card={'cards':[card]}
    elif(isinstance(card, (list,tuple,set))): card={'cards':list(card)}
    if(isinstance(card.get('cards'), str)): card={'cards':[card['cards']]}
    if(not isinstance(card, dict)): raise TypeError(f"{_name_}: the definition of tag '{tag}' is wrong.")
    
 ##%%%%%##
    def _RDH_get(tag=None, cardL=None):
        """Fits/MosaicHeaderInfoRetrieve-database.headerkeyread internal function: convert the headerinfo to the wanted value for the tag, according to parameter 'datatagconvert'
  Parameters
  ----------
      tag : str, None
          Name of the tag
      cardL : list
          List with values to convert
  Return
  ------
      List of coverted card values
  """
        _name_='_RDH_get';
        tmpv=None;
        if(tag in SkZp_Par['datatagconvert']):
            try:
                if(callable(SkZp_Par['datatagconvert'][tag])):
                    tmpv=SkZp_Par['datatagconvert'][tag](cardL) 
                elif(isinstance(SkZp_Par['datatagconvert'][tag], str)):
                    if(not isinstance(cardL, tuple)): cardL= tuple( cardL )
                    tmpv=SkZp_Par['datatagconvert'][tag].format(*cardL) 
            except:
                tmpv=None
        else:
            tmpv=cardL
        return tmpv
 ##%%%%%##


    outdata=None; #Initialization for the tag value
  #Get from headerdata the wanted info/cards 
    cardL=[hdrinfo[fkey] for fkey in card['cards'] if fkey in hdrinfo] if('cards' in card) else [];

  #Reject unwanted values
    if('rej' in card):
        cardL=[val for val in cardL if val not in card['rej']]

    if(not cardL): #no input info
        if('eval' in card):  #the callable is run on all the header info
            try:
                outdata=card['eval'](hdrinfo);
            except Exception as exc:
                outdata=None;
                if(_opt.OptionGet('debugging:log')): print(f'eval: {tag} < {card} > : exception', file=SkZp_Par['stderr']);
        if('def' in card and outdata is None):   outdata=card['def']
  ####
    if('eval' in card):
        if(card['eval']=='mean'):
            outdata=numpy.mean([float(x) for x in cardL]);
        elif(callable(card['eval'])): 
            try:
                outdata=card['eval'](hdrinfo);
            except Exception as exc:
                outdata=None;
                if(_opt.OptionGet('debugging:log')): print('eval', tag, card, file=SkZp_Par['stderr'])
    else: outdata=cardL
    if('round' in card):
            outdata=  round(outdata, card['round'])
    if('join' in card): outdata=card['join'].join([str(val) for val in outdata])

    if(not isinstance(outdata, str) and hasattr(outdata, 'count')):
        if(len(outdata)==1):  outdata=outdata[0]
        else: outdata=tuple(cardL)

    outdata=_RDH_get(tag, outdata) #transform info from header to final tag value

    if('def' in card and  outdata is None):   outdata=card['def']

    if(isinstance(outdata, str)):
        outdata=outdata.strip()
        if(outdata==''): outdata=None;

    return outdata;


 #General
def _hdr_DATE(hdrd): 
    return hdrd['DATE-OBS'].split('T')[0] if('T' in hdrd['DATE-OBS']) else hdrd['DATE-OBS']
def _hdr_TIME(hdrd): 
    return hdrd['DATE-OBS'].split('T')[1] if('T' in hdrd['DATE-OBS']) else hdrd['TIME-OBS']
def _hdr_TYPE(hdrd): 
    card=hdrd.get('IMAGETYP')
    if(card):  card=hdrd['IMAGETYP'].lower()
    else: return card
    for itype in SkZp_Par['entrytypelist']:
        if(card.startswith(itype)): return itype
    for itype in SkZp_Par['entrytypelist']:
        if(itype in card.split()): return itype
    if('light frame' in card): return 'raw'
    if('frame' in card): card=re.sub('frame','',card).strip()
    return card


# 'ENTRYTYPE''HIGH', 'GAIN', 'RON', 'CHIP', 'EXPTIME', 'FILTER', 'PSFFWHM', 'PSFELLIP', 
# 'AIRMASS', 'SKY', 'MJD', 'NIGHT', 'DATE', 'TIME', 'RA', 'DEC', 'OBJECT', 'INSTRUMENT', 
# 'MAGZPT', 'NX', 'NY', 'BITPIX', 'EXPID', 'IMGQUAL', 'OBSSET', 'SCALE', 
# 'TELESCOPE', 'SITENAME', 'SITEALT', 'SITELAT', 'SITELONG', 'EQUINOX', 
# 'STKOFF', 'AV,SM', 'DATASEC', 'OVERSCAN', 'IMGSTAT', 'APCORR', 'SKZP_FLG'];


SkZp_DB['headerkey'][None]={ 'mos':{'INSTRUMENT':'INSTRUME', 'OBJECT':'OBJECT', 'AIRMASS':'AIRMASS', 'RA':'RA', 'DEC':'DEC', 'FILTER':'FILTER', 'MJD':'MJD-OBS', 'DATE':_hdr_DATE, 'TIME':_hdr_TIME, 
                                   'EXPTIME':'EXPTIME', 'TELESCOPE':'TELESCOP', 'SITENAME':'SITENAME', 'SITEALT':'SITEALT', 'SITELAT':'SITELAT', 'SITELONG':'SITELONG', 'EQUINOX':'EQUINOX', 'EXPID': 'None'},
                                   'chip':{'NX':'NAXIS1', 'NY':'NAXIS2', 'BITPIX':'BITPIX', 'ENTRYTYPE':_hdr_TYPE, 'GAIN':'EGAIN', 'RON':'ENOISE', 'SCALE':'SCALE', 'MAGZPT':'MAGZPT', 'OVERSCAN':{'cards':['NOVERSCN','NBIASLNS']}, 'DATASEC':'DATASEC', 'BIASSEC':'BIASSEC', 'SKY': 'None' },
                           'datatag':SkZp_Par['def:datatag']};
 #GSAOI
SkZp_DB['headerkey']['GSAOI']={ 'mos':{'DATE':'DATE-OBS', 'TIME':'TIME-OBS','FILTER':{'rej':('Clear'), 'cards':['FILTER1','FILTER2']}, 'OFFSET':{'cards':['POFFSET','QOFFSET']}, 'EXPID':'DATALAB', 'FOWLER':'LNRS', 'TELESCOPE':'TELESCOP', 'SITENAME':'OBSERVAT', 'SITEALT':{'def':2722}, 'SITELAT':{'def', -30.24075}, 'SITELONG':{'def', -70.7366933}},
                               'chip':{'CHIP':'FRMNAME', 'SCALE':{'cards':['XSCALE','YSCALE']}, 'GAIN':'GAIN', 'RON':'RDNOISE'},
                               'datatag':['OFFSET'], 'output':'mosaic' };
 #Swope
SkZp_DB['headerkey']['Direct/4Kx4K-4']={ 'mos':{},
                                        'chip':{'DATE':'UT-DATE', 'TIME':'UT-TIME', 'CHIP':'OPAMP', 'FILTER':{'rej':['open','Open','Free_slot'], 'cards':'FILTER'}, 'RA':'RA-D', 'DEC':'DEC-D', 'OFFSET':{'cards':['CHOFFX','CHOFFY']}, 'BINNING':'BINNING', },
                                     'datatag':['OFFSET', 'BINNING', ], 'output':'chip' };

 #Baade
SkZp_DB['headerkey']['IMACS_Short-Camera']={ 'mos':{'DATE':'UT-DATE', 'TIME':'UT-TIME'},
                                        'chip':{'CHIP':'CHIP', 'FILTER':{'rej':['open','Open','Free_slot'],'cards':['FILTER']}, 'RA':'RA-D', 'DEC':'DEC-D', 'OFFSET':{'cards':['CHOFFX','CHOFFY']}, 'EXPID':'FILENAME',
                                                'ROTANGLE':'ROTANGLE', 'BINNING':'BINNING', 'DISPERSER':'DISPERSR', 'FOCUS':'DETFOCUS', 'READSPEED':'SPEED', },
                                     'datatag':['OFFSET', 'ROTANGLE', 'BINNING', 'DISPERSER', 'FOCUS', 'READSPEED', ], 'output':'mosaic' };
SkZp_DB['headerkey']['IMACS_Long-Camera']={ 'mos':{'DATE':'UT-DATE', 'TIME':'UT-TIME'},
                                        'chip':{'CHIP':'CHIP', 'FILTER':{'rej':['open','Open','Free_slot'],'cards':['FILTER']}, 'RA':'RA-D', 'DEC':'DEC-D', 'OFFSET':{'cards':['CHOFFX','CHOFFY']}, 'EXPID':'FILENAME',
                                                'ROTANGLE':'ROTANGLE', 'BINNING':'BINNING', 'DISPERSER':'DISPERSR', 'FOCUS':'DETFOCUS', 'READSPEED':'SPEED', },
                                     'datatag':['OFFSET', 'ROTANGLE', 'BINNING', 'DISPERSER', 'FOCUS', 'READSPEED', ], 'output':'mosaic' };

 #VIRCAM
SkZp_DB['headerkey']['VIRCAM']    ={ 'mos':{ 'TILE':'OBJECT',
                                           'AIRMASS':{'eval':'mean', 'cards':['ESO TEL AIRM START','ESO TEL AIRM END'], 'round':6}, 'FILTER':'ESO INS FILT1 NAME',
                                            'DIT':'ESO DET DIT', 'NDIT':'ESO DET NDIT', 'OFFSET':'OFFSET_I', 'POSANG':'ESO TEL POSANG', 'OBNAME':'ESO OBS NAME', 'SITELAT':'ESO TEL GEOLAT', 'SITELONG':'ESO TEL GEOLON', 'SITEALT':'ESO TEL GEOELEV', 'SITENAME':{'def':'PARANAL'}, 'SCALE':{'def':0.341}, 'TELESCOPE':{'def':'VISTA'}, }, 
                                    'chip':{'CHIP':'ESO DET CHIP NO', 'SUBSECT':(lambda hdrd: chr((((hdrd['ESO DET CHIP NO']-1)>>2)<<1)+int((hdrd['OFFSET_I']-1)/3)+ord('a')) ), },
                                 'datatag':['DIT', 'NDIT', 'OFFSET', 'POSNAME', 'TILE', 'OBNAME', 'SUBSECT'], 'output':'mosaic' };
 #VIRCAM:VVV
SkZp_DB['headerkey']['VIRCAM:VVV']=deepcopy(SkZp_DB['headerkey']['VIRCAM']);
SkZp_DB['headerkey']['VIRCAM:VVV']['mos'].update({'CASUVERS':'CASUVERS', 'ESOGRADE':'ESOGRADE', 'OBSTATUS':'OBSTATUS', 'OBTYPE':(lambda hdrd:  re.sub('\d', '', hdrd['ESO OBS NAME'])[0:2] ), 'OBSSET':(lambda hdrd:hdrd['ESO OBS NAME'][:4]) });
SkZp_DB['headerkey']['VIRCAM:VVV']['chip'].update({'GAINCOR':'GAINCOR', 'SKY':'SKYLEVEL', 'FWHM':'SEEING', 'ELLIPTIC':'ELLIPTIC', 'MAGZPT':'MAGZPT', 'FOV':{'join':'-', 'cards':['OBJECT','OFFSET_I','ESO DET CHIP NO']} });
SkZp_DB['headerkey']['VIRCAM:VVV']['datatag']=['GAINCOR', 'ELLIPTIC', 'DIT', 'NDIT', 'OFFSET', 'POSNAME', 'TILE', 'OBNAME', 'OBTYPE', 'SUBSECT', 'CASUVERS', 'ESOGRADE', 'OBSTATUS'];

 #DECAM
SkZp_DB['headerkey']['DECam']={ 'mos':{'EQUINOX':'TELEQUIN', 'DIMMSEE':'DIMMSEE', 'MAGZERO':'MAGZERO', 'PHOTFLAG':'PHOTFLAG', 'EXPID':'RECNO', 'PROCTYPE':'PROCTYPE',
                                       },
                               'chip':{'CHIP':'EXTNAME', 'SKY':'SKYBRITE', 'SKYSIGMA':'SKYSIGMA'},
                            'datatag':['DIMMSEE', 'MAGZERO', 'PHOTFLAG', 'PROCTYPE',   'SKYSIGMA'] };

  #Tucan
SkZp_DB['headerkey']['Tucan']={ 'mos':{},
                               'chip':{'ENTRYTYPE':'FRAME', 'FRAME':'FRAME', 'CCD-TEMP':'CCD-TEMP', 'CHIP':{'def':'X'}},
                            'datatag':['FRAME', 'CCD-TEMP'] };
  #SBIG CCD
SkZp_DB['headerkey']['SBIG CCD']={ 'mos':{},
                               'chip':{'FRAME':'FRAME', 'CCD-TEMP':'CCD-TEMP', 'CHIP':{'def':'X'}},
                            'datatag':['FRAME', 'CCD-TEMP'] };

  #Ekos
SkZp_DB['headerkey']['Ekos']={ 'mos':{},
                               'chip':{'ENTRYTYPE':'FRAME', 'FRAME':'FRAME', 'CCD-TEMP':'CCD-TEMP', 'CHIP':{'def':'X'}},
                            'datatag':['FRAME', 'CCD-TEMP'] };
##


############################
## EXTRACTING FROM MOSAIC ##
############################
##
###################################
## CHIP SELECTION
SkZp_DB['_doc_']['chipselect']="""Dictionary with keys 'part', 'pos', 'posang', 'reject' with callable to be used during chip selection procedure. """;
SkZp_DB['chipselect'][ 'VIRCAM'     ]= {'part':( lambda xdict: chr((((int(xdict['CHIP'])-1)>>2)<<1)+int((int(xdict['OFFSET'])-1)/3)+ord('a'))   ),
                                         'pos':( lambda xdict: ( 16.7*(((int(xdict['CHIP'])-1)%4)-1.5), 22.*(((int(xdict['CHIP'])-1)>>2)-1.5) ) ),
                                      'posang':( lambda xdict: (90-float(xdict['POSANG'])) ), };
SkZp_DB['chipselect'][ 'VIRCAM:VVV' ]= deepcopy(SkZp_DB['chipselect']['VIRCAM']);

def _DECam_chippos_(chip=None):
    chipgap, chipsize =(153, 201), (4096,2048);
    chippos0={ '1':(-3.0*(chipgap[0]+chipsize[0])*0.27/60,  0.5*(chipgap[1]+chipsize[1])*0.27/60),   
            '2':(-2.0*(chipgap[0]+chipsize[0])*0.27/60,  0.5*(chipgap[1]+chipsize[1])*0.27/60),   
            '3':(-(chipgap[0]+chipsize[0])*0.27/60, 0.5*(chipgap[1]+chipsize[1])*0.27/60),    
            '4':(0.0, 0.5*(chipgap[1]+chipsize[1])*0.27/60),   
            '5':((chipgap[0]+chipsize[0])*0.27/60, 0.5*(chipgap[1]+chipsize[1])*0.27/60),   
            '6':(2.0*(chipgap[0]+chipsize[0])*0.27/60, 0.5*(chipgap[1]+chipsize[1])*0.27/60),   
            '7':(3.0*(chipgap[0]+chipsize[0])*0.27/60, 0.5*(chipgap[1]+chipsize[1])*0.27/60),

            '8':(-2.5*(chipgap[0]+chipsize[0])*0.27/60,  1.5*(chipgap[1]+chipsize[1])*0.27/60),   
            '9':(-1.5*(chipgap[0]+chipsize[0])*0.27/60,  1.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '10':(-0.5*(chipgap[0]+chipsize[0])*0.27/60,  1.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '11':(0.5*(chipgap[0]+chipsize[0])*0.27/60, 1.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '12':(1.5*(chipgap[0]+chipsize[0])*0.27/60, 1.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '13':(2.5*(chipgap[0]+chipsize[0])*0.27/60, 1.5*(chipgap[1]+chipsize[1])*0.27/60),

            '14':(-2.5*(chipgap[0]+chipsize[0])*0.27/60,  2.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '15':(-1.5*(chipgap[0]+chipsize[0])*0.27/60,  2.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '16':(-0.5*(chipgap[0]+chipsize[0])*0.27/60,  2.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '17':(0.5*(chipgap[0]+chipsize[0])*0.27/60, 2.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '18':(1.5*(chipgap[0]+chipsize[0])*0.27/60, 2.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '19':(2.5*(chipgap[0]+chipsize[0])*0.27/60, 2.5*(chipgap[1]+chipsize[1])*0.27/60),

            '20':(-2.0*(chipgap[0]+chipsize[0])*0.27/60,  3.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '21':(-(chipgap[0]+chipsize[0])*0.27/60,  3.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '22':( 0.0,  3.5*(chipgap[1]+chipsize[1])*0.27/60), 
            '23':((chipgap[0]+chipsize[0])*0.27/60, 3.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '24':(2.0*(chipgap[0]+chipsize[0])*0.27/60, 3.5*(chipgap[1]+chipsize[1])*0.27/60),

            '25':(-1.5*(chipgap[0]+chipsize[0])*0.27/60,  4.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '26':(-0.5*(chipgap[0]+chipsize[0])*0.27/60,  4.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '27':( 0.5*(chipgap[0]+chipsize[0])*0.27/60,  4.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '28':(1.5*(chipgap[0]+chipsize[0])*0.27/60, 4.5*(chipgap[1]+chipsize[1])*0.27/60),

            '29':(-(chipgap[0]+chipsize[0])*0.27/60,  5.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '30':( 0.0,  5.5*(chipgap[1]+chipsize[1])*0.27/60),  
            '31':( (chipgap[0]+chipsize[0])*0.27/60,  5.5*(chipgap[1]+chipsize[1])*0.27/60)
  }
    if(not isinstance(chip,str) or not re.search('^[NS]', chip)): raise ValueError("Wrong value for chip name for DECam");
    ysign=1 if(chip[0]=='S') else -1;
    cid=chip[1]
    return (chippos0[cid][0], ysign*chippos0[cid][1])

SkZp_DB['chipselect'][ 'DECam']={ 
        'pos': (lambda xdict: _DECam_chippos_(xdixt['CHIP'])), 
        'reject': (lambda xdict: True if(xdict['PROCTYPE']=='Resampled') else False), 
        'posang':(lambda xdict: xdict['POSANG'])}


SkZp_DB['_doc_']['obs_set_check']="""For each instrument, a callable to check for correct chip extraction values for several instruments. The callable should accept 2 parameters: list of dict (containing the extraction info), dict of dict (containing the header of HDU=0 of the mosaics)""";

def _VIRCAMVVV_obscheck(inputdata, mosinfo):
    obspS={}; # for each pawprint of OBS NAME, dict of set of chips
    obspL={}; # for each pawprint of OBS NAME, dict of list of members
    tilepS={};  #for each part (OFF of OBS), dict of set of chips
    tilepL={};  #for each part (OFF of OBS), dict of list of members
    for ii,inp in enumerate(inputdata):
#    if(not inp['outname']): continue;
      #get list of EXTNAME in the mosaic
        lstext=fits.listextname(inp['mosaic']); # For chip selection
        nhdu=len(lstext); # For chip selection
        obn  =headerkeyread('OBNAME', SkZp_DB['headerkey']['VIRCAM:VVV']['mos']['OBNAME'],  mosinfo[ inp['mosaic'] ] );
        tilen=headerkeyread('OBJECT', SkZp_DB['headerkey']['VIRCAM:VVV']['mos']['OBJECT'],  mosinfo[ inp['mosaic'] ] );
        offn =headerkeyread('OFFSET', SkZp_DB['headerkey']['VIRCAM:VVV']['mos']['OFFSET'],  mosinfo[ inp['mosaic'] ] );
        obsp ='{} {}'.format(obn. offn);
        tilep='{} {}'.format(tilen. offn);

        obspS.setdefault(obsp, set);
        obspL.setdefault(obsp, []);
        tilepS.setdefault(tilep, set);
        tilepL.setdefault(tilep, []);

        obspS[obsp].update(set(inp['chip']['#']));
        obspL[obsp].append(ii);
        tilepS[tilep].update(set(inp['chip']['#']));
        tilepL[tilep].append(ii);
    for obs in obspS:
        for ii in obspL[obs]:
            if(obspS[obs].issuperset(inputdata[ii]['chip']['#'])): inputdata[ii]['chip']['#']=tuple(obspS[obs]);
    if(_opt.OptionGet('image:uniform')):
        for tile in tilepS:
            for ii in tilepL[tile]:
                if(tilepS[tile].issuperset(inputdata[ii]['chip']['#'])): inputdata[ii]['chip']['#']=tuple(tilepS[tile])
SkZp_DB['obs_set_check'][ 'VIRCAM:VVV' ]=_VIRCAMVVV_obscheck






###################################
## PATTERN NAME
SkZp_DB['_doc_']['namepattern']=""" Definition of pattern to create filename. Pattern is defined by % followed by a character""";
SkZp_DB['namepattern'][ '-'          ]= {'%F':(lambda x : x)};
SkZp_DB['namepattern'][ None         ]= SkZp_DB['namepattern']['-'];
SkZp_DB['namepattern'][ 'VIRCAM'     ]= {'%F':(lambda x : x[3:9]+x[11:15])};
SkZp_DB['namepattern'][ 'VIRCAM:VVV' ]= deepcopy(SkZp_DB['namepattern']['VIRCAM']);

#####################################
## BAD PSF AREA
SkZp_DB['_doc_']['nopsfzone']="""Areas of the sensors not ideal for PSF calculation""";
SkZp_DB['nopsfzone'][ 'VIRCAM'     ]    =(lambda xdict:  '{}_{}_{}.npz'.format(str(xdict['OBJECT']), str(xdict['OFFSET']), str(xdict['CHIP']))  );
SkZp_DB['nopsfzone'][ 'VIRCAM:VVV' ]=SkZp_DB['nopsfzone']['VIRCAM'];

#####################################
## BAD PIXEL AREA

# {'type':'', 'x':, 'y':, 'wx':, 'wy':},
# {'type':'', 'x':, 'y':, 'wx':, 'wy':},  {'type':'', 'x':, 'y':, 'wx':, 'wy':},  {'type':'', 'x':, 'y':, 'wx':, 'wy':},  {'type':'', 'x':, 'y':, 'wx':, 'wy':},  {'type':'', 'x':, 'y':, 'wx':, 'wy':},
SkZp_DB['_doc_']['badpixelarea']="""Areas of the sensors that have surious issues and have to be removed from photometric file because the data inside are not good.
For each chip it is given a dictionary with keys:
    'bad': tuple
        Tuple of areas of bad pixels.
    'sugg' : tuple
        Tuple of areas with data of lesser quality that are suggested to be rejected.
The pixel areas are descrped by dictionary:
    'type' : str
        Type of the area:
          'box' : rettangular area centered on a point;
          'frame' : area along the border of the chip; use just 'wx' and 'wy';
          'ellipse' : elliptic area centered on a point.
    'x' : int or float
        X coordinate of the reference point.
    'y' : int or float
        Y coordinate of the reference point.
    'wx' : int or float
        Characteristic length along X axes
    'wy' : int or float
        Characteristic length along Y axes

""";

SkZp_DB['badpixelarea']['VIRCAM']={'1':{ 'bad':({'type':'box', 'x':1056, 'y':910, 'wx':47, 'wy':40},  {'type':'box', 'x':551, 'y':1042, 'wx':117, 'wy':62},  {'type':'box', 'x':368, 'y':1121, 'wx':57, 'wy':74},
                                               {'type':'box', 'x':483, 'y':1082, 'wx':130, 'wy':80},  {'type':'box', 'x':564, 'y':1017, 'wx':85, 'wy':28}, {'type':'box', 'x':423, 'y':1136, 'wx':69, 'wy':43},
                                               {'type':'box', 'x':472, 'y':1152, 'wx':74, 'wy':54},  {'type':'box', 'x':1019, 'y':858, 'wx':74, 'wy':69},  {'type':'box', 'x':1026, 'y':839, 'wx':53, 'wy':28}),
                                        'sugg':({'type':'frame', 'wx':60, 'wy':60}, ), 
   }};
SkZp_DB['badpixelarea']['VIRCAM:VVV']=deepcopy(SkZp_DB['badpixelarea']['VIRCAM']);




#####################
# GENERIC DATABASE #
#####################
 ###############
 # LIST OF FILTERS 
 # List of standard names of passbands
 ##Standard Passband
SkZp_DB['_doc_']['passbands']="""Translation between filter name of the instruments and standard passband names (Almost a copy of alias:*:FILTER).
Used during standard calibration.
  '_wave_' : the internal database of the central wavelenth [nm] according to The Asiago Database on 
             Photometric Systems (ADPS, http://ulisse.pd.astro.it/Astro/ADPS/).
             Passband with identical name and almost identical central wavelenth are not repeated. 
             Otherwise common alias are used (e.g. 'Rc' for R Cousins).
  None     : the list of the standard passsband names ordered by wavelength using data in '_wave_'."""

SkZp_DB['passbands']['_wave_']={'SDSS':{'u':356, 'g':483, 'r':626, 'i':767, 'z':910},
'JOHNSON':{'U':360, 'B':440, 'V':550, 'R':700, 'I':900, 'J':1250, 'H':1620, 'K':2200, 'L':3400, 'M':5000, 'N':10000},
'COUSINS':{'Rc':647, 'Ic':787},
'BESSEL':{'Rb':643, 'Ib':806},
'STROMGREN':{'v':411, 'b':467, 'y':547}, 
'2MASS/UKIRT/UH2.2':{ 'Ks':2160, 'Z':882, 'Y':1031, 'Kp':2110,}, 
'WASHINGTON':{'C':391, 'Mw':509, 'T1':633, 'T2':789}, 
}

def PassbandDB():
    print("NAME  FILTER  L_EFF\n-------------------")
    for name,filters in SkZp_DB['passbands']['_wave_'].items():
        print(name)
        for flt,leff in filters.items():
            print("\t{fltr:5} {l_eff:5d}".format(fltr=flt, l_eff=leff))
        print()
####
_tmpd_=dict(ChainMap(*SkZp_DB['passbands']['_wave_'].values()));
SkZp_DB['passbands'][None]=sorted(_tmpd_, key=_tmpd_.get);


 ##############################
 # LIST OF STANDARD FIELDS
 ##############################
SkZp_DB['standardfield']={
'bdm12d134': ( 11.769333, -11.876556),

'pg0122': ( 21.356083, 20.2845),
'pg0231': ( 38.357708, 5.279472),
'pg0918': ( 140.364792, 2.744611),
'pg0942': ( 146.267125, -3.063444),
'pg1047': ( 162.561125, -0.007361),
'pg1323': ( 201.465292, -8.873194),
'pg1525': ( 232.104083, -7.25275),
'pg1528': ( 232.703667, 6.004139),
'pg1633': ( 248.792, 9.770694),
'pg1657': ( 254.903208, 7.720833),
'pg2213': ( 334.067833, -0.332944),
'pg2331': ( 353.429042, 5.773861),
'pg2336': ( 354.675875, 0.694417),

'g162_66': ( 158.425792, -11.697417),
'g163_50': ( 167.031, -5.182139),
'g44_40': ( 162.740625, 6.822472),
'g93_48': ( 328.096625, 2.390944),
'gd246': ( 348.074583, 10.789778),
'gd71': ( 88.095708, 15.883722),

'ru149': ( 111.055292, -0.5265),
'ru152': ( 112.414792, -2.107778),

'sa92': ( 13.769208, 0.790389),
'sa93': ( 28.550292, 0.768306),
'sa94': ( 43.981417, 0.726111),
'sa95': ( 58.48125, 0.16825),
'sa96': ( 73.201208, 0.020472),
'sa97': ( 89.485583, 0.098333),
'sa98': ( 102.985208, -0.302028),
'sa99': ( 118.718792, -0.563889),
'sa100': ( 133.259917, -0.679139),
'sa101': ( 149.100292, -0.297639),
'sa102': ( 164.00175, -0.821722),
'sa103': ( 178.895125, -0.804361),
'sa104': ( 190.580583, -0.576889),
'sa105': ( 204.515, -0.663333),
'sa106': ( 220.154958, -0.239694),
'sa107': ( 234.8675, -0.226861),
'sa108': ( 249.435875, -0.500694),
'sa109': ( 266.178292, -0.2415),
'sa110': ( 280.58875, 0.268583),
'sa111': ( 294.36675, 0.429056),
'sa112': ( 310.506458, 0.255333),
'sa113': ( 325.388292, 0.603472),
'sa114': ( 340.472792, 0.825861),

't_phe': ( 7.51675, -46.535389),
}

SkZp_DB['objfield']={
        #Harris catalog
#        id0          RAd          DECd
'ngc104': (6.023625,   -72.081278),
'ngc288': (13.188500,   -26.582611),
'ngc362': (15.809417,   -70.848778),
'whiting1': (30.737500,    -3.252778),
'ngc1261': (48.067542,   -55.216222),
'pal1': (53.333500,    79.581056),
'am1': (58.759583,   -49.615278),
'eridanus': (66.185417,   -21.186944),
'pal2': (71.524625,    31.381500),
'ngc1851': (78.528167,   -40.046556),
#        id0          RAd          DECd
'ngc1904': (81.046208,   -24.524722),
'ngc2298': (102.247542,   -36.005306),
'ngc2419': (114.535292,    38.882444),
'ko2': (119.570833,    26.255000),
'pyxis': (136.990833,   -37.221389),
'ngc2808': (138.012917,   -64.863500),
'e3': (140.237792,   -77.281889),
'pal3': (151.382917,     0.071667),
'ngc3201': (154.403417,   -46.412472),
'pal4': (172.320000,    28.973583),
#        id0          RAd          DECd
'ko1': (179.827083,    12.260000),
'ngc4147': (182.526250,    18.542639),
'ngc4372': (186.439167,   -72.659000),
'rup106': (189.667500,   -51.150278),
'ngc4590': (189.866583,   -26.744056),
'ngc4833': (194.891333,   -70.876500),
'ngc5024': (198.230208,    18.168167),
'ngc5053': (199.112875,    17.700250),
'ngc5139': (201.696833,   -47.479583),
'ngc5272': (205.548417,    28.377278),
#        id0          RAd          DECd
'ngc5286': (206.611708,   -51.374250),
'am4': (209.090417,   -27.167500),
'ngc5466': (211.363708,    28.534444),
'ngc5634': (217.405125,    -5.976417),
'ngc5694': (219.901208,   -26.538944),
'ic4499': (225.076875,   -82.213694),
'ngc5824': (225.994292,   -33.068222),
'pal5': (229.021875,    -0.111611),
'ngc5897': (229.352083,   -21.010278),
'ngc5904': (229.638417,     2.081028),



'ngc5927': (232.002875,   -50.673028),
'ngc5946': (233.868833,   -50.659667),
'bh176': (234.781042,   -50.052722),
'ngc5986': (236.512500,   -37.786417),
'lynga7': (242.765208,   -55.317778),
'pal14': (242.752500,    14.957778),
'ngc6093': (244.260042,   -22.976083),
'ngc6121': (245.896750,   -26.525750),
'ngc6101': (246.450500,   -72.202194),
'ngc6144': (246.807750,   -26.023500),
#        id0          RAd          DECd
'ngc6139': (246.918208,   -38.848750),
'terzan3': (247.167000,   -35.353472),
'ngc6171': (248.132750,   -13.053778),
'1636-283': (249.856042,   -28.398694),
'ngc6205': (250.421833,    36.459861),
'ngc6229': (251.744958,    47.527750),
'ngc6218': (251.809083,    -1.948528),
'fsr1735': (253.044167,   -47.058056),
'ngc6235': (253.355458,   -22.177444),
'ngc6254': (254.287708,    -4.100306),
#        id0          RAd          DECd
'ngc6256': (254.885917,   -37.121389),
'pal15': (254.962500,    -0.538889),
'ngc6266': (255.303333,   -30.113722),
'ngc6273': (255.657500,   -26.267972),
'ngc6284': (256.118792,   -24.764861),
'ngc6287': (256.288042,   -22.708361),
'ngc6293': (257.542500,   -26.582083),
'ngc6304': (258.634375,   -29.462028),
'ngc6316': (259.155417,   -28.140111),
'ngc6341': (259.280792,    43.135944),
#        id0          RAd          DECd
'ngc6325': (259.496708,   -23.766000),
'ngc6333': (259.796917,   -18.515944),
'ngc6342': (260.292000,   -19.587417),
'ngc6356': (260.895542,   -17.813028),
'ngc6355': (260.994125,   -26.353417),
'ngc6352': (261.371292,   -48.422167),
'ic1257': (261.785417,    -7.093056),
'terzan2': (261.887917,   -30.802333),
'ngc6366': (261.934333,    -5.079861),
'terzan4': (262.662500,   -31.595528),
#        id0          RAd          DECd
'hp1': (262.771667,   -29.981667),
'ngc6362': (262.979125,   -67.048333),
'liller1': (263.352083,   -33.389000),
'ngc6380': (263.616667,   -39.069167),
'terzan1': (263.949167,   -30.469722),
'ton2': (264.043750,   -38.553333),
'ngc6388': (264.071792,   -44.735500),
'ngc6402': (264.400417,    -3.245917),
'ngc6401': (264.652500,   -23.909500),
'ngc6397': (265.175375,   -53.674333),
#        id0          RAd          DECd
'pal6': (265.925833,   -26.222500),
'ngc6426': (266.227708,     3.170139),
'djorg1': (266.867917,   -33.065556),
'terzan5': (267.020000,   -24.779167),
'ngc6440': (267.219583,   -20.360250),
'ngc6441': (267.554417,   -37.051444),
'terzan6': (267.693250,   -31.275389),
'ngc6453': (267.715417,   -34.599167),
'uks1': (268.613333,   -24.145278),
'ngc6496': (269.765333,   -44.265944),
#        id0          RAd          DECd
'terzan9': (270.411667,   -26.839722),
'djorg2': (270.454583,   -27.825833),
'ngc6517': (270.460500,    -8.958778),
'terzan10': (270.901667,   -26.072500),
'ngc6522': (270.891750,   -30.033972),
'ngc6535': (270.960458,    -0.297639),
'ngc6528': (271.206833,   -30.056278),
'ngc6539': (271.207000,    -7.585861),
'ngc6540': (271.535833,   -27.765278),
'ngc6544': (271.835750,   -24.997333),
#        id0          RAd          DECd
'ngc6541': (272.009833,   -43.714889),
'2ms-gc01': (272.090875,   -19.829722),
'eso-sc06': (272.275000,   -46.423056),
'ngc6553': (272.323333,   -25.908694),
'2ms-gc02': (272.402083,   -20.778889),
'ngc6558': (272.573333,   -31.763889),
'ic1276': (272.684167,    -7.207611),
'terzan12': (273.065833,   -22.741944),
'ngc6569': (273.411667,   -31.826889),
'bh261': (273.527500,   -28.635000),
#        id0          RAd          DECd
'glimpse02': (274.627083,   -16.977222),
'ngc6584': (274.656667,   -52.215778),
'ngc6624': (275.918792,   -30.361028),
'ngc6626': (276.136708,   -24.869778),
'ngc6638': (277.733750,   -25.497472),
'ngc6637': (277.846250,   -32.348083),
'ngc6642': (277.975417,   -23.475194),
'ngc6652': (278.940125,   -32.990722),
'ngc6656': (279.099750,   -23.904750),
'pal8': (280.374583,   -19.825833),
#        id0          RAd          DECd
'ngc6681': (280.803167,   -32.292111),
'glimpse01': (282.207083,    -1.497222),
'ngc6712': (283.267917,    -8.706111),
'ngc6715': (283.763875,   -30.479861),
'ngc6717': (283.775167,   -22.701472),
'ngc6723': (284.888125,   -36.632250),
'ngc6749': (286.313750,     1.900833),
'ngc6752': (287.717125,   -59.984556),
'ngc6760': (287.800042,     1.030472),
'ngc6779': (289.148208,    30.183472),
#        id0          RAd          DECd
'terzan7': (289.433000,   -34.657722),
'pal10': (289.508750,    18.571667),
'arp2': (292.183792,   -30.355639),
'ngc6809': (294.998792,   -30.964750),
'terzan8': (295.435042,   -33.999472),
'pal11': (296.310000,    -8.007222),
'ngc6838': (298.443708,    18.779194),
'ngc6864': (301.519542,   -21.921167),
'ngc6934': (308.547375,     7.404472),
'ngc6981': (313.365417,   -12.537306),
#        id0          RAd          DECd
'ngc7006': (315.372417,    16.187333),
'ngc7078': (322.493042,    12.167000),
'ngc7089': (323.362583,    -0.823250),
'ngc7099': (325.092167,   -23.179861),
'pal12': (326.661833,   -21.252611),
'pal13': (346.685167,    12.772000),
'ngc7492': (347.110958,   -15.611500),
#       name20          RAd          DECd
'47tuc': (6.023625,   -72.081278),
'e1': (58.759583,   -49.615278),
#       name20          RAd          DECd
'm79': (81.046208,   -24.524722),
#       name20          RAd          DECd
'm68': (189.866583,   -26.744056),
'm53': (198.230208,    18.168167),
'omegacen': (201.696833,   -47.479583),
'm3': (205.548417,    28.377278),
#       name20          RAd          DECd
'm5': (229.638417,     2.081028),
#       name20          RAd          DECd
'bh184': (242.765208,   -55.317778),
'avdb': (242.752500,    14.957778),
'm80': (244.260042,   -22.976083),
'm4': (245.896750,   -26.525750),
#       name20          RAd          DECd
'm107': (248.132750,   -13.053778),
'eso452-sc11': (249.856042,   -28.398694),
'm13': (250.421833,    36.459861),
'm12': (251.809083,    -1.948528),
'm10': (254.287708,    -4.100306),
#       name20          RAd          DECd
'm62': (255.303333,   -30.113722),
'm19': (255.657500,   -26.267972),
'm92': (259.280792,    43.135944),
#       name20          RAd          DECd
'm9': (259.796917,   -18.515944),
'hp3': (261.887917,   -30.802333),
'hp4': (262.662500,   -31.595528),
#       name20          RAd          DECd
'bh229': (262.771667,   -29.981667),
'ton1': (263.616667,   -39.069167),
'hp2': (263.949167,   -30.469722),
'pismis26': (264.043750,   -38.553333),
'm14': (264.400417,    -3.245917),
#       name20          RAd          DECd
'terzan11': (267.020000,   -24.779167),
'hp5': (267.693250,   -31.275389),
#       name20          RAd          DECd
'eso456-sc38': (270.454583,   -27.825833),
'djorg3': (271.535833,   -27.765278),
#       name20          RAd          DECd
'2mass-gc01': (272.090875,   -19.829722),
'eso280-sc06': (272.275000,   -46.423056),
'2mass-gc02': (272.402083,   -20.778889),
'pal7': (272.684167,    -7.207611),
'al3': (273.527500,   -28.635000),
#       name20          RAd          DECd
'm28': (276.136708,   -24.869778),
'm69': (277.846250,   -32.348083),
'm22': (279.099750,   -23.904750),
#       name20          RAd          DECd
'm70': (280.803167,   -32.292111),
'm54': (283.763875,   -30.479861),
'pal9': (283.775167,   -22.701472),
'm56': (289.148208,    30.183472),
#       name20          RAd          DECd
'm55': (294.998792,   -30.964750),
'm71': (298.443708,    18.779194),
'm75': (301.519542,   -21.921167),
'm72': (313.365417,   -12.537306),
#       name20          RAd          DECd
'm15': (322.493042,    12.167000),
'm2': (323.362583,    -0.823250),
'm30': (325.092167,   -23.179861),


'133p': ( 299.390625, -19.147472),
'67p': ( 264.883833, -29.203167),
'ab_lep': ( 88.802875, -22.896889),
'ascc105': ( 295.42575, 27.378361),
'ascc109': ( 298.458208, 34.575528),
'ascc111': ( 302.784375, 37.454611),
'axaf': ( 52.929375, -27.744833),
'abell35': ( 193.408292, -22.868861),
'andi': ( 11.284667, 38.030917),
'andii': ( 19.005625, 33.408278),
'andiii': ( 8.770708, 36.485222),
'andix': ( 13.082625, 43.187333),
'andv': ( 17.421583, 47.616944),
'andvi': ( 357.832458, 24.575111),
'andvii': ( 351.469375, 50.666667),
'andx': ( 16.498292, 44.798583),
'andxi': ( 11.462917, 33.791722),
'andxii': ( 11.739792, 34.367611),
'andxiii': ( 12.843417, 32.998306),
'andxiv': ( 12.780917, 29.689972),
'andxix': ( 4.763917, 35.033833),
'andxv': ( 18.448542, 38.108611),
'andxvi': ( 14.758333, 32.364472),
'andxviii': ( 0.426042, 45.084389),
'andxx': ( 1.758833, 35.123222),
'andxxi': ( 358.563625, 42.461),
'anonymous10': ( 170.590792, -21.692278),
'anonymous11': ( 171.200667, -21.692139),
'aquarius': ( 311.6165, -12.864333),
'arp2': ( 292.20425, -30.342417),
'bh176': ( 234.825542, -50.035194),
'bllac': ( 330.671667, 42.283917),
'br1202m0725': ( 181.36025, -7.717944),
'barnard59': ( 257.936833, -27.371889),
'be17': ( 80.148, 30.505417),
'be18': ( 80.552167, 45.453167),
'be20': ( 83.095958, 0.198),
'be21': ( 87.948208, 21.8365),
'be29': ( 103.219833, 16.910833),
'be54': ( 315.668375, 40.465694),
'be66': ( 45.877417, 58.761861),
'be99': ( 350.099417, 71.754056),
'booi': ( 209.92875, 14.512611),
'booii': ( 209.383542, 12.813417),
'booiii': ( 209.17425, 26.796056),
'cvni': ( 201.933542, 33.562694),
'carina': ( 100.419042, -51.043444),
'carina_c': ( 100.469208, -51.023806),
'carina_e': ( 102.224542, -50.068278),
'carina_s': ( 100.418917, -51.985944),
'comaber': ( 186.629708, 23.895694),
'cr261': ( 189.590792, -68.373444),
'cr359': ( 270.145125, 2.941028),
'crater2': ( 177.198625, -18.413667),
'draco': ( 260.145708, 57.851194),
'e1': ( 20.893625, -44.548694),
'e2': ( 60.765417, -44.633444),
'e3': ( 100.729583, -45.202333),
'e3cluster': ( 140.129542, -77.21575),
'e4': ( 140.906333, -45.481028),
'e4_108': ( 139.652167, -45.498417),
'e5': ( 181.313292, -45.6715),
'e6': ( 221.719, -45.372806),
'e7': ( 261.749125, -44.943417),
'e9': ( 341.299792, -44.511306),
'eso383': ( 202.877375, -35.070278),
'eridanus': ( 66.185458, -21.196611),
'fornax': ( 39.993, -34.452194),
'globule': ( 187.934208, -63.646861),
'hd140283': ( 235.753625, -10.937722),
'hd32533': ( 74.746333, -66.201361),
'hp1': ( 262.775333, -29.984194),
'hercules': ( 247.711875, 12.792417),
'hydra': ( 159.994708, -27.367139),
'jl163': ( 2.67125, -50.225389),
'king2': ( 12.5545, 58.180333),
'lb1735': ( 67.925375, -53.611806),
'lgs3': ( 15.873917, 21.884111),
'lmc0': ( 78.323542, -61.978639),
'lmc1': ( 78.335792, -63.564194),
'lmc3': ( 78.010458, -66.733778),
'lmc4': ( 76.819917, -68.974083),
'lse259': ( 253.487375, -56.009694),
'lse44': ( 208.199708, -48.147417),
'lss982': ( 122.634875, -40.516389),
'leoa': ( 149.739542, 30.739444),
'leoi': ( 152.068208, 12.392917),
'leoii': ( 168.295083, 22.152333),
'leoiv': ( 173.230208, -0.355472),
'lynga7': ( 242.777292, -55.369361),
'm31': ( 11.060458, 41.639444),
'm31halo': ( 11.519625, 40.7575),
'mct0401': ( 60.746625, -40.185056),
'mct0550': ( 87.860583, -49.113444),
'mct2019': ( 305.713708, -43.494306),
'marka': ( 310.915083, -10.772667),
'messier16': ( 274.652958, -13.788778),
'orion': ( 83.7665, -5.586028),
'pegiii': ( 335.997583, 5.435306),
'pegasus': ( 352.048958, 14.740528),
'pipe': ( 259.621083, -26.827694),
'pyxis': ( 136.996667, -37.216417),
're1816': ( 274.064667, 54.1515),
'reticulum': ( 69.034917, -58.860111),
'sag2a': ( 278.994875, -30.819861),
'sagittarius': ( 292.397042, -17.678972),
'sculptor': ( 14.9525, -33.676),
'segue2': ( 34.707083, 20.166361),
'segue3': ( 320.2715, 19.111139),
'sextans': ( 153.076708, -1.531667),
'sextansa': ( 152.758958, -4.695111),
'sextansb': ( 149.903833, 5.316833),
'sp1': ( 237.922667, -51.512361),
'ton2': ( 264.041667, -38.554861),
'tr14': ( 161.130417, -59.590139),
'tr24': ( 254.145458, -40.571639),
'tr5': ( 99.024833, 9.4435),
'triii': ( 33.196583, 36.181111),
'ugc10743': ( 257.795708, 7.880389),
'umaii': ( 132.660042, 63.125722),
'ursaminor': ( 226.739375, 67.197139),
'vwpyx': ( 134.448542, -28.964194),
'wd0830': ( 127.927583, -53.65175),
'wd1056': ( 164.539583, -38.748917),
'wlm': ( 0.462667, -15.451917),
'cl0302': ( 45.574, -4.381917),
'146p': ( 232.437542, -29.247056),
'be39': ( 116.5195, -4.680944),
'cfdf7': ( 334.28225, 0.338111),
'ltt2415': ( 89.114542, -27.859944),
'umai': ( 158.621458, 51.920389),
}
 


##Alias
SkZp_DB['_doc_']['alias']="""List of alias for header data instruments. Filters, chips, etc can have not standard name in the headers.
For the list of standard names see passbands:None""";
SkZp_DB['alias']['IMACS_Short-Camera'] ={'FILTER':{'Bessell_B2':'B', 'Bessell_V2':'V', 'Bessell_R2':'R', 'CTIO-I2':'I'} };
SkZp_DB['alias']['IMACS_Long-Camera']  ={'FILTER':{'Bessell_B1':'B', 'Bessell_V1':'V', 'Bessell_R1':'R', 'CTIO-I1':'I'} };
SkZp_DB['alias']['GSAOI']              ={'FILTER':{'Z_G1101':'Z', 'J_G1102':'J', 'H_G1103':'H', 'Kshort_G1105':'Ks', 'Kprime_G1104':'Kp', 'K_G1106':'K', 'BrG_G1122':'BrG', 'H2(1-0)_G1121':'H2_10', 'FeII_G1118':'FeII', 'Kcntshrt_G1111':'Kcs', 'CH4short_G1109':'CH4s'}, 
                                           'CHIP':{'GSAOI_Frame1':'1', 'GSAOI_Frame2':'2', 'GSAOI_Frame3':'3', 'GSAOI_Frame4':'4'} };
  #BAADE
SkZp_DB['passbands']['IMACS_Short-Camera']={'Bessell_B2':'B', 'Bessell_V2':'V', 'Bessell_R2':'R', 'CTIO-I2':'I'};
SkZp_DB['passbands']['IMACS_Long-Camera'] ={'Bessell_B1':'B', 'Bessell_V1':'V', 'Bessell_R1':'R', 'CTIO-I1':'I'};

#This create a reverse copy of the alias
#for instr in SkZp_DB['alias']:
#  for atype in SkZp_DB['alias'][instr]:
#    tmpd={};
#    for key,value in SkZp_DB['alias'][instr][atype].items():
#      tmpd[value]=key;
#    SkZp_DB['alias'][instr][atype].update(tmpd);

##########################
## GAINRONHIGH
  #IMACS_Short-Camera
SkZp_DB['gainronhigh']['IMACS_Short-Camera']={'HIGH':{'1':40000,   '2':56000,   '3':56000,   '4':39000, '5':57000, '6':44000, '7':40000, '8':57000},}


  #Swope Direct/4Kx4K-4
SkZp_DB['gainronhigh']['Direct/4Kx4K-4']={'HIGH':{'1':60000,   '2':60000,   '3':60000,   '4':60000},}

  #GSAOI
SkZp_DB['gainronhigh']['GSAOI']={'GAIN':{'1':2.434,   '2':2.010,   '3':2.411,   '4':2.644},
                                  #RON depends on the readout mode => Number of Non-destructive reads (tag:FOWLER)
                                  'RON':{'1':{2:26.53, 8:13.63, 16:10.22},
                                         '2':{2:19.10, 8: 9.85, 16: 7.44},
                                         '3':{2:27.24, 8:14.22, 16:10.61},
                                         '4':{2:32.26, 8:16.78, 16:12.79} },
                                 'HIGH':{'1':SkZp_Par['photo:hgdcorrection']*52400, '2':SkZp_Par['photo:hgdcorrection']*50250, '3':SkZp_Par['photo:hgdcorrection']*53700, '4':SkZp_Par['photo:hgdcorrection']*52300 }   };

  #VIRCAM
SkZp_DB['gainronhigh']['VIRCAM']={'GAIN':{'1':3.7,  '2':4.2,  '3':4.0,  '4':4.2,   '5':4.2,  '6':4.1,  '7':3.9,  '8':4.2,
                                          '9':4.6, '10':4.0, '11':4.6, '12':4.0,  '13':5.8, '14':4.8, '15':4.0, '16':5.0},
                                  'RON':{'1':23.9,  '2':24.4,  '3':22.8,  '4':24.0,   '5':24.4,  '6':23.6,  '7':23.1,  '8':24.3,
                                         '9':19.0, '10':24.9, '11':24.1, '12':23.8,  '13':26.6, '14':18.7, '15':17.7, '16':20.8},
                                 'HIGH':{'1': 32000 ,  '2': 32000 ,  '3': 32000 ,  '4': 32000 ,  '5': 32000 ,  '6': 32000 ,  '7': 32000 ,  '8': 32000 ,
                                         '9': 32000 , '10': 32000 , '11': 32000 , '12': 32000 , '13': 32000 , '14': 32000 , '15': 32000 , '16': 32000 }  };
  #VIRCAM:VVV
SkZp_DB['gainronhigh']['VIRCAM:VVV']=deepcopy(SkZp_DB['gainronhigh']['VIRCAM']);
SkZp_DB['gainronhigh']['VIRCAM:VVV'].update({'HIGH':{'1':19000.0,  '2':30800.0,  '3':29500.0,  '4':23000.0,  '5':16000.0,  '6':16000.0,  '7':18800.0,  '8':25000.0,
                                         '9':25000.0, '10':20000.0, '11':23000.0, '12':20000.0, '13':35000.0, '14':23000.0, '15':20000.0, '16':28000.0},
                                  'HIGHCORR':{'b':{'J'+'j':1.0600, 'H'+'j':1.0420, 'Ks'+'j':1.0000,  'Y'+'z':1.4160, 'Z'+'z':1.3770,  'Ks'+'v':1.0000},
                                              'd':{'J'+'j':1.2760, 'H'+'j':1.2940, 'Ks'+'j':1.3000,  'Y'+'z':1.5610, 'Z'+'z':1.5070,  'Ks'+'v':1.0000},
                                              'e':{'J'+'h':1.2760, 'H'+'h':1.1000, 'Ks'+'h':1.0000,  'J'+'j':1.2760,  'Ks'+'v':1.0000},} });
def VVV_HGD(dataframe=None):
  return SkZp_Par['photo:hgdcorrection'] * (SkZp_DB['gainronhigh']['VIRCAM:VVV']['HIGH'][str(dataframe['CHIP'])] * SkZp_DB['gainronhigh']['VIRCAM:VVV']['HIGHCORR'][ dataframe['OBTYPE'][0] ][ dataframe['FILTER']+dataframe['OBTYPE'][1] ]-dataframe['SKY']) +dataframe['SKY'];



#############
## SKZ_OPT ##
#############
SkZp_DB['_doc_']['SkZp_Opt']="""Options for specific instrument or use.""";
SkZp_DB['SkZp_Opt']['GSAOI']={'photo:DAO:psfdef':'MOFFAT35', 'photo:DAO:psfother':['MOFFAT25', 'PENNY1', 'MOFFAT15', 'PENNY2', 'GAUSSIAN'], 'photo:DAO:psfothergood':2,
                           'photo:psf:starinit':500, 'photo:psf:starmax':400, 'photo:psf:starmin':100,
                           'photo:psf:psfradius':25, 'photo:in-outskyradius':11, 'photo:psf-inskyradius':3,
                           'photo:thre:psfcal':3, 'photo:thre:srclst':4, 'photo:DAO:varpsf':[-1,1,2,3], 'photo:DAO:allstarinput':'nei',
                           'photo:Steps:psfcal':["Ground", "AddFph", "AddFph", "AddFph", "Refine"], 'photo:Steps:srclst':["Ground", "AddFph", "AddFph", "AddFph", "Refine"],
                           'stack:match:makemode':['dao:|p20:/'],
                           };

SkZp_DB['SkZp_Opt']['VIRCAM:VVV']={'optfiles':['VVV-SkZpipe.opt', 'VSpipe.opt'], 'inputdata:file':'VVV_imgdata', 
                           'photo:DAO:psfdef':'MOFFAT35', 'photo:DAO:psfother':['MOFFAT25', 'PENNY1', 'PENNY2', 'GAUSSIAN', 'ALLPSF'], 'photo:DAO:psfothergood':1,
                           'photo:psf:starinit':400, 'photo:psf:starmax':250, 'photo:psf:starmin':50,
                           'photo:psf:psfradius':8, 'photo:in-outskyradius':11, 'photo:psf-inskyradius':3,
                           'photo:averagedsummed':'2,1', 'photo:thre:psfcal':3, 'photo:thre:srclst':4, 'photo:DAO:allstarinput':'nei', 'photo:DAO:varpsf':[-1,0,1,2],
                           'photo:Steps:psfcal':["Ground", "AddCoo", "AddFph", "ChkAdd", "Refine"], 'photo:Steps:srclst':["Ground", "AddFph", "AddFph", "Refine"],
                           'stack:bytag':'FOV', 'stack:substacktag':'OBTYPE', 'stack:match:srcext':'.als', 'stack:match:makemode':['wcs'], 'stack:match:improveposwith':'allframe', 'stack:match:improveposmode':-1, 'stack:par:minfrm':1, 'stack:par:percentile':.5, 
                           'photo:allframe:niter':175,
                           };




######################
## FIELD STRUCTURE ###
######################
## ORIENTATION ###
SkZp_DB['_doc_']['pointing']="""Information about the pointing and the field of view of the instrument."""
SkZp_DB['_doc_']['pointing:orientation']="""Dictionary with information about the orientation of the field of view of the instrument.
    'fixfov' : int
        Integer flag about if the the field of view has a fixed pointing or not:
            1 : Perfectly fixed respect ra,dec (the position angle and flipping is the same; typical of instruments of telescopes on equatorial mount).
            0 : It can rotate freely, even during an observation run (e.g. Hubble).
           -1 : It can rotate, but usually during a run X,Y keep the same position angle respect ra,dec (typical of instruments of telescopes on altazimuthal mount).
    'axdirection' : tuple of int
        Integer flag if the sensor axes (x,y) are parallel (+1) or antiparallel (-1) to the celestial tangential axes. Instruments with direct view of the sky have (1,1) (i.e. having declination increasing upwards and right ascension leftwards is (1,1), while if x,y are parallel to ra,dec is (-1,1) )
    """;
SkZp_DB['_doc_']['pointing:accuracy']="""Tuple with probable error in pointing (arcsec, pixel)."""

SkZp_DB['pointing']={'GSAOI':{'orientation':{'fixfov':-1, },'accuracy':(1, 50),},
                     'IMACS_Short-Camera':{'orientation':{'fixfov':-1, },'accuracy':(1, 50),},
                     'IMACS_Long-Camera':{'orientation':{'fixfov':-1, },'accuracy':(1, 50),},
                     'Direct/4Kx4K-4':{'orientation':{'fixfov':1, 'axdirection':(1,1)},'accuracy':(1, 50),},
                     'VIRCAM':{'orientation':{'fixfov':-1, },'accuracy':(1, 50),}, 'VIRCAM:VVV':{'orientation':{'fixfov':-1, },'accuracy':(1, 50),},
                     'DECam':{'orientation':{'fixfov':1, },'accuracy':(1, 50),}, 'Tucan':{'orientation':{'fixfov':1, },'accuracy':(1, 50),}
};

## DISTORSION ###
SkZp_DB['_doc_']['mosoffset']="""Linear trasformation for chips of a mosaic between their XY system and Tangential system. '0' is for the name of the chip selected as reference.
The structure is {0:(pan), 'X':(X_shift, *X, *Y, *X^2, *X*Y, *Y^2, ...), 'Y':(Y_shift, *X, *Y, *X^2, *X*Y, *Y^2, ...) }""";
SkZp_DB['mosoffset']={} 
SkZp_DB['mosoffset']['GSAOI']={'1':(   +1.0, -2186.0,  +0.9717, -0.0013, +0.0054, +0.9976), 
                               '2':(-2206.0, -2186.0,  +1.0015, -0.0004, +0.0070, +0.9987), 
                               '3':(-2185.0,    -1.0,  +0.9987, +0.0016, -0.0295, +0.9966),
                               '4':(   +0.0,    +0.0,  +1.0000, +0.0000, +0.0000, +1.0000),
                               '0':'4'}

SkZp_DB['MOSdistortion']={}
SkZp_DB['MOSdistortion']['GSAOI']={'XY2TAN':{'1':{0:(    0, -2040), 'X':(+109.80, +1.012301, -0.005240,  -6.4630e-6, -0.7839e-6, -6.4819e-6), 'Y':(-54.55, +0.0088626, +0.9986750)}, 
                                             '2':{0:(-2040, -2040), 'X':( -53.19, +1.014186, -0.006859,  -6.9459e-6, -0.6716e-6, -6.8029e-6), 'Y':(-55.14, +0.0093159, +0.9990231)}, 
                                             '3':{0:(-2040,     0), 'X':( -53.25, +1.015191, -0.011735,  -6.7015e-6, -0.6234e-6, -6.0440e-6), 'Y':(+97.25, +0.0122772, +0.9980012)}, 
                                             '4':{0:(    0,     0), 'X':( +97.34, +1.013634, -0.007376,  -6.7308e-6, -0.3860e-6, -6.2116e-6), 'Y':(+96.95, +0.0080727, +0.9978631)}} }

SkZp_DB['MOSdistortion']['IMACSshort']={'XY2TAN':{'1':{0:(    0, -2040), 'X':(+109.80, +1.012301, -0.005240,  -6.4630e-6, -0.7839e-6, -6.4819e-6), 'Y':(-54.55, +0.0088626, +0.9986750)}, 
                                                  '2':{0:(-2040, -2040), 'X':( -53.19, +1.014186, -0.006859,  -6.9459e-6, -0.6716e-6, -6.8029e-6), 'Y':(-55.14, +0.0093159, +0.9990231)}, 
                                                  '3':{0:(-2040,     0), 'X':( -53.25, +1.015191, -0.011735,  -6.7015e-6, -0.6234e-6, -6.0440e-6), 'Y':(+97.25, +0.0122772, +0.9980012)}, 
                                                  '4':{0:(-2040,     0), 'X':( -53.25, +1.015191, -0.011735,  -6.7015e-6, -0.6234e-6, -6.0440e-6), 'Y':(+97.25, +0.0122772, +0.9980012)}, 
                                                  '5':{0:(-2040,     0), 'X':( -53.25, +1.015191, -0.011735,  -6.7015e-6, -0.6234e-6, -6.0440e-6), 'Y':(+97.25, +0.0122772, +0.9980012)}, 
                                                  '6':{0:(-2040,     0), 'X':( -53.25, +1.015191, -0.011735,  -6.7015e-6, -0.6234e-6, -6.0440e-6), 'Y':(+97.25, +0.0122772, +0.9980012)}, 
                                                  '7':{0:(-2040,     0), 'X':( -53.25, +1.015191, -0.011735,  -6.7015e-6, -0.6234e-6, -6.0440e-6), 'Y':(+97.25, +0.0122772, +0.9980012)}, 
                                                  '8':{0:(    0,     0), 'X':( +97.34, +1.013634, -0.007376,  -6.7308e-6, -0.3860e-6, -6.2116e-6), 'Y':(+96.95, +0.0080727, +0.9978631)}} }

SkZp_DB['MOSdistortion']['Direct/4Kx4K-4']={'TAN2XY':{'1':{0:(    0,     0), 'X':(    0.00,  +2.298851, +0.000000,  -0.0000e-6, -0.0000e-6, -0.0000e-6), 'Y':(    0.00,  +0.000000, +2.298851)}, 
                                                      '2':{0:(    0,     0), 'X':(    0.00,  +2.298851, +0.000000,  -0.0000e-6, -0.0000e-6, -0.0000e-6), 'Y':(    0.00,  +0.000000, +2.298851)}, 
                                                      '3':{0:(    0,     0), 'X':( 1927.39,  +2.299079, +0.020899,  -0.0000e-6, -0.0000e-6, -0.0000e-6), 'Y':( 1838.52,  +0.021282, +2.297132)}, 
                                                      '4':{0:(    0,     1), 'X':(    0.00,  +2.298851, +0.000000,  -0.0000e-6, -0.0000e-6, -0.0000e-6), 'Y':(    0.00,  +0.000000, +2.298851)}} }
















#########
## END ##
#########

#For the double naming of GSAOI chips
for db_ in [SkZp_DB['mosoffset']['GSAOI'], SkZp_DB['MOSdistortion']['GSAOI']['XY2TAN'], SkZp_DB['gainronhigh']['GSAOI']['GAIN'], SkZp_DB['gainronhigh']['GSAOI']['RON'], SkZp_DB['gainronhigh']['GSAOI']['HIGH']]:
    for ii in range(1,5):
        ii=str(ii);
        db_['GSAOI_Frame'+ii]=db_[ii];

SkZp_DBI={'_name_':'SkZp_DBI', '_doc_':{}};
for key in SkZp_DB:
    for instr in SkZp_DB[key]:
        SkZp_DBI.setdefault(instr, set());
        SkZp_DBI[instr].add(key);



