"""Generic classes.

class Image

class IdXY(GenStructData)

""";

import os, re, math, io, copy 
import multiprocessing as multiprc
import psutil, numpy;
from sys import stdout, stderr



from ...exceptions import *
from .. import basicpar as bpar
from .. import options as _opt

###############################################################################
class Image:
    """Class to define a image

Attributes
----------
    fname : str
        Base name of the image (without extention)
    fwhm : float
        Full Width Half Maximum
    gain : float
        Gain
    ron : float
        Read Out Noise
    hgd : float
       Maximum  
    chip : str
        Chip identificator
    exptime : float
        Exposure time
    filter : str
        Filter (None if no filter)
    airmass : float
        Airmass
    mjd : float
        Modified Julian Day (Julian Day-2400000.5)
    date : str
        Date of observation
    time : str
        Time of observation (UT)
    ra : float
        Right Ascension
    dec : float
        Declination
    instr : str
        Instrument
    nx,ny : int
        Length of the two axes
    bitpix : int
        Bitpix, Bits per pixel
    scale : tuple of float
        Scale in arsec/pixel
    apcorr : tuple of float
        Aperture correction (to be eventually added)

""";

    def __init__(self, data=None):
        """Class to manage image data

Parameters
----------
    data : dict, str
        Dictionary with image data as a dictionary or the name of the image and the data will be retrieved from SkZp_Par['inputdata'].

Attributes
----------

""";
        if(not isinstance(data,(dict,str))): raise TypeError("Image class: wrong input type, it must be tha basename of the image or the dictionary with the data [dict, str]");
        if(isinstance(data, str) or (len(data)==1 and data.get('NAME') )):
            tmpd=bpar.SkZp_Par['inputdata'].get(data if(isinstance(data, str)) else data.get('NAME') )
            if(not tmpd): raise KeyError(f"Image class: input {data} is not a valid image name")
            if(isinstance(data, str)):
                data=tmpd
            else:
                data.update(tmpd)
        if(not all(tag in data for tag in ('NAME', 'FWHM'))): raise TypeError("Image class: input data doesn't have needed keys. (NAME FWHM)");
        
        from ...functions  import getfloat
        self.fname=data['NAME'].strip();
        if(not self.fname or not isinstance(self.fname,str)): raise ValueError("");
        self.fwhm=data.get('FWHM');
        self.gain=data.get('GAIN');
        self.ron=data.get('RON');
        self.hgd=data.get('HIGH');
        self.chip=data.get('CHIP');
        self.exptime=getfloat(data.get('EXPTIME'), 0);
        self.filter=data.get('FILTER');
        self.airmass=data.get('AIRMASS');
        self.mjd=data.get('MJD');
        self.night=data.get('NIGHT');
        self.date=data.get('DATE');
        self.time=data.get('TIME');
        self.ra=data.get('RA');
        self.dec=data.get('DEC');
        self.instr=data.get('INSTRUMENT');
        self.nx=data.get('NX');
        self.ny=data.get('NY');
        self.bitpix=data.get('BITPIX');
        self.scale=data.get('SCALE');
        self.apcorr=data.get('APCORR');
        if(isinstance(self.apcorr,str)): self.apcorr=tuple( getfloat( x, 0) for x in re.split('[,;]',self.apcorr));
    
        if(isinstance(self.scale,str)): self.scale=tuple(float(x) for x in self.scale.split(';'));
        else: self.scale=(self.scale,self.scale);
    
        try:
            self.dataframe=copy.deepcopy(data);
        except:
            print(data.__class__, data)
            raise
   ###

#####
    def __exit__(self, exc_type, exc_value, exc_tb):
        if(exc_type!=None):
            return False;

    def __enter__(self):
        return self;
    
###############################################################################
class MProc():
    """Class for multiprocessing 

Parameters
----------
    nproc : int or bool or None. Default option 'mp:nproc'.
        Number of requiered processes/jobs, or if to use multiprocessing. A value of 1 is equal to 0/False.
        If negative, it will be set to the number of core/cpu less (abs()-1) (joblib style: i.e. -1 for all the cpu, -2 to use all the cpu but one).
        If True, `nproc` will be set to the number of core/cpu.
    narg : int or None
        Number of input data to elaborate.
    method :  str. Default option mp:method'.
        Method for multiprocessing: Process or Pool;
    saferun : int
        Limit the number of processing up to the number of cores (1) or number of core less 1 (-1)
    memreq : int/float or list of int/float
        Amount of memory n MiB required by each process. If it is a number, a list of nproc values will be considered.
        If it is a iterable, only the nproc highest values will be considered.
        nproc will be reduced to match the available system memory.
    minproc : int
        Minimum number of processes/jobs. Useful for elaboration that use few resources and need to be speed up.
        If negative, it will be set to the number of core/cpu less (abs()-1) (joblib style: i.e. -1 for all the cpu, -2 to use all the cpu but one).
        


""";
   # __init__(self, nproc=None, narg=None, method='pool', saferun=True, memreq=0, minproc=0, verb=True):
    _name_="MPRoc";
    error,output=None,None;
    nproc=None;
    pool=None;
    _methT=('pool','process');

    def nproc_set(self, nproc=None, narg=None, method=None, saferun=-1, memreq=0, minproc=0):
        """Set the internal variables according to nproc value.
""";
        _name_='nproc_set';
        if(nproc is None): nproc=self.nproc;
        if(nproc is not None and not isinstance(nproc, (int,bool))): raise TypeError(self._name_+": `nproc` must be an int or bool <{}>".format(nproc));
        if(not isinstance(minproc, int)): raise TypeError(self._name_+": `minproc` must be an int");
        if(narg is not None):
            if( not isinstance(narg, int)): raise TypeError(self._name_+": `narg` must be an int or None <{}>".format(narg));
            elif(narg<=0): raise ValueError(self._name_+": `narg` must be a positive int <{}>".format(narg));
        if(method is not None and not isinstance(method, str)): raise TypeError(self._name_+": `method` must be a str.");
        if(method is not None):
            method=method.lower();
            if(method not in self._methT): raise ValueError(self._name_+": `method` must be {:}.".format(self.methT));
        if(not isinstance(memreq, (int,float, list,tuple))): raise TypeError(self._name_+": `memreq` must be an int or float, or a list/tuple of int/float");

        ncpu=multiprc.cpu_count();
        if(isinstance(nproc, bool)):  self.nproc= ncpu if(nproc) else 0;
        elif(nproc is None): self.nproc=_opt.OptionGet('mp:nproc', otype='I')
        else: self.nproc=nproc;

        if(self.nproc<0): self.nproc= ncpu-abs(nproc+1);  ## joblib style
        if(self.nproc==1): self.nproc=0;
   
   #INPUT
        if(narg is not None): self.nproc=min(narg,self.nproc);

   #SAFERUN
        if(saferun):
            if(self.nproc>ncpu-1):
                if(saferun==-1): self.nproc=ncpu-1;
                elif(self.nproc>ncpu): self.nproc=ncpu;
   #MINIMUM number of process (for jobs that use few resources)
        if(minproc):
            if(minproc<0): minproc= ncpu-abs(minproc+1);  ## joblib style
            if(self.nproc<minproc): self.nproc=minproc;

   #MEMORY
        if(self.nproc):
            if(isinstance(memreq, (int,float))):  memreq=[memreq];
            if(any(x<0 for x in memreq)): raise ValueError("Mproc: 'memreq' must be an int or float, or a list/tuple of int/float");
            if(len(memreq)>1):
                memreqL=sorted(memreq, reverse=True);
                for ii,x in enumerate(memreqL):
                    if(x>0):
                        x=int(x);
                        if(x<=0): x=1;
                        memreqL[ii]=x;
                    else: memreqL[ii]=0;
            else: memreqL=memreq[:];
            if(memreqL[0]>0):
                nwork=len(memreqL);
                if(nwork<self.nproc): memreqL.extend(memreqL[-1:]*(self.nproc-nwork));
                else: memreqL=memreqL[:self.nproc];
                memavl=(psutil.virtual_memory().available>>20)*bpar.SkZp_Par['mp:availmemfrac'];
                memreqC=0;
                for ii,x in enumerate(memreqL):
                    if(x==0): break;
                    memreqC+=x;
                    if(memreqC>memavl):
                        if(ii>0):
                            self.nproc=ii;
                            print(f"!!!Warning: Multiprocessing: number of processes reduced to {self.nproc} for memory limit!!! {memreqL}", file=bpar.SkZp_Par['stdout']);
                        else:
                            self.nproc=1;
                            print("!!!Warning: Multiprocessing: Exceeded memory limit!!! Number of processes reduced to 1!! ",memreqL, file=bpar.SkZp_Par['stdout']);

                        break;

        bpar.ParameterSet('mp:nproc', self.nproc)
        if(self.nproc):
            if(method[0:4]=='proc'):
                self.error=multiprc.Queue();
                self.output=multiprc.Queue();
            elif(method[0:4]=='pool'):
                self.pool=multiprc.Pool(processes=self.nproc)
                if(_opt.OptionGet('debug', otype='Flg')): print(f"nproc={self.nproc}", file=bpar.SkZp_Par['stderr'], flush=True)
        else:
            self.error=[];
            self.output=[];

        return;
    
 ## INIT #START# 
    def __init__(self, nproc=None, narg=None, method='pool', saferun=True, memreq=0, minproc=0, verb=True):
        """MPRoc object for multiprocessing """;

        self._name_='MProc object';
        if(nproc is not None and not isinstance(nproc, (int,bool))): raise TypeError(self._name_+": `nproc` must be an int or bool.");
        if(method is not None and not isinstance(method, str)): raise TypeError(self._name_+": 'method' must be a str.");
        if(method is not None):
            method=method.lower();
            if(method not in self._methT): raise ValueError(self._name_+": 'method' must be {:}.".format(self.methT));
        if(memreq is not None and not isinstance(memreq, (int,float)) and not isinstance(memreq, list) ): 
            raise TypeError(self._name_+": 'memreq' must be an int or float <{}>".format(memreq));
    

        self.nproc=nproc;
        self.nproc_set(nproc=nproc, narg=narg, saferun=saferun, method=method, memreq=memreq, minproc=minproc);
 ## INIT #END# 

    def close(self):
        bpar.SkZp_Par['mp:nproc']= 0

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close();
        if(exc_type!=None):
            return False;

    def __enter__(self):
        return self;

    def __del__(self):
        self.close();


