"""Module with photometric funtions
"""


import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy
import numpy 
    
from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters  import database as _db
from ..parameters  import options as _opt
from ..parameters  import daoparameters as daopar
from ..parameters.classes.fileclass import basefile
from ..parameters.classes.fileclass import daofile
from .. import functions as funct
from ..mathfunct import krdelta




def filecalib(filein=None, fileformat=None, param=None, fileout='daophot', amcorr=False, coeff0error=False):
  """Calibrate photometrically a input file.

Parameters
----------
    filein : str
        Name of the input file.
    fileformat : dict or PhotoFileFormat
        Describe the structure of the input file. As dictionary it must have the following key:value pairs.
        Default DAO.raw format.
          '' : 
    param : dict
        Dictionary that provides for each filter (used as key) a dictionary with air-extintion and
        calibration coefficients, and the pair of filters used for the color relation.
        For each filter, the available entries are:
          'am' : tuple of floats
               Atmospheric extintion coefficient and its error. Not mandatory. Default (0,0).
          'coeff' : list/tuple of tuples
               The coefficinets are provided as tuple/list of tuples of values in pairs: (value, error).
               The order of the coefficients follows the degree of the color expression (constant, linear, quadratic, ...).
          'color' : tuple of str
               The pair of filter name used for the color, in order. None or empty tuple if the calibration is just a zero point correction.
        Example: {'B':{ 'coeff':((5.20, 0.001), (-0.02, 0.001)), 'am':(0.25, 0.002), 'color':('B','V')},
                  'V':{ 'coeff':((5.20, 0.001), (+0.02, 0.001)), 'am':(0.15, 0.002), 'color':('B','V')}, }
    fileout : str
        Name of the input file. Default `filein`+'-cal'
    amcorr : bool
        Flag to perform the airmass correction. Defualt False
    coeff0error: bool
        Flag to use the error of the zero-point coefficient or not (because it does not increase the dispersion of the data)

Returns
-------
    
""";
  _name_='filecalib';

  if(not isinstance(filein, str)): raise TypeError(_name_+": `filein` must be a string");
  if(fileformat is not None  and not isinstance(fileformat, (dict, basefile.PhotoFileFormat))): raise TypeError(_name_+": `fileformat` must be a dictionary or PhotoFileFormat");
  if(not isinstance(param, dict)): raise TypeError(_name_+": `param` must be a dictionary");
  if(not fileout): filein+'-cal';
  if(not isinstance(fileout, str)): raise TypeError(_name_+": `fileout` must be a string");
  if(not isinstance(amcorr, bool)): raise TypeError(_name_+": `amcorr` must be a string");

  class DAOrawdata:
    def __init__(self, stream=None, filters=None):
      self.filters=filters.copy();
      self.nmag=len(filters);
      self._dtype_nlines=math.ceil(( +1)/6.);
      self.idx, self.x, self.y, self.mag, self.emag=(None,)*5;
      line='';
      for ii in range(self._dtype_nlines):
        line+=stream.readline().rstrip();
      if(not line):  return;
      tmpl=line.split();
      self.idx, self.x,self.y, self.chi2, self.sharp=tmpl[0], float(tmpl[1]), float(tmpl[2]), float(tmpl[-2]), float(tmpl[-1]);
      self.mag=dict(zip( filters, (float(x) for x in tmpl[3:(3+self.nmag*2):2]) ));
      self.emag=dict(zip( filters, (float(x) for x in tmpl[4:(3+self.nmag*2):2]) ));
    def __str__(self):
      return "{:>7s} {:8.3f} {:8.3f}".format(self.idx, self.x, self.y)+''.join(" {:8.4f} {:8.4f}".format(self.mag[ii], self.emag[ii]) for ii in self.filters)+" {:8.4f} {:8.4f}".format(self.chi2,self.sharp);
    def print(self):
      return str(self)+'\n';

  #FormatFile
  if(fileformat is None):
    fileformat={'header':daofile.DAOHeader, 'source':DAOrawdata, };
  else:
    if(not issubclass(fileformat['header'], basefile.FileHeader)): raise SkZpipeError("in `fileformat` 'header' must be a FileHeader subclass", exclocus=_name_)
    if(not issubclass(fileformat['source'], bclasses.IdXY)): raise SkZpipeError("in `fileformat` 'header' must be a FileHeader subclass", exclocus=_name_)

  ###########
  #CalibParam
  param=param.copy();
  filters=sorted(param.keys(), key=_db.SkZp_DB['passbands'][None].index);
  nfilters=len(filters);
  if(nfilters<2): raise SkZpipeError("`param` contain less than 2 filters: impossible to calibrate".format(filter=flt), exclocus=_name_);
  param['std']=None;
  colfltD={};
  for flt in filters:
      if(not param[flt].get('coeff')): raise SkZpipeError("in `param` filter {filter} has no 'coeff' defined: impossible to calibrate".format(filter=flt), exclocus=_name_);
      if('color' not in param[flt]):   raise SkZpipeError("in `param` filter {filter} has no 'color' defined: impossible to calibrate".format(filter=flt), exclocus=_name_);

      param[flt].setdefault('am', (0,0));
      if(not amcorr): param[flt]['am']=(0,0);

      if(nfilters==2): 
        if(param[flt]['coeff'] is None):
          if(param['std']): raise TypeError(_name_+": in `param` 'coeff' is None (standard photometry) for both two filters.");
          param['std']=flt;
      elif(not isinstance(param[flt]['coeff'], (list,tuple)) or not param[flt]['coeff']): raise TypeError(_name_+": in `param` 'coeff' of filter {filter} is not a tuple of 2-elements tuples. <{wrg}>".format(filter=flt, wrg=param[flt]['coeff']));
      for coef in param[flt]['coeff']:
          if(not isinstance(coef, tuple) or len(coef)!=2):
            raise TypeError(_name_+": in `param` 'coeff' of filter {filter} is not a tuple of 2-elements tuples. <{wrg}>".format(filter=flt, wrg=coef));

      colfltD.setdefault(param[flt]['color'], [])
      colfltD[ param[flt]['color'] ].append(flt);
      if(not param[flt]['color']): param[flt]['coeff']=param[flt]['coeff'][0:1];
      if(len(param[flt]['coeff'])>2):
        raise SkZpipeError("in `param` for filter {filter}  'coeff' has more than 2 coeff (polynomial calibration): not yet implemented!".format(filter=flt), exclocus=_name_);
      if(not coeff0error):
        param[flt]['coeff']=[(param[flt]['coeff'][0][0], 0)]+ list(param[flt]['coeff'])[1:];

  colorsL=sorted(colfltD.keys(), key=lambda x: len(colfltD[x]), reverse=True); #colors ordered by frequency
  top_col=tuple(colorsL[0]); #most frequent color
  top_freq=len(colfltD[top_col]); #frequency of the most frequent color
  if(nfilters==2 and tuple(filters) not in colfltD): raise SkZpipeError("the color by the only two filters is not used for calibration".format(filter=flt), exclocus=_name_);
  if(nfilters>2 and top_freq==1): raise SkZpipeError("each filter use a different color: calibration not implemented (error prtopagation really complicated)".format(filter=flt), exclocus=_name_);
  if(top_freq>=2 and all(x not in colfltD[top_col] for x in top_col) ): raise SkZpipeError("the most used color is not used for its two filters: calibration not implemented <{col}:{filters}>".format(col-top_col, filters=colfltD[top_col]), exclocus=_name_);

