"""Module with mathematical funtions
"""


import math, numpy, random;
from scipy.optimize import curve_fit as sp_curve_fit

from .exceptions import *
from .parameters  import basicpar as bpar
from .parameters  import options as _opt
from .parameters.classes  import bclasses


##TEMPLATE for function (15 lines)
############
def TEMPXXYYZZ():
    """Template of function and its Description

Parameters
----------
    x : obj
        X

Return
------
    x
"""
    _name_='XXYYZZ'

############
def sign(x=None):
    """Return the sign of the number

Parameters
----------
    x : int or float
        Number

Return
------
    sign : -1, 0, +1
        
"""
    _name_='sign'
    if(x==0): return 0
    if(x>0): return +1
    return -1

############
def hms2deg(ang=None):
    """Transform (h m s) format to decimal degrees

Parameters
----------
    ang : tuple
        Sequence of 3 floats

Return
------
    float
    Value in decimal degrees
"""
    _name_='hms2deg'
    if(isinstance(ang,str)): ang=ang.split(':') if(':' in ang) else ang.split()
    (hh, mm, ss)=tuple(ang)
    sgn=1
    if(any(isinstance(x,str) for x in ang)):
        if(isinstance(hh,str)): 
            if('-'in hh): sgn=-1
        (hh, mm, ss)=(float(x)  for x in ang)
    if(hh<0): sgn=-1

    d=mm/4.+ss/240.
    return 15.*hh+(d if(sgn>0) else -d )

############
def dms2deg(ang=None):
    """Transform (deg ' ") format to decimal degrees

Parameters
----------
    ang : tuple
        Sequence of 3 floats

Return
------
    float
    Value in decimal degrees
"""
    _name_='dms2deg'
    if(isinstance(ang,str)): ang=ang.split(':') if(':' in ang) else ang.split()
    (dd, mm, ss)=tuple(ang)
    sgn=1
    if(any(isinstance(x,str) for x in ang)):
        if(isinstance(dd,str)): 
            if('-'in dd): sgn=-1
        (dd, mm, ss)=(float(x)  for x in ang)
    if(dd<0): sgn=-1

    d=mm/60.+ss/3600.
    return dd+(d if(sgn>0) else -d )


############
def radec2decdeg(ra=None, dec=None):
    """Transform right ascension in hour format and declination in decimal degrees

Parameters
----------
    ra : sequence
        Sequence of 3 values for hour angle
    ang : tuple
        Sequence of 3 floats in sexagesimal units

Return
------
    x
"""
    _name_='radec2decdeg'
    return (hms2deg(ra), dms2deg(dec))



############
def eq2plane(ra=None, dec=None, ra0=None, dec0=None, theta=0, radec=None, radec0=None):
    """

Parameters
----------
    ra, dec : float
        Equatorial coordinates of the point
    ra0, dec0 : float
        Equatorial coordinates of the reference point
    theta : float
        Rotation angle pf the field
    

Return
------
    tuple
        Coordinates in the tangential plane.

""";
    if(isinstance(radec,tuple) and ra==None and dec==None): (ra,dec)=radec;
    if(isinstance(radec0,tuple) and ra0==None and dec0==None): (ra0,dec0)=radec0;
    a=math.cos(math.radians(dec))*math.cos(math.radians(ra-ra0));
    b=math.cos(math.radians(dec0))*a + math.sin(math.radians(dec))*math.sin(math.radians(dec0));
    x=60.*math.degrees( math.cos(math.radians(dec))*math.sin(math.radians(ra-ra0))/b );
    y=60.*math.degrees( ( math.cos(math.radians(dec0))*math.sin(math.radians(dec))-a*math.sin(math.radians(dec0)) )/b);
    return ( x*math.cos(math.radians(theta))-math.sin(math.radians(theta))*y, x*math.sin(math.radians(theta))+math.cos(math.radians(theta))*y );

######
def logerrmag(mag, a,b,c,d):
    """Relation amont magnitude and decimal logarithm of the error log10(emag)=c*( (0.4*(mag-a))**4 +b)**.25+d

Parameters
----------
    mag : float
        Magnitude for which calculate empyric logerr
    a,b,c,d : float
        Parameters of the function.
          a : minimum

""";
    return c*( (0.4*(mag-a))**4 +b)**.25+d;

############
def meanmag(values=None, mag=None, err=None):
    """Calculate the magnitude of the mean

Parameters
----------
    values : list of tuples (mag,err)
        List 

Return
------
    x
""";
    _name_='meanmag'
    if(values is None):
        if(mag is None or err is None): raise SkZpipeError(f"", exclocus=_name_);
        values=list(zip( mag,err))
    mag0=sum( mag/err**2 for mag,err in values )
    err0=sum( 1/(err*err) for mag,err in values )
    mag0/=err0
    err0=math.sqrt(err0)

    mm=numpy.mean(values, axis=0)[0] #mean of mag
    lum=numpy.power(10, [0.4*(mm-mag) for mag,err in values]) #rel lum 
    elum=(numpy.array(values)[:,1]*math.log(10)/2.5*mag1)**2   #err of rel lum
    lum0=numpy.power(10, 0.4*(mm-mag0))  #lum0
    for ii in range(100):
        corr=(lum-lum0)/(  elum+ 0.25*(lum-lum0)**2 )  