###############################################################################
class GlobalOutPut:
    """Class to manage the global output.

Parameters
----------
    otype : str
        Type of the output: 'out' for stdout, 'err' for stderr. Deafult 'out'.

    """;
    otype,stream=None,None;
    dbglog,logopn=None,None;
  

    def __init__(self, otype='out'):
        """GlobalOutPut object


""";
        _name_="GlobalOutPut object";
        if(not isinstance(otype,str)): raise ValueError(_name_+": 'otype' must be a str ('out' or 'err')");
        otype=otype.lower();
        if( otype not in ('out', 'err')): raise ValueError(_name_+": 'otype' must be a str ('out' or 'err')");
        self.otype=otype;
        self.stream=stdout if(self.otype == 'out') else stderr;

    def write(self, s=None):
        """Write method of class GlobalOutPut"""
        if(s is None): raise TypeError(self._name_+": write() takes exactly one argument (0 given)");
        if(_opt.OptionGet('debugging:log', otype='Flg')):
            with open(_opt.OptionGet('debugging:logfile', otype='S'), 'a') as flog:
                flog.write(s);
        return self.stream.write(s);


    def flush(self):
        self.stream.flush();
    def writelines(self, datas):
        self.stream.writelines(datas)
    def __getattr__(self, attr):
        return getattr(self.stream, attr);

###############################################################################
class OutputPipe:
  """OutputPipe class: class to manage the output of the parallel processing.

Parameters
----------
    mproc : int or bool
        Number of processes to run parallelly (if >1 the output must be manage for multiprocessing, otherwise not), or if the multiprocessing is on.
    otype : str
        Type of the output: 'out' for like stdout; 'err' for like stderr; 'null' for like '/dev/null': the output will throw away. Deafult 'out'.
    output : str or StringIO or TextIOWrapper
        Name of the file or where store the output when closing the object (deafult SkZp_Par['stdout']);
    mode : str
        The mode in which the output file is opened: 'w' for writing (truncating the file if it already exists), 'a' for appending.

""";
  mproc,output,stream=None,None,None;
  sopened,fopened=True, True;
  mode, otype='w', 'out';
  _name_="OutputPipe";
  

  def __init__(self, mproc=None, otype='out', output=None, mode='w'):
    """OutputPipe onject for output of process""";
    _name_="OutputPipe object";
    if(mproc is not None and not isinstance(mproc, (int,bool))): raise TypeError(_name_+": `mproc` must be a int or bool.");
    if(output is not None and not isinstance(output,(str,io.StringIO, io.TextIOWrapper, OutputPipe)) and not hasattr(output,'write')): raise TypeError(_name_+": `output` can be None, a string or StringIO, TextIOWrapper, OutputPipe, or an object with `write` method.<{}>".format(output.__class__)); 
    if( not isinstance(mode,str)): raise TypeError(_name_+": `mode` must be a str.");
    if( mode not in ('w','a')): raise ValueError(_name_+": wrong value for `mode`: must be 'w' or 'a' (it cannot be read mode 'r') <{}>.".format(mode));
    if( not isinstance(otype,str)): raise TypeError(_name_+": `otype` must be a str.");
    if( otype not in ('out', 'err', 'null')): raise ValueError(_name_+": `otype` must be a str ('out', 'err', 'null') <{}>.".format(otype));
    self.otype=otype;

    if(mproc is None): 
      if(not bpar.SkZp_Par['mp:nproc']):
        mproc=_opt.OptionGet('mp:nproc', otype='I')
      else:
        mproc=bpar.SkZp_Par['mp:nproc'];
    self.mproc=bool(mproc>1) if(isinstance(mproc,int)) else mproc;
    self.output=output;
    if(self.mproc or self.output):
      self.stream= io.StringIO(); #if change it, change in discharge
      self.sopened=True
      if(isinstance(self.output, str)):
        self.output=open(self.output, self.mode);
        self.fopened=True
    else:
      if(self.otype == 'out'):
        self.stream=bpar.SkZp_Par['stdout'];
      elif(self.otype == 'err'):
        bpar.SkZp_Par['stderr'];
        
      self.sopened=False;
    self.mode=mode;
  #### INIT END #

  def write(self, s=None):
    if(s is None): raise TypeError(self._name_+": write() takes exactly one argument (0 given)");
    if(self.otype=='null' or not s): return;
    if(not hasattr(self.stream, 'write')):
      if(_opt.OptionGet('debug', otype='Flg')): print(">>!!{}!!<<".format(s), end=' ');
      return;
    return self.stream.write(s);

  def close(self):
    """Terminate the use of the object, flushing it.
""";
    if(self.stream is None): return;
    outopn=False;
    if(hasattr(self.stream, 'getvalue')):
      if(self.output):
        self.output.write(self.stream.getvalue());
        self.output.flush();
        if(self.sopened): self.stream.close()
        if(self.fopened): self.output.close()
      else:
        output_=bpar.SkZp_Par['stdout'] if(self.otype == 'out') else bpar.SkZp_Par['stderr'];
        output_.write(self.stream.getvalue());
        output_.flush();
    self.stream=None;
    self.output=None;

  def discharge(self):
    self.stream.flush();
    if(self.sopened):
      if(self.output):
        output_=self.output;
      else:
        output_=bpar.SkZp_Par['stdout'] if(self.otype == 'out') else bpar.SkZp_Par['stderr'];
      output_.write(self.stream.getvalue());
      output_.flush();
      self.stream= io.StringIO();  #Same as in init

  def flush(self):
    if(hasattr(self.stream, 'flush')): self.stream.flush();
  def writelines(self, datas):
    self.stream.writelines(datas)
  def __getattr__(self, attr):
    return getattr(self.stream, attr);
    
#  def fileno(self):
#    return self.stream.fileno();
    
  def __exit__(self, exc_type, exc_value, exc_tb):
    self.close();
    if(exc_type!=None):
      return False;

  def __enter__(self):
    return self;

#  def __del__(self):
#    self.close();


###############################################################################
class Region:
  """Class to define region of 2D space."""

  def __init__(self, data=None, x=None, y=None, dx=None, dy=None, shape=None):
    """Class to define region of 2D space.

Parameters
----------
    data : dict
        Dictionary with keys 'x', 'y', 'dx', 'dy', 'shape' that define the region.
    x : float
        First coordinate of the central point.
    y : float
        Second coordinate of the central point.
    dx : float
        Half size along first coordinate.
    dy : float
        Half size along second coordinate.
        
    shape : str
     
""";
    
    if(isinstance(data,dict)):
      if(data.get('x')): x=data['x'];
    
###############################################################################





###############################################################################
    
 #OTHER Class
