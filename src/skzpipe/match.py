"""Module with functions and classes related to mathing.

class Match:
    Class to manage files with matching relations and products.

MakeMatch:
    Create a Match object and make the file. Fronted for Match() and Match.make()

class MatchMap:
    Class for position maps

sourcematching:
    Matching between 2 catalogs, a master (catalog used as main reference) and a slave (used to find matches to master's sources)

"""

import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy, glob
import numpy
from astropy import wcs 

from .exceptions import *
from .parameters import basicpar as bpar
from .parameters  import database as _db
from .parameters import daoparameters as daopar
from .parameters import options as _opt
from .parameters.classes import bclasses
from .parameters.classes.fileclass import basefile
from .parameters.classes.fileclass import daofile
from .photometry.daophot import daofunctions as daofunct
from . import functions as funct
from . import mathfunct
from . import fits



def DAOmchlinechk(line):
    if(not line.startswith(" '")): return False
    if(len(line)<40): return False
    if(line.count("'")!=2): return False
    if(' ' in line[2:line.rfind("'")].strip()): return False
    try:
        coeff=[float(x) for x in line[line.rfind("'")+1:].split()]
    except:
        return False
    if(len(coeff)not in (2+6, 2+12, 2+20)): return False
    if(coeff[7]<0): return False

    return True

###############
## CLASS MCH ##
###############
class Match:
    """Class to manage files with matching relations and products.

Parameters
----------
    mch : str
        Filename of the matching file
    mode : str
        Mode for the opening of matching file. 'r' (default) to read an existing file; 'w' to create a file, deleting an existing one.
    base : str
        Basename of the matching file (filename without extension, as defined in 'match:extension' option).
        This value is used only if `mch` is None.
    dformat : str
        Format for the storing of the transformation data.
            'DAO' : DAOmaster format
            'Coord' : Using CoordTransf object
    stdout : Output object
        Standard output object.

Attributes
----------
    mch : str
        Filename of the matching file
    base : str
        Basename of the matching file (filename without extension, as defined in 'match:extension' option)
    stdout : Output object
        Standard output object.
    files : list of str
        List of input matching files
    nfr : int
        Number of input matching files
    frames : list of str
        List of the frame names (aka basenames of the files, filenames without extension)
    data : list of tuples
        List of the transformation coefficients
    nxny : List of tuples
        List of image sizes
    xxyy : List of dict
        List of directories 
    exists : bool
        If the matching file already exists
    dformat : str
        Format for the storing of the transformation data.
    


""";
    mch='';
    base='';
    frames=None;  #list of frames (basenames)
    files=None;   #list of the files used in the match
    data=[];      #list of tuples with coefficients
    nxny=None;    #list of tuples with image size
    xxyy=None;    #list of directories 
    nfr=0;
    exists=False;
    stdout=bpar.SkZp_Par['stdout'];
    dformat='DAO' #format to store the transformations

#  
    def readline(self, line='', dformat='DAO'):
        """Transform a line of matching file in a tuple, checking for length

Parameters
----------
    line : str
        String with a line from a matching file to convert into a tuple of (str, floats).
    dformat : str
        Format of the input file. 'DAO' (default) for daomaster .mch output

Return
------
    Tuple of (str, floats) with size of 1+6+2 [+6] [+8]
"""
        _name_="Match.readline";
        if(dformat.upper().startswith('DAO')):
            if(not DAOmchlinechk(line)): return ();
            tmpl=line.replace("'",'').split();
#            tmpl[0]=tmpl[0].strip();
            for ii in range(1,len(tmpl)):
                tmpl[ii]=float(tmpl[ii]);
        else: raise SkZpipeError(f"not a valid input format <{dformat}>", exclocus='Match');
        return tuple(tmpl);

#
    def read(self, filedata=True, dformat='DAO'):
        """Read the matching file and store the information, also reading the file headers.

Parameters
----------
    filedata : bool
        Flag to determine if to read also info from headers or not
    dformat : str
        Format of the input file.
         'DAO' (default) for daomaster .mch output

Return
------
    Number of files in matching file. 0 if an error occurs.
""";
        _name_="Match.read";
        if(os.path.exists(self.mch)):
                with  open(self.mch, 'r') as f_mch:
                    self.frames=[]; self.files=[]; self.data=[];
                    self.nxny=[]; self.xxyy=[];
                    for line in f_mch:
                        #read a line from mch and transform it in a tuple
                        tmpt=self.readline(line, dformat=dformat);
                        if(tmpt):
                            self.files.append(tmpt[0]);
                            self.frames.append(tmpt[0].split('.')[0]);
                            self.data.append(tmpt);
                self.nfr=len(self.frames);
                funct.check_file(self.files, bpar.DAO_Par['headerlen'], bpar.DAO_Par['namemaxlen']);
                if(filedata):
                        for fn in self.files:
                                if(dformat.upper().startswith('DAO')):
                                        with daofile.DAOPhotoFile(fname=fn) as daof:
                                                self.nxny.append((daof.header.nx, daof.header.ny));
                                                self.xxyy.append([(1,daof.header.nx), (1,daof.header.ny)]);
                            #nsrc=daof.read();
                            #stat=daof.stat();
                        for ii in range(self.nfr):
                            self.xxyy.append({ 'X':(1,self.nxny[ii][0]),   'Y':(1,self.nxny[ii][1]), 
                                                              'bar':(.5*self.nxny[ii][0], .5*self.nxny[ii][1]), 
                                                            'bar0':( self.data[ii][1]+self.data[ii][3]*.5*self.nxny[ii][0]+self.data[ii][5]*.5*self.nxny[ii][1] , self.data[ii][2]+self.data[ii][4]*.5*self.nxny[ii][0]+self.data[ii][6]*.5*self.nxny[ii][1] ) });
                self.exists=True;
                return self.nfr;
        self.exists=False;
        return 0;

    def printline(self, n=1):
        """Create a string with the data of the 'n'-th line.

Parameters
----------
    n : int
        Number of the line/frame to be printed. 1<= n <= number of frames.
""";
        _name_="Match.printline";
        if(not funct.isinteger(n)): raise TypeError(_name_+': Wrong type for n. Not an integer or convertable in an integer.');
        n=int(n)-1;
        if(n<0 or n>=self.nfr): return '';
        extra='';
        datum=self.data[n];
        if(len(datum)>9):
            for cc in datum[9:]:
              extra+="  {:11.9f}".format(cc);
        return " '{:} '  {:9.4f} {:9.4f}  {:11.9f} {:11.9f} {:11.9f} {:11.9f}  {:6.3f} {:6.4f} {:}\n".format(datum[0], datum[1], datum[2], datum[3], datum[4], datum[5], datum[6], datum[7], datum[8], extra);

    def write(self, output=None):
        """Write matching files from internal data if consistent with number of frames

Parameters
---------
    output : str, None
        To change the name of the output file.
""";
        _name_="Match.write";
        if(output is None): output=self.mch;
        if(not isinstance(output,str)): raise TypeError(_name_+": 'output' must be None or the new filename for the output.");
        if(len(self.data)==self.nfr and self.nfr>1):
            with open(output, 'w') as f_mch:
                for ii in range(1,self.nfr+1):
                    f_mch.write(self.printline(ii));
            return 0;
        return 1;

#
    def set(self, data=None):
        """Set the transformations according to a given list of tuple.

Parameters
----------
    data : list of tuple
        List of tuples for each entry of matching file to be used to set the internal variables.

""";
        _name_="Match.set";
        if(data is None or not isinstance(data, list)): return 1;
        for dd in data:
            if(not isinstance(dd, tuple)): return 2;
            if(len(dd)<9): return 3;
        self.nfr=len(data);
        self.data=data.copy();
        (self.frames, self.files)=([],[])
        for dd in data:
            self.files.append(dd[0]);
            self.frames.append(dd[0].split('.')[0]);
        return self.write();
  
### INIT ###
    def __init__(self, mch=None, mode='r', base=None, stdout=None):
        """Initialization of Match class

""";
        _name_='Match object';
        self.exists=False;
        if(mch is None):
            if(base is None): raise ValueError(_name_+": filename or basename not provided");
            if(not isinstance(base, str)): raise TypeError(_name_+": wrong type for `base`, it must be a string or None");
            self.base=base.strip();
            if(not self.base): raise ValueError(_name_+": filename or basename not provided");
            mch=self.base+_opt.SkZp_Opt['S']['match:extension'];
        if(not isinstance(mch, str)): raise TypeError(_name_+": wrong type for `base`, it must be a string or None");
        self.mch=mch.strip();
        if(not self.mch or _opt.SkZp_Opt['S']['match:extension'] not in self.mch): raise ValueError(_name_+": `mch` is not a valid filename <{mch}>! it must be the name of matching file (with extension; - if it will be generated as [directory name]_[suffix of master frame]+extension(match:extension option)).".format(mch=self.mch));

        if(hasattr(stdout, 'write')):
            self.stdout=stdout; 
        else:
            self.stdout=bclasses.OutputPipe(otype='null' if(stdout=='null') else 'out');

        if(mode=='w'): funct.clean_file(self.mch);
        if('%d' in self.mch):
            wd=os.path.basename(os.getcwd());
            self.mch=self.mch.replace('%d',wd);
        if(not self.base): self.base=self.mch.rsplit('.', 1)[0];
        self.nfr, self.frames, self.files, self.data, self.nxny, self.xxyy=0, [], [], [], [], [];
        self.read();
### INIT END ###

    def checkcoeff(self, values=None):
        """Checks the values of the coefficients""";
        _name_='check';
        if(not isinstance(values, (tuple,list))): raise TypeError(_name_+": wrong type for 'values' (tuple/list)");
        for val in values:
            if(val is not None and not isinstance(val, tuple)): raise TypeError(_name_+": elements of 'values' must be a list/tuple of 2-values tuple or None");
        nn=min(len(values), len(self.data[0])-1);
        for fi in range(1,self.nfr):
            for ii in range(nn):
                if(values[ii] is None): continue;
                if(values[ii][0]<= self.data[fi][ii+1]<=values[ii][1] ): continue;
                return (fi+1,ii);
        return None;
      

    def checkfiles(self, files=None, bytag=None, raisexc=True):
        """Checks if the files in `files` (filtred with bytag) are the files in the Match object.

Parameters
----------
    files : list
        List of files to match (master, others). The whole list or just the list of other files can be given as with a wildcard *
          (e.g. '*.als' or ['master.als', '*.als']) or with an extension to be append to filenames in 'runlist' parameter.
    bytag : dict
        Dictionary with tag name and value to select further files.

Raises
------
    TypeError :  `files`
    ValueError : if `files` has just 1 element and not valid value.
""";
        _name_='checkifiles';
        if(not isinstance(files, (list,str))): raise TypeError(_name_+": wrong type for `files` <{}>".format(files.__class__));
        if(self.exists):
            if(not isinstance(bytag, dict)): bytag=None;
            if(len(bpar.SkZp_Par['inputdata'])<2): bytag=None;

            if(not isinstance(files, list)): files=[files];
            if(len(files)==1):
                if( '*' in files[0]):
                    files=glob.glob(files[0]);
                elif(files[0][0]=='.' and len(bpar.SkZp_Par['runlist'])>1):
                    ext=files[0];
                    files=[ff+ext for ff in bpar.SkZp_Par['runlist']];
                else:
                    raise ValueError(_name_+": `files` contains just 1 value. Wrong values for list of files <{}>".format(files));
            elif(len(files)==2):
                tmpl=[];
                if( '*' in files[1]):
                    tmpl=glob.glob(files[1]);
                elif(files[0][0]=='.' and len(bpar.SkZp_Par['runlist'])>1):
                    ext=files[1];
                    tmpl=[ff+ext for ff in bpar.SkZp_Par['runlist']];
                if(tmpl):
                    files=files[0:1];
                    for tmpf in tmpl:
                        if(tmpf != files[0]): files.append(tmpf);
    
            if(bytag is not None):
                tmpl=files.copy();
                for tmpf in tmpl:
                    frm=tmpf.split('.')[0];
                    for tag in bytag:
                        if(frm not in bpar.SkZp_Par['inputdata'] or tag not in bpar.SkZp_Par['inputdata'][frm] or bpar.SkZp_Par['inputdata'][frm][tag]!=bytag[tag]): files.remove(tmpf);
            if(len(files)!=self.nfr):  return False;
            for fn in files:
                if(fn not in self.files):  return False;
            return True; 
        ##
        return False;    
    
    def applytransf(self, point=(1,1), frame=None):
        """Apply the transformation to a point
        """
        if('.' not in frame and frame in self.frames): frame=self.files[self.frames.index(frame)];
        if(frame not in self.files): raise SkZpipeError("not a valid filename!", 'Match');
        if(not isinstance(point,tuple)): raise SkZpipeError("point coordinates must be a tuple (x,y)", 'Match');
        x=point[0]; y=point[1];
        coeff=list(self.data[self.files.index(frame)][1:]);
        coeff=coeff[0:6]+coeff[8:]+[0]*(len(coeff)-23);
        
        xx=coeff[0]+coeff[2]*x+coeff[4]*y+coeff[6]*x**2+coeff[8]*x*y+coeff[10]*y**2+coeff[12]*x**3+coeff[14]*x**2*y+coeff[16]*x*y**2+coeff[18]*y**3;
        yy=coeff[1]+coeff[3]*x+coeff[5]*y+coeff[7]*x**2+coeff[9]*x*y+coeff[11]*y**2+coeff[13]*x**3+coeff[15]*x**2*y+coeff[17]*x*y**2+coeff[19]*y**3;
        return (xx,yy);

    def toCoordTransf(self, n=2):
        """Transform the transformation in the given line into a CoordTransf object
        """
        if(not isinstance(n, int) or n<=0): raise TypeError(f"Match.toCoordTransf: parameter `n` must be a positive integer.   <{n}>")
        
        data=self.data[n-1]

        if(len(data)==2):
            return bclasses.CoordTransf(coeff={'X':(data[1]), 'Y':(data[2])})
        elif(len(data)==4 or len(data)==6):
            return bclasses.CoordTransf(coeff={'X':(data[1], data[3], data[5]), 'Y':(data[2], data[4], data[6])})

    def __del__(self):
        if(isinstance(self.stdout, bclasses.OutputPipe)): self.stdout.close();
            
    def __exit__(self, exc_type, exc_value, exc_tb):
        if(isinstance(self.stdout, bclasses.OutputPipe)):
            self.stdout.close();
            self.stdout=bpar.SkZp_Par['stdout'];
        if(exc_type is not None):
            return False;

    def __enter__(self):
        return self;


