"""Classes for Files and Sources

class FileHeader(bclasses.GenStructData)
    class PhotoFileHeader(FileHeader)

    class SourceData(bclasses.IdXY)
    class Source(bclasses.IdXY)
        class Source_fph(Source): # ID X Y MAG ERR  SKY NITER CHI SHARP
        class Source_ap(Source): # ID X Y MAG ERR SKY SKY_DEV SKY_SKEW
            class Source_apL(Source_ap)
    class SourceMD(bclasses.IdXY)
class IdXYml(bclasses.GenStructData)

class FileFormat
    class PhotoFileFormat(FileFormat)

class GenFile
    class PsfFile(GenFile)
    class PhotoFile(GenFile)

class CtlgFile()

"""

import os, re, math, io, copy, collections

import numpy
from scipy.optimize import curve_fit as sp_curve_fit
from astropy import wcs
from astropy.io import fits as pyfits
from astropy import units
from astropy.coordinates import SkyCoord

from ....exceptions import *
from ... import basicpar as bpar
from ... import options as _opt
from .. import bclasses

###############
##   CLASS   ##
###############



 ################
 ## FILE Class ##
 ################

#HEADER
class FileHeader(bclasses.GenStructData):
    """Class for generic header.

Parameters
----------
  indata : tuple, list, FileHeader object,str, io.TextIOWrapper
        Input data as a tuple of header data values, or a list of lines [str] of header, or a FileHeader object, or the filename from which extract the header or the associated io.TextIOWrapper.
  hform : dict
        Dictionary defining the format of the header.
          'body' : dict
               Dictionary with characteristics to determine the body of the header (up to where it is header):
                 'pref' : str
                      String that is present at the start of every line of the header;
                 'len' : int
                      Length in lines of the header
                 'end' : str
                      String that is present at the end of the header;
          'pos': tuple of ints or int
               Positions (from 0 to 'len'-1) of the lines in indata with actual data; () or -1 for all the lines;

Attributes
----------
    dlines : tuple of str
        tuple of lines with data, corrisponding to hform['pos'].
    length : int
        Length in lines of the header.
    pos : tuple
        Tuple of positions (starting with 0) in indata with actual data.
""";
#  _dtype_names=((), ());
#  _dtype_nlines=len(_dtype_names);
#  _dtype_formats=((), )*_dtype_nlines;
#  _dtype_nfield=tuple(len(x) for x in _dtype_names);
#  _dtype_delimiter=(None,)*_dtype_nlines;
#  _str_format=("", "");
#  
##  ()=();
    length=0;
    pos=();
    dlines=();

    def __init__(self, indata=None, hform={'body':{'len':1}, 'pos':0}):
        """FileHeader object: generic class for header of GenFile class. No methods.

""";
        _name_='FileHeader object';
      #Initialization for Header object that just define the format
        self.dlines=();
        self.length=0;
        self.pos=();

        if(indata is not None and not isinstance(indata, (str, io.TextIOWrapper, list, tuple, FileHeader))): raise TypeError(_name_+": wrong input 'indata' (None, str, io.TextIOWrapper, list, tuple, FileHeader) ");
        if(not indata): return;

        if(any(key not in hform for key in ('body','pos'))): raise SkZpipeError("'hform' dictionary must have keys 'body' and 'pos'.", exclocus=_name_);
        if(not isinstance(hform['body'], dict)): raise TypeError(_name_+": hform['body'] must be a dict.");
        if(not any(key in hform['body']  for key in ('pref', 'len', 'end'))): raise SkZpipeError("hform['body'] dictionary must have any of the keys 'pref', 'len', 'end'.", exclocus='FileHeader object');
        if(not isinstance(hform['pos'], (int,tuple))): raise TypeError(_name_+": hform['pos'] must be a int or tuple of integers.");
        self.pos= (hform['pos'],) if(isinstance(hform['pos'],int)) else hform['pos'];
        for pos in self.pos:
            if(not isinstance(pos, int)): raise TypeError(_name_+": hform['pos'] must be a int or tuple of integers [{pos}].".format(pos=pos));
            if(pos<0):
                self.pos=();
                break;

        if(isinstance(indata, str)):
            indata=open(indata);
            op_flg=True;
        else:
            op_flg=False;
        if(isinstance(indata, io.TextIOWrapper)):
            tmpl=[];
            if('len' in hform['body']):  #Read the first hform['body']['len'] lines
                if(not isinstance(hform['body']['len'],int) or hform['body']['len']<0): raise TypeError(_name_+": hform['body']['len'] must be a positive integer.");
                for ii in range(hform['body']['len']):
                    tmpl.append(indata.readline());
            elif('pref' in hform['body']):  #Read the first lines untill they start with hform['body']['pref']
                if(not isinstance(hform['body']['pref'],str)): raise TypeError(_name_+": hform['body']['pref'] must be a str.");
                for line in indata:
                    if(line.lstrip().startswith(hform['body']['pref'])): tmpl.append(line);
                    else:
         ##!!!!!Losing one input line from file. need closing and reread!!!!!!!!!
                        break;
            elif('end' in hform['body']):  #Read the first lines untill a line starting with hform['body']['end']
                if(not isinstance(hform['body']['end'],str)): raise TypeError(_name_+": hform['body']['end'] must be a str.");
                for line in indata:
                    if(line.lstrip().startswith(hform['body']['end'])): break;
                    tmpl.append(line);
         ##!!!!!Losing one input line from file. need closing and reread!!!!!!!!!
            if(op_flg): indata.close();
            indata=tmpl;

        if(isinstance(indata, list)):
            self.dlines=[];
            if(self.length==0): self.length=len(indata); 
            if(self.pos):
                for ii in self.pos:
                    self.dlines.append(indata[ii]);
            else:  self.dlines=indata;
            self.dlines=tuple(self.dlines);

        if(isinstance(indata,FileHeader)):
            self.dlines=indata.dlines; #It is a tuple, so a copy creates a new object
            self.length=indata.length; 
        elif(isinstance(indata,tuple)):
            self.dlines=indata;
            if(self.length==0): self.length=len(indata); 
    
        if(not isinstance(self.dlines, tuple)):  raise TypeError(_name_+": attribute 'dlines' should be a tuple.");

  ###
    def __copy__(self):
        return self.__class__(self);
    def copy(self):
        return self.__class__(self);

FileFooter=FileHeader;
###############################################################################
###############################################################################
###############################################################################

class PhotoFileHeader(FileHeader):
    """PhotoFileHeader class: generic class for header of PhotoFile class. No methods.

Parameters
----------
  indata : tuple, list, PhotoFileHeader object,str, io.TextIOWrapper
        Input data as a tuple of header data values, or a list of lines [str] of header, or a PhotoFileHeader object, or the filename from which extract the header or the associated io.TextIOWrapper.
  hform : dict
        Dictionary defining the format of the header.
          'len':   [int] length in lines of the header;
          'pos':   [tuple,int]  positions (from 0 to 'len'-1) of the lines in indata with actual data;
          'in' :   [tuple] tuple of objects forming the header data;
          'out':   [str] string with the output format for the header;
          'split': [tuple] tuple of lengths of the field for each header datum into which to split the input data

Attributes
----------
    dlines : tuple of str
        tuple of lines with data, corrisponding to hform['pos'].
    length : int
        Length in lines of the header.
    pos : tuple
        Tuple of positions (starting with 0) in indata with actual data.
    nx,ny : int
        Size of the image in pixel
    low : float
        Lowest good datum
    high : float
        Highest good datum
    thresh : float
        Threshold for detection
    ap1 : float
        First aperture radius
    gain : float
        Gain
    ron : float
        RON
    frad : float
        Fiiting radius
""";

    def __init__(self, indata=None, hform={'len':1, 'pos':0}):
        """PhotoFileHeader object for header of PhotoFile class. No methods.

""";
    
        super().__init__(indata=indata, hform=hform); #=>FileHeader
   #Initialization for Header object that just define the format
        self.nx,self.ny, self.low,self.high, self.thresh, self.ap1, self.gain,self.ron, self.frad=(0,0,  0,-1, 0, 0, 0,-1, 0);

        if(isinstance(indata,PhotoFileHeader)):
            self.nx, self.ny, self.low, self.high, self.thresh, self.ap1, self.gain, self.ron, self.frad = indata.nx, indata.ny, indata.low, indata.high, indata.thresh, indata.ap1, indata.gain, indata.ron, indata.frad;

  ###
    def tuple(self):
        return (self.nx, self.ny, self.low, self.high, self.thresh, self.ap1, self.gain, self.ron, self.frad);
    def __repr__(self):
        return """# NX NY  LOW HIGH   THRE  FRAD  AP  GAIN RON
# {:d} {:d}  {:f} {:f}  {:f} {:f} {:f} {:f} {:f}""".format(self.nx, self.ny,  self.low, self.high,  self.thresh, self.frad, self.ap1, self.gain, self.ron);
    def __str__(self):
        return repr(self);

    def print(self):
        return str(self)+"\n";

    def __copy__(self):
        return PhotoFileHeader(self);
    def copy(self):
        return PhotoFileHeader(self);

###############################################################################

 ##################
 #CLASS    "declaration"
class SourceData(bclasses.IdXY):  # ID X Y data
    pass;
class Source(bclasses.IdXY): # ID X Y MAG ERR
    pass;
class Source_fph(Source): # ID X Y MAG ERR  SKY NITER CHI SHARP
    pass;
class Source_ap(Source): # ID X Y MAG ERR SKY SKY_DEV SKY_SKEW
    pass;
class Source_apL(Source_ap): # ID X Y MAG ERR SKY SKY_DEV SKY_SKEW MAG_I ERR_I ...
    pass;
class FileFormat:
    """Class to define the format of a generic file""";
    pass
class PhotoFileFormat(FileFormat):
    """Class to define the format of a photometric file""";
    pass
 ##################


#FILEFORMAT
PhotoFileFormatInitD={'_doc_':
"""Database of PhotoFileFormat
  KEY
     'ftype' : str, None
        Name of the type
     'form_class' : class
        Class of the format.
     'header_class' : class
        Class of the format.
     'footer_class' : Header subclass
        Header subclass of the format.
     'src_class': class
        Class to use to generate the source list.
     'comments' : str
        The string used to indicate the start of a comment
     'coordsys' : tuple 
        Tuple of 2 values with: 
            type of coordinates (string or astropy unit), 
            coordinate frame (string, astropy frame)
                        

"""};

PhotoFileFormatInitD[None] ={'ftype':None,
                             'form_class':PhotoFileFormat, 'header_class':PhotoFileHeader, 'footer_class':None, 'src_class':bclasses.IdXY, 'comments':'#', };

PhotoFileFormatInitD['']   ={'ftype':'', 
                             'form_class':PhotoFileFormat, 'header_class':PhotoFileHeader, 'footer_class':None, 'src_class':SourceData, 'comments':'#', } 

PhotoFileFormatInitD['src']={'ftype':"src",
                             'form_class':PhotoFileFormat, 'header_class':PhotoFileHeader, 'footer_class':None, 'src_class':Source, 'comments':'#', };

PhotoFileFormatInitD['fph']={'ftype':"fph",
                             'form_class':PhotoFileFormat, 'header_class':PhotoFileHeader, 'footer_class':None, 'src_class':Source_fph, 'comments':'#', };

PhotoFileFormatInitD['ap'] ={'ftype':"ap",  
                             'form_class':PhotoFileFormat, 'header_class':PhotoFileHeader, 'footer_class':None, 'src_class':Source_ap, 'comments':'#', };

###############################################################################
def PhotoFileFormatSign(fname=None, fstream=None):
    """Create a signature of the format of the file

Parameters
----------
    fname : str or None
        Name of the file
    fstream : IOStream
        Object that support read method.

""";
    _name_='PhotoFileFormatSign';
    if(fname is None and fstream is None): raise ValueError(_name_+": 'fname' and 'fstream' cannot be both undefined.");
    if(isinstance(fname,str)): fstream=open(fname);

    linesL, startL, same0L = [], [], [];
    nfldL, lenL, samefL = [], [];
    for ii in range(10):
        line=fstream.readline();
        if(line == ''): break;
        linesL.append(line);
        startL.append(line[0]);
        same0L.append( not line[0].isspace() and not line[0].isdecimal() and line[0]!='.' and line[0]==startL[0] );
        lenL.append(len(line));
        tup=tuple([len(line.split() )]+['f' if(isnumber(fld)) else 's' for fld in line.strip().split()]);
        fldL.append( tup);
    
    headerL=[]
    for ii in range(1,10):
        samefL.append(tup==fldL[ii-1])
        if(sameL0[ii]): headerL.append(ii+1);
    
  ##
    if(isinstance(fname,str)): fstream.close();