class CoordTransf:
    """Class that define a coordinate transformation in 'ndim' dimensions.

Parameters
----------
    coeff : dict or CoordTransf
        Dictionary with the full trasnformation: 
            {0:(pan), 'X':(X_shift, *X, *Y, *X^2, *X*Y, *Y^2, ...), 'Y':(Y_shift, *X, *Y, *X^2, *X*Y, *Y^2, ...) } }
        If it is not set, the other parameters will be checked. The five trasformation are executed in the given order.
    pan : tuple of floats
        Initial shift (tuple of ndim elements).
    zoom : tuple of floats
        Linear trasformation in the axes (tuple of ndim positive elements).
    flip :  tuple of int
        Change of the sign (mirroring, invertion) along the axes (tuple of ndim 0/1).
    rotate : tuple of floats
        Angles of the rotation (tuple of ndim-1 elements).
    shift :  tuple of floats
        Final shift (tuple of ndim elements).
    others : dict
        Dictionary with 1 key, that describe the input format.
            'dao' : Dictionary with:
                'nxny': Tuple with the values used as image size
                'coeff': Tuple with (2,4,6,12,20) coefficients from DAOmaster
"""

    def __init__(self, coeff=None, pan=None, zoom=None, rotate=None, flip=None, shift=None, ndim=2):
        if(ndim!=2): raise ValueError('CoordTransf: implemented only 2D')
        if(not coeff):
            if(pan==None): pan=(0.,)*ndim;
            elif(not(isinstance(pan,tuple) or isinstance(pan,list)) or len(pan)!=ndim): raise ValueError('CoordTransf: wrong value for pan');
            if(zoom==None): zoom=(1.,)*ndim;
            elif(not(isinstance(zoom,tuple) or isinstance(pan,list)) or len(zoom)!=ndim): raise ValueError('CoordTransf: wrong value for zoom');
            if(flip==None): flip=(0.,)*ndim;
            elif(not(isinstance(flip,tuple) or isinstance(flip,list)) or len(flip)!=ndim): raise ValueError('CoordTransf: wrong value for flip');
            if(rotate==None): rotate=(0.,)*(ndim-1);
            elif(isinstance(rotate,float) or isinstance(rotate,int)): rotate=(rotate,);
            elif(not (isinstance(rotate,tuple) or isinstance(rotate,list)) or len(rotate)!=ndim-1):  raise ValueError('CoordTransf: wrong value for rotate');
            if(shift==None): shift=(0.,)*ndim;
            elif(not(isinstance(shift,tuple) or isinstance(shift,list)) or len(shift)!=ndim): raise ValueError('CoordTransf: wrong value for shift');
            zoom=( abs(zoom[0]) if(flip[0]==0) else -abs(zoom[0]) , abs(zoom[1]) if(flip[1]==0) else -abs(zoom[1]));
            rotate=(rotate[0]%360,);
            if(rotate[0]==0): cosa,sina=1.,0.;
            elif(rotate[0]==90): cosa,sina=0.,1.;
            elif(rotate[0]==180): cosa,sina=-1.,0.;
            elif(rotate[0]==270): cosa,sina=0.,-1.;
            elif(rotate[0]==45): cosa,sina=0.5*math.sqrt(2),0.5*math.sqrt(2);
            else: cosa,sina=math.cos(rotate[0]/180*math.pi), math.sin(rotate[0]/180*math.pi);
            coeff={0:pan, 'X':(shift[0], zoom[0]*cosa, -zoom[1]*sina), 'Y':(shift[1], zoom[0]*sina, zoom[1]*cosa) }

            if(others):
                if(len(others)!=1): raise ValueError("CoordTransf: `others` parameter can have just 1 entry.")
                if('dao' in others):
                    if(not isinstance(others['dao'], dict)):  
                        raise TypeError("CoordTransf: `others`:'dao' parameter must be a dict {'nxny: (), 'coeff': ()}")
                    if(any(not isinstance(others['dao'].get(x), tuple) for x in others['dao'])):  
                        raise TypeError("CoordTransf: `others`:'dao' parameter must be a dict {'nxny: (), 'coeff': ()}")
                    if(len(others['dao']['coeff'])not in (2,4,6,12,20)):  
                        raise ValueError("CoordTransf: `others`:'dao':'coeff' must be a tuple of 2, 4, 6, 12 or 20 elements.")
                    coeff={'0':(0,0), 'X':others['dao'][::2], 'Y':others['dao'][1::2]}
                    if(len(others['dao']['coeff']) >6):
                        if(len(others['dao']['nxny'])!=2):  
                            raise ValueError("CoordTransf: `others`:'dao':'coeff' must be a tuple of 2, 4, 6, 12 or 20 elements.")
                        if(len(others['dao']['coeff']) >= 12):
                            coeff['X']=coeff['X'][:3]+tuple(x/others['dao']['nxny'][0] for x in coeff['X'][3:])
                            coeff['X']=coeff['Y'][:3]+tuple(x/others['dao']['nxny'][1] for x in coeff['Y'][3:])
                        if(len(others['dao']['coeff']) == 20):  
                            coeff['X']=coeff['X'][3:6]+tuple(x/others['dao']['nxny'][0] for x in coeff['X'][6:])
                            coeff['X']=coeff['Y'][3:6]+tuple(x/others['dao']['nxny'][1] for x in coeff['Y'][6:])

        if(not isinstance(coeff,(dict,CoordTransf))): raise TypeError("CoordTransf: `coeff` must be dict, a CoordTransf object or None if transformation is define with other parameters.");
        if(isinstance(coeff, CoordTransf)):
            coeff=coeff.coeff.copy()
        else:
            if(0 not in coeff): coeff[0]=(0,0);
            if('X' not in coeff): coeff['X']=(0, 1., 0.);
            if('Y' not in coeff): coeff['Y']=(0, 0., 1.);
            if(len(coeff[0])!=ndim): raise ValueError("CoordTransf: wrong value for coeff[0]");
            if(isinstance(coeff['X'],float)): coeff['X']=(coeff['X'],);
            if(isinstance(coeff['Y'],float)): coeff['Y']=(coeff['Y'],);
            if(len(coeff['X'])==1):
                coeff[0]=(coeff[0][0]+coeff['X'][0],   coeff[0][1]); 
                coeff['X']=(0, 1., 0.);
            if(len(coeff['Y'])==1):
                coeff[0]=(coeff[0][0],   coeff[0][1]+coeff['Y'][0]); 
                coeff['Y']=(0, 0., 1.);
        self.coeff=coeff.copy();

        self.dgr={};
        for tag in ('X','Y'):
            dgr=(math.sqrt(8*len(self.coeff[tag])+1)-3)/2;
            if(dgr!=int(dgr)): raise ValueError("CoordTransf: wrong length for coeff['{:}']".format(tag));
            self.dgr[tag]=int(dgr);

    def concatenate(self, ante=None, post=None):
        if(isinstance(ante, CoordTransf) and post is None):
            coeff={}
            coeff[0]=ante.coeff[0];
            if(self.coeff['X']==(0., 1., 0.)):
                coeff['X']=ante.coeff['X'];
            elif(ante.coeff['X']==(0., 1., 0.)):
                coeff[0]=(coeff[0][0]+self.coeff[0][0], coeff[0][1]);
                coeff['X']=self.coeff['X'];
            else:
                x0= self.coeff['X'][0] + self.coeff['X'][1]*(ante.coeff['X'][0]+self.coeff[0][0]) + self.coeff['X'][2]*(ante.coeff['Y'][0]+self.coeff[0][1]);
                xx= self.coeff['X'][1]*ante.coeff['X'][1] + self.coeff['X'][2]*ante.coeff['Y'][1];
                xy= self.coeff['X'][1]*ante.coeff['X'][2] + self.coeff['X'][2]*ante.coeff['Y'][2];
                coeff['X']=(x0, xx, xy);
            
            if(self.coeff['Y']==(0., 0., 1.)):
                coeff['Y']=ante.coeff['Y'];
            elif(ante.coeff['Y']==(0., 0., 1.)):
                coeff[0]=(coeff[0][0], coeff[0][1]+self.coeff[0][1] );
                coeff['Y']=self.coeff['Y'];
            else:
                y0= self.coeff['Y'][0] + self.coeff['Y'][1]*(ante.coeff['X'][0]+self.coeff[0][0]) + self.coeff['Y'][2]*(ante.coeff['Y'][0]+self.coeff[0][1]);
                yx= self.coeff['Y'][1]*ante.coeff['X'][1] + self.coeff['Y'][2]*ante.coeff['Y'][1];
                yy= self.coeff['Y'][1]*ante.coeff['X'][2] + self.coeff['Y'][2]*ante.coeff['Y'][2];
                coeff['Y']=(y0, yx, yy);
            return CoordTransf(coeff=coeff);
        elif(isinstance(post, CoordTransf) and ante is None):
            return post.concatenate(ante=self);

    def do(self, xy=None):
        """Apply the transformation to a couple of coordinates

Parameters
----------
    xy : object with 
        Couple of coordinates""";
        if(len(xy)!=2): return;
        
        x=xy[0]+self.coeff[0][0];
        y=xy[1]+self.coeff[0][1];
        new={'X':0, 'Y':0};
        for tag in ('X','Y'):
            for dgr in range(self.dgr[tag]+1):
                for idx in range(dgr+1):
                    new[tag]+=self.coeff[tag][((dgr*(dgr+1))>>1)+idx]*x**(dgr-idx)*y**(idx);
        return (new['X'], new['Y']);
    
    def applyto(self, points=None):
        """Apply the coordinate trasformation to a set of points given as tuple of coordinates, or list objects

Parameters
----------
    points : tuple of 2 floats, list of tuples of 2 floats, list of object with x,y attributes, iterable of 2-elements objects
        Coordinates to be transformed. They can be a tuple of (x,y), or a list of (x,y) or a list of objects that have attributes x and y

Return
------
    
    """
        outL=[]
        if(isinstance(points, tuple)): points=[points]