#If the color a-b is the same for the calibration of several filters
# M_x=C_x(A)*(m'_a-m'_b)+m'_x   C_x=-A_x/(1+A_a-A_b) 
#
# sig(M_x)^2 = col**2 * SUM_i[ (D{C_x}\D{A_i})**2 sig(A_i)^2] + SUM_i[ (d_xi + C_x*(d_ai-d_bi))**2 sig(m'_i)^2 ]
# d_ai Kronecker delta for a,i  ;  D{}/D{} partial derivative  ;  sig()^2 square error
# sig(M_x)^2 = col**2 * sig(C_x)^2 + SUM_i[ (d_xi + C_x*(d_ai-d_bi))**2 sig(m'_i)^2 ]  with i=x,a,b
# sig(C_x)^2 = SUM_i[ (( d_xi*(1+A_a-A_b) - A_x*(d_ai-d_bi) )/(1+A_a-A_b)**2)**2 sig(A_i)^2 ]  with i=x,a,b
# 
# coeffD, s2coeffD = C_x , sig(C_x)^2

  coeffD, s2coeffD=dict((x,0) for x in filters), dict((x,0) for x in filters);
  detA=0; calib_type='';
 ###
  if(nfilters==2 and param['std']):
      calib_type='1+std';
      ii=1-filters.index(param['std']);
      flt=filters[ii];
      coeffD[flt]=1-1./(1-param[flt]['coeff'][1][0]); #!

 ### Only one color for all
  elif(len(colorsL)==1 and top_freq==nfilters):
    calib_type='4all';
    detA=1+param[top_col[0]]['coeff'][1][0]-param[top_col[1]]['coeff'][1][0]; #!
    for flt in filters:
      coeffD[flt]=-param[flt]['coeff'][1][0]/detA;
      s2coeffD[flt]=sum( ( ( krdelta((flt, iflt))*detA-param[flt]['coeff'][1][0]*(krdelta((top_col[0], iflt))-krdelta((top_col[1], iflt))) )/detA**2 * param[iflt]['coeff'][1][1])**2
                         for iflt in set(top_col)|set((flt,)));
 ### One color for some and a mixed for others
  elif(top_freq>=2 and len(colflt[colorsL[1]])==1 and all(colfltD[col][0] in col and set(top_col)&set(col)  for col in colorsL[1:]) ):
    calib_type='1mixed';
    detA=1+param[top_col[0]]['coeff'][1][0]-param[top_col[1]]['coeff'][1][0]; #!
    for flt in colfltD[top_col]:
      coeffD[flt]=-param[flt]['coeff'][1][0]/detA;
      s2coeffD[flt]=sum( ( ( krdelta((flt, iflt))*detA-param[flt]['coeff'][1][0]*(krdelta((top_col[0], iflt))-krdelta((top_col[1], iflt))) )/detA**2 * param[iflt]['coeff'][1][1])**2
                         for iflt in set(top_col)|set((flt,)));
    for flt in set(filters)-set(colfltD[top_col]):
      col_flt=param[flt]['color'];
      detF=1+param[flt]['coeff'][1][0] if(flt == col_flt[0]) else 1-param[flt]['coeff'][1][0]; 
      coeffD[flt]=-param[flt]['coeff'][1][0]/detF;
      s2coeffD[flt]=(param[iflt]['coeff'][1][1]/detF**2)**2
      
    
  else: raise SkZpipeError("this type of calibration is not implemented ({})".format(colfltD), exclocus=_name_);
                 

 ############################
 # Opening FILE
 ############################
  header=fileformat['header'](filein);
  funct.check_file(files=filein, minline=header.length+1, namemaxlen=256, raisexc=True);
  with open(filein) as fin, open(fileout, 'w') as fout:
   #READ and COPY HEADER
    for ii in range(header.length):
      fout.write(fin.readline());
  
   #READ sources
    while(True):
      source=fileformat['source'](stream=fin, filters=filters);
      if(source.mag is None): break;
  
      mag =dict((x, y -param[x]['coeff'][0][0])    for x,y in source.mag.items());
      s2mag=dict((x,y*y+param[x]['coeff'][0][1]**2) for x,y in source.emag.items());
      Mag, s2Mag={},{};
     ####################################
  
      color=mag[top_col[0]]-mag[top_col[1]];
      if(calib_type=='1+std'):
          ii=1-filters.index(param['std']);
          flt=filters[ii];
      elif(calib_type=='4all'):
        for flt in filters:
          Mag[flt]=mag[flt]+coeffD[flt]*color;
          s2Mag[flt]= s2coeffD[flt]*color**2 + sum(  ( krdelta((flt, iflt)) + param[flt]['coeff'][1][0]*(krdelta((top_col[0], iflt))-krdelta((top_col[1], iflt))) )**2 * s2mag[flt]
                                                     for iflt in set(top_col)|set((flt,)));
      elif(calib_type=='1mixed'):
        for flt in colfltD[top_col]:
          Mag[flt]=mag[flt]+coeffD[flt]*color;
          s2Mag[flt]= s2coeffD[flt]*color**2 + sum(  ( krdelta((flt, iflt)) + param[flt]['coeff'][1][0]*(krdelta((top_col[0], iflt))-krdelta((top_col[1], iflt))) )**2 * s2mag[flt]
                                                     for iflt in set(top_col)|set((flt,)));
        for flt in set(filters)-set(colfltD[top_col]):
          col_flt=param[flt]['color'];
          if(flt==col_flt[0]):
            color=mag[flt]-Mag[col_flt[1]]
            Mag[flt]=mag[flt]+coeffD[flt]*color;
            s2Mag[flt]= s2coeffD[flt]*color**2 + coeffD[flt]**2*s2Mag[col_flt[1]] + (1+coeffD[flt])**2*s2mag[flt];
          else:
            color=Mag[col_flt[0]]-mag[flt];
            Mag[flt]=mag[flt]+coeffD[flt]*color;
            s2Mag[flt]= s2coeffD[flt]*color**2 + coeffD[flt]**2*s2Mag[col_flt[1]] + (1-coeffD[flt])**2*s2mag[flt];
            

              

  
     #####
      source.mag.update(Mag);
      source.emag.update(dict((x,math.sqrt(y)) for x,y in s2Mag.items()));
      
      fout.write(source.print());
  