##############################################################
##############################################################
    def move(self, old=None, new=None, name=None):
        """Change the position of a file from 'old' to new' in all the internal variables.

Parameters
----------
    old : int
        Position of the file/frame that has to be changed
    new : int
        New position for the file/frame.
    name : str
        Name of the frame to be changed. An alternative to 'old'
""";
        _name_='Match.move';
        if(not isinstance(new,int)): raise TypeError(_name_+": 'new' must be an integer between 0 and nfr-1.");
        if(old is not None and not isinstance(new,int)): raise TypeError(_name_+": 'old' must be an integer or None (if 'name' is used instead).");
        if(old is None and not isinstance(name,str)): raise TypeError(_name_+": 'name' must be a string (if 'old' is None).");
        if(old is None):
            if(name not in self.files and  name not in self.frames): raise ValueError(_name_+": 'name' {name} is neither a valid file or a valid frame.".format(name=name));
            old=self.files.index(name) if(name in self.files) else self.frames.index(name);
        if(old != new):
            for ll in (self.files, self.frames, self.data, self.nxny, self.xxyy ):
                ll.insert(new, ll.pop(old));
        return 0;


  ##########
    def setmaster(self, master=None, bytag=None):
        """Set the master frame, providing the exact name of the file to be used as master frame, or a dictionary of pairs tag:value from SkZp_Par['inputdata'] to use to select it. If None is given, the master frame will be selected as the one with the nearest origin from the baricenter of all the frames.

Parameters
----------
    master : str, None
        Name of the file to be used as master frame, or None.
    bytag : dict
        Dictionary with the selection parameter for the master frame: it will be the first image that satisfy all the conditions.

""";
        if( master is not None and not isinstance(master, str) ): return -1;
        if( bytag is not None and not isinstance(bytag, dict) ): return -1;
        if(master is None and bytag):
            for frm in self.frames:
                cnt=0;
                for tag in bytag:
                    if(frm in bpar.SkZp_Par['inputdata'] and tag in bpar.SkZp_Par['inputdata'][frm] and bpar.SkZp_Par['inputdata'][frm][tag]==bytag[tag]): cnt+=1;
                if(cnt==len(bytag)):
                    master=frm;
                    break;
        elif(master is None):
            barL, orL=[], [];
            barx,bary=0,0;
            for ii in range(self.nfr):
                nx,ny=self.nxny[ii];
                data=self.data[ii];
                barL.append( (data[1]+data[3]*.5*nx+data[5]*.5*ny , data[2]+data[4]*.5*nx+data[6]*.5*ny) );
                barx+=barL[-1][0]/self.nfr;
                bary+=barL[-1][1]/self.nfr;
                orL.append( (data[1] , data[2]) );
            dist0=(barx-orL[0][0])**2+(bary-orL[0][1])**2;
            master=self.data[0][0];
            for ii in range(1,self.nfr):
                dist=(barx-orL[ii][0])**2+(bary-orL[ii][1])**2;
                if(dist0 > dist):
                    master,dist0 = self.data[ii][0], dist;
                    
        self.move(name=master, new=0);
        return 0;

    ##########
    def sortbypos(self, ang=None, point='o', point0='o', keepmaster=True, write=False):
        """Sort the list of frames in mch according given direction or according the distance or their baricenters from the master origin.

Parameters
----------
    ang : float
        Angle in degree of the direcion along which to sort the frames (using the coordinates of their origins or baricenters, according to 'point'). If it is None, the geometric distance of the baricenters will be used.
    point : str
        To determnine the point of the frames to be used for the distnce: 'o'/'O'/'orig' for origins of the frames; 'b'/'B'/'baric' for the baricenters of the frames.
    point0 : str
        To determnine the reference point to be used for the distance from master frame: 'o'/'O'/'orig' for origins of the frames; 'b'/'B'/'baric' for the baricenters of the frames.
    keepmaster: bool
        Flag to keep the original master frame and sort the remaining frames. 
    write : bool
        To write the file at the end
""";
        _name_="Match.sortbypos";
        if(ang is not None and not isinstance(ang, (float,int))): raise TypeError(_name_+": Wrong type for 'ang'.");
        if(point is not None and not isinstance(point,str)): raise TypeError(_name_+": Wrong type for 'point'.");
        if(point0 is not None and not isinstance(point0,str)): raise TypeError(_name_+": Wrong type for 'point0'.");
        if(keepmaster is not None and not isinstance(keepmaster, bool)): raise TypeError(_name_+": Wrong type for 'keepmaster'.");
        point=point[0].lower();
        if(isinstance(point0,str)):  point0=point0[0].lower();
        if(point not in 'bo'): raise ValueError(_name_+": Wrong value for 'point' [{}] ('o'/'O'/'orig' for origins of the frames; 'b'/'B'/'baric' for the baricenters of the frames).".format(point));
        if(isinstance(point0,str) and point0 not in 'bo'): raise ValueError(_name_+": Wrong value for 'point0' [{}] ('o'/'O'/'orig' for origins of the frames; 'b'/'B'/'baric' for the baricenters of the frames).".format(point0));

        posl=[];
        (ndata, nfiles, nframes, nnxny, nxxyy)=([], [], [], [], []);
        oo=0;
        if(point and not keepmaster):
            self.setmaster(master=None);
            keepmaster=True;
        if(keepmaster):
            ndata.append(self.data[0]);
            nfiles.append(self.files[0]);
            nframes.append(self.frames[0]);
            nnxny.append(self.nxny[0]);
            nxxyy.append(self.xxyy[0]);
            oo=1;
        if(ang is None):
            if(point0=='o'):
                x0,y0=self.data[0][1], self.data[0][2];
            elif(point0=='b'):
                x0,y0=self.xxyy[0]['bar0'];

            if(point=='o'):
                for dd in self.data[oo:]:
                    xx,yy=dd[1]-x0, dd[2]-y0;
                    posl.append(int(xx**2+yy**2));
            elif(point=='b'):
                for ii in range(oo,self.nfr):
                    xx,yy=self.xxyy[ii]['bar0'];
                    posl.append(int((xx-x0)**2+(yy-y0)**2));

        elif(ang is not None):
            cosa=math.cos(math.pi*ang/180);
            sina=math.sin(math.pi*ang/180);
            if(point=='o'):
                for dd in self.data[oo:]:
                    posl.append(int(cosa*dd[1]+sina*dd[2]));
            elif(point=='b'):
                for ii in range(oo,self.nfr):
                    barx,bary = self.xxyy[ii]['bar0'];
                    posl.append(int(cosa*barx+sina*bary));
        ##  
        sortp=sorted(posl);
        for pos in sortp:
            ii=posl.index(pos);
            del(posl[ii]);
            ndata.append(self.data.pop(ii+oo));
            nfiles.append(self.files.pop(ii+oo));
            nframes.append(self.frames.pop(ii+oo));
        self.data  =ndata;
        self.frames=nframes;
        self.files =nfiles;

        if(write): self.write();
        return 0;

    #####
    def sort(self, method=None, param=None, write=False):
        """Sort the list of frames in mch according given method.

Parameters
----------
    method : str
        Name of the method to use to sort:
          'pos' : acccording the relative position of the frames. It actually uses method sortbypos passing `param` as parameter to the method.
          'exptime' : use the logarithm base-10 to calculate geometric mean exposure time and the absolute deviation from the mean as value for the sorting.
          'list' : it is provided the new ordered list of files.
    param : dict
        Dictionary of the parameters to use for the sorting. The names vary with the method.
        For method 'pos':
          see Match.sortbypos.
        For method 'exptime':
          'meanlog':float
             to provide a mean log(expt) to calculate the absolute deviations from the mean;
          'fullmean' : bool
             If the mean use all the values with repetitions ("weighted" mean) or each exposure time only one time. Default True.
        For method 'list':
          'files' : list
             New ordered list of the files
    write : bool
        To write the file at the end
""";
        _name_="Match.sort";

        if(not isinstance(method,str)): raise TypeError(_name_+": `method' must be a string");
        if(param is None): param={};
        if(not isinstance(param,dict)): raise TypeError(_name_+": `param' must be a dictionary");
  
        (ndata, nfiles, nframes, nnxny, nxxyy)=([], [], [], [], []);
        if(method=='pos'): return self.sortbypos(**param, write=write);
        elif(method=='exptime'):
            meanlog=param.get('meanlog');
            if(meanlog is not None and not isinstance(meanlog, float)): raise TypeError(_name_+": 'meanlog' must be a flot, if given. None to compute it.");
            fullmean=param.get('fullmean');
            if(fullmean is None): fullmean=True;
            tmpl=[math.log10(expt) for expt in funct.InputDataTagValueList(tag='EXPTIME', entrylist=self.frames)];
            if(meanlog is None):
                expt0=numpy.array(tmpl).mean() if(fullmean) else numpy.array(list(set(tmpl))).mean();
            else: expt0=meanlog;
            tmpl=sorted([ (ii,abs(tmpl[ii]-expt0)) for ii in range(len(self.files))],key=(lambda x : x[1]) );
            for x in tmpl:
                ii=x[0];

                ndata.append(self.data[ii]);
                nfiles.append(self.files[ii]);
                nframes.append(self.frames[ii]);
        elif(method=='list'):
            nfiles=param['files'].copy()
            for x in param['files']:
                ii=self.files.index(x);

                ndata.append(self.data[ii]);
                nframes.append(self.frames[ii]);
        else:
            raise ValueError(_name_+": `method` has not a valid value");

            self.data  =ndata;
            self.frames=nframes;
            self.files =nfiles;
        if(write): self.write();
        return 0;

    ##########
    def split(self, subset=None, tag=None):
        """Split a matching file in parts according to dictionary with subsets or value of a specified tag. The names of the subsets will be "{base}_{key}.mch" if 'subset' is used, or "{base}_{tag_value}.mch" if 'tag' is used.

Parameters
----------
    subset : dict
        Dictionary of list/tuple of the subsets.
    tag : str
        name of the tag to be used to split the matching file

Return
------
    Dictionary of Match objects.
""";
        if(subset is None and tag is None): return [self];
        if(subset is not None and not isinstance(subset, dict)): raise TypeError("Match.split: subset must be None or a dictionary");
        if(tag is not None and not isinstance(tag, str)): raise TypeError("Match.split: subset must be None or a text");
        if(not self.exists): raise SkZpipeError("Cannot split a non-existing matching file", exclocus=self.mch);
        if(subset is not None and tag is not None): raise SkZpipeError("Match.split: both subset and tag are defined.", exclocus=self.mch);
        mchD={};
        if(tag is not None):
            #by tag
            (tagL, tagD)=funct.InputDataSplitByTag(tag=tag, entrylist=self.frames);
            for val in tagL:
#               if(len(tagD[val])<2): raise SkZpipeError("Match.split: a subset has just 1 file.");
                mcht=Match("{:}_{:}.mch".format(self.base, str(val)), stdout=self.stdout);
                mcht.makemch("copy:"+self.mch, bytag={tag:val});
                mchD[val]=mcht;
        else:
            #by subset
            for key in subset:
                if(not isinstance(subset[key], (list,tuple))): raise TypeError("Match.split: subset must be a dictionary of lists or tuples");
