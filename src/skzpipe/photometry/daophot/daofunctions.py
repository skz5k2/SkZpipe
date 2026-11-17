import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy
import numpy 
    
from ...exceptions import *
from ...parameters  import basicpar as bpar
from ...parameters  import daoparameters as daopar
from ...parameters.classes.fileclass import daofile
from ... import functions as funct
#from ... import mathfunctions as mathfunct

from ._daoCfunctions import *


def DAOoptFileInitialize():
  with open("daophot.opt", 'w') as f_opt:
    f_opt.write("GA=1\nRE=1\n");
  funct.clean_file(['photo.opt', 'allstar.opt']);

def DAOoptCheck(opt=None, env='daophot', autofix=True, raisexc=False):
  """Check the option for DAOPhot if the value is inside the permitted intervals.

Parameters
----------
    opt : str
        DAOPhot option in the format "key=value": the key is a 2-char string (every other chars are ignored), and the value is a float.
    env : str
        DAOPhot option environment ('daophot', 'photo', ...)
    autofix : bool
        Flag to enable the autofix to the nearest permitted value.
    raisexc: bool
        Flag to chose between raise an exception or return empy tuple. If autofix is True, this is ignored.

Returns
-------
    3-element tuple: (option, key, value)
""";
  _name_='DAOoptCheck';
  if(not isinstance(opt, str)): raise TypeError(_name_+": `opt` must be a string");
  if(not isinstance(env, str)): raise TypeError(_name_+": `env` must be a string");
  if(env not in daopar.DAO_Par['permittedoptionvalue']): raise ValueError(_name_+": Wrong value for option environment ({:})".format(", ".join(a)));
  opt=opt.strip().upper();
  if(opt in ['OP', 'OPT', '']): return (opt, opt, None);
  if('=' not in opt or len(opt)<4): raise ValueError(_name_+": wrong value for opt {:}".format(opt));
  tmpl=opt.split('=');
  if(len(tmpl)>2):
    raise SkZpipeWarning("Option {:} for {:} with '=' inside ".format(opt, env), exclocus=_name_);
  key=tmpl[0].strip()[0:2];
  val=float(tmpl[1]);

  if(key in daopar.DAO_Par['permittedoptionvalue'][env]):
    if(val < daopar.DAO_Par['permittedoptionvalue'][env][key][0]):
      if(autofix):
        opt , val = "{:}={:}".format(key, str(daopar.DAO_Par['permittedoptionvalue'][env][key][0])) , daopar.DAO_Par['permittedoptionvalue'][env][key][0];
      elif(raisexc): raise ValueError("!!!ERROR in DAOPhot: opt {:} has a value lower than permitted ({:} < {:})".format(key, opt, str(daopar.DAO_Par['permittedoptionvalue'][env][key][0])));
      else: return (None, None, None);
    if(val > daopar.DAO_Par['permittedoptionvalue'][env][key][1]):
      if(autofix):
        opt , val = "{:}={:}".format(key, str(daopar.DAO_Par['permittedoptionvalue'][env][key][1])) , daopar.DAO_Par['permittedoptionvalue'][env][key][1];
      elif(raisexc): raise ValueError("!!!ERROR in DAOPhot: opt {:} has a value higher than permitted ({:} > {:})".format(key, opt, str(daopar.DAO_Par['permittedoptionvalue'][env][key][1])));
      else: return (None, None, None);
 # elif(raisexc): raise ValueError("!!!ERROR in DAOPhot: opt {:} for {:} does not exist!".format(opt, env));
 # else: return (None, None, None);
  
  return ("{:}={:}".format(key,str(val)), key, val);


def DAOoptStore(optD=None, opt='', env=None, autofix=True, raisexc=False):
  """Store DAOphot option 'opt' in the dictionary 'optD'; 'opt' must be in the usual format 'OPT=VAL'

Parameters
----------
    optD : dict
        Dictionary where to store the option
    opt : str
        String with the option
    autofix : bool
        Flag to enable the autofix to the nearest permitted value.
    raisexc: bool
        Flag to chose between raise an exception or return empy tuple. If autofix is True, this is ignored.

Return
------
    'opt' return by the check as a test.

"""
  _name_='DAOoptStore';
  if(not isinstance(optD, dict)): raise TypeError(_name_+": optD must be a dictionary")
  opt, key, val=DAOoptCheck(opt=opt, env=env, autofix=autofix, raisexc=raisexc);
  if(opt): optD[key]=opt;
  return opt;