#############################################
def clipping_ratio(val1=None, err1=None, val2=None, err2=None, clip=None, shift=0, datum1=None, datum2=None):
    """Calculate the ratio for the data clipping between the difference of the input values and the clipping 
threshold: if greater than 1 it exceed the threshold; if the threshold is 0, 0 is return.

Parameters
----------
    val1,val2 : float
        Values of the data
    err1,err2 : float
        Uncertainties of the data
    clip : float, tuple of 2 float, tuple of 2 tuples of 2 float
        Values for data clipping. It is used to calculate the threshold of the clipping.
        It is possible to provide one value for when the difference is positive (first element), 
        and one for when the difference is negative. It is possible to provide two value and 
        keep the greatest threshold.
        If just a value is provided, it is propagated downwards.
        If the clipping value is positive, the threshold is obtained multiplying it by the difference 
        uncertainty. If negative, the threshold is the absolute value. If 0, the threshold is 1
    shift : float
        Shift to be apply to the difference `val1`-`val2`. Default 0
    datum1,datum2 : tuple of 2 float
        Values for (val1,err1) and (val2,err2) (alternative input method).

Return
------
    ratio : float
        A number greater or equal to zero. abs(val1-val2-shift)/thre
        If clipping value is 0, than abs(val1-val2-shift) is return

    """
    _name_='clipping_ratio'
    if(datum1 != None): 
        if(isinstance(datum1,tuple) and all(isinstance(x,(int,float)) for x in datum1)): (val1, err1)=datum1;
        else: raise TypeError(f"{_name_}: `datum1` must be None or a tuple (val,err).   <{datum1}>");
    if(datum2 != None): 
        if(isinstance(datum2,tuple) and all(isinstance(x,(int,float)) for x in datum2)): (val2, err2)=datum2;
        else: raise TypeError(f"{_name_}: `datum2` must be None or a tuple (val,err).   <{datum2}>");
    if(not all(isinstance(x,(int,float)) for x in (val1, err1) )): 
        raise TypeError(f"{_name_}: `val1`,`err1` must be a number   <{val1} , {err1}>");
    if(not all(isinstance(x,(int,float)) for x in (val2, err2) )): 
        raise TypeError(f"{_name_}: `val2`,`err2` must be a number   <{val2} , {err2}>");

    if(isinstance(clip, (float,int))): clip=((clip,clip),(clip,clip))
    if((not isinstance(clip, (tuple,list))) or len(clip)!=2): 
        raise TypeError(_name_+": `clip` must be a number, or sequence of 2 numbers, or s sequence of 2 sequence of 2 numbers");
    clip=list(clip)
    for ii in (0,1):
        if(isinstance(clip[ii], (float,int))): clip[ii]=(clip[ii],clip[ii])
  
    thre=[0,0]
    dval=val1-val2-shift;
    if(dval>=0):
        thre[0]=(clip[0][0]*sqrt(err1**2+err2**2)) if(clip[0][0]>0) else ( abs(clip[0][0]) if(clip[0][0]<0) else 1);
        thre[1]=(clip[0][1]*sqrt(err1**2+err2**2)) if(clip[0][1]>0) else ( abs(clip[0][1]) if(clip[0][1]<0) else 1);
        thre[0]=max(thre);
    else:
        dval*=-1;
        thre[0]=(clip[1][0]*sqrt(err1**2+err2**2)) if(clip[1][0]>0) else ( abs(clip[1][2]) if(clip[1][0]<0) else 1);
        thre[1]=(clip[1][1]*sqrt(err1**2+err2**2)) if(clip[1][1]>0) else ( abs(clip[1][3]) if(clip[1][1]<0) else 1);
        thre[0]=max(thre);
    if(thre[0]==0): thre[0]=1
    return dval/thre[0]


#########
def freq_val2index(x,x0,wd,st):
    return numpy.int64(numpy.floor( (x-x0-wd)/st )+1)
def freq_index2val(i,x0,wd,st):
    return  (x0+0.5*wd+i*st );

