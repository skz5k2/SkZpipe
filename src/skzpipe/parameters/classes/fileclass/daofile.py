import os

from ....exceptions import *

from ... import basicpar as bpar
from ... import daoparameters as daopar
from . import basefile
from .... import functions as funct



###########
##DAO file#
###########

#Header
#daopar.DAO_Par['headerlen']=3;
#daopar.DAO_Par['HeaderTxt']=" NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD\n";
#daopar.DAO_Par['HeaderFormat']={'in':(int, int, int, float, float, float, float, float, float, float), 'out':"{:3d}{:6d}{:6d}{:8.1f}{:8.1f}{:8.3f}{:8.3f}{:8.3f}{:8.3f}{:8.3f}", 'split':(3,6,6,8,8,8,8,8,8,8), '#N':10};

class DAOHeader(basefile.PhotoFileHeader):
    """Object to store the header of photometric outputs of DAOPhot suite.
    """
    length=daopar.DAO_Par['headerlen'];
    pos=(1,);
    
    nl, nx, ny, low, high, thresh, ap1, gain, ron, frad =(1,   0,   0,   0.0,  -1.0, 00.000,  0.000,  0.000,  0.000,  0.000); 
    def __init__(self, indata=None):
      #Initialization generic part (not if 'indata' is string)
        super().__init__(indata=indata, hform={'body':{'len':daopar.DAO_Par['headerlen']}, 'pos':1});   #, **daopar.DAO_Par['HeaderFormat']}); #=>basefile.PhotoFileHeader
        if(not self.dlines):
            self.dlines=("  1     0     0     0.0    -1.0  00.000   0.000   0.000   0.000   0.000", );
      #Initialization with another
        if(isinstance(indata, DAOHeader)):
            self.__dict__.update(indata.__dict__);
        else:
            self.nl, self.nx, self.ny, self.low, self.high, self.thresh, self.ap1, self.gain, self.ron, self.frad = funct.splitconvert(data=self.dlines[0], converters=daopar.DAO_Par['HeaderFormat']['in']) 

    def tuple(self):
        return (self.nl, self.nx, self.ny, self.low, self.high, self.thresh, self.ap1, self.gain, self.ron, self.frad);
    def __repr__(self):
        return daopar.DAO_Par['HeaderFormat']['out'].format(self.nl, self.nx, self.ny, self.low, self.high, self.thresh, self.ap1, self.gain, self.ron, self.frad);
    def __str__(self):
        return repr(self);

    def print(self):
        return daopar.DAO_Par['HeaderTxt']+str(self)+"\n \n";

    def __copy__(self):
        return DAOHeader(self);
    def copy(self):
        return DAOHeader(self);
        
#######################################################

#Files
#daopar.DAO_Par['suffix']={'img':'.fits', 'src':'.coo', 'aph':'.ap', 'psfsrc':'.lst', 'psf':'.psf', 'fph':'.als', 'imgs':'s'};
#daopar.DAO_Par['IdLen']= 7;
#daopar.DAO_Par['IdTxt']= "{:7d}";
#daopar.DAO_Par['DataLen']= 9;
#daopar.DAO_Par['DataPrec']= 3;
#daopar.DAO_Par['ErrPrec']= 4;
#daopar.DAO_Par['DataTxt']= "{{:{:d}.{:d}f}}".format(daopar.DAO_Par['DataLen'],daopar.DAO_Par['DataPrec']);
#daopar.DAO_Par['ErrTxt']= "{{:{:d}.{:d}f}}".format(daopar.DAO_Par['DataLen'],daopar.DAO_Par['ErrPrec']);
#daopar.DAO_Par['DataErrTxt']=daopar.DAO_Par['DataTxt']+daopar.DAO_Par['ErrTxt'];
#daopar.DAO_Par['LineLen']= 300;
#daopar.DAO_Par['ApNum']=12;