def Dao_check_file(files=[], minline=None, namemaxlen=None, raisexc=True):   #RAISE IOError SkZpipeErr
  """Check a DAOphot file if it exists, has enough lines and its filename is not too long (it uses check_file from functions submodule with right parameters).

Parameters
----------
    files : list
        List of filenames to check.
    minline : int
        Minimum number of lines (deafault DAO_Par['headerlen']+1).
    namemaxlen : int
        Maximum length of filenames (default DAO_Par['namemaxlen']).
    raisexc : bool
        Flag to set if raise an exception or just return an error value.

Return
------
    0 if all files pass the checks. if raisexc, an exception; otherwise, 1 if a filename is longer than the maximum namelength, 2 if a file has less lines than the minimum. -1 is return if None is passed as filename.
""";

  if(minline is None): minline=daopar.DAO_Par['headerlen']+1;
  if(namemaxlen is None): namemaxlen=daopar.DAO_Par['namemaxlen'];
  return funct.check_file(files=files, minline=minline, namemaxlen=namemaxlen, raisexc=raisexc);   #RAISE IOError SkZpipeErr


def Dao_exist_file(files=[], minline=None, namemaxlen=None, raisexc=True):   #RAISE IOError SkZpipeErr
  """Check a DAOphot file if it exists, has enough lines and its filename is not too long

Parameters
----------
    files : list
        List of filenames to check.
    minline : int
        Minimum number of lines (deafault DAO_Par['headerlen']+1).
    namemaxlen : int
        Maximum length of filenames (default DAO_Par['namemaxlen']).
    raisexc : bool
        Flag to set if raise an exception or just return an error value.

""";
  if(minline is None): minline=daopar.DAO_Par['headerlen'];
  if(namemaxlen is None): namemaxlen=daopar.DAO_Par['namemaxlen'];
  return funct.check_file(files=files, minline=minline, namemaxlen=namemaxlen, raisexc=raisexc);   #RAISE IOError SkZpipeErr


def copyheader(fin=None, fout=None, initstr=''):
  """Read and copy the header from file-object/tuple fin to fout(s)

Parameters
----------
""";
  _name_='copyheader';
  if(not isinstance(fout,list)): fout=[fout]
  if(isinstance(fin,tuple)):
    if(len(fin)==len(daopar.DAO_Par['HeaderFormat']['in'])):
      hdr=daopar.DAOHeader(fin);
      for ff in fout:
        if(ff!=None): ff.write(hdr.print());
      return fin;
    else: raise ValueError(_name_+': wrong size of input tuple');
  else:
    for ii in range(daopar.DAO_Par['headerlen']):
      line=fin.readline();
      if(ii==1): hdr=funct.splitconvert(data=line, delimiter=daopar.DAO_Par['HeaderFormat']['split'], converters=daopar.DAO_Par['HeaderFormat']['in']);
      for ff in fout:
        if(ff!=None): ff.write(initstr+line);
  return hdr;



def maxmag(fname=None, maxerr=None):
  """Return the maximum magnitude in the given file with the associated error lesser than the given value.

Parameters
----------
"""
  _name_='maxmag';
  Dao_check_file(fname);
  if(maxerr!=None and not isinstance(maxerr, (float, int))): raise TypeError(_name_+": maxerr must be None or a numeric value.");
  maxmag=-99.999;
  with open(fname) as fin:
    hdr=copyheader(fin);
    if(maxerr!=None):
      for line in fin:
        if(hdr[0]==2): line=fin.readline()+fin.readline();
        tmpl=line.split();
        n=(len(tmpl)>>1) if(hdr[0]==2) else 1 ;
        mag, err=float(tmpl[3]), float(tmpl[3+n]);
        if(err>maxerr): continue;
        if(mag<90 and maxmag<mag): maxmag=mag;
    else:
      for line in fin:
        if(hdr[0]==2): line=fin.readline();
        tmpl=line.split();
        mag=float(tmpl[3]);
        if(mag<90 and maxmag<mag): maxmag=mag;
        if(hdr[0]==2): fin.readline();
  return maxmag;
  