def convfreq2d(datain=None, options=None, excl=None, shape='box', verb=False):
    """Calculate convolute frequency.

Parameters
----------
    datain : ndarray
        Numpy 2D-array with input data. 
    options : list of dicts
        List of a dictionary with options for each coordinate of the data points.
        It is actualized by the procedure.
          Format of the dict:
            'min' : float
               Minimum value
            'wd' : float
               Width of the bin along that axis
            'st' : float
               Step of the bin along that axisa. If not given will be set equal to 'wd'.
            'n#' : int
               Number of the bins along that axis
            'max' : float
               Greatest value not included in the frequency. Used only to calculate the number of bin, 
               not actually used by the procedure.
        If a value is not given, it will be calculated according to 'max'='min'+'wd'+('n#'-1)*'st'. When 'n#' is calculated (with ceil), 'max' will be recalculated.
    excl : list
        Output (it is replaced). List where the number of excluded data points will be store (see below in Other outputs).
    shape : str
        Shape of the bin: 'box' for a n-cube; 'circle' for a n-sphere. 
    verb : bool
        Verbosity flag

Return
------
    out : numpy.ndarray
        Array with the convoluted frequencies.

Other outputs
-------------
    excl : list
        List with two elemnets as the number of excluded data points. 
        The first value is the number of the data point excluded because one of the value is lower than its correspective minimum. 
        The second value is the number of the data point excluded later because one of the value is greater or igual to its correspective maximum.
 
""";
    _name_='convfreq2d';
    try:
        datain=numpy.array(datain);
    except:
        raise TyprError(_name_+": `datain` must be a numpy ndarray or compatible object.");
    ndim=datain.ndim;
    if(ndim not in (1,2)): raise SkZpipeError("The dimension of `datain` must be 1 or 2. Not yet implemented for more dimensions", exclocus=_name_);
    if(ndim==1 or (ndim==2 and 1 in datain.shape)): 
        datain=datain.reshape((datain.size,1))
        ndim=1
    ndat,nvar=datain.shape
    if(nvar!=len(options)): raise SkZpipeError(f"The length of `options` must be the same as the number of columns (variables) of `datain`.   <{len(options)} ; {nvar}>", exclocus=_name_);
  
    if(not options or not isinstance(options, (list,tuple)) or any(not opt or not isinstance(opt,dict) for opt in options)): raise TypeError(_name_+": 'opt' must be a list of dict");
    if(excl is not None and not isinstance(excl,list)): raise TypeError(_name_+": `excl` must be a list or None");
    if(excl is None): excl=[];
    excl[:]=[0,0];
    if(not isinstance(shape, str)): raise TypeError(_name_+": `shape` must be a str");
    if(not isinstance(verb, bool)): raise TypeError(_name_+": `verb` must be a bool");
    if(_opt.SkZp_Opt['Flg']['debug']): verb=True;
  
    narr=[];
    minv=datain.min(axis=0);
    maxv=datain.max(axis=0);
  #Fixing Options
    for ii,opt in enumerate(options): #One option for each dimension
        if('wd' in opt and opt['wd']<=0): raise SkZpipeError(f"In `options` of variable {ii} 'wd' is not positive: senseless", exclocus=_name_)
        if('n#' in opt and opt['n#']<=0): raise SkZpipeError(f"In `options` of variable {ii} 'n#' is not positive: senseless", exclocus=_name_)
        if('st' in opt): 
            if( opt['st']<=0): raise SkZpipeError("In `options` of variable {ii} 'st' is not positive: senseless", exclocus=_name_)
            if('wd' in opt and opt['st']>opt['wd']): raise SkZpipeError("In `options` of variable {ii} 'st' is greater than 'wd': senseless", exclocus=_name_)

        if('st' not in opt):
            if('wd' not in opt and all(x in opt for x in ('max','min','n#'))): opt['wd']=(opt['max']-opt['min'])/opt['n#'];
            if('wd' in opt):   opt['st']=opt['wd']
    
        if('min' not in opt):
            if(all(x in opt for x in ('max','wd','st','n#'))):  opt['min']=opt['max']-opt['wd']-(opt['n#']-1)*opt['st'];
            else:   opt['min']=minv[ii];
        if('max' not in opt):
            if(all(x in opt for x in ('min','wd','st','n#'))):  opt['max']=opt['min']+opt['wd']+(opt['n#']-1)*opt['st'];
            else:   opt['max']=maxv[ii];
    
        if('st' not in opt):
            if('wd' not in opt and all(x in opt for x in ('max','min','n#'))): opt['wd']=(opt['max']-opt['min'])/opt['n#'];
            if('wd' in opt):   opt['st']=opt['wd'];
        if(all(x in opt for x in ('min','max','wd','st','n#'))): pass
        elif('min' not in opt and all(x in opt for x in (      'max','wd','st','n#'))):   opt['min']=opt['max']-opt['wd']-(opt['n#']-1)*opt['st'];
        elif('max' not in opt and all(x in opt for x in ('min',      'wd','st','n#'))):   opt['max']=opt['min']+opt['wd']+(opt['n#']-1)*opt['st'];
        elif('wd'  not in opt and all(x in opt for x in ('min','max',     'st','n#'))):   opt['wd']=opt['max']-opt['min']-(opt['n#']-1)*opt['st'];
        elif('n#'  not in opt and all(x in opt for x in ('min','max','wd','st'     ))):
            opt['n#']=freq_val2index(opt['max'], opt['min'], opt['wd'], opt['st'])
            tmpv=opt['min']+opt['wd']+(opt['n#']-1)*opt['st'];
            if(opt['max']>tmpv):  opt['max']=tmpv;
        else: raise SkZpipeError(f"Not enough options to calculate frequencies.  <{opt}>", exclocus=_name_);
          
        narr.append(opt['n#']);
    frout=numpy.zeros(narr, dtype=numpy.uint32);
    if(nvar==1): shape='box';
  
    if(verb): 
        for ii in range(len(options)):
            print("""Axis {axis}
      minimum (included):  {xmin}
      number of bins:      {xn}
      bin's width:         {xwd}
      step:                {xst}
      maximum (excluded):  {xmax}
  """.format(axis=ii, xmin=options[ii]['min'], xmax=options[ii]['max'], xwd=options[ii]['wd'], xst=options[ii]['st'], xn=options[ii]['n#'], ), file=bpar.SkZp_Par['stdout']);
  
  #Frequencies
    if(shape=='box'):
        if(options[0]['wd']==options[0]['st']):
            datain=datain.transpose()

            pos=numpy.zeros(datain.shape, dtype=numpy.int64)
            for ii in range(nvar): #data value => index value
                pos[ii]=freq_val2index(datain[ii], options[ii]['min'], options[ii]['wd'], options[ii]['st'])
            oshape=tuple(options[ii]['n#'] for ii in range(nvar))

            for idx,freq_i in zip(*numpy.unique( numpy.array(list(zip(*tuple(x[0] for x in numpy.split(pos, nvar)))), ','.join(['i']*nvar)), return_counts=True)):
                idx=tuple(idx) if(nvar>1) else (idx,)
                if(any( ii<0  for ii in idx )):
                    excl[0]+=1;
                elif(any( idx[ii]>=options[ii]['n#'] for ii in range(nvar) )):
                    excl[1]+=1;
                else:
                    frout[idx]=freq_i
        else:
            datain=datain.transpose()
            bound=numpy.zeros(datain.shape+(2,), dtype=numpy.int64)
            for ii in range(nvar):
                bound[ii,:,0]=numpy.maximum(numpy.zeros(datain[ii].shape),                   freq_val2index(datain[ii], options[ii]['min'], options[ii]['wd'], options[ii]['st']) )
                bound[ii,:,1]=numpy.minimum(numpy.zeros(datain[ii].shape)+options[ii]['n#'], freq_val2index(datain[ii], options[ii]['min'],                 0, options[ii]['st']) )

            posL=[]

            from itertools import product
            for idt in range(ndat):
                if( any( bound[ii,idt,0]>=options[ii]['n#'] for ii in range(nvar)) ):
                    excl[1]+=1
                elif( any(bound[ii,idt,1]<=0  for ii in range(nvar)) ):
                    excl[0]+=1
                else: posL.extend( list(product( *(range(x[0], x[1]) for x in bound[:,idt,:] ) )) )

            for idx,freq_i in zip(  *numpy.unique( numpy.array(posL, dtype=','.join(('i',)*nvar)), return_counts=True)  ):
                idx=tuple(idx) if(nvar>1) else (idx,)
                frout[idx]=freq_i

    elif(shape=='circle'):
        for data in datain:
            idx=tuple((numpy.maximum(numpy.zeros(data[ii].shape),                   freq_val2index(data[ii], options[ii]['min'], options[ii]['wd'], options[ii]['st']) ), 
                       numpy.minimum(numpy.zeros(data[ii].shape)+options[ii]['n#'], freq_val2index(data[ii], options[ii]['min'],                 0, options[ii]['st']) ) )
                      for ii in range(nvar) )
            if(any( idx[ii][1]<0  for ii in range(nvar) )):   excl[0]+=1;
            elif(any( idx[ii][0]>=options[ii]['n#'] for ii in range(nvar) )):   excl[1]+=1;
            else:
                rangeL, idx=[],[]
                for ii in range(nvar):
                    x0= max(                0 , freq_val2index(data[ii], options[ii]['min'], options[ii]['wd'], options[ii]['st']) ); #First index in
                    x1= min(options[ii]['n#'] , freq_val2index(data[ii], options[ii]['min'],                 0, options[ii]['st']) ); #First index greater than in
                    rangeL.append( ( x0,x1 ) );
                    idx.append(x0)
                rangeL.append((0,0));
                idx.append(0);
                while(True):
                    r=0;
                    for ii in range(ndim):
                        r+=( (data[ii]-options[ii]['min']-options[ii]['st']*idx[ii])/options[ii]['wd'] -0.5 )**2;
                    if(r<0.25): frout[tuple(idx[:-1])]+=1;
                    for ii in range(ndim+1):
                        idx[ii]+=1;
                        if(idx[ii]<=rangeL[ii][1]): break;
                        else: idx[ii]=rangeL[ii][0];
                    if(idx[-1]): break;
    
    if(verb): print(f"""Number of excluded points:
      Points lesser than the minimums:  {excl[0]}
      Other points greater than the maximums: {excl[1]}
      """, file=bpar.SkZp_Par['stderr']);
  
    return frout;

