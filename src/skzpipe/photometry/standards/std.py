import math
import numpy

from ...exceptions import *

from ...parameters  import basicpar as bpar
from ...parameters  import options as _opt
from ...parameters  import database as _db
from ...parameters.classes  import bclasses
from ...parameters.classes.fileclass  import basefile
from ...parameters.classes.fileclass import daofile 
from ..daophot import daofunctions as daofunct
from ... import functions as funct
from ... import match

#STAR
class StdStar(bclasses.IdXY):
  """Class for standard star


""";
  _dtype_names=('idx','ra', 'dec', 'x','y');
  _dtype_nfield=len(_dtype_names);
  _dtype_formats=(str, float, float, float, float);
  _dtype_nlines=1;
  _dtype_delimiter=None;
  _str_format="{idx:>12} {x:10f} {y:10f}";

  (idx,idn, ra,dec, x,y,  data)='-',0, 0.,0.,  0.,0.,   '';


  def __init__(self, line='', pos={'id':1, 'ra':2, 'dec':3, 'x':4, 'y':5, 'mag':[6,8]}, sep=None, coordtransf=None):
    if(isinstance(line, StdStar)):
      self.idx=line.idx;
      self.ra=line.ra;
      self.dec=line.dec;
      self.x=line.x;
      self.y=line.y;
      self.mag=line.mag.copy();
      self.err=line.err.copy();
    else:
      if(not isinstance(line, str)): raise TypeError("StdStar: wrong input type for line");
      if(not isinstance(pos, dict)): raise TypeError("StdStar: wrong input type for pos");
      tmpl=line.strip().split(sep);
      if(not tmpl): raise ValueError('StdStar: wrong input value');
      self.idx=tmpl[pos['id']-1];
      self.ra=float(tmpl[pos['ra']-1]);
      self.dec=float(tmpl[pos['dec']-1]);
      if(pos['x']>0 and pos['y']>0):
        self.x=float(tmpl[pos['x']-1]);
        self.y=float(tmpl[pos['y']-1]);
      elif(pos['x']==0 or pos['y']==0):
        self.x=None;
        self.y=None;
      else:
        dst=float(tmpl[ abs(pos['x'])-1 ]);
        ang=float(tmpl[ abs(pos['y'])-1 ]);
        self.x=dst*math.cos(math.pi*ang/180.);
        self.y=dst*math.sin(math.pi*ang/180.);
      self.mag,self.err=[],[];
      for ii in pos['mag']:
        self.mag.append(funct.getfloat(tmpl[ii-1], 99.999));
      if('err' in pos):
        for ii in pos['err']:
          self.err.append(funct.getfloat(tmpl[ii-1], 0.00));
      else:
        for ii in pos['mag']:
          self.err.append(funct.getfloat(tmpl[ii], 0.00));
      if(isinstance(coordtransf, bclasses.CoordTransf)): 
          coordtransf.applyto([self]);
  def __str__(self):
    txt="{:} {:f} {:f} {:f} {:f}".format(self.idx, self.ra, self.dec, self.x, self.y);
    for ii in range(len(self.mag)):
      txt+=" {:f} {:f}".format(self.mag[ii], self.err[ii]);
    return txt;
bpar.SkZp_Par['stdstar']=StdStar;