def apmaxmag(apfile=None, maxerr=None):
  """Return the maximum magnitude in the given .ap file with the associated error lesser than the given value.

Parameters
----------
"""
  _name_='apmaxmag';
  return maxmag(apfile, maxerr);
  

def coordtransf(fname=None, direct=True, coeff=None, output=None):
  """Transform the coordinate in a DAOphot file
direct determines if to use direct or inverse transformation
coeff=(x0, y0, a, b, c, d) are the coefficient of the transformation matrix in .mch file\nif not given, c=-b and d=a
[x]=[x0]+ [a c] [X]\n[y]=[y0]+ [b d] [Y]

Parameters
----------
""";
  _name_='coordtransf';
  if(not isinstance(fname,str)): raise TypeError(_name_+": fname must be a string.");
  Dao_check_file(fname);
  if(not isinstance(direct,bool)): raise TypeError(_name_+": direct must be a boolean.");
  if(not isinstance(coeff,tuple) or len(coeff) not in [2,4,6]): raise TypeError(_name_+": coeff must be a tuple of 2, 4 or 6 values.");
  if(output==None): output=fname+'_T';
  if(not isinstance(output,str)): raise TypeError(_name_+": output must be a string or None.");
  ll=len(coeff);
  coeff=tuple(float(x) for x in coeff);
  if(ll==2): (x0, y0, a,b,c,d)=(coeff[0], coeff[1],  1, 0, 0, 1);
  elif(ll==4): (x0, y0, a,b,c,d)=(coeff[0], coeff[1],  coeff[2], coeff[3], -coeff[3], coeff[2]);
  if(not direct):
    invd=1./(a*d-b*c);
    at,bt,ct,dt = d*invd, -b*invd, -c*invd, a*invd;
    x0t, y0t = -x0*at-y0*ct, -x0*bt-y0*dt;
    (x0, y0, a,b,c,d)=(x0t, y0t, at,bt,ct,dt);
  with open(fname) as fin, open(output, 'w') as fout:
    copyheader(fin, fout);
    for line in fin:
      tmpl=line.split(None,3)[:3];
      lenfld=line.find(tmpl[2])+len(tmpl[2]);
#      lenfld=25; while(line[lenfld]!=' '): lenfld+=1;
      idn=int(tmpl[0]); x=float(tmpl[1]); y=float(tmpl[2]);
      xx,yy = x0+a*x+c*y, y0+b*x+d*y;
      fout.write("{:7d} {:8.3f} {:8.3f}".format(idn, xx, yy)+line[25:]);  #format_row
  
#############################
def applyOffset(infile=None, offset=(0,0), outfile=None, id0=0):
  """Apply the offset and renumerate the stars

Parameters
----------
""";
  _name_='applyOffset';
  Dao_check_file(infile);
  if(not isinstance(offset,tuple) or len(offset)!=2): raise TypeError(_name_+": offset must be a tuple of 2 values.");
    
  funct.idmod(infile, id0, 3);
  coordtransf(infile+'_M', coeff=offset);
  funct.clean_file(infile+'_M');
  if(isinstance(outfile,str)): shutil.move(infile+"_M_T", outfile);