#####

def freq2maxline(datain=None, axis=1, smooth=True, nmin=5):
  """Calculate the lines of the maximums in the frequencies

Parameters
----------
    datain : numpy.ndarray
        2D Array with the frequencies.
    axis : int
        Axis to be considered dependent variable, along which to find the maximum (while keeping fixed the value of the other). Default 1
    smooth : bool
        If the output has to be smooth (with a 3-element mean). Default True.
    nmin : int
        Minimum value for the maximum to be considered.

Return
------
    output : numpy ndarray
        2D Numpy array with positions of maximum (indipendent variable, dependent variable).
""";
  _name_='freq2maxline';
  try:
    datain=numpy.array(datain);
  except:
    raise TyprError(_name_+": `datain` must be a numpy ndarray or compatible object.");
  shape=datain.shape;
  if(len(shape)!=2): raise SkZpipeError("`datain` must be 2D array", exclocus=_name_);
  if(axis not in (0,1)): raise ValueError(_name_+": `axis` must be 0 or 1 (`datain` must be 2D array)");

  posmax=datain.argmax(axis=axis);
  maxline, sigma=[],[];
  ii0, ii1=0, shape[1-axis]-1;
  for ii,pm in enumerate(posmax):
    xwsum=0;
    pm0,pm1 = pm-2, pm+2+1;
    if(pm0<0): pm0=0;
    if(pm1>=shape[axis]): pm1=shape[axis]-1;
    if(axis==0):
      if(datain[pm, ii]<nmin): wei=0;
      else:
        xwsum=(datain[pm0:pm1, ii]*numpy.arange(pm0, pm1)).sum();
        x2wsum=(datain[pm0:pm1, ii]*numpy.arange(pm0, pm1)**2).sum();
        wei=datain[pm0:pm1, ii].sum();
    elif(axis==1): 
      if(datain[ii, pm]<nmin): wei=0;
      else:
        xwsum=(datain[ii, pm0:pm1]*numpy.arange(pm0, pm1)).sum();
        x2wsum=(datain[ii, pm0:pm1]*numpy.arange(pm0, pm1)**2).sum();
        wei=datain[ii, pm0:pm1].sum();
    else:  raise ValueError(_name_+": `axis` must be 0 or 1 (`datain` must be 2D array)");

    if(wei):
      idmax=xwsum/wei;
      sig=math.sqrt(x2wsum/wei-idmax**2);
    elif(ii>0.66*shape[0]):
      ii1=ii;
      break;
    elif(ii==ii0):
      ii0+=1;
      continue;
    else:
      idmax=maxline[-1];
      sig=sigma[-1];
    maxline.append(idmax);
    sigma.append(sig);

  if(smooth):
    tmpl=maxline.copy();
    for ii in range(1,len(maxline)-1):
      maxline[ii]=sum(tmpl[ii-1:ii+2])/3;

  return numpy.array( list(zip(range(ii0,ii1-1), maxline, sigma)) );

######
def findextrema(datain=None, what='min', erange=1, mode='all', indexout=None):
  """Find extrema points (minimum or maximum) in a set of data.

Parameters
----------
    array : numpy.ndarray
        2D Array with the x,y data.
    what : str
        Type of extremum to find: 'min' (default) for minima; 'max' for maxima.
    erange : int
        Number of points before and after to analize to determine the maximum/minimum. Default 1.
    mode : str
        How to compare the point with  the previous and following points (+-erange): 'all' (default) to compare with each point; 'mean' to compare with the mean of the two groups.
    indexout : None or list
        Alternative output in which to append the list of the positions of the extrema.

""";
  _name_='findextrema';
  try:
    datain=numpy.array(datain);
  except:
    raise TyprError(_name_+": `datain` must be a numpy ndarray or compatible object.");
  shape=datain.shape;
  if(len(shape)!=2): raise SkZpipeError("`datain` must be 2D array", exclocus=_name_);
  if(not isinstance(what,str)): raise TypeError(_name_+"`what` must be a str ('min' or 'max')");
  if(what not in ('min','max')): raise ValueError(_name_+"`what` must be a str ('min' or 'max')");
  if(not isinstance(erange,int)): raise TypeError(_name_+"`erange` must be a positive integer");
  if( erange<1): raise ValueError(_name_+"`erange` must be a positive integer");
  if(not isinstance(mode,str)): raise TypeError(_name_+"`mode` must be a str ('mean' or 'all')");
  if(mode not in ('mean','all')): raise ValueError(_name_+"`mode` must be a str ('mean' or 'all')");
 
  if(not isinstance(indexout,list)): indexout=[];
  if(what=='min'):
    if(mode=='mean'):
      for ii in range(erange, len(datain)-erange):
        vprev=datain[ii-erange:ii, 1].mean();
        vnext=datain[ii+1:ii+erange+1, 1].mean();
        if(datain[ii, 1]<=vprev and datain[ii, 1]<=vnext): indexout.append(ii);
    elif(mode=='all'):
      for ii in range(erange, len(datain)-erange):
        count=0;
        for jj in range(erange):
          if(datain[ii, 1]<=datain[ii-jj-1, 1]  and  datain[ii, 1]<=datain[ii+jj+1, 1]): count+=1;
        if(count==erange): indexout.append(ii);
    else: raise ValueError(_name_+"`mode` must be a str ('mean' or 'all')");
  else: # what=='max'
    if(mode=='mean'):
      for ii in range(erange, len(datain)-erange):
        vprev=datain[ii-erange:ii, 1].mean();
        vnext=datain[ii+1:ii+erange+1, 1].mean();
        if(datain[ii, 1]>=vprev and datain[ii, 1]>=vnext): indexout.append(ii);
    elif(mode=='all'):
      for ii in range(erange, len(datain)-erange):
        count=0;
        for jj in range(erange):
          if(datain[ii, 1]>=datain[ii-jj-1, 1]  and  datain[ii, 1]>=datain[ii+jj+1, 1]): count+=1;
        if(count==erange): indexout.append(ii);
    else: raise ValueError(_name_+"`mode` must be a str ('mean' or 'all')");

  return datain[indexout,:];