class DAOPsfFile(basefile.PsfFile):
    """Object to store the output of the PSF calculation of DAOPhot:psf
    """
    funct='';
    npar=0;
    par=[];
    xhwhm=0;
    yhwhm=0;
    height=0;
    mag=99;
    
    def __init__(self, fname=None, data=None):
        super().__init__(fname=fname, data=data); #=>basefile.PsfFile
        if(data is None):
            if(self.fname and os.path.exists(self.fname)):
                with open(self.fname) as fpsf:
                    data=fpsf.readline()+fpsf.readline();
            self.funct, self.tablesize, self.npar, self.ntable, self.par, self.xhwhm, self.yhwhm,  self.mag, self.height= '', 0, 0, 0, [], 0, 0, 0, 99;
        if(isinstance(data,str)):
            tmpl = data.strip().split('\n');
            self.funct, self.tablesize, self.npar, self.ntable, self.exp, self.mag, self.cheight, self.x, self.y =funct.splitconvert(data=tmpl[0], delimiter=None,  converters=(str, int, int, int, int, float, float, float, float));
            self.par=list(funct.splitconvert(data=tmpl[1], delimiter=(14,13),  converters=(float,float), maxsplit=-1, appendinput=False, delim_repeat=True, conv_repeat=True));
            self.xhwhm, self.yhwhm =self.par[:2];

        elif(isinstance(data,dict)):
            for key in data:
                setattr(self, key, data[key]);
        elif(isinstance(data,tuple)):
            self.funct, self.tablesize, self.npar, self.ntable, self.exp, self.mag, self.cheight, self.x, self.y =data[:9];
            self.par=list(data[9:9+self.npar]);
        elif(isinstance(data,DAOPsfFile)):
            self.__dict__.update(data.__dict__);
        else: raise TypeError('DAOPsfFile'+': Wrong type for data in the initialization <{data}>'.format(data=data));

    def __str__(self):
        txt="{:>9} {:4d} {:4d} {:4d} {:4d} {:8.3f} {:14.3f} {:8.1f} {:8.1f}\n ".format(self.funct, self.tablesize, self.npar, self.ntable, self.exp, self.mag, self.cheight, self.x, self.y);
        for ii in range(self.npar):
            txt+="{:13.6e}".format(self.par[ii]);
        return txt;

    
###############################
#CLASS Declaration
class DAOIdXY(basefile.bclasses.IdXY):
  pass;
class DAOSourceData(basefile.SourceData):
  pass;
class DAOSource(basefile.Source):
  pass;
class DAOSource_als(basefile.Source_fph):
  pass;
class DAOSource_alf(DAOSource_als):
  pass;
class DAOSource_ap(basefile.IdXYml):
  pass;
class DAOSource_apL(DAOSource_ap):
  pass;
class DAOSource_nei(basefile.Source):
  pass;
class DAOSource_coo(basefile.Source):
  pass;

class DAOSource_raw(basefile.Source):
  pass;
class DAOSource_mag(basefile.Source_fph):
  pass;
class DAOPhotoFileFormat(basefile.PhotoFileFormat):  
  """Class to define the format of a photometric file for DAOPhot
""";
  pass;
###############################

"""Database of PhotoFileFormat
  KEYS
     'ftype'      : name of the type

     'form_class' : Class of the format.
     'header_class'  : header class of the format.
     'footer_class'  : header class of the format.
     'src_class'  : class to use to generate the source list.


""";

DAOFileFormatInitD={};
DAOFileFormatInitD[None] ={'ftype':None,  'numl':1,
                           'form_class':DAOPhotoFileFormat, 'header_class':DAOHeader, 'footer_class':None, 'src_class':DAOIdXY, };
DAOFileFormatInitD['']   ={'ftype':'',    'numl':1,
                           'src_class':DAOSourceData, 'header_class':DAOHeader, 'form_class':DAOPhotoFileFormat, 'footer_class':None, };
DAOFileFormatInitD['als']={'ftype':"als", 'numl':1,
                           'src_class':DAOSource_als, 'header_class':DAOHeader, 'form_class':DAOPhotoFileFormat, 'footer_class':None, };
DAOFileFormatInitD['alf']=DAOFileFormatInitD['als'].copy()
DAOFileFormatInitD['alf']['ftype']='alf';
DAOFileFormatInitD['alf']['src_class']=DAOSource_alf;
DAOFileFormatInitD['coo']={'ftype':"coo", 'numl':1,
                           'form_class':DAOPhotoFileFormat, 'header_class':DAOHeader, 'footer_class':None, 'src_class':DAOSource_coo, };

DAOFileFormatInitD['lst']={'ftype':"lst", 'numl':3,
                 'ndata':1, 'lendata':43,         'format_row':{'in': (int, float, float, float, float), 'sep':(7,9,9,9,9), 'out':"{:7d} {:8.3f} {:8.3f} {:8.3f} {:8.4f}"},
                           'form_class':DAOPhotoFileFormat, 'header_class':DAOHeader, 'footer_class':None, 'src_class':DAOSource, };