###############################################################################


#####
class FileFormat:
    """Class to define the format of a generic file

Parameters
----------
    ftype : dict or FileFormat or str
        Input information for the format of the file. Mainly as dictionary or FileFormat object, or as key of the internal database.
        Keys for the dictionary:
         'ftype' : str or None
             Name of the type
         'form_class' : FileFormat subclass
             Class of the format.
         'header_class' : Header subclass
             Header class of the format.
         'footer_class' : Footer subclass
             Footer class of the format.
             

Attributes
----------
    Same as the input parameter `ftype` as dictionary.
    'form_class' : FileFormat subclass
        Class of the format.

""";
    ftype='';
    def __init__(self, ftype=None, FFormatInitD=None):
        self.ftype='';
        self.form_class=None;

  ###
    def copy(self):
        return self.__class__(ftype=self.__dict__.copy());
    def __copy__(self):
        return self.__class__(ftype=self.__dict__.copy());

#####
class PhotoFileFormat(FileFormat):
    """Class to define the format of a photometric file

Parameters
----------
    ftype : dict or PhotoFileFormat or str
        Input information for the format of the photometric file. Mainly as dictionary or PhotoFileFormat object, or as key of the internal database.
        Keys for the dictionary:
         'ftype' : str or None
             Name of the type
         'form_class' : FileFormat subclass
             Class of the format.
         'header_class' : Header subclass
             Header class of the format.
         'footer_class' : Footer subclass
             Footer class of the format.
         'src_class' : IdXY subclass
             Class to use to generate the source list.
         'comments' : str, None [optional]
             The string used to indicate the start of a comment
             

Attributes
----------
    Same as the input parameter `ftype` as dictionary.
""";
    comments=None;

    def __init__(self, ftype=None, FFormatInitD=None):
        """PhotoFileFormat class: format of PhotoFile class. No methods.

""";
        _name_='PhotoFileFormat object';
        if(not isinstance(FFormatInitD, dict)): FFormatInitD=PhotoFileFormatInitD;

        if(isinstance(ftype, collections.abc.Hashable) and  ftype not in FFormatInitD): 
            if(not isinstance(ftype, (PhotoFileFormat,dict))): raise TypeError(_name_+": 'ftype' must be the name of a file type or a dict with the type definitions");
        if(ftype.__hash__ and ftype in FFormatInitD): ftype=FFormatInitD[ftype];

        if(isinstance(ftype, dict)):
            test={'ftype', 'header_class', 'form_class', 'src_class'}-set(ftype);
            if(test == set()):
                self.__dict__=ftype.copy()
            else: raise KeyError(_name_+": missing keys in the definition {keys}.".format(keys=test));
        elif(isinstance(ftype, PhotoFileFormat)):
            self.__dict__.update(ftype.__dict__);
        else: raise TypeError(_name_+": 'ftype' must be a dict or a PhotoFileFormat object or type defined in the initialization dictionary for this format ({keys})".format(keys=list(FFormatInitD)));
      
        if(self.ftype is not None and  not isinstance(self.ftype,str)): raise TypeError(_name_+": 'ftype' is set to a wrong type {}".format(ftype));



###############################################################################
PhotoFileFormatD={
    None:  PhotoFileFormat(ftype=None),
    '':    PhotoFileFormat(ftype=''),
    'fph': PhotoFileFormat(ftype="fph"),
    'src': PhotoFileFormat(ftype="src"),
    'ap':  PhotoFileFormat(ftype="ap"),
};

###############################################################################
###############################################################################
"""
Attributes for correct definition
---------------------------------
  _dtype_names : tuple of str / tuple of tuples of str
        Tuple of the name of the variable in the order as they appear in the input.
        Basic names: idx is a string ID, x and y are coordinates, mag and emag are magnitud and its error
  _dtype_formats : tuple of class or coverters / tuple of tuples of class/coverters 
        Tuple of object convertibles, one for each item in _dtype_names
  _dtype_nfield : int
        Number of single datum for each input. Default len(_dtype_names).
  _dtype_nlines : int
        Number of line to be read for each source
  _dtype_delimiter : None, str, int, sequence
        The string used to separate values.  By default, any consecutive
        whitespaces act as delimiter.  An integer or sequence of integers
        can also be provided as width(s) of each field.
  _str_format : formatted str
        Formatted string naming the variable according to _dtype_names

Additional attributes
---------------------
  withid : bool 
        If the object has a own ID (string or number)
  idn : int
        Additional integer ID passed during the initialization or get from `idx`. Default 0
""";

 #SOURCE Classes
###############################################################################
class IdXYml(bclasses.GenStructData):  #Really usefull? Maybe only DAOap use multiline!
    """Class for 2D point with ID with data distributed on several lines (based on GenStructData).

Parameters for initialization
-----------------------------
    data : str, list or tuple of str
        The several lines appended sequencely
 
Attributes for correct definition
---------------------------------
  _dtype_names : tuple of tuples of str
        For each line, tuple of the names of the variables in the order as they appear in the input.
        Basic names:
          idx : str
            A string ID
          x,y : float
            Coordinates
          mag,emag : float
            Magnitud and its error
          sky : float
            Sky value around the source
          skydev : float
            Standard deviation of the sky value around the source
          skyskew : float
            Skewness of the sky value around the source
          chi2 : float (positive)
            Chi square value of PSF fitting for the source
          sharp : float
            Sharp value for the source
          niter : int (positive)
            Number of iteration to converge the fitting
  _dtype_formats : tuple of tuples of class/coverters 
        For each line, a tuple of object convertibles, one for each item in _dtype_names
  _dtype_nfield : int
        For each line, number of single datum for each input. Default len(_dtype_names).
  _dtype_nlines : int
        For each line, number of line to be read for each source
  _dtype_delimiter : None, str, int, sequence
        For each line, the string used to separate values.  By default, any consecutive
        whitespaces act as delimiter.  An integer or sequence of integers
        can also be provided as width(s) of each field.
  _str_format : formatted str
        For each line, formatted string naming the variable according to _dtype_names

Additional attributes
---------------------
  withid : bool 
        If the object has a own ID (string or number)
  idn : int
        Additional integer ID passed during the initialization or get from `idx`. Default 0
""";
    _dtype_names=(('idx',), ('x', 'y'));
    _dtype_nlines=len(_dtype_names);
    _dtype_formats=((str,), (float, float));
    _dtype_nfield=tuple(len(x) for x in _dtype_names);
    _dtype_delimiter=(' ',' ');
    _str_format=("{idx:>12}", "{x:10f} {y:10f}");
  
    (idx,idn, x,y)='-',0, 0.,0.;
    withid=True;

    
 ###__INIT__###
    def __init__(self, data=None, withid=None, idn=0):
        """IdXY object with 2D coordinates and eventually an ID with data distributed on multiple lines.
""";
        _name_='IdXY-multiline object';
        self.idx="-";
        if(data is None): raise ValueError(_name_+": No data to create the object");
        if(withid is not None): self.withid=withid;
        super().__init__(data=data); #=> bclasses.GenStructData

        try:
            nid=int(self.idx);
        except:
            if(idn): self.idn=idn;
        else:
            self.idn=nid;

 ###__INIT___### END

  ###
    def coordL(self):
        return [self.x, self.y];
    def coordT(self):
        return (self.x, self.y);
    def coordD(self):
        return {'x': self.x, 'y':self.y};
    def flist(self):
        if(self.idn):
            return [getattr(self, var) for var in ('idn',)+self._dtype_names[1:]];
        else:
            return [getattr(self, var) for var in self._dtype_names[1:]];
    
###############################################################################

class SourceData(bclasses.IdXY):  ## UTIL????
  """Class for 2D point with ID, including the full data string in attribute `data`

Parameters
----------
    data :
        Initialization data
    withid : bool
        If the object as an ID or not
    idn : int
        The integer version of the ID
    fulldata : bool
        If to store all the data?

""";
  _dtype_names=('idx','x','y');
  _dtype_nfield=len(_dtype_names);
  _dtype_formats=(str, float, float);
  _dtype_nlines=1;
  _dtype_delimiter=None;
  _str_format="{idx:>12} {x:10f} {y:10f}";
  
  (idx,idn, x,y,  data)='-',0, 0.,0.,  '';

  def __init__(self, data=None, withid=None, idn=0, fulldata=True):
    """SourceData object with 2D coordinates and eventually an ID.
""";
    _name_='SourceData object';
    self.idx="-";
    if(withid is not None): self.withid=withid;
    self.data=data;
    if(not self.withid):
      if('idx' in self._dtype_names):
        self._dtype_names=self._dtype_names[1:];
        self._dtype_formats=self._dtype_formats[1:];
    if(len(self._dtype_formats)!=len(self._dtype_names)): raise SkZpipeError("", exclocus=_name_);

    from ....functions  import splitconvert
    data=splitconvert(data=data, delimiter=self._dtype_delimiter,  converters=self._dtype_formats, appendinput=True if(fulldata) else -1, conv_repeat=False);
    if(isinstance(data,(list,tuple))):
      self.__dict__.update(dict(zip( self._dtype_names, data[:-1]  )));
      setattr(self, 'data', data[-1]);
    elif(isinstance(data, bclasses.IdXY)):
      self.__dict__.update(copy.deepcopy(data.__dict__))
      setattr(self, 'data', str(data) if(fulldata) else '');
    else: raise TypeError(_name_+': Wrong type for data in the initialization');
    self.fulldata=fulldata;
    if(isinstance(self.data, str)):  self.data=self.data.rstrip('\n');

    try:
      nid=int(self.idx);
    except:
      if(idn): self.idn=idn;
    else:
      self.idn=nid;

  ###
  def __str__(self):
    if(isinstance(self.data,str)):
      return self.data if(self.fulldata) else self._str_format.format(**dict( ( var , getattr(self, var) ) for var in self._dtype_names if(var!='-') )  )+self.data;
    else:
      return self._dtype_delimiter.join(self.data) if(isinstance(self._dtype_delimiter,str)) else " ".join(self.data);
      

###############################################################################

class Source(bclasses.IdXY):
    """Class for 2D point with ID and one photometric datum  (magnitude, error, sky)""";
    _dtype_names=('idx','x','y', 'mag', 'emag', 'sky');
    _dtype_nfield=len(_dtype_names);
    _dtype_formats=(str, float, float, float, float, float);
    _dtype_nlines=1;
    _dtype_delimiter=None;
    _str_format="{idx:>12} {x:10f} {y:10f} {mag:.4f} {emag:.4f}  {sky:.4f}";
  
    (idx,idn, x,y, mag,emag, sky)='-',0, 0.,0.,  99.999,0., 0.;
    withid=True;

    def __init__(self, data=None, withid=None, idn=0):
        """Source object
""";
        super().__init__(data=data, withid=withid, idn=idn); #=>bclasses.IdXY
  ###

###############################################################################

class Source_fph(Source):
    """Class for 2D point for psf-fitting photometry with ID, magnitude and error, sky, #iteration, chi2, sharp""";
    _dtype_names=('idx','x','y', 'mag', 'emag', 'sky', 'niter', 'chi2', 'sharp');
    _dtype_nfield=len(_dtype_names);
    _dtype_formats=(str, float, float,  float,float,  float, int, float, float);
    _dtype_nlines=1;
    _dtype_delimiter=None;
    _str_format="{idx:>12} {x:10f} {y:10f}  {mag:.4f} {emag:.4f}  {sky:.4f} {niter} {chi2:.4f} {sharp:.4f}";
    
    (idx,idn, x,y,  mag,emag,  sky, niter, chi2, sharp)='-',0, 0.,0.,  99.999,0.,  0.,0, 0.,0.;
    withid=True;
  
    def __init__(self, data=None, withid=None, idn=0):
        """Source_fph object
  """;
        super().__init__(data=data, withid=withid, idn=idn); #=>Source
  ###