############
def curvefit_mag_logemag(datain=None, freqoption=None, nmin=5):
  """Calculate the coefficient for the relation between magnitude and the logarithm of the uncertainty based on logerrmag. It uses scipy.optimize.curve_fit

Parameters
----------
    datain : numpy array
        2D array with input data
    freqoption : dict of dicts
        Disctionary with keys 0 and 1 containing dictionaries with options for the frequencies in the two data column
    nmin : int
        Minimum number of sources

Return
------
    output : as scipy.optimize.curve_fit
        Output of scipy.optimize.curve_fit
""";
  _name_='curvefit_mag_logemag';

  if(not freqoption):
    freqoption=[{ 'wd':0.3, 'st':0.2}, { 'wd':0.005, 'st':0.001}];
  m_min,e_min=numpy.round(datain.min(axis=0), 3);
  m_max,e_max=numpy.round(datain.max(axis=0), 3);
  freqoption[0].setdefault('min', m_min);
  freqoption[1].setdefault('min', e_min);
  freqoption[0].setdefault('max', m_max);
  freqoption[1].setdefault('max', e_max);
  excl=[];
  frarr=convfreq2d(datain=datain, options=freqoption, excl=excl, verb=False);
  maxline=freq2maxline(datain=frarr, nmin=nmin);
  linetofit=numpy.array([[freq_index2val(i=ii, x0=freqoption[0]['min'], wd=freqoption[0]['wd'], st=freqoption[0]['st']), numpy.log10(freq_index2val(i=jj, x0=freqoption[1]['min'], wd=freqoption[1]['wd'], st=freqoption[1]['st'])), freqoption[1]['st']*ss/math.log(10)/freq_index2val(i=jj, x0=freqoption[1]['min'], wd=freqoption[1]['wd'], st=freqoption[1]['st']) ] for ii,jj,ss in maxline]);

  minpos,maxpos=[],[];
  erange=int(math.ceil(1./freqoption[0]['st'])); #size in step of 1 mag
  minL=findextrema(datain=linetofit, what='min', erange=erange, mode='all', indexout=minpos);
  maxL=findextrema(datain=linetofit, what='max', erange=erange, mode='all', indexout=maxpos);
  #print(minpos, minL, maxpos, maxL) #@@@@
  m0,err0=minL[-1,:2] if(len(minL)) else maxline[erange,:2];
  if(len(maxL)!=0):
    if(len(minL)==1):
      if(maxpos[-1]<minpos[-1]): linetofit=linetofit[maxpos[-1]-1: , :];
    elif(maxpos[-1]<minpos[-1]): 
      linetofit=linetofit[maxpos[-1]-1: , :];
  
  return sp_curve_fit( f=logerrmag, xdata=linetofit[:,0], ydata=linetofit[:,1], sigma=linetofit[:,2], p0=[m0, 1, 1, err0-1], bounds=([m0-2, 0, .8, -4],[m0+2, 20, 1.2, 0]) );
  
 

############
def isinsidebox(point=None, vertices=None, test=True):
  """Check if a point is inside a box, or not

Parameters
----------
    point : 2-tuple or list of 2-tuple or numpy 2D array
        Coordinates of the point or list of coordinates
    vertices : list of 2-tuples or numpy 2D array
        Array-compatible list of the 4 vertices, each represented by a 2 coordinates.
    test : bool
        If True, the function test the parameter for being inside (<=1) and returns bools for each point.
        If False, the funtion return directly the parameter.

Return
------
    out : array of bool or array of values
        A bool for each input point.
""";
  _name_='isinsidebox';

  if(isinstance(point, tuple)): point=numpy.array([point]);
  else: point=numpy.array(point);
  if(not isinstance(point, numpy.ndarray)): raise TypeError(_name_+": `point` must be a 2-tuple, or compatible with a (,2) numpy.ndarray");
  if(point.shape[1]!=2): raise TypeError(_name_+": `point` must be a 2-tuple or a list of 2-tuples");
  vertices=numpy.array(vertices);
  if(vertices.shape!=(4,2)): raise TypeError(_name_+": `point` must be campatible with a (4,2) numpy.array");
  
  bar=vertices.mean(axis=0);
  vertices=vertices-bar;
 
  cval= numpy.sqrt(2./numpy.square(vertices).sum(axis=0));
  tmpa=cval*vertices;
  cpix=numpy.array([-tmpa[0,0]-tmpa[1,1]+tmpa[2,0]+tmpa[3,1], -tmpa[0,1]+tmpa[1,0]+tmpa[2,1]-tmpa[3,0]] )*0.25;
  icpix=numpy.array([cpix[1], -cpix[0]]);

  if(test):
    return numpy.round(abs(((point-bar)*cval*cpix).sum(axis=1))+abs(((point-bar)*cval*icpix[[1,0]]).sum(axis=1)),6)<=1;
  else:
    return numpy.round(abs(((point-bar)*cval*cpix).sum(axis=1))+abs(((point-bar)*cval*icpix[[1,0]]).sum(axis=1)),6);


############
def discretedistrition(xmin=None, xmax=None, dx=None, nx=None, dfunct=None, dy=None, npart=None):
  """Create a discrete distribution to obtain random values according a given density distribution. The function samples the [xmin:xmax] range of x-axis in `dx`-long or  `nx` bins, while in the y-axis in `dy`-long bins or to sample the area of the density function (in the range [xmin:xmax]) with `nbin` parts. The random values can be obtain simply taking the n-value from the list, with n obtain from multiplying the size of the list by a random number. The `dx` value permit to cover all the bin width with an additional random value.

Parameters
----------
    xmin : float
        Minimum value of the variable
    xmax : float
        Maximum value of the variable
    dx : float
        Width of the bins along x-axis
    nx : int
        Number of bins in the x-axis
    dfunct : callable
        Callable that accept a parameter and return the density distribution at that value
    dy : float
        Width of the step to sample the distribution
    npart : int
        Number of parts to sample the distribution in the given range ([xmin:xmax]).

Return
------
    Dictionary with:
      'distr' : list
          List of x-values of the lower border of the bins.
      'dx' : float
          Width of the x-bins
""";
  _name_='discretedistrition';

  if(not isinstance(xmin, (int,float))): raise TypeError(_name_+": `xmin` must be a float");
  if(not isinstance(xmax, (int,float))): raise TypeError(_name_+": `xmax` must be a float");
  if(dx is not None and not isinstance(dx, (int,float))): raise TypeError(_name_+": `dx` must be a float");
  if(nx is not None and (not isinstance(nx, int) or nx<=0) ): raise TypeError(_name_+": `nx` must be a positive integer");
  if(dx is None and nx is None): raise ValueError(_name_+": `dx` and `nx` cannot be both undefined");
  if(dx is not None and nx is not None): raise ValueError(_name_+": `dx` and `nx` cannot be both defined");

  if(not callable(dfunct)): raise TypeError(_name_+": `dfunct` must be a callable");

  if(dy is not None and not isinstance(dy, (int,float))): raise TypeError(_name_+": `dy` must be a float");
  if(npart is not None and (not isinstance(npart, int) or npart<=0) ): raise TypeError(_name_+": `npart` must be a positive integer");
  if(dy is None and npart is None): raise ValueError(_name_+": `dy` and `npart` cannot be both undefined");
  if(dy is not None and npart is not None): raise ValueError(_name_+": `dy` and `npart` cannot be both defined");

  if(nx is not None): dx=(xmax-xmin)/nx;
  else:
    nx=math.ceil((xmax-xmin)/dx);
    xmax=xmin+nx*dx;
  
  hlist=[ (dfunct(xmin+ii*dx)+dfunct(xmin+(ii+1)*dx)+dfunct(xmin+(ii+0.5)*dx))/3. for ii in range(nx) ];
  vol=sum(hlist);

  if(npart is not None):
    dy=vol/npart;
  else:
    npart=math.ceil(vol/dy);
  
  hlist=[max(1,round(hx/dy)) for hx in hlist];
  npart=sum(hlist);

  distrL=[];
  for ii in range(nx):
    distrL.extend( [ xmin+ii*dx ]*hlist[ii]  );
  
  return {'distr':distrL, 'dx':dx, 'xmin':xmin, 'nx':nx};