DAOFileFormatInitD['nei']={'ftype':"nei", 'numl':3,
                           'form_class':DAOPhotoFileFormat, 'header_class':DAOHeader, 'footer_class':None, 'src_class':DAOSource_nei, };

DAOFileFormatInitD['ap'] ={'ftype':"ap", 'numl':2, 'ndata':1, 'lendata':34,
                           'form_class':DAOPhotoFileFormat, 'header_class':DAOHeader, 'footer_class':None, 'src_class':DAOSource_ap, };

DAOFileFormatInitD['raw'] ={'ftype':"raw", 'numl':1,
     'ndata':1, 'lendata':34,   'format_row':{'in': ((),(int, float, float, float), (float, float, float, float)), 'sep':((),(7,9,9,9),(14,6,6,8)), 'out':('',"{:7d} {:8.3f} {:8.3f} {:8.3f}","{:14.3f} {:5.2f} {:5.2f} {:7.4f}")},
                            'src_class':DAOSource_ap, 'header_class':DAOHeader, 'form_class':DAOPhotoFileFormat, 'footer_class':None, };

DAOFileFormatInitD['mag']={'ftype':"mag", 'numl':1,
                           'src_class':DAOSource_mag, 'header_class':DAOHeader, 'form_class':DAOPhotoFileFormat, 'footer_class':None, };



class DAOPhotoFileFormat(basefile.PhotoFileFormat):  
    """Class to define the format of a photometric file for DAOPhot
""";
    def __init__(self, ftype=None):
        """DAOPhotoFileFormat class: format of DAOPhotoFile class. No methods.
""";
        _name_='DAOPhotoFileFormat object';
        self.numl=0;
        super().__init__(ftype=ftype, FFormatInitD=DAOFileFormatInitD); #=>basefile.PhotoFileFormat

        if(not isinstance(self.numl,int) or self.numl<=0): raise TypeError(_name_+": 'numl' must be a positive integer");
    

    def copy(self):
        return DAOPhotoFileFormat(self);
    def __copy__(self):
        return self.copy();
  
###################################

DAO_idxy=DAOPhotoFileFormat(ftype=None)
DAO_data=DAOPhotoFileFormat(ftype='')
DAO_als=DAOPhotoFileFormat(ftype="als")
DAO_alf=DAOPhotoFileFormat(ftype="alf")
DAO_coo=DAOPhotoFileFormat(ftype="coo")
DAO_lst=DAOPhotoFileFormat(ftype="lst")
DAO_nei=DAOPhotoFileFormat(ftype="nei")
DAO_ap1=DAOPhotoFileFormat(ftype="ap")
DAO_mag=DAOPhotoFileFormat(ftype="mag")
DAOFileFormatD={None:DAO_idxy, '':DAO_data, 'als':DAO_als, 'alf':DAO_alf, 'coo':DAO_coo, 'lst':DAO_lst, 'nei':DAO_nei, 'ap':DAO_ap1,  'mag':DAO_mag}
###################################

################
###SOURCE class
class DAOIdXY(basefile.bclasses.IdXY):
    """Class for DAO 2D point with ID""";
    _dtype_names=('idx', 'x', 'y');
    _dtype_nfield=len(_dtype_names);
    _dtype_formats=(str, float, float);
    _dtype_nlines=1;
    _dtype_delimiter=(7,9,9);
    _str_format="{idx:>7} {x:8.3f} {y:8.3f}";
    
    (idx,idn, x,y)='-',0, 0.,0.;
    withid=True;
    def __init__(self, data=None):
        super().__init__(data=data, withid=True); #=>basefile.bclasses.IdXY
        self.idx=str(self.idn);

class DAOSourceData(basefile.SourceData):
    """Class for DAO 2D point with ID and data""";
    _dtype_delimiter=(7,9,9);
    _str_format="{idx:>7} {x:8.3f} {y:8.3f}";
    
    (idx,idn, x,y, data)='-',0, 0.,0., '';
    withid=True;
    def __init__(self, data=None, fulldata=True):
        super().__init__(data=data, withid=True, fulldata=fulldata); #=>basefile.SourceData
        self.idx=str(self.idn);