#        if(len(subset[key])<2): raise SkZpipeError("Match.split: a subset has just 1 file.");
                mcht=Match("{:}_{:}.mch".format(self.base, str(key)), stdout=self.stdout);
                mcht.makemch("copy:"+self.mch, files=subset[key]);
                mchD[key]=mcht;
          
        return mchD;


  ##########
    def transf(self, x0=0, y0=0, ang=None, coeff=None):
        """Change the transformations applying a common trasformation to all the frames.

Parameters
----------
    x0 : float
    y0 : float
        Offset in x and y to apply to all the frames.
    ang : float
        Angle in degree of the rotation to apply.
    coeff : None, tuple, float
        Tuple of 4 or 6 coeffincients fo the trasformation. Or a float that will be multiplied to the previous coefficients.

Returns
-------
    check : int
        0 on success, 1 on error
""";
        if(ang is None and coeff is None):
            if(x0==0 and y0==0): return 0;
            else: coeff=1;
        if(ang is not None): 
            coeff=(x0, y0, math.cos(ang), math.sin(ang), -math.sin(ang), math.cos(ang));
        newdata=[];
        if(isinstance(coeff, tuple)):
            if(len(coeff)==6):
                x0=coeff[0]; y0=coeff[1];
                coeff=coeff[2:];
            for dd in self.data:
                newdata.append((dd[0], x0+dd[1]*coeff[0]+dd[2]*coeff[2],  y0+dd[1]*coeff[1]+dd[2]*coeff[3],  dd[3]*coeff[0]+dd[4]*coeff[2],  dd[3]*coeff[1]+dd[4]*coeff[3],     dd[5]*coeff[0]+dd[6]*coeff[2],  dd[5]*coeff[1]+dd[6]*coeff[3]) +dd[7:])
        else:
            try:
                coeff=float(coeff);
                if(coeff==-1):
                    for dd in self.data:
                        newdata.append( (dd[0], x0+dd[1],  y0+dd[2],  1.000,  0.000,  0.000,  1.000, dd[7], dd[8]) +tuple([0 for x in dd[9:]]) )
                else:
                    for dd in self.data:
                        newdata.append( (dd[0], x0+dd[1]*coeff,  y0+dd[2]*coeff,  dd[3]*coeff,  dd[4]*coeff,     dd[5]*coeff,  dd[6]*coeff) +dd[7:] )
            except:
                return 1;
        self.data=newdata;
        return 0;
    ####
    def deltamag(self):
        """Retunr the mean difference in magnitude between the master file and the other files, with standard deviation

Returns
-------
    deltamag : tuple of tuples of two floats
        A tuple containing for each additional file a tuple with mean shift in magnitude between the phometry and its standard deviation.
""";
        _name_='Match.deltamag';
        return tuple( tuple(self.data[ii][7:9])  for ii in range(1,self.nfr));
            


    ####################
    ####################
    def readDAOopt(self, optstr=None, optdict=None, master=None, nfiles=None, optfor=1):
        """Read options for DAOmatch/master

Parameters
----------
    optstr : str
        String with the option. Options for different frames are separated by colon ':'. Options for the same frame are separated by comma ',' (e.g. '[1:;' or '<14,%5,[2').
          Options of DAOmaster available are:
            %##  : consider only stars with CHI2 < ##
            <##  : consider only stars with instrumental magnitude less than (brighter than) ##
            [##  : consider only stars with sharpness index in the interval -## to +##
            |##  : consider only stars with magnitude uncertainty less than ##
        Some DAOmatch/DAOmaster options for the master frame acept values refer to the source data. Instead of the exact value it is possible to give:
          'p' followed by the percenticle (integer 1-100) to calculate the desired value;
          '#' followed by the number of sources in the master frame to use aproximately in the match (actually the program calculates first the correspending percenticle and use it to calculate the final value);
    optdict : dict
        A dictionary with specific keys:
          for options given with master frame (DAOmatch) or the transformation file (DAOmaster):
            'chi2' : float  to give the maximum chi2 value
            'chi2p': int    to give the maximum chi2 value as percentile
            'chi2#': int    to give the maximum chi2 value as number of sources in the master frame
            'mag'  : float  to give the maximum magnitude
            'magp' : int    to give the maximum magnitude as percentile
            'mag#' : int    to give the maximum magnitude as number of sources in the master frame
            'emag'  : float to give the maximum magnitude error
            'emagp' : int   to give the maximum magnitude error as percentile
            'emag#' : int   to give the maximum magnitude error as number of sources in the master frame
            'sharp' : float to give the maximum absolute sharpness value
          for subsequent frames (for DAOmatch) the options are given with the key 'other' as a list
            ;    : has the same scale and rotation as the master image; look for shifts in x and y only
            /##  : the ratio 'scaleN/scale1' of the relative scales is ##; only transformations consistent
                    with that scale factor would be considered; if the ratio is 1 (same scale) just put '/'
          other keys:
            'fixfov' : bool  to say that the frame have the same scale and orientation of the FoV
        The options in optdict will overwrite the option in optstr. the '#' version will be transformed in 'p' version, and subsequently in a value.
    master : str
        Master file of the match (first file of the list).
    nfiles : int
        Number of files to be match. Default attribute nfr
    optfor : int
        Id of the program that will use the options. 0 for DAOmatch, 1 for DAOmaster.

Return
------
    List of option, one for each file.
""";
        _name_='Match.readDAOopt';
        if(optfor==0): _name_+=' for DAOmatch';
        elif(optfor==1): _name_+=' for DAOmaster';
        else: raise ValueError(_name_);
        if(optstr is not None and not isinstance(optstr,str)): raise TypeError(_name_+": `optstr` must be a string or None");
        if(optdict is not None and not isinstance(optdict,dict)): raise TypeError(_name_+": `optdict` must be a dictionary or None");
        if(master is not None and not isinstance(master,str)): raise TypeError(_name_+": `master` must be a string or None");
        if(nfiles is not None and not isinstance(nfiles,int)): raise TypeError(_name_+": `nfiles` must be an integer or None");
        if(master is None and self.nfr): master=self.files[0];
        if(nfiles is None): nfiles=self.nfr;
        nmaster=funct.get_num_lines(master)-bpar.DAO_Par['headerlen'] if(master) else 0;
        optl, optd = ['']*nfiles, dict( (x,None) for x in ('chi2','mag','emag','sharp')+('chi2p','magp','emagp')+('chi2#','mag#','emag#')+ ('other',));
        keyd={'chi2':'%', 'mag':'<', 'emag':'|', 'sharp':'['};
      ### MASTER
        if(optstr and isinstance(optstr, str)):
            tmpl=optstr.split(':');
          #Starting with the master frame options
            if(tmpl[0]):
                for opt in tmpl[0].split(','):
                    if(opt):
                        for key in keyd:
                            if(  opt[0]==keyd[key]):
                                try:
                                    if(  opt[1]=='p'): optd[key+'p']=int(opt[2:]);
                                    elif(opt[1]=='#'): optd[key+'#']=int(opt[2:]);
                                    else: optd[key]=float(opt[1:]);
                                except Exception as err:
                                    raise SkZpipeError(str(err), exclocus=_name_);
            if(optd.get('sharpp') or optd.get('sharp#')): raise SkZpipeError("'p' and '#' not yet implemented for sharp.", exclocus=_name_);
            if(len(tmpl)>1): optd['other']=tmpl[1:];
      ###
        if(optdict): optd.update(optdict);
      ###
        for key in ('chi2','mag','emag'):
            if(optd[key+'#']):
                optd[key+'p']=math.ceil(100*optd[key0+'#']/nmaster);
            if(optd[key+'p']):
                tmpv=int(optd[key+'p']);
                tmpd=daofunct.DAOPhotoFile_stat(fname=master, cols=[ bpar.DAO_Par['DMT_Opt1'][opt[0]] ], perc=[tmpv], coltype='als')[0];
                optd[key]=tmpd['perc'+str(tmpv)];
            if(optd[key]):
                optl[0]+=keyd[key]+str(round(optd[key],3));

      ###OTHER FRAMES
        if(optd['other']): optl[1:]=optd['other'];
        if(optd.get('fixfov')):  optl[1:]=[';']*(nfiles-1);
        if(len(optl)==1):  optl.append(''); #there always at least 2 file to match
        if(nfiles!=len(optl)): optl= optl[0:-1]+optl[-1:]*(nfiles-len(optl)+1);

        for ii in range(1, len(optl)):
            if(optl[ii]!=''):
                check_val=False;
                if(re.search('['+bpar.DAO_Par['DMT_OptN'][0] +']', optl[ii][0])):
                    if(len(bpar.DAO_Par['DMT_OptN'][1])>0):
                        if(re.search('['+bpar.DAO_Par['DMT_OptN'][1] +']', optl[ii][0])): optl[ii]=optl[ii][0];
                    if(len(bpar.DAO_Par['DMT_OptN'][2])>0):
                        if(re.search('['+bpar.DAO_Par['DMT_OptN'][2] +']', optl[ii][0]) and len(optl[ii][0])>1 ): check_val=True;
                    if(len(bpar.DAO_Par['DMT_OptN'][3])>0):
                        if(re.search('['+bpar.DAO_Par['DMT_OptN'][3] +']', optl[ii][0])): check_val=True;
                    if(check_val):
                        try:
                            tmpv=float(optl[ii][1:]);
                        except:
                            optl[ii]='';
                        else:
                            optl[ii]=optl[ii][0]+str(tmpv);
                else: optl[ii]='';
        return optl;
    
    ##########
    def makemch(self, mode=None, files=None, modeoption=None, bytag=None, transf=None):
        """Create a matching file using different way.

Parameters
----------
    mode : str
        Type of tranformation to generate (all with upto 6 coefficients):
            '1'+opt
                Creates an identity transformation with additions.
                    - '{ang}': a value among {} to apply a rotation of angle 'ang'
                    - 'off'  : to use the 'OFFSETXY' tag value to set the offset of the transformations
            'wcs' 
                Use internal WCS of the images to determine the transformations.
            'dboff'+opt
                Use internal database and the header information about scale/offset to determine the transformations.
                    -mos : to dishabilitate the mosaic internal offset ('dboff-mos')
            'dao'
              Use DAOmatch. It admits the passing of options after a colon, separated by colon for different files.
              For the master frame, different options can be a comma-separated list.
              For the subsequent frames the option are just put one after the other.
              E.G. 'dao:[1:;' or 'dao:<14,%5,[2:/2:/'.
              The subsequent frames that are missing their option, the last given is used (e.g. for 3 frames 'dao:[1:;' 
              is equal to 'dao:[1:;:;')

              Options of DAOmatch available are:
                   For the master frame:
                     <##  : consider only stars with instrumental magnitude less than (brighter than) ##
                     |##  : consider only stars with magnitude uncertainty less than ##
                     %##  : consider only stars with CHI2 < ##
                     [##  : consider only stars with sharpness index in the interval -## to +##
                   If ## starts with p, the ## percentile (1-100) will be used as value.
                   '*' option (to use just a rettangular subarea) is still not supported.
                   For subsequent frames:
                     ;    : has the same scale and rotation as the master image; look for shifts in x and y only
                     /##  : the ratio 'scaleN/scale1' of the relative scales is ##; only transformations consistent
                            with that scale factor would be considered; if the ratio is 1 (same scale) just put '/'

            'copy:filename' 
              Permits to copy the transformation from an existing matching file 'filename'. You can change the old extension 
              with the one given with files, or to keep just the files listed in files or by bytag.
            'use:filename@ncoeff'
              Permits to reuse the transformation (just the first ncoeff coefficients) from an existing matching file 'filename' 
              using the data in the parameter `files` (see it). `ncoeff` must be 6,12,20.
            'merge'
              Permits to merge several matching files (given with files variable).
            'sort##@mode1[@mode2]'
              Permits to create a matching file iteratively. 
              First, it is create with mode1.
              Second the frame nearest to the global baricenter is set as master and the list of frames is sorted. 
              Additionally a mode2 is used to create the final using the sorted list.
              ## are the mandatory 2 options for the sort (see Match.sortbypos: ang, point, point0):
                1) - B/b or O/o to sort by the position of the baricenters or the origins in the mode1 trasformation 
                        system (`point` in Match.sortbypos)
                2) - B/b or O/o to sort by the position respect the baricenter or the origin of the master frame in the mode1 
                        trasformation system (`point0` in Match.sortbypos). 
                   - A/a follow by the angle of the direction along which the frames must be sorted (`ang` in Match.sortbypos). 

    files : list of str, str, dict
        List of files to match (master, others). It can be given as with a wildcard * (e.g. '*.als'; feeded to glob) 
        or with an extension to be append to filenames in parameter 'runlist'.
        If mode='copy:filename' `files` can be the new extension or the list of files to copy in the new matching file.
        If mode='use':
            a list of the new filenames (the number of entries must be the same) or maintaning the same basename/frame.
            a dictionary that map the old file/frame with the new file.
        If mode='merge', `files` must be the list of matching files.
    modeoption : dict  !!!NOT YET IMPLEMENTED !!!
        Dictionary with the options for the 'mode'. This values overwrite the ones given within mode.
        Available keys are:
          for 'mode'='dao',
            'mag' : float, str starting with p
                maximum allowed magnitude (<value);
            'chi2' : float, str starting with p
                maximum allowed chi square (<value);
            'sharp' : float, str starting with p
                maximum allowed absolute valued of sharp (-value< <value);
            'err' : float, str starting with p
                maximum allowed error in magnitude (<value);
            If the value starts with p, the value will indicate the percentile.

            'area' :  list of 4 int
                to use  only a subarea [list of 4 int: xmin, xmax, ymin, ymax].

            'scale' : float
                0 if the subsequent frame is just shifted; or the relative scale scale/scale0 respect with the first frame
            'fixfov' : bool
                True for same exact field of view: no rotation and same scale, just shifted (ideally for same camera).
                       
    bytag : dict
        Dictionary with tag name and value to select further files.{tag:value[, ...]}  
    transf : str
        alias for mode (retro-compatibility).
  
Return
------
    0/1 for succeeed/failing.
""";
        _name_='Match.makemch';
        modeL=('1','wcs','dboff','dao', 'copy','use','merge', 'sort');
        if(not mode and transf): mode=transf;
        if(mode==1): mode='1'
        if(not isinstance(mode,str) or not any(mode.startswith(md) for md in modeL)): raise ValueError(_name_+": No or wrong `mode` value. <{}>".format(mode));
        if(bytag is not None):
            if(not isinstance(bytag, dict)): raise TypeError(_name_+': `bytag` must be a dictionary');
            if(len(bpar.SkZp_Par['inputdata'])<2): raise SkZpipeError("Not enough data in the inputdata to select by tag", exclocus=self.mch);
        if(mode.startswith('copy:')):
            if(files is not None and not isinstance(files,(str,list,tuple))): raise TypeError(_name_+": mode 'copy': Wrong type for `files` (None, str, list, tuple) <{}>".format(repr(files)));
        if(mode.startswith('use:')):
            if(not isinstance(files,(list,tuple,dict))): raise TypeError(_name_+": mode 'use': Wrong type for `files` (None, str, list, tuple, dict) <{}>".format(repr(files)));
        if(mode.startswith('merge') and not isinstance(files,(list,tuple))): raise TypeError(_name_+": mode 'merge': Wrong type for `files` (list, tuple) <{}>".format(repr(files)));
        if(mode.startswith('sort') and '@' not in mode): raise TypeError(_name_+": mode 'sort': you need to specify the mode to create the matching file.");
        frames=[]