####
def randomcatalog(nsrc=1000, seed=None, fieldsize=None, mag=(8,22,0.1), coordtransf=None, output='randomsources', fmt=('%10.6f',  '%10.6f',  '%8.3f')):
  """Generate a catalog of artificial stars

Parameters
----------
    nsrc : int
        Number of artificial sources
    seed : int or compatible (see random.seed)
        Seed to initialize the random number generator (for reproducibility)
    fieldsize : number, tuple or 2 numbers
        The size of the 2D field of view (supposed rettangular)
    mag : tuple of floats
        Tuple (min, max[,step]) containing minimum and maximum magnitude for the sources. The step can be provided,
        otherwise a continuos distribution will be considered (step=0).
    coordtransf : bclasses.CoordTransf object or compatible
        Coordinate transformation to be applied to the rectangular field.
    output : str
        Filename of the output. Default 'randomsources'
""";
  _name_='randomcatalog';

  if(not isinstance(nsrc,int) or nsrc<=0): raise TypeError(_name_+": `nsrc` has to be a positive integer");
  if(isinstance(fieldsize,(int,float))): fieldsize=(fieldsize,fieldsize);
  if(not isinstance(fieldsize,tuple) or len(fieldsize)!=2): raise TypeError(_name_+": `fieldsize` has to be a tuple of 2 number");
  if(not isinstance(mag,tuple) or len(mag) not in (2,3)): raise TypeError(_name_+": `mag` has to be a tuple of 2 or 3 float");
  if(not isinstance(output,str)): raise TypeError(_name_+": `output` has to be a string");

  lx,ly=fieldsize;
  
  if(len(mag)==2): mag+=(0,);
  magmin,magmax,magst=mag;
  ctransf=bclasses.CoordTransf(coordtransf);

  random.seed(seed);
  srcL=[];
  if(magst>0):
    nstep=int(math.ceil((magmax-magmin)/magst))+1;
    for ii in range(nsrc):
      x,y,amag = random.uniform(0,lx), random.uniform(0,ly), magmin+magst*random.randrange(nstep);
      x,y=ctransf.do((x,y));
      srcL.append([x,y,amag]);
  else:
    for ii in range(nsrc):
      x,y,amag = random.uniform(0,lx), random.uniform(0,ly), random.uniform(magmin,magmax);
      x,y=ctransf.do((x,y))
      srcL.append([x,y,amag])
   
  srcL=numpy.array(srcL);
  numpy.savetxt(output, srcL, fmt=fmt);
  return srcL;


######
def krdelta(index=None):
  """Kronecker delta

Parameters
----------
    index : tuple
        Iterable with the indexes
""";
  _name_='krdelta'
  if(len(index)<2): raise ValueError(_name_+": `index` musta have more than 1 element. <{}>".format(index));
  return 1 if(len(set(index))==1) else 0;


######
def fudgedlinearfit(ydata=None, erry=None, xdata=None, fudge=None, guess=None, options=None):
  """Calculate the  linear least square fit applying a 'fudging' factor to the weight. 

It takes a dependent variable and #var independent variables and calculate a regression to obtain the #var coefficients.
The intersect is considered as a variable with all data values equal to 1 (and error 0).
Based on http://ned.ipac.caltech.edu/level5/Stetson/Stetson_contents.html

Parameters
----------
    ydata : list or ndarray
        Iterable with #data value of the dependent variable. It will be recast as a (#data) Numpy array 
    erry : list or ndarray
        Iterable with #data value of the errors of dependent variable. It will be recast as a (#data) Numpy array 
    xdata : ndarray
        Numpy array (#data, #var) with #data value of the errors of the #var independent variable.
        It will be recast as a (#data, #var) Numpy array 
    fudge : callable or dict
        Callable that take as input the residual array and sigma and retuen the 'fudging factor'
        (a value between 0 and 1) by which the weight will be multiply.
        Or dictionary with one key as identifier of the function, and the value is a dictionary with parameters.
          'pbs' : P. B. Stetson fudging function (a 'Moffat-like' function: 1/(1+|x/(a*sigma)|**b))
                 'a' : float or tuple of 2 float
                      Parameter 'a' that defines the FWHM in sigma. A general one or a couple of value (up,down),
                      the first for positive residuals (x>0), the seconnd for negative residuals (x<0) (not working with 2 different values).
                      Default 2.
                 'b' : float or tuple of 2 float
                      Parameter 'b' that defines the shape. A general one or a couple of value (up,down),
                      the first for positive residuals (x>0), the seconnd for negative residuals (x<0) (not working with 2 different values)..
                      Default 4.
        As callable, it has to accept a array as input and manage conditional case consenquently. Se following example
          def pbsfudge(x=0, sigma=1, a=(2,2), b=(4,4)):
              mask=(x>=0);
              ret=numpy.ones(x.shape)
              ret[ mask]= 1/(1+abs(x[ mask]/(a[0]*sigma))**b[0]);
              ret[~mask]= 1/(1+abs(x[~mask]/(a[1]*sigma))**b[1]);
              return ret;

    guess : list or ndarray
        Iterable with #var initial value of fitting coefficients.
    options : dict
        Dictionary with options
          'niter' : int
                Maximum number of iterations
          'enough' : float
                Smalllest relative variation of a coefficient to stop the iteration
          'en_flag' : 'any' or 'all'
                If to stop the iteration if any coefficient has the smallest relative variation, or if all the coefficients have the smallest relative variation.

Return
------
   out : dict
        Dictionary with output informatio:
          'niter' : int
                Number of iterations
          'ndata' : int
                Number of data
          'nvar' : int
                Number of variables
          'rms' : float
                Root mean square
          'me1' : float
                "mean error of unit weight" (the mean error, or the correct value of sigma, corresponding to a data point with w = 1)
          'wsigma' : float
                Weighted rms
          'coeff' : ndarray
                1d-array with the values of the coefficients
          'error' : ndarray
                1d-array with the values of errors of the coefficients
          'corr' : ndarray
                2d-array with correlations among the variable
          'fudge' : dict
                Dictionary with the charactaristic of the fudging function
          'enough' : ndarray
                1d-array with the lastest relative variation of coefficients

""";
  _name_='fudgedlinearfit';

  ydata=numpy.array(ydata)
  if(ydata.ndim>1):
    if(ydata.shape[1]>1): raise SkZpipeError("`ydata` is not a 1-dimensional array", exclocus=_name_);
  ndata=ydata.size;
  ydata.resize((ndata,));
  erry=numpy.array(erry)
  if(ydata.size != erry.size): raise SkZpipeError("`ydata` and `erry` have differente size", exclocus=_name_);
  erry.resize((ndata,));
  xdata=numpy.array(xdata, ndmin=2)
  if(xdata.ndim!=2): raise SkZpipeError("`xdata` is not a 2-dimensional array", exclocus=_name_);
  if(xdata.shape[0]!=ndata): raise SkZpipeError("`ydata` and `xdata` has not the same amount of data <{} {}>".format(ydata.shape, xdata.shape), exclocus=_name_);
  nvar=xdata.shape[1];