def appendfiles(master=None, files=None, output=None, id0=0, nl=1, step=1000):
  """Append to master file the files in the list. Return a tuple with: the greatest id of the master file, the id0s used for the other files, the last id.

Parameters
----------
  master= name of the file to which the others are appended.
  files= name of the file or list of names of files that have to be appended.
  output= filename of the resulting file.
  id0= list/tuple of the zero-point for the new id number (the first id of file[i] will start with id0[i]+1). 0 for automatic calculation. <0 for no renumbering.
       if the given id0[i] is less than the last greater id, it is automatically calculated.
  nl=  NL of the files
  step=  minimum separation in the id between two consecutive file in the automatic renumbering.
""";
  _name_='appendfiles';
  Dao_check_file(master);
  if(not isinstance(nl,int) or nl<1 or nl>3): raise TypeError(_name_+": nl must be an integer (1,3 or 2).");
  if(not isinstance(id0,tuple) and not isinstance(id0,int) and not isinstance(id0,list)): raise TypeError(_name_+": id0 must be an integer or a tuple/list of integers.");
  if(not isinstance(step,int)): raise TypeError(_name_+": step must be an integer.");
  if(not isinstance(files, list) and not isinstance(files,str)): raise TypeError(_name_+": files must be a string or a list of filenames.");
  if(not isinstance(output,str)): raise TypeError(_name_+": output must be a string.");
  if(nl not in (1,2)): raise ValueError(_name_+": nl must be 1 or 2");
  
  if(isinstance(id0,tuple)): id0=list(id0);
  elif(isinstance(id0,int)): id0=[id0];
  if(isinstance(files, str)): files=[files];
  Dao_check_file(files);
  if(len(id0)<len(files)): id0+=([0]*(len(files)-len(id0)) if(id0[0]>=0) else [-1]*(len(files)-len(id0)));
  id0.insert(0,0);

  idtxt,idlen=daopar.DAO_Par['IdTxt'], daopar.DAO_Par['IdLen'];
  with open(output, 'w') as fout:
    lastid=0;
    #Master
    with open(master) as fin:
      nl0=copyheader(fin, fout)[0];
      if(nl!=2):
        for line in fin:
          fout.write(line);
          id0[0]=int(line.split(None,1)[0]);
          if(lastid<id0[0]): lastid=id0[0];
      else:
        for line in fin:
          fout.write(line);
          line=fin.readline();
          fout.write(line);
          id0[0]=int(line.split(None,1)[0]);
          if(lastid<id0[0]): lastid=id0[0];
          fout.write(fin.readline());
    id0[0]=lastid;
    #OTHERS
    for fi in range(len(files)):
      with open(files[fi]) as fin:
        nl0=copyheader(fin)[0];
        if(0<=id0[fi+1]<lastid): id0[fi+1]=lastid-(lastid%step)+2*step;
        lastid=id0[fi+1];
        if(nl!=2):
          for line in fin:
            lastid+=1;
            nline=line if(id0[fi+1]<0) else idtxt.format(lastid)+line[idlen:];
            fout.write(nline);
        else:
          for line in fin:
            lastid+=1;
            fout.write(line);
            line=fin.readline();
            nline=line if(id0[fi+1]<0) else idtxt.format(lastid)+line[idlen:];
            fout.write(nline);
            fout.write(fin.readline());
  return tuple(id0+[lastid]);
      
######################################################### 
def compareCooAp(coofile=None, apfile=None, output=None):
  """
Compare the id of a .coo file with the ones in a .ap file and return the source not present in the second.

Parameters
----------
    coofile : str
        Name of the file with the source list
    apfile : str
        Name of the .ap file
    output : str
        Name of the output file thar will contain the sources in 'coofile' not present in 'apfile'

Return
------
    the number of missing sources.
""";
  _name_='compareCooAp';
  Dao_check_file([coofile]);
  if(not isinstance(output,str)): raise TypeError(_name_+": output must be a string.");
  
  nap=int((funct.get_num_lines(apfile)-daopar.DAO_Par['headerlen'])/3);
  if(nap<1):
    shutil.copy(coofile, output);
    return (funct.get_num_lines(coofile)-daopar.DAO_Par['headerlen']);
  idL=[];
  no=0;
  with open(coofile) as fcoo, open(output, 'w') as fout:
    with open(apfile) as fap:
      nl0=copyheader(fap)[0];
      tmpl=[];
      for line in fap:
        line=fap.readline();
        tmpl.append(int(line.split(None,1)[0]));
        fap.readline();
    maxid=max(tmpl);
    idL=[0]*(maxid+1);
    for ii in tmpl:
      idL[ii]=ii;
    nl0=copyheader(fcoo, fout)[0];
    for line in fcoo:
      idn=int(line.split(None,1)[0]);
      if(idn>maxid or idL[idn]==0):
        fout.write(line);
        no+=1;

  return no;
        