#Sort
        if(mode.startswith('sort')):
            mode=mode.lower();
            if(mode[4] not in ('b','o')): raise SkZpipeError("Wrong type for mode sort.", exclocus=_name_)
            modeL=mode.split('@');
            smode=modeL.pop(0);
            ang,point,point0=None,None,None;
            point=smode[4];
            if(smode[5] in 'bo'):
                point0=smode[5];
            elif(smode[5]=='a'):
                ang=funct.getfloat(smode[6:]);

            if(len(modeL)==2):
                print(f"Making {self.mch} {modeL[0]} + {smode} + {modeL[1]}", file=self.stdout);
            else:
                print(f"Making {self.mch} {modeL[0]} + {smode}", file=self.stdout);
            self.makemch(mode=modeL[0], files=files, modeoption=modeoption, bytag=bytag);
            self.sortbypos(ang=ang, point=point, point0=point0, keepmaster=False);
              # files=None to use the sorted version!!
            if(len(modeL)==2):
                self.makemch(mode=modeL[1], files=None, modeoption=modeoption, bytag=bytag);
            else:
                self.write()
            self.stdout.flush()
            self.read();
            return 0;
            
        
#Copy      
        if(mode.startswith('copy:')):
            if(isinstance(files, str) and files[0]!='.'): files='.'+files;
            funct.check_file(mode[5:]);
            if(files is None and bytag is None):
                shutil.copy(mode[5:], self.mch);
                print(f"Making {self.mch} {mode}", file=self.stdout);
            else:
                omch=Match(mode[5:]);
                print(f"Making {self.mch} {mode}  {files}  {bytag}", file=self.stdout);
                with open(self.mch, 'w') as f_mch:
                    with open(omch.mch) as f_omch:
                        for fn in omch.files:
                            tmpf=None;
                            line=f_omch.readline(dformat='DAO');
                            if(isinstance(files, str)):
                                tmpf=fn.split('.')[0]+files;
                            elif(files is not None):
                                if(fn not in files): continue;
                            if(bytag is not None):
                                frm=fn.split('.')[0];
                                for tag in bytag:
                                    if(frm not in bpar.SkZp_Par['inputdata'] or tag not in bpar.SkZp_Par['inputdata'][frm] or bpar.SkZp_Par['inputdata'][frm][tag]!=bytag[tag]): line='';
                            f_mch.write(line.replace(fn,tmpf) if(tmpf) else line);
            self.read();
            return 0;
#Use
        if(mode.startswith('use:')):
            omfn,ncoeff=mode[4:].split('@') if('@' in mode) else (mode[4:],'');
            if(ncoeff):
                ncoeff=int(ncoeff);
                if(ncoeff not in (6,12,20)): raise ValueError(f"{_name_}: `ncoeff` given in mode {mode} is not valid: only 6,12,20")
            funct.check_file(omfn);
            with Match(omfn) as omch:
                nfiles=len(files);
                if(nfiles>omch.nfr): raise SkZpipeError(f"The number of items in `files` must be less or equal to number of elements in the matching file  ({len(files)};{omch.nfr})", exclocus=self.mch);
                print(f"Making {self.mch} {mode}({ncoeff})  {files}  {bytag}", file=self.stdout);
                data=[];
                if(isinstance(files,dict)):
                    for fil in files:
                        frm=fil.rsplit('.',1)[0];
                        if(fil in omch.files):
                            data.append( (files[fil],)+ omch.data[ omch.files.index(fil) ][1:]);
                        elif(frm  in omch.frames):
                            data.append( (files[fil],)+ omch.data[ omch.frames.index(fil) ][1:]);
                        else: raise SkZpipeError(f"Error in the dictionary for mode 'use': file/frame {fil} is not in the matching file {omch.mch}", exclocus=_name_);
                else:
                    frames=[ff.rsplit('.',1)[0] for ff in files];
                    for ii in range(omch.nfr):
                        if(nfiles<omch.nfr):
                            if(omch.frames[ii] in frames):
                                data.append((files[frames.index(omch.frames[ii])],)+omch.data[ii][1:]);
                            else: continue;
                        else:
                            data.append((files[ii],)+omch.data[ii][1:]);
            if(len(data)!=nfiles): raise SkZpipeError("in mode 'use' the final number of files is less than in the input", exclocus=_name_);
            if(ncoeff):
                ncoeff+=3; #6->9, 12->15,  20->23 : +name +Dmag,sdev
                if(ncoeff>len(data[0])):
                    for ii in range(nfiles):
                        data[ii]=data[ii][:ncoeff]
            if(self.set(data)): return 1;
            self.read();
            return 0;
#Merge
        if(mode.startswith('merge')):
            print(f"Making {self.mch} {mode}  {' '.join(files)}  ", file=self.stdout);
            with open(self.mch, 'w') as f_mch:
                for ff in files:
                    with open(ff) as f_mm:
                        for line in f_mm:
                            f_mch.write(line);
            self.read();
            return 0;
##################
        if(not files): 
            if(self.exists): files=self.files.copy()
            else:  raise ValueError(_name_+": files is undefined and no initial list was given.");
        if(not isinstance(files, list)): files=[files];
        if(any('*' in x or '?' in x or x[0]=='.' for x in files)):
            fileL=[]
            while(files and ('*' in files[0] or '?' in files[0] or files[0][0]=='.')):
                patt=files.pop(0)
                tmpl=[]
                if( '*' in patt or '?' in patt):
                    tmpl=glob.glob(patt)
                elif(patt[0]=='.'):
                    if(len(bpar.SkZp_Par['runlist'])>1):
                        tmpl=[ff+patt for ff in bpar.SkZp_Par['runlist']];
                    else: raise ValueError(_name_+": 'files' cannot be an extension if parameter 'runlist' is not define.");
                elif(os.path.exists(patt)):
                    tmpl.append(patt)
                else:   raise ValueError(f"{_name_}: wrong values for 'files'.    <{patt}>")

                for ff in tmpl:
                    if(ff not in fileL): fileL.append(ff);
            files=fileL

          

        if(bytag is not None):
            fileL=[]
            for fff in files:
                frm=fff.rsplit('.',1)[0]
                for tag in bytag:
                    if(frm not in bpar.SkZp_Par['inputdata'] or tag not in bpar.SkZp_Par['inputdata'][frm] or bpar.SkZp_Par['inputdata'][frm][tag]!=bytag[tag]):
                        frm=None
                        break;
                if(frm): fileL.append(fff)
            files[:]=fileL
        frames=[fff.rsplit('.',1)[0] for fff in files]
      
        if(len(files)<2):  raise ValueError(f"{_name_}: not enough files. <{files}>");
        funct.check_file(files, 4, bpar.DAO_Par['namemaxlen']);
    
#    self.files=files.copy();
#    self.frames=[ x.rsplit('.',1)[0] for x in self.files];
#    self.nfr=len(self.files);
    
        funct.clean_file([self.mch]);
      #DAOMATCH 
        if(mode.startswith('dao')):
            optl=self.readDAOopt(optstr=mode[4:], optdict=modeoption, master=files[0], nfiles=len(files));
                
            print(f"Making {self.mch} dao:{optl}  {' '.join(files)}  ",file=self.stdout, flush=True);
            self.stdout.flush()
            logfile=self.base+".Log_dmt";
            with open(logfile, 'w') as f_log:
                    with subprocess.Popen(_opt.SkZp_Opt['S']['progr:exec:daomatch'], shell=False, stdin=subprocess.PIPE, stdout=f_log, stderr=subprocess.STDOUT, bufsize=0, universal_newlines=True) as daom:
                            f_log.write('=> '+files[0]+optl[0]+'\n');
                            daom.stdin.write(files[0]+optl[0]+'\n');
                            f_log.write('=> '+self.mch+'\n');
                            daom.stdin.write(self.mch+'\n');
                            daom.stdin.flush();
                            for ii in range(1, len(files)):
                                f_log.write('=> '+files[ii]+optl[ii]+'\n');
                                daom.stdin.write(files[ii]+optl[ii]+'\n');
                                f_log.write('=> y\n');
                                daom.stdin.write('y\n');
                            daom.stdin.write('\n');
            self.read();
            if(self.checkfiles(files)): return 0;
            else: return 1;

        else: ## Other modes that create themselves the matching file
            print(f"Making {self.mch} {mode}  {' '.join(files)}  ", file=self.stdout);

            with open(self.mch, 'w') as f_mch:
                mstr=frames[0];
            #1 identical
                if(mode.startswith('1')):
                    f_mch.write(" '{files[0]}   '    0.000     0.000  1.000000  0.000000  0.000000  1.000000    0.000  0.00\n")
                    for ff in files[1:]:
                        coef=[0,0, 1,0,0,1]; dmag=0;
                        if('{' in ff):
                            tmpl=re.split("[{}]", ff);
                            ff=tmpl[0];
                            opt=tmpl[1].split(',');
                            if(len(opt)==3):
                                ang=opt[2];
                                opt=opt[0:2];
                                opt.append(math.cos(math.radians(ang)));
                                opt.append(math.sin(math.radians(ang)));
                                opt.append(-opt[3]);
                                opt.append(opt[2]);
                            for ii in range(len(opt)):
                                coef[ii]=opt[ii];
                        f_mch.write(f" '{ff}  '   {coef[0]:.3f} {coef[1]:.3f}   {coef[2]:.3f}  {coef[3]:.3f}  {coef[4]:.3f}  {coef[5]:.3f}   {dmag:.3f}  0.00\n");
              #WCS
                elif(mode.startswith('wcs')):
                    fnm=mstr+".fits";
                    funct.check_file([fnm]);
                    if('off' in mode and bpar.SkZp_Par['inputdata'][mstr].get('OFFSETXY')):
                        (xoffm, yoffm, *_)=bpar.SkZp_Par['inputdata'][ mstr ]['OFFSETXY']
                    with fits.pyfits.open(fnm) as hdul:
                        wcs_tr0=wcs.WCS(hdul[0].header);
                    if(not wcs_tr0.has_celestial): return 11
                    listf=[];
                    f_mch.write(f" '{files[0]}   '    0.000     0.000  1.000000  0.000000  0.000000  1.000000    0.000  0.00\n");
                    for fff,frm in zip(files[1:], frames[1:]):
                        fn=frm+".fits";
                        funct.check_file([fn]);
                        with fits.pyfits.open(fn) as hdul:
                            wcs_tr=wcs.WCS(hdul[0].header);
                            xycrd = numpy.array([[0, 0], [hdul[0].header['NAXIS1'], 0], [0, hdul[0].header['NAXIS2']]], numpy.float_); #3 points in frame (0,0) (NX,0), (0,NY)
                        radec = wcs_tr.wcs_pix2world(xycrd, 1);
                        xycrd0= wcs_tr0.wcs_world2pix(radec, 1);  #the 3 points in master-frame reference
                        aa=(xycrd0[1][0]-xycrd0[0][0])/xycrd[1][0];
                        bb=(xycrd0[1][1]-xycrd0[0][1])/xycrd[1][0];

                        cc=(xycrd0[2][0]-xycrd0[0][0])/xycrd[2][1];
                        dd=(xycrd0[2][1]-xycrd0[0][1])/xycrd[2][1];
                        dmag,smag=0.,0.;

                        if('off' in mode and bpar.SkZp_Par['inputdata'][frm].get('OFFSETXY')):
                            (xoff, yoff, *_)=bpar.SkZp_Par['inputdata'][ frm ]['OFFSETXY']
                            xycrd0[0][0], xycrd0[0][1] = xoff-xoffm, yoff-yoffm;
                            
                        
                        self.stdout.write(".");
                        listf.append(fff);
                        f_mch.write(f" '{fff}  '   {xycrd0[0][0]:8.3f}  {xycrd0[0][1]:8.3f}  {aa:.6f}  {bb:.6f}  {cc:.6f}  {dd:.6f}    {dmag:.3f} {smag:.3f}\n")