#    if(not isinstance(points, list)): raise TypeError(f"CoordTransf.applyto: `points` must be tuple of 2 floats, list of tuples of 2 floats, list of object with x,y attributes.   <{points.__class__}>")

        for ii, pnt in enumerate(points):
            if(isinstance(pnt, tuple)): 
                    points[ii]=self.do(pnt)
            elif(hasattr(pnt,'x') and hasattr(pnt,'y')): 
                    (pnt.x,pnt.y)=self.do( (pnt.x, pnt.y) )
            else: 
                    pnt=pnt.__class__(self.do(tuple(pnt)))
            outL.append(pnt)
        return points.__class__(outL)


###############################################################################
class LinkedNode():
    """Class for a node in a linked list

""";
    node=None;
    nextnd=None;
    prevnd=None

    def __init__(self, obj=None, prevnd=None, nextnd=None):
        _name_="LinkNode";
        if(any(x is not None and not isinstance(x,LinkedNode)  for x in (prevnd, nextnd))): raise TypeError(_name_+": `prevnd` and `nextnd` must be None or LinkedNode object");
        self.node=obj;
        if(prevnd is not None):
            self.prevnd=prevnd;
            if(self.prevnd.nextnd is not None):  #Inserting a new node in a chain
                if(nextnd is not None): raise SkZPipeError("Interrupting a chain: inserting a new node and giving a next node", exclocus=_name_);
                self.nextnd=self.prevnd.nextnd;
                self.prevnd.nextnd=self;
                
                if(self.prevnd is not self.nextnd.prevnd): raise SkZPipeError("Error in the chain where it is inserting a new node: the previous of the next node is not the previous node", exclocus=_name_);
                self.nextnd.prevnd=self;
            else: self.nextnd=nextnd;
        if(self.nextnd is None and nextnd is not None):
            self.nextnd=nextnd;
            if(self.nextnd.prevnd is not None):  #Inserting a new node in a chain
                self.prevnd=self.nextnd.prevnd;
                self.nextnd.prevnd=self;
                
                if(self.nextnd is not self.prevnd.nextnd): raise SkZPipeError("Error in the chain where it is inserting a new node: the next of the previous node is not the next node", exclocus=_name_);
                self.prevnd.nextnd=self;
            

###############################################################################
class GenStructData():
    """Generic class for data structured in multi lines, to create specific class to store data fron files.

Parameters
----------
    data : str, list of str, tuple of values, dict, object with read/readline method, numpy.ndarray
        The several lines appended sequencely, or a sequence of lines.
          str : a string with data that will be split and converted in the values (functions.splitconvert)
          list of str : several lines of input data (same as str)
          tuple of values : the values assigned to attributes according to the order in _data_names
          dict : the keys must be contained in _data_names. The values will be assigned properly.
          objcet : _data_nlines will be read and attributes assigned as list of str
    template : GenStructData object or dict
        - Object to be used as template for the internal structure (not the values!).
        - Dictionary with basic attribute: _data_names, _data_nlines, _data_nfield, _data_init, 
          _data_delimiter, _data_str. Each key is the name of the attribute.
 
Attributes for correct definition
---------------------------------
    _data_names : tuple of str 
        For each line, tuple of the names of the variables in the order
        as they appear in the input.
        '-' for values that has to be skipped (in `_data_init` set the
        coverters as str).
    _data_init : tuple of functions
        For each line, a tuple of funtion to convert input into object,
        one for each item in _data_names.
        e.g.   (int, float, float) or [(int, float),(int, float)]
        Rememeber to set as str the coverter for fields defined as '-'
        that has to be skipped.
        The ideal is to use hashable classes.
    _data_delimiter : dict with 'in and 'out'
            'in' : None or str or tuple of int
                To split the input string in separete fields.
                The characters used to split input string (using method
                split).
                A tuple with the sequence of integers as width(s) of
                each field or the common value.
            'out' : str
                to join the string outputs to form a line.
        Default: None.
    _data_str : tuple of formatted string or formatted string 
        Formatted string with each replacement field containing as
        keyword the variable name (as in _data_names, except the '-'s).
        Or a tuple of Formatted strings as before that will be joined
        with _data_delimiter['out']

If the input data is multi-lined, the attributes are lists of the
specified types, except for _data_delimiter.

    _data_nlines : int
        Number of lines from source data associated to it.
        Calculated as len(_data_names) .
    _data_nfield : int or list of int
        For each line, number of values provided.
        Calculated as [len(x) for x in _data_names].
    _str_flen : tuple of tuples of int
        For each line, a tuple with the length of each field (the same
        values given in _data_str).
    _str_llen : int or list of int
        For each line, its length (with last new-line,
        tecnically _str_llen[i] >= sum(_str_flen[i]) + _data_nfield).

  
  If _data_nlines is 1 (single-lined data), the attributes must be given coherently, all with one-line format or multi-line format.


How to reuse for subclasses
---------------------------
    Methods that can need be redefined:
        __init__
            Rememeber to run the parent initialization  [ super().__init__() ]

    Attributes that can need be redefined
        See above "Attributes for correct definition"


Methods
-------
    __str__
        To work with str(), print() (no ending newline)
    __repr__
        For repr()
    __iter__
        To return each value through iteration
    list
        Return a list with each value ordered as in the name definition
    formlist
        Return a list of the values of a certain format `form` in the same order of the name definition, 
        exluding certain attributes in `rej`
""";
    _data_names=()
    _data_init=()
    _data_delimiter={'in':None,'out':' ')
    _data_str=""
    
    #Really useful?
    _data_nlines=0  #len(_data_names)
    _data_nfield=tuple(len(x) for x in _data_names)
    _str_flen=()
    _str_llen=None
  
#  ()=();

 ###__INIT__###

    def _get_len(self): #, tsformat=None, tnames=None, delimiter=None):
        """Calculate _str_flen,_str_llen
        """
        from ...functions  import extract_fieldlen
        ret_f, ret_l=[],[]
        for ii in range(self._data_nlines):
            fln,dln=extract_fieldlen( self._data_str[ii], self._data_names[ii] ) 
            ret_f.append( fln )
            ret_l.append( sum(fln+dln) )
        return tuple(ret_f),tuple(ret_l)

    def _fix_structure(self):
        if(self._data_nlines==0):
            self._data_nlines=len(self._data_names) if(isinstance(self._data_names, list)) else 1

       #Fixing delimiters
        if(not isinstance(self._data_delimiter, dict)):
            self._data_delimiter={'in': self._data_delimiter}
        self._data_delimiter.set(' ')

#        if(not self._str_flen or not self._str_llen):
#            self._str_flen, self._str_llen=self._get_len()
    

    def _copy_GenStructData_data(self, obj=None):
        if(obj._data_nlines>1):
            for ii in range(obj._data_nlines):
                for var in obj._data_names[ii]:
                    setattr(self, var, getattr(obj, var))
        else:
            for var in obj._data_names:
                    setattr(self, var, getattr(obj, var))

    def _copy_GenStructData_struct(self, obj=None):
        self._data_names=obj._data_names[:] # tuple or list of tuples
        self._data_init=obj._data_init[:] # tuple or list of tuples
        self._data_delimiter=obj._data_delimiter.copy()  #dict
        self._data_str=obj._data_str[:] # str or tuple of str; or list of them
        self._data_nlines=obj._data_nlines