##############################################################
def fileupdate(first=None, second=None, output=None, nl=None):
  """
Update first file with the second. Match by ID.

Parameters
----------
    first : str
        Name of first file
    second : str
        Name of second file
    output : str
        Name of output file
    nl : int
        nl of the first file [optional, the funtion read automatically the header]
""";
  _name_='fileupdate';
  Dao_exist_file([first, second]);
  if(not isinstance(output,str)): raise TypeError(_name_+": output must be a string.");
  
  starD,idL={},[]
  nl1=0
  with open(output, 'w') as fout:
    #FIRST
    with open(first) as fin:
      nl1=copyheader(fin, fout)[0];
      if(nl==None): nl=nl1;
      if(nl==2):
        for line in fin:
          line=fin.readline();
          idn=int(line.split(None,1)[0]);
          idL.append(idn);
          starD[idn]=["\n",line];
          starD[idn].append(fin.readline());
      else:
        for line in fin:
          idn=int(line.split(None,1)[0]);
          idL.append(idn);
          starD[idn]=[line];
    #SECOND
    with open(second) as fin:
      nl1=copyheader(fin)[0];
      if(not idL):
        for line in fin:
          fout.write(line);
        return;
      if(nl==2):
        for line in fin:
          line=fin.readline();
          idn=int(line.split(None,1)[0]);
          if(idn not in idL): idL.append(idn);
          starD[idn]=["\n",line];
          starD[idn].append(fin.readline());
      else:
        for line in fin:
          idn=int(line.split(None,1)[0]);
          idL.append(idn);
          starD[idn]=[line];
    #WRITE
    for idn in idL:
      for line in starD[idn]:
        fout.write(line);


def areaclean(fname=None, areas=None, output=None, mindist=0, fixlist=None):
  """
Clean a file excluding sources in certain rectangular areas.

Parameters
----------
  areas:   can be the filename with the list or a list of tuples.
            tuple format: (X1, X2, Y1, Y2)
            file format: X1 X2 Y1 Y2

  mindist: is to extend the excluding area with an additional border

  fixlist: additional list of areas"""
  _name_='areaclean';
  Dao_check_file(fname);
  if(not isinstance(output,str)): raise TypeError(_name_+": output must be a string.");
  if((not isinstance(mindist,float) and  not isinstance(mindist,int)) or mindist<0): raise TypeError(_name_+": mindist must be a positive number.");
  if(not isinstance(areas,str) and not isinstance(areas,list)): raise TypeError(_name_+": areas must be a filename or a list of tuples.");
  if(fixlist!=None and not isinstance(fixlist,list)): raise TypeError(_name_+": fixlist must be a list of tuples.");
  areaL=[];
  if(isinstance(areas,str)):
    funct.check_file(areas);
    with open(areas) as fin:
      for line in fin:
        areaL.append(tuple(float(x) for x in line.split()));
  else:
    areaL=areas.copy()
  if(fixlist): areaL+=fixlist;

  with open(fname) as fin, open(output,'w') as fout:
    nl=copyheader(fin,fout)[0];
    if(nl==2):
      for line in fin:
        keep=True;
        line=fin.readline();
        x,y=tuple(float(x) for x in line.split(None,3)[1:3]);
        line+=fin.readline();
        for xi,xf,yi,yf in areaL:
          if(xi-mindist<=x<=xf+mindist and yi-mindist<=y<=yf+mindist):
            keep=False;
            break;
        if(keep): fout.write("\n"+line);
    else:
      for line in fin:
        keep=True;
        x,y=tuple(float(x) for x in line.split(None,3)[1:3]);
        for xi,xf,yi,yf in areaL:
          if(xi-mindist<=x<=xf+mindist and yi-mindist<=y<=yf+mindist):
            keep=False;
            break;
        if(keep): fout.write(line);
  

def listselect(fname=None, starlist=None, radius=None, selected=None, remaining=None, keepid=True):
  """Select and remove from a DAO file stars.

Parameters
----------
The input file is a classical 1-line file (i.e. .als) with 3-line header.
The file with selected stars can have no header.
All output files have the header of the input file.
If radius is non-positive or None, stars are selected with id.
keepid determines if the id in 'selected' output file is the same of the input file (or istead the same of 'starlist').""";
  _name_='listselect';
  Dao_check_file([fname, starlist]);