##              z=funct.get_output(['xy2sky', fn, '0', '0']).split()[0:3];
##              (x0,y0)=tuple(funct.get_output(['sky2xy', fnm]+z).split()[4,5]);
##
##              z=funct.get_output(['xy2sky', fn, '2000', '0']).split()[0:3];
##              (x1,y1)=tuple(funct.get_output(['sky2xy', fnm]+z).split()[4,5]);
##
##              z=funct.get_output(['xy2sky', fn, '0', '2000']).split()[0:3];
##              (x2,y2)=tuple(funct.get_output(['sky2xy', fnm]+z).split()[4,5]);
##              (aa,bb,cc,dd,  dmag)=((x1-x0)/2000., -(x2-x0)/2000., (y1-y0)/2000., (y2-y0)/2000.,    0);
                    self.stdout.write("\n");
              #DB OFFSET
                elif(mode.startswith('dboff')): 
                    (instrL, instrD)=funct.InputDataSplitByTag(tag='INSTRUMENT', entrylist=frames);
                    if(len(instrL)>1):
                        print(f'Error: The images are from different instruments. It is not possible to use the database to match. {instrL}', file=self.stdout)
                        return 1;
                    instr=instrL[0];
                    if(bpar.SkZp_Par['inputdata'][frames[0]].get('OFFSETXY')):
                        if('-mos' in mode):
                            for fff,frm in zip(files, frames):
                                (xoff, yoff, *_)=bpar.SkZp_Par['inputdata'][ frm ]['OFFSETXY']
#                                print(">>:>>", fff, frm, xoff, yoff, bpar.SkZp_Par['inputdata'][ frm ]['OFFSETXY'])   #@@@@@
                                f_mch.write(f" '{fff}   '    {xoff}     {yoff}  {1.}  {0.}  {0.}  {1.}    0.000  0.00\n")
                        elif(instr in _db.SkZp_DB['mosoffset']):
                            for fff,frm in zip(files, frames):
                                (x0, y0, aa, bb, cc, dd)=_db.SkZp_DB['mosoffset'][instr][ bpar.SkZp_Par['inputdata'][ frm ]['CHIP'] ];
                                (xoff, yoff, *_)=bpar.SkZp_Par['inputdata'][ frm ]['OFFSETXY']
                                f_mch.write(f" '{fff}   '    {x0+xoff}     {y0+yoff}  {aa}  {bb}  {cc}  {dd}    0.000  0.00\n");
        
        self.read();
        if(self.checkfiles(files)): return 0;
        else: return 1;
    #################
    def make(self, mode=None, files=None, modeoption=None, bytag=None, transf=None):
        """Create a matching file using different way. Alias for Match.makemch

"""
        return self.makemch(mode=mode, files=files, modeoption=modeoption, bytag=bytag, transf=transf);


  ####################################  
    def DAOmaster(self, flag=None, sigma=None, ncoeff=None, radius=None, output=None, selopt=None):
        """Run DAOmaster to refine and obtain products of the matching.

Parameters
----------
    flag: str, int, None
        matching flags. As string '#min,%,#enough', 1 for matching of sources in all the frames. Default 1.
    sigma : float
        Value for the sigma clipping on the magnitude for the match
    ncoeff : int
        Number of transformation coefficients (2: simple shift; 4: shift and rotation; 6: shift, ratation 
        and linear trasnformation; 12: quadratic; 20: cubic).
    radius : float, list, tuple,str
        Initial matching radius, or (either as list/tuple or str) initial,min or initial,min,step  or 
        initial,min,-#iter(<0)
    output : list, str, dict, None
        Options for the final outputs: the first determine the id number of the sources; the following 5 
        global outputs (which names can be given); the last 2 output for each frame. In order they are:
          'reid': stars will be renumbered after being sorted by mean magnitude (or leave the existing ones 
                   based on the id of master frame);

          'mag' : a file with mean magnitudes and scatter;
          'cor' : a file with corrected magnitues (each magnitude from each frames corrected by the calculated offset);
          'raw' : a file with raw magnitude and errors (as in the original input files)
          'mch' : a file with the transformation table (the original will be overwritten);
          'tfr' : a file with the transfer table: a table that gives for each star the line position, not the id, 
                   in the initial input files.

          'coo' : a .coo file for each frame with the sources in the master list in the coordinates of each frame;
          'mtr' : a .mtr file for each frame with the original input, changing only the source id.
        The value can be:
          A list of the entries you want (e.g. output=['reid', 'mch'])
          A string with the desired output, always inluding the storing of the new transformation ('mch') 
            except in the case of 'test'; the renumbering ('reid) is included by default, while adding a final 'I' disables it.
              'cat' is equal to 'cor' and 'raw' together.
              'all' to set all the output options.
              'test' just run DAOmaster without any output.
          A string of 8 comma-separated y/n flags, one for each option, in the orden given above 
            (e.g. output="y,n,n,n,y,n,n,n" for 'reid' and 'mch').
          A dictionary where each entry has as key the wanted ouput and as value None, or the new filename 
            (e.g. output={'reid':None, 'mch':"xyz.transf", 'mag':"meanmag.mag"} for renumbering, new trasformations 
            stored as "xyz.transf", and mean magnitudes stored as "meanmag.mag").
          None (default) equal to 'mch'.
    selopt : str or dict
        A comma-separated list of the available options (e.g. '[1:;' or '<14,%5,[2')
          Options of DAOmaster available are:
            %##  : consider only stars with CHI2 < ##
            <##  : consider only stars with instrumental magnitude less than (brighter than) ##
            [##  : consider only stars with sharpness index in the interval -## to +##
            |##  : consider only stars with magnitude uncertainty less than ##
        A dictionary with keys:
          'chi2' : to give the maximum chi2 value
          'chi2p': to give the maximum chi2 value as percentile
          'mag'  : to give the maximum magnitude
          'magp' : to give the maximum magnitude as percentile
          'emag'  : to give the maximum magnitude error
          'emagp' : to give the maximum magnitude error as percentile
          'sharp' : to give the maximum absolute sharpness value

Reuturn
-------
   return : 2-element tuple
        It returns a tuple of 3 values: execution time, number of matched sources
     
""";
        _name_="Match.DAOmaster";
        funct.check_file([self.mch], 2, bpar.DAO_Par['namemaxlen']);
        if(not isinstance(sigma,(float,int))): raise TypeError(f"{_name_}: `sigma` must be a number  <{sigma}>")
        if(not isinstance(ncoeff,int)): raise TypeError(f"{_name_}: `ncoeff` must be an integer   <{ncoeff}>")
        if(not isinstance(radius,(float,int,str,tuple,list))): raise TypeError(f"{_name_}: `radius` must be a number or a string or tuple/list   <{radius}>")
        if(output is not None and not isinstance(output,(str,list,dict))): raise TypeError(f"{_name_}: `output` must be a string or a list or a dictionary    <{output.__class__}");
        if(selopt is not None and not isinstance(selopt,(str,dict))): raise TypeError(f"{_name_}: `selopt` must be a string or a dictionary   <{selopt.__class__}>")

        mchbkp=self.mch+".bkp";
        self.read(filedata=False);
        
      #FLAG
        if(flag is None): flag=1;
        flag=str(flag);
        flagl=[float(x) for x in flag.split(',')];
        if(len(flagl)!=3):
            if(flag == '1'):
                flag=f"{self.nfr},1,{self.nfr}"
            else:
                raise SkZpipeError(_name_+": in flags "+flag);
        else:
#flag1
            if(flagl[0]>self.nfr):
                flagl[0]=self.nfr;
                print('Warning: first flag is higher than number of frame. Set to number of frames.', file=self.stdout);
            elif(flagl[0]<=0):
                flagl[0]=1;
                print('Warning: first flag is 0 or negative. Set to 1.', file=self.stdout);
#flag2
            if(flagl[1]>1):
                flagl[1]=1;
                print('Warning: second flag is higher than 1. Set to 1.', file=self.stdout);
            elif(flagl[1]<=0):
                flagl[1]=.1;
                print('Warning: second flag is 0 or negative. Set to 0.1', file=self.stdout);