#        self._data_nfield=obj._data_nfield
#        self._str_flen=obj._str_flen
#        self._str_llen=obj._str_llen


    def __init__(self, data=None,  **kwargs): #kwargs= template, attributes
        """GenStructData object: an object from multi-lined structured data. This is not a class for direct use.

""";
        _name_='GenStructData object'
        from ...functions  import splitconvert
        if(data is None or (not isinstance(data,(str,list,tuple, dict, GenStructData, numpy.ndarray)) and not hasattr(data, 'read') and not hasattr(data, 'readline'))):
            raise TypeError(f"{_name_}: Wrong type for `data` to create the object.   < {data.__class__} > < {data} >")
    ###########################
    #Setting structure
        if( isinstance(kwargs.get('template'),GenStructData) ):
            _copy_GenStructData_struct(kwargs['template'])   
    
        self._fix_structure()

    ####################################
    #Setting data
        #If stream o Wrapper => string, extracting as many lines as needed
        if(hasattr(data, 'read') or hasattr(data, 'readline')): 
            if(hasattr(data, 'readline')):
                ldata='';
                for ii in range(self._data_nlines):
                    ldata+=data.readline()
            else:
                ldata=''; nlines=0;
                while True:
                    if(nlines==self._data_nlines): break
                    char=data.read(1);
                    if(not char): raise IOError(_name_+": Reached end of stream before")
                    ldata+=char;
                    if(char=="\n"): nlines+=1
            data=ldata;

        #If string => list of str
        if(isinstance(data,str)): 
            data=data.rstrip('\n').split('\n')
            if(len(data)!=self._data_nlines): raise ValueError(_name_+": Wrong number of lines ({lendata}/{nline}) in `data`".format(lendata=len(data), nline=self._data_nlines));

        # If list of str => list of list of data
        if(isinstance(data, list) and len(data)==self._data_nlines and all(isinstance(x,str) for x in data)): 
            dtmp=[]
            for ii in range(self._data_nlines):
                dtmp.append( splitconvert(data=data[ii], delimiter=self._data_delimiter['in'],  converters=self._data_init[ii], maxsplit=len(self._data_names[ii]), appendinput=False, conv_repeat=False) )
            data=dtmp;

        if(isinstance(data,(list,tuple)) and self._data_nlines==1 and len(data)!=self._data_nlines): data=[data]; #If _data_nlines==1 and list of data => list of list of data


        if(isinstance(data,(list,tuple))):
            for ii in range(self._data_nlines):
                #__dict__ stores the instance variables
                self.__dict__.update( dict((var, conv(val)) for var,conv,val in zip( self._data_names[ii] , self._data_init[ii], data[ii]  ) if(var!='-')) ) #

        # data= GenStructData
        elif(isinstance(data, GenStructData)):
            #__dict__ stores the instance variables
            self.__dict__.update(copy.deepcopy(data.__dict__)) ## ??? It copies all the instance variable

        # data= dict
        elif(isinstance(data, dict)):
            _names=self._data_names[0]
            for x in self._data_names[1:]:
                _names+=x
            _names=set(data)-(set(_names)-{'-'})
            if(_names): raise SkZpipeError(f"in `data` as dict, some keys are not legit attributes names.   <{_names}>", exclocus=_name_)
            #__dict__ stores the instance variables
            self.__dict__.update(copy.deepcopy(data))
        else: raise TypeError(_name_+': Wrong type for `data` in the initialization');

###### END INIT #####
 ####
  ###
    def __str__(self):
        "String representation without final newline"
        def _str1_(names, frmstr):
            tmpd=dict( ( var , getattr(self, var) ) for var in names if(var!='-') )  
            if(isinstance(fstr, str)):
                return frmstr.format(**tmpd)
            else:
                return self._data_delimiter['out'].join( fstr.format(**tmpd) for fstr in frmstr )
        if(self._data_nlines == 1 ):
            return _str1_(self._data_names, self._data_str)
        else:
            return '\n'.join( _str1_(tvar,fstr) for fstr,tvar in zip(self._data_str,self._data_names)  )
#        tmpL=[]
#        for fstr,tvar in zip(self._data_str,self._data_names):
#            tmpD={}
#            for var in tvar:
#               if(var!='-'): 
#                    tmpD[var]=getattr(self, var)
#            print(fstr,'\n', tvar )
#            tmpS=fstr.format(**tmpD) 
#            tmpL.append( tmpS) 
#        return '\n'.join( tmpL)
###
    def names2txt(self):
        "Lines with the names of the variables"
        if(self._data_nlines == 1 ):
            return self._data_delimiter['out'].join( x for x in self._data_names if(x!='-') )
        else:
            return '\n'.join( delim.join(tvar)  for tvar,delim  in zip(self._data_names, self._data_delimiter['out']) )
###
    def __repr__(self):
        return str(self)  #Can be better representation?
###
    def print(self):
        """String representation terminating with newline"""
        return str(self)+'\n';
###        
    def __iter__(self):
        for tvar in self._data_names:
            for varn in tvar:
                if(varn!='-'):
                    yield getattr(self, varn);
###
    def list(self, just=None):
        """Return a list of the values of the provided variable names.

Parameters
----------
    just : list or None
        List of the variable names to return the value.
        If None or null value, the internal list will be used.

Return
------
    list
"""
        if(just):
            return [getattr(self, var) for var in just]
        else:
            return [getattr(self, var) for tvar in self._data_names for var in tvar if(var!='-')]
###
    def classlist(self, cls=None, rej=None):
        """Return a list of the values of a certain class among the variables
        exluding certain attributes in `rej`

Parameters
----------
    cls : class
        Class of the values to be selected
    rej : list of str
        List of attributes not to be included

Return
------
    list
        List  of the values of a certain class among the variables exluding
        certain attributes in `rej`.
    """
        _name_='GenStructData.formlist'
        if(cls is None and not rej): return self.list()
        from inspect import isclass
        if(cls is not None and not isclass(cls)): raise SkZpipeError("`cls` must be None or a class", exclocus=_name_)
        if(rej):
            if(not isinstance(rej, list)): raise SkZpipeError(f"`rej` must be None or a list.   <{rej.__class__}>", exclocus=_name_)
            if(not all(isinstance(x, str) for x in rej)): raise SkZpipeError("`rej` must be a list of str.   {rej}", exclocus=_name_)
        _names=self._data_names[0]
        for x in self._data_names[1:]:
            _names+=x
        _names=[x for x in _names if(x!='-')]
        if(rej):
            for x in rej:
                if(x in _name): _name.remove(x)
                else: raise SkZpipeError(f"`rej` must be a list of attribute names. '{x}' do not exist.", exclocus=_name_)
        if(cls):
            return [getattr(self, var) for tvar in self._data_names for var in _names if(isinstance(var, cls))]
        else:
            return [getattr(self, var) for tvar in self._data_names for var in _names]
    
###############################################################################

class Multimeasure():
    """Class to store several measures with their uncertainties and retrieve them with indexes. 
It permits to create attributes with indexing operator to retrieve the pair (value,sigma). 
The indexing can be with positional numbers (like a list) or optional names (like a dict).

Parameters
----------
    values : sequence of floats
        List of data values
    sigmas : sequence of floats
        List of data uncertainties. If shorter than `values`, it will be filled with last value.
    names : sequence of str
        List of names variables (same order as `values`)

Attributes
----------
    num : int
        Number of measures
"""

    _values=[] #list of pairs (val,err)
    _names={} #dictionary of name:pos
    num=0
    def __init__(self, values=None, sigmas=None, names=None):
        """An object of Multimeasure class for multi-measure attributes"""
        _name_='Multimeasure object'
    
        if(not values): raise SkZpipeError(f"Wrong type or value for `values`.   <{values}>", exclocus=_name_)
        if(not sigmas): raise SkZpipeError(f"Wrong type or value for `sigmas`.   <{sigmas}>", exclocus=_name_)
        if(not all(isinstance(x,(float,int)) for x in values) or not all(isinstance(x,(float,int)) for x in sigmas) ): 
            raise SkZpipeError(f"Wrong values for `values` or `sigmas`: they must be numbers ", exclocus=_name_);
        if(len(sigmas)<len(values)):
            sigmas=list(sigmas)
            sigmas.extend(sigmas[-1:]*(len(values)-len(sigmas)))
        self._values=list(zip(values,sigmas));
        self.num=len(self._values)
        if(names):
            if(not all(isinstance(x,str) for x in names)): 
                raise SkZpipeError(f"Wrong value for `names`.   <{names}>", exclocus=_name_);
            if(len(names) != self.num): 
                raise SkZpipeError(f"`names` has not the same number of items as `values`.   <{len(names)} != {self.num}>".format(self.num, len(self._names)), exclocus=_name_);
      
            self._names=dict(zip( names, range(self.num)  ));
          
    def __getitem__(self, key):
        _name_='Multimeasure object'
        if(isinstance(key, int)): return self._values[key];
        elif(isinstance(key, str)): return self._values[self._names[key]];
        else: raise TypeError(f'{_name_}: wrong type for key.   <{key}>')
    
    def __setitem__(self, key, value, sigma):
        _name_='Multimeasure object'
        if(not isinstance(value,(int,float))): raise SkZpipeError("Wrong type: `value` must be float.   <{value}>".format(value), exclocus=_name_);
        if(not isinstance(sigma,(int,float))): raise SkZpipeError("Wrong type: `sigma` must be float.   <{value}>".format(sigma), exclocus=_name_);
        if(isinstance(key, int)): self._values[key]=(value, sigma);
        elif(isinstance(key, str)): self._values[self._names[key]]=(value, sigma);
        else: raise TypeError(f'{_name_}: wrong type for `key`.   <{key.__class__}>')
    def __getattr__(self, name=None):
        _name_='Multimeasure object'
        if(not isinstance(name,str)): raise TypeError(f"{_name_}: `name` must be a str.   <{name}>")
        if(not self._names): raise AttributeError(f"{_name_}: there are no named attributes")
        if(name not in self._names): raise AttributeError(f"{_name_} object has no {name} attribute")
        return self._values[self._names[name]]

     
    def list(self, names=None):
        """Return a list of the data (value,sigma). If `names` is given, only these data (and in that order) are returned.

Parameters
----------
    names: sequence of indexes
        Sequence of the indexes of the data to be return as list of tuple
Return
------
    list : list of tuple
        List of tuple of 2 float (value,sigma)
        """
        if(names):   return [ self[key] for key in names]
        else :  return self._values[:]
  