class DAOSource(basefile.Source):
    """Class for DAO 2D point with ID and data""";
    _dtype_names  =('idx',   'x',   'y', 'mag', 'emag', 'sky');
    _dtype_formats=(  str, float, float, float,  float, float);
    _dtype_nfield=len(_dtype_names);
    _dtype_nlines=1;
    _dtype_delimiter=(7,9,9,9,9,9);
    _str_format="{idx:>7} {x:8.3f} {y:8.3f} {mag:8.3f} {emag:8.4f} {sky:8.3f}";
    
    (idx,idn, x,y, mag,emag, sky)='-',0, 0.,0., 99.999,0., 0;
    withid=True;
    def __init__(self, data=None): #DAOSource
        super().__init__(data=data, withid=True); #=>basefile.Source
        self.idx=str(self.idn);

class DAOSource_als(basefile.Source_fph):
    """Source object in Allstar output (idx, x, y, mag, emag, sky, niter, chi2, sharp)
    """
    _dtype_names=('idx', 'x', 'y', 'mag', 'emag', 'sky', 'niter', 'chi2', 'sharp');
    _dtype_formats=(int, float, float, float, float, float, float, float, float);
    _dtype_nfield=len(_dtype_names);
    _dtype_nlines=1;
    _dtype_delimiter=(7,9,9,9,9,9,9,9,9)
    _str_format="{idx:>7} {x:8.3f} {y:8.3f} {mag:8.3f} {emag:8.4f} {sky:8.3f} {niter:8.0f} {chi2:8.3f} {sharp:8.3f}";

    (idx,idn, x,y, mag,emag, sky, niter, chi2, sharp)='-',0, 0.,0., 99.999,0., 0, 0, 0., 0;

    def __init__(self, data=None):
        super().__init__(data=data, withid=True); #=>basefile.Source_fph
        self.idx=str(self.idn);

class DAOSource_alf(DAOSource_als):
    """Source object in Allframe output (idx, x, y, mag, emag, sky, niter, chi2, sharp)
    """
    _str_format="{idx:>7} {x:8.3f} {y:8.3f} {mag:8.3f} {emag:8.4f} {sky:8.2f} {niter:8.0f} {chi2:8.2f} {sharp:8.3f}";
    def __init__(self, data=None):
        super().__init__(data); #=>DAOSource_als
        self.idx=str(self.idn);

class DAOSource_nei(basefile.Source):
    """Source object in .nei output (idx, x, y, mag, sky)
    """
    _dtype_names  =('idx',   'x',   'y', 'mag', 'sky');
    _dtype_formats=(  int, float, float, float, float);
    _dtype_nfield=len(_dtype_names);
    _dtype_nlines=1;
    _dtype_delimiter=(7,9,9,9,9);
    _str_format="{idx:>7} {x:8.3f} {y:8.3f} {mag:8.3f} {sky:8.3f}";

    (idx,idn, x,y,  mag,emag,  sky, niter, chi2, sharp)='-',0, 0.,0.,  99.999,0.,  0.,0, 0.,0.;

    def __init__(self, data = None):
        super().__init__(data=data, withid=True); #=>basefile.Source
        self.idx=str(self.idn);
        self.emag = 0;

class DAOSource_coo(basefile.Source):
    """Source object in DAOPhot:find output (idx, x, y, mag, sharp, rnd, rndm).
    """
    _dtype_names  =('idx',   'x',   'y', 'mag', 'sharp', 'rnd', 'rndm');
    _dtype_formats=(  int, float, float, float,   float, float, float);
    _dtype_nfield=len(_dtype_names);
    _dtype_nlines=1;
    _dtype_delimiter=(7,9,9,9,9,9,9);
    _str_format="{idx:>7} {x:8.3f} {y:8.3f} {mag:8.3f} {sharp:8.3f} {rnd:8.3f} {rndm:8.3f}";

    (idx, idn,  x,   y, mag, sharp, rnd, rndm)=('-',0, 0.,0.,  99.999, 0., 0., 0.  );

    def __init__(self, data = None):
        super().__init__(data=data, withid=True); #=>basefile.Source
        self.idx=str(self.idn);
        self.emag = 0;

class DAOSource_ap(basefile.IdXYml):
    _dtype_names=((),('idx','x', 'y', 'mag'), ('sky', 'skydev', 'skyskew','emag')) 
    _dtype_formats=((),(int, float, float, float), (float, float, float, float));
    _dtype_nfield=tuple(len(x) for x in _dtype_names);
    _dtype_delimiter=((),(7,9,9,9),(14,6,6,8));
    _str_format=('',"{idx:>7} {x:8.3f} {y:8.3f} {mag:8.3f}","{sky:14.3f} {skydev:5.2f} {skyskew:5.2f} {emag:7.4f}");
    _dtype_nlines=3;

    (idx,idn, x, y, mag,   sky, skydev, skyskew,emag)=('0',0,  0.,0.,  99.999,  0., 0., 0., 0.0 )
    
    def __init__(self, data = None):
        super().__init__(data); #=>basefile.IdXYml
        self.idx=str(self.idn);