#  xdata.resize((ndata,nvar));

  ##%%#
  def pbsfudge(x,sigma,a=(2,2),b=(4,4)):
    """To work with array, not numbers"""
    mask=x>=0;
    ret=numpy.ones(x.shape)
    ret[mask]=1/(1+abs(x[mask]/(a[0]*sigma))**b[0]);
    ret[~mask]=1/(1+abs(x[~mask]/(a[1]*sigma))**b[1]);
    return ret;
    
  ##%%#
 
  if(isinstance(fudge, dict)):
    if('pbs' in fudge):
      fudgeD=fudge['pbs'].copy();
      fudgeD['_type_']='pbs';

      fudgeD.setdefault('a',(2,2));
      fudgeD.setdefault('b',(4,4));
      if(not isinstance(fudgeD['a'], tuple)): fudgeD['a']=(fudgeD['a'],fudgeD['a']);
      if(not isinstance(fudgeD['b'], tuple)): fudgeD['b']=(fudgeD['b'],fudgeD['b']);
      fudge=lambda x,sigma: pbsfudge(x=x, sigma=sigma, a=fudgeD['a'], b=fudgeD['b']);
    else: raise SkZpipeError("Wrong entry for `fudge` dictionary", exclocus=_name_);
  elif(fudge is not None and not callable(fudge)): raise TypeError(_name_+": wrong type for `fudge`! It must be None, a dictionary or a callable with 2 parameters. <{}>".format(fudge.__class__));
  else: fudgeD={'fudge':fudge, '_type_':'user'}
      

  if(not isinstance(options,dict)): options={}
  options=options.copy();
  options.setdefault('niter',1000);
  options.setdefault('enough',1e-4);
  options.setdefault('en_flag','any');
  options.setdefault('wsigma',1e-6);
  options['en_flag']=options['en_flag'].lower() 
  if(options['en_flag'] not in ('any','all')): raise SkZpipeError("Wrong value for 'en_flag' in `options` ('any' or 'all') <{}>".format(options['en_flag']), exclocus=_name_)

  wsigma=math.sqrt(numpy.sum(erry**2)/(ndata-nvar));

  coeff=None;
  if(guess):
      guess=numpy.array(guess)
      guess.resize((nvar,));
      
      eps=ydata-xdata.dot(guess)
      wsigma=math.sqrt(eps.dot(eps)/(ndata-nvar));
      rms=wsigma;
  
      coeff=guess;
  else:
      eps=numpy.zeros(ndata);

  niter=0;
  while(niter<options['niter']):
    coeff0=coeff;
    matrix=numpy.zeros((nvar,nvar));
    
    weit2=fudge(eps, wsigma)/erry**2 if(callable(fudge)) else 1./erry**2 ;
    
    vector=numpy.array(ydata*weit2).dot(xdata)
    matrix=numpy.array(xdata.T*weit2).dot(xdata);

  ########
    invmatrix=numpy.linalg.inv(matrix);
    coeff=invmatrix.dot(vector)
    niter+=1;
  #########
    wsigma0=wsigma;    
    eps=ydata-xdata.dot(coeff)
    fudgev=fudge(eps, wsigma0) if(fudge is not None) else numpy.ones(ndata);

    rms   =math.sqrt( eps.dot(eps)       /(ndata-nvar)                          );
    me1   =math.sqrt( eps.dot(eps*weit2) /(ndata-nvar)                          );
    wsigma=math.sqrt( eps.dot(eps*fudgev)/(ndata-nvar) /fudgev.mean()  );
    
    if(wsigma<options['wsigma'] or fudge is None): break
    
    if(coeff0 is not None):
      maskD=(coeff!=0)
      mask0=numpy.logical_and(~maskD,(coeff0!=0))
      enough=numpy.zeros((nvar,))

      enough[maskD]=coeff0[maskD]/coeff[maskD]-1
      enough[mask0]=coeff[mask0]/coeff0[mask0]-1

      if(options['en_flag']=='any'):
        if(any(enough<options['enough'])): break;
      elif(options['en_flag']=='all'):
        if(all(enough<options['enough'])): break;

  corr=invmatrix.copy();
  for ii in range(nvar):
    corr[ii,:]/=math.sqrt(invmatrix[ii,ii])
    corr[:,ii]/=math.sqrt(invmatrix[ii,ii])

  return {'niter':niter, 'ndata':ndata, 'nvar':nvar, 'rms':rms, 'wsigma':wsigma, 'me1':me1, 'coeff':coeff, 'error':numpy.sqrt(invmatrix.diagonal())*me1, 'corr':corr, 'fudge':fudgeD, 'enough':enough}


######
#def movingaverage(array=None, n=1): # ==> scipy.scipy.ndimage.uniform_filter1d( input=array, size=n)
#  """Calculate the moving/convoluted average of a numpy array, using a subarray of shape (n,n) or n. The average at certain position is calculated centering the subarray on that position (the values on the border are calculated using less elements).