###############################################################################

class Source_ap(Source):
    """Class for 2D point with ID, aperture magnitude and error, sky, sky standard deviation and sky skewness""";
    _dtype_names=('idx', 'x','y', 'mag','emag', 'sky','skydev','skyskew');
    _dtype_nfield=len(_dtype_names);
    _dtype_formats=(str, float, float,  float,float,  float, float,float);
    _dtype_nlines=1;
    _dtype_delimiter=None;
    _str_format="{idx:>12} {x:10f} {y:10f}  {mag:.4f} {emag:.4f}  {sky:.4f} {skydev:.4f} {skyskew:.4f}";
    
    (idx,idn, x,y, mag,emag, sky,skydev,skyskew)='-',0, 0.,0.,  99.999,0.,  0.,0.,0.;
    withid=True;
  
    def __init__(self, data = None, withid=None, idn=0):
        """Source_ap object
  """;
        super().__init__(data=data, withid=withid, idn=idn); #=>Source
  ###

###############################################################################

class Source_apL(Source_ap):
  """Class for 2D point with ID, aperture magnitude and error, sky, sky standard deviation and sky skewness""";
  _dtype_names=('idx', 'x','y', 'mag','emag', 'sky','skydev','skyskew');
  _dtype_nfield=len(_dtype_names);
  _dtype_formats=(str, float, float,  float,float,  float, float,float);
  _dtype_nlines=1;
  _dtype_delimiter=None;
  _str_format="{idx:>12} {x:10f} {y:10f}  {mag:.4f} {emag:.4f}  {sky:.4f} {skydev:.4f} {skyskew:.4f}";
  
  (idx,idn, x,y, mag,emag, sky,skydev,skyskew)='-',0, 0.,0.,  99.999,0.,  0.,0.,0.;
  
  withid=True;

  def __init__(self, data = None, maxap=12, withid=None, idn=0):
    super().__init__(data=data, withid=withid, idn=idn); #=>Source_ap
    self.mL=[self.mag]; self.errL=[self.emag];
    if(isinstance(data,str)):
      tmpl=[float(x) for x in data.strip().split(self._dtype_delimiter)[self._dtype_n:]];
      mxpos=min(maxap,len(tmpl[0])>>1);
      if(mxpos>0):
        self.mL.extend(tmpl[0:mxpos<<1:2]);
        self.errL.extend(tmpl[1:mxpos<<1:2]);
    self.nap=len(self.mL);
  ###
  def __str__(self):
    out="{:}  {:10f} {:10f} {:8f} {:6f} {:6f} {:8.4f} {:8.4f}".format(self.idx, self.x, self.y, self.sky, self.skydev, self.skyskew, self.mL[0], self.errL[0])
    for ii in range(1,self.nap):
      out+=" {:8.4f} {:8.4f}".format(self.mL[ii], self.errL[ii]);
    return out;
  def print(self):
    out="{:}  {:10f} {:10f} {:6.4f} {:6.4f} {:8f} {:6f} {:6f}".format(self.idx, self.x, self.y, self.mag, self.emag, self.sky, self.skydev, self.skyskew)
    for ii in range(1,self.nap):
      out+=" {:8.4f} {:8.4f}".format(self.mL[ii], self.errL[ii]);
    return out;
  def list(self):
    return [self.idx, self.x, self.y, self.mag, self.emag, self.sky, self.skydev, self.skyskew];
  def flist(self):
    return [self.x, self.y, self.mag, self.emag, self.sky, self.skydev, self.skyskew];

###############################################################################

class SourceMD(bclasses.IdXY):
    """Class for source with multiple data able to union data from differente sources, as the match of different catalogs

Parameters
----------
    initdata : list of dict, SourceMD
        List of dictionaries, one per each attribute-object to include
        Keys:
            'obj' : str; name of the attribute-object
            'class' : class; class of the attribute-object
            'data' : data for initialization
            'mode' : str; mode for initialization
                'copy': a copy of the object passed with 'data' (by value). Default if 'data' is 
                  an instance of 'class'. Default is to use copy() method of the object
                'link': assigned the object passed with 'data' (by reference: any change in the 
                  original object appears also in the attribute-object).
                'kwargs': 'data' is a dictionary to pass arguments by keywords to the class.
                'args': 'data' is a tuple to pass values by position to the class.
        The attribute-objects are creates with setattr(self, ['obj'], ?? ), according to the mode.
    main : int
        Position in `data` of the attribute-object with tha data to be copied as main attributes 
        (as 'idx', 'x', and 'y') of the object.
        The attribute-object must have 'idxy' method (like IdXY class)
    idd : None, int, tuple of (str,int)
        ID for the source, if different from `main` attribute-object.
        If an integer is provide, attribute 'idx'=str(`idd`) and 'idn'=`idd`
        If a tuple is provided, 'idx'=`idd`[0], 'idn'=`idd`[1]

Attributes
----------
  """;
    _dtype_names=('idx', 'x', 'y');
    _dtype_nfield=len(_dtype_names);
    _dtype_formats=(str, float, float);
    _dtype_nlines=1;
    _dtype_delimiter=None;
    _str_format="{idx:>12} {x:10f} {y:10f}";

    _attr_obj=()
  
    (idx,idn, x,y)='-',0, 0,0;
    def __init__(self, initdata=None, main=None, idx=None):
        """SourceMD object to store source with multiple data
"""
        _name_='SourceMD object'
        import inspect
        if(not isinstance(initdata,list) or not all(isinstance(x,dict) for x in initdata)): 
            raise SkZpipeError(f"`initdata` must be a list of dict.   <{initdata.__class__}>", exclocus=_name_) 
        if(any({'obj', 'class','data'}-set(x)  for x in initdata)): 
            raise SkZpipeError(f"Dictionaries in `initdata` must have the keys 'obj', 'class','data'", exclocus=_name_)
        if(any(not isinstance(x['obj'],str) or not inspect.isclass(x['class']) for x in initdata)): 
            raise SkZpipeError(f"In items of `initdata` 'obj' must has a str, 'class' a class", exclocus=_name_)
        if(any(hasattr(self, x['obj']) for x in initdata)):  
            raise SkZpipeError(f"An item in `initdata` is trying to redefined an existing attribute", exclocus=_name_) 
        if(any(x.get('mode') not in (None, 'copy','link','kwargs','args')  for x in initdata)): 
            raise SkZpipeError(f"In items in `initdata` 'mode' must be 'copy','link','kwargs','args'", exclocus=_name_)
        for x in initdata: 
            if(x.get('mode') == 'args' and not isinstance(x['data'], tuple)):
                raise SkZpipeError(f"In items in `initdata` 'mode' is 'args', 'data' must be a tuple", exclocus=_name_)
            if(x.get('mode') == 'kwargs' and not isinstance(x['data'], dict)):
                raise SkZpipeError(f"In items in `initdata` 'mode' is 'kwargs', 'data' must be a dict", exclocus=_name_)

        if(not isinstance(main, int)):  raise SkZpipeError(f"`main` must be an int.   <{main.__class__}>", exclocus=_name_) 
        if(idd is not None and not isinstance(idd, (int,tuple))):  raise SkZpipeError(f"`idd` must be an int or tuple (str,int).   <{idd.__class__}>", exclocus=_name_)
        if(isinstance(idd, tuple)):  
            if(not isinstance(idd[0], str) or not isinstance(idd[1], int)):
                raise SkZpipeError(f"`idd` must be an int or tuple (str,int).   <{idd}>", exclocus=_name_)
        elif(isinstance(idd, int)): idd=(str(idd), idd)

        self._attr_obj=[] #ordered list of names of attribute-objects
        for attr in initdata:
            mode=attr.get('mode')
            if(mode):
                if(mode=='copy'):
                    if(hasattr(attr['data'], 'copy')):
                        setattr(self, attr['obj'], attr['data'].copy())
                    else:
                        setattr(self, attr['obj'], attr['class'](attr['data']))
                elif(mode=='link'):
                    setattr(self, attr['obj'], attr['data'])
                elif(mode=='args'):
                    setattr(self, attr['obj'], attr['class'](*attr['data']))
                elif(mode=='kwargs'):
                    setattr(self, attr['obj'], attr['class'](**attr['data']))
            else:
                if(isinstance(attr['data'], attr['class'])): #If initdata is an object of the class
                    if(hasattr(attr['data'], 'copy')):
                        setattr(self, attr['obj'], attr['data'].copy())
                    else:
                        setattr(self, attr['obj'], attr['class'](attr['data']))
                else:
                    setattr(self, attr['obj'], attr['class'](attr['data'])) # ????????
            self._attr_obj.append(attr['obj'])
        self._attr_obj=tuple(self._attr_obj)
        
        datamain=dict( zip(('idx','x','y'), getattr(self, self._attr_obj[main]).idxy()) )
        super().__init__(data=datamain, withid=True, idn=idd[1] if(idd) else idd) # => IdXY
        

SourceTypeD={None:bclasses.IdXY, '':SourceData, 'src':Source, 'fph':Source_fph, 'ap':Source_ap};

###############################################################################
###############################################################################
###########
#FILE Class
###########

#Generic File

class GenFile:
    fname='';
    basename='';
    ext='';
    ext_delim='.';
    ftype=None;
    fform=None;
    header=None;    #Header object
  
    ###
    def setname(self, fname=None, ext_delim=None):
        pass;
   ### INIT START ###
    def __init__(self, fname=None, ext_delim=None, FormatInit=None):
        """Generic file.
  
Parameters
----------
    fname : str
        Name of the file
    ext_delim : str OR int
        Separation character for the extension or size of the extension.
    FormatInit : dict or callable
        Object to initialize the file format.

Attributes
----------
    fname : str
        Name of the file
    ext_delim : str OR int
        Separation character for the extension or size of the extension.
    basename : str
        Basename of the file (name without extension and separation character).
    ext : str
        Extension of the file (without separation character).
    ftype : str
        Type of the file
    fform : FileFormat
        Class describing the format of the file
       

""";
        self.setname(fname=fname, ext_delim=ext_delim);

        if(isinstance(FormatInit, dict)):
            if(self.ext in FormatInit):
                self.fform=FormatInit[self.ext]['form_class'](FormatInit[self.ext]);
            elif('form_class' in FormatInit):
                self.fform=FormatInit['form_class'](FormatInit[self.ext]);
        elif(isinstance(FormatInit, FileFormat)):
            self.fform=FormatInit.copy();
        elif(callable(FormatInit)):
            self.fform=FormatInit(self);
      
   #Now fform is set
        if(isinstance(self.fform, FileFormat)):
            self.header= self.fform.header_class(self.fname)
            self.footer= self.fform.footer_class(self.fname) if(self.fform.footer_class) else None;
        else:
            pass;
        self.ftype= self.fform.ftype if(isinstance(self.fform, FileFormat)) else None;
 ### INIT END ###

    def setname(self, fname=None, ext_delim=None):
        """Set or change the name of the file

Parameters
----------
    fname : str
        Name of the file
    ext_delim : str OR int
        Separation character for the extension or size of the extension.

""";
        if(fname is None): fname='';
        if(not isinstance(fname,str)): raise TypeError("GenFile: wrong type for `fname`. It must be a string. <{}>".format(fname.__class__));
        if(fname and fname != fname.strip()): raise ValueError("GenFile: `fname` starts or finishs with spaces.");
        self.fname=fname;
        if(not fname): return;
        self.ext_delim=ext_delim if(ext_delim is not None) else '.';
        if(isinstance(self.ext_delim,str)):
            tmpl=self.fname.rsplit(self.ext_delim,1);
            if(len(tmpl)==1): tmpl.append('');
            (self.basename,self.ext)=tuple(tmpl);
        elif(isinstance(self.ext_delim,int)):
            self.basename=self.fname[:-self.ext_delim];
            self.ext=self.fname[-self.ext_delim:];
        else: raise TypeError("GenFile: wrong value for `ext_delim`: not str or int.");

    def __enter__(self):
        return self;
    def __exit__(self, exc_type, exc_value, exc_tb):
        if(exc_type!=None):
            return False;
        else:
            pass;

    def writeheader(self, output=None, overwrite=False):
        """Write the header in the file

Parameters
----------
    output : str, io.TextIOWrapper
        Name of the file where to write the header, or object with write attribute. Default None is the internal filename.
    overwrite : bool
        To overwrite an existing file
""";
        if(not self.header or not hasattr(self.header, 'print')): raise SkZpipeError("There is no Hedaer defined.", exclocus='GenFile');
        if(output is None): output=self.fname;
        if(isinstance(output,str)):
            if(os.path.exists(output) and not overwrite):  raise SkZpipeError("Cannot write header: File {name} exist and `overwrite` is set to {flag}".format(name=output, flag=overwrite), exclocus='GenFile');
            with open(output, 'w') as fout:
                fout.write(self.header.print());
        elif(hasattr(output, 'write')):
            output.write(self.header.print());

 ####
    def check_file(self, minline=None, namemaxlen=None, raisexc=True):
        """Check if the file exists or it has enough lines

Parameters
----------
    minline : int
        Minimum number of lines (deafault DAO_Par['headerlen']+1).
    namemaxlen : int
        Maximum length of filenames (default DAO_Par['namemaxlen']).
    raisexc : bool
        Flag to set if raise an exception or just return an error value.

Return
------
    check : int
        0 if the file has passed the checks.
        If the checks fail and raisexc is True, an exception is raised.
        Otherwise, it is returned:
          255 if a filename is longer than the maximum namelength, 
           -1 if a file has less lines than the minimum. 
            1 if None is passed as filename.
""";
        _name_='GenFile.check_file';
        from ....functions  import check_file

        if(minline is None): minline=self.header.length+1;
        ret=check_file(files=[self.fname], minline=minline, namemaxlen=namemaxlen, raisexc=raisexc);
        return ret[1] if(ret) else 0;