#flag3
            if(flagl[2]>self.nfr):
                flagl[2]=self.nfr;
                print('Warning: third flag is higher than number of frame. Set to number of frames.', file=self.stdout);
            elif(flagl[2]<=0):
                flagl[2]=1;
                print('Warning: third flag is 0 or negative. Set to 1.', file=self.stdout);
            flag=','.join([str(x) for x in flagl]);
    
      #MATCH RAD
        (mmtrad,smtrad,imtrad)=(1,0,0);
        if(isinstance(radius,str)):
            if(',' in radius):
                radius=radius.split(',');
        if(isinstance(radius,(list,tuple))):
            mradl=radius;
            radius=float(mradl[0]);
            mmtrad=round(float(mradl[1]),1);
            if(len(mradl)>2): smtrad=float(mradl[2]);
            if(mmtrad<=0 or mmtrad>=radius or smtrad>=radius): raise SkZpipeError("in `radius` wrong matching radius values", exclocus=_name_);
        if(smtrad==0): 
            imtrad=20;
            smtrad=max(round((radius-mmtrad)/imtrad,1),0.1);
            imtrad=int((radius-mmtrad)/smtrad);
        elif(smtrad<0):
            imtrad=int(abs(smtrad));
            smtrad=round((radius-mmtrad)/imtrad, 1);
        else:
            imtrad=int((radius-mmtrad)/smtrad);
        smtrad=round(smtrad,1);
        radius=round(mmtrad+smtrad*imtrad,1);

      #OPTIONS
        optstr, optdict='',{};
        if(isinstance(selopt,str)): optstr=selopt;
        elif(isinstance(selopt,dict)): optdict=selopt;
        optl=self.readDAOopt(optstr=optstr, optdict=optdict);
    
      #OUTPUT
        outputL, outputD=[],{};
        noutput=len(bpar.DAO_Par['DMSoutput']);
        if(output is None):   outputL, outputD= ['n','n','n','n','y','n','n','n'], {                                                  'mch':None };
        elif(output=='test'): outputL, outputD= ['n','n','n','n','n','n','n','n'], {                                                             };
        elif(output=='all'):  outputL, outputD= ['y','y','y','y','y','y','y','y'], { 'reid':None, 'mag':None, 'cor':None, 'raw':None, 'mch':None, 'tfr':None, 'coo':None,  'mtr':None };
        elif(output=='mch'):  outputL, outputD= ['n','n','n','n','y','n','n','n'], {                                                  'mch':None };
        elif(output=='mag'):  outputL, outputD= ['y','y','n','n','y','n','n','n'], { 'reid':None, 'mag':None,                         'mch':None };
        elif(output=='magI'): outputL, outputD= ['n','y','n','n','y','n','n','n'], {              'mag':None,                         'mch':None };
        elif(output=='raw'):  outputL, outputD= ['y','n','n','y','y','n','n','n'], { 'reid':None,                         'raw':None, 'mch':None };
        elif(output=='rawI'): outputL, outputD= ['n','n','n','y','y','n','n','n'], {                                      'raw':None, 'mch':None };
        elif(output=='cor'):  outputL, outputD= ['y','n','y','n','y','n','n','n'], { 'reid':None,             'cor':None,             'mch':None };
        elif(output=='corI'): outputL, outputD= ['n','n','y','n','y','n','n','n'], {                          'cor':None,             'mch':None };
        elif(output=='cat'):  outputL, outputD= ['y','n','y','y','y','n','n','n'], { 'reid':None,             'cor':None, 'raw':None, 'mch':None };
        elif(output=='catI'): outputL, outputD= ['n','n','y','y','y','n','n','n'], {                          'cor':None, 'raw':None, 'mch':None };
        elif(isinstance(output,str)):
            outputL=output.split(',');
            if(noutput!=len(outputL)): raise SkZpipeError(f"{_name_}: not enough y/n. They must be {noutput}, while they are {len(outputL)}.")
            for ii in range(noutput):
                if(outputL[ii]=='y'): outputD[bpar.DAO_Par['DMSoutput'][ii]]=None 
        elif(isinstance(output,dict)):
            for ask in bpar.DAO_Par['DMSoutput']:
                if(ask in output):
                    outputL.append('y');
                    if(output[ask] is not None and not isinstance(output[ask],str)): 
                        raise TypeError(f"{_name_}: 'ouput' as dictionary accept as values None or str! <{ask}:{output[ask]}>")
                    outputD[ask]=output[ask];
                else:
                    outputL.append('n');
        elif(isinstance(output,list)):
            for ask in bpar.DAO_Par['DMSoutput']:
                outputL.append('y' if(ask in output) else 'n');
            
      #Cleaning output files
        shutil.move(self.mch, mchbkp);  #mch will be backed-up instread of deleted, obviously
        for ii in range(len(bpar.DAO_Par['DMSext1'])):
            if(outputL[ii+1]=="y"):
                if(outputD.get(bpar.DAO_Par['DMSoutput'][ii+1]) is None ): outputD[bpar.DAO_Par['DMSoutput'][ii+1]]=self.base+bpar.DAO_Par['DMSext1'][ii];
                funct.clean_file([ outputD[ bpar.DAO_Par['DMSoutput'][ii+1]] ]);

        for ii in range(len(bpar.DAO_Par['DMSext2'])):
            if(outputL[1+len(bpar.DAO_Par['DMSext1'])+ii]=="y"):
                for ff in self.frames:
                    funct.clean_file([ff+bpar.DAO_Par['DMSext2'][ii]]);
        
        initime=int(time.time());
        logfile=self.base+".Log_dms";
        print(f"{_name_}({_opt.SkZp_Opt['S']['progr:exec:daomaster']}) with {ncoeff} coefficients for {self.mch} radius=[{radius}:{mmtrad}:{smtrad}] (flag:{flag}; sigma:{sigma}); option:{optl[0]}; output: {outputD}; logfile: {logfile}", file=self.stdout)
        with open(logfile+".tmp", 'w') as f_log:
                with subprocess.Popen(_opt.SkZp_Opt['S']['progr:exec:daomaster'], shell=False, stdin=subprocess.PIPE, stdout=f_log, stderr=subprocess.STDOUT) as daom:
                        funct.proc_writeline(mchbkp+optl[0], daom, f_log);
                        funct.proc_writeline(flag, daom, f_log);
                        funct.proc_writeline(sigma, daom, f_log);
                        funct.proc_writeline(ncoeff, daom, f_log);
                        funct.proc_writeline(radius, daom, f_log);
            
                        for ii in range(int(imtrad*.4)+2):
                                funct.proc_writeline(round(radius-ii*smtrad,2), daom, f_log);
                        for ii in range(int(imtrad*.3), int(imtrad*.7)+2):
                                funct.proc_writeline(round(radius-ii*smtrad,2), daom, f_log);
                        for ii in range(int(imtrad*.6), imtrad+1):
                                rad=round(radius-ii*smtrad,2);
                                if(rad<mmtrad): rad=mmtrad;
                                funct.proc_writeline(rad, daom, f_log);
                
                        for ii in range(_opt.OptionGet('match:minraditer')):
                                funct.proc_writeline(mmtrad, daom, f_log);
                        funct.proc_writeline(0, daom, f_log);
            
                        funct.proc_writeline(outputL[0], daom, f_log);
                        for ii in range(len(bpar.DAO_Par['DMSext1'])):
                                if(not optl[0] or bpar.DAO_Par['DMSext1Flg'][ii]):
                                        funct.proc_writeline(outputL[1+ii], daom, f_log);
                                        if(outputL[1+ii]=='y'): funct.proc_writeline(outputD[bpar.DAO_Par['DMSoutput'][ii+1]], daom, f_log);
                        for ii in range(len(bpar.DAO_Par['DMSext2'])):
                                if(not optl[0] or bpar.DAO_Par['DMSext2Flg'][ii]):
                                        funct.proc_writeline(outputL[1+len(bpar.DAO_Par['DMSext1'])+ii], daom, f_log);
                            
        stars='';
        if(outputD.get('mch') != self.mch): shutil.copy(mchbkp, self.mch); #restored if not created a new .mch (test) or using a different filename
        with open(logfile+".tmp") as f_tmp:
            with open(logfile, "w") as f_log:
                for line in f_tmp:
                    line=re.sub('[\x00-\x08\x0c-\x1f]', '', line);
                    f_log.write(line);
                    if('stars within radius' in line): stars=line.strip();
        funct.clean_file(logfile+".tmp");
        
        self.read();
        flenL=[];
        for ff in self.files:
                flenL.append(funct.get_num_lines(ff)-bpar.DAO_Par['headerlen']);
        
        print(f"  {stars}  in  {int(time.time()-initime)}s   [stat #sources: min {min(flenL)}; max {max(flenL)}; mean {int(numpy.mean(flenL))}]", file=self.stdout);
        stars=int(stars.split()[0].replace(',',''));
        return (int(time.time()-initime), stars) ;
 ### DAOmaster
    
  ####################################  
    def refine(self, mode='DAOmaster', flag=None, sigma=None, ncoeff=None, radius=None, output=None, selopt=None):
        """Refine the coordinate transformation and produce matching output.

Parameters
----------
    mode : str
        Mode to refine. Default (and only): 'DAOmaster' (or 'DAO').
    flag: str, int, None
        Matching flags. As string '#min,%,#enough', 1 for matching of sources in all the frames. Default 1.
    sigma : float
        Value for the sigma clipping on the magnitude for the match
    ncoeff : int
        Number of transformation coefficients (2: simple shift; 4: shift and rotation; 6: shift, ratation and linear trasnformation; 12: quadratic; 20: cubic).
    radius : float, list, tuple,str
        Initial matching radius, or (either as list/tuple or str) initial,min or initial,min,step  or initial,min,-#iter(<0)
    output : list, str, dict, None
        Options for the final outputs: the first determine the id number of the sources; the following 5 global outputs (which names can be given); the last 2 output for each frame. In order they are:
          'reid': stars will be renumbered after being sorted by mean magnitude (or leave the existing ones based on the id of master frame);

          'mag' : a file with mean magnitudes and scatter;
          'cor' : a file with corrected magnitues (each magnitude from each frames corrected by the calculated offset);
          'raw' : a file with raw magnitude and errors (as in the original input files)
          'mch' : a file with the transformation table (the original will be overwritten);
          'tfr' : a file with the transfer table (table with for each star the position, not the id,  in the initial input files);

          'coo' : a .coo file for each frame with the sources in the master list in the coordinates of each frame;
          'mtr' : a .mtr file for each frame with the original input, changing only the source id.
        The value can be:
          a list of the entries you want (e.g. output=['reid', 'mch'])
          a string with the desired output, always inluding the storing of the new transformation ('mch') except in the case of 'test';
          the renumbering ('reid) is included by default, while adding a final 'I' disables it.
            'cat' is equal to 'cor' and 'raw' together.
            'all' to set all the output options.
            'test' just run DAOmaster without any output.
          a string of 8 comma-separated y/n flags, one for each option, in the orden given above (e.g. output="y,n,n,n,y,n,n,n" for 'reid' and 'mch').
          a dictionary where each entry has as key the wanted ouput and as value None, or the new filename (e.g. output={'reid':None, 'mch':"xyz.transf", 'mag':"meanmag.mag"} for renumbering, new trasformations stored as "xyz.transf", and mean magnitudes stored as "meanmag.mag").
          None (default) equal to 'mch'.
    selopt : str or dict
        A comma-separated list of the available options (e.g. '[1:;' or '<14,%5,[2')
          Options of DAOmaster available are:
            %##  : consider only stars with CHI2 < ##
            <##  : consider only stars with instrumental magnitude less than (brighter than) ##
            [##  : consider only stars with sharpness index in the interval -## to +##
            |##  : consider only stars with magnitude uncertainty less than ##
        A dictionary with keys:
          'chi2' : to give the maximum chi2 value
          'chi2p': to give the maximum chi2 value as percentile
          'mag'  : to give the maximum magnitude
          'magp' : to give the maximum magnitude as percentile
          'emag'  : to give the maximum magnitude error
          'emagp' : to give the maximum magnitude error as percentile
          'sharp' : to give the maximum absolute sharpness value

Reuturn
-------
   return : 2-element tuple
        It returns a tuple of 3 values: execution time, number of matched sources
     
""";
        _name_="Match.refine";
        if(mode.upper().startswith('DAO')):
            return self.DAOmaster(flag=flag, sigma=sigma, ncoeff=ncoeff, radius=radius, output=output, selopt=selopt);
        else: raise ValueError(f"{_name_}: Wrong value for `mode` parameter.")

  ###
    def DAOrefine(self, flag=None, sigma=None, ncoeff=None, radius=None, output=None, selopt=None):
        """Run DAOmaster to refine and obtain products of the matching. See refine or DAOmaster.
"""
        return self.DAOmaster(flag=flag, sigma=sigma, ncoeff=ncoeff, radius=radius, output=output, selopt=selopt);



  #########################
  ##########
    def DAOraw1line(self, rawfile=None, output=None, header=1):
        """Tranform a multi-magnitude ouput of DAOmaster in a format with a line for each source (DAOmaster put up to 6 pairs of data in a single line), mantaining the output format of the data.

Parameters
----------
    rawfile : str
        Name of the file to be converted, or the suffix (e.g. '.xyz') or the type ('raw', 'cor'). Default is 'raw'.
    output : str
        Output filename. Default is the rawfile filename with suffix '1'.
    header : integer
        Flag to determine if:
            1 : write normally the header (default)
            0 : do not write the header
           -1 : write the header commented out with a '#'
""";
        _name_='Match.DAOraw1line'
        if(rawfile is None or rawfile=='raw'): rawfile=self.base+'.raw';
        elif(rawfile=='cor'): rawfile=self.base+'.cor';
        elif(rawfile[0]=='.'): rawfile=self.base+rawfile;
        if(not os.path.exists(rawfile)): raise IOError(f"Input file {rawfile} doesn't exist!")
        if(output is None): output=rawfile+"1";
        elif(output[0]=='.'): output=self.base+output;
        nline=math.ceil((self.nfr+1)/6.);
        com='' if(header>0) else '#';
        with open(rawfile) as f_in, open(output, 'w') as f_out:
            for i in range(bpar.DAO_Par['headerlen']):
                line=f_in.readline();
                if(header): f_out.write(com+line);
            for line in f_in:
                line=line.rstrip();
                for i in range(1,nline):
                    line+=" "+f_in.readline().strip();
                f_out.write(line+"\n");

    ##########
    def DAOraw2Timeseries(self, rawfile=None, output=None, tags=None, inputdata=None, tagtime='MJD'):
        """Tranform a multi-magnitude ouput of DAOmaster in a time series using time information (tagtime='MJD') in 'inputdata'. The output is a table where first column is the filename from which the magnitude comes, second column the time, then columns for additional information from 'tags', for each source there are 2 column (mag, err).

Parameters
----------
    rawfile : str
        Name of the file to be converted, or the type ('raw, 'cor'), or the suffix with inutial dot.
    output : str
        Output filename. If not given it would be 'rawfile'+'1'
    tags : list,None
        List of additional tag whose information will be added before the sources columns
    inputdata : dict,None
        Dictionary with information for time ('MJD') for each file used by DAOmaster. Default SkZp_Par['inputdata'].
    tagtime : str
        Key of 'inputdata' with the time of the observation. Default 'MJD'.
""";
        _name_='Match.DAOraw2Timeseries'
        if(rawfile=='raw'): rawfile=self.base+'.raw';
        elif(rawfile=='cor'): rawfile=self.base+'.cor';
        elif(rawfile[0]=='.'): rawfile=self.base+rawfile;
        if(not os.path.exists(rawfile)): raise IOError(f"{_name_}: Input file {rawfile} doesn't exist!")
        if(output is None): output=rawfile+"TS";
        if(len(bpar.SkZp_Par['runlist'])<self.nfr): raise SkZpipeError(_name_+": Missing input data");
        if(tags is None): tags=[];
        if(not isinstance(tags, list)): raise ValueError(_name_+": Wrong value for tags. It should be a list");
        if(inputdata is None): inputdata=bpar.SkZp_Par['inputdata'];
        if(not isinstance(inputdata, dict)): raise ValueError(_name_+": Wrong value for inputdata. It should be a dict");
        othrL=[];
        for tag in tags:
            if(not isinstance(tag, str) or tag not in bpar.SkZp_Par['datatag']): raise KeyError(f"{_name_}: Wrong '{tag}' tag in tags")
            othrL.append([]);
        mjdL=[];
        for frm in self.frames:
            if(frm not in inputdata): raise SkZpipeError(_name_+": Missing input data for "+frm);
            mjd=inputdata[frm][tagtime];
            if(mjd is None or not isinstance(mjd, float)): raise SkZpipeError(_name_+": Missing time data");
            mjdL.append(mjd);
            for i in range(len(tags)):
                othrL[i].append(inputdata[frm][tags[i]]);
                
        nline=math.ceil((self.nfr+1)/6.);
        tmpa=[self.frames, mjdL]+othrL;
        with open(rawfile) as f_in:
            for i in range(3):
                line=f_in.readline();
            for line in f_in:
                tmpl=line.split()[3:];
                for i in range(1,nline):
                    tmpl+=f_in.readline().split();
                tmpl=tmpl[:-2];
                if(len(tmpl)!=2*self.nfr): raise SkZpipeError(_name_+": Problems reading input file: a line with less data."+repr(tmpl));
                tmpa.append(tmpl[0::2]);
                tmpa.append(tmpl[1::2]);
        numpy.savetxt(output, numpy.array(tmpa).T, fmt='%s');

    ##########
    def DAOraw1line2Timeseries(self, rawfile=None, output=None, tags=None, inputdata=None, tagtime='MJD'):
        """Tranform a 1-lined multi-magnitude ouput of DAOmaster in a time series using time information (tagtime='MJD') in 'inputdata'. The output is a table where first column is the filename from which the magnitude comes, second column the time, then columns for additional information from 'tags', for each source there are 2 column (mag, err).

Parameters
----------
    rawfile : str
        Name of the file to be converted, or the type ('raw1, 'cor1'), or the suffix with inutial dot.
    output : str
        Output filename. If not given it would be 'rawfile'+'1'
    tags : list,None
        List of additional tag whose information will be added before the sources columns
    inputdata : dict,None
        Dictionary with information for time ('MJD') for each file used by DAOmaster. Default SkZp_Par['inputdata'].
    tagtime : str
        Key of 'inputdata' with the time of the observation. Default 'MJD'.
""";
        _name_='Match.DAOraw1line2Timeseries'
        if(rawfile=='raw' or rawfile=='raw1'): rawfile=self.base+'.raw1';
        elif(rawfile=='cor' or rawfile=='cor1'): rawfile=self.base+'.cor1';
        elif(rawfile[0]=='.'): rawfile=self.base+rawfile;
        if(not os.path.exists(rawfile)): raise IOError(f"{_name_}: Input file {rawfile} doesn't exist!")
        if(output is None): output=rawfile+"TS";
        if(len(bpar.SkZp_Par['runlist'])<self.nfr): raise SkZpipeError(_name_+": Missing input data");
        if(tags is None): tags=[];
        if(not isinstance(tags, list)): raise ValueError(_name_+": Wrong value for tags. It should be a list");
        if(inputdata is None): inputdata=bpar.SkZp_Par['inputdata'];
        if(not isinstance(tags, dict)): raise ValueError(_name_+": Wrong value for inputdata. It should be a dict");
        othrL=[];
        for tag in tags:
            if(not isinstance(tag, str) or tag not in bpar.SkZp_Par['datatag']): raise KeyError(f"{_name_}: Wrong '{tag}' tag in tags")
            othrL.append([]);
        mjdL=[];
        for frm in self.frames:
            if(frm not in bpar.SkZp_Par['runlist']): raise SkZpipeError(_name_+": Missing input data");
            mjd=bpar.SkZp_Par['inputdata'][frm]['MJD'];
            if(mjd is None or not isinstance(mjd, float)): raise SkZpipeError(_name_+": Missing MJD data");
            mjdL.append(mjd);
            for i in range(len(tags)):
                othrL[i].append(bpar.SkZp_Par['inputdata'][frm][tags[i]]);
                
        tmpa=[self.frames, mjdL]+othrL;
        with open(rawfile) as f_in:
            for i in range(3):
                line=f_in.readline();
            for line in f_in:
                tmpl=line.split()[3:-2];
                if(len(tmpl)!=2*self.nfr): raise SkZpipeError(_name_+": Problems reading input file: a line with less data."+repr(tmpl));
                tmpa.append(tmpl[0::2]);
                tmpa.append(tmpl[1::2]);
        numpy.savetxt(output, numpy.array(tmpa).T, fmt='%s');

  ##########
    def DAOrawselect(self, rawfile=None, select=None, output=None):
        """Filter a multimagnitude output using the values of the columns.

Parameters
----------
   rawfile : str
        Name of the file to filter.  Use 'raw' or 'cor' to operate on the .raw or .cor file produced by DAOmaster
   select : dict
        Dictionary where the absolute values of keys are the number of the column to filter, while the sign is to 
        keep the value greater (+) or lesser (-) or equal than the given value
   output : str
        Name of the output. By default the output filename is input filename +'F'
""";
        _name_='DAOrawselect';
        if(not isinstance(select, dict)): raise TypeError(f"{_name_}: parameter `select` must be a dictionary");
        if(not select): raise ValueError(f"{_name_}: parameter `select` is not set");
        tmpd={};
        for pos in select:
            tmpd[int(pos)]=float(select[pos]);
        select=tmpd;
        if(rawfile=='raw'): rawfile=self.base+'.raw';
        elif(rawfile=='cor'): rawfile=self.base+'.cor';
        elif(rawfile[0]=='.'): rawfile=self.base+rawfile;
        if(not os.path.exists(rawfile)): raise IOError(f"Input file {rawfile} doesn't exist!")
        if(output is None): output=rawfile+"F";
        nline=math.ceil((self.nfr+1)/6.);
        with open(rawfile) as f_in, open(output, 'w') as f_out:
            for i in range(bpar.DAO_Par['headerlen']):
                line=f_in.readline();
                f_out.write(line);
            for line in f_in:
                flg=0;
                for i in range(1,nline):
                    line+=f_in.readline();
                tmpl=[float(x) for x in line.split()];
                for pos in select:
                    posa=abs(pos);
                    if(posa==0 or posa>len(tmpl)):  raise ValueError("Wrong value for a key in select");
                    sgn=pos/posa;
                    if(sgn>0 and tmpl[posa-1]>=select[pos]): flg+=1;
                    elif(sgn<0 and tmpl[posa-1]<=select[pos]): flg+=1;
                if(flg==len(select)): f_out.write(line);