###############################################################################
###############################################################################

class Multivalue():
    """Class to store several single values and retrieve them with indexes. 
It permits to create attributes with indexing operator to retrieve the value. 
The indexing can be with positional numbers (like a list) or optional names (like a dict).

Parameters
----------
    values : sequence of floats
        List of data values
    names : sequence of str
        List of names variables (same order as `values`)

Attributes
----------
    num : int
        Number of values
"""

    _values=[] #list of pairs (val,err)
    _names={} #dictionary of name:pos
    num=0
    def __init__(self, values=None, names=None):
        """An object of Multivalue class for multi-valued attributes""";
        _name_='Multivalue object';
    
        if(not values): raise SkZpipeError(f"Wrong type or value for `values` <{values}>", exclocus=_name_)
        if(not all(isinstance(x,(float,int)) for x in values)): 
            raise SkZpipeError(f"Wrong value for `values` <{values}>", exclocus=_name_);
        self._values=list(values)
        self.num=len(self._values)
        if(names):
            if(not all(isinstance(x,str) for x in names)): 
                raise SkZpipeError(f"Wrong value for `names` <{names}>", exclocus=_name_);
            self._names=tuple(names)  #temporarly a tuple
            if(self.num != len(self._names)): 
                raise SkZpipeError("`names` has not the same number of items as `values` <{} {}>".format(self.num, len(self._names)), exclocus=_name_);
      
            self._names=dict(zip( self._names, range(self.num)  ));
          
    def __getitem__(self, key):
        _name_='Multivalue object'
        if(isinstance(key, int)): return self._values[key];
        elif(isinstance(key, str)): return self._values[self._names[key]];
        else: raise TypeError(f'{_name_}: wrong type for key.   <{key}>')
    
    def __setitem__(self, key, value, sigma):
        _name_='Multivalue object'
        if(not isinstance(value,(int,float))): raise SkZpipeError("Wrong type: `value` must be float.   <{value}>".format(value), exclocus=_name_);
        if(not isinstance(sigma,(int,float))): raise SkZpipeError("Wrong type: `sigma` must be float.   <{value}>".format(sigma), exclocus=_name_);
        if(isinstance(key, int)): self._values[key]=(value, sigma);
        elif(isinstance(key, str)): self._values[self._names[key]]=(value, sigma);
        else: raise TypeError(f'{_name_}: wrong type for `key`.   <{key.__class__}>')
    def __getattr__(self, name=None):
        _name_='Multivalue object'
        if(not isinstance(name,str)): raise TypeError(f"{_name_}: `name` must be a str.   <{name}>")
        if(not self._names): raise AttributeError(f"{_name_}: there are no named attributes")
        if(name not in self._names): raise AttributeError(f"{_name_} object has no {name} attribute")
        return self._values[self._names[name]]

     
    def list(self, names=None):
        """Return a list of the data (value,sigma). If `names` is given, only these data (and in that order) are returned.

Parameters
----------
    names: sequence of indexes
        Sequence of the indexes of the data to be return as list of tuple
Return
------
    list : list of tuple
        List of tuple of 2 float (value,sigma)
        """
        if(names):   return [ self[key] for key in names]
        else :  return self._values[:]
  
###############################################################################
class IdXY(GenStructData):
    """Class for 2D point with ID (based on bclasses.GenStructData).

Parameters
----------
    data :
        Initialization data
    withid : bool
        If the object as an ID or not
    idn : int
        The integer version of the ID (>0)

Attributes for correct definition
---------------------------------
  _data_names : tuple  
        Tuple of the names of the variables in the order as they appear in the input data.
        Basic names (see also below 'Attributes names'):
          idx : str
            A string ID (optional)
          x,y : float
            Coordinates
  _data_init : tuple of class or coverters 
        Tuple of object convertibles, one for each item in _data_names
  _data_nfield : int
        Number of single datum for each input. Default len(_data_names).
  _data_nlines : int
        Number of line to be read for each source
  _data_delimiter : None, str, int, sequence
        The string used to separate values.  By default, any consecutive
        whitespaces act as delimiter.  An integer or sequence of integers
        can also be provided as width(s) of each field.
  _data_str : formatted str
        Formatted string naming the variable according to _data_names

Attributes names
----------------
A standard name for the uncertainty of a measurement is the name of the associated attribute with 
prefix 'e' (e.g. the attribute 'mag' has as attribute for its error 'emag').

Additional attributes
---------------------
    withid : bool 
        If the object has an ID (string or number)
    idn : int
        Additional integer ID passed during the initialization or get from `idx`. Default 0

Methods
-------
    setcoord(x,y)
        Set the coordinates
    shiftcoord(dx,dy)
        Add to the coordinates the given shift
    coordL,coordT,coordD
        Return the coordinates respectively as a 2D list, a 2D tuple, a dictionary {'x':x, 'y':y}}
    idxy
        Return (idx,x,y)
    flist
        Return a list of 

""";
    _data_names=(('idx', 'x', 'y'),)
    _data_nfield=(3,)
    _data_init=((str, float, float),)
    _data_str=("{idx:>12} {x:10f} {y:10f}",)
    _data_delimiter=(' ',)
    _data_nlines=1;
    
    (idx,idn, x,y)='-',0, 0.,0.;
    withid=True;
  
  
   ###__INIT__###
    def __init__(self, data=None, *, withid=None, idn=0):
        """IdXY object with 2D coordinates and eventually an ID.
  """;
        _name_='IdXY object';
        if(data is None): raise ValueError(_name_+": No data to create the object");
        if(isinstance(idn,int) and idn<0): raise ValueError(f"{_name_}: `idn` cannot be a negative number")
        self.idx="-";
        if(withid is not None):
            self.withid=withid
        else:
            if(len(data)==2):
                if(idn>0):
                    self.withid=True
                    data=(str(idn),)+tuple(data)
                else: self.withid=False
    
        if(not self.withid): #NO ID, remove it
            if('idx' in self._data_names[0]):
                if(self._data_names[0].index('idx')==0):
                    self._data_names=(self._data_names[0][1:],)+self._data_names[1:]
                    self._data_nfield=(len(self._data_names[0]),)+self._data_nfield[1:]
                    self._data_init=(self._data_init[0][1:],)+self._data_init[1:]
                    self._data_str=(self._data_str[0].split(self._data_delimiter[0],1)[1],)+self._data_str[1:]
                else: raise SkZpipeError(_name_+"The class has not been defined correctly! The defualt name for The ID attribute `idx` is put not at the beginning and the object is created without ID", exclocus=_name_);

        super().__init__(data=data) #=>bclasses.GenStructData
        
        if(not idn):
            from ...functions  import extractint
            nid=extractint(self.idx)
            if(nid is None):
                self.idn=0 
            else: #if idx is convertable in int
                self.idn=nid;
        else:
            self.idn=idn
    
    
      ###
    def setcoord(self, x, y):
        """Set the coordinates `x`, `y`"""
        selx,self.y=x,y;
    def shiftcoord(self, dx, dy):
        self.x+=dx;
        self.y+=dy;
    def coordL(self):
        """Return coordiantes as list"""
        return [self.x, self.y];
    def coordT(self):
        """Return coordiantes as tuple"""
        return (self.x, self.y);
    def coordD(self):
        """Return coordiantes as dict"""
        return {'x': self.x, 'y':self.y}
    def idxy(self):
        """Return idx and coordiantes as tuple"""
        return (self.idx, self.x, self.y);
    def flist(self):
        _names=list(self._data_names)
        if('idn' in _names): _names.remove('idn')

        if(self.idn):
            return [getattr(self, var) for var in ['idn']+_names];
        else:
            return [getattr(self, var) for var in _names];
    
###############################################################################
def unaliasvarname(var):
    """Revert alias for variable set to the singles values

Alias
-----
    Coordinates variables:
         'xy' : x,y(,z) 
         'xyz' : x,y,z
            For Cartasian coordinates
        'radec','equat' : ra,dec
            For Celestial Equatorial coordinates
        'lb','gal' : l,b
            For Galactic Coordinates
        'azh' : az,h
            For Local horintal coordinates

    """
    if(isinstance(var, tuple)):
        if(len(var)==1): return var, 'er_'+var
    if(var == 'xy'): return 'x','y'
    elif(var == 'xyz'): return 'x','y','z'
    elif(var == 'radec'): return 'ra','dec'
    elif(var == 'equat'): return 'ra','dec'
    elif(var == 'lb'): return 'l','b'
    elif(var == 'gal'): return 'l','b'
    elif(var == 'azh'): return 'az', 'h'