#  if(selected==None and remaining==None): raise SkZpipeError(_name_+': No output given.');
  if(radius==None): radius=0;
  if((not isinstance(radius,float) and  not isinstance(radius,int))): raise TypeError(_name_+": radius must be a number or None.");
  if(selected!=None and not isinstance(selected,str)): raise TypeError(_name_+": selected must be a string.");
  if(remaining!=None and not isinstance(remaining,str)): raise TypeError(_name_+": remaining must be a string.");
  if(not isinstance(keepid,bool)): raise TypeError(_name_+": keepid must be a boolean.");
  radius=radius*radius if(radius>0) else 0;
  
  class Cand(daopar.DAOSourceData):
    pos=0;
    dst=0;
 
  with open(starlist) as flst: 
    line=flst.readline();
    if('NL' in line):
      for ii in range(daopar.DAO_Par['headerlen']):
        line=flst.readline();
    if(line.strip()): starL=[daofile.DAOIdXY(line)];
    for line in flst:
      if(line.strip()): starL.append( daofile.DAOIdXY(line) );
  fsel=open(selected, 'w') if(selected!=None) else None;  
  frem=open(remaining, 'w') if(remaining!=None) else None;
  instarL=[];
  with open(fname) as fin:
    nl=copyheader(fin, [fsel, frem])[0];
    if(nl!=2):
      for line in fin:
        instarL.append(daopar.DAOSourceData(line));
  ns=0;
  idtxt,idlen=daopar.DAO_Par['IdTxt'], daopar.DAO_Par['IdLen'];
  if(radius==0):
    for star in starL:
      ii=0;
      for instar in instarL:
        if(instar.idx==star.idx):
          ns+=1;
          if(fsel!=None):
            if(keepid):
              fsel.write(instar.data);
            else:
              fsel.write(idtxt.format(star.idx)+instar.data[idlen:]);
          instarL[ii].idx='';
          break;
        ii+=1;
  else:
    for star in starL:
      ii=0; cndL=[];
      for instar in instarL:
        dst=(instar.x-star.x)**2+(instar.y-star.y)**2;
        if(dst<=radius):
          cndL.append(Cand(instar));
          cndL[-1].dst=dst;
          cndL[-1].pos=ii;
          break;
        ii+=1;
      if(cndL):
        if(len(cndL)>1):
          for cnd in cndL[1:]:
            if(cndL[0].dst>cnd.dst): cndL[0]=cnd;
        ns+=1;
        if(fsel!=None):
          if(keepid):
            fsel.write(cndL[0].data);
          else:
            fsel.write(idtxt.format(star.idx)+cndL[0].data[idlen:]);
        instarL[cndL[0].pos].idx='';

  if(frem!=None):
    for instar in instarL:
      if(instar.idn): frem.write(instar.data);

  if(fsel!=None): fsel.close();  
  if(frem!=None): frem.close();
  return ns;