def MakeMatch(mch=None, omode='r', base=None, stdout=None,   mode=None, files=None, modeoption=None, bytag=None, transf=None):
    """Create a Match object and make the file. Fronted for Match() and Match.make()
    """
    obj=Match(mch=mch, mode=omode, base=base, stdout=stdout)
    obj.makemch(mode=mode, files=files, modeoption=modeoption, bytag=bytag, transf=transf)
    return obj

############################
############################    


   

###############
## CLASS MAP ##
###############
class MatchMap:
    """Class for position maps.

  """
    nx,ny=0,0;
    mapa=None;
    step=30;
    x0,y0=None,None;

    def check():
        """Integrity check""";  
        if(self.nx<=0 or self.ny<=0 or self.map is None or not isinstance(self.map, list) or self.x0==none or self.y0 is None): raise SkZpipeError("missing data!", 'MachMap');
        if(len(self.map)!=self.nx): raise SkZpipeError("missing data!", 'MachMap');

    def allocate(self):
        """Create the map"""  
        if(self.nx<=0 or self.ny<=0): raise SkZpipeError("cannot allocate space if nx,ny <=0!!", 'MachMap');
        mapa=numpy.zeros((self.ny, self.nx),dtype=numpy.int16);
  
    def fill1(plist=None):
        if(not isinstance(plist, list) or len(plist)!=4): raise SkZpipeError('wrong use', 'MatchMap');
        xb,yb=plist[0];
        for ii in range(1,4):
            xb+=plist[ii][0];
            yb+=plist[ii][1];
            if(plist[0][1]>plist[ii][1]):
                tmpt=plist[0];
                plist[0]=plist[ii];
                plist[ii]=tmpt;
        xb*=.25; yb*=.25;
        angl=math.atan2(plist[0][0],plist[0][1]);
        for x in plist[1:]:
            angl.append(math.atan2(x[0],x[1])-angl[0]);
        angl[0]=0;
        for ii in range(1,4):
            if(angl[ii]<0): angl[ii]+=2*math.pi;
        sortp=sorted(angl);
        tmpl=[];
        for x in sortp:
            tmpl.append(plist[angl.index(x)]);
        plist=tmpl;
        
  ###
    def fill(self, mch=None):
        try:
            self.check();
        except:
            self.allocate();
        self.check();
        if(mch is None or not isinstance(mch, Match)): raise SkZpipeError('not passing a Match object.', 'MatchMap');
        for ii in mch.nfr:
            pointl=[];
            nx,ny=mch.nxny[ii];
            pointl.append(mch.applytransf(( mch.xxyy[ii][0][0], mch.xxyy[ii][1][0] ), self.files[ii]));
            pointl.append(mch.applytransf(( mch.xxyy[ii][0][1], mch.xxyy[ii][1][0] ), self.files[ii]));
            pointl.append(mch.applytransf(( mch.xxyy[ii][0][1], mch.xxyy[ii][1][1] ), self.files[ii]));
            pointl.append(mch.applytransf(( mch.xxyy[ii][0][0], mch.xxyy[ii][1][1] ), self.files[ii]));
            self.fill1(pointl);
        
  ### INIT ###
    def __init__(self, x0=None, y0=None, nx=0,ny=0, step=0):
        """Initializing MatchMap object"""
        self.x0,self.y0=x0,y0
        self.nx,self.ny=nx,ny
        self.step=step


    ### INIT END###

    def print(self, fout=None):
        self.check();
        if(fout is None or not isinstance(fout, io.TextIOWrapper)): fout=self.stdout;
        fout.write(f"# {self.nx:4d} {self.ny:4d}  {self.x0:8.2f} {self.y0:8.2f}  {self.step:4.2f}\n");
        for ii in range(self.nx):
            for jj in range(self.ny):
                fout.write(f"{(self.ii+self.x0-.5)*self.step:9.1f} {(self.jj+self.y0-.5)*self.step:9.1f}  {self.map[ii][jj]:3d}  {self.ii:4d} {self.jj:4d}\n")
            fout.write('\n');
            fout.flush();

    def shrink(cutvalue=0):
        self.check();
        x0,y0=0,0;
        x1,y1=self.nx,self.ny;
        for ii in range(x0,x1):
            for jj in range(y0,y1):
                if(self.map[ii][jj]>cutvalue): break;
            if(jj==y1): x0+=1;
            else: break;
        for ii in range(x1-1,x0-1,-1):
            for jj in range(y0,y1):
                if(self.map[ii][jj]>cutvalue): break;
            if(jj==y1): x1-=1;
            else: break;
        for jj in range(y0,y1):
            for ii in range(x0,x1):
                if(self.map[ii][jj]>cutvalue): break;
            if(ii==x1): y0+=1;
            else: break;
        for jj in range(y1-1,y0-1,-1):
            for ii in range(x0,x1):
                if(self.map[ii][jj]>cutvalue): break;
            if(ii==x1): y1-=1;
            else: break;

        if(x0>0): x0-=1;
        if(y0>0): y0-=1;
        if(x1<self.nx): x1+=1;
        if(y1<self.ny): y1+=1;
        
        if(x0>0 or x1<self.nx):
            self.map=self.map[x0:x1];
            self.nx=x1-x0;
        if(y0>0 or y1<self.ny):
            for ii in range(self.nx):
                self.map[ii]=self.map[ii][y0:y1];
        self.ny=y1-y0;
        self.x0+=x0;
        self.y0+=y0;

    def __exit__(self, exc_type, exc_value, exc_tb):
        if(exc_type is not None):
            return False;

    def __enter__(self):
        return self;

####################
####################
def sourcematching(master=None, slave=None, ctype=None, iteration=None, clip=None, justbest=True, coordtransf=None, verb=False):
    """Matching between 2 catalogs, a master (catalog used as main reference)
    and a slave (used to find matches to master's sources).

Parameters
----------
    master : sequence of IdXY objects
        Sequence/list of IdXY objects used as reference catalog
    slave : sequence of IdXY objects
        Sequence/list of IdXY objects used as catalog to find matching 
        candidates for master's sources.
        It should be the denser catalog.
    ctype : str
        Type of coordinates used in x and y attributes of IdXY objects.
          'cart' : for cartesian coordinates (on a flat plane).
          'sph' : for spherical coordinates (on a spherical surface, 
            like equatorial or galactic coordinates).
    iteration : dict
        Dictionary with values to calculate the matching distances 
        using numpy.linspace.
          'start': starting input value for matching distance (mandatory).
          'stop': ending input value for matching distance. If not 
                provided, the procedure will use  a single matching 
                distance ('stop'='start', 'num'=1).
          'num': number of input value for matching distance. If not
                provided and neither 'step', 
                'num'=2 if 'start'!='stop', num=1 otherwise. 
                If `justbest` is False, 'num' is set to 1.
          'step': step for input value for matching distance (used olny 
                if 'num' is not given)
          'funct': callable executed eventually on the output of 
                numpy.linspace to obtain matching distances.
    clip : dict  
        Dictionary with the values for the data clipping for data of 
        sources. 
        The keys can be a tuple of 2 strings (with the name of the 
        measurement and its uncertainty) or a string (the name of the 
        measurement;, the uncertainty name will be obtain adding the 
        prefix 'er_'), while the values are float or tuple.
        It is not used if 'justbest' is False.
        The keys are the names of the datum; if the datum is the 
        attribute of a attribute, the names are concatenated with 
        colon ':'.
        The values are the thresholds for clipping. The threshold is 
        compared with the difference between the value of master source 
        and slave source.
          If positive, it is the maximum permitteed ratio between the 
            difference and the difference uncertainty (sigma clipping).
          If negative, its absolute value is the maximum permitted value 
            for the absolute value of the difference.
    justbest : bool
        Flag to determine the return values (it influences the 
        `iteration` information). 
        If True, just the best match is return, with its information 
          (see Return section).
        If False, all the slave sources inside the matching distance 
          are returned (see Return section). 
          Only one matching distance is allowed in this case ('num' of 
          `iteration` is set to 1) and `clip` is not used.
    coordtransf: CoordTransf object or dict of CoordTransf object (NOT YET IMPLEMENTED)
        Coordinate transformation to be applied to the `slave` catalog 
        or dictionary with 'master' and/or 'slave' as keys.
        To correct for known offset, rotations, ...
    subarea : dict
        Dictionary with option for subarea regrouping.
        The square-shape area covered by both master and slave catalogs 
        is divided in several 'nx'x'ny' subareas. This subareas are used 
        to reduce the comparisons among sources.
          'size': to provide the size of the subarea square
          'dens': mean value of 'density' to calculate the size (an 
          average number of sources per subarea)

          '0'   : tuple with coordinates of the origin of the area
          'nxny': tuple with number of subareas in X and Y axes
    verb : bool
        Verbosity flag

Return
------
    output : dict with list of IdXY objets
        Dictionary with:
          'match': list of matching position. List of tuples containing: 
            if `justbest` is True (only best match)
                the position of the object in master catalog;
                a tuple with: the position of the object in slave catalog; 
                radial distance; dx distance; dy distance; clipping ratios
            if `justbest` is False (all the sources in the nearby)
                the position of the object in master catalog;
                a list of tuples with: the position of the object in 
                slave catalog; distance
            Positions start with 0
          'm-rej': list of position of unmatched objects in master catalog
          's-rej': list of position of unmatched objects in slave catalog


    """
    _name_='sourcematching'
    if(not hasattr(master,'__iter__')): raise TypeError(f"{_name_}:`master` must be an itarable.   <{master.__class__}>")
#    master=list(master) ## !!!!! COULD EXIST BETTER SOL
#    if(not all(isinstance(x, bclasses.IdXY) for x in master)): raise SkZpipeError(f"`master` must be a sequence of IdXY objects", exclacus=_name_)
    if(not hasattr(slave,'__iter__')): raise TypeError(f"{_name_}: `slave` must be a sequence.   <{slave.__class__}>")