_coord_data_str={'x':" {x:10.4f}", 'y':" {y:10.4f}", 'z':" {z:10.4f}", 
                   'ra':" {ra:10.6f}", 'dec':" {dec:10.6f}", 'l':" {l:10.6f}", 'b':" {b:10.6f}", 'az':" {az:10.6f}", 'h':" {h:10.6f}", 
                   'idx':"{idx:10}",   'idn':"{idn:10d}",   '_coords':"9.5f", '_measures': '9.4f', '_singles': '9.4f'}

###############################################################################
class Point(IdXY):
    """2D-3D point

Parameters
----------
    data : tuple
        Input data with the coordinates
    ctype : str
        Desscription of the type of coordinates (the value will be passed to funtion unaliasvarname)
            'xy' : x,y
            'xyz' : x,y,z
            'radec' : ra,dec
            'lb' : l,b
            'azh' : az,h

        
"""
    def __init___(self, data, /, **kwargs):
    """ Point2 object"""
    _name_='Point object'

    ctype=unaliasvarname(kwards.get('ctype','xy'))
    if(isinstance(ctype,tuple)):
        _data_names=( ctype, )
        _data_nfield=(len(ctype), )
        _data_init=((float,float))
        _data_str=''
        for vv in ctype:
            _data_str+=_coord_data_str[vv]+self._data_delimiter
        _data_str=_data_str.rstrip()

    super().__init__(data, withid=False)


###############################################################################
"""
        _check_integrity(check_value)
            Method to check if the class is defined correctly
            Rememeber to run the parent _check_integrity  [ super()._check_integrity(check_value=check_value) ]
    _check_integrity(check_value=True)
        Method to check if the class is defined correctly
            check_value : bool
                Check if the variable listed in `_data_names` are set.

"""
def CheckClassDefinition(obj=None):
    """Check if a sub-class is defined correctly

Parameters
----------
    obj : obj
        Object whose class is to be checked.
""";
    _name_='CheckClassDefinition'
    if(isinstance(obj, GenStructData)):
        if(isinstance(obj, IdXY)):
            if(obj._data_nlines!=1): raise ValueError(_name_+":IdXY: `_data_nlines` for this king of object can be just 1. Use the multi-lines version");

        if(not isinstance(obj._data_nlines, int)): raise TypeError(_name_+": `_data_nlines` must be a positive integer");
        if(obj._data_nlines<1): raise ValueError(_name_+": `_data_nlines` must be a positive integer");
        if(not isinstance(obj._data_names, tuple)):  raise TypeError(_name_+": `_data_names` must be a tuple");
    
       #Checking multilines
        if(any( obj._data_nlines != len(x) for x in  (obj._data_names, obj._data_nfield, obj._data_init, obj._data_delimiter, obj._data_str) ) ):
            raise ValueError(_name_+"The class has not been defined correctly! `_data_nlines` is not the number of elements in `_data_names`, `_data_init` and the entries '{}' in `_data_str`");
       #Checking field number
        for ii in range(obj._data_nlines):
            if(any( obj._data_nfield[ii] != len(x) for x in  (obj._data_names[ii], obj._data_init[ii], re.findall("{.*?}", obj._data_str[ii])) ) ):
                raise SkZpipeError("The class has not been defined correctly! For the input line {nl}, `_data_nfield[{nl}]` <{nfld}> is not the number of elements in `_data_names[{nl}]` <{names}>, or `_data_init[{nl}]` <{formats}>, or the entries in `_data_str[{nl}] <{str_f}>`".format(nl=ii, nfld=obj._data_nfield[ii], names=obj._data_names[ii], formats=obj._data_init[ii], str_f=obj._data_str[ii]), exclocus=_name_);
   #Checking delimiters
        for ii in range(obj._data_nlines):
            if(isinstance(obj._data_delimiter[ii],tuple)):
                if(any( not isinstance(x,int) for x in obj._data_delimiter[ii])): 
                    raise TypeError(_name_+"The class has not been defined correctly! For the input line {nl}, `_data_delimiter[{nl}]` is a tuple but not of integer".format(nl=ii));
                if(len(obj._data_delimiter[ii])!=obj._data_nfield[ii]): 
                    raise ValueError(_name_+"The class has not been defined correctly! `_data_nfield[{nl}]` is not the number of elements in `_data_delimiter[{nl}]`".format(nl=ii));
    
       #Checking all the variable has a (default) value
        if(check_value):
            for ii in range(obj._data_nlines):
                for var in obj._data_names[ii]:
                    if(var!='-'):
                        if(not hasattr(obj, var)): 
                            raise SkZpipeError("The class has not been defined correctly! `{var}` for line {nl} of `_data_names` is not defined".format(var=var, nl=ii), exclocus=_name_);
    

class CtlgSource(GenStructData):
    """Class to store entries of a catalog with integer ID and three kinds of data: coordinates, measurements, single values.

Parameters
----------
    data : 
        Input data. All will be converted to float.
    idn : int
        ID of the entry (positive)
    delimiter : str or None
        Set of characters that saparate input values
    varnames : tuple or list
        List of variable name in the same order as the input data. It will be used to define _data_names.
        It can be used:
            alias for variable set;
            1D-tuple for measurement variable (to be expanded setting error name adding the suffix 'er_')
        If it not provide, coords+measures+singles will be used.
        The variable name for the integer ID must be 'idn'. 
    coords : tuple or tuple of tuples
        List of variables about coordinates (2D or 3D), using suggested alias for the set, or a tuple 
        of the list of the names.
    measures : tuple or tuple of tuples
        List of variables about mesurements (value + error). If only the variable name is provided, 
        it will be converted in a 2D tuple setting error name adding the suffix 'er_'.
    singles : tuple 
        List of variables with single value.
    str_format : str
        Formatted string; a sigle line with the format for the output.
    dtype_formats : tuple 
        Tuple of object convertibles, one for each item in varnames (store in in _data_init)


Best practice for variable names
--------------------------------
    The code prefers this rules for naming
    Coordinates variables:
        x,y(,z) : xy (xyz)
            For Cartasian coordinates
        ra,dec : radec
            For Celestial Equatorial coordinates
        l,b : lb
            For Galactic Coordinates
        az,h : azh
            For Local horintal coordinates

    Measurement variable:
        The error/uncertainty should be named adding the prefix 'e_' to the variable name: par,e_par ; vel,e_vel ; ...

    """
    _coords=()
    _measures=()
    _singles=()

    def __init__(self, data,/, **kwargs):
        """CtlgSource object to store single datum/entries from catalogs"""
        _name_="CtlgSource object"


        self._data_nlines=1
        self._data_delimeter=(None,)

        delim= kwargs.get('delimiter')
        idn= kwargs.get('idn')
        if('coords' in kwargs):
            tmpl=[]
            for vnm in kwargs['coords']:
                tmpt=unaliasvarname(vnm)
                if(tmpt): tmpl.append(tmpt)
                else: tmpl.append(vnm)
            self._coords=tuple(tmpl)
        if('measures' in kwargs):
            tmpl=[]
            for vnm in kwargs['measures']:
                if(isinstance(vnm, str)): vnm=(vnm, 'er_'+vnm)
                tmpl.append(vnm)
            self._measures=tuple(tmpl)
        if('singles' in kwargs):
            self._singles=tuple(kwargs['singles'])

        names=()
        for x in self._coords+self._measures:
            names+=x
        names=names+self._singles

        if('varnames' in kwargs):
            tmpl=[]
            for vnm in kwargs['varnames']:
                tmpt=unaliasvarname(vnm)
                if(tmpt): tmpl.extend(list(tmpt))
                else: tmpl.append(vnm)
            self._data_names=(tuple(tmpl),)
        else:
            tmpl=()
            for x in self._coords+self._measures:
                tmpl+=x
            self._data_names=(names,)
        
        if(not (self._coords or self._measures or self._singles) ): raise SkZpipeError(f"{_name_}: Neither 'coords' or 'measures' or 'singles' were defined!")
        self._data_nfield=tuple( len(x) for x in self._data_names )

        self._data_init=kwargs.get('dtype_formats')
        if(not self._data_init):
            self._data_init=[]
            formD={'idn':int, 'idx':str}
            for var in self._data_names[0]:
                self._data_init.append(formD.get(var, float))
            self._data_init=( tuple(self._data_init), )

        if(delim): self._data_delimeter=(delim,)

        if('str_format' in kwargs):
            self._data_str=kwargs['str_format']
        else:
            formD={**_coord_data_str}
            for tvar in self._coords:
                for var in tvar:
                    if(var not in formD):  formD[var]=f" {{{var}:"+_coord_data_str['_coords']+"}"
            for tvar in self._measures:
                for var in tvar:
                    if(var not in formD):  formD[var]=f" {{{var}:"+_coord_data_str['_measures']+"}"
            for var in self._singles:
                    if(var not in formD):  formD[var]=f" {{{var}:"+_coord_data_str['_singles']+"}"
            self._data_str=formD[ self._data_names[0][0] ]
            for var in self._data_names[0][1:]:
                self._data_str+=' '+formD[var] if(self.delim is None) else delim+formD[var]
                
    
        super().__init__(data, idn=idn)