def coordupdate(fname=None, newcoord=None, output=None, rej_nonew=False, maxshift=0):
  """Update the coordonates with a new set. Match is done by ID.

Parameters
----------
    fname : str
        Name of the DAOfile to update
    newcoord :  str
        Name of the DAOfile with the new coordinates
    output : str, None
        Name of the output file. Default is 'fname'+"upd".
    rej_nonew : bool`
        True to reject entries with no new coordinates (e.g. Allstar didn't converge for them)
    maxshift : float, None
        Maximum distance between old and new coordinates and reject which exceeds it. Default is 0.

Return
------
        Tuple of 4 elements: number of input sources, number of new coordinates, number of updated sources, number or rejected sources.
""";
  _name_='coordupdate';
  Dao_check_file([fname, newcoord]);
  if(output==None): output=fname+'upd';
  if(maxshift==None): maxshift=0;
  if((not isinstance(maxshift,float) and  not isinstance(maxshift,int))): raise TypeError(_name_+": maxshift must be a number or None.");
  if(not isinstance(output,str)): raise TypeError(_name_+": output must be a string.");
  if(not isinstance(rej_nonew,bool)): raise TypeError(_name_+": rej_nonew must be a boolean.");
  maxshift=maxshift*maxshift if(maxshift>0) else 0;

  nn=funct.get_num_lines(newcoord)-3;
  newcL=[None]*nn;
  with open(newcoord) as fin:
    nl=copyheader(fin)[0];
    if(nl!=2):
      for line in fin:
        tmps=daofile.DAOIdXY(line);
        tmpi=tmps.idn-len(newcL) +1;
        if(tmpi>0): newcL+=[None]*tmpi;
        newcL[tmps.idn]=tmps;
    else: raise SkZpipeError("using a .ap file as new-coordinate set not implemented", exclocus=_name_);
  idmax=len(newcL);
  with open(fname) as fin, open(output, 'w') as fout:
    no, rej, mm=0,0,0;
    nl=copyheader(fin, fout)[0];
    if(nl!=2):
      for line in fin:
        tmps=daofile.DAOSourceData(line, fulldata=False);
        no+=1;
        if(tmps.idn<idmax and newcL[tmps.idn]!=None):
          mm+=1;
          if(maxshift>0):
            dst=(tmps.x-newcL[tmps.idn].x)**2+(tmps.y-newcL[tmps.idn].y)**2;
            if(dst>maxshift):
              rej+=1;
              continue;
          tmps.setcoord(newcL[tmps.idn].x, newcL[tmps.idn].y);
          fout.write(str(tmps)+'\n');
        elif(rej_nonew): rej+=1;
        else: fout.write(line);
        if(mm>=nn): break;
      if(mm>=nn):
        for line in fin:
          if(rej_nonew): rej+=1;
          else: fout.write(line);
    else: raise SkZpipeError("applying to a .ap file not implemented", exclocus=_name_);
  return (no, nn, no-rej, rej);

#################################################################    
def reg2file(regfile=None, id0=0, outfile=None, hdrtemplate=None):
  """
Transform a reg file in a source list compatible with DAOPHOT

Parameters
--------
    regfile : str
        Name of the input reg file
    id0 : dict, int
        Zero-point for id number (first id = id0+1), or a dictionary with id association
    outfile : str
        Name of output file. It can be also the suffix (starting with a dot '.') to be soubstituted to '.reg' in regfile.  
        By default is set to '.lsrc'.
    hdrtemplete : str
        Name of a daophot file from which it copies the header. Otherwise it will make it up.
           
"""; 
  _name_='reg2dao';
  funct.check_file(regfile);
  if(hdrtemplate!=None): Dao_check_file(hdrtemplate, minline=daopar.DAO_Par['headerlen']);
  if(not isinstance(id0, dict) and (not isinstance(id0, int) or id0<0)): raise TypeError(_name_+": id0 must be a non-negative integer or a dictionary.");
  if(outfile==None): outfile=func.remove_extension(regfile, ('.reg',))+".lsrc"
  if(outfile[0]=='.'): outfile=func.remove_extension(regfile, ('.reg',))+outfile
  with open(regfile) as fin, open(outfile, 'w') as fout:
    if(hdrtemplate):
      with open(hdrtemplate) as ftmp:
        copyheader(ftmp, fout);
    else:
      pass;
    for line in fin:
      if(line[0]=='#' or not re.search('^(circle|box|ellipse|point|text)', line)): continue;
      
      tmpl=line.split('#');
      tmpl.append('');
      (xx,yy)=tuple(float(x) for x in re.sub("[(),]"," ", tmpl[0]).split()[1:3]);
      text= re.split('[{}]', tmpl[1].split('text=')[1])[1] if('text=' in tmpl[1].lower()) else None;
      if(isinstance(id0,int)):
        id0+=1;
        idd=id0;
      else:
        if(text in id0): idd=int(id0[text]);
        else: raise KeyError(_name_+": missing proper key in id0 for "+regfile);
      star=daopar.DAOSource((idd,xx,yy, 25.0, 1));
      fout.write(str(star)+'\n');
  
  return 0;

#################################################################
def ap1line(apfile=None, outfile=None):
  """Put .ap file in 1-line format.

Parameters
----------
""";
  if(not outfile): outfile=apfile+"_1l";
  aphfile=daofile.DAOPhotoFile(ftype='ap', fname=apfile);
  aphfile.read();
  aphfile.print(outfile);

