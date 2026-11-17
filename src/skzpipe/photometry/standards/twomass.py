
import os, sys, shutil, re
#import numpy

from ...exceptions import *
from ... import parameters as par
from ... import functions as funct
from .std import *


bands=['J', 'H', 'Ks'];
class TwoMStdStar(StdStar):
  def __init__(self, line=None):
    pos={'id':6, 'ra':1, 'dec':2, 'x':-26, 'y':-27, 'mag':[7,11,15], 'err':[9,13,17]};
    super().__init__(line=line, pos=pos);
    if(isinstance(line, TwoMStdStar)):
      pass;
    else:
      pass;

class TwoMStdField(StdField):
  def __init__(self, field=None):
    self.bands=bands;
    super().__init__(line=line, pos=pos, skip='\|', stdclass=TwoMStdStar);
    if(isinstance(field, str)):
      with open(field) as fin:
        line=fpos.readline();
        self.ref=tuple(float(x) for x in line.split()[0:2])
        line=fpho.readline();
        self.stdL=[];
        for line in fpos:
          self.stdL.append(PbsStdStar(line+fpho.readline()));
    elif(isinstance(field, TwoMStdField)):
      self.field=field.field;
      self.ref=field.ref;
      self.stdL=[];
      for std in field.stdL:
          self.stdL.append(TwoMStdStar(std));
    
par.SkZp_Par['stdfield']=TwoMStdField;