#FIELD
class StdField:
  def __init__(self, field=None, bands=None, skip='#', stdclass=StdStar, ref_pattern=''):
    self.bands=bands;
    self.ref=None;
    if('\\' in skip): skip=skip.replace('\\', '\\\\');
    if(isinstance(field, str)):
      self.field=field;
      with open(field) as fstd:
        self.stdL=[];
        for line in fstd:
          line=line.strip();
          if(ref_pattern and re.search(ref_pattern, line)): self.ref=line;
          if(len(line)<5 or re.search('^['+skip+']', line)): continue;
          self.stdL.append(stdclass(line));
    if(isinstance(field, StdField)):
      self.field=field.field;
      self.ref=field.ref;
      self.stdL=[];
      for std in field.stdL:
          self.stdL.append(stdclass(std));

  def xytransf(self, ref=None, coordtransf=None):
    """Change the (x,y) coordinates of all stars""";
    if(coordtransf!=None and not isinstance(coordtransf, bclasses.CoordTransf)): raise TypeError('StdField.xytransf: coordtransf must be a CoordTransf object or None');
    if(isinstance(ref, tuple)):
      dx=-3600*(self.ref[0]-ref[0])*math.cos(math.radians(self.ref[1]));
      dy=3600*(self.ref[1]-ref[1]);
    else: dx,dy=0,0;
    if(coordtransf==None):
      cootr=bclasses.CoordTransf(pan=(dx,dy));
    else:
      cootr=coordtransf.concatenate(ante=bclasses.CoordTransf(pan=(dx, dy)));
    cootr.applyto(self.stdL);
    self.ref=ref;
  
###    
  def daowrite(self, passband=None, header=None, fname=None):
    """Write a DAOPhot lst-type file for each of the given passbands with extension .std

Parameters
----------
    passband : 

    header : 

    fname : str
        Filename 

""";
    if(passband==None): passband=self.bands;
    if(not isinstance(passband,list)): passband=[passband];
    if(not header and os.path.exixts(fname+'.coo')): header=daofile.DAOHeader(imgname+".coo");
    if(not isinstance(fname,str)): fname=self.field;

    for band in passband:
      if(band not in self.bands): raise ValueError("StdField: wrong requested passband. {band} not in available {blist}".format(band=band, blist=self.bands));
    if(len(passband)==1):
      fname=fname+".std";
    else:
      fname=fname+"__{:}.std";
    for band in set(passband):
      with daofile.DAOPhotoFile(ftype='lst', fname=fname.format(band), header=header) as daof: 
        createit=True;
        if(_opt.OptionGet('speedup')>1):
          if(not daof.check_file(raisexc=False)): createit=False;
        if(createit):
          bpos=self.bands.index(band);
          ii=0;
          for std in self.stdL:
            ii+=1;
            if(-90<std.mag[bpos]<90 and -50<std.x<daof.fform.header.nx+50 and -50<std.y<daof.fform.header.ny+50):
              daof.sourcesappend((ii, std.x, std.y, std.mag[bpos], std.err[bpos]));
          print(daof.fname,':', self.field, band, len(daof.srcL), file=bpar.SkZp_Par['stdout']);
          if(daof.srcL): daof.writefile(overwrite=True);
        else:
          print(daof.fname,':', self.field, band, funct.get_num_lines(daof.fname), file=bpar.SkZp_Par['stdout']);

###
  def makestdlst(self, imgname=None, coordtransf=None, addpassband=None, fformat=None, header=None):
    """
Make a list of standard for a given image

Parameters
----------
    imgname : str
        Basename of the image
    coordtrasf : CoordTransf
        Coordinate transformation to be applied
    addpassband : list
        List of additional passbands of which to create a standard list
    fformat : str
        Format for the outputfile (only 'DAO' ifor DAOPHOT suite files is supported)
    header : PhotoFileHeader, None
        Header for the output files

Funtions
--------
   xytransf
   daowrite
""";
    _name_='StdField.makestdlst';
    if(imgname not in bpar.SkZp_Par['inputdata']): raise ValueError(_name_+": `imgname` {} not in the internal database ".format(imgname));
    img=bclasses.Image(imgname);
    if(not isinstance(coordtransf, bclasses.CoordTransf)):
        if(img.instr in _db.SkZp_DB['MOSdistortion']):
            coordtransf= bclasses.CoordTransf(coeff=_db.SkZp_DB['MOSdistortion'][img.instr]['TAN2XY'][img.chip])
        else: 
            coordtransf= bclasses.CoordTransf(shift=(img.nx,img.ny), zoom=(1./img.scale[0],1./img.scale[1]))

   #transform x,y of the catalog according to coordtransf
    self.xytransf(ref=(img.ra,img.dec), coordtransf=coordtransf);
    passband=[img.filter];
    if(isinstance(addpassband,list) and addpassband): passband+=addpassband;
    self.daowrite(passband, header, imgname);
    return passband;