###############################################################################

 #PSF
class PsfFile(GenFile):
    """Class for a generic file that describe a point-spread function.

Parameters
----------
    fname : str or PsfFile
        Filename
    data : dict or PsfFile
        Data of the psf as PsfFile or dictionary (to update the object; keys: 'funct', 'xhwhm', 'yhwhm',  'mag1', 'height', 'npar', 'par').
    fileformat : callable
        Function to read a stream, extract data and return them as a dictionary

Attributes
----------
    funct : str
        Identifier of the PSF function
    xhwhm : float
        Half width half maximum along X axis
    yhwhm : float 
        Half width half maximum along Y axis
    mag1 : float 
        Instrumental magnitude corresponding to psf of unit normalization
    height : float 
        Central height
    npar : int 
        Number of parameters of the function
    par : list of float
        List of the parameters of the function
""";
    funct='';
    xhwhm=0;
    yhwhm=0;
    height=0;
    mag1=99;
    npar=0;
    par=[];
    _dtype_formats=(str, float, float, float, float, int); 
  
    def __init__(self, fname=None, data=None, fileformat=None):
        """PsfFile object for file containing PSF description.
  
  """;
        _name_='PsfFile object';
        if(isinstance(fname,PsfFile)):
            if(data is None):
                data=fname;
                fname=data.fname;
            else: raise SkZpipeError("If `fname` is a PsfFile, `data` cannot contain data", exclocus=_name_);
        super().__init__(fname=fname); #=>GenFile
        if(isinstance(data,dict)):  
            self.__dict__.update(copy.deepcopy(data))
        elif(isinstance(data,PsfFile)):  
            self.__dict__.update(copy.deepcopy(data.__dict__))
        elif(data is None):
            if(callable(fileformat)):
                with open(self.fname) as fpsf:
                    self.__dict__.update(fileformat(fpsf));
            else:
                self.funct, self.npar, self.par, self.xhwhm, self.yhwhm,  self.mag1, self.height= '', 0, [], 0, 0, 0, 99;

  ###
    def __str__(self):
        txt="{:} {:.6f} {:.6f} {:.2f} {:.4f} {:d}\n".format(self.funct, self.xhwhm, self.yhwhm, self.cheight, self.mag1, self.npar);
        for ii in range(self.npar):
            txt+=" {:.6e}".format(self.par[ii]);
        return txt;
    def dict(self):
        return {'funct':self.funct, 'xhwhm':self.xhwhm, 'yhwhm':self.yhwhm,  'mag1':self.mag1, 'height':self.height, 'npar':self.npar, 'par':self.par};

###############################################################################
###############################################################################

 #PHOTO
class PhotoFile(GenFile):
    """Class for a photometric file.

Parameters
---------
    fname : str
        Filename
    ftype : PhotoFileFormat
        Format of the PhotoFile
    header : PhotoFileHeader
        Header of the file
    footer : PhotoFileHeader
        Footer of the file
    FormatInit : dict
        Dictionary with initialization parameteres
    image : str
        Filename of the image that generated the photometric file.
    coordtype : str
        Type of the coordinate system associated with the data.
          'pxl' : position in pixels
          'deg'
 
Attributes
----------
    srcL : list
        List of sources. Each element is a Source object (according to own PhotoFileFormat).
    srcT : numpy.ndarray or astropy.table.Table or panda.Table
        Table with data of the sources.
    nsrc : int
        Number of sources
    image : str
        Filename of the image that generated the photometric file.

Methods
-------

""";
    srcL=[];     #List of sources
    srcT=numpy.array([], ndmin=2);     #Array of sources
    syncListTab=False;
    nsrc=None
    image=None  #filename of the image
  
    def __init__(self, fname=None, ftype=None, header=None, footer=None, FormatInit=None, image=None):
        """Object to manage a photometric file


""";
        _name_="PhotoFile object";
        if(isinstance(fname, PhotoFile)):
            if(ftype is None):
                ftype=fname;
                fname=ftype.fname;
            else: raise SkZpipeError("If `fname` is a PhotoFile, `ftype` cannot contain data", exclocus=_name_);
        super().__init__(fname=fname, FormatInit=FormatInit);  #=> GenFile
        self.srcL = [];  #List of sources
        self.srcT=numpy.array([], ndmin=2);     #Array of sources
        self.nsrc=-1;   #number of sources
        if(not isinstance(self.fform, PhotoFileFormat)): self.fform=PhotoFileFormatD[None].copy();

        if(isinstance(ftype, PhotoFile)):
            self.fform=PhotoFileFormat(ftype=ftype.fform);
            if(not isinstance(header, PhotoFileHeader)): header=ftype.header.copy();           #ftype.fform.header_class(self.fname);
            if(not self.fname): self.fname = ftype.fname;
            self.srcL, self.srcT = copy.deepcopy(ftype.srcL), ftype.srcT.copy();
            ftype=ftype.fform.ftype;
        if(ftype in SourceTypeD): self.sourcetype=SourceTypeD[ftype];
        if(isinstance(header,FileHeader)): self.header=header.copy();

        if(image is None):
            if(os.path.exists(self.basename+bpar.SkZp_Par['fitsextension'])): self.image=self.basename+bpar.SkZp_Par['fitsextension'];
        else:
            if(isinstance(image, str)): self.image=image;
            else: raise TypeError(_name_+": `image` must be a str or None");

  ###
    def __enter__(self):
        return self;
    def __exit__(self, exc_type, exc_value, exc_tb):
        if(exc_type!=None):
            return False;
        else:
            pass;


    def read_astable(self, data_table=None, struct=True):
        """Store the file as an array/table.

Parameters
----------
    data_table : object numpy.array compatible
        2D-'Array' with the data to be stored
    struct : bool
        ??? For structured array?

Return
------
    shape : tuple of 2 int
        Shape of the table/array
""";
        _name_='read_astable'; 
    
        if(data_table is not None):
            self.srcT=numpy.array(data_table, dtype=float)  ##  dtype if(False and struct) else float);
        else:
            dtype=numpy.dtype({'names':self.sourcetype._dtype_names[0], 'formats':self.sourcetype._dtype_formats[0]}) if(self.sourcetype._dtype_nlines==1) else None;
            comments=self.fform.comments
            delimiter=self.sourcetype._dtype_delimiter
            converters=None
            if(not self.header): raise SkZpipeError("The header is not define. The file not exist at the creation.", exclocus="PhotoFile");
            skip_header=self.header.length
            skip_footer=self.footer.length if(self.footer) else 0
            usecols=None; unpack=False 
            self.srcT=numpy.genfromtxt(fname=self.fname, dtype=dtype, comments=comments, delimiter=delimiter, converters=converters, skip_header=skip_header, skip_footer=skip_footer, usecols=usecols, unpack=unpack);
        self.nsrc=len(self.srcT);
        syncListTab=True;
        return self.srcT.shape;

    def read_assources(self):
        """Store the file as a list of sources.

Return
------
    nsrc : int
        Lenght of the list
""";
        with open(self.fname) as fin:
            if(not self.header): raise SkZpipeError("The header is not define. The file not exist at the creation.", exclocus="PhotoFile");
            self.srcL=[];
            for ii in range(self.header.length):
                fin.readline();
            for line in fin:
                for ii in range(self.sourcetype._dtype_nlines-1):
                    line+=fin.readline();
                self.srcL.append(self.sourcetype(line));
            self.nsrc=len(self.srcL);
        return self.nsrc;

    def read(self, mode='list'):
        """Load the file as sources (it calls read_assources/read_astable).

Parameters
----------
    mode : str
        Mode of the reading: 'list' (default) to read as a list of sources; 'table' to read as a numpy table.

""";
        _name_='PhotoFile.read';
        if(not isinstance(mode, str)): raise TypeError(_name_+": 'mode' must be a str ('list' or 'table')");
        mode=mode.lower();
        if(mode not in ('list','table')): raise ValueError(_name_+": 'mode' must be a str ('list' or 'table')");
        if(mode == 'list'): self.read_assources();
        else: self.read_astable();

###
    def sources2table(self):
        """Transform the data stored as a list of sources to an numpy table.
""";
        self.srcT=numpy.array(self.srcL[0].list(), ndmin=2, dtype=numpy.float);
        for src in self.srcL[1:]:
            numpy.vstack([self.srcT, src.list()])

    def table2sources(self):
        """Transform the data stored as an numpy table to a list of sources.
""";
        self.srcL=[];
        for src in self.srcT:
            self.srcL.append(self.sourcetype(list(src)))

###
    def sourcesappend(self, src=None):
        """Append a source to the list of sources.

Parameters
----------
    src : Source class
        Object with the source to add.

""";
        self.srcL.append(self.sourcetype(src));
        self.nsrc+=1

    def tableappend(self, src=None):
        """Append a source to the table of sources.

Parameters
----------
    src : list
        List with the source data to add.

""";
        if(isinstance(src, bclasses.IdXY)): src=src.list();
        numpy.vstack([self.srcT, src]);
        self.nsrc+=1

###
    def writesources(self, fname=None, mode='a'):
        """Write a PhotoFile from the internal list of sources

Parameters
----------
    fname : str, optional
        Name of the file. Default attribute `fname`.
    mode : str
        Mode for the writing (as for open function): 'a' to add the sources to an existing file; 'w' to write the sources overwriting  the file.
""";
        if(len(self.srcL)==0 and self.srcT.size==0): raise ValueError("PhotoFile {name}: wrong internal source list <{llen}><{asize}>".format(name=self.fname, llen=len(self.srcL), asize=self.srcT.size));
        if(not fname): fname=self.fname;
        if(not fname): raise ValueError("PhotoFile: no `fname`");
        with open(fname, mode) as fout:
            for src in self.srcL:
                fout.write(src.print());

  ###
    def writefile(self, fname=None, overwrite=False):
        """Write a PhotoFile
Parameters
----------
    fname : str, optional
        Name of the file. Default attribute `fname`.
""";
        if(not fname): fname=self.fname;
        if(not fname): raise ValueError("PhotoFile: no 'fname'");
        self.writeheader(output=fname, overwrite=overwrite);
        self.writesources(fname=fname, mode='a');