#END CtlgSource    
##############################################################################################    
##############################################################################################    

class Catalog:
    """Class to store a catalog with entries that have an integer ID and three kinds of data: coordinates, measurements, single values.

Parameters
----------
    inputdata : str, list/tuple of entries, object with read/readline method, numpy.ndarray
        Input data.
    headerlen : int
        How many initial line have to be skipped. Anyway it skips automatically any line starting with '#'.
    id0 : int
        Eventual zero-point for ID of the entry (positive)
    delimiter : str or None
        Set of characters that saparate input values
    varnames : tuple or list
        List of variable name in the same order as the input data. It will be used to define _data_names.
        It can be used:
            alias for variable set;
            1D-tuple for measurement variables (to be expanded setting error name adding the suffix 'er_')
        If it not provide, coords+measures+singles will be used.
        The variable name for the integer ID must be 'idn', for the string ID must be 'idx'. 
    coords : tuple or tuple of tuples
        List of variables about coordinates (2D or 3D), using suggested alias for the set, or a tuple 
        of the list of the names.
    measures : tuple or tuple of tuples
        List of variables about mesurements (value + error). If only the variable name is provided, 
        it will be converted in a 2D tuple setting error name adding the suffix 'er_'.
    singles : tuple 
        List of variables with single value.
    str_format : str
        Formatted string; a sigle line with the format for the output.


Best practice for variable names
--------------------------------
    The code prefers this rules for naming
    Coordinates variables:
        x,y(,z) : xy (xyz)
            For Cartasian coordinates
        ra,dec : radec
            For Celestial Equatorial coordinates
        l,b : lb
            For Galactic Coordinates
        az,h : azh
            For Local horintal coordinates

    Measurement variable:
        The error/uncertainty should be named adding the prefix 'e_' to the variable name: par,e_par ; vel,e_vel ; ...

    """
    coords=()
    measures=()
    singles=()
    delim=None
    _idx=0

###########################################################################################################################
#  Hereafter an exact partial copy of the CtlgSource defined before and renamed CtlgSrc that will be used as inner class  #
#  CtlgSrc.__init__ is modified since most of the structure initialization is done by the Catalog.__init__                #
#  If CtlgSource is modified, remember to update CtlgSrc AND Catalog.__init__                                             #
###########################################################################################################################

    class CtlgSrc(GenStructData):
        """Class to store entries of a catalog with integer ID and three kinds of data: coordinates, measurements, single values.
    Mofified version of CtlgSource class with the structure initialization delegated to the Catalog.__init__.
    See documentation of CtlgSource class

    """
        _coords=()
        _measures=()
        _singles=()

        def __init__(self, data, **kwargs):
            """CtlgSrc object to store data from catalogs"""

            self._data_nlines=1
            self._data_delimeter=(None,)
    
            delim= kwargs.get('delimiter')
            idn= kwargs.get('idn')
            self._coords=kwargs['coords']
            self._measures=kwargs['measures']
            self._singles=kwargs['singles']
    
            self._data_names=(kwargs['varnames'],)
        
            self._data_nfield=tuple( len(x) for x in self._data_names )
            self._data_init=kwargs['dtype_formats']
            self._data_str=kwargs['str_format']
            if(delim): self._data_delimeter=(delim,)

            self._str_flen=kwargs['str_flen']
            self._str_llen=kwargs['str_llen']
                
            super().__init__(data, idn=idn)
###############################################################################
#  End of the copy-clone of the CtlgSource defined before and renamed CtlgSrc #
###############################################################################

    def __init__(self, inputdata,/, **kwargs):
        """Catalog object to store data from catalogs"""
      
        setid=True
        self.id0= kwargs.get('id0')
        if(not self.id0): self.id0=1
        hdrlen=kwargs.get('headerlen')
        if(not hdrlen): hdrlen=0

        #Initializing structure for inner class CtlgSrc
        if('coords' in kwargs):
            tmpl=[]
            for vnm in kwargs['coords']:
                tmpt=unaliasvarname(vnm)
                if(tmpt): tmpl.append(tmpt)
                else: tmpl.append(vnm)
            self.coords=tuple(tmpl)
        if('measures' in kwargs):
            tmpl=[]
            for vnm in kwargs['measures']:
                if(isinstance(vnm, str)): vnm=(vnm, 'er_'+vnm)
                tmpl.append(vnm)
            self.measures=tuple(tmpl)
        if('singles' in kwargs):
            self.singles=tuple(kwargs['singles'])

        names=()
        for x in self.coords+self.measures:
            names+=x
        names=names+self.singles

        if('varnames' in kwargs):
            tmpl=[]
            for vnm in kwargs['varnames']:
                tmpt=unaliasvarname(vnm)
                if(tmpt): tmpl.extend(list(tmpt))
                else: tmpl.append(vnm)
            self.varnames=tuple(tmpl)
            self.singles+=tuple(set(self.varnames)-set(names))
        else:
            self.varnames=names
        
        if(not self.singles ):
            self.singles=[]
            for var in self.varnames:
                if(not any(var in x for x in self.coords+self.measures ) ): self.singles.append(var)
            self.singles=tuple(self.singles)
        delim= kwargs.get('delimiter')
        if(delim): self.delim=delim

        self.dtype_formats=kwargs.get('dtype_formats')
        if(not self.dtype_formats):
            self.dtype_formats=[]
            formD={'idn':int, 'idx':str}
            for var in self.varnames:
                self.dtype_formats.append(formD.get(var, float))
            self.dtype_formats=( tuple(self.dtype_formats), )


        if('str_format' in kwargs):
            self.str_format=kwargs['str_format']
        else:
            formD={ **_coord_data_str}
            for tvar in self.coords:
                for var in tvar:
                    if(var not in formD):  formD[var]=f" {{{var}:"+_coord_data_str['_coords']+"}"
            for tvar in self.measures:
                for var in tvar:
                    if(var not in formD):  formD[var]=f" {{{var}:"+_coord_data_str['_measures']+"}"
            for var in self.singles:
                    if(var not in formD):  formD[var]=f" {{{var}:"+_coord_data_str['_singles']+"}"

            self.str_format=formD[ self.varnames[0] ]
            for var in self.varnames[1:]:
                self.str_format+=' '+formD[var] if(delim is None) else delim+formD[var]

        from ...functions  import extract_fieldlen
        ret_f, ret_l=[],[]
        fln,dln=extract_fieldlen( self.str_format, self.varnames) 
        self.str_flen, self.str_llen= fln, sum(fln+dln)

        #It need to add a ID?
        if('idn' in self.varnames): setid=False

        #Storing data
        if(isinstance(inputdata,str)): 
            #string data -> list of str
            if('\n'in inputdata): inputdata=inputdata.rstrip('\n').split('\n')
            #filename -> stream
            elif(os.path.exists(inputdata)): inputdata=open(inputdata)

        self.Ctlg=[]
        self.ndata=0
        if(hdrlen):
            for entry in inputdata:
                hdrlen-=1
                if(hdrlen==0): break

        
        idn=self.id0 if(setid) else None
        for entry in inputdata:
            if(isinstance(entry,str) and entry.startswith('#')): continue
            self.Ctlg.append(self.CtlgSrc( [entry.split(self.delim)], 
                idn=idn, delimiter=self.delim, varnames=self.varnames, coords=self.coords, measures=self.measures, singles=self.singles, 
                dtype_formats=self.dtype_formats,
                str_format=self.str_format, str_flen=self.str_flen, str_llen=self.str_llen ) )
            self.ndata+=1
            if(setid): idn+=1


    def array(self, just=None):
        """Return a array of the values of the provided variable names, or the full list in the same order of the name definition"""
        return numpy.array([ entry.list(just) for entry in self.Ctlg])

    def __getitem__(self, key):
        _name_='Catalog object'
        if(isinstance(key, int)): return self.Ctlg[key]
        elif(isinstance(key, str)):
            if( key in self.varnames): return [getattr(x, key) for x in self.Ctlg]
            else: raise ValueError(f"{_name_}: the variable doesn't exists.   <{key}>")
        else: raise TypeError(f'{_name_}: wrong type for key.   <{key}>')

    def __iter__(self):
        self._idx=0
        return self
    def __next__(self):
        if(self._idx<self.ndata):
            nval=self.Ctlg[self._idx]
            self._idx+=1
            return nval
        else:
            raise StopIteration