#    if(isinstance(data, str)):
#      tmpl = data.strip().split('\n');
#      self.idx, self.x,self.y, self.mag = ( t(x) for t,x in zip(DAO_ap1.format_row['in'][1], tmpl[0].split()[:4]) );
#      self.sky, self.skydev, self.skyskew, self.emag = ( t(x) for t,x in zip(DAO_ap1.format_row['in'][2], tmpl[1].split()[:4]) );
#    elif(isinstance(data, tuple)):
#      if(len(data)==1):  self.idx, self.x,self.y, self.mag,self.emag, self.sky, self.skydev, self.skyskew = data[:8];
#      elif(len(data)==2):
#        self.idx, self.x,self.y, self.mag = data[0][:4];
#        self.sky, self.skydev, self.skyskew, self.emag = data[1][:4];
#      else: raise TypeError('DAOSource_ap: Wrong type for data in the initialization')
#    elif(isinstance(data, basefile.Source_ap)): self.idx, self.x,self.y, self.mag,self.emag, self.sky, self.skydev, self.skyskew = funct.extractint(data.idx), data.x,data.y, data.mag,data.emag, data.sky, data.skydev, data.skyskew;
#    elif(isinstance(data, basefile.Source_fph)): self.idx, self.x,self.y, self.mag,self.emag, self.sky, self.skydev, self.skyskew = funct.extractint(data.idx), data.x,data.y, data.mag,data.emag, data.sky, 0, 0;
#    else: raise TypeError('DAOSource_ap: Wrong type for data in the initialization')
#  def __str__(self):
#    out='\n'+DAO_ap1.format_row['out'][1].format(self.idx, self.x, self.y, self.mag);
#    out+='\n'+DAO_ap1.format_row['out'][2].format(self.sky, self.skydev, self.skyskew, self.emag)
#    return out;
#  def oneline(self):
#    """One-line string""";
#    out=DAO_idxy.format_row['out']+daopar.DAO_Par['DataErrTxt']+daopar.DAO_Par['DataTxt']*3;
#    return out.format(self.idx, self.x, self.y, self.mag, self.emag, self.sky, self.skydev, self.skyskew);
#  def list(self):
#    return [self.idx, self.x, self.y, self.mag,self.emag, self.sky, self.skydev, self.skyskew];
#  def flist(self):
#    return [self.x, self.y, self.mag,self.emag, self.sky, self.skydev, self.skyskew];

class DAOSource_apL(DAOSource_ap):
    def __init__(self, data = None):
        super().__init__(data); #=>DAOSource_ap
        self.idx=str(self.idn);
        self.mL=[self.mag]; self.errL=[self.emag];
        if(isinstance(data,str)):
            tmpl = data.strip().split('\n');
            tmpl[0]=[float(x) for x in tmpl[0].split()[4:]];
            tmpl[1]=[float(x) for x in tmpl[1].split()[4:]];
        elif(isinstance(data,tuple)):   
            if(len(data)==1):
                tmpl[0]=list(data[8::2]);
                tmpl[1]=list(data[9::2]);
            elif(len(data)==2):
                tmpl[0]=list(data[0][4:]);
                tmpl[1]=list(data[1][4:]);
        else: raise TypeError('DAOSource_apL: Wrong type for data in the initialization')
        if(len(tmpl[0])>0):
            self.mL.extend(tmpl[0]);
            self.errL.extend(tmpl[1]);
        self.nap=len(self.mL);
    def __str__(self):
        out='\n'+DAO_ap1.format_row['out'][1].format(self.idx, self.x, self.y, self.mL[0])
        for ii in range(1,self.nap):
            out+=daopar.DAO_Par['DataTxt'].format(self.mL[ii]);
        out+='\n'+DAO_ap1.format_row['out'][2].format(self.sky, self.skydev, self.skyskew, self.errL[0])
        for ii in range(1,self.nap):
            out+=daopar.DAO_Par['ErrTxt'].format(self.errL[ii]);
        return out;
    def oneline(self):
        out=DAO_idxy.format_row['out']+daopar.DAO_Par['DataTxt']*3+daopar.DAO_Par['DataErrTxt'];
        out=out.format(self.idx, self.x, self.y, self.sky, self.skydev, self.skyskew, self.mL[0], self.errL[0]);
        for ii in range(1,self.nap):
            out+=daopar.DAO_Par['DataErrTxt'].format(self.mL[ii], self.errL[ii]);
        return out;
        