#####
    def stat(self, mode='table', cols=None, perc=None):
        """Calculate statistics for columns of a PhotoFile.

Parameters
----------
    mode : str, optional
        Mode for the calculation: using source list ('source'), or numpy table ('table').
    cols : list, None, optional using table mode
        List of columns for which to calculate statistics (1 for the first column, 2 for the second one, ...). None for all.
    perc : list, None, optional using table mode
        List of integer with additional percentiles to calculate

Return
------
    List of a dict for each column with: 'mean', 'min', 'max', 'median', 'perc##'=percentile:10, 25, 75, 90



""";
        _name_='PhotoFile.stat()'


        xmax, ymax=-1e6, -1e6;  
        xmin, ymin=+1e6, +1e6;  
        if(mode=='table'  and self.srcT.size==0): self.read_astable();
        if(mode=='source' and not self.srcL): self.read_assources();

        if(self.srcL):  #Using SOURCE mode
            if(hasattr(self.srcL[0], 'mag')):
                hasmag=True;
                mmax, emax=0,0;
                mmin,emin=99,10;
            else:
                hasmag=False;
                mmin,mmax, emin,emax=None,None, None,None;
            if(hasattr(self.srcL[0], 'sky')):
                hassky=True;
                smax=0;
                smin=1.e6;
            else:
                hassky=False;
                smin,smax=None,None;
            for src in self.srcL:
                if(xmin>src.x): xmin=src.x;
                if(xmax<src.x): xmax=src.x;
                if(ymin>src.y): ymin=src.y;
                if(ymax<src.y): ymax=src.y;
                if(hasmag and -90<src.mag<90):
                    if(mmin>src.mag): mmin=src.mag;
                    if(mmax<src.mag): mmax=src.mag;
                    if(src.emag>0):
                        if(emin>src.emag): emin=src.emag;
                        if(emax<src.emag): emax=src.emag;
                if(hassky):
                    if(smin>src.sky): smin=src.sky;
                    if(smax<src.sky): smax=src.sky;
            return {'x':(xmin,xmax), 'y':(ymin,ymax), 'mag':(mmin,mmax), 'emag':(emin,emax), 'sky':(smin,smax) }
        else:  #Using ARRAY mode
            outstat=[];
            if(cols):
                if(not isinstance(cols,list)): raise TypeError(_name_+": 'cols' must be None or a list of integer");
                for ii,col in enumerate(cols):
                    cols[ii]=int(col)-1;
            if(perc):
                if(not isinstance(perc,list)): raise TypeError(_name_+": 'perc' must be None or a list of integer");
                for ii,prc in enumerate(perc):
                    perc[ii]=int(prc);
            else: perc=[];
            icol= cols if(cols) else range(self.srcT.shape[0]);
            for ii in icol:
                outstat.append( {'mean':round(self.srcT[ii].mean(),4), '#n': self.srcT[ii].size, 'min':round(self.srcT[ii].min(),4), 'max':round(self.srcT[ii].max(),4), 'std':round(self.srcT[ii].std(),6), 'median':round(numpy.median(self.srcT[ii]),4), 'perc10':round(numpy.percentile(self.srcT[ii], 10),4), 'perc25':round(numpy.percentile(self.srcT[ii], 25),4), 'perc75':round(numpy.percentile(self.srcT[ii], 75),4), 'perc90':round(numpy.percentile(self.srcT[ii], 90),4) } );
                for prc in perc:
                    outstat[-1]['perc{}'.format(prc)]=round(numpy.percentile(self.srcT[ii], prc),4);
            return outstat;

#####
    def magshift(self, magshift=0, error=0):
        """Apply a shift in magnitude to all the sources and sum quadratically the errors

Parameters
----------
    magshift : float
        Magnitude shift that will be added to all the sources
    error : float
        Error of the shift. It is added quadratically to the magnitude error of the sources.
""";
        if(self.srcL):
            for src in self.srcL:
                src.mag+=magshift;
                if(error): src.emag=math.sqrt(src.emag**2+error**2);
        elif(self.srcT.size):
            raise SkZpipeWarning("Not yet implemented to operate on table of photometric sources")
        else:
            raise SkZpipeError("No data loaded!", exclocus='PhotoFile');
#####
    def coordArr(self):
        """Return a Numpy array with the point coordinates"""
        return numpy.array([src.coordL() for src in self.srcL], dtype=numpy.float)

#####
    def wcs_vertex(self, image=None, wcsobj=None):
        """Transform the coordinates of the source array from pixel to world system. Additionally, it can trasform the world coordinates in a relative position in arcsec along the world axes, providing the coordinates of the origin.

Parameters
----------
    image : str
        Name of the image containing the WCS in the header (First to be check and use).
    wcsobj : astropy.wcs.WCS
        Object with the trasformation to use (if 'image' is not defined).
    wcsmode : str
        Mode to calculate the pix2world trasformation. [Not yet implemented]

""";
        _name_='PhotoFile.wcs_vertex';
        if(image is not None and isinstance(image, str)): raise TypeError(_name_+": 'image' must be a string");
        if(wcsobj is not None and isinstance(wcsobj, wcs.WCS)): raise TypeError(_name_+": 'wcsobj' must be a astropy.wcs.WCS");

        if(image is None and wcsobj is None):
            if(self.image): image=self.image;
            else: raise TypeError(_name_+": 'image' and 'wcsobj' cannot be both None.");
        if(wcsobj is None):
            if(os.path.exists(image)):
                with pyfits.open(image) as hdul:
                    wcsobj=wcs.WCS(hdul[0].header);
            else:  raise ValueError(_name_+": Impossible to determine the WCS");
        if(not isinstance(wcsobj, wcs.WCS)): raise TypeError(_name_+": 'wcsobj' must be a WCS object.");


        vertex = numpy.array([[0, 0], [self.header.nx, 0], [self.header.nx, self.header.ny], [0, self.header.ny]], numpy.float_); #4 points in frame (0,0) (NX,0), (NX,NY), (0,NY)
        return  wcsobj.wcs_pix2world(vertex, 1);

    def wcs_pix2world(self, image=None, wcsobj=None, wcsmode=None, origin=None, scale=1, posmode=None):
        """Transform the coordinates of the source array from pixel to world system. Additionally, it can trasform the world coordinates in a relative position in arcsec along the world axes, providing the coordinates of the origin.

Parameters
----------
    image : str
        Name of the image containing the WCS in the header (First to be check and use).
    wcsobj : astropy.wcs.WCS
        Object with the trasformation to use (if 'image' is not defined).
    wcsmode : str
        Mode to calculate the pix2world trasformation. [Not yet implemented]
    origin : tuple of floats
        Coordinates in degree of the origin to calculate the relative position.
    scale : float
        Scale [1/arcsec] of the relative positions.
    posmode : str
        Mode to calculate the relative positions.
         'delta' : delta(ra)*cos(dec); delta(dec)
         'delta0' : delta(ra)*cos(dec0); delta(dec)

""";
        _name_='PhotoFile.wcs_pix2world'
        if(image is not None and isinstance(image, str)): raise TypeError(_name_+": 'image' must be a string");
        if(wcsobj is not None and isinstance(wcsobj, wcs.WCS)): raise TypeError(_name_+": 'wcsobj' must be a astropy.wcs.WCS");
        if(wcsmode is not None and isinstance(wcsmode, str)): raise TypeError(_name_+": 'wcsmode' must be a string");
        if(origin is not None and isinstance(origin, tuple)): raise TypeError(_name_+": 'origin' must be a tuple of floats");
        if(posmode is not None and isinstance(posmode, str)): raise TypeError(_name_+": 'posmode' must be a string");
        if(origin is not None): origin=tuple(float(x) for x in origin);
        if(scale is not None): scale=float(scale);
        if(wcsmode is not None): wcsmode=wcsmode.lower();
        if(posmode is not None): posmode=posmode.lower();
  
        xpos,ypos=self.fform.src_class._dtype_names.index('x'), self.fform.src_class._dtype_names.index('y') ;
        if(image is None and wcsobj is None):
            if(self.image): image=self.image;
            else: raise SkZpipeError(f"`image` and `wcsobj` cannot be both None.", exclocus=_name_);
        if(wcsobj is None):
            if(os.path.exists(image)):
                with pyfits.open(image) as hdul:
                    wcsobj=wcs.WCS(hdul[0].header);
            else:  raise ValueError(_name_+": Impossible to determine the WCS");
        if(not isinstance(wcsobj, wcs.WCS)): raise TypeError(_name_+": 'wcsobj' must be a WCS object.");

        if(self.srcT.size==0): self.read_astable();
        radec = wcsobj.wcs_pix2world(self.srcT[:,(xpos,ypos)], 1);
        if(origin is not None):
            if(isinstance(origin, tuple) and len(origin)==2):
                if(posmode.startswith('delta')):
                    radec[:,0]-=origin[0];
                    if(posmode=='delta0'):
                        radec[:,0]*=math.cos(math.radians(origin[1]));
                    else:
                        for ii in range(radec.shape[0]):
                            radec[ii,0]*=math.cos(math.radians(radec[ii,1]));
                    radec[:,1]-=origin[1];
                    radec[:,0]*=3600.*scale;
                    radec[:,1]*=3600.*scale;
            else: raise ValueError(_name_+": Wrong value for 'origin'");
        self.srcT[:,(xpos,ypos)]=radec;

        vertex = numpy.array([[0, 0], [self.header.nx, 0], [self.header.nx, self.header.ny], [0, self.header.ny]], numpy.float_); #4 points in frame (0,0) (NX,0), (NX,NY), (0,NY)
        return  wcsobj.wcs_pix2world(vertex, 1);

    def wcs_world2pix(self, image=None, wcsobj=None, wcsmode=None, origin=None, scale=1, posmode=None):
        """Transform the coordinates of the source array from world system to pixel. If the world coordinates are in the form of relative position along the world axes, providing the coordinates of the origin it previously restore them in ra,dec format.

Parameters
----------
    image : str
        Name of the image containing the WCS
    wcsobj : astropy.wcs.WCS
        Object with the trasformation to use
    wcsmode : str
        Mode to calculate the world2pix trasformation. [Not yet implemented]
    origin : tuple of floats
        Coordinates in degree of the origin of the relative position.
    scale : float
        Scale [1/arcsec] of the relative positions.
    posmode : str
        Mode to calculate the relative positions.
         'delta' : delta(ra)*cos(dec); delta(dec)
         'delta0' : delta(ra)*cos(dec0); delta(dec)

""";
        _name_='PhotoFile.wcs_world2pix';
        if(image is not None and isinstance(image, str)): raise TypeError(_name_+": 'image' must be a string");
        if(wcsobj is not None and isinstance(wcsobj, wcs.WCS)): raise TypeError(_name_+": 'wcsobj' must be a astropy.wcs.WCS");
        if(wcsmode is not None and isinstance(wcsmode, str)): raise TypeError(_name_+": 'wcsmode' must be a string");
        if(origin is not None and isinstance(origin, tuple)): raise TypeError(_name_+": 'origin' must be a tuple of floats");
        if(posmode is not None and isinstance(posmode, str)): raise TypeError(_name_+": 'posmode' must be a string");

        if(origin is not None): origin=tuple(float(x) for x in origin);
        if(scale is not None): scale=float(scale);
        if(wcsmode is not None): wcsmode=wcsmode.lower();
        if(posmode is not None): posmode=posmode.lower();

        xpos,ypos=self.fform.src_class._dtype_names.index('x'), self.fform.src_class._dtype_names.index('y') ;
        if(image is None and wcsobj is None): image=self.basename+bpar.SkZp_Par['fitsextension'];
    
        if(wcsobj is None):
            if(os.path.exists(image)):
                with pyfits.open(image) as hdul:
                    wcsobj=wcs.WCS(hdul[0].header);
            else:  raise TypeError(_name_+": 'wcsobj' is None and 'image' <{image}> doesn't exist.".format(image=image));
        if(not isinstance(wcsobj, wcs.WCS)): raise TypeError(_name_+": 'wcsobj' must be a WCS object.");

        if(self.srcT.size==0): self.read_astable();
        radec=self.srcT[:,(xpos,ypos)];
        if(origin is not None):
            if(isinstance() and len(origin)==2):
                if(posmode.startswith('delta')):
                    radec[:,0]/=3600.*scale;
                    radec[:,1]/=3600.*scale;
                    radec[:,1]+=origin[1];
                    if(posmode=='delta0'):
                        radec[:,0]/=math.cos(math.radians(origin[1]));
                    else:
                        for ii in range(radec.shape[0]):
                            radec[ii,0]/=math.cos(math.radians(radec[ii,1]));
                    radec[:,0]+=origin[0];
            else: raise ValueError(_name_+": Wrong value for 'origin'");
        self.srcT[:,(xpos,ypos)]=wcsobj.wcs_world2pix(radec, 1);
    

  ###
    def select(self, area=None, mode=False, store=None):
        """Select sources in the given areas and then reject or keep just them.

Parameters
----------
    area : dict
        Dictionary with the data areas (same format as 'badpixelarea' database).
    mode : str or bool
        Mode for the selection:
          'keep'/True to keep the sources inside the data areas
          'reject'/False to reject the sources inside the data areas
        (Actually, just the first two characters are read.)
    store : str or None
        Name of the file where to store the rejected sources.
Return
------
    out : tuple of ints
        Tuple with the number of kept sources and the number of rejected sources.

""";
        _name_='Photofile.select'
  
        if(area is None): return (self.nsrc, 0);
        if(not isinstance(area,dict)): raise TypeError(_name_+": `area` must be a dict or None");
        if(not area): return (self.nsrc, 0);
        if(not isinstance(mode, (str,bool))): raise TypeError(_name_+": `mode` must be a str or bool");
        if(not isinstance(store, str)): raise TypeError(_name_+": `store` must be a str or bool");
        if(isinstance(mode, str)):
            mode=mode.lower();
            if(mode.startswith('ke')): mode=True;
            elif(mode.startswith('re')): mode=False;
            else: raise ValueError(_name_+": `mode` as string must be 'keep' or 'reject'");
  
        if(self.srcL):
            tmpl=self.srcL;
            self.srcL,rejL=[],[];
            for src in tmpl:
                inside=False;
                for ar in area:
                    if(ar['type']=='box'):
                        if(abs(src.x-ar['x'])<=ar['wx'] and abs(src.y-ar['y'])<=ar['wy']): inside=True;
                    elif(ar['type']=='ellipse'):
                        if(((src.x-ar['x'])/ar['wx'])**2 + ((src.y-ar['y'])/ar['wy'])**2 <=1): inside=True;
                    elif(ar['type']=='frame'):
                        if(src.x<ar['wx'] or src.y<ar['wy']): inside=True;
                    if(inside): break;
                if(inside==mode): self.srcL.append(src);
                else: rejL.append(src);
            self.nsrc=len(self.srcL);
            nrej=len(self.rejL);
            if(store):
                rejF=self.copy();
                rejF.setname(store);
                rejF.srcL=rejL;
                rejF.writefile(overwrite=True);
            return (self.nsrc, nrej);
        raise SkZpipeError(f"selection working only with source list", exclocus=_name_)