###    
def ap2grow(apfile=None, outfile=None, apertures=None, minmag=25, normalize=False):
  """Trasform a multi-ap .ap file in a growing table.

Parameters
----------
    apfile : str
        Name of .ap file
    outfile : str
        Name of output file
    apertures : None, iterable
        "list" of the apertures (it is typeset to list bfore use).
    minmag : float
        Faintest magnitude allowed for a source to be used
    normalize : bool, int
        If the magnitudes are normalized to the last aperture, or the aperture to be used to normalize
""";
  if(not outfile): outfile=apfile+"_g";
  if(isinstance(normalize, bool)):
    if(normalize): normap= -1;
  else:
    normap=normalize-1;
    normalize=True;
  with open(apfile) as fin, open(outfile, 'w') as fout:
    header=copyheader(fin, fout);
    tmpa=[];
    if(apertures): tmpa.append(list(apertures));
    for line in fin:
      line=fin.readline();
      star=daopar.DAOSource_ap(line+fin.readline());
      if(max(star.mL)>minmag): continue;
      if(normalize): star.m=[x-star.m[normap] for x in star.m]
      tmpa.append(star.m);
      tmpa.append(star.err);
  numpy.savetxt(outfile, numpy.array(tmpa).T, fmt='%s');

###########################################################

def DAOPhotoFile_stat(fname=None, ftype=None, cols=None, coltype=None, perc=None):
  """Calculate statistics for columns of a DAOPhotoFile.

Parameters
----------
    fname : str
        Name of DAO photometric file
    ftype : str, None
        Type of DAO photometric file (extension of the prototype)
    cols : list, None
        List of columns for which to calculate statistics (1 for the first column, 2 for the second one, ...). None for all.
    coltype : str, None
        How to manage the `cols` parameter: exactly or referred to 'als' files. None for as in the file.
    perc : list, None
        List of integer with additional percentiles to calculate

Return
------
    List of a dict for each column with: 'mean', 'min', 'max', 'median', 'perc##'=percentile:10, 25, 75, 90
""";
  _name_='DAOPhotoFile_stat';
  if(not isinstance(fname,str)): raise TypeError(_name_+": 'fname' must be a string <{}>".format(fname));
  if(cols):
     if(not isinstance(cols,list)): raise TypeError(_name_+": 'cols' must be None or a list of integer");
     for ii,col in enumerate(cols):
       cols[ii]=int(col)-1;
  if(perc):
     if(not isinstance(perc,list)): raise TypeError(_name_+": 'perc' must be None or a list of integer");
     for ii,prc in enumerate(perc):
       perc[ii]=int(prc);
  else: perc=[];
  if(ftype is not None and not isinstance(ftype,str)): raise TypeError(_name_+": 'ftype' must be a string or None");

  with open(fname) as fdao:
    header=copyheader(fdao);
    nl=header[0];
    data=[];
    for line in fdao:
      if(nl==2):
        tmpl1=list( float(x) for x in fdao.readline().split() );
        tmpl2=list( float(x) for x in fdao.readline().split() );
        if(len(tmpl1)!=len(tmpl2) or len(tmpl1)<4 ): raise SkZpipeError("Problems in file '{}'".format(fname), exclocus=_name_);
        if(coltype=='als'):
          data.append(tmpl1[:4]+[tmpl2[3], tmpl2[0],  0, 0, 0]);
        else:
          data.append(tmpl1+tmpl2);
      else:
        data.append(list(float(x) for x in line.split()));
  data=numpy.array(data, numpy.float_).transpose();
  outstat=[];
  icol= cols if(cols) else range(data.shape[0]);
  for ii in icol:
    outstat.append( {'mean':round(data[ii].mean(),4), '#n': data[ii].size, 'min':round(data[ii].min(),4), 'max':round(data[ii].max(),4), 'std':round(data[ii].std(),6), 'median':round(numpy.median(data[ii]),4), 'perc10':round(numpy.percentile(data[ii], 10),4), 'perc25':round(numpy.percentile(data[ii], 25),4), 'perc75':round(numpy.percentile(data[ii], 75),4), 'perc90':round(numpy.percentile(data[ii], 90),4) } );
    for prc in perc:
      outstat[-1]['perc{}'.format(prc)]=round(numpy.percentile(data[ii], prc),4);
  return outstat;