class DAOSource_raw(basefile.SourceMD):
    def __init__():
        super().__init__(data); #=>basefile.SourceMD
        self.idx=str(self.idn);

class DAOSource_mag(basefile.Source_fph):
    """Source object in Allstar output (idx, x, y, mag, emag, e1m, nobs, chi2, sharp, var, blunder)
    """
    _dtype_names= ('idx',  'x',   'y', 'mag', 'emag', 'e1m', 'nobs', 'chi2', 'sharp', 'var', 'blunder');
    _dtype_formats=(int, float, float, float,  float,  float, float,  float,   float, float,   float);
    _dtype_nfield=len(_dtype_names);
    _dtype_nlines=1;
    _dtype_delimiter=(7, 9,9, 9,9, 9,9,9,9,9,9)
    _str_format="{idx:>7} {x:8.3f} {y:8.3f} {mag:8.3f} {emag:8.4f} {e1m:8.3f} {nobs:8.0f} {chi2:8.3f} {sharp:8.3f} {var:8.2f} {blunder:8.3f}";

    (idx,idn, x,y, mag,emag, e1m, nobs, chi2, sharp, var, blunder)='-',0, 0.,0., 99.999,0., 0, 0, 0., 0, 0, 0;

    def __init__(self, data=None):
        super().__init__(data=data, withid=True); #=>basefile.Source_fph
        self.idx=str(self.idn);

####
DAOSourceTypeD={None:DAOIdXY, '':DAOSourceData, 'als':DAOSource_als, 'alf':DAOSource_alf, 'coo':DAOSource_coo, 'lst':DAOSource, 'nei':DAOSource_nei, 'ap':DAOSource_ap, 'aph':DAOSource_apL, 'mag':DAOSource_mag}

########################################################
########################################################
#FILE Class
class DAOPhotoFile(basefile.PhotoFile):
    """

""";
    def __init__(self, fname=None, ftype=None, header=None):
        """

""";
        super().__init__(fname=fname, ftype=ftype, header=header, FormatInit=DAOFileFormatInitD); #=>basefile.PhotoFile
        self.sourcetype=None;
        if(not isinstance(self.fform, DAOPhotoFileFormat)): self.fform=DAO_idxy.copy();
        if(ftype==None and isinstance(fname,str)):
            suff=fname.split('.')[-1];
            if(suff in DAOFileFormatD): ftype=suff;
        if(header==None and isinstance(fname,str) and funct.get_num_lines(fname)>=daopar.DAO_Par['headerlen']):
            header=DAOHeader(fname);
            
        if(isinstance(ftype,DAOPhotoFile)):
            if(not isinstance(header, DAOHeader)): header=ftype.header;
            self.fname, self.srcL, self.fform = ftype.fname, ftype.srcL.copy(), DAOPhotoFileFormat(ftype.fform);
        elif(ftype in DAOFileFormatD): 
            self.fform = DAOPhotoFileFormat(DAOFileFormatD[ftype]);
            self.sourcetype=DAOSourceTypeD[ftype];
        if(not self.sourcetype): self.sourcetype=DAOFileFormatD[self.fform.ftype];

        if(fname): self.fname=fname;
        if(isinstance(header, DAOHeader)): self.fform.header=header;
        self.header=self.fform.header;

    def __enter__(self):
        return self;
    def __exit__(self, exc_type, exc_value, exc_tb):
        if(exc_type!=None):
            return False;
        else:
            pass;


    def oneline(self, fname=None):
        """Write a DAOPhotoFile from the internal list of sources in oneline format.
""";
        if(not self.srcL): raise ValueError("DAOPhotoFile: wrong internal source list");
        if(not fname): fname=self.fname;
        if(not fname): raise ValueError('DAOPhotoFile: no name');
        tmpf=DAOPhotoFile(self);
        tmpf.fform.header.nline=1;
        with open(fname, 'w') as fout:
            tmpf.writeheader(output=fout);
            for src in tmpf.srcL:
                fout.write(src.oneline());