#####
    def cleaning(self, setting=None, copy=True, cleanfile=None, rejfile=None):
        """Reject sources according to given paramenters.

Parameters
----------
    setting : dict of dict
        Dictionary of dictionaries with the setting for the source rejection.
        The key is the name of the attribute to whose values the cut will be applied (e.g. 'mag', 'emag', 'chi2'),
        except 'area' to apply a cut using the coordinates.
        The keys for the attribute's dictionaries can be:
          'max' : float
              Maximum permitted value. Option available for attribute with only no-negative value (as 'chi2', 'niter', 'emag')
          'range' : 2-element tuple
              Tuple of 2 values (min,max) with the range of values to keep.
          'out' : None or str
              A filename to store the sources rejected.
              None to store them as defined by `rejfile`.
              An empty string ('') to not store them.
        Specific keys for 'area' (syntax similar to ds9 regions):
          'frame' : int or list/tuple of 1,2,4 values
              List/tuple of the 4 width of the external frame that has to be excluded:
              (bottom, right, top, left) or (vertical, horizontal) or constant value.
          'box' : tuple or list of tuples
              Tuple with central position and full width and height (x, y, width, height)
              The inner (<=) part is rejected
          'nbox' : tuple or list of tuples
              Tuple with central position and full width and height (x, y, width, height)
              The outer (>) part is rejected (the opposite of 'box')
          'ellipse' : tuple or list of tuples
              Tuple with central position and x- and y- semiaxis (x, y, rx, ry)
              The inner (<=) part is rejected
          'nellipse' : tuple or list of tuples
              Tuple with central position and x- and y- semiaxis (x, y, rx, ry)
              The outer (>) part is rejected (the opposite of 'ellipse')
        Specific keys for 'emag':
          'sigma' : float
              Value for a sigma-clipping cut using a fit of the maximum of the frequencies in (mag;err) plane.
    copy : bool
        If true (default), it is created a new PhotoFile object with the kept sources. Otherwise the original is modified.
    cleanfile : str
        Name of the file with kept sources. It is set (if not None), then `copy` will be set to True (to create a written copy). Default the filename +'-Kp'
    rejfile : str
        Name of the file with rejected sources, '-' to not save the rejected sources. Default the filename +'-Rj'

Return
------
   out : tuple of 2 int
        Tuple with number of kept sources and rejected sources.
""";
        _name_='PhotoFile.cleaning';
        if(setting and not isinstance(setting, dict)): raise TypeError(_name_+": `setting` must be a dictionary or None");

        if(not isinstance(copy, bool)): raise TypeError(_name_+": `copy` must be a bool");
        if(cleanfile is not None and not isinstance(cleanfile, str)): raise TypeError(_name_+": `cleanfile` must be a string or None")
        if(cleanfile is None): cleanfile=self.fname+'-Kp'
        else: #cleanfile is set: you want to create a written copy
            copy=True

        if(rejfile is not None and not isinstance(rejfile, str)): raise TypeError(_name_+": `rejfile` must be a string or None");
        if(rejfile is None): rejfile=self.fname+'-Rj';

        for attr in setting:
            if( not isinstance(setting[attr], dict)): raise TypeError(_name_+": '{key}' in `setting` must be a dictionary <{var}>".format(key=attr, var=setting[attr]));
            for key in setting[attr]:
                if(key=='max'):
                    if(not isinstance(setting[attr][key], (float,int))):  raise TypeError(_name_+": '{key}' in `setting`:'{attr}' must be a number <{var}>".format(key=key, attr=attr, var=setting[attr][key]));
                if(key=='range'):
                    if(not isinstance(setting[attr][key], (tuple,list))):  raise TypeError(_name_+": '{key}' in `setting`:'{attr}' must be a tuple/list of 2 numbers <{var}>".format(key=key, attr=attr, var=setting[attr][key]));
                    if(len(setting[attr][key])!=2):  raise TypeError(_name_+": '{key}' in `setting`:'{attr}' must be a tuple/list of 2 numbers <{var}>".format(key=key, attr=attr, var=setting[attr][key]));
                    for val in setting[attr][key]: 
                        if(not isinstance(val, (float,int))):  raise TypeError(_name_+": '{key}' in `setting`:'{attr}' must be a tuple/list of 2 numbers <{var}>".format(key=key, attr=attr, var=setting[attr][key]));
                if(key=='out'):
                    if(setting[attr][key] is not None and not isinstance(setting[attr][key], str)):  raise TypeError(_name_+": '{key}' in `setting`:'{attr}' must be None or a str <{var}>".format(key=key, attr=attr, var=setting[attr][key]));
            setting[attr].setdefault('out');

        if(self.nsrc<=0): self.read_assources();
        FsrcL, RsrcL=self.srcL, [];

  ##%%%%##
        def _StoreRej(out=None, rejL=None):
            if(out is None): RsrcL.extend(rejL)
            elif(out):
                if(not out and rejL):
                    with PhotoFile(out, self) as outPF:
                        outPF.srcL=rejL;
                        outPF.nsrc=len(rejL);
                        outPF.writefile(overwrite=True);
  ##%%%%##
          

   
        if(setting.get('area')):
            out=setting['area'].get('out');
            rsrcL=[];
            if('frame' in setting['area']):
                try:
                    frame=copy.copy(setting['area']['frame']);
                except AttributeError:
                    frame=setting['area']['frame'];
                if(not isinstance(frame, (list,tuple))): frame=[frame];
                if(len(frame)==1): frame*=4;
                elif(len(frame)==2): frame*=2;
                else: raise SkZpipeError("'frame' in 'area' of `setting` must contain 1, 2 or 4 values <{var}>",exclocus=_name_);
                ksrcL=[];
                for src in FsrcL:
                    if(frame[0]<src.y<self.header.ny-frame[2] and frame[3]<src.x<self.header.nx-frame[1]): ksrcL.append(src);
                    else: rsrcL.append(src);
                FsrcL=ksrcL;

            if('box' in setting['area']):
                try:
                    boxL=copy.copy(setting['area']['box']);
                except AttributeError:
                    boxL=setting['area']['box'];
                if(not isinstance(boxL, list)): boxL=[boxL];
                for box in boxL:
                    if(not isinstance(box, tuple)):  raise TypeError(_name_+": 'box' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=box));
                    blen=len(box);
                    if(blen not in (3,4)): raise ValueError(_name_+": 'box' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=box));
                    if(blen==3): box+=(box[2],);
                    ksrcL=[];
                    for src in FsrcL:
                        if(abs(src.x-box[0])<=0.5*box[2] and abs(src.y-box[1])<0.5*box[3]): rsrcL.append(src);
                        else: ksrcL.append(src);
                    FsrcL=ksrcL;

            if('nbox' in setting['area']):
                try:
                    boxL=copy.copy(setting['area']['nbox']);
                except AttributeError:
                    boxL=setting['area']['nbox'];
                if(not isinstance(boxL, list)): boxL=[boxL];
                for box in boxL:
                    if(not isinstance(box, tuple)):  raise TypeError(_name_+": 'nbox' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=box));
                    blen=len(box);
                    if(blen not in (3,4)): raise ValueError(_name_+": 'nbox' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=box));
                    if(blen==3): box+=(box[2],);
                    box=box[:2]+(box[2]*.5,box[3]*.5); #Redefined with half
                    ksrcL=[];
                    for src in FsrcL:
                        if(abs(src.x-box[0])<=box[2] and abs(src.y-box[1])<=box[3]): ksrcL.append(src);
                        else: rsrcL.append(src);
                    FsrcL=ksrcL;

            if('ellipse' in setting['area']):
                try:
                    ellipseL=copy.copy(setting['area']['ellipse']);
                except AttributeError:
                    ellipseL=setting['area']['ellipse'];
                if(not isinstance(ellipseL, list)): ellipseL=[ellipseL];
                for ellipse in ellipseL:
                    if(not isinstance(ellipse, tuple)):  raise TypeError(_name_+": 'ellipse' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=ellipse));
                    blen=len(ellipse);
                    if(blen not in (3,4)): raise ValueError(_name_+": 'ellipse' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=ellipse));
                    if(blen==3): ellipse+=(ellipse[2],);
                    ellipse=ellipse[:2]+(ellipse[2]**2,ellipse[3]**2);
                    ksrcL=[];
                    for src in FsrcL:
                        if((src.x-ellipse[0])**2/ellipse[2] + (src.y-ellipse[1])**2/ellipse[3] <=1): rsrcL.append(src);
                        else: ksrcL.append(src);
                    FsrcL=ksrcL;

            if('nellipse' in setting['area']):
                try:
                    ellipseL=copy.copy(setting['area']['nellipse']);
                except AttributeError:
                    ellipseL=setting['area']['nellipse'];
                if(not isinstance(ellipseL, list)): ellipseL=[ellipseL];
                for ellipse in ellipseL:
                    if(not isinstance(ellipse, tuple)):  raise TypeError(_name_+": 'nellipse' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=ellipse));
                    blen=len(ellipse);
                    if(blen not in (3,4)): raise ValueError(_name_+": 'nellipse' in `setting`:'area' must be a tuple of 3/4 values <{var}>".format(var=ellipse));
                    if(blen==3): ellipse+=(ellipse[2],);
                    ellipse=ellipse[:2]+(ellipse[2]**2,ellipse[3]**2);
                    ksrcL=[];
                    for src in FsrcL:
                        if((src.x-ellipse[0])**2/ellipse[2] + (src.y-ellipse[1])**2/ellipse[3] <=1): ksrcL.append(src);
                        else: rsrcL.append(src);
                    FsrcL=ksrcL;

            _StoreRej(out=out, rejL=rsrcL);
          
        if(setting.get('mag')):
            out=setting['mag'].get('out');
            if('range' in setting['mag']):
                xmin,xmax=setting['mag']['range']
            elif('max' in setting['mag']):
                xmin,xmax=-99,setting['mag']['max']
            ksrcL,rsrcL=[],[];
            for src in FsrcL:
                if(xmin<=src.mag<=xmax): ksrcL.append(src);
                else: RsrcL.append(src);

            FsrcL=ksrcL;
            _StoreRej(out=out, rejL=rsrcL);

        if(setting.get('chi2')):
            out=setting['chi2'].get('out');
            if(not hasattr(self.srcL[0], 'chi2')): raise SkZpipeError("The sources have no `chi2` attribute", exclocus=_name_);
            if(setting['chi2']['max']<0): raise TypeError(_name_+": 'chi2' in `setting` must be a positive number <{var}>".format(var=setting['chi2']['max']));
            xmax=setting['chi2']['max'];
            ksrcL,rsrcL=[],[];
            for src in FsrcL:
                if(src.chi2<=xmax): ksrcL.append(src);
                else: RsrcL.append(src);

            FsrcL=ksrcL;
            _StoreRej(out=out, rejL=rsrcL);

        if(setting.get('sharp')):
            out=setting['sharp'].get('out');
            if(not hasattr(self.srcL[0], 'sharp')): raise SkZpipeError("The sources have no `sharp` attribute", exclocus=_name_);
            xmin,xmax=setting['sharp']['range'];
            ksrcL,rsrcL=[],[];
            for src in FsrcL:
                if(xmin<=src.sharp<=xmax): ksrcL.append(src);
                else: RsrcL.append(src);

            FsrcL=ksrcL;
            _StoreRej(out=out, rejL=rsrcL);

        if(setting.get('sky')):
            out=setting['sky'].get('out');
            if(not hasattr(self.srcL[0], 'sky')): raise SkZpipeError("The sources have no `sky` attribute", exclocus=_name_);
            xmin,xmax=setting['sky']['range'];
            ksrcL,rsrcL=[],[];
            for src in FsrcL:
                if(xmin<=src.sky<=xmax): ksrcL.append(src);
                else: RsrcL.append(src);

            FsrcL=ksrcL;
            _StoreRej(out=out, rejL=rsrcL);

        if(setting.get('niter')):
            out=setting['niter'].get('out')
            if(not hasattr(self.srcL[0], 'niter')): raise SkZpipeError("The sources have no `niter` attribute", exclocus=_name_);
            xmax=setting['niter']['max']
            ksrcL,rsrcL=[],[]
            for src in FsrcL:
                if(src.niter<=xmax): ksrcL.append(src)
                else: RsrcL.append(src)

            FsrcL=ksrcL;
            _StoreRej(out=out, rejL=rsrcL);

        if(setting.get('emag')):
            out=setting['emag'].get('out');
            if(not hasattr(self.srcL[0], 'emag')): raise SkZpipeError("The sources have no `emag` attribute", exclocus=_name_);
            rsrcL=[];
            if('max' in setting['emag']):
                xmax=setting['emag']['max'];
                ksrcL=[];
                for src in FsrcL:
                    if(src.emag<=xmax): ksrcL.append(src);
                    else: RsrcL.append(src);

                FsrcL=ksrcL;

            if('sigma' in setting['emag']):
                from .... import mathfunct as mathf
                data=numpy.array([[src.mag, src.emag] for src in FsrcL]);
                popt, pcov=mathf.curvefit_mag_logemag(datain=data);
                ksrcL=[];
                for src in FsrcL:
                    if(math.log10(src.emag)<=mathf.logerrmag(src.mag, popt[0], popt[1], popt[2], popt[3])+math.log10(setting['emag']['sigma']+1)): ksrcL.append(src);
                    else: rsrcL.append(src);

                FsrcL=ksrcL;

            _StoreRej(out=out, rejL=rsrcL);
          
  ####
        if(cleanfile): 
            if(copy):
                with PhotoFile(cleanfile, self) as keptPF:
                    keptPF.srcL=FsrcL;
                    keptPF.nsrc=len(FsrcL);
                    keptPF.writefile(overwrite=True);
            else:
                self.srcL=FsrcL;
                self.nsrc=len(FsrcL);
           #     self.writefile(overwrite=True)  overwriting should be done later, in case
        if(rejfile and rejfile!='-' and RsrcL):
            with PhotoFile(rejfile, self) as rejPF:
                rejPF.srcL=RsrcL;
                rejPF.nsrc=len(RsrcL);
                rejPF.writefile(overwrite=True);
      
        return len(FsrcL), len(RsrcL);
      
  
  ###
    def backup(self):
        """Create a back-up of a file. The backup file name has the modification time appended to the end.
  
Return
------
    Integer: 0 for succeed, -1 for failing
  """;
        _name_='PhotoFile.backup'
        if(os.path.exists(self.fname)):
            shutil.copy(self.fname, self.fname+datetime.datetime.fromtimestamp(os.stat(self.fname).st_mtime).strftime('-%Y%m%d_%H%M%S'));
            return 0;
        return -1;

  ###  
    def regfromcat(self, skip_header=0, datapos=0, size1=0, size2=None, un_flg=0, col_flg=0, shp_flg=0, regfile='', additionaltext=None):
        """Creates a reg file for DS9 from a generic catalog.
  
  Parameters
  ----------
      x : 
          X
    size : float or dict
        The size value of the region. If more 
can be provided as a single value of the size or as a list/tuple (-size0, a, data0) with 3 values
                    to calculate the size with size=size0+a(data0-data);
                    ellipse wants 2 values and box can have 1 or 2. 
  the flags can be both number or the text
    unit-flag:  0:fk5  [arcsec]; 1:image  [pxl]
    colors:     0:black 1:white 2:red 3:green 4:blue 5:cyan 6:magenta 7:yellow
    shape:      0:circle 1:box 2:elipse -1:text
    additionaltext:  a tuple with an additional text to be included to a geometric ragion. First element must be a string or the number of the column with the datum
  
"""
        """regfromcat(cat=input-catalog,  skip_header=n-headerrow, datapos=column of the first coordinate, size1=size of the region, size2=additional size, un_flg=size unit flag,  col_flg=color-flag, shp_flg=shape-flag, regfile=output file, additionaltext=('text'/#column, size))
  Copyright Francesco SkZ Mauro (2013)
    datapos:    it can be the number of the column with fisrt coordinate or a list/tuple with the number of the columns of first coordinates,
                of the two data to be used to calculate the dimensions of the region (if the second of these two is not given,
                it is assumed as the following column).
  """;
        _name_='PhotoFile.regfromcat';
        atxt=additionaltext;
        if(not isinstance(cat,str) or not os.path.exists(cat)): raise IOError("regfromcat: no input file "+str(cat));
  #Datapos
        if(isinstance(datapos, int)): datapos=(datapos-1, -1, -1);
        elif(isinstance(datapos, list) or isinstance(datapos, tuple)):
            if(len(datapos)==1): datapos=(datapos[0]-1, -1, -1);
            elif(len(datapos)==2): datapos=(datapos[0]-1, datapos[1]-1, datapos[1]);
            elif(len(datapos)==3): datapos=(datapos[0]-1, datapos[1]-1, datapos[2]-1);
            else: raise ValueError("regfromcat: Wrong value for datapos {:}".format(str(datapos)));
        else: raise TypeError("regfromcat: Wrong value for datapos {:}".format(str(datapos)));
  #Size
        if(isinstance(size1, int)): size1=(size1, 0, 0);
        elif(isinstance(size1, list) or isinstance(size1, tuple)):
            if(len(size1)==1): size1=(size1[0], 0, 1);
            elif(len(size1)==2): size1=(size1[0], size1[1], size1[1]+1);
            elif(len(size1)!=3): raise ValueError("regfromcat: Wrong value for size1 {:}".format(str(size1)));
        else: raise TypeError("regfromcat: Wrong value for size1 {:}".format(str(size1)));
        if(size2 is None): size2=size1;
        else:
            if(isinstance(size2, int)): size2=(size2, 0, 0);
            elif(isinstance(size2, list) or isinstance(size2, tuple)):
                if(len(size2)==1): size2=(size2[0], 0, 1);
                elif(len(size2)==2): size2=(size2[0], size2[1], size2[1]+1);
                elif(len(size2)!=3): raise ValueError("regfromcat: Wrong value for size2 {:}".format(str(size2)));
            else: raise TypeError("regfromcat: Wrong type for size2 {:}".format(str(size2)));
  #Unit
        systL=["fk5", "image", 'physical']; unitL=['"','', ''];
        if(isinstance(un_flg, str)):
            un_flg=un_flg.lower();
            if('pxl' in un_flg or 'pix' in un_flg): un_flg=1;
            elif(un_flg in systL): un_flg=systL.find(un_flg);
        elif(un_flg<0 or un_flg>=len(systL)): raise ValueError("regfromcat: Wrong value for unit flag! {:}".format(str(un_flg)));
  #Shape
        shapeL=["circle", "box", "ellipse", "text"];
        if(isinstance(shp_flg, str)):
            shp_flg=shp_flg.lower();
            if(shp_flg in shapeL):
                shp_flg=-1 if(shp_flg=='text') else shapeL.index(shp_flg);
            else: raise ValueError("regfromcat: Wrong value for shape flag! {:}".format(str(shp_flg)));
        elif(isinstance(shp_flg, int) and shp_flg<-1 or shp_flg>=len(systL)): raise ValueError("regfromcat: Wrong value for shape flag! {:}".format(str(shp_flg)));
        if(shp_flg==-1 and datapos[1]<0): 
            raise ValueError("regfromcat: Wrong value for shape flag or missing a datapos value! (shape flag: {:} ; datapos: {:} )".format(str(shp_flg), str(datapos))); 
  #Color
        colorL=["black","white","red","green","blue","cyan","magenta","yellow"];
        if(isinstance(col_flg, str)):
            col_flg=col_flg.lower();
            if(col_flg not in colorL): raise ValueError("regfromcat: Wrong value for color flag! {:}".format(str(col_flg)));
        elif(isinstance(col_flg, int)):
            if(col_flg<0 or col_flg>=len(colorL)): raise ValueError("regfromcat: Wrong value for color flag! {:}".format(str(col_flg)));
            else: col_flg=colorL[col_flg];
  #AdditionaText
        if(shp_flg==-1): atxt=None;
        if(atxt is not None):
            if( not isinstance(atxt, tuple)): raise TypeError("regfromcat: additionaltext must be None or a tuple of 2 elements (text, font size)");
            if((not isinstance(atxt[1], int) or atxt[1]<1) or (not isinstance(atxt[0], str) and not isinstance(atxt[0], int)) or atxt[1]<=0 ): 
                raise ValueError("regfromcat: additionaltext must be None or a tuple of 2 elements (text, font size)");
        if(not regfile): regfile=cat+'.reg'
  
        with open(regfile, 'w') as f_out,  open(cat) as f_in:
            fsize=atxt[1] if(atxt) else size1[0];
            f_out.write("""# Region file format: DS9 version 4.0
  global color={:} font="helvetica {:d} normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=0 delete=1 include=1 source=1
  {:}
  """.format(col_flg, int(fsize), systL[un_flg]));
            ii=0;
            for ii in range(skip_header):
                line=f_in.readline();
            if(ii+1<skip_header): raise SkZpipeError("Error! Not enough lines!", exclocus='regfromcat');
            for line in f_in:
                if(len(line)<5 or line[0]=='#'): continue;
                tmpl=line.strip().split();
                x=float(tmpl[datapos[0]]);  y=float(tmpl[datapos[0]+1]);
                if(shp_flg>=0):
                    data=(float(tmpl[datapos[1]]) if(datapos[1]>=0)else 0, float(tmpl[datapos[2]]) if(datapos[2]>=0)else 0);
                    dim=[size1[0]+size1[1]*(size1[2]-data[0]), size2[0]+size2[1]*(size2[2]-data[1])];
                    text= " text={{{:}}}".format(tmpl[atxt[0]-1]) if(atxt) else '';
                    if(shp_flg==0): 
                        f_out.write("circle({:.6f},{:.6f}, {:.3f}{:}) #tag={{{:}}}{:}\n".format(x, y, dim[0], unitL[un_flg], regfile, text));
                    else: f_out.write("{:}({:.6f},{:.6f}, {:.3f}{:},{:.3f}{:}) #tag={{{:}}}{:}\n".format( shape[shp_flg], x, y, dim[0], unitL[un_flg], dim[1], unitL[un_flg], regfile, text));
                elif(0<=datapos[1]<len(tmpl)):
                    f_out.write("# text({:.6f},{:.6f}) text={{{:}}}\n".format( x, y, tmpl[datapos[1]]));
  
  ################################
    def idmod(self, id0=0, skiprows=0, outfile=None):
        """Reenumerate the IDs
  
  Parameters
  ----------
      id0 : int
          Zero-point for the ID (first ID is 'id0'+1). It must be non-negative.
      skiprows : int
          Number of initial rows to skip
      outfile : str
          Name of the output file. Default value is 'fname'+"_M"
  
  Return
  ------
  """
        _name_='PhotoFile.idmod';
        if(not isinstance(fname,str)): raise TypeError("idmod: fname must be a string.");
        check_file(fname, minline=skiprows);
        if(not isinstance(id0,int) or id0<0): raise TypeError("idmod: id0 must be a non-negative integer.");
        if(not isinstance(skiprows,int)): raise TypeError("idmod: skiprows must be an integer.");
        if(outfile is None): outfile=fname+'_M';
        with open(fname) as fin, open(outfile, 'w') as fout:
            for ii in range(skiprows):
                fout.write(fin.readline());
            for line in fin:
                idx=line.split(None,1)[0];
                lenfld=line.find(idx)+len(idx);
                frmt="{{:{:d}d}}".format(lenfld);
                id0+=1;
                fout.write(frmt.format(id0)+line[lenfld:])
  
  ################################
    def sourcematching(self, withfile=None, status='master', outfile=None, ctype=None, iteration=None, clip=None, justbest=True, coordtransf=None, verb=False):
        """Matching with another source list. Using match.sourcematching

Parameters
----------
    withfile : str, list of IdXY objects, PhotoFile
        The other source list to match with. It can be the name of a file or a list of IdXY objects
    status : str
        Status of the local source list: 
            'master': catalog used as main reference
            'slave' : catalog used to find matching candidates for master's sources (it should be the denser catalog)
    outfile : str
          Name of the output file. 

    ctype,iteration,clip,justbest,coordtransf,verb : see match.sourcematching
      
  
  Return
  ------
  """
        _name_='PhotoFile.sourcematching'
        if(not self.srcL): self.read_assources()
        if(self.nsrc==0): raise SkZpipeError(f"The current PhotoFile is empty", exclocus=_name_)
        if(status not in ('master','slave')): raise SkZpipeError("`status` can be only 'master' or 'slave'.  <{status}>", exclocus=_name_)
        if(outfile is not None and not isinstance(outfile, (str,Photofile))): 
            raise TypeError(f"{_name_}: `outfile` must be None or a filename or a PhotoFile object")
        fname,phfile=None,None
        if(isinstance(withfile, str)):
            if(not os.path.exists(withfile)): 
                raise SkZpipeError(f"`withfile` should be a filename but it doesn't exist.   <{withfile}>", exclocus=_name_)
            fname=withfile
            phfile=PhotoFile(fname)
            phfile.read_assources()
            withfile=phfile.srcL
        elif(isinstance(withfile, list)):
            if(len(withfile)==0): raise SkZpipeError(f"`withfile` is an empty list", exclocus=_name_)
            if(not all(isinstance(x,bclasses.IdXY) for x in withfile)): 
                raise SkZpipeError(f"`withfile` is a list but not of IdXY objects   <{withfile[0].__class__}>", exclocus=_name_)
        elif(isinstance(withfile, PhotoFile)):
            if(not withfile.srcL): withfile.read_assources()
            if(withfile.nsrc==0): raise SkZpipeError(f"`withfile` is an empty PhotoFile", exclocus=_name_)
            phfile=withfile
            withfile=phfile.srcL

        if(status=='master'):
            master=self.srcL; slave=withfile
        else:
            master=withfile; slave=self.srcL
        output=sourcematching(master=master, slave=slave, ctype=ctype, iteration=iteration, clip=clip, justbest=justbest, coordtransf=coordtransf, verb=verb)
        sourcesep=' '*4
        if(isinstance(outfile, str)): #write in a file
            with open(outfile, 'w') as fout:
                for mtc in output['match']:
                    mii,ssT=mtc
                    if(justbest):
                        sii,dst,Dx,Dy, *clpT=ssT
                        fout.write(str(master[mii])+sourcesep+str(slave[sii])+f"   {dst:6.4f}  {Dx:6.4f} {Dy:6.4f}"+' '.join([f"{x:.4f}" for x in clpT])+'\n' )
                    else:
                        sii=[x[0] for x in ssT]
                        dst=[x[1] for x in ssT]
                        fout.write(str(master[mii])+'\n' )
                        for ii in range(len(sii)):
                            fout.write(sourcesep+str(slave[sii])+f"   {dst[ii]:6.4f}\n" )
                        #fout.write('\n')
            
            if(status=='master'):
                with PhotoFile(outfile+'_Mrej', self) as outPF:
                    outPF.srcL=[master[mii] for mii in output['m-rej']]
                    outPF.nsrc=len(outPF.srcL);
                    outPF.writefile(overwrite=True);
                if(phfile):
                    with PhotoFile(outfile+'_Srej', phfile) as outPF:
                        outPF.srcL=[slave[sii] for sii in output['s-rej']]
                        outPF.nsrc=len(outPF.srcL);
                        outPF.writefile(overwrite=True);

            else:
                with PhotoFile(outfile+'_Srej', self) as outPF:
                    outPF.srcL=[slave[sii] for sii in output['s-rej']]
                    outPF.nsrc=len(outPF.srcL);
                    outPF.writefile(overwrite=True);
                if(phfile):
                    with PhotoFile(outfile+'_Mrej', phfile) as outPF:
                        outPF.srcL=[master[mii] for mii in output['m-rej']]
                        outPF.nsrc=len(outPF.srcL);
                        outPF.writefile(overwrite=True);

        else:
            mchsrcL=[]
            if(justbest):
                nclip=len(clip) if(clip) else 0
                #output={'match':[ (mst_ii, (slv_jj,   dst, Dx, Dy,   mean_clip, clips, ...)),  (...), ...]}
                initdata=[{'obj':'mst', 'class':master[0].__class_, 'data':None, 'mode':'copy' },
                    {'obj':'slv', 'class':slave[0].__class__, 'data':None, 'mode':'copy' },
                    {'obj':'dist', 'class':dict, 'data':{'Dr':None, 'Dx':None, 'Dy':None}, 'mode':'copy' }]
                if(nclip):
                    initdata.append({'obj':'clip', 'class':dict, 'data':{'mean':None}, 'mode':'copy'})
                for mtc in output['match']:
                    init=copy.deepcopy(initdata)
                    init[0].update({'data':master[mtc[0]]})
                    init[1].update({'data':slave[mtc[1][0]]})
                    init[2]['data'].update({'Dr':mtc[1][1], 'Dx':mtc[1][2], 'Dy':mtc[1][3]})
                    if(nclip):
                        init[3]['data'].update({'mean':mtc[1][4]})
                        for ii,clp in enumerate(clip):
                            clp=clp.rsplit(':',1)[1]
                            initdata[3]['data'].update({clp:mtc[1][ii+5]})

                    mchsrL.append(SourceMD(initdata=init, main=1, idx=None))
            else:
                pass


  

###############################################################################

 #CATALOG
class CtlgFile():

    def __init__(self, ftype=None, fname=None, header=None):
        self.fname, self.srcL = fname, [];
        self.fform, self.sourcetype = PhotoFileFormatD[None].copy(), SourceTypeD[''];

        if(isinstance(ftype, PhotoFile)):
            if(not isinstance(header, PhotoFileHeader)): header=ftype.fform.header;
            self.fform=PhotoFileFormat(ftype=ftype.fform.ftype, header=header);
            self.fname, self.srcL=ftype.fname, ftype.srcL.copy();
            ftype=ftype.fform.ftype;
        if(ftype in SourceTypeD): self.sourcetype=SourceTypeD[ftype];
        if(fname): self.fname=fname;

    def __enter__(self):
        return self;
    def __exit__(self, exc_type, exc_value, exc_tb):
        if(exc_type!=None):
            return False;
        else:
            pass;

    def setname(self, fname=None):
        if(isinstance(fname,str) and fname): self.fname=fname;
        else: raise ValueError("CtlgFile: wrong name");

    def read(self):
        """Load a photometry file from a file 'fname'""";
        with open(self.fname) as fin:
            fin.readline();
            self.header=PhotoFileHeader(fin.readline());
            fin.readline();
            self.srcL=[];
            for line in fin:
                for ii in range(self.sourcetype._dtype_nlines-1):
                    line+=fin.readline();
                self.srcL.append(self.sourcetype(line));
        return len(self.srcL);

    def append(self, src=None):
        self.srcL.append(self.sourcetype(src));

    def write(self, fname=None, overwrite=False):
        """Write a CtlgFile from athe internal list of sources""";
        if(not self.srcL): raise ValueError("CtlgFile: wrong internal source list");
        if(not fname): fname=self.fname;
        if(not fname): raise ValueError('CtlgFile: no name');
        with open(fname, 'w') as fout:
            self.writeheader(output=fout, overwrite=overwrite);
            for src in self.srcL:
                fout.write(str(src)+'\n');

    def stat(self):
        """Create statistics of the list or sources""";
        _name_='CtlgFile.stat()'
        xmax, ymax=-1e6, -1e6;  
        xmin, ymin=+1e6, +1e6;  
        if(not self.srcL): 
            with open(self.fname) as fin:
                for ii in range(3):  #HEADER LENGTH  @@@@@
                    fin.readline();
                for line in fin:
                    for ii in range(self._dtype_nlines-1):
                        line+=fin.readline();
                    tmpo=self.sourcetype(line);
                    tmpl=line.split();
        else:
            if(hasattr(self.srcL[0], 'mag')):
                hasmag=True;
                mmax, emax=0,0;
                mmin,emin=99,10;
            else:
                hasmag=False;
                mmin,mmax, emin,emax=None,None, None,None;
            if(hasattr(self.srcL[0], 'sky')):
                hassky=True;
                smax=0;
                smin=1.e6;
            else:
                hassky=False;
                smin,smax=None,None;
            for src in self.srcL:
                if(xmin>src.x): xmin=src.x;
                if(xmax<src.x): xmax=src.x;
                if(ymin>src.y): ymin=src.y;
                if(ymax<src.y): ymax=src.y;
                if(hasmag and -90<src.mag<90):
                    if(mmin>src.mag): mmin=src.mag;
                    if(mmax<src.mag): mmax=src.mag;
                    if(src.emag>0):
                        if(emin>src.emag): emin=src.emag;
                        if(emax<src.emag): emax=src.emag;
                if(hassky):
                    if(smin>src.sky): smin=src.sky;
                    if(smax<src.sky): smax=src.sky;
        return {'x':(xmin,xmax), 'y':(ymin,ymax), 'mag':(mmin,mmax), 'emag':(emin,emax), 'sky':(smin,smax) }



def CheckClassDefinition(obj=None):
    """Check if a sub-class is defined correctly

Parameters
----------
    obj : obj
        Object whose class is to be checked.
""";
    _name_='CheckClassDefinition'
    if(isinstance(obj, IdXYml)):
        if(self._dtype_nlines<2): raise ValueError(_name_+": `_dtype_nlines` for this king of object must be greater than 1. Use the one-line version");

        if(not self.withid):
            for ii in range(self._dtype_nfield):
                if('idx' in self._dtype_names[ii]):
                    if(self._dtype_names[ii].index('idx')==0):
                        self._dtype_names=self._dtype_names[ii][1:];
                        self._dtype_formats=self._dtype_formats[ii][1:]; 
                    else: raise SkZpipeError("The class has been defined correctly! the defualt name for the ID attribute `idx` is put not at the beginning and the object is created without ID", exclocus=_name_);

    
    bclasses.CheckClassDefinition(obj)