bpar.SkZp_Par['stdfield']=StdField;
###################################
def GetStandard(tag=None, files=None, addpassband=None, fieldclass=None, match_ext=['.ap', '.als']):
  """
Get standard star list for given images and match the aperture photometry with it.

Parameters
----------
    tag : str
        tag from SkZp_Par['inputdata'] to separate  'files' into different standard fields.
    files : list, None
        list of files to create the list of standard and do the match. If None, all the files in 'entrylist' parameter will be used.
    addpassband : list(str)
        To add additional passbands to the one determined by the filter use for the image.
    fieldclass : StdField
        class for the standard field (StdField or derived). If None, the program use SkZp_Par['stdfield'], defined by the last imported standard module.
    match_ext : str, list of str
        (list of) suffix (with dot) for the photometric file that has to be matched with the standard field using daomatch/daomaster. The matching process can suffer for crowdness and the first photometric file could not have enough additional information to select a better matching set of sources (like '.ap' files), so an additional suffix can be necessary to get e good first guess. Default options 'photo:ext:aperture', 'photo:ext:fitting'.
""";
  _name_="GetStandard";
  if(fieldclass==None): fieldclass=bpar.SkZp_Par['stdfield'];
  if(not issubclass(fieldclass, StdField)): raise TypeError(_name_+": `fieldclass` must be a StdField class or a subclass. <{}>".format(fieldclass.__class__));
  if(match_ext is None): match_ext=[_opt.OptionGet('photo:ext:aperture'), _opt.OptionGet('photo:ext:fitting')];
  if(not isinstance(match_ext, list)): match_ext=[match_ext];
  if(len(match_ext)==0): raise ValueError(_name_+": `match_ext` must be an extension or a list of them: it's empty.");

  nfail, failL=0,[];
  #sin10=0.174 cos10=0.985
  a_val, b_val=(.98,1.02), (-0.2,0.2);
  coeff_ref=[None, None, a_val, b_val, b_val, a_val];

  (fieldnameL, fieldnameD)=funct.InputDataSplitByTag(tag=tag, entrylist=files);
  for fieldname in fieldnameL:
    print('Tag: '+fieldname, file=bpar.SkZp_Par['stdout']);
    ra0=numpy.mean(funct.InputDataTagValueList(tag='RA', entrylist=fieldnameD[fieldname]));
    dec0=numpy.mean(funct.InputDataTagValueList(tag='DEC', entrylist=fieldnameD[fieldname]));
    stdf0=fieldclass(field=fieldname, pointing=(ra0,dec0));  #creating the standard field catalog from name or pointing
    for img in fieldnameD[fieldname]:
      stdf=fieldclass(stdf0); #create a copy: makestdlst will transform the x,y position
      if(match_ext[0]):
        mfile=img+match_ext[0];
        if(daofunct.Dao_check_file(mfile, raisexc=False)):
          print('No matching: no matching file '+mfile, file=bpar.SkZp_Par['stdout']);
          continue;
       #create a standard photometry for each passband
        passband=stdf.makestdlst(img, addpassband=addpassband, fformat='DAO', header=daofile.DAOHeader(mfile)); 
        fail=False;
        mch=match.Match(img+'-std.mch');
        #mag0=daofunct.maxmag(mfile, 1)-2;
        files=[];
        if(len(passband)==1): files.append(img+".std");
        else:
          for band in passband:
            files.append("{:}__{:}.std".format(img,band));
        
        #if(not mch.makemch('dao:<p50:;', [mfile]+files)):
        if(not mch.makemch('dao', [mfile]+files)):
            ccheck=mch.checkcoeff(coeff_ref); #The trasformatio should be approximately only a shift: check for it
            if(ccheck): #The trasformatio should be approximately only a shift: check for it
                if(_opt.OptionGet('output:verbose') and _opt.OptionGet('output:verbosity')>0): print('!!! Matching coefficient for {mch} are not as supposed at file {mfile} #{pos}: {coeff}'.format(mch=mch.mch, mfile=mch.files[ccheck[0]-1], pos=ccheck[1]-1, coeff=mch.data[ccheck[0]-1]), file=bpar.SkZp_Par['stdout']);
                if(not mch.makemch('dao:<p50', [mfile]+files)):
                    ccheck=mch.checkcoeff(coeff_ref); #The trasformatio should be approximately only a shift: check for it
                    if(ccheck):  #The trasformatio should be approximately only a shift: check for it
                        if(_opt.OptionGet('output:verbose') and _opt.OptionGet('output:verbosity')>0):
                            print('!!! Matching coefficient for {mch} are not as supposed at file {mfile} #{pos}: {coeff}'.format(mch=mch.mch, mfile=mch.files[ccheck[0]-1], pos=ccheck[1]-1, coeff=mch.data[ccheck[0]-1]), file=bpar.SkZp_Par['stdout']);
                        fail=True; 
                else:
                  fail=True;
        else:
            if(not mch.makemch('dao:<p50', [mfile]+files)):
                if(ccheck):  #The trasformatio should be approximately only a shift: check for it
                    if(_opt.OptionGet('output:verbose') and _opt.OptionGet('output:verbosity')>0): print('!!! Matching coefficient for {mch} are not as supposed at file {mfile} #{pos}: {coeff}'.format(mch=mch.mch, mfile=mch.files[ccheck[0]-1], pos=ccheck[1]-1, coeff=mch.data[ccheck[0]-1]), file=bpar.SkZp_Par['stdout']);
                    fail=True; 
            else:
                fail=True;
        mch.stdout.flush();

        if(fail and len(match_ext)>1): 
          if(daofunct.Dao_check_file(img+match_ext[1], raisexc=False)==0):
            with match.Match(img+'-std0.mch') as mch0:
  #            mag0=daofunct.maxmag(img+'.als', 1)-2;
              if(mch0.makemch('dao:<p60%2[1:;', [img+match_ext[1]]+files)==0):
                ccheck=mch0.checkcoeff(coeff_ref);
                if(not ccheck):
                    fail=False;
                    mch.makemch('use:'+mch0.mch, [img+match_ext[0]]+files);
                    funct.clean_file(mch0.mch);
                else:
                    if(_opt.OptionGet('output:verbose') and _opt.OptionGet('output:verbosity')>0): print('!!! Matching coefficient for {mch} are not as supposed at file {mfile} #{pos}: {coeff}'.format(mch=mch0.mch, mfile=mch0.files[ccheck[0]-1], pos=ccheck[1]-1, coeff=mch0.data[ccheck[0]-1]), file=bpar.SkZp_Par['stdout']);
                
        if(fail): 
          print('FAILED!', file=bpar.SkZp_Par['stdout']);
          if(not _opt.OptionGet('debug')): funct.clean_file([mch.mch]);
          nfail+=1;
          failL.append(img);
          continue;

        mch.DAOmaster(1, 1, 6, 50, 'mch');
#        mch.DAOmaster(1,1,6,20, 'rawI');
        mch.DAOmaster(1, 1, 6, 10, 'rawI');
        mch.DAOrawstraight();
        with open(mch.base+'.raw1') as fin, open(mch.base+'.out', 'w') as fout:
          daofunct.copyheader(fin, fout, '#');
          for line in fin:
            star=daofile.DAOSource(line);
            star.mag+=2.5*math.log(bpar.SkZp_Par['inputdata'][img]['EXPTIME'], 10);
            fout.write(str(star)[:43]+line[43:].rstrip());
            fout.write("  {:6.4f}\n".format(bpar.SkZp_Par['inputdata'][img]['AIRMASS']));

  print("#fail: {:}".format(nfail), failL, file=bpar.SkZp_Par['stdout']);