#    slave=list(slave)
#    if(not all(isinstance(x, bclasses.IdXY) for x in slave)): raise SkZpipeError(f"`slave` must be a sequence of IdXY objects", exclacus=_name_)
    
    ctype=bclasses.unaliasvarname(ctype)
    if(not isinstance(ctype, tuple) ): raise ValueError(f"{_name_}: Wrong value for `ctype`")
#    if(not isinstance(ctype, str) ): raise TypeError(f"{_name_}: `ctype` must be a string   <{ctype.__class__}>")
#    if(ctype not in ('xy', 'sph')): raise SkZpipeError(f"`ctype` can be only 'xy','sph'   <{ctype}>", exclacus=_name_)

    if(not isinstance(iteration, dict) ): raise TypeError(f"{_name_}: `iteration` must be a dict.   <{iteration.__class__}>")
    tmps=set(iteration.keys())-{'start','stop', 'num','step','funct'}
    if(tmps): raise SkZpipeError(f"Keys in `iteration` can be only 'start','stop','num','step','funct'.   <{tmps}>", exclacus=_name_)
    if('start' not in iteration): raise SkZpipeError(f"Key 'start' must be present in `iteration`.", exclacus=_name_)
    if('funct' in iteration and not callable(iteration['funct'])):
        raise ValueError(f"{_name_}: Optional key 'funct' in `iteration` must be a callable.   <{iteration['funct'].__class__}>")
    tmps=set(iteration.keys())-{'funct'}
    if(not all(isinstance(iteration[x], (float,int)) for x in tmps)): raise ValueError(f"{_name_}: Values in `iteration` (except for 'funct') must be a number (float or int)")

    if(clip is not None and not isinstance(clip, dict) ): raise TypeError(f"{_name_}: `clip` must be a dictionary {'dataname':clipping_value}.   <{type(clip)}>")
    if(clip is not None):
        if(not all(isinstance(x, str) for x in clip.keys())): raise SkZpipeError(f"Keys in `clip` must be a string.   <{clip}>", exclacus=_name_)
        if(not all(isinstance(x, (float,int)) for x in clip.values())): raise SkZpipeError(f"Values in `clip` must be a number (float or int).   <{clip}>", exclacus=_name_)


    if(isinstance(coordtransf, bclasses.CoordTransf) ): coordtransf={'slave':coordtransf}
    if(coordtransf is not None):
        if(not isinstance(coordtransf, dict) ): raise SkZpipeError(f"`coordtransf` must be a dict or None.   <{coordtransf.__class__}>", exclacus=_name_)
        tmps=set(coordtransf.keys())-{'master','slave'}
        if(tmps): raise SkZpipeError(f"Keys in `coordtransf` can be only 'master','slave'   <{tmps}>", exclacus=_name_)
        if(not all(isinstance(x, bclasses.CoordTransf) for x in coordtransf.values())): raise SkZpipeError(f"Values in `coordtransf` must be CoordTransf objects", exclacus=_name_)


    if(subarea is None): subarea={'dens':100}
    if(not isinstance(subarea, dict) or not subarea): raise TypeError(f"{_name_}: `subarea` must be a no-empty dict   <{type(subarea)}>")
    _s_num=('size','dens')
    _s_tup=( '0','nxny')
    tmps=set(subarea.keys())-set(_s_num+_s_tup)
    if(tmps): raise SkZpipeError(f"Keys in `subarea` can be only {_s_num+_s_tup}   <{tmps}>", exclacus=_name_)
    if(not any(subarea.get(x) for x in _s_num )): raise SkZpipeError(f"`subarea` must have one of these keys {_s_num}", exclacus=_name_)
    if(not all(isinstance(subarea[x], (float,int)) for x in _s_num if(subarea.get(x)))): 
        raise ValueError(f"{_name_}: Values for {_s_num} in `subarea` must be a number (float or int)")
    if(not all(isinstance(subarea[x], (tuple,list)) for x in _s_tup if(subarea.get(x))) or not all(isinstance(y, (float,int)) for x in _s_tup for y in subarea.get(x, []) ) ): 
        raise ValueError(f"{_name_}: Values for {_s_tup} in `subarea` must be a tuple of 2 numbers (float or int)")

    if(not isinstance(verb, bool) ): raise SkZpipeError(f"`verb` must be a bool   <{verb.__class__}>", exclacus=_name_)

  #Iteration distance
    iteration=iteration.copy()
    if('stop' not in iteration or not justbest):
        iteration['stop']=iteration['start']
        iteration['num']=1
    if('num' not in iteration):
        if('step' in iteration): iteration['num']=int(round((iteration['stop']-iteration['start'])/iteration['step'],0))
        else:  iteration['num']=2
    iterdist=numpy.linspace(iteration['start'], iteration['stop'], iteration['num'])
    if('funct' in iteration): iterdist=tuple(iteration['funct'](x) for x in iterdist)

    if(verb): print(f"From distance {iterdist[0]:.3f} to {iterdist[-1]:.3f} in {iterdist['num']} iterations", file=bpar.SkZp_Par['stdout'])

  #SUBareas
    coordmst=numpy.array(x.coordT() for x in master)
    nmst=len(coordmst)
    coordslv=numpy.array(x.coordT() for x in slave)
    nslv=len(coordslv)

    xMmin,yMmin=coordmst.min(axis=0)
    xMmax,yMmax=coordmst.max(axis=0)
    xSmin,ySmin=coordslv.min(axis=0)
    xSmax,ySmax=coordslv.max(axis=0)

    subsize=subarea.get( 'size', numpy.sqrt((xSmax-xSmin)*(ySmax-ySmin)*subarea['dens']/nslv) ) #using slave data, or size could be too small
    if(any(subsize<x for x in interdist)):
        print("Size of subareas is smaller than a matching distance. Taking twice the biggest.", file=bpar.SkZp_Par['stderr'])
        subsize=2*numpy.max(interdist)

    xmin,ymin=numpy.max( ((xMmin,yMmin),(xSmin,ySmin)), axis=0 )
    xmax,ymax=numpy.min( ((xMmax,yMmax),(xSmax,ySmax)), axis=0 )
    if(xmin>=xmax or ymin>=ymax  ): raise SkZpipeError(f"`master` and `slave` catalog don't overlap!", exclocus=_name_)
    #source near border can lose maching candidates, so expanding the subareas by 1 subsize all around
    if('0' in subarea): 
        xmin,ymin=subarea['0']
    else:
        xmin-=subsize
        ymin-=subsize
    subnx,subny=subarea.get('nxny', numpy.ceil(( (xmax-xmin)/subsize, (ymax-ymin)/subsize ))+1 )
    
    #SUBAREA is a (subnx,subny) 2D-space where each element is a list of object positions from slave.
    #For simplicity, it is handle as a 1D-structure concatenating each line
    #SUBAREA(I,J)=LIST(I+subnx*J)
    #SUBAREA contains the list of slave object
    indexing=(lambda x,y: ( mathfunct.freq_val2index(x, xmin, 0, subsize) , mathfunct.freq_val2index(y, ymin, 0, subsize) ) ) 
    deindexing=(lambda idx: ( idx%subnx , idx//subnx ) ) 

    subareaM=[None]*nmst #in which subarea is located a master source
    subareaS=[[]]*(subnx*subny)   #which slave sources a subarea contains
#    rejS=[]
    mtcS=[False]*nslv
    matched=[]
    for ii in range(nmst):
        xx,yy=indexing(coordmst[ii][0], coordmst[ii][1])
        if(0<=xx<subnx or 0<=yy<subny ):
            subareaM[ii]=x+subnx*y  #if None not in the intersaction master,slave

    for ii in range(nslv):
        xx,yy=indexing(coordslv[ii][0], coordslv[ii][1])
        if(0<=xx<subnx or 0<=yy<subny ):
            subarea[x+subnx*y].append(ii)
#        else: rejS.append(ii)

    #START
    clipT=tuple(clip)
    fstclip=1+1+1+1 #pos, rad_dst, x_dst, y_dst
    for mdst in iterdist:
        if(verb): print(f"Matching distance: {mdst:.3f}", file=bpar.SkZp_Par['stdout'])
        mdst2=mdst*mdst
        for ii in range(nmst):
            if(subareaM[ii] is None or subareaM[ii]<0): continue;
            #distance correction if coordinates are spherical or cartesian
            cproj=(3600.*math.cos(math.radians(master[ii].y)), 3600.) if(ctype=='sph') else (1,1)
            cndL=[]

           #getting list of slave source where look for candidates
            islvsrcL=[]
            ix,iy=deindexing(subareaM[ii])
           #for each master source will check its subarea and the 8 around
            for iiyy in range(iy-1, iy+2):
                if(iiyy<0 or iiyy>=subny): continue
                for iixx in range(ix-1, ix+2):
                    if(iixx<0 or iixx>=subny): continue
                    islvsrcL.extend(subarea[iixx+subnx*iiyy])
            for jj in islvsrcL:
                if(mtcS[jj]): continue #already a match
                Dx=(master[ii].x-slave[jj].x)*cproj[0]
                Dy=(master[ii].y-slave[jj].y)*cproj[1]
                if(Dx**2+Dy**2<mdst2):
                    #it should check also the data in `clip`
                    if(clip and justbest): #Clipping ONLY for beast match
                        cndD=[jj, math.sqrt(Dx**2+Dy**2), Dx, Dy] #candidate data: id slave, distance**2
                        for attr in clipT:  #to be sure the same sequence for all
                            val=clip[attr]
                            attrL=attr.split(':')
                            objM, objS=master[ii], slave[jj]
                            for attr in attrL:
                                if(not hasattr(objM, attr) ): 
                                    raise SkZpipeError(f"Master source {ii} has not attribute {'.'.join(attrL[:attrL.index(attr)+1])}", exclacus=_name_)
                                if(not hasattr(objS, attr) ): 
                                    raise SkZpipeError(f"Slave source {jj} has not attribute {'.'.join(attrL[:attrL.index(attr)+1])}", exclacus=_name_)
                                _objM, _objS=objM, objS
                                objM, objS=getattr(_objM,attr), getattr(_objS,attr)
                            if(isinstance(objM, float)): 
                                if(hasattr(_objM, 'e'+attr)):  objM=(objM,getattr(_objM,'e'+attr))
                                else:  objM=(objM,0.)
                            elif(isinstance(objM, (tuple,list))): 
                                if(len(objM)!=2): 
                                    raise SkZpipeError(f"In master source {ii} attribute {'.'.join(attrL[:attrL.index(attr)+1])} is not a float or a pair of float", exclacus=_name_)
                            else: raise SkZpipeError(f"In master source {ii} attribute {'.'.join(attrL[:attrL.index(attr)+1])} is not a float or a pair of float", exclacus=_name_)
                            if(isinstance(objS, float)):
                                if(hasattr(_objS, 'e'+attr)):  objS=(objS,getattr(_objS,'e'+attr))
                                else:  objS=(objS,0.)
                            elif(isinstance(objS, (tuple,list))):
                                if(len(objS)!=2): 
                                    raise SkZpipeError(f"In slave source {jj} attribute {'.'.join(attrL[:attrL.index(attr)+1])} is not a float or a pair of float", exclacus=_name_)
                            else: raise SkZpipeError(f"In slave source {jj} attribute {'.'.join(attrL[:attrL.index(attr)+1])} is not a float or a pair of float", exclacus=_name_)
                            ratio=mathfunct.clipping_ratio(datum1=objM,datum2=objS, clip=val, shift=0)
                            cndD.append(ratio)
                        #END CLIP
                        cndD.insert(fstclip, numpy.mean(cndD[fstclip:])) #putting as first clipping data the mean clip ratio
                        cndL.append(tuple(cndD))
                    else:
                        cndL.append((jj, math.sqrt(Dx**2+Dy**2)))

            if(cndL): #There is a possible match
                msrc=None
                #cndL is a list of (jj, Dx**2+Dy**2, Dx, Dy)+(clippping_ratios: mean, clip1, ...)
                if(len(cndL)>1 and justbest):
                    cndseL=[[]]*2   #(len(cndL[0])-(fstclip-1))  #list of list of tuple: to sort candidates for distance and clipping ratios
                    cndseL[0]=cndL.copy()
                    cndseL[0].sort(key=(lambda x:x[1])) #sorting by distance
                    cndseL[1]=cndL.copy()
                    cndseL[1].sort(key=(lambda x:x[fstclip])) #sorting by mean clip
                    if(cndseL[0][0][0]==cndseL[1][0][0]): #ID: nearest candidate is also best clip-ratio candidate
                        msrc=cndseL[0][0] #matching source pos
                    else:
                        ncnd=max((len(cndL)+1)>>1,2) #checking best half, but al least 2
                        for kk in range(1,ncnd):
                            if(cndseL[0][kk][0]==cndseL[1][0][0]): #kk-th candidate by dist is the best clip-ratio candidate
                                msrc=cndseL[1][0]
                                break
                else:
                    msrc=cndL[0] if(justbest) else  cndL  #justbest==False => cndL=[  (pos, rad_dst), ... ] 
                #setting as matched
                if(msrc):
                    if(justbest): #only case more than 1 iter
                        mtcS[msrc[0]]=True
                        subareaM[ii]=-1
                    matched.append( (ii, msrc) )
    #END
    return {'match':matched, 'm-rej':list( ii for ii in range(nmst) if(subareaM[ii] is None or subareaM[ii]>=0)), 's-rej':list(  ii for ii in range(nslv) if(not mtcS[ii])) }