############
def movingpolyfit(x=None, y=None, deg=None, size=None, step=None, fixedlow=False, rcond=None, full=False, w=None, cov=False):
    """Operate numpy.polyfit on subparts of size `size` shifting of `step` at each iteration

Parameters
----------
    x : array_like, shape (M,)
        x-coordinates of the M sample points ``(x[i], y[i])``.
    y : array_like, shape (M,) or (M, K)
        y-coordinates of the sample points. Several data sets of sample points sharing the same 
        x-coordinates can be fitted at once by passing in a 2D-array that contains one dataset per column.
    deg : int
        Degree of the fitting polynomial
    size : int
        Length of the slices
    step : int
        Shift to operate at each iteration
    fixedlow : bool
        If only the upper limit of the bin is moving, while the lower end stay fixed (so the bin width increases).
    rcond, full, w, cov :
        See numpy.polyfit

Return
------
    Array of polyfit output. [x_mean, coefficients, residuals]
    Each row start with the mean x for the interval, then the coefficients as returned by polyfit, and ends with the size and the residuals.
"""
    _name_='movingpolyfit'
    try:
        x=numpy.array(x)
    except:
        raise TypeError(f"{_name_}: `x` must be a array_like object")
    output=[]
    for ii in range(0, len(x)-size, step):
        if(fixedlow):
            out=numpy.polyfit(x=x[:ii+size], y=y[:ii+size], deg=deg, rcond=rcond, full=full, w=w, cov=cov)
        else:
            out=numpy.polyfit(x=x[ii:ii+size], y=y[ii:ii+size], deg=deg, rcond=rcond, full=full, w=w, cov=cov)
        if(isinstance(out,tuple)):
            coef=out[0]
            resid=out[1][0]
        else: 
            coef=out
            resid=0
        coef=numpy.insert(coef, 0, x[ii:ii+size].mean())
        coef=numpy.append(coef, [resid/y[ii:ii+size].mean(), resid])
        output.append(coef)
    return numpy.array(output)



############
def bestpolyfit(x=None, y=None, deg=None, rcond=None,  w=None, cov=False):
    """Operate numpy.polyfit on subparts of size `size` shifting of `step` at each iteration

Parameters
----------
    x : array_like, shape (M,)
        x-coordinates of the M sample points ``(x[i], y[i])``.
    y : array_like, shape (M,) or (M, K)
        y-coordinates of the sample points. Several data sets of sample points sharing the same 
        x-coordinates can be fitted at once by passing in a 2D-array that contains one dataset per column.
    deg : int
        Maximum degree of the fitting polynomial to check
    rcond, w, cov :
        See numpy.polyfit
    full=True

Return
------
    Array of polyfit output. Each row start with the mean x for the interval, then the coefficients as returned by polyfit, and ends with the size and the residuals.
"""
    _name_='bestpolyfit'
    output,Dresid=[],[]
    for ii in range(deg+1):
        out=numpy.polyfit(x=x, y=y, deg=ii, rcond=rcond, full=True, w=w, cov=cov)
        out=list(out)
        Dresid.append(out[1][0])
        output.append(out)
    Dresid=[(Dresid[ii]-Dresid[ii+1]) for ii in range(len(Dresid)-1)]
    for ii in range(len(Dresid)-1):
        if(Dresid[ii]<Dresid[ii+1]): break
    ii+=1 #Flex point
    output.insert(0,ii)
    return output





############
def dointersect(point=None, slope=None, A=None, B=None):
    """If the line passing through `point` with slope `slope` intersects the segment A B.

Parameters
----------
    point : Coord
        2D point with x,y attributes
    slope : float
        Slope of the line
    A : Coord
        2D endpoint of the segment
    B : Coord
        2D endpoint of the segment

Return
------
    output : tuple of flag
        0:  If the line passes through an endpoint, it returns 0
            If the line passes through internal point of the segment, it returns -1
            If the line passes outside the segment, it returns +1
            None if the segment is parallel to the line
        1:  If the line passes through an endpoint, it returns -1 if it passes through A, +1 if through B
            Otherwise, it returns if the line passes below A (-1) or above A (+1)
"""
    _name_='dointersect'
    if(any(not hasattr(point, x) for x in ('x','y'))): raise TypeError(f"{_name_}: Wrong type for `point`")
    if(any(not hasattr(A, x) for x in ('x','y'))): raise TypeError(f"{_name_}: Wrong type for `A`")
    if(any(not hasattr(B, x) for x in ('x','y'))): raise TypeError(f"{_name_}: Wrong type for `B`")
    if(isinstance(slope, int)): slope=float(slope)
    if(not isinstance(slope,float)):  raise TypeError(f"{_name_}: Wrong type for `slope`")

    valA=slope*(A.x-point.x)-(A.y-point.y)
    valB=slope*(B.x-point.x)-(B.y-point.y)
    AB=sign(valA*valB)
    if(AB==0): 
        if(valA==0): 
            if(valB==0): return (None,1)
            return AB, -1
        return AB, +1
    else: 
        if(A.y-B.y == slope*(A.x-B.x)): return None, sign(valA)
        return AB, sign(valA)


############
def findintersect(point=None, slope=None, A=None, B=None):
    """Give the point of intersection between a line passing through `point` with slope `slope` and the segment A B.

Parameters
----------
    point : Coord
        2D point with x,y attributes
    slope : float
        Slope of the line
    A : Coord
        2D endpoint of the segment
    B : Coord
        2D endpoint of the segment

Return
------
    output : tuple 
        Tuple with 2D coordinates of the intersect point.
        If the segment is parallel to the line, return None
"""
    _name_='findintersect'
    if(any(not hasattr(point, x) for x in ('x','y'))): raise TypeError(f"{_name_}: Wrong type for `point`")
    if(any(not hasattr(A, x) for x in ('x','y'))): raise TypeError(f"{_name_}: Wrong type for `A`")
    if(any(not hasattr(B, x) for x in ('x','y'))): raise TypeError(f"{_name_}: Wrong type for `B`")
    if(isinstance(slope, int)): slope=float(slope)
    if(not isinstance(slope,float)):  raise TypeError(f"{_name_}: Wrong type for `slope`")

    q=point.y-slope*point.x
    DxAB=A.x-B.x; DyAB=A.y-B.y
    if(DyAB == slope*DxAB): return ()
    
    x=DxAB*A.y-DyAB*A.x-q*DxAB
    x/=slope*DxAB-DyAB
    y=slope*x+q

    return (x,y)





