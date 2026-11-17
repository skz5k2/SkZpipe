"""Module with generic funtions
"""

import os, subprocess, sys, shutil, math, re, time
import datetime, glob, fileinput, tarfile, copy
import numpy, collections, pandas

from .exceptions import *
from .parameters  import basicpar as bpar
from .parameters  import database as _db
from .parameters  import options as _opt
from .parameters.classes  import fileclass
from . import fits
from . import mathfunct

##TEMPLATE for function (15 lines)
############
def TEMPXXYYZZ():
    """Template of function and its Description

Parameters
----------
    x : obj
        X

Returns
-------
    x
"""
    _name_='XXYYZZ'


###variable to manipulate internal input data storage (22)
# runlist=None, entrylist=None, dataframe=None, datatag=None, 
#    runlist : None, list
#        list of the entries to process. None for parameter 'runlist'
#    entrylist : None, list, str
#        Ordered list of the entries to choose from. None for parameter 'inputlist'. Or the name of the parameter: 'runlist' for parameter 'runlist', 'inputlist' for parameter 'inputlist'.
#    dataframe : None, dict
#        Dictionary of input data (dictionary of dictionaries). None for database defined in parameter 'inputdata'
#    datatag : None, list
#        List of the tags in input data. None for parameter 'datatag'
#
#  if(runlist is None): runlist=bpar.SkZp_Par['runlist'];
#  if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
#  if(isinstance(entrylist, str)):
#    if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
#    elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
#    else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name. <{}>".format(entrylist));
#  if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
#  if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
#  if(not isinstance(runlist, list)): raise TypeError(_name_+": `runlist` must be a list.  <{}>".format(runlist));
#  if(not isinstance(entrylist, list)): raise TypeError(_name_+": `entrylist` must be a list.  <{}>".format(entrylist));
#  if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": `dataframe` must be a dict. <{}>".format(dataframe));
#  if(not isinstance(datatag,   list)): raise TypeError(_name_+": `datatag` must be a list. <{}>".format(datatag));



######################
#==General Function==#
######################

from pydoc import pager
#def pager(text=''):
#  """Call system pager
#
#Parameters
#----------
#    text : str
#        Text to be visualized
#
#""";
#  _name_='pager';
#  try:
#      # args stolen fron git source, see `man less`
#      pager = subprocess.Popen(['less', '-F', '-R', '-S', '-X', '-K'], stdin=subprocess.PIPE, stdout=sys.stdout)
#      pager.stdin.write(bytes(text,'utf-8'))
#      pager.stdin.close()
#      pager.wait()
#  except KeyboardInterrupt:
#      # let less handle this, -K will exit cleanly
#      pass;
#  

############
#==Number=#
############
def isinteger(x=None):
    """Check it 'x' can be converted in an integer

Parameters
----------
    x : 
        Object that will be tested for integer conversion.

Returns
-------
    True/False
""";
    try:
        int(x);
        return True;
#  except ValueError, TypeError:
    except:
        return False;

###############
def getfloat(x=None, x0=None):
    """Return a float conversion of 'x' or return 'x0' if there is an error. 
    It can used to test if the object is a number.

Parameters
----------
    x : 
        Object to be converted in float.
    x0 : 
        Return value if an error occurs (default None).

Returns
-------
    the float conversion or 'x0'
""";
    try:
        return float(x);
    except (ValueError,TypeError):
        return x0;

###############
def extractint(txt='', upto=None):
    """Return the first integer present in a string up to a certain string. First, all no-[0-9] characters are replaced with spaces; 
    then it is split and  the first sequence is converted to an integer.

Parameters
----------
    txt : str
        String from which the integer is extracted
    upto : str
        String that end the search

Returns
-------
    An integer or None
""";
    ret=re.sub('[^0-9]', ' ', txt.split(upto)[0]).split()
    if(ret): return int(ret[0])

############
def extract_fieldlen(txt='', names=None):
    """Extract from a formatted stringf the length of the fields (e.g. "{x:10.3f} {y:8.2f}" -> (10, 8) ).

Parameters
----------
    txt : str
        String with format to be measured
    names : list or tuple
        List of the variable names in the format
Returns
-------
    ret :2 tuples of int
        A tuple with the length of the fields in the formatted string and a tuple with the length of the intra-field parts.
"""
    _name_='extract_fieldlen'
    fln,dln=[],[]
    if(names):
        for nm in names:
            fln.append( abs(extractint( txt[txt.find(nm):],'}' ) ) )
    else:
        for xt in re.findall('{.+?}', txt):
            if(':'in xt): fln.append(extractint(xt[xt.find(':'):]))
            else: fln.append(extractint(xt))
    dln=tuple( len(xd) for xd in re.split('{.+?}', txt) )
        
    return tuple(fln),dln

############
def len_formatted(txt='', names=None):
    """Calculate the length of a formatted string (e.g. "{x:10.3f} {y:8.2f}").

Parameters
----------
    txt : str
        String with format to be measured
    names : list or tuple
        List of the variable names in the format
Returns
-------
    len : int
        Length of the produced string.
"""
    _name_='len_formatted'
    
    fln,dln=extract_fieldlen(txt, names)
        
    return sum(fln+dln)


############
#=Sequence=#
############
def itemfreq(line=''):
    """Calculated the frequencies of each element in an iterable objecti (not a generator) with count method

Parameters
----------
    line : iterable object with count method
        Object (not a generator) to be analyzed

Returns
-------
    freq : dict
        Dictionary with the occurrences for each element
""";
    _name_='itemfreq';
    if(not hasattr(line, 'count')): raise TypeError(f"{_name_}: `line` must have 'count' method <{line.__class__}>")
    freq={}
  #setdefault and set(line) have the same (if in:skip; else add), but with the second you use count once per element
    for x in set(line): #
        freq[x]= line.count(x)
#        freq.setdefault(x, line.count(x))
    return freq

###############
def findallpos(elem='', line=''):
    """Find all the position of an element in an iterable object with count and index method (collections.abc.Sequence)

Parameters
----------
    elem : element of `line`
        Element of `line` of which to find all the occurrences
        If `elem` is a str object and `line` is a bytes object, `elem` will be encoded using 'utf-8'.
    line : iterable object with count and index method (collections.abc.Sequence)
        Object to be analyzed.
        If `line` is a str onject and `elem` is a bytes object, `line` will be encoded using 'utf-8'.

Returns
-------
    out : tuple
        Tuple with the positions of the occurrences of the element
""";
    _name_='findallpos';
    if(not hasattr(line, 'count') or not hasattr(line, 'index')): raise TypeError(f"{_name_}: `line` must have 'count' and 'index' method <{line.__class__}>")
    try:
        length=len(elem)
    except:
        length=1
    if(isinstance(elem,bytes) and isinstance(line,str)):
        line=bytes(line, encoding='utf-8')
    elif(isinstance(line,bytes) and isinstance(elem,str)):
        elem=bytes(elem, encoding='utf-8')
    occ=line.count(elem)
    out=[-length]
    for ii in range(occ):
                  #starting     starting point 
                  #point pos    from where to look for
        out.append(out[-1]+length+   line[out[-1]+length:].index(elem))
    return tuple(out[1:])
####
def intervalpos(pos):
    """Tranform a list of position in a list of intervals of positions, grouping contigous ones.
    For example: (1,2,3,6,7,9) => [(1,3), (6,7), (9,9)]

Parameters
----------
    pos : list, iterable
        Sequence of positions

Return
------
    ret : list of tuple
    List of intervals of positions.
"""
    pos=sorted(pos)
    outL=[]
    ii=1
    pos0=pos[0]
    while(ii<len(pos)):
        if(pos[ii]!=pos[ii-1]+1):
            outL.append((pos0, pos[ii-1]))
            pos0=pos[ii]
        ii+=1
    outL.append((pos0, pos[ii-1]))
    return outL
####
def not_intervalpos(interval, length):
    """Calculate the complement of a list of intervals of positions, considering the length of the original sequence.
    
Parameters
----------
interval : sequence of taples (of 2 intengers)
    Sequence of interval of positions (expressed as tuple of no-negative integers)
length : int
    Positive integer giving the size of the original sequence. 
    The maximum position is length-1
Return
------
complement : sequence of tuples
    Complement of a list of intervals of positions

"""
    outL=[]
    if(interval[0][0]>0): outL.append((0,interval[0][0]))
    for ii in range(len(interval)-1):
        outL.append((interval[ii][1]+1,interval[ii+1][0]-1))
    if(interval[-1][1]<length-1): outL.append((interval[-1][1]+1,length-1))
    return outL
####
def intervalcompat(first=None, second=None, length=None, excludeborders=True):
    """Check if the two sequence of intervals (of posotions) are overlapping: each interval in a sequence overlaps with one in the others.

Parameters
----------
first,second: sequence of tuples (of 2 int)
    Sequence of intervals expressed as a tuple of 2 integers (greater or equals to zero).
    THe minimum position is always 0
length : int
    Positive integer giving the size of the original sequence. 
    The maximum position is length-1
excludeborders : bool
    If intervals including borders (0 and length-1) will be included in the comparision

"""
    ifst=0
    isnd=0
    efst=len(first)
    esnd=len(second)
    if(excludeborders):
        if(0 in first[0]): ifst=1
        if(0 in second[0]): isnd=1
#        if(abs((len(fisrt)-ifst)-(len(second)-isnd))>1): return False

        if(length-1 in first[-1]): efst-=1
        if(length-1 in second[-1]): esnd-=1

    if(efst-ifst != esnd-isnd ): return False
    for ii in range(efst-ifst):
        chk=set(range(first[ifst+ii][0], first[ifst+ii][1]+1)) & set(range(second[isnd+ii][0], second[isnd+ii][1]+1))
        if(not chk): return False

    return True


#########################
#= Filename Management =#
#########################

def pathsplit(fname=None):
  """Separate the full path of a file in dirname,basename.

Parameters
----------
    fname : str
        Filename with path

Returns
-------
    out : tuple of str
        (dirname, basename)
""";
  _name_='pathsplit';
  if(not isinstance(fname,str)): raise TypeError(_name_+": fname must be a string");
  return (os.path.dirname(fname), os.path.basename(fname));

############
def remove_extension(fname=None, extlist=[]):
    """Remove the filename extension (reading from left to right, the last part after the last dot). It is possible to provide a list of possible choices.

Parameters
----------
    fname : str
        Filename
    extlist : list of str
        List of strings of suffix (starting with dot)

Returns
-------
    
"""
    _name_='remove_extension'

    import pathlib
    pathfn=pathlib.Path(fname)
    if(extlist):
        if(not isinstance(extlist, (list,tuple)) or any(not isinstance(x, str) for x in extlist)): raise TypeError(f"{_name_}: `extlist` must be a list empty or a list of str")
        if(pathfn.suffix in extlist):
            return pathfn.stem
    else:
        return pathfn.stem


#####################
#=Script Management=#
#####################
def startime(mesg='', verb=True):
    """Return the current time in seconds. 

Parameters
----------
    mesg : str
        Text to be print after the date.
    verb : bool
        Flag to print time and date.

Returns
-------
    Time in second (time.time())
"""
    _name_='startime'
    if(mesg): mesg+='\n'
    now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if(verb): print(f"{sys.argv[0]}\n{now}\n{mesg}", file=bpar.SkZp_Par['stdout'])
    stime=time.time()
    bpar.SkZp_Par['starttime']=stime
    return stime

###############
def endtime(starttime=None, verb=True, error=True, tformat='s', ndigit=1):
    """Return the time difference between now and a given time (in seconds). It can print the current date and time and the difference.

Parameters
----------
    starttime : int, float
        Time in seconds (from time.time() or datetime.datetime.now())
    verb : bool
        Flag to print (execution time, error and date).
    error : bool
        Flag to print how many error where capture and where.
    tformat : str
        Format of the execution time: 's' for seconds, 'm' for minutes, 'h' for hours.
    ndigit : int
        precision of the output (used by round()). Default 1.

Returns
-------
    The difference between now and starttime 
"""
    _name_='endtime'
    nowtime=time.time();
    runtime=None;
    if(tformat=='s'): tformat=1.;
    elif(tformat=='m'): tformat=60.;
    elif(tformat=='h'): tformat=3600.;
    else: raise ValueError(_name_+": Wrong value for 'tformat' [{}]. it must be 's', 'm', or 'h'.".format(tformat));
    if(not isinstance(starttime,(int,float))): starttime=bpar.SkZp_Par['starttime']
    runtime=int(round(nowtime-starttime, 0));
    if(verb): print(round(runtime/tformat,ndigit), file=bpar.SkZp_Par['stdout']);
    if(verb):
        if(error): print("\nError count:", len(bpar.SkZp_Par['errorlist']), bpar.SkZp_Par['errorlist'], file=bpar.SkZp_Par['stdout']);
        print("{:}\n{:}\n".format(sys.argv[0], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), file=bpar.SkZp_Par['stdout']);
    return runtime;

###############
def seterrorlist():
  """Backup old error list and clear it.
""";
  _name_='seterrorlist';
  if(bpar.SkZp_Par['errorlist']):
    bpar.SkZp_Par['errorhistory'][datetime.datetime.now().strftime('%Y%m%d_%H%M%S')]=bpar.SkZp_Par['errorlist'].copy(); 

  bpar.SkZp_Par['errorlist'].clear();

###############
def scriptdefine(auto=True):
  """Analize the name of the script (sys.argv[0]) and split it in path and scriptname, and the type of the name (the part after '_'). It should be run at the beginning of every script.

Parameters
----------
    auto : bool
        To set automatically the 'script' global parameter with its output

Returns
-------
    Tuple of str: scriptpath, scriptname, mode, scriptsubtype
    scriptpath : the directory where the script is located
    scriptname : the name of the script
    mode       : how the script is run: 'alone', 'ishell'
    scriptsubtype  : the subtype defined as the suffix joined with an underscore '_' (for ex. Refine for DpAls4psf_Refine)
""";
  (pathscript, scriptname, mode, scriptsubtype)=(None,)*4;
  if(sys.argv[0]!=''):
    (pathscript, scriptname)=pathsplit(sys.argv[0]);
    scriptname=re.sub(r'\.py$','',scriptname)
    scriptsubtype=scriptname.split('_')[-1];
  else: scriptname=''
  if(not scriptname or 'ipykernel' in scriptname): mode='ishell'
  elif(__name__=='__main__'): mode='ishell'
  else: mode='alone'
  if(auto): 
      bpar.SkZp_Par['script'].update({'pathscript':pathscript, 'scriptname':scriptname, 'mode':mode, 'scriptsubtype':scriptsubtype});
  return (pathscript, scriptname, scriptsubtype);

############
def WaitStop(names=[''], suff=''):
  """Check for signal to stop (temporarly or defenitely) the execution. The presence of a WAIT or *.WAIT file will pause the executio, while the presence of a STOP or *.STOP file will stop the execution. 

Parameters
----------
    names : list, str
       List of basenames for the .WAIT and .STOP
    suff : str
        Suffix for the '.WAIT' extension.
Returns
-------
    Time spent during the process.
""";
  _name_='WaitStop';
  initime=time.time();
  if(isinstance(names,str)): names=[names];
  if(not isinstance(names,list)): raise TypeError(_name_+": Wrong type for 'names'. It must be a list of str or a str.");
  if(any(not isinstance(name,str) for name in names) ): raise TypeError(_name_+": Wrong type for 'names'. It must be a list of str or a str. < {names} >".format(names=names));
  if(not isinstance(suff,str)): raise TypeError(_name_+": Wrong type for 'suff'. It must be a str.");
  for name in ['']+names:
    try:
      while(os.path.exists("WAIT"+suff) or os.path.exists(name+".WAIT"+suff)):
        time.sleep(10);
    except  KeyboardInterrupt :
      pass;
  for name in ['']+names:
    if(os.path.exists("STOP") or os.path.exists(name+".STOP")):
      print('\n'+FramedText("Obbedisco", excl=True), file=bpar.SkZp_Par['stdout']);
      print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file=bpar.SkZp_Par['stdout']);
      sys.exit(-1);
  return round(time.time()-initime, 1);


##########
#= LOCK =#
##########
def LockRun(runfile=None):
  """Create a lock file

Parameters
----------
    runfile : str
        Basename to use for the lock file, adding the suffix set in option 'locking:ext'.

Returns
-------
    True if the file is create, False/None otherwise.
""";
  if(runfile is None or runfile==''): return False;
  lockfile=runfile+_opt.OptionGet('locking:ext',otype='S')
  if(os.path.exists(lockfile)):
    raise SkZpipeError("it seems that there is already a SkZpipe running for the file!", exclocus=runfile);
  with open(lockfile, "w") as f_tmp:
    f_tmp.write("1");
    return True;
    

###
def UnLockRun(lock=False, runfile=None):
  """Remove the lock file

Parameters
----------
    lock : bool
        Flag for the lock status
    runfile : str
        Basename to use for the lock file, adding the extension set in option 'locking:ext'.

Returns
-------
    True if nothing has to be done, False if the lock file is removed.
""";
  if(not lock or runfile is None or runfile==''): return True;
  lockfile=runfile+_opt.OptionGet('locking:ext',otype='S')
  clean_file([lockfile]);  ### MULTISTEP
  return False;

###
def LockRunCheck(entrylist=None, verb=False):
  """Create a lock file

Parameters
----------
    entrylist : list of str, None
        List of basenames to check for active lock files, adding the suffix set in option 'locking:ext'.
    verb : bool
        If to print to stdout the list.

Returns
-------
    output : list of str
        List of basenames with active lock files.
""";
  if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
  lockL=[entry for entry in entrylist if(os.path.exists(entry+_opt.OptionGet('locking:ext',otype='S')))];
  if(lockL):
    if(verb or _opt.OptionGet('debug')): print("These entries has an active lock file", lockL, file=bpar.SkZp_Par['stdout'], flush=True);
  return lockL;
  
##lock

###################
#=File Management=#
###################

def backupfile(fname=None, keep=False):
    """Create a back-up of a file. The backup file name has the modification time appended to the end.

Parameters
----------
    fname : str
        Name of the file to backup
    keep : bool
        Flag to create a backup or change the name of the exixting file.

Returns
-------
    Integer: 0 for succeed, -1 for failing
"""
    if(isinstance(fname,str) and os.path.exists(fname)):
        if(re.search(r'\.(html?|txt|dat|csv)$', fname) ): #or re.search('\..{3,4}$',fname)):
            sname=fname.rsplit('.',1)
            nname=sname[0]+datetime.datetime.fromtimestamp(os.stat(fname).st_mtime).strftime('-%Y%m%d_%H%M%S')+'.'+sname[1]
        else:
            nname=fname+datetime.datetime.fromtimestamp(os.stat(fname).st_mtime).strftime('-%Y%m%d_%H%M%S')
        if(keep):
            shutil.copy(fname, nname)
        else:
            shutil.move(fname, nname)
        return 0;
    return -1;

###############


def file_stat(fname='', opt=None):
    """Count newlines, bytes, spaces, minimum/maximum length of lines, ...

Parameters
----------
    fname : str
        Name of the file to analyze
    opt : str
        String with options: 
            'l' for newline count; 
            'c' for byte count; 
            's' for space count (it implies 'l' and 'c')

Returns
-------
    Number of newline or a tuple of the values:
        line count, bytes counts,  not-empty line count,
        minimum length, minimum legth not counting spaces, 
        maximum length, maximum legth not counting spaces, 
        mean length, mean legth not counting spaces, 
        if the last line does NOT terminate with newline
"""
    _name_='file_stat'
    if(opt is None): opt='l'
    elif('s' in opt): opt='lcs'
    nl=-1
    if(os.path.exists(fname)):
        with open(fname, 'rb') as f_in: #open for reading in binary mode
            nc, nl, nll,  minl, minll,   maxl, maxll,  meanl,meansp=0,0,0,  1e100,1e100,  0,0, 0,0
            lastb=b''
            buf=f_in.read(1<<20) #Read a buffer of 1MiB 
            while (buf):
                nl+=buf.count(b'\n') #count \n not lines!
                if('c' in opt):
                    nc+=len(buf)  #count #n bytes

                    if('s' in opt):
                        sbufL=(lastb+buf).split(b'\n') #add the previous last part; and split by '\n': the last element doesn't terminate with '\n'
                        lastb=sbufL.pop()  #takeaway the last part that not terminate with a \n

                        lenL=[len(x) for x in sbufL]
                        lenNSL=[len(re.sub(b'\\s',b'',x)) for x in sbufL]
                        nspaceL=[x-y for x,y in zip(lenL,lenNSL)]

                        minl,maxl = min([minl]+lenL), max([maxl]+lenL)
                        meanl+=sum(lenL)
                        meansp+=sum(nspaceL)
                        nll+=sum([ 1 if(x>0) else 0 for x in lenNSL ])
                        minll=min([minll]+[x for x in lenNSL if(x>0)])
                        maxll=max([maxll]+lenNSL)

                buf=f_in.read(1<<20) #Read next 1MiB

            if(lastb): #adding the last line not terminating with \n
                nl+=1
                if('s' in opt):
                    lenL,lenNSL=len(lastb), len(re.sub(b'\\s',b'',lastb))
                    nspaceL=lenL-lenNSL
                    minl,maxl = min(minl, lenL), max(maxl,lenL)
                    meanl+=lenL
                    meansp+=nspaceL
                    nll+=1 if(lenNSL>0) else 0 
                    if(lenNSL>0): minll=min(minll,lenNSL)
                    maxll=max(maxll,lenNSL)

            if('s' in opt):
                return (nl, nc,  nll,   minl, minll,  maxl, maxll,   meanl/nl, meansp/nl,   bool(lastb))
    return nl
    

###############
def get_num_lines(fname=None, newline=True):
    """Return the "number of lines" in a file: if `newline` is True, it returns the newline ('\\n') count; if False, the actual number of line

Parameters
----------
    fname : str
        Name of the file to process.
    newline : bool
        If to return the newline count, or to cosider last line not terminating with a newline ('\\n').

Returns
-------
    Number of lines in the file. -2 if invalid filename; -1 if it doesn't exist.
""";
    if(not fname): return -2;
    if(os.path.exists(fname)):
        try:
            bsize=os.statvfs(fname).f_bsize
        except:
            bsize=8<<10
        nl=0; lastb=b''
        with open(fname, 'rb') as f_in:
            buf=f_in.read(bsize)
            while (buf):
                nl+=buf.count(b'\n')
                lastb=buf.rpartition(b'\n')[-1]
                buf=f_in.read(bsize)
            if(not newline and lastb): nl+=1
        return nl;
    return -1;


def getchecksum(fname=None, method=None):
    """Return checksum of a file

Parameters
----------
    fname : str
        Filename
    method : str
        Name of the method (that has to be implemented by hashlib). Default 'sha1' (fastest).


Return
------
    return : bytes
        Checksum as bytes
"""
    _name_='getchecksum'
    try:
        bsize=os.statvfs(fname).f_bsize
    except:
        bsize=8192
    if(not isinstance(method,str)): method='sha1'
    elif(method not in hashlib.algorithms_available):
        raise ValueError(f"{_name_}: Wrong value for `mathod`. {method} is not available. {hashlib.algorithms_available}")
    with open(fname, "rb") as f:
        import hashlib
        file_hash = getattr(hashlib, method.lower())()
        chunk = f.read(bsize)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(bsize)

        return file_hash.digest()





###############
def check_file(files=[], minline=1, namemaxlen=None, raisexc=True):   #RAISE IOError SkZpipeErr
    """Check a file if it exists, has enough lines and its filename is not too long. If runs on an iterable, it stops at the first error.

Parameters
----------
    files : str or iterable of str
        List of filenames to check
    minline : int
        Minimum number of lines
    namemaxlen : int
        Maximum length of filenames
    raisexc : bool
        Flag to set if raise an exception or just return an error value.

Returns
-------
    ret : 0 or tuple of 2 int
        0 if all files exist.
        If the check fails:
          if `raisexc` is True, an exception is raised.
          Otherwise, a tuple with the filename and: 
            -255 if a filename is longer than the maximum namelength,
              -2 if None is passed as filename.
              -1 if a file doesn't exist
               n if a file has less lines than the minimum (n the number of lines).

""";
    _name_='check_file'
    if(not namemaxlen): namemaxlen=bpar.SkZp_Par['maxnamelength']
    if(isinstance(files, str)):  files=[files]
    elif(files is None): return (ifile, 1)
    try:
        for ifile in files:
            if(ifile is None): return (ifile, -2)
            size=get_num_lines(ifile)
            if(size<minline):
                if(raisexc):
                    raise OSError(f"!!!ERROR: file {ifile} has not enough lines or doesn't exist! (size:{size}; min:{minline})");
                else:
                      
                    return (ifile, size)
            if(namemaxlen is None): continue
            if(len(ifile)>namemaxlen):
                if(raisexc):
                    raise SkZpipeError(f"the filename {ifile} is too long! Maximum length is {maxlenm} characters.\n")
                else:
                    return (ifile,-255)
    except:
        print('>', ifile, '<')
        raise
        raise TypeError(_name_+": wrong arguments")
    return 0;


###############
def clean_file(files=None, suff=None):
  """Delete files if they exist.

Parameters
----------
    files : str or tuple of str   or  list of (str or tuple od str)
        The filename or a tuple with (basename, extension) of a list of these to delete if existing.
    suff : str, None
        If present, an existing file will be rename adding this suffix instead of be deleting.
Returns
-------
    None
""";
  _name_='clean_file';
  if(suff is not None and not isinstance(suff, str)): raise TypeError(_name_+": 'suff' must be a string or None <{}>".format(repr(suff)));
  if(not isinstance(files, list)): 
    if(isinstance(files, (str,tuple))): 
      files=[files];
    else: raise TypeError(_name_+": 'files' must be a (list of) str or tuple of str <{}>".format(repr(files)));
  for ofile in files:
    if(isinstance(ofile, tuple)):
      if(all( isinstance(x, str) for x in ofile)): ofile=ofile[0]+ofile[1];
      #elif(not isinstance(ofile[0], str)): raise TypeError(_name_+": 'files' must be a (list of) str or tuple of str <{}>".format(repr(ofile)));
      else: raise TypeError(_name_+": 'files' must be a (list of) str or tuple of 2 str <{}> <{}>".format(repr(ofile), repr(files)));
      
    if(os.path.exists(ofile)):
      if(suff):
        shutil.move(ofile, ofile+suff);
      else:
#        if(ofile.endswith('.als') or ofile.endswith('.psf')): print("!!!!>", files, suff, "<!!!") #@@@@@
        os.unlink(ofile);


#########################
def purgefile(fname=None, nhdr=0, text=None, outfile=None):
    """Purge a file from lines with a specified text.

Parameters
----------
    fname : str
        Filename
    nhdr : int
        The number of initial lines to skip. If the number is negative, the lines will not be 
        included in the output file.

Returns
-------
    x
""";
    _name_='purgefile';
    check_file(fname);
    if(outfile is None): outfile=fname+"-P"; 
    if(not isinstance(nhdr, int)): raise TypeError(_name_+": nhdr must be a integer.");
    if(not text): raise ValueError(_name_+": text is not defined or empty.");
    with open(fname) as fin, open(outfile, 'w') as fout:
        for ii in range(abs(nhdr)):
            line=fin.readline();
            if(nhdr>0): fout.write(line);
        nl, nr=0,0;
        for line in fin:
            if(text not in line):
                fout.write(line);
                nl+=1;
            else:
                nr+=1;
        return (nl, nr);


#############
def FileCharacterize(fname=None, delimiter=None):
    """Extract characteristic of the structure of a file

Parameters
----------
    fname : str
        Filename

Returns
-------
    Characterization

Functions
---------
    findallpos
    itemfreq
    intervalpos
""";
    _name_='FileCharacterize';
    if(not isinstance(fname,str) or not os.path.exists(fname)): raise SkZpipeError(f"`fname` must be the name of an existing file.   <{fname}>", exclocus=_name_)
    fsize=os.stat(fname).st_size; numlines= get_num_lines(fname)
    if(fsize==0 or numlines==0): return
    print('>>>', _name_, fname, ':', fsize>>20, numlines, int(fsize/numlines), file=bpar.SkZp_Par['stdout']) #@@@@
    sepchar='|,;\t '
    intradigchar='.eE'
    print(sepchar,'\n', intradigchar, file=bpar.SkZp_Par['stdout'])
 ##%%%%%##
 ##%%%%%##

    with open(fname) as fin:
        starting={}
        cstart0,cstart1='',''
        cstartL=[]
        alphaperc=[]

        print(f"Reading first 1MiB of lines", file=bpar.SkZp_Par['stdout'])
        linesL=fin.readlines(1<<20) #read untill 1 MiB
        nlbuf=len(linesL)
        print(f"Read first {nlbuf} lines", file=bpar.SkZp_Par['stdout'])
        nl=min(100,numlines)
        print(f"Analyzing first {nl} lines for headers", file=bpar.SkZp_Par['stdout'])
        for ii in range(nl):
            line=linesL[ii]
            itfreq=itemfreq(line)
            noalnum=sorted([x for x in itfreq if(not x.isalnum() and x not in '-+_')])
            alpha=sorted([x for x in itfreq if(x.isalpha() or x in '_')])

            if(line.lstrip()[0:1]): #an empty line will result in an empty string, so skipped
                cstart=line.lstrip()[0:1]
                if(cstart.isdecimal()): break
                cstart1+=cstart
                cstart0+=line[0:1]
                cstartL.append(cstart1[-1] in cstart1[:-1])
                alphaperc.append(int(100*sum(itfreq[x] for x in alpha)/(len(line)-1)))

        starting0=itemfreq(cstart0)
        starting1=itemfreq(cstart1)
        chead=sorted([x for x in starting1 if(x.isalpha() or x in '#')])

        print('Starting char:',cstart1, file=bpar.SkZp_Par['stdout'])
        print('If starting no-space char is repeated:',  cstartL , file=bpar.SkZp_Par['stdout'])
        print('First char: ', starting0,'\nFirst no-space: ',starting1, '\nChar alphabetic or #: ', chead, file=bpar.SkZp_Par['stdout'])
        print("% of alphabetic char+'_'", alphaperc, file=bpar.SkZp_Par['stdout'])
        if('#' in cstart1):
            comrange=intervalpos(findallpos('#',cstart1))
            print(comrange, file=bpar.SkZp_Par['stdout'])
        print('================\n', f"Analyzing lines {ii}:{nl}...", file=bpar.SkZp_Par['stdout'])

        if(ii==nl-1): return
        nhdr,nhdr0=ii,ii
        rangespace={}
        charact={}
        spacepos={}
        inters={}
        for ii in range(nhdr0,nl):
            line=linesL[ii]
            itfreq=itemfreq(line)
            noalnum=sorted([x for x in itfreq if(not x.isalnum() and x not in '-+_')])
            alpha=sorted([x for x in itfreq if(x.isalpha() or x in '_')])
            charpos=dict((x, findallpos(x, line)) for x in noalnum)
            signpos=dict((x, findallpos(x, line)) for x in '-+')
            for x in noalnum:
                charact.setdefault(x,{'freq':{}, 'pos':{}})
                charact[x]['freq'].setdefault(itfreq[x],0)
                charact[x]['freq'][itfreq[x]]+=1
                charact[x]['pos'].setdefault(tuple(charpos[x]),0)
                charact[x]['pos'][tuple(charpos[x])]+=1
                if(x.isspace()):
                    spacepos.setdefault(x,set())
                    spacepos[x]|=set(charpos[x])
                    rangespace.setdefault(x,[])
                    rangespace[x].append(intervalpos(charpos[x]))

                    inters.setdefault(x,set())
                    if(inters[x]): #for initialization 
                            #avoiding empty lines or line without the char
                            if(intervalcompat(first=intervalpos(charpos[x]), second=intervalpos(sorted(inters[x])), length=len(line), excludeborders=True)): 
                                inters[x]&=set(charpos[x])
                            else: 
                                print(f"positions of char '{x}' not compatible with anteriors: resetting at ",ii, file=bpar.SkZp_Par['stdout'])
                                nhdr=ii
                                inters[x]=set(charpos[x])
                    else: inters[x]=set(charpos[x])
                    #print(repr(x), inters[x])
            for x in signpos:
                charact.setdefault(x,{'freq':{}, 'pos':{}})
                charact[x]['pos'].setdefault(tuple(signpos[x]),0)
                charact[x]['pos'][tuple(signpos[x])]+=1
            if('\t' in noalnum): spacepos|=set(charpos['\t'])
            #END

    print('================\nUsed space char are:', sorted(spacepos), file=bpar.SkZp_Par['stdout'])
    print('\nChar analysis:\n--------------', file=bpar.SkZp_Par['stdout'])
    print('New line', repr('\n'), file=bpar.SkZp_Par['stdout'])
    char='\n'
    des=charact[char]
    print('Different line length ', len(des['pos']) , file=bpar.SkZp_Par['stdout'])
    tmpl=sorted(inters[char])
    print('Same length for all >=> ', tmpl, file=bpar.SkZp_Par['stdout'])
    if(len(des['pos'])>1):
        for pos,freq in des['pos'].items():
            print(f" {freq} lines have length {pos}", file=bpar.SkZp_Par['stdout'])
    print('================\n', file=bpar.SkZp_Par['stdout'])
    for char in sepchar:
        print('Separating character:', repr(char), file=bpar.SkZp_Par['stdout'])
        if(char not in charact): print("\tNo present!", file=bpar.SkZp_Par['stdout'])
        else:
            des=charact[char]
            print('Different set of positions: ', len(des['pos']) , file=bpar.SkZp_Par['stdout'])
            if(char.isspace()): # and len(des['pos'])>1): #Only for space it make sense a analysis of position ("visually nice")
                tmpl=sorted(inters[char])
                print(f'{len(tmpl)} common to all >=> ', tmpl, '\n=>',intervalpos(tmpl), file=bpar.SkZp_Par['stdout'])
                if(inters[char] and len(des['pos'])< 10):
                    for pos,freq in des['pos'].items():
                        print(f'  it appears {len(pos):4d} times in {freq:4d} lines', file=bpar.SkZp_Par['stdout'])
                        tmpl=sorted(set(pos)-inters[char])
                        print(f"   with {len(tmpl)} not common positions {tmpl}", file=bpar.SkZp_Par['stdout'])
                        if(len(pos)==itfreq.get(char)): print('Same as last line', file=bpar.SkZp_Par['stdout'] )
            else:
                print('Frequency of frequency:', file=bpar.SkZp_Par['stdout'])
                for freq, ffreq in des['freq'].items():
                    print(f'    it appears {freq:4d} times in {ffreq:4d} lines', file=bpar.SkZp_Par['stdout'])
                    if(freq==itfreq.get(char)): print('Same as last line', file=bpar.SkZp_Par['stdout']) 
            print('================\n', file=bpar.SkZp_Par['stdout'])


    for char,des in charact.items():
        if(char in sepchar+'\n'): continue
        print('Character:', repr(char), file=bpar.SkZp_Par['stdout'])
        print('Frequency of frequency:', file=bpar.SkZp_Par['stdout'])
        for freq, ffreq in des['freq'].items():
            print(f'    it appears {freq:4d} times in {ffreq:4d} lines', file=bpar.SkZp_Par['stdout'])
            print('Same as last line:', freq==itfreq.get(char), file=bpar.SkZp_Par['stdout'])

        print('Different set of positions: ', len(des['pos']) , file=bpar.SkZp_Par['stdout'])
        if(char.isspace()): # and len(des['pos'])>1): #Only for space it make sense a analysis of position ("visually nice")
            tmpl=sorted(inters[char])
            print('Common to all >=> ', tmpl, '\n=>',intervalpos(tmpl), file=bpar.SkZp_Par['stdout'])
            if(inters[char] and len(des['pos'])< 10):
                for pos,freq in des['pos'].items():
                    print(' Freq and not common',freq, sorted(set(pos)-inters[char]), file=bpar.SkZp_Par['stdout'])
        print('================\n', file=bpar.SkZp_Par['stdout'])


############
def FileGetType(fname=None, fstream=None):
    """Create a signature of the format of the file

Parameters
----------
    fname : str or None
        Name of the file
    fstream : IOStream
        Object that support read method.

Returns
-------
    out : tuple of str
        Tuple of file format: (Main, sub-type)
""";
    _name_='GetFileType';
    if(fname is None and fstream is None): raise ValueError(_name_+": 'fname' and 'fstream' cannot be both undefined.");
    if(fname is not None and isinstance(fname,str)): raise TypeError(_name_+": 'fname' must be a string.");
    mtype, stype='',''
    isFITS=fits.isfits(fname)
    if(isFITS['flag']&1):
        mtype='FITS'
        stype= 'mos' if(isFITS['flag']&2) else 'single'

        return (mtype, stype)
    if(fname): fstream=open(fname);

    line=fstream.read();
    if(len(line)<10): return None
    elif(line.strip() == "NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD"):
        if(fname): ext=fname.split('.')[-1];
        line=fstream.read();
        nl=int(line.split()[0]);
        for ii in range(3 if(nl==2)else 2): #read up to the first source (NL==2 start with an empty line)
            line=fstream.read();
        nfld=len(line.split()); # number of fields first line of a source
        if(nl == 2):
            if(nfld==4): return ("DAO","ap"); # AP single mag
            elif(nfld>4): return ("DAO","ap"); # AP multi mag
            else:  raise SkZpipeError("Unknown file type of DAO type (it seems AP but have less than 4 fields)", exclocus=_name_);
        elif(nl == 1):
            if(nfld==9): return ("DAO","als");
            elif(nfld==6): return ("DAO","coo");
      
        elif(nl == 3):
            if(ext=='lst'): return ("DAO","lst");
            elif(ext=='nst'): return ("DAO","nei");
            else:
                raise SkZpipeError("Unknown file type of DAO type", exclocus=_name_);
    elif(line.startswith(" '") and line[2:].find("' ")>0): 
        from match import DAOmchlinechk
        if(DAOmchlinechk(line)):
            if(all(DAOmchlinechk(line) for line in fstream)): return ("DAO","mch")
  ##
    if(fname): fstream.close();
#  return None


############
def tailfile(f=None, n=1):
  """Return the last 'n' lines of the file 'f'

Parameters
----------
    f : str or IOStream
        Name of the file or an object with method read and seek.
    n : int
        Number (not negative) of the lines to return

Returns
-------
    ret : list of str
        List of the last 'n' lines (with terminal newline). If n==0, then an empty list is return anyway. If the file is empty, return a list with empty lines.
""";
  _name_='tailfile';
  if(not isinstance(n,int)): raise TypeError(_name_+": 'n' must be an int");
  if(n<0): raise ValueError(_name_+": 'n' must be a not negative int");
  if(n==0): return [];
  if(not isinstance(f, (str,IOStream))): raise TypeError(_name_+": 'f' must be a str (filename) or a IOStream");
  if(isinstance(f, str)):
    if(not os.path.exists(f)): raise IOError(_name_+": file {f} does not exist".format(f=f));
    f=open(f, 'rb');
  BSIZE = 1024;
  f.seek(0, 2);
  posbyte = f.tell();
  missing = n;
  nread = 1;
  data='';
  ret=[];
  while(missing > 0 and posbyte > 0):
      if(posbyte - BSIZE > 0):
        f.seek(-nread*BSIZE, 2);
        data=f.read(BSIZE)+data;
      else:
        f.seek(0,0);
        data=f.read(posbyte)+data;
      nl=data.rfind(b'\n');
      if(nl>=0):
        ret[0:0]=data[nl+1]
      missing -= lines_found;
      posbyte -= BSIZE;
      nread+=1;
  return data;


############
def read_until(fobj, txt, line=''):
    """Read from the given file object until the line contains the string in 'txt' or at least one of the string in the list/tuple 'txt'

Parameters
----------
    fobj : file object
        File object from where to read.
    txt : str, list, tuple
        String to look for in the read lines or a list/tuple with the string to look for.
    line : str
        Inicial value for the read line

Returns
-------
    The line that match the given string. Or '' if the end-of-file is reached before.
""";
    if(not line): line=fobj.readline()
    if(not isinstance(txt, (tuple,list))): txt=[txt];
    while(line and not any(tt in line for tt in txt)):
        line=fobj.readline()
    return line;


##################
##################
def fixpathprogram(progr=None, pathdir=None):
    """Fix to the program name adding an existing pathdir, if it was not given with full path.

Parameters
----------
    progr : str
        Name of the program
    pathdir : str
        Alternative directory where the program is located. If not set, the value store in 'progr:path:dir' option will be used.

Returns
-------
    progr : str
        The program name.
""";
    _name_='fixpathprogram';
    if(not progr or not isinstance(progr, str)): raise TypeError(_name_+": `progr` must be a string");
    if(pathdir and not isinstance(pathdir, str)): raise TypeError(_name_+": `pathdir` must be a string or None");

    if(os.path.sep not in progr):
        if(not pathdir): pathdir=_opt.OptionGet('progr:path:dir');
        if(pathdir):  progr=pathdir+os.path.sep+progr;
    return progr;


########################
########################
def sortbyfilter(iterable=None, filtermap=None):
    """Sort the input iterable according wavelength of the matched filter

Parameters
----------
    iterable : iterable
        Iterable with the object to sort
    filtermap : list, dict
        Dictionary or list that provide for each object the filter (by key for dictionry, by position for list).
        If not provide, `iterable` will be used (as list).

Returns
-------
    output : list
        List with the sorted objects
""";
    _name_='sortbyfilter';
    if(not isinstance(filtermap, dict)):
        iterable=list(iterable);
        if(not filtermap): filtermap=iterable.copy();
        filtermap=dict(zip(iterable, filtermap));
    if(isinstance(filtermap, dict)):
        return sorted(iterable, key=(lambda x : _db.SkZp_DB['passbands'][None].index(filtermap[x]) ));
    else: raise TypeError(_name_+": `filtermap` must be a list/tuple or a dictionary <{}>".format(repr(filtermap)));


############
def lookup(txt=None, lookupseq=None, case=None):
    """Look up a string in a sequence of strings to find a corrispondence.
    (for example `txt` is the 'OBJECT' card value and `lookupseq` is a list of field names).

Algorithm
---------
    Firstly, it checks for the case, and eventually convert `txt` lower- or upper-case.
    1. if `txt` is an item of `lookupseq`
    2. if `txt` starts with an item  of `lookupseq` (and it returns the longest).
    2. if `txt` contains an item  of `lookupseq` (and it returns the longest).

Parameters
----------
    txt : sequence of str
        String to look for
    lookupseq : sequence of str
        Sequence of strings to use as look-up list.
    case : str
        If `lookupseq` contains only lower- o uppercase strings.
        None or '' for undefined/mixed.

Returns
-------
    matching item or None
"""
    _name_='lookup'
    if(not isinstance(txt, str)): raise TypeError(f"{_name_}: `txt` must be a str subclass.   <{txt.__class__}>")
    if(case): 
        if(isinstance(case,str)):
            case=case.lower()
            if(case not in ('lower', 'upper')): raise SkZpipeError(f"parameter `case` must be 'lower' or 'upper', or None/''.   <{case}>", exclocus=_name_)
        else: raise SkZpipeError(f"parameter `case` must be 'lower' or 'upper', or None/''.   <{case}>", exclocus=_name_)

    if(isinstance(lookupseq, str)): lookupseq=[lookupseq]
    #lookupseq=tuple(lookupseq)
    lookupseq=tuple(sorted(lookupseq))
    if(not all(isinstance(x) for x in lookupseq)): raise TypeError(f"{_name_}: `lookupseq` must be a sequence of  str objects.")

    if(not case):
        if(all(x.islower() for x in lookupseq)): case='lower'
        if(all(x.isupper() for x in lookupseq)): case='upper'

    if(txt in lookupseq): return txt
    ##%%%%%##
    def _look_up(txt,lookupseq):
        if(txt in lookupseq): return txt
        tmpl=[]
        # ##start with
        for item in lookupseq:
            if(txt[0]>item[0]): break
            if(txt.startswith(item)): tmpl.append(item)
        if(len(tmpl)==1):  return tmpl[0]
        else:
            return sorted(tmpl, key=len)[-1]
        #contain 
        for item in lookupseq:
            if(item in txt):  tmpl.append(item)
        if(len(tmpl)==1):  return tmpl[0]
        else:
            return sorted(tmpl, key=len)[-1]
        return
    ##%%%%%##
            
    if(case):
        txt=getattr(txt,case)()
        ret=_look_up(txt,lookupseq)
        if(ret): return ret
        else:
            txt2=re.sub('_', ' ', re.sub(r'\W',' ', txt))
            lookupseq2=tuple(re.sub('_', ' ', re.sub(r'\W',' ',x)) for x in lookupseq)
        ret=_look_up(txt,lookupseq)
        if(ret): return lookupseq[lookupseq2.index(ret)]

    else:
        ret=_look_up(txt,lookupseq)
        if(ret): return ret
        else:
            txt2=txt.lower()
            lookupseq2=tuple(x.lower() for x in lookupseq)
        ret=_look_up(txt2,lookupseq2)
        if(ret): return lookupseq[lookupseq2.index(ret)]
        else:
            txt2=re.sub('_', ' ', re.sub(r'\W',' ', txt2))
            lookupseq2=tuple(re.sub('_', ' ', re.sub(r'\W',' ',x)) for x in lookupseq2)
        ret=_look_up(txt2,lookupseq2)
        if(ret): return lookupseq[lookupseq2.index(ret)]

    return


############
#=  RAM   =#
############
def ProcedureRequiredMemory(procedure=None, argsize=None, ndigits=2):
    """Calculate the allocated memory required by a procedure.

Parameters
----------
    procedure : str
        Name of the procedure ('DAOallframe', 'stack', 'photo').
    argsize : dict
        Dictionary with the information about the size of the arguments of the procedure.
        Some keys:
            'images': list of filesize of the images in MiB
            'lists': list of filesize of the source lists in MiB
            'improvepos': mode to improve position during stack procedure
            'other':  an additional value
    ndigits : int
        Precision in decimal digits for the rounding

Returns
-------
   x : float
    Required memory by the procedure
""";
    _name_='ProcedureRequiredMemory';
    if(procedure is None ): return
    elif(procedure == 'photo'):
        totsize=sum(argsize['images'])*2+argsize['lists'];
    elif(procedure == 'DAOallframe'):
        totsize=sum(argsize['images'])*3+argsize['other'];
    elif(procedure == 'stack'):
        totimg=sum(argsize['images'])
        totlst=numpy.array(argsize['lists']).sum();
        nimg,nlst=len(argsize['images']), len(argsize['lists']);
        totimg*= 3 if(argsize['improvepos']=='allframe') else 1.5; #Allframe stores in memory 3 times the size of the images
        totsize=round(max(totimg, 2*totlst),2);
    else: raise ValueError(_name_+": Wrong value for 'procedure', not a recognized procedure.");
    return round(totsize, ndigits);

############
def ramdircreate():
    """Create the directory in RAM for the procedures

Parameters
----------
    x : obj
        X

Returns
-------
    out : int
        Exit code: 
            0 for succeed; 
            1 if it's not possible to run in memory; 
            2 if it is not possible to create the directory
"""
    _name_='ramdircreate'

    uidir=bpar.SkZp_Par['ramfolder'][0]+os.sep+str(bpar.SkZp_Par['ramfolder'][1]())
    baseramdir=bpar.SkZp_Par['ramfolder'][2]
    if(not os.path.exists(uidir)): 
        if(_opt.OptionGet('debug')): 
            print(f"{uidir} doesn't exists! Not going on RAM", file=bpar.SkZp_Par['stderr'], flush=True)
            return 1 #No directory in RAM to use, skip
    try:
        if(not os.path.exists(uidir+os.sep+baseramdir)): os.mkdir(uidir+os.sep+baseramdir)
    except:
        print(f"Cannot create {uidir+os.sep+baseramdir}! Not going on RAM", file=bpar.SkZp_Par['stderr'], flush=True)
        return 2
    return 0

####
def setrunonram(*, procedure=None, flag=None, needed=None):
    """Prepared everything to run a photometric procedure in a filesystem on RAM.
    It creates the subdirectory for the procedure (using tempfile.mkdtemp), 
    then it copies copy the needed files.

Parameters
----------
    procedure : str
        Name of the procedure used to create the sufdirectorya (=`prodedure`+'_rdir'+random) 
    flag : bool
        If to run the procedure on RAM. Default value from option 'speedingup:ramdisk'.
    needed : list or tuple
        List of files or extensions of files (starting with dot) that the procedure needs.

Return
------
    return : dict
        Dictionary containing the information:
            'rdir' : full path of the dictionary in RAM for the procedure
            'brdir' : name of the dictionary and name of the symbolic link in the original current working directory
            'oldcwd' :original current working directory

"""
    _name_='setrunonram'
    if(not procedure or not isinstance(procedure,str)): raise SkZpipeError(f"Parameter `procedure` is not defined or invalid.", exclocus=_name_)
    if(flag is None): flag=_opt.OptionGet('speedingup:ramdisk', otype='Flg')
    if(not flag): return {}  #NO, skip

    ### create the general directory
    if(ramdircreate()): return {}

    runonramD={}
    import tempfile
    baseramdir=bpar.SkZp_Par['ramfolder'][0] +os.sep+ str(bpar.SkZp_Par['ramfolder'][1]()) +os.sep+ bpar.SkZp_Par['ramfolder'][2]
    try:
        rdir=tempfile.mkdtemp(suffix=None, prefix=procedure+'_rdir', dir=baseramdir) #creation of sub directory
    except:
        if(_opt.OptionGet('debug')): 
            print(f"Cannot create in {baseramdir} the directory for the procedure {procedure+'_rdir'}  <{rdir}>! Not going on RAM", file=bpar.SkZp_Par['stderr'], flush=True)
        return {} #cannot create the subdirectory for the procedure
    brdir=os.path.basename(rdir)
    os.symlink(rdir, brdir)  #creation of symb link to sub directory
    runonramD['proc']=procedure
    runonramD['rdir']=rdir
    runonramD['brdir']=brdir
    runonramD['oldcwd']=os.getcwd()
    if(_opt.OptionGet('debug')): 
        print('Going on RAM =>', runonramD, needed, file=bpar.SkZp_Par['stdout'], flush=True) #THIS GOES TO GENERAL STDOUT, NOT OF THE PROCEDURE
    for fname in needed:
        if(isinstance(fname,str) and os.path.exists(fname)):
            shutil.copy(fname, rdir, follow_symlinks=False)
            trgt=fname
            while(os.path.islink(trgt)):
                trgt=os.readlink(trgt)
                if(os.path.exists(trgt)):
                    shutil.copy(trgt, rdir, follow_symlinks=False)
                else:
                    trgt=''

    if(_opt.OptionGet('debug')): 
        print('File copied in the procedure directory on RAM:', sorted(glob.glob(rdir+os.sep+'*')), file=bpar.SkZp_Par['stdout'], flush=True) #THIS GOES TO GENERAL STDOUT, NOT OF THE PROCEDURE

    os.chdir(brdir)
    return runonramD

####
def unsetrunonram(info=None):
    """Undo the environment used to run a procedure in a directory on RAM

Parameters
----------
    info : dict
        Dictionary containing the information:
            'rdir' : full path of the dictionary in RAM for the procedure
            'brdir' : name of the dictionary and name of the symbolic link in the original current working directory
            'oldcwd' :original current working directory


    """
    _name_='unsetrunonram'
    if(info):
        if(not isinstance(info, dict) or any(key not in info for key in ('rdir', 'brdir','oldcwd')) ):
            raise SkZpipeError(f"Parameter `info` is not a dictionary or has not the needed values ('rdir', 'brdir','oldcwd').   < {info} >", exclocus=_name_)
        if(os.getcwd() != info.get('rdir')): 
            raise SkZpipeError(f"{_name_}: the current working directory of procedure is the directory in RAM!!!  < {os.getcwd()} >< {info.get('rdir')} >", exclocus=_name_)
        fnL=sorted(glob.glob('*')) #NO HIDDEN FILES +glob.glob('.*') ????
        moved=[]
        for fn in fnL:
            if(not os.path.exists(info['oldcwd']+os.sep+fn) or getchecksum(fn) != getchecksum(info['oldcwd']+os.sep+fn)): #if the file not exists in oldcwd or is different
                if(os.path.exists(info['oldcwd']+os.sep+fn)): os.unlink(info['oldcwd']+os.sep+fn)
                shutil.move(fn, info['oldcwd'])  #there should not be directory! Only files or link with relative path
            else:
                if(_opt.OptionGet('debug')): 
                    print(f"File {fn} already exists and it is the same\n", file=bpar.SkZp_Par['stdout'], flush=True)
                os.unlink(fn)
            trgt=fn
            while(os.path.islink(trgt)):
                trgt=os.readlink(trgt)
                if(trgt not in fnL and trgt not in moved):
                    if(not os.path.exists(info['oldcwd']+os.sep+trgt) or getchecksum(trgt) != getchecksum(info['oldcwd']+os.sep+trgt)):
                        if(os.path.exists(info['oldcwd']+os.sep+trgt)): os.unlink(info['oldcwd']+os.sep+trgt)
                        shutil.move(trgt, info['oldcwd'])
                        moved.append(trgt)
        if(_opt.OptionGet('debug')): 
            print('\nFiles moved =>', fnL, '+', moved, file=bpar.SkZp_Par['stdout'], flush=True)
#            print([ os.path.exists(fn) for fn in fnL+moved ], file=bpar.SkZp_Par['stdout'], flush=True)
#            print([ (getchecksum(fn) == getchecksum(info['oldcwd']+os.sep+fn)) for fn in fnL+moved ], file=bpar.SkZp_Par['stdout'], flush=True)

        os.chdir(info['oldcwd'])
        try:
            os.rmdir(info['rdir'])
        except:
            print(f"{_name_}: Problems deleting temporary directory {info['rdir']}!", file=bpar.SkZp_Par['stderr']) #THIS GOES TO GENERAL STDERR, NOT OF THE PROCEDURE
        os.unlink(info['brdir'])


###############################
#=External Process Management=#
###############################
def proc_writeline(txt=None, proc=None, f_log=None):
    """Send a string to a program in execution through standard input and write it down in the log stream.

Parameters
----------
    txt : str
        Text to be sent
    proc : Popen obj
        Process generate by module subprocess
    f_log : stream
        Stream where to store log info (object with write method)

Returns
-------
    x
""";
    _name_='proc_writeline'
    if(txt is None or proc is None): return 1
    txt=str(txt)
    if(f_log): f_log.write('=> '+txt+'\n')
    proc.stdin.write(bytes(txt+'\n','utf-8'))
#  proc.stdin.write(txt+'\n')
    proc.stdin.flush()
    if(f_log): f_log.flush()
    return 0


#################
def tell_progr(progr, mess, f_Log=None):
    """Execute an external program passing command through stdandard input.

Parameters
----------
    progr : str
        Name of the program to execute
    mess : list
        List of input for the program to be passed through standard input
    f_Log : str
        Name of the stream to log output.

"""
    _name_='tell_progr'
    with subprocess.Popen(progr, shell=False, stdin=subprocess.PIPE, stdout=f_Log) as proc:
        for imes in mess:
            proc_writeline(imes, proc, f_Log)


###############
def get_output(cmd):
    """Return the outout of an external process using `subprocess` module

Parameters
----------
    cmd : list of str
        List with the commando and its arguments

Returns
-------
    output : str
        string utf-8 decoded of the standard output
"""
    _name_='get_output'
    if(cmd):
        proc=subprocess.run(cmd)
        if(proc.stderr): bpar.SkZp_Par['stderr'].write(proc.stderr.decode('utf-8'))
        return proc.stdout.decode('utf-8')
    else:
        return ''


#############
#############
def FramedText(txt='', excl=False):
    """Create a frame of # around a text.

Parameters
----------
    txt : str
        Text to frame
    excl : bool
        Flag to add 3 exclamation marks before and after

Returns
-------
    Framed text
"""
    _name_='FramedText';
    if(not isinstance(txt,str)): raise TypeError(_name_+": Wrong type for input. It muct be a str")
    if(excl): txt="!!! "+txt+" !!!"
    frmtxt="#"*(len(txt)+4) + "\n# " + txt + " #\n" + "#"*(len(txt)+4)
    return frmtxt


############
def SpeedUpTest():
    """Print a warning message if speed-up option is on.

Returns
-------
    Warning message.
"""
    _name_='SpeedUpTest';
    if( _opt.SkZp_Opt['I']['speedup']>0 ):
        print('\n'+FramedText("Speed-up activated: {:2d}".format(_opt.SkZp_Opt['I']['speedup']), excl=True)+'\n', file=bpar.SkZp_Par['stdout']);


############
def flush_out():
    """Flush standard output and error as defined internally in SkZp_Par['stdout'] and SkZp_Par['stderr'].

"""
    bpar.SkZp_Par['stdout'].flush()
    bpar.SkZp_Par['stderr'].flush()
  


########################
#=FileSystem and Space=#
########################
def fs_stat(path='./'):
    """Return info of the file system containing the privide path.

Parameters
----------
    minspace : str
        Path whose file system has to be analyzed. Default current working directory. 

Return
------
    free : float
        Amount of free space in MiB
    
""";
    _name_='fs_stat'
    if(os.path.exists(path)):
        #statvfs=os.statvfs(path)
        #avspace=(statvfs.f_bavail*statvfs.f_frsize)>>20;
        return {'avail': round(psutil.disk_usage(path).free/(1<<20),3)}

############
def check4space(minspace=None):
    """Check if there is enough free space available on the file system containing the current 
working directory. If not, it pause the execution with WaitStop function.

Parameters
----------
    minspace : int or float
        Minimum amount of MiB necesary.

    
"""
    _name_='check4space'
    if(minspace):
        #statvfs=os.statvfs('./');
        #avspace=(statvfs.f_bavail*statvfs.f_frsize)>>20;
        avspace=round(psutil.disk_usage(".").free/(1<<20),3)
        if(avspace<minspace):
            print(f"!!!ATTENTION: NOT ENOUGH FREE SPACE! ({avspace}<{minspace})\nDelete file WAIT after having freed enough memory\n", file=bpar.SkZp_Par['stdout']);
            with open("WAIT",'w') as f_tmp:
                f_tmp.write('');
            WaitStop();


######################################################

#########################
#=Instrument Management=#
#########################
##VIRCAM 
def VIRCAM_setstripeid(stripe=None):
    """Return the correct identificator (a-h) of the VIRCAM stripe

Parameters
----------
    stripe : str, int
        Identification of the "stripe" of a VIRCAM tile as a integer [1-8] or a letter [a-h,A-H]

Returns
-------
    Return the name of the stripe as a letter among a and h
""";
    _name_='VIRCAM_setstripeid';
    if(not isinstance(stripe,str) and not isinstance(stripe, int)): raise TypeError(_name_+": stripe must be a [a-h] character or a [1-8] integer");
    if(isinstance(stripe,str)):
        stripe=stripe.lower();
        if(not re.search('[a-h]',stripe)): raise ValueError(_name_+": stripe must be [a-h]");
    elif(stripe>8 or stripe<1): raise ValueError(_name_+": stripe must be between 1 and 8");
    else:
        stripe=chr(ord('a')+stripe-1);
    return stripe;
    

###
def VIRCAM_getstripeid(chip=None, offset=None):
    """Return the identificator of the stripe of the image in a VIRCAM tile

Parameters
----------
    chip : int
        Number of the chip

Returns
-------
    The letter [a-h] of the stripe
""";
    _name_='VIRCAM_getstripeid';
    return chr(((int(chip)-1)>>2)<<1+int((int(offset)-1)/3)+ord('a'))


###
def VIRCAM_getcenterpos(chip=None):
    """Return the apprimate (X,Y) position of the center of the given chip in a VIRCAM pawprint field of view

Parameters
----------
    chip : int
        Number of the chip (1-16)

Returns
-------
    Tuple of (X,Y) position of the center of 
"""
    return (22.0*(((chip-1)%4)-1.5), 20.3*(((chip-1)>>2)-1.5))
##vircam


########################
#=FITS Info Management=#
########################

###
def FitsHeaderInfoClean(value, spacerepl):
    """Covert the values of a card entry from a FITS header, read as string.

Parameters
----------
    value : str, float, integer
        Value of the header card
    spacerpl : str
        Group of characters that will replace spaces ' ' inside the card value.

Returns
-------
    The value converted in a number or the original value.
"""
    _name_="FitsHeaderInfoClean"
    if(not isinstance(value, str)): return value
    if(' / ' in value):    value=value.rpartition(' / ')[0]
    value=value.replace("'",'').strip().replace(' ', spacerepl)
  #Not string
    try:
        value= float(value) if('.' in value) else int(value)
    except ValueError:
        pass
    return value
  

###
def FitsHeaderInfoLineRead(line='', spacerepl=None):
    """Transform a line of a FITS header into a tuple.

Parameters
----------
    line : str
        Line from a FITS header containing the card.
    spacerepl : str
        String to replace internal spaces in the value of the card

Returns
-------
    out : tuple
        Tuple of two values: the card name and the value
""";
    _name_='FitsHeaderInfoLineRead';
    if(not isinstance(line, str)): raise TypeError(_name_+": 'line' must be a string");
    if(spacerepl is None): spacerepl=bpar.SkZp_Par['charconversion'][' '];
    if(not isinstance(spacerepl, str)): raise TypeError(_name_+": 'spacerepl' must be a string");
    line=line.strip();
    if(len(line)<3 or line[0]=='#' or not '=' in line): return ();
    tmpl=[s.strip() for s in line.split('=')];
    if(not tmpl[0] or not tmpl[1]): return ();
    tmpl[0]=re.sub('^HIERARCH','',tmpl[0]).strip();
    return ( tmpl[0], FitsHeaderInfoClean(tmpl[1], spacerepl) );


###
def FitsHeaderInfoRead(header=None, index=0, spacerepl=None):
    """Read the header of a image opening directly the image or using an existing header file.

Parameters
----------
    header : str, HDU
        Name of isource: the image or the text file where the header info were stored.
    index : int, str
        Number or name of the HDU from where read the header. -1 to retieve all the headers.
    spacerepl : str
        String to replace internal spaces in the value of the card

Returns
-------
    output: list
        A list of dictionaries with the header data, an entry for each HDU
"""
    _name_='FitsHeaderInfoRead'
    if(spacerepl is None): spacerepl=bpar.SkZp_Par['charconversion'][' '];
    if(not isinstance(spacerepl, str)): raise TypeError(f"{_name_}: 'spacerepl' must be a string <{spacerepl.__class__}>");
    hdrinfo={};
    if(not isinstance(index, (int,str))): raise TypeError(f"{_name_}: 'index' have to be an integer or string <{index.__class__}>");
  #  if(isinstance(index, int) and index<0): raise TypeError(_name_+": 'index' have to be a no-negative integer or string");
    hdrinfo=[];
    try:
        if(isinstance(header,str)):
            if(header.endswith(bpar.SkZp_Par['fitsextension']) or header.endswith(bpar.SkZp_Par['mosaicextension'])): #if image or mosaic
                if(isinstance(index,int)):
                    if(index<0): #-1 for ALL
                        with fits.pyfits.open(header) as hdul:
                            for hdu in hdul:
                                hdrinfo.append(dict(hdu.header));
                    else: hdrinfo.append(dict(fits.pyfits.getheader(header, ext=index)));
                else:
                    hdrinfo.append(dict( fits.pyfits.getheader(header, extname=index) ));
                for hdr in hdrinfo: #you can iterate because it contain object return by pointer, not value
                    for tag in hdr:
                        hdr[tag]=FitsHeaderInfoClean(hdr[tag], spacerepl);
            else: #text file 
                with open(header) as f_hdr:
                    hdrinfo.append({});
                    for line in f_hdr:
                        line=FitsHeaderInfoLineRead(line, spacerepl);
                        if(line):
                            hdrinfo[0][line[0]]=line[1];
        elif(isinstance(header, (fits.pyfits.PrimaryHDU,fits.pyfits.hdu.image.ImageHDU,fits.pyfits.hdu.base.ExtensionHDU))):
            hdrinfo.append(dict(header.header));
            for hdr in hdrinfo: #you can iterate because it containobject return by pointer, not value
                for tag in hdr:
                    hdr[tag]=FitsHeaderInfoClean(hdr[tag], spacerepl);
        else: raise TypeError(f"{_name_}: `header` must be the name of the file (FITS or txt file with header info) or a HDU <{header.__class__}>");
    except:
        raise;
  
    for key in ['', 'COMMENT']: #keys to be removed
        for hdr in hdrinfo:
            if(key in hdr): del(hdr[key]);  #it is a dict, so just 1 item for each key!!
  
    return hdrinfo;


######################################
#=Input and Internal Data Management=#
######################################
def splitconvert(data=None, delimiter=None,  converters=None, maxsplit=-1, appendinput=False, delim_repeat=False, conv_repeat=False):
    """Split the input `data` into parts according to `delimiter` and convert them according to `converters`.

Parameters
----------
    data : str, list, tuple
        Data to be processed. It can be any object that can use the [:] notation.
        str : It will be split with str.split (`delimiter` is None or str), or according to sizes in `delimiter`
    delimiter : None,str, sequence of int
        The string used to separate values, or sequence of integers as widths of the fields, or the common width of all the fields.
        str, None : pattern that separates the fields (e.g. ','). str.split method will be used.
        tuple of int : values of the sizes of the fields (e.g. (7,9,9,9,9) )
    converters : None, sequence of callables or None
        Sequence of items: a callable to convert a field to its value/object; None to leave unchanged the data.
    maxsplit : int
        If maxsplit is given, at most `maxsplit` splits are done. If negative (default), all the splits 
        are done. As for str.split
    appendinput : bool, int
        False, 0: just standard output
        True, >0: the last element of the tuple will be the whole initial input.
              <0: the last element of the tuple will be the initial input not converted.
    delim_repeat : bool
        If `delimiter` is a sequance of integer, the last will be used to extract the remaining fields.
    conv_repeat : bool
        If True, the last entry of `converters` will be used on all the remaining fields.

Returns
-------
    out : tuple
        Tuple of object. The number is limited by `maxsplit` (-1 for all, if not negative the tuple will include `maxsplit` objects).
""";
    _name_='splitconvert';
    if(not isinstance(maxsplit,int)): raise TypeError(_name_+": `maxsplit` must be an integer");
    if(not isinstance(appendinput,(bool,int))): raise TypeError(_name_+": `appendinput` must be a bool or integer");
    if(maxsplit==0): return ();
    unconverted=None
    if(isinstance(delimiter, int)): delimiter=(delimiter,)*int(len(data)/delimiter+1)

    #data=str ; delimiter for .split()
    if(isinstance(data,str) and (delimiter is None or isinstance(delimiter,str))):
        tmpL=data.split(delimiter, maxsplit=maxsplit);
        if(maxsplit<len(tmpL)): unconverted=tmpL[maxsplit]
        if(maxsplit>0): tmpL=tmpL[:maxsplit];
    elif(not isinstance(data,str) and isinstance(delimiter,str)): 
        raise SkZpipeError(f" `delimiter` cannot be a str if `data` is not.   <{delimiter}>", exclocus=_name_)
    #data= [:] ; delimiter=tuple
    elif(isinstance(data, (str,list,tuple) ) and isinstance(delimiter,(list,tuple))):
        tmpL=[];
        tmps=copy.copy(data);
        for pp in delimiter:
            if(pp>0):
                tmpL.append(tmps[:pp]);
                tmps=tmps[pp:];
            elif(pp==0):
                tmpL.append(tmps[:0]);
            else: 
                break;
            if(len(tmps)==0 or len(tmpL)==maxsplit): break
        if(delim_repeat and len(tmpL)!=maxsplit):
            while(len(tmps)):
                if(delimiter[-1]>0):
                    tmpL.append(tmps[:delimiter[-1]]);
                    tmps=tmps[delimiter[-1]:];
                elif(delimiter[-1]==0):
                    tmpL.append(tmps[:0]);
                else: 
                    break;
                if(len(tmps)==0 or len(tmpL)==maxsplit): break
        unconverted=tmps;
    elif(isinstance(data, tuple) and delimiter is None): tmpl=list(data)
    else:  raise SkZpipeError(f"Incompatible types for `data` and delimiter`.   <{data.__class_}>,<{delimiter.__class_}>", exclocus=_name_)
   ###
    if(converters):
        if(callable(converters)): converters=[converters]
        converters=list(converters)
        if(conv_repeat and len(tmpL)>len(converters)): converters+=converters[-1:]*(len(tmpL)-len(converters))
        for ii in range(min(len(converters), len(tmpL))):
            if(callable(converters[ii])): tmpL[ii]=converters[ii](tmpL[ii]);
   ###
    if(appendinput):
        tmpL.append( data if(int(appendinput)>0) else unconverted );

    return tuple(tmpL);


###############
def DictdataUpdate(olddict=None, newdict=None, override=False):
    """Update properly a dictionary with data from new one. It will update only if the item is new or if new value is not None. By default it updates only keys with value None.

Parameters
----------
    olddict : dict
        Dictionary to be updated
    newdict : dict
        Dictionary with the new values
    override : bool
        Flag to update also items with value not None

Returns
-------
    Tuple: number of new items, number of updatable items.
"""
    _name_='DictdataUpdate';
    if(not isinstance(olddict,dict)): raise TypeError(_name_+": 'olddict' must be a dict");
    if(not isinstance(newdict,dict)): raise TypeError(_name_+": 'newdict' must be a dict");
    if(not isinstance(override,bool)): raise TypeError(_name_+": 'override' must be a bool");
#    print(">>:>>", olddict.get('NAME'), olddict.get('DATE'),olddict.get('DATE').__class__, newdict.get('DATE'), newdict.get('DATE').__class__) #@@@@
#    print(">>:>>", olddict.get('NAME'), olddict.get('TIME'),olddict.get('TIME').__class__, newdict.get('TIME'), newdict.get('TIME').__class__) #@@@@
    #Update only if new value is not None
    newdata, updata={},{};
    for tag,val in newdict.items():
        if(tag in olddict):
            if(val is not None):  #Update only if the new value is defined (=! None)
                oldval=olddict[tag]
                if(oldval is None or oldval=='-'): newdata[tag]=val    #Store to update if the old value is not defined 
                elif(oldval==str(val)): newdata[tag]=val    #Store to update if the old value is string version of the new
                else: updata[tag]=val  #Otherwise, store the value as updatable
        else: newdata[tag]=val  #Store to update if not existing (like .setdefault)

    olddict.update(newdata)
    if(override):    olddict.update(updata);

    return (len(newdata), len(updata));
        
######################
def ResetInitialize(*,really=False, hard=False):
    """Reset some part of the initialization or all the parameters (keyword-only arguments).

Parameters
----------
    really : bool
        To confirm the reset. Default False to prevent accidental reset
    hard : bool
        For a hard reset. Default False to prevent accidental reset

Returns
-------
    Value and description (if present);
""";
    _name_='ResetInitialize';
    if(really):
        bpar.SkZp_Par['store4later']={'calib_coeff':{}, 'inputdata':()};
        bpar.SkZp_Par['inputfiles']=[]
        if(hard):
            bpar._hardreset_(hard)
            SkZp_Par['inputdata']={};
            SkZp_Par['inputlist']=[];
            SkZp_Par['runlist']=[];

            SkZp_Par['inputfiles']=[];
            SkZp_Par['errorlist']=[];    
            SkZp_Par['errorhistory']={}; 

            SkZp_Par['stdout']=sys.stdout
            SkZp_Par['stderr']=sys.stderr  
    else: 
        print(f"{_name_}: Aborting reset (really=True to really reset)", file=bpar.SkZp_Par['stdout']);
    return;


########################################################

############
def airmass(ha=None, dec=None, lat=None, method=None):
    """Calculate airmass using different method (Rapp-Arraras & Domingo-Santos, 2011)

Parameters
----------
    ha : float
        Hour angle of point in the celestial sphere
    dec : float
        Declination of point in the celestial sphere
    lat : float
        Latitude of the observer
    method : str
        Method to be used to calculate the airmass:
            'YI67': One parameter form of Young & Irvine (1967)
            'DR-1': One parameter form of De Mairan (1723) and Radau (1877)
            'HK76': One parameter form of Heindl & Koch (1976)
            'Ra-2': Two-Parameter Form of Rapp-Arraras
            'He-3': Three-Parameter Form of Herring (1992)
            'He-4': Four-Parameter Form of Herring (1992) (Ifadis & Savvaidis, 2001)
            'He-5': Five-Parameter Form of Herring (1992) (Rapp-Arraras & Domingo-Santos, 2011)
Returns
-------
    airmass : float
"""
    _name_='airmass'
    sinh=( math.sin(math.radians(lat))*math.sin(math.radians(dec)) + math.cos(math.radians(lat))*math.cos(math.radians(dec))*math.cos(math.radians(ha)) )
    if(method is None): method=_opt.OptionGet('inputdata:am:method', otype='S')
    if(method=='DR-1'):
        a1=bpar.SkZp_Par['airmasscoeff'][method][0]
        am=math.sqrt((a1*sinh)**2+2*a1+1)-a1*sinh
    elif(method=='YI67'):
        secz=1./sinh
        a1=bpar.SkZp_Par['airmasscoeff'][method][0]
        am=secz*(1-a1*(secz*secz-1))
    elif(method=='HK76'):
        a1=bpar.SkZp_Par['airmasscoeff'][method][0]
        am=(2+a1)/(sinh+math.sqrt(2*a1+sinh**2))
    elif(method=='Ra-2'):
        a1,a2=bpar.SkZp_Par['airmasscoeff'][method]
        am=1./(sinh+a1*(1-sinh)/(sinh+a2))
    elif(method=='He-3'):
        a1,a2,a3=bpar.SkZp_Par['airmasscoeff'][method]
        am=(1+a1/(1+a2/(1+a3))) / (sinh+a1/(sinh+a2/(sinh+a3)))
    elif(method=='He-4'):
        a1,a2,a3,a4=bpar.SkZp_Par['airmasscoeff'][method]
        am=(1+a1/(1+a2/(1+a3/(1+a4)))) / (sinh+a1/(sinh+a2/(sinh+a3/(sinh+a4))))
    elif(method=='He-5'):
        a1,a2,a3,a4,a5=bpar.SkZp_Par['airmasscoeff'][method]
        am=(1+a1/(1+a2/(1+a3/(1+a4/(1+a5))))) / (sinh+a1/(sinh+a2/(sinh+a3/(sinh+a4/(sinh+a5)))))
    else: raise ValueError('Airmass: wrong method name')

    return am

###
def InputDataSetAirMass(method=None, check=None, diff=None, force=False, entrylist=None, dataframe=None):
    """Calculate the airmass for each entry.

Parameters
----------
    check : int or None
        Three-way flag to check the existing value.
            0: no check
            -1: only check and raise a warning
            +1: check and eventually fix it
        If None, option 'inputdata:am:check' is used. Use option 'inputdata:am:diff'.
    diff : float or None
        Difference threshold to warn/fix:
            0: disable check
            >0: absolute difference  ( |AIRMASS-am| )
            <0: relative absolute difference ( |1-am/AIRMASS| )
        If None, option 'inputdata:am:diff' is used.
    force : bool
        Force the calculation even if there is a value.
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']

Returns
-------
    None
""";
    _name_='InputDataSetAirMass';
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name. <{}>".format(entrylist));
    if(not isinstance(dataframe,  (dict, pandas.DataFrame))): raise TypeError(_name_+": `dataframe` must be a dict or a pandas.DataFrame.   <{}>".format(dataframe.__class__))
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": `entrylist` must be a list. <{}>".format(entrylist))
    if(check is None): check=_opt.OptionGet('inputdata:am:check')
    if(diff is None): diff=_opt.OptionGet('inputdata:am:diff')

    if(diff==0): check=0
    from astropy.time import Time
    if(isinstance(dataframe, dict)):
        for img in entrylist:
            if(check or force or dataframe[img]['AIRMASS'] is None):
                if(dataframe[img]['RA'] is None or dataframe[img]['DEC'] is None or dataframe[img]['SITELAT'] is None  or dataframe[img]['SITELONG'] is None):
                    continue
                if(dataframe[img]['MJD'] is not None or (dataframe[img]['DATE'] is not None and dataframe[img]['TIME'] is not None) ):
                    lat=dataframe[img]['SITELAT'] ; plong=dataframe[img]['SITELONG']
                    ra=dataframe[img]['RA'] ; dec=dataframe[img]['DEC']
                    if(dataframe[img]['MJD'] is not None):
                        timed=Time(dataframe[img]['MJD'], format='mjd')
                    else:
                        timed=Time(dataframe[img]['DATE']+'T'+dataframe[img]['TIME'], format='isot', scale='utc')
                    sidt=timed.sidereal_time('mean', longitude=plong).degree
                    ha0=sidt-ra
                    expt=dataframe[img]['EXPTIME']; amL=[]
                    if(expt):
                        for dt,ww in ((0,1), (0.5*expt,4), (expt,1)):
                            ha=ha0+dt/240.
                            amL.append(ww*airmass(ha=ha, dec=dec, lat=lat, method=method))
                        am=round(sum(amL)/6 ,5)
                    else:
                        am=round(airmass(ha=ha0, dec=dec, lat=lat, method=method),5)

                    if(force or dataframe[img]['AIRMASS'] is None):
                        dataframe[img]['AIRMASS']=am
                    elif(dataframe[img]['AIRMASS']is not None and check):
                        if(diff<0):
                            if(abs(1-am/dataframe[img]['AIRMASS'])>abs(diff)): 
                                print(f"AIRMASS: image {img} has an airmass value that differ too much (>{abs(diff)}%) from the calculated.  <{dataframe[img]['AIRMASS']};{am}>",  file=bpar.SkZp_Par['stderr'])
                                if(check>0):  dataframe[img]['AIRMASS']=am
                        else:
                            if(abs(am-dataframe[img]['AIRMASS'])>diff): 
                                print(f"AIRMASS: image {img} has an airmass value that differ too much (>{diff}) from the calculated.  <{dataframe[img]['AIRMASS']};{am}>",  file=bpar.SkZp_Par['stderr'])
                                if(check>0):  dataframe[img]['AIRMASS']=am

    else:
        pass

###
def InputDataSetMJD(force=False, entrylist=None, dataframe=None):
    """Calculate the Modified Julian Date for each entry.

Parameters
----------
    force : bool
        Force the calculation even if there is a value.
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']

Returns
-------
    None
""";
    _name_='InputDataSetMJD';
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name. <{}>".format(entrylist));
    if(not isinstance(dataframe,  (dict, pandas.DataFrame))): raise TypeError(_name_+": `dataframe` must be a dict or a pandas.DataFrame.   <{}>".format(dataframe.__class__));
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": `entrylist` must be a list. <{}>".format(entrylist));
    if(isinstance(dataframe, dict)):
        from astropy.time import Time
        for img in entrylist:
            if(force or dataframe[img]['MJD'] is None):
                if(dataframe[img]['DATE'] is not None and dataframe[img]['TIME'] is not None):
#                    print('>>>', img, dataframe[img]['DATE'], dataframe[img]['TIME'],dataframe[img]['TIME'].__class__) #@@@@
                    mjd=Time(dataframe[img]['DATE']+'T'+dataframe[img]['TIME'], format='isot', scale='utc').mjd
#                    (year,mt,day)=( int(x) for x in dataframe[img]['DATE'].split('-'))
#                    (hour,mn,sec)=( float(x) for x in dataframe[img]['TIME'].split(':'))
#                    dataframe[img]['MJD']=datetime.date(year,mt,day).toordinal()+(hour+mn/60.+sec/3600.)/24.+1721424-2400000.;
                    dataframe[img]['MJD']=mjd
    else:
        pass

###
def InputDataSetNightNumber(relenum=True, force=False, entrylist=None, dataframe=None):
    """Calculate the observation night number for each entry.

Parameters
----------
    relenum : bool
        True to set the night number as relative (the observation night will be enumerated); False to set the night number as temporal distance (MJD-MJD0+1). Option 'inputdata:nightrel'
    force : bool
        Force the calculation even if there is a value.
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']

Returns
-------
    None
""";
    _name_='InputDataSetNightNumber';
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    tjdL,nn = [],0;
    nit=_opt.OptionGet('inputdata:nightstart');
    for img in entrylist:
            if(dataframe[img]['MJD'] is not None): tjdL.append(int(dataframe[img]['MJD']-nit));
            if(dataframe[img]['NIGHT'] is not None): nn+=1;
    if(len(entrylist)>len(tjdL)): print(_name_+": !!!WARNING!!! Not all the entries have a MJD set.", file=bpar.SkZp_Par['stdout'] )
    if(nn>0 and nn<len(entrylist)):
        print(_name_+": !!!WARNING!!! Some entries have already a NIGHT set: Possibility of inconsistency. Rerun with parameter `force` or option 'inputdata:nightset' set to True.", file=bpar.SkZp_Par['stdout'] )
    if(_opt.SkZp_Opt['Flg']['inputdata:nightrel']):
        tjdL=sorted(list(set(tjdL)));
        for img in entrylist:
            if(force or dataframe[img]['NIGHT'] is None):
                if(dataframe[img]['MJD'] is not None):
                    dataframe[img]['NIGHT']=1+tjdL.index(int(dataframe[img]['MJD']-nit));
    else:
        tjd0=min(tjdL);
        for img in entrylist:
            if(force or dataframe[img]['NIGHT'] is None):
                if(dataframe[img]['MJD'] is not None):
                    dataframe[img]['NIGHT']=1+int(dataframe[img]['MJD']-nit)-tjd0;




############
def InputDataSetFix(forceMJD=None, forceAM=None, forcenight=None,  relenum=True):
    """To set/fix the Modified Julian Date, airmass, and observing night number.

Parameters
----------
    forceMJD : bool
        If the MJD has to be recalculated even if there is a valid value.
    forceAM : bool
        If the airmass has to be recalculated even if there is a valid value.
    forcenight : bool
        If the night number has to be recalculates even if there is a valid value.
    relenum : bool
        True to set the night number as relative (the observation night will be enumerated); 
        False to set the night number as temporal distance (MJD-MJD0+1). Option 'inputdata:nightrel'

Returns
-------
    None
"""
    _name_='InputDataSetFix'

    InputDataSetMJD(forceMJD or _opt.OptionGet('inputdata:mjdfix', otype='Flg'))
    InputDataSetAirMass(check=None, force=forceAM, entrylist=None, dataframe=None)
    InputDataSetNightNumber(relenum=True, force=forcenight)
      


########################
def InputDataImageStatAdd(statkey=None, ndigits=2, singletag=None, override=False, entrylist=None, dataframe=None, datatag=None):
    """Add to input data image statistic information. It ca be adding/setting tags for each given entry, 
    or a sigle one as a string with ;-separated values. The tag names will be in uppercase

Parameters
----------
    statkey : list of str
        List of the image statistics to add as single tags. Options are: 'mean', 'med', 'min', 'max', 'std'
    ndigits : int, list of int
        Precision in decimal digits (default 1 digit). One value for each key, or a global one.
    singletag : str
        The name of the single tag, if only a single tag is added/set.
    override : bool
        To change the value of an existing tag, even if its value is not None.
    entrylist : None, list
        List of the entrylist to which add the new tags. None for all entrylist in SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags of data. None for SkZp_Par['datatag']
""";
    _name_='InputDataImageStatAdd';
    from .parameters.classes  import bclasses
    if(statkey is None): return;
    if(not isinstance(statkey, list)): raise TypeError(_name_+": 'statkey' must be a list <{}>".format(statkey));
    if(not isinstance(ndigits, int)):
        if(isinstance(ndigits, list)):
            if(not all(isinstance(x,int) for x in ndigits)): raise TypeError(_name_+": `ndigits` must be an int or a list od int");
        else: raise TypeError(_name_+": `ndigits` must be an int or a list od int");

    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, list) and not isinstance(entrylist, tuple)): raise TypeError(_name_+": 'entrylist' must be a list or a tuple");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple.");
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe, dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(isinstance(singletag, str)): singletag=singletag.upper();
    if(not isinstance(override, bool)): raise  TypeError(_name_+": `override` must be a bool");

    if(isinstance(ndigits, int)): ndigits=[ndigits]*len(statkey);
    elif(isinstance(ndigits, list)):
        if(len(ndigits)<len(statkey)): ndigits.extend( [ ndigits[-1]*(len(statkey)-len(ndigits)) ] );

    if(override): imglist=entrylist;
    else:
        imglist=[];
        for img in entrylist:
            if(singletag):
                if(dataframe[img].get(singletag) is None): imglist.append(img);
            else:
                if(any( dataframe[img].get(stk.upper()) is None for stk in statkey)): imglist.append(img);
                
    if(not imglist): return;
    nproc= len(os.sched_getaffinity(0));
    with bclasses.MProc(nproc=nproc, narg=len(imglist), method='pool', minproc=-1) as mpobj: 
        retval=mpobj.pool.map(func=fits.statimage, iterable=imglist.copy());
        retval=dict(zip(imglist, retval)); #Now a dict img:stat
    stkey=set(retval[imglist[0]].keys());
    err=set(statkey)-stkey;
    if(err): raise SkZpipeError(message="Some of the statistic keys doen't exist <{}>".format(err), exclocus=_name_);
    

    for img in imglist:
        vaL=[];
        for stk,nd in zip(statkey,ndigits):
            tag=stk.upper();
            stt=stk.lower();
            if(singletag): vaL.append(round(retval[img][stk], nd));
            else:
                if(override or (dataframe[img].get(tag) is None)): dataframe[img][tag] =round(retval[img][stk], nd);
        if(singletag and (override or (dataframe[img].get(singletag) is None))): dataframe[img][singletag]=";".join( [str(val) for val in vaL] );

    if(singletag): 
        if(singletag not in datatag): datatag.append(singletag);
    else: 
        for stk in statkey:
            tag=stk.upper();
            if(tag not in datatag): datatag.append(tag);
        

#########################
#=INPUTDATA MANAGEMENT =#
#########################

########
def InputDataAnalyze(inputdata=None):
    """Analyze the inputdata (read by InputDataExternalLoad) to try to understand for what they are for, 
  checking mainly the first and second field of each line. It checks if the first field is a valid filename 
  or basename, and then if it refers to a fits file, with 1 HDU (so an image) or more than 1 (a mosaic). 
  It checks if the second field is a number or not. 
  It assumes that all header lines and empty or commented lines are already removed.

Parameters
----------
    inputdata : list/tuple of list
        List of list containing inputdata. Each sublist is the data from a line.

Returns
-------
    return : dict
        Dictionary with information of input data:
            'nl':number of data lines;
            '1':dictionary with information about first field.
                The number of first fields that are: 
                    'img' :    an existing image
                    'mos' :   an existing mosaic
                    'imgfn' :  look-like filename of an image
                    'mosfn' :  look-like filename of a mosaic
                    'file' :  a file but not a fits;
                    'base' :  the basename of a file
                    'other' : dictionary for a not-existing and not-basename entries,
                              grouped according the presence of a FITS extension:
                                'img': ending with 'fitsextension'
                                'mos': ending with 'mosaicextension'
                                'other': the others
                                'list' : list of positions of no-fits and no-basename entries.

            'others':dictionary with information about following fields:
                    'fwhm' : int, number of second fields that are numbers;
                    'type' : int, number of third fields that are entrytype;
            'fields':dictionary with information about number of fields: 
                    'same' : bool, if all the lines have same number of fields,
                    'mean','min','max': int, the mean, min and max number of fields,
            'header':dictionary with information about header: 
                    'same': bool, if also the header present a lines with that same number of fields.
                    'nhdr': list, list of number of fields of header lines with tags inside (parameter 'def:datatag')
                    'hdrfld': list, list of sets of tags in common between parameter 'def:datatag' and the header line.


""";
    _name_='InputDataAnalyze'
    if(isinstance(inputdata, tuple) and len(inputdata)==2 and isinstance(inputdata[1], list)): 
        hdrdata=inputdata[0]
        inputdata=inputdata[1]
    if(not inputdata or not isinstance(inputdata, list) or any(not isinstance(x, list) for x in inputdata)): 
        raise SkZpipeError(f"`inputdata` is not a list of list.   <{len(inputdata)} ; {set(x.__class__ for x in inputdata)}>", exclocus=_name_)
    notimage=[]
  

    noex, basen, fn, img, mos={'img':0, 'mos':0, 'other':0},0,0,0,0
    fwhm, etype=0,0
    nlL=[];
    for ii,line in enumerate(inputdata):
        nlL.append(len(line))
        #name, n# HDU, check, with_fits_ext
        isFITS=fits.isfits(line[0])
    #    print(isFITS)  #@@@@
        if(isFITS['base'] & 2): isFITS=fits.isfits(line[0]+bpar.SkZp_Par['fitsextension']) #exist as +.fits and can be open
        if(isFITS['check']==255): #filename too long
            raise SkZpipeError(f"The first field of a input line is too long (>{bpar.SkZp_Par['maxnamelength']}) to be a filename <{line[0]}>", exclocus=_name_)
        
        elif(isFITS['nhdu']==1): img+=1 # a FITS with 1HDU=image
        elif(isFITS['nhdu'] >1): mos+=1 # a FITS with 2 HDU needs extraction => as mosaic
        elif(isFITS['nhdu']==0): #file exists, but not a FITS
            fn+=1
            notimage.append(ii)
        elif(isFITS['check']): #doesn't exist
            if(glob.glob(line[0]+'.*')):
                basen+=1
            else:
                if(  isFITS['ext']==0):  noex['other']+=1
                elif(isFITS['ext']==1):  noex['img']+=1
                elif(isFITS['ext']==-1): noex['mos']+=1
                notimage.append(ii)

        val=getfloat(line[1]) if(nlL[-1]>1) else None #getfloat retun None if not a float
        if(val is not None): fwhm+=1  
        if(nlL[-1]>2): 
            if(isinstance(line[2],str) and line[2] in bpar.SkZp_Par['entrytypelist']): etype+=1
    allsame=all(nlL[0]==x for x in nlL)
    arrnl=numpy.array(nlL)

    #HEADER
    hnlL,nhdr,hdrfld,hdrsame=[],[],[],None
    if(isinstance(hdrdata, list)):
        for line in hdrdata:
            fields=set(line.split())
            hnlL.append(len(fields))
            common=fields.intersection(set(bpar.SkZp_Par['def:datatag']))
            if(common): 
                nhdr.append(len(fields))
                hdrfld.append(len(common))
        if(allsame):
            hdrsame=True if(nlL[0] in hnlL) else False
      
    return {'nl':len(inputdata),   
            '1':{'other':noex, 'file':fn, 'img':img, 'mos':mos, 'base':basen, 'listbad':notimage},     
            'others':{'fwhm':fwhm, 'type':etype},
            'fields':{'same':allsame, 'mean':round(arrnl.mean(),1), 'min':arrnl.min(), 'max':arrnl.max()},
            'header':{'same':hdrsame, 'nhdr':nhdr, 'hdrfld':hdrfld } }
    
    
############
def ReadGRH(instr=None, fileGRH=None):
    """Read for each line chip name, gain[e-/ADU], ron[e-], High Good Datum.
HGD can be a list of 'tag:value'

Parameters
----------
    instr : str, None
        Name of the instrument
    fileGRH : str
        Name of the file with gain, ron and maximum good datum value information.

Returns
-------
    x
""";
    _name_='ReadGRH';
    if(fileGRH is None): fileGRH=_opt.SkZp_Opt['S']['inputdata:gainronhigh:file'];
    if(isinstance(fileGRH,str) and not os.path.exists(fileGRH)): raise IOError("ReadGRH: No input file "+fileGRH);
    if(instr is None):
        try:
            with open(fileGRH) as f_grh:
                print("Reading {:} ...".format(fileGRH), file=bpar.SkZp_Par['stdout']);
                nl=0;
                for line in f_grh:
                    line=line.strip()
                    if(len(line)<3 or line[0]=='#'):
                        continue;
                    tmpl=line.split()
                    if(len(tmpl)<4): continue
                    _opt.SkZp_Opt['D']['photo:gain'][tmpl[0]]=float(tmpl[1]);
                    _opt.SkZp_Opt['D']['photo:ron'][tmpl[0]]=float(tmpl[2]);
                    for hgd in tmpl[3:]:
                        if(":" in hgd):
                            tmpll=hgd.split(':')
                            _opt.SkZp_Opt['D']['photo:high'][tmpl[0]+":"+tmpll[0]]=float(tmpll[1]);
                        else:
                            _opt.SkZp_Opt['D']['photo:high'][tmpl[0]]=float(hgd);
                    nl+=1;
        except OSError:
            raise OSError("problems opening/reading "+fileGRH);
    elif(instr in _db.SkZp_DB['gainronhigh']):
        pass;
    else:
        raise SkZpipeError("No data for instrument "+instr);
        
    return nl;



###############################
##=  Get Data From DataBase =##
###############################
def GetFromDB_SkZp_Opt(instr=None, verb=True):
    """Import SkZp_Opt from internal database.

Parameters
----------
    instr : str
        Name of the instrument
    verb : bool
        Verbosity flag

Returns
-------
    0 on success, -1 if fails
""";
    _name_='InputDataDatabaseRetrieve for SkZp_Opt';
    if(not instr):
        if(_opt.OptionGet('inputdata:instrument')): instr=_opt.OptionGet('inputdata:instrument');
    if(not instr or not isinstance(instr,str)): 
        print(_name_+": instr [{:}] is not the name of an instrument stored in the internal dataBase".format(instr),  file=bpar.SkZp_Par['stderr']);

    if( instr in _db.SkZp_DB['SkZp_Opt']):
        if(verb):  print("Updating options for instrument {instr} with internal database.".format(instr=instr), file=bpar.SkZp_Par['stdout']);
        _opt.OptionCheckInput(options=_db.SkZp_DB['SkZp_Opt'][instr]);
        _opt.OptionSet(optdict= _db.SkZp_DB['SkZp_Opt'][instr]);
        return 0;
    return -1;
    

###
def GetFromDB_Par(pardict=None, instr=None, verb=True):  #NOT USE!!!
    """Import data from internal database of specific *_Par values.

Parameters
----------
    pardict : dict
        Dictionary with parameters to update
    instr : str
        Name of the instrument
    verb : bool
        Verbosity flag

Returns
-------
    output : bool
""";
    _name_='InputDataDatabaseRetrieve';
    exctxt=' for Par';
    if(not pardict or not isinstance(pardict, dict) or '_name_' not in pardict): raise TypeError(_name_+exctxt+": pardict must be a valid dictionary with the parameters to be updated");
    if(not instr):
        if(_opt.OptionGet('inputdata:instrument')): instr=_opt.OptionGet('inputdata:instrument');
    if(not instr or not isinstance(instr,str)): raise TypeError("{name}{txt}: instr [{instr}] must be the name of an instrument stored in the internal dataBase".format(name=_name_, txt=exctxt, instr=instr));
    name=pardict['_name_'];

    if(":" in name):
        nameL=name.split(":");
        if(nameL[0] in _db.SkZp_DB and instr in _db.SkZp_DB[nameL[0]]):
            for tag in _db.SkZp_DB[nameL[0]][instr]:
                pardict[tag][nameL[1]]=_db.SkZp_DB[nameL[0]][instr][tag];      
    elif(name in _db.SkZp_DB and instr in _db.SkZp_DB[name]):
        for tag in _db.SkZp_DB[name][instr]:
            pardict[tag]=_db.SkZp_DB[name][instr][tag];
        return True;
    return False;
    


###
def GetFromDB_GRH(dataframe=None, instr=None, verb=True):
    """Update data dictionary with data from internal database of Gain, RON, High good datum.

Parameters
----------
    dataframe : dict
        Dictionary with data to update
    instr : str
        Name of the instrument
    verb : bool
        Verbosity flag

Returns
-------
    status : int
        0 if no error. -1 if there are no data
""";
    _name_='InputDataDatabaseRetrieve for gain, ron and high good datum';
    if(_opt.SkZp_Opt['Flg']['debug'] or _opt.SkZp_Opt['Flg']['output:verbose']): verb=True;
    exctxt=' for gain,ron,high';
    if(not isinstance(dataframe, dict)): raise TypeError(f"{_name_}: dataframe must be a dictionary.");
    if('CHIP' not in dataframe): raise SkZpipeError("The data dictionary doesn't have 'CHIP' key", exclocus=_name_);

    if(not instr):
        if(_opt.OptionGet('inputdata:instrument')): instr=_opt.OptionGet('inputdata:instrument');
        elif('INSTRUMENT' in dataframe): instr=dataframe['INSTRUMENT'];
    if(not instr or not isinstance(instr,str)): raise TypeError(f"{_name_}: `instr` [{instr}] must be the name of an instrument stored in the internal dataBase".format(exctxt, instr));

    if(instr not in _db.SkZp_DB['gainronhigh']):
#    if(verb): print("InputDataDatabaseRetrieve{:}: there are no data for instr [{:}] in the internal dataBase".format(' gain, ron and high good datum', instr), file=bpar.SkZp_Par['stdout']);   FIX THIS: It cannot print it for every image!
        return -1;
    if(verb and bpar.SkZp_Par['counter']['db_retr']==0):
        print(_name_+": reading data for instrument {instr} in the internal database".format(instr=instr), file=bpar.SkZp_Par['stdout']);
    bpar.SkZp_Par['counter']['db_retr']+=1;

    grhD={};
    if('GAIN' in _db.SkZp_DB['gainronhigh'][instr]):
        grhD['GAIN']=_db.SkZp_DB['gainronhigh'][ instr ]['GAIN'][ dataframe['CHIP'] ];
    if('RON' in _db.SkZp_DB['gainronhigh'][instr]):
        grhD['RON']= _db.SkZp_DB['gainronhigh'][ instr ]['RON'][ dataframe['CHIP'] ];
    if('HIGH' in _db.SkZp_DB['gainronhigh'][instr]):
        grhD['HIGH']=_db.SkZp_DB['gainronhigh'][ instr ]['HIGH'][ dataframe['CHIP'] ];

  #Instrument fixing
    if(instr == 'VIRCAM:VVV'):
        grhD['GAIN']=round( float(grhD['GAIN'])*float(dataframe['GAINCOR']), 6);
        if(grhD['GAIN']<=0): raise ValueError(f"{_name_}: VVV gain returned zero or negative! <{grhD['GAIN']}>");
        grhD['HIGH']=round( _db.VVV_HGD(dataframe), 2);
        if(grhD['HIGH']<=0): raise ValueError(f"{_name_}: VVV high good value returned zero or negative! <{grhD['HIGH']}>");
    elif(instr == 'GSAOI'):
        grhD['RON']=grhD['RON'][dataframe['CHIP']][ dataframe['FOWLER'] ];

  #Fixing and updating
    dataframe['RON']=round(float(dataframe['RON']) if(dataframe['RON']) else grhD['RON'] , 6);

    if(dataframe['GAIN']):
        dataframe['GAIN']=round(float(dataframe['GAIN']),6)
        if('GAIN' in grhD):
            dataframe['HIGH']=round(grhD['HIGH']*grhD['GAIN']/dataframe['GAIN'],2) if('GAIN' in grhD) else round(grhD['HIGH'],2)
            
    else:
        if('GAIN' in grhD): dataframe['GAIN']=round(grhD['GAIN'],6);
        if('HIGH' in grhD): dataframe['HIGH']=round(grhD['HIGH'],2);
        
    return 0;


###
def InputDataDatabaseRetrieve(instr=None, entrylist=None, dataframe=None, readmode=True, verb=True):
    """Import data from internal database.

Parameters
----------
    instr : str, None
        Name of the instrument used to produce the data
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']
    readmode : bool
        Flag
    verb : bool
        Verbosity flag

Returns
-------
    x
""";
    _name_='InputDataDatabaseRetrieve';
    exctxt='';
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    if(not instr and _opt.OptionGet('inputdata:instrument')): instr=_opt.OptionGet('inputdata:instrument');
    instrS=InputDataTagValueSet(tag='INSTRUMENT');
    if(not instr and instrS is not None):
        if(len(instrS)==1): instr=tuple(instrS)[0];
    GetFromDB_SkZp_Opt(instr, verb=verb);
# #Skip if parameter flag says so
    if(readmode):
      #if instrument is not given as input, but its parameter is set, use that value
    #  if(not isinstance(instr,str)): raise TypeError("DatabaseRetrieve{:}: instr [{:}] must be the name of an instrument stored in the internal dataBase".format(exctxt, instr));
    #  GetFromDB_DAO_Par(p, instr);
        if(verb):  print("Updating input data with gain,ron and high good datum from internal database", file=bpar.SkZp_Par['stdout']);
        for ii,img in enumerate(entrylist):
            instr0=instr;
            if(instr0 and (not 'INSTRUMENT' in dataframe[img] or not dataframe[img]['INSTRUMENT'])): dataframe[img]['INSTRUMENT']=instr0;
            if(not instr0 and 'INSTRUMENT' in dataframe[img]):  instr0=dataframe[img]['INSTRUMENT'];
          # input instr and header value are set, but different
            if(instr0 and 'INSTRUMENT' in dataframe[img] and instr0!=dataframe[img]['INSTRUMENT']):
                if(dataframe[img]['INSTRUMENT'] not in instr0):
                    print(_name_+': for image {img} the given instrument [{instr0}] is different from the one in the input data [{instr}].'.format(img=img, instr0=instr0, instr=dataframe[img]['INSTRUMENT']), file=bpar.SkZp_Par['stderr']);
            if(not instr0 and (not 'INSTRUMENT' in dataframe[img] or not dataframe[img]['INSTRUMENT'])): raise SkZpipeError(_name_+': No instrument name is given.', exclocus=img);

            if(_opt.OptionGet('inputdata:gainronhigh:dbforce', otype='Flg') or not dataframe[img]['GAIN'] or not dataframe[img]['RON'] or not dataframe[img]['HIGH']):
                GetFromDB_GRH(dataframe[img], instr0, verb=verb and ii==0);

        
            if(instr == 'VIRCAM:VVV'):
                chp=int(dataframe[img]['CHIP']);
                off=int(dataframe[img]['OFFSET']);
                dataframe[img]['POSNAME']="{:};{:d}".format(int(chp)+0.3*(.5+abs(off-3.5)), off>>2);

##################################
##=  Get Data From Fits Header =##
##################################
def FitsHeaderInfoRetrieve(image=None, headertype=None, index=0, instr=None, headerext=None, extraheaderkey=None, extradatatag=None):
    """Retrieve data from Fits header of the given image. It returns a tuple with (dictionary with info from headers, list of additional datatag)

Parameters
----------
    image : str
        Full name (with extension) or basename (the extension is retrieved from internal parameter 'fitsextension') of the image for which retrieve data from headers
    headertype : str,list
        The type of header from which to retrieve the info.
          'mos','mosaic' : To retrieve info from the header of the mosaic or general info about the 
               overall observation (e.g.  instrument, date/time, exposure time, filter, ...)
          'chip' : To retrieve info from the header of the single image or specific info about the 
               sensor (e.g. size, gain, ron, scale, binning, internal offset)
        Default ['mos','chip'] to retrieve all the info (generic and specific)
    index : int, str
        Number or name of the HDU from where read the header. Default 0.
    instr : str
        Instrument for the image
    headerext : dict
        Dictionary giving the extension for each header type.
    extraheaderkey :  dict, None
        Dictionary that map the extra tags to their correspondig header card (key=tag; value=header card or how to get the value)
    extradatatag : list, None
        List of extra tag to be added in the desired orden. If it is not given, it is generated automatically.

Returns
-------
    A 2-element tuple: dictionary with info from headers; list of additional datatag.

Functions
---------
    FitsHeaderInfoRead
    parameters.database.headerkeyread
""";
    _name_='FitsHeaderInfoRetrieve';
    
    if(not isinstance(image, str)): raise TypeError(_name_+": `image` must be a string");
    if(not os.path.exists(image)): 
        if(os.path.exists(image+bpar.SkZp_Par['fitsextension'])): image+=bpar.SkZp_Par['fitsextension'];
        else: raise IOError(f"{_name_}: {image}({bpar.SkZp_Par['fitsextension']}) image does not exist!");
    if(not isinstance(index, (int,str))): raise TypeError(f"{_name_}: `index` must be a integer or a string <{index.__class__}>");

  #set defaults for instr and headerext
    if(not instr): instr=_opt.OptionGet('inputdata:instrument');
    if(not headerext): headerext={'chip':bpar.SkZp_Par['chipheaderext'], 'mos':bpar.SkZp_Par['mosheaderext']};
    else:
        headerext.setdefault('chip', bpar.SkZp_Par['chipheaderext'])
        headerext.setdefault('mos', bpar.SkZp_Par['mosheaderext'])

    with fits.pyfits.open(image) as fitso:
        nhdu=len(fitso);
      #Set instr=INSTRUMENT if not given ('headerkey'[None] contain the default values for it)
        if(not instr): instr=fitso[0].header.get( _db.SkZp_DB['headerkey'][None]['mos']['INSTRUMENT'] )
        if(isinstance(index,str) and index not in fitso):  raise ValueError(f"{_name_}: wrong value for `index` <{index}>")
    imgbn=image.rsplit('.',1)[0]  #Basename

    if(isinstance(index,int)):
        if(index<0):  raise ValueError(f"{_name_}: wrong value for `index` <{index}>")
        if(index>nhdu): raise ValueError(f"{_name_}: wrong value for `index` <{index}>")

    hdrextflag=dict( (tp, os.path.exists(imgbn+ext))  for tp,ext in headerext.items()) # if exist the txt version of the headers. If 'mos' exist and nhdu=1, it is a extracted image
    infohdr={'mos': FitsHeaderInfoRead(imgbn+headerext['mos'])[0] if(hdrextflag['mos']) else {}};    #getting mos info if in txt file
    if(not instr): instr=infohdr['mos'].get( _db.SkZp_DB['headerkey'][None]['mos']['INSTRUMENT'] )
  #
    if(not headertype):
        headertype= ['mos', 'chip'];
#      if(nhdu==1): #single image
#          headertype= ['mos', 'chip'] if(hdrextflag['mos']) else ['chip'];
#      else: #mosaic
#          headertype= ['chip'] if(index) else ['mos'];
    else:    
        headertype=[headertype] if(not isinstance(headertype, (tuple,list))) else list(headertype); 
        if(not all(tp in ('mos','mosaic','chip') for tp in headertype )): raise SkZpipeError(f"Wrong header type: 'chip' or 'mos'/'mosaic' <{headertype}>", exclocus=_name_);
        if('mosaic' in headertype): headertype[headertype.index('mosaic')]='mos'; 
        if(len(headertype)>=2):
                if('chip' not in headertype or len(headertype)>2): raise SkZpipeError(f"Wrong headertype list <{headertype}>", exclocus=_name_)
                headertype=['mos', 'chip']; 
    #NOW headertype contain only 'mos' OR 'chip', in this order!

  #EXTRAHEADERKEYS
    if(not extraheaderkey): extraheaderkey=_opt.OptionGet('inputdata:extraheaderkey',otype='D').copy();
    if(not extradatatag): extradatatag=_opt.OptionGet('inputdata:extradatatag', otype='L').copy();
    if(not isinstance(extraheaderkey, dict) or not isinstance(extradatatag, list)): raise TypeError(f"{_name_}: Wrong type for `extraheaderkey` (dict/None) or `extradatatag` (list/None) <{extraheaderkey.__class__}><{extradatatag.__class__}>");
    for tag in extraheaderkey:
        if(tag not in extradatatag): extradatatag.append(tag);
    if(len(extradatatag)<len(extraheaderkey)): raise SkZpipeError(f"{_name_}: `extraheaderkey` is longer than `extradatatag` <{len(extraheaderkey)};{len(extradatatag)}>.");

  #########
    hdrinfo, headerkeyD, = {}, {}  #info from headers, instruction, final-data, list-tag
    hdrdata, datatag = {'HDRSRC':''}, []; #info from headers, instruction, final-data, list-tag
    
  #Read headers as spicified and store cards => you need to know the INSTRUMENT
    if(nhdu>1): #has more than 1 hdu: mosaic
        if('mos' in headertype):
            tmpd=FitsHeaderInfoRead(image, index=0)[0];    #Which default? from image! o extracted txt?
            if(tmpd):
                hdrinfo.update(tmpd);
                hdrdata['HDRSRC']+='mos'
        if('chip' in headertype and index): #from a mosaic extract info from a chip only if you ask for a specific hdu
            tmpd=FitsHeaderInfoRead(image, index=index)[0];    #Which default? from image! o extracted txt?
            if(tmpd):
                hdrinfo.update(tmpd);
                hdrdata['HDRSRC']+='chip'

    else: #single image: 'mos' only from txt or included in 'chip'
        infohdr['chip']=FitsHeaderInfoRead(imgbn+headerext['chip'] if(hdrextflag['chip']) else image)[0];
        for typ in headertype:
            hdrinfo.update(infohdr[typ]);
            hdrdata['HDRSRC']+=typ

  #Set instr=INSTRUMENT if not given ('headerkey'[None] contain the default values for it)
    if(not instr and _db.SkZp_DB['headerkey'][None]['mos']['INSTRUMENT'] in hdrinfo):  instr = hdrinfo.get(  _db.SkZp_DB['headerkey'][None]['mos']['INSTRUMENT']);
#######
  #Read from database the default  headerkey definitions
    for typ in headertype:
        headerkeyD.update(**_db.SkZp_DB['headerkey'][None][typ])
    datatag.extend(_db.SkZp_DB['headerkey'][None]['datatag'].copy())

  ##Update headerkey list
  #from DB for that instrument
    if(instr in _db.SkZp_DB['headerkey']):
        for typ in headertype:
            headerkeyD.update(_db.SkZp_DB['headerkey'][ instr ].get(typ, {}));
        datatag.extend( _db.SkZp_DB['headerkey'][ instr ]['datatag'].copy() )
  #from options
    for tag in headerkeyD:
        if(tag not in datatag): datatag.append(tag);
    if(len(datatag)<len(headerkeyD)): raise SkZpipeError(_name_+': something wrong with extraheaderkey and extradatatag.');
    if(extraheaderkey): headerkeyD.update(extraheaderkey);
    if(extradatatag):      datatag.extend(extradatatag);
    datatag+=['HDRSRC'];


    
  #START 
  #Retrieve selected info for each tag
    for tag in headerkeyD:
        hdrdata[tag]=_db.headerkeyread(tag, headerkeyD[tag], hdrinfo);

    #Check that listed tag has a entry in hdrdata
    for tag in datatag:
        hdrdata.setdefault(tag);

    return (hdrdata, datatag);


#########
def MosaicHeaderInfoRetrieve(mosaic=None, instr=None, extraheaderkey=None, extradatatag=None):
    """Retrieve data from headers of the given mosaic. It returns a tuple with (dictionary with info from headers, list of additional datatag)

Parameters
----------
    mosaic : str
        Full name (with extension) or basename (but the extension has to be the one in internal parameter 'fitsextension') of the mosaic for which retrieve data from headers
    instr : str
        Instrument for the mosaic
    extraheaderkey :  dict, None
        Dictionary that map the extra tags to their correspondig header card (key=tag; value=header card or how to get the value)
    extradatatag : list, None
        List of extra tag to be added in the desired orden. If it is not given, it is generated automatically.

Returns
-------
    A 2-element tuple: dictionary with info from headers; list of additional datatag.

Functions
---------
    FitsHeaderInfoRead
    parameters.database.headerkeyread
""";
    _name_='MosaicHeaderInfoRetrieve';
    
    if(not isinstance(mosaic, str)): raise TypeError(_name_+": `mosaic` must be a string");
    if(not os.path.exists(mosaic)): raise IOError(f"{_name_}: {mosaic} mosaic does not exist!");

    if(not instr): instr=_opt.OptionGet('inputdata:instrument');

  #if instr is not given, use the one in options
    if(not extraheaderkey): extraheaderkey=_opt.SkZp_Opt['D']['inputdata:extraheaderkey'].copy();
    if(not extradatatag): extradatatag=_opt.SkZp_Opt['L']['inputdata:extradatatag'].copy();
    if(not isinstance(extraheaderkey, dict) or not isinstance(extradatatag, list)): raise TypeError(_name_+": Wrong type for extraheaderkey (dict/None) or extradatatag (list/None)");
  
    for tag in extraheaderkey:
        if(tag not in extradatatag): extradatatag.append(tag);
    if(len(extradatatag)<len(extraheaderkey)): raise SkZpipeError(_name_+': something wrong with extraheaderkey and extradatatag.');

  ##
    hdrinfo, hdrdata, datatag = {}, {}, [];
    headerkeyD = {'mos':{}, 'chip':{}};
  #Read from database the headerkey definitions
    headerkeyD['mos'].update(**_db.SkZp_DB['headerkey'][None]['mos']);
    headerkeyD['chip'].update( **_db.SkZp_DB['headerkey'][None]['chip']); #merging the 2 dict (python>=3.5)
    
  #Read headers as spicified) and store cards => you need to know the INSTRUMENT
    hdrinfo=FitsHeaderInfoRead(header=mosaic, index=-1);

  #Set instr=INSTRUMENT if not given (headerkeyD contain the default values for _db.SkZp_DB['headerkey'])
    if(not instr and headerkeyD['mos']['INSTRUMENT'] in hdrinfo[0]):  instr = hdrinfo[0][headerkeyD['mos']['INSTRUMENT']];

  ##Update headerkey list
  #from DB for that instrument
    if(instr in _db.SkZp_DB['headerkey']):
        for hdui in ('mos','chip'):
            if(hdui in _db.SkZp_DB['headerkey'][instr]):
                headerkeyD[hdui].update(_db.SkZp_DB['headerkey'][ instr ][hdui]);
        datatag=_db.SkZp_DB['headerkey'][ instr ]['datatag'].copy();
  #from options
    for tag in list(headerkeyD['mos'])+list(headerkeyD['chip']):
        if(tag not in datatag): datatag.append(tag);
    if(len(datatag)<len(headerkeyD)): raise SkZpipeError(_name_+': something wrong with extraheaderkey and extradatatag.');
    if(extraheaderkey): headerkeyD.update(extraheaderkey);
    if(extradatatag):      datatag.extend(extradatatag);
    
  #START 
  #Retrieve selected info
  #From HDU 0/mosaic header
    for tag in headerkeyD['mos']:
        hdrdata[tag]=_db.headerkeyread(tag, headerkeyD['mos'][tag], hdrinfo[0]);
  #From chip headers
    for tag in headerkeyD['chip']:
        tagvL=[]
        for header in hdrinfo[1:]:
            tagvL.append(_db.headerkeyread(tag, headerkeyD['chip'][tag], {**hdrinfo[0], **header}));
        if(not all( type(tagvL[0])==type(x) for x in tagvL) ): 
            raise ValueError(_name_+": in mosaic {mosaic} return values for tag '{tag}' has different type for different chip! <{val}>".format(mosaic=mosaic, tag=tag, val=tagvL));
        if( all( tagvL[0]==x for x in tagvL) ): hdrdata[tag]=tagvL[0];
        elif(isinstance(tagvL[0],(float,int))):
            tmparr=numpy.array(tagvL);
            hdrdata[tag]=(tmparr.mean(), tmparr.std(), numpy.median(tmparr));
        else:  hdrdata[tag]=tagvL;
        

    #Check that listed tag has a entry in hdrdata
    for tag in datatag:
        hdrdata.setdefault(tag);

    return (hdrdata, datatag);

  ###@_______________________+---------------

###
def InputDataFromFitsHeader(entrylist=None, instr=None, listof='image', chipheaderext=None, mosheaderext=None, dataframe=None, datatag=None, override=None):
    """Extract data from Fits Header.

Parameters
----------
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    instr : str, None
        Instrument name
    listof : str
        If the inputdata contains information about images: 'image'
        If the inputdata contains list of mosaic names: 'mosaic'
    chipheaderext : str, None
        Extension of the extracted header of the chip
    mosheaderext : str, None
        Extension of the extracted header of the mosaic
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags in input data. None for SkZp_Par['datatag']
    override : bool, None
        Flag to determine if the data from FITS header have to override the existing data.

Returns
-------
    Tuple: number of extracted header from  chip, number of extracted header from mosaic

Functions
---------
    FitsHeaderInfoRetrieve
""";
    _name_='InputDataFromFitsHeader';
    if(not isinstance(listof,str)): raise TypeError(_name_+": `listof` must be a string ('image' or 'mosaic') <{}>".format(listof));
    if(not any( x in listof for x in ('image', 'mosaic'))): raise ValueError(_name_+": Wrong value for `listof` <{}>".format(listfor));
    if(chipheaderext is None): chipheaderext=bpar.SkZp_Par['chipheaderext'];
    if( mosheaderext is None):  mosheaderext=bpar.SkZp_Par['mosheaderext'];
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": 'datatag' must be a list.");
    if( override is None): override=_opt.SkZp_Opt['Flg']['inputdata:headeroverride'];

    print("Updating input data with extracted fits headers", file=bpar.SkZp_Par['stdout']);
    if(not instr): instr=_opt.OptionGet('inputdata:instrument');
    headerext={'chip':chipheaderext, 'mos':mosheaderext};
    nhdr={'chip':0, 'mos':0};
    datatag_old=datatag.copy();
    datatag_db=_db.SkZp_DB['headerkey'][None]['datatag'].copy()

#  nproc= _opt.SkZp_Opt['I']['mp:nproc'] if(_opt.SkZp_Opt['I']['mp:nproc']) else len(os.sched_getaffinity(0));
    nproc= len(os.sched_getaffinity(0));
   ##%%%%%##
    def _IDFFH_get(img):
        isFITS=fits.isfits(img)
        nhdu=isFITS['nhdu']
        if(nhdu<=0): nhdu=(isFITS['base']&2) + (isFITS['base']&8)
        if(nhdu<=0): return #no HDU, no header!
        return FitsHeaderInfoRetrieve(image=img, headertype=None, instr=instr, headerext=headerext)
  
#  with bclasses.MProc(nproc=nproc, narg=len(entrylist), method='pool', minproc=-1) as mpobj: 
#    retval=mpobj.pool.map(func=FitsHeaderInfoRetrieve, iterable=entrylist.copy());
#    retval=dict(zip(entrylist, retval)); #Now a dict img:(hdrdata, hdrdatatag)
#      
#  for img in entrylist:
#    datatag_db.extend([tag for tag in retval[img][1] if tag not in datatag_db])
#   #Aimed Update if new value is not None
#    DictdataUpdate(olddict=dataframe[img], newdict=retval[img][0], override=override);
#    
#    for tp in nhdr:
#      if( tp in retval[img][0]['HDRSRC']): nhdr[tp]+=1;
#  retval.clear();

    for img in entrylist:
        isFITS=fits.isfits(img)
        nhdu=isFITS['nhdu']
        if(nhdu<=0): nhdu=(isFITS['base']&2) + (isFITS['base']&8)
        if(nhdu<=0): continue #no HDU, no header!
        hdrdata, hdrdatatag = FitsHeaderInfoRetrieve(image=img, headertype=None, instr=instr, headerext=headerext)

        datatag_db.extend([tag for tag in hdrdatatag if tag not in datatag_db]) #THIS cannot be parallelized
      #Aimed Update if new value is not None
        DictdataUpdate(olddict=dataframe[img], newdict=hdrdata, override=override) #THIS cannot be parallelized
        
        for tp in nhdr:
            if( tp in hdrdata['HDRSRC']): nhdr[tp]+=1;

        if(_opt.OptionGet('inputdata:instrumentset') and instr):   dataframe[img]['INSTRUMENT']=instr
        
    ## Here set the merge among datatag from header and input file (the later are appended)
    datatag_db.extend([tag for tag in datatag_old if tag not in datatag_db])
    datatag[:]=datatag_db
    ##

    if('HDRSRC' in datatag):
        datatag.remove('HDRSRC')
    datatag.append('HDRSRC')


    return (nhdr['chip'], nhdr['mos'])


#############################################################
#############################################################

########################
#=InputData Management=#
########################
########
def InputDataTagValueList(tag=None, entrylist=None, dataframe=None, datatag=None):
    """Retrieve the list of values of the given tag among the entries in `entrylist` from dictioary database `dataframe` if present in tag list `datatag`.

Parameters
----------
    tag : str
        Name of the tag
    entrylist : None, list, str
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags in input data. None for SkZp_Par['datatag']
Returns
-------
    output : list
        List of the values or None if tag is not in datatag.
""";
    _name_='InputDataTagValueList';
    if(not isinstance(tag, str)): raise TypeError(_name_+": 'tag' must be a str. <{}>".format(tag));
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name. <{}>".format(entrylist));
    if(not isinstance(entrylist, (list,tuple))): raise TypeError(_name_+": 'entrylist' must be a list or a tuple. <{}>".format(entrylist));
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple. <{}>".format(datatag));
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe, dict)): raise TypeError(_name_+": 'dataframe' must be a dict. <{}>".format(dataframe.__class__));

    if(tag in datatag):
        return [dataframe[fn][tag] for fn in entrylist]

    return None;

####
def InputDataTagValueSet(tag=None, entrylist=None, dataframe=None, datatag=None):
    """Retrieve the set of values of the given tag among the entries in `entrylist` from dictioary database `dataframe` if present in tag list `datatag`.

Parameters
----------
    tag : str
        Name of the tag
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags in input data. None for SkZp_Par['datatag']
Returns
-------
    output : set
        Set of the values or None if tag is not in datatag.

Functions
---------
    InputDataTagValueList

""";
    _name_='InputDataTagValueSet';
    ret=InputDataTagValueList(tag=tag, entrylist=entrylist, dataframe=dataframe, datatag=datatag);
    if(ret is None): return; 
    return set(ret);
  
######
def InputDataDict2PandasDF(inputdata=None, entrylist=None, datatag=None):
    """Transform a inputdata database from dictionary form to Pandas Dataframe

Parameters
----------
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']
    entrylist : None, list, str
        List of input data entries. None for SkZp_Par['inputlist']
    datatag : None, list
        List of the tags in input data. None for SkZp_Par['datatag']

Returns
-------
    output : pandas Dataframe
        The inputdata stored in a dictionary is transferred to a Paandas dataframe
"""
    _name_='InputDataDict2PandasDF'
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name. <{}>".format(entrylist));
    if(not isinstance(entrylist, (list,tuple))): raise TypeError(_name_+": 'entrylist' must be a list or a tuple. <{}>".format(entrylist));
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple. <{}>".format(datatag));
    if(inputdata is None): inputdata=bpar.SkZp_Par['inputdata'];
    if(not isinstance(inputdata, dict)): raise TypeError(_name_+": 'dataframe' must be a dict. <{}>".format(dataframe.__class__));

    tmpdf=pandas.DataFrame(inputdata).T # index=entrylist, columns=datatag)
    return tmpdf


####
def InputDataUpdate(newdata=None, entries=None, taglist=None,   dataframe=None, datatag=None, raisexc=True):
    """Update input data in `dataframe` (default parameter 'inputdata') using additional data through `newdata`. It permits to add new tags, but does not add new entries. Entries present in `dataframe` but not in `newdata` will have the values for the new tags set to None. To update specific tags, use InputDataTagUpdate.

Parameters
----------
    newdata : dict
        Dictionary with additional data to be included. 
    entries : None, list
        List with the entries to modify. Default None  for all.
    taglist : list of str
        Ordered list of the tag in `newdata`. If not provided, it will be retrieved from the dictionary
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        Ordered list of the tags of each entry in dataframe. None for SkZp_Par['datatag']

Returns
-------
    return : tuple 
    Number of updated entries, set of tags in common between `newdata` and `dataframe`.
""";
    _name_='InputDataUpdate'; 

    if(not isinstance(newdata,  dict)): raise TypeError(_name_+": `newdata` must be a dict.");
    if(entries is not None and not isinstance(entries, list)): raise TypeError(_name_+": `entries` must be a list or None.");
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": `dataframe` must be a dict.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": `datatag` must be a list.");

    newlist=list(newdata.keys());
    tagset0=set(newdata[newlist[0]]);
    if('NAME' in tagset0): 
        if(newdata[newlist[0]]['NAME']!=newlist[0]): 
            raise SkZpipeError(message="entry {it} in `newdata` has 'NAME' value different from its name <{name}>".format(it=newlist[0], name=newdata[newlist[0]]['NAME']), exclocus=_name_);
    for item in newlist[1:]:
        tagset=set(newdata[item]);
        if(tagset!=tagset0): raise SkZpipeError(message="`newdata` has entries with different set of tags <{ts} != {ts0}>".format(ts=tagset, ts0=tagset0), exclocus=_name_);
        if('NAME' in tagset): 
            if(newdata[item]['NAME']!=item): raise SkZpipeError(message="entry {it} in `newdata` has 'NAME' value different from its name <{name}>".format(it=item, name=newdata[item]['NAME']), exclocus=_name_);
    if(taglist is None): taglist=list(tagset0);

    newtag=tagset0-set(datatag);
    comtag=tagset0-newtag;
    updt=0;
    for img in dataframe:
        if(img in newdata):
            dataframe[img].update(newdata[img]);
            updt+=1;
        else:
            dataframe[img].update(dict().fromkeys(newtag))
    datatag.extend(list(newtag));
        
    return updt, comtag;



########################
def InputDataSelect(select=None, atleastone=True, excludeNone=True, drop=False, runlist=None,   dataframe=None, entrylist=None, datatag=None, verb=True):
    """Select entries in input data `dataframe`/`entrylist` to include in `runlist`  (default global parameter 'runlist').

Parameters
----------
    select : str, dict, list of str
        Selection options. 
        If a dict, the items can be:
          'suffix' : list of str
               List  of suffix of filename (entry name+suffix) that have to exist.
          'tag' : dict
               Dictionary where the keys are the names of the tags to use, while the values can be:
                 allowed value or list of allowed values (a compare == will be used);
                 callable that accepts the tag value as input and returning a bool.
          'mode' : str, list of str
              '.XYZ'       : if it is a str starting with a dot, it is meant as suffix (={'suffix':['.XYZ']}).
              'psfcal'     : rejecting entries that have not ENTRYTYPE='image:sci' and have not image 
                                (= 'suffix' set with parameter 'fitsextension' ).
              'stack'      : rejecting entries that have not ENTRYTYPE='image:sci' and have not files to create
                                a stack image (= 'suffix':[ SkZp_Opt['S']['photo:psf:done'], '.als', '.psf',
                                parameter 'fitsextension' ] ).
              'psfdone'    : same as 'stack'
              'srclst'     : rejecting entries that have not ENTRYTYPE='stack' and have not files to create a
                                source list (= 'suffix':[ SkZp_Opt['S']['photo:psf:done'], '.psf', parameter 'fitsextension' ] ).
              'framephoto' : rejecting entries that have not ENTRYTYPE='stack' and have not a source list
                                (= 'suffix':[ SkZp_Opt['S']['photo:psf:done'], '.als' ] ).
              'catalog'    : rejecting entries that have not ENTRYTYPE='image:sci' and have not files to create a catalog from '.alf'.
              'ctlg'       : as 'catalog'
              'exist'      : rejecting entries that have not fits.
              'standard'   : add option 'image:standard' to 'tag' key
        If a string, it indicate a 'mode' (see above). If list, a list of 'mode'.
    atleastone : tuple, list, str
        Flag to determine for which criteria is valid the 'at least one' rule:
          'tag'  :  selected if at least one of the tags has the right value (otherwise all the tags have to be satisfied).
          'suff' :  selected if at least one of the suffix is of an existing file (otherwise all the suffixes have to be satisfied).
    excludeNone : bool
        Flag to determine if a value of None for a tag is always reason to be rejected or not.
    drop : bool
        Flag to determine if the selection will replace the complete internal list (parameter `entrylist`),
            or just the selection in `runlist`.
    runlist : None, list
        List where to store the list of the selected entries (output). None for global parameter 'runlist'.
        It will be cleared at the beginning.
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for global parameter 'inputdata'.
    entrylist : None, list, str
        Ordered list of the entries to choose from. None for parameter 'inputlist'. Or the name of the
            parameter: 'runlist' for global parameter 'runlist', 'inputlist' for global parameter 'inputlist'.
    datatag : None, list
        List of the tags of input data. None for SkZp_Par['datatag']
    verb : bool
        Verbosity flag

Returns
-------
    x : int
        Number of selected entries
""";
    _name_='InputDataSelect'; 
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(runlist is None): runlist=bpar.SkZp_Par['runlist'];
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list, None or a valid descriptor.");
    if(not isinstance(runlist, list)): raise TypeError(_name_+": 'runlist' must be a list.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": 'datatag' must be a list.");

    selectD={'suffix':_opt.OptionGet('image:select:bysuffix'), 'tag':_opt.OptionGet('image:select:bytag'), 'mode':_opt.OptionGet('image:select:bymode')};
    if(not select and all( not selectD[x] for x in selectD)):
        runlist[:]=entrylist.copy();
        return len(runlist);
    if(isinstance(select,str)): select=[select];
    if(isinstance(select,list)): select={'mode':select};
    

    if(isinstance(select,dict)):
        if('mode' in select):
            if(not isinstance(select['mode'],list)): select['mode']=[select['mode']];
            for mode in select['mode']:
      ##TOO MUCH DAOPHOT DEPENDENT!!! MUST BE MORE GENERAL!!
                if(mode in ('psfcal')):
                    selectD['tag'].update({'ENTRYTYPE':['image:sci']});
                elif(mode in ('stack', 'psfdone')):
                    selectD['suffix'].extend( [ bpar.SkZp_Par['fitsextension'], _opt.SkZp_Opt['S']['photo:psf:done'], _opt.SkZp_Opt['S'  ]['stack:match:srcext'], '.psf' ] );   ##!!!! BIAS
                    selectD['tag'].update({'ENTRYTYPE':['image:sci']});
                elif(mode in ('srclst')):
                    selectD['suffix'].extend( [ bpar.SkZp_Par['fitsextension'], _opt.SkZp_Opt['S']['photo:psf:done'] ] );
                    selectD['tag'].update({'ENTRYTYPE':['stack']});
                elif(mode in ('framephoto')):
                    selectD['suffix'].extend( [ _opt.SkZp_Opt['S']['match:extension'], _opt.SkZp_Opt['S']['photo:ext:srclst'] ] );  
                    selectD['tag'].update({'ENTRYTYPE':['stack']});
                elif(mode in ('ctlg', 'catalog')):
                    selectD['suffix'].extend(['.alf']);   ##!!!! BIAS
                    selectD['tag'].update({'ENTRYTYPE':['image:sci']});
                elif(mode in ('exist')):
                    selectD['suffix'].extend([bpar.SkZp_Par['fitsextension']]);
                elif(mode in ('standard')):
                    if(selectD['tag']):
                        for tag,lval in _opt.OptionGet('image:standard').items():
                            if(tag in selectD['tag']):
                                selectD['tag'][tag]=list( set(select['tag'][tag] ) | set(lval) );
                            else: selectD['tag'][tag]=lval;
                    else: selectD['tag']=_opt.OptionGet('image:standard');
                elif(mode[0]=='.'):
                    selectD['suffix'].append(mode)
                else: raise ValueError(_name_+": `select` contain an invalid value <{}>".format(mode));
        if('suffix' in select):
            if(not isinstance(select['suffix'],list)): 
                if(isinstance(select['suffix'],str)): 
                    select['suffix']=[ select['suffix'] ]
                else:  raise ValueError(f"{_name_}: `select` contain an invalid value.   <{select}>")
            selectD['suffix'].extend(select['suffix']);
        if('tag' in select):
            if(not isinstance(select['tag'],  dict)): raise TypeError(_name_+": `select['tag']` must be a dict.");
            for tgg in select['tag']:
                if(not isinstance(select['tag'][tgg], list)): select['tag'][tgg]=[ select['tag'][tgg] ];
                selectD['tag'].setdefault(tgg.upper(), []);    #TAG NAME must be upper case!
                selectD['tag'][tgg.upper()].extend(select['tag'][tgg]);

    for tgg in selectD['tag']:
        if(tgg not in datatag): raise KeyError(_name_+": `select` contains tag <{tag}> that are not in input data (not in `datatag`)".format(tag=tgg));

  #Selecting
    runlist0=[];
    for img in entrylist: #Cycle over entries
        if(img not in dataframe): raise KeyError(_name_+": entry {:} is not present in the input data.".format(img));
        
        skipflg=False;
        if('tag' in selectD):   # and not skipflg):  Not necessary
            for tgg in selectD['tag']: #Cycle over requested tag
                keepflg=False;
                for val in selectD['tag'][tgg]:
                    if(excludeNone and dataframe[img][tgg] is None): break; #default is to reject: keepflg=False
                    check= val(dataframe[img][tgg]) if(callable(val)) else (dataframe[img][tgg].__class__(val)==dataframe[img][tgg]);
                    if(check):
                        keepflg=True;
                        break;
                if(not keepflg):
                    if(verb): print("Skipping ", dataframe[img]['NAME'], "[tag= {tag} : {val} ]".format(tag=tgg, val=dataframe[img][tgg]), file=bpar.SkZp_Par['stdout']);
                    skipflg=True;
                    break;
        if(not skipflg and 'suffix' in selectD):
            for suf in selectD['suffix']:
                if(not os.path.exists(dataframe[img]['NAME']+suf)):
                    if(verb): print("Skipping ", dataframe[img]['NAME'], "[missing {suff}]".format(suff=suf), file=bpar.SkZp_Par['stdout']);
                    skipflg=True;
                    break;
        if(not skipflg): runlist0.append(img);
################################## 
# Check uniformity in Observation Sets

    if(False and (_opt.OptionGet('image:setcheck', 'Flg') or _opt.OptionGet('image:uniform', 'Flg'))):
        #RUN Instrument specific check
        if(instr in _db.SkZp_DB['obs_set_check']):    _db.SkZp_DB['obs_set_check'](inputdata, mosinfo);
        
            #Additional check for uniformity if not instrument is set
        elif(_opt.SkZp_Opt['Flg']['image:uniform']):
            chipset=set();
            for inp in inputdata:
                if(inp['chip']['#']): chipset|=set(inp['chip']['#']);
            chipset=tuple(chipset);
            for inp in inputdata:
                if(inp['chip']['#']): inp['chip']['#']=chipset;
            
    #
    if(drop): entrylist[:]=runlist0;
    runlist[:]=runlist0;
    return len(runlist);


###################
########################
def InputDataTagUpdate(tags=None, entrylist=None, dataframe=None, datatag=None):
  """Add or update tags for each given entry.

Parameters
----------
    tags : dict
        Dictionary with:
          key :  str
            the name of the new tag
          value : callable or str or number
            a callable that takes as input the input-data of an entry and return the value for the new tag; or a fix value (str or number).
    entrylist : None, list
        List of the entrylist to which add the new tags. None for all entrylist in SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags of data. None for SkZp_Par['datatag']
""";
  _name_='InputDataTagUpdate';
  if(not isinstance(tags, dict)): raise TypeError(_name_+": 'tags' must be a dict");
  if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
  if(isinstance(entrylist, str)):
    if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
    elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
    else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
  if(not isinstance(entrylist, list) and not isinstance(entrylist, tuple)): raise TypeError(_name_+": 'entrylist' must be a list or a tuple");
  if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
  if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple.");
  if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
  if(not isinstance(dataframe, dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");

  for tg in tags:
    if(not isinstance(tg, str)): raise TypeError(_name_+": keys in 'tags' must be a string [{:}]".format(str(tags)));
    if(not callable(tags[tg]) and not isinstance(tags[tg], (str,int,float))): raise TypeError(_name_+": values in 'tags' must be a callable or a fix value (str or a number)");
   
  for tg in tags:
    for img in entrylist:
      dataframe[img][tg]=tags[tg](dataframe[img]) if(callable(tags[tg])) else tags[tg];
      
    if(tg not in datatag): datatag.append(tg);
  
  return;

        

########################
def InputDataTagRemove(tag=None, entrylist=None, dataframe=None, datatag=None):
    """Remove tags from a given inputdata dictionary.

Parameters
----------
    tag : 
        Iterable with the names of the tags.
    entrylist : None, list
        list of the entries to which add the tags. None for all entrylist in SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags of input data. None for SkZp_Par['datatag']

Returns
-------
    List of removed tags.
"""
    _name_='InputDataTagRemove';
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, list) and not isinstance(entrylist, tuple)): raise TypeError(_name_+": `entrylist` must be a list or a tuple");
    if(not isinstance(tag, (list,tuple))): raise TypeError(_name_+": `tag` must be a dict");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple.");
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe, dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");

    remL=[];
    for tg in tag:
        if(not isinstance(tg, str)): raise TypeError(_name_+": keys in `tag` must be a string [{:}]".format(str(tag)));
        if(tg not in datatag): continue;
        for img in entrylist:
            del dataframe[img][tg];
        remL.append(tg);
        datatag.remove(tg)
    return remL;
    

###################
###################
def InputDataEntryAdd(new=None, old=None, tags=None, entrytype=None, dataframe=None, entrylist=None, datatag=None):
    """Add the entry 'new' in dataframe (default SkZp_Par['inputdata']) and entrylist (default SkZp_Par['inputlist']) using eventually data from existing 'old' entry.

Parameters
----------
    new : str
        Name of the new entry
    old : str
        Existing entry of SkZp_Par['inputdata'] to be used as default values.
    tags : list, None
        List of tags to be copied in the new entry from the old one. None (default) means all; empty list means that all the filed will be set to None.
    entrytype : str
        Value for 'ENTRYTYPE' tag. None (default) to not change it.
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    entrylist : None, list
        list of the entries. None for SkZp_Par['inputlist']
    datatag : None, list
        List of the tags of input data. None for SkZp_Par['datatag']
Returns
-------
    Integer, None
        None if the entry is added without problems; if the entry already exists, its index in 'entrylist' is return.
""";
    _name_='InputDataEntryAdd';
    if(dataframe is None and not all(xx is None for xx in (dataframe, entrylist, datatag))): raise SkZpipeError("Error in given values: if `dataframe` is None also entrylist and datatag must be None!", exclocus=_name_);
    if(dataframe is None):  dataframe =bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(datatag is None):   datatag  =bpar.SkZp_Par['datatag'];
    if(not isinstance(new, str)): raise TypeError(_name_+": `new` {:} must be a str".format(str(new)));
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": `dataframe` must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": `entrylist` must be a list.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": `datatag` must be a list.");
    if(old is not None and old not in dataframe): raise KeyError(_name_+": `old` entry {:} does not exist!".format(old));
    if(tags is not None and not isinstance(tags, list)): raise TypeError(_name_+": `tags` must be a list. <{}>".format(tags));
    if(entrytype is not None and not isinstance(entrytype, str)): raise TypeError(_name_+": `entrytype` must be a str or None <{}>".format(entrytype));

    
    ret=entrylist.index(new) if(new in entrylist) else None;

    if(old):
        if(tags is None):
            tmpd=copy.deepcopy(dataframe[old]) 
        else:
            tmpd=dict().fromkeys(datatag);
            try:
                tmpd.update(dict((tag, dataframe[old][tag]) for tag in tags));
            except:
                raise KeyError(_name_+": Wrong value for a tag to be copied! Tag {tag} doesn't exist!".format(tag=tag));
    else:
        tmpd=dict().fromkeys(datatag);
    dataframe[new]=tmpd;
    dataframe[new]['NAME']=new;
    if(new not in entrylist): entrylist.append(new);
    if(entrytype): dataframe[new]['ENTRYTYPE']=entrytype
    else:
        etype=_opt.OptionGet('inputdata:tag:entrytype', otype='S')
        if(etype): dataframe[new]['ENTRYTYPE']=etype
    return ret;

###################
def InputDataEntryGet(entry=None, taglist=None, dataframe=None, raisexc=False):
    """Get the data of an entry from the database in 'dataframe' (default SkZp_Par['inputdata']). if `taglist` is provided, only the data of the tags in it will be returned.

Parameters
----------
    entry : str
        Name of the entry whose data has to be retrieved
    taglist : list
        Secuence of tags to extract. Default None for all
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    raisexc : bool
        Flag to set if raise an exception or just return an error value.

Returns
-------
    output : dict
        Dictionary with data of the entry
"""
    _name_='InputDataEntryUpdate';
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(entry, str)): raise TypeError(_name_+": 'entry' {:} must be a string".format(entry));
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(entry not in dataframe):
        if(raisexc):
            raise KeyError(_name_+": 'entry' {:} does not exist!".format(entry));
        else:
            print(_name_+": 'entry' {:} does not exist!".format(entry), file=bpar.SkZp_Par['stderr']);

    if(taglist):
        data=dataframe.get(entry);
        if(data):
            return dict((tag, data.get(tag)) for tag in taglist);
        return data;
    else:
        return dataframe.get(entry);

###################
def InputDataEntryUpdate(entry=None, newdata=None, dataframe=None):
    """Update an entry of the database in 'dataframe' (default SkZp_Par['inputdata']) with new data.

Parameters
----------
    entry : str
        Name of the entry to update
    newdata : dict
        Dictionary with the new data.
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
""";
    _name_='InputDataEntryUpdate';
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(entry, str)): raise TypeError(_name_+": 'entry' {:} must be a string".format(entry));
    if(not isinstance(newdata, dict)): raise TypeError(_name_+": 'newdata' must be a dictionary");
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(entry not in dataframe): raise KeyError(_name_+": 'entry' {:} does not exist!".format(entry));
    if(any(tag not in dataframe[entry] for tag in newdata)): raise SkZpipeError("A tag in 'newdata' is not present in the database! ({})".format(newdata), exclocus=_name_);
    if('NAME' in newdata and newdata['NAME']!=dataframe[entry]['NAME']): 
        raise SkZpipeError(f"It's not possible to change the value of 'NAME' tag! You have to create a new entry! ({newdata})", exclocus=_name_);

    dataframe[entry].update(newdata);

###################
def InputDataEntryDelete(name=None, dataframe=None, entrylist=None):
    """Delete the entry 'name' from dataframe (default SkZp_Par['inputdata']) and entrylist (default SkZp_Par['inputlist']);

Parameters
----------
    name : str,list,tuple (iterable)
        Name of the entry
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    entrylist : None, list
        list of the entries. None for SkZp_Par['inputlist']
"""
    _name_='InputDataEntryDelete';
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(isinstance(name,str)): name=[name];
    for img in name:
        if(img in entrylist):
            del(dataframe[img])
            entrylist.remove(img)


###################
###################
def InputDataIntegrityCheck(dataframe=None, entrylist=None, datatag=None, raisexc=True):
    """check the integrity of the internal database 'dataframe' (default SkZp_Par['inputdata']), 'entrylist' (default SkZp_Par['inputlist']), datatag (default SkZp_Par['datatag'])

Parameters
----------
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    entrylist : None, list
        list of the entries. None for SkZp_Par['inputlist']
    datatag : None, list
        List of the tags of input data. None for SkZp_Par['datatag']
    raisexc : bool
        Flag to set if raise an exception or just return an error value.
Returns
-------
    Integer, str
        0 if there are no problems. 1 if 'dataframe' has keys not present in 'entrylist'. 2 if 'entrylist' has entries not present in 'dataframe'. 
        If a entry has a difference 
"""
    _name_='InputDataIntegrityCheck';
    if(dataframe is None and not all(xx is None for xx in (dataframe, entrylist, datatag))): raise SkZpipeError("Error in given values: if 'dataframe' is None also entrylist and datatag must be None!", exclocus=_name_);
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": 'datatag' must be a list.");

    setkeys=set(dataframe);
    setlist=set(entrylist);
    settags=set(datatag);

    diff=setkeys-setlist;
    if(diff):
        if(raisexc): raise SkZpipeError(f"'dataframe' has keys not present in 'entrylist'!   <{diff}>", exclocus=_name_);
        else:
            print(f"{_name_}: Error: 'dataframe' has keys not present in 'entrylist'!   <{diff}>", file=bpar.SkZp_Par['stderr']);
            return 1;
    diff=setlist-setkeys;
    if(diff):
        if(raisexc): raise SkZpipeError(f"'entrylist' has entries not present in 'dataframe'!   <{diff}>", exclocus=_name_);
        else:
            print(f"{_name_}: 'entrylist' has entries not present in 'dataframe'!   <{diff}>", file=bpar.SkZp_Par['stderr']);
            return 2;
    for img in entrylist:
        settagI=set(dataframe[img]);
        diff=settags-settagI;
        if(diff):
            if(raisexc): raise SkZpipeError(f"The entry {img} has less tags!   <{diff}>", exclocus=_name_);
            else:
                print(_name_, f"Error: The entry {img} has less tags!   <{diff}>", file=bpar.SkZp_Par['stderr']);
                return img;
        diff=settagI-settags;
        if(diff):
            if(raisexc): raise SkZpipeError(f"The entry {img} has more tags!   <{diff}>", exclocus=_name_);
            else:
                print(_name_, f"Error: The entry {img} has more tags!   <{diff}>", file=bpar.SkZp_Par['stderr']);
                return img

    return 0

###################
    
#####################
def InputDataCheckFix(runlist=None, entrylist=None, dataframe=None, datatag=None):
    """Check InputData values and fix format and values (it sould be run at the end of the data retrievement).

Parameters
----------
    runlist : None, list
        list of the entries to process. None for SkZp_Par['runlist']
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags in input data. None for SkZp_Par['datatag']
"""
    _name_='InputDataCheckFix'
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(runlist is None): runlist=bpar.SkZp_Par['runlist'];
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    if(not isinstance(runlist, list)): raise TypeError(_name_+": 'runlist' must be a list.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": 'datatag' must be a list.");

    for fn in entrylist:
        if(not dataframe[fn]['CHIP']):
            chipnum=_opt.OptionGet('inputdata:tag:chip')
            if(chipnum not in (None,'')): dataframe[fn]['CHIP']=chipnum

        if(_opt.OptionGet('inputdata:aliasingfix', otype='Flg')):
            if(dataframe[fn]['INSTRUMENT'] in _db.SkZp_DB['alias']):
                for key in _db.SkZp_DB['alias'][dataframe[fn]['INSTRUMENT']]:
                    if(dataframe[fn][key] in _db.SkZp_DB['alias'][ dataframe[fn]['INSTRUMENT'] ][key]):
                        dataframe[fn][key]= _db.SkZp_DB['alias'][ dataframe[fn]['INSTRUMENT'] ][key][ dataframe[fn][key] ]
        
#        lookupfield(dataframe[fn]['OBJECT'], _db.SkZp_DB['standardfield'].keys())

        if(isinteger(dataframe[fn].get('BITPIX'))):
            if(abs(dataframe[fn]['BITPIX'])!= 32 and dataframe[fn]['ENTRYTYPE']=='image:sci'):  
                print(f"{fn}: The image is not float(32bit): BITPIX={int(dataframe[fn]['BITPIX']):d}! There could be problems with DAOPhot!\n", file=bpar.SkZp_Par['stdout']);
        else:  print(f"{_name_}: The image {fn}  has not tag BITPIX defined correctly ({dataframe[fn].get('BITPIX')})! Rerun after header-data retrievement! \n", file=bpar.SkZp_Par['stdout']);

        tmpD={}
        for tag in ('OFFSET', 'OFFSETXY', 'SCALE'):
            if(dataframe[fn].get(tag)):
                tagv=dataframe[fn][tag]
                if(not isinstance(tagv, tuple) or all(isinstance(x,float) for x in tagv)):
                    dataframe[fn][tag]=bpar.SkZp_Par['datatagconvert'][tag](tagv)
                tmpD[tag]=dataframe[fn][tag]

        
        if(tmpD.get('SCALE') and tmpD.get('OFFSET')): 
            dataframe[fn]['OFFSETXY']=( round(tmpD['OFFSET'][0]/tmpD['SCALE'][0],6), round(tmpD['OFFSET'][1]/tmpD['SCALE'][1],6) ) 
        else: dataframe[fn]['OFFSETXY']=None;
        #
    if('OFFSETXY' not in datatag): datatag.append('OFFSETXY');

    return;

#####################
def InputDataInfo(entrylist=None, dataframe=None, datatag=None):
    """Check InputData values and fix format and values (it sould be run at the end of the data retrievement).

Parameters
----------
    entrylist : None, list
        List of input data entries. None for SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags in input data. None for SkZp_Par['datatag']
"""
    _name_='InputDataInfo'
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": 'datatag' must be a list.");

    print(f"InputData Info:\n\tnumber of entries: {len(entrylist)}\n[{entrylist[:10]} ... {entrylist[-10:]}]\tnumber of tags: {len(datatag)}\ndatatag\n", file=bpar.SkZp_Par['stdout'])
#    for fn in entrylist:
#        if(not dataframe[fn]['CHIP']):
#            chipnum=_opt.OptionGet('inputdata:tag:chip')



#################################
##=  Get Data From Input File =##
#################################
def InputDataExternalLoad(inputfile=None, header=None, comment=None, minlen=1, delimiter='', stripheader=True):
    """Load input-data from `inputfile`, if it does not already contain valid data, and return a tuple 
  with  header and data.

Parameters
----------
    inputfile : str, list of str, None
        The input external source: filename, list of filename, pattern for glob. 
        If None or '-' (standard input), it is selected accordingly to the way the code is run (interactive 
        shell o stand-alone script, using parameter 'script'). 
        First it is used the filename from option 'inputdata:file'.
        Otherwise:
          if run as stand-alone script, it will use filenames passed in from command line or standard input;
          if run from interactive shell, it is set as list of images in the current directory (images 
            defined with internal parameter 'fitsextension', list retrieved with glob)
        Strings will be condidered as a filename or as pattern for glob if they contain * or ? or [.
        If several filename are provided as input, they need to have same format and only the first header 
        will be stored to be used later (to get tag names).
    header : none, str, int
        Describe the header of the input:
          int : number of initial lines to be considered as header
          str : initial pattern that identifies the header. Header consists of just all the first 
                lines that starts with this pattern. Method str.startswith is used to detect the pattern.
          None : use 'headerfilepattern' parameter.
    comment : str
        Initial pattern that identifies a comment-out line that have not to be read. 
        If None, it uses 'commentpattern' parameter.
    minlen : int
        Minimum length of a valid space-stripped input line.
    delimiter : None or str
        The string used to separate values.
    stripheader : bool
        If to strip the header lines from `comment` or `header` initial patterns

Returns
----------
    out : tuple of 2 objects
        Tuple with: header data, input data .
        Header data can be a list of header lines or None;
        Input data can be a list of list of data.

  """;
    _name_='InputDataExternalLoad';
    if(comment is None): comment=bpar.SkZp_Par['commentpattern'];
    if(header is None):  header =bpar.SkZp_Par['headerfilepattern'];
    if(not isinstance(header,(str,int))): raise TypeError(_name_+": 'header' must be a string, a no-negative integer.");
    if(isinstance(header,int) and header<0): raise TypeError(_name_+": 'header' must be a no-negative integer or a string.");
    if(not isinstance(comment,str)): raise TypeError(_name_+": `comment` must be a string")
    if(not isinstance(minlen,int)): raise TypeError(_name_+": `minlen` must be a positive integer")
    if(delimiter is not None and not isinstance(delimiter,str)): raise TypeError(_name_+": `delimiter` must be None or a string")
    if(delimeter == ''):
        delimeter=_opt.OptionGet('inputdata:delimeter','S')
    globpatt='[*?[]' 
  
   ##%%%%%##
    def _IDEL_read(inputfile):
        headerlines,datalines, files=[],[], []
        fname=inputfile[0]
        if(fname=='-'): fname='<stdin>'
        with sys.stdin if(fname=='<stdin>') else open(fname) as f_in:
           #READING HEADER
            if(isinstance(header,int)):
                headerlines=[ f_in.readline().strip() for ii in range(header)]
            else:
                line=f_in.readline().strip();
                #while(re.search('^'+header, line)): #re.search is better than str.startswith since can use matching patterns
                while(line.startswith(header)): #
                    headerlines.append(line.lstrip(header) if(stripheader) else line)
                    #headerlines.append(line);
                    line=f_in.readline().strip();
             #next line is read: to check if a valid data line
                if(not line.startswith(comment)): 
                    if(len(line)>=minlen):
                        datalines.append(line.split(delimiter) );
        
           #READING DATA
            for line in f_in:
                line=line.strip();
                if(line.startswith(comment) or len(line)<minlen): continue;
                datalines.append( line.split(delimiter) )

        hlenS=set( len(x) for x in headerlines )
        lenS=set( len(x) for x in datalines )
        if(len(lenS)>1): raise SkZpipeError(f"Data lines in input files have not the same amount of fields.   <{lenS}>", exclocus=_name_)

        #update parameter 'inputfiles'
        bpar.SkZp_Par['inputfiles'].append( (fname, len(headerlines), len(datalines)) )

        if(tuple(lenS)[0]>=len(bpar.SkZp_Par['def:datatag'])):
            if(_opt.OptionGet('inputdata:appendupdate','Flg')):
                bpar.SkZp_Par['not2update'].extend([x[0] for x in datalines])
            
      
        for fname in inputfile[1:]: #FOLLOWING files: Not considering header
            if(fname=='-'): fname='<stdin>'
            with sys.stdin if(fname=='<stdin>') else open(fname) as f_in:
               #READING DATA Only
                tmpl=[]
                for line in f_in:
                    line=line.strip();
                    if(line.startswith(comment) or len(line)<minlen): continue;
                    tmpl.append( line.split(delimiter) )
      
            lenSt=set( len(x) for x in tmpl )
            if(len(lenSt)>1): raise SkZpipeError(f"Data lines in input file {fname} have not the same amount of fields.", exclocus=_name_)
            lenS=lenS.union(lenSt)
            if(len(lenS)>1): raise SkZpipeError(f"Data lines in input files have not the same amount of fields.   <{lenS}>", exclocus=_name_)

            datalines.extend(tmpl)
            #update parameter 'inputfiles'
            bpar.SkZp_Par['inputfiles'].append( (fname, -1, len(tmpl)) )
            
        bpar.SkZp_Par['store4later']['inputdata']=(headerlines, datalines)

        return (headerlines, datalines)
   ##%%%%%##

    if(inputfile is None or inputfile =='-'): #undefined or take standard input (= stdin for script, option or glob for ishell)
          #First mode: stand-alone script
        if(bpar.SkZp_Par['script']['mode']=='alone' and len(sys.argv)>1): #if there are arguments passed in from command line
            if(all(x=='-' or get_num_lines(x)>=0 for x in sys.argv[1:])):
                if(inputfile=='-' and '-' not in sys.argv[1:]):
                    inputfile=['-']+sys.argv[1:]    #  LIST of inputfiles
                else:
                    inputfile=sys.argv[1:]    #  LIST of inputfiles
        elif(bpar.SkZp_Par['script']['mode']=='alone' and inpufile=='-'): #if no argv but it is said to read stdinput
            pass; #keep it
  
        elif(not check_file([_opt.OptionGet('inputdata:file')], minline=1, raisexc=False) ): 
            inputfile=_opt.OptionGet('inputdata:file')     # inputfile from opt
        else:
            tmpl=sorted(glob.glob('*'+bpar.SkZp_Par['fitsextension']))  #list of images
            if(tmpl):
                bpar.SkZp_Par['inputfiles'].append( ('<glob FITS>', -1, len(tmpl)) )
                return (None, [ [x] for x in tmpl ])     #  list of entries  !!!
            tmpl=sorted(glob.glob('*'+bpar.SkZp_Par['script']['mosaicextension']))  #list of mosaic
            if(tmpl):
                bpar.SkZp_Par['inputfiles'].append( ('<glob MOSAIC>', -1, len(tmpl)) )
                return (None, [ [x] for x in tmpl ])     #  list of entries  !!!
            raise SkZpipeError("`inputfile` is undefined and no image or mosaic in current directory", exclocus=_name_) #RAISE !!!
  
   ################
    elif(isinstance(inputfile, list)):   ## RETURN directly, no change to inputfile var
        if( all( isinstance(x, str) for x in inputfile  ) ):
            #list of str
                if(any( '\n' in x.strip() for x in inputfile)): #has \n inside
                    raise SkZpipeError("`inputfile` is a list of multi-line strings", exclocus=_name_) #RAISE !!!

                if(any( x.endswith('\n') for x in inputfile)): #some terminate with \n
                    headerlines,datalines=[],[]
                    for x in inputfile:
                        x=x.strip()    
                        if(comment and x.startswith(comment) ):
                            headerlines.append(x.lstrip(comment) if(stripheader) else x)
                        elif( header and isinstance(header,str) and x.startswith(header) ):
                            headerlines.append(x.lstrip(header) if(stripheader) else x)
                        else: break
                    for x in inputfile:
                        x=x.strip()    
                        if(len(x)<minlen or (comment and x.startswith(comment))):
                            continue;
                        else:
                            datalines.append(x)
                    bpar.SkZp_Par['inputfiles'].append( ('<list>', len(headerlines), len(datalines)) )
                    return (headerlines, datalines);    #  list of entries ????
  
                if(get_num_lines(inputfile[0])>=0): #First ones are no-empty but no fits
                    if(all(get_num_lines(x)>=0 for x in inputfile) #All are no-empty files
                    and all( x.endswith(bpar.SkZp_Par['fitsextension']) or x.endswith(bpar.SkZp_Par['mosaicextension']) for x in inputfile) ): #all end with .fit or .fits
                        bpar.SkZp_Par['inputfiles'].append( ('<list>', -1, len(inputfile)) )
                        return (None, [[x] for x in inputfile]) #  list of images or mosaics => list of entries !!!
  
                elif(all(get_num_lines(x)==-1 for x in inputfile)): #none is a existing file
                    if(all(get_num_lines(x+bpar.SkZp_Par['fitsextension'])>0 for x in inputfile)): #All are basename of images
                        bpar.SkZp_Par['inputfiles'].append( ('<list>', -1, len(inputfile)) )
                        return (None, [[x] for x in inputfile]) #  list of images or mosaics => list of entries !!!
  
                    elif(all(re.search(globpatt, x) for x in inputfile)): #list of patterns
                        tmpl=[]
                        for x in inputfile:
                            tmpl.extend( sorted(glob.glob(x)) )
                        bpar.SkZp_Par['inputfiles'].append( ('<glob>', -1, len(tmpl)) )
                        return (None, [[x] for x in tmpl])  #  list of entries  !!!
  
                    else: ## List of input line????
                        headerlines,datalines=[],[]
                        for x in inputfile:
                            x=x.strip()    
                            if(comment and x.startswith(comment) ):
                                headerlines.append(x.lstrip(comment) if(stripheader) else x)
                            elif( header and isinstance(header,str) and x.startswith(header) ):
                                headerlines.append(x.lstrip(header) if(stripheader) else x)
                            else: break
                        for x in inputfile:
                            x=x.strip()    
                            if(len(x)<minlen or (comment and x.startswith(comment))):
                                continue;
                            else:
                                datalines.append(x.split(delimiter) )
                        bpar.SkZp_Par['inputfiles'].append( ('<list>', len(headerlines), len(datalines)) )
                        return (headerlines, datalines);    #  list of entries ????
                else:
                    raise SkZpipeError("`inputfile` is a list of a mix of existing and not existing/empty files", exclocus=_name_) #RAISE
        #elif( all( not isinstance(x, list) for x in inputfile  ) ):
        elif( all( isinstance(x, list) for x in inputfile  ) ):  
            bpar.SkZp_Par['inputfiles'].append( ('<list>', -1, len(inputfile)) )
            return (None, inputfile)  #  list of list/entries  !!!
  
        elif( any( isinstance(x, str) for x in inputfile  ) ):
            raise SkZpipeError("`inputfile` is a list of a mix of string and other objects", exclocus=_name_) #RAISE !!!
        else:
            raise SkZpipeError("`inputfile` is a list of a mix of objects not strings. Not regular", exclocus=_name_) #RAISE !!!

    #if not str/list : it is the final tuple, update parameter 'inputfiles', => 
    if(not isinstance(inputfile, (str,list))): 
        bpar.SkZp_Par['inputfiles'].append( ('<argv>', -1, len(inputfile)) )
        return inputfile

    # => List
    if(not isinstance(inputfile, list)): inputfile=[inputfile]

    # if there is glob pattern => (None, list of files)
    if(any( re.search(globpatt, x) for x in inputfile )): 
        tmpl=[]
        for x in inputfile:
            tmpl.extend( sorted(glob.glob(x)) )
        bpar.SkZp_Par['inputfiles'].append( ('<glob>', -1, len(tmpl)) )
        return (None, [[x] for x in tmpl])  #   list of entries  !!!
  
    #check if input files really exit
    check_file([x for x in inputfile if(x!='-')])
  
    #Finally actually read data! -> (header, data)
    return _IDEL_read(inputfile)


#######################
def InputDataRetrieve(inputfile=None, taglist=None, tagconv=None, mode='w', listof='image',  runlist=None, entrylist=None, dataframe=None, datatag=None, verb=False):
    """Reads input from `inputfile` and retrieves the image information.
    It skips entries of not-existing images or other type of entries not well defined (using 
    the tag 'ENTRYTYPE').

Parameters
----------
    inputfile : str, None, tuple of 2 lists
        The input information. If it is '-' or None (default) then it will read accordinly to how 
        the code is run (see InputDataExternalLoad). If it is another string, it will be used 
        as a filename. It can be the output of InputDataExternalLoad (tuple of two lists).
    taglist : list of str
        List of tag of the data. If it is not given, it will use the very first line as list of tags. 
        It is suggested to comment out this line with a '# '
    tagconv : list
        List of conversion specifiers of the tags. If it is not given, it will use the second line as 
        list of format. It is suggested to comment out this line with a '#% '. Usable specifiers: int, 
        float, str.
        mode : str
        'w' to create new set of data, 'a' to append/update the set of data,
    listof : str
        If `inputfile` contains information about images: 'image'
        If `inputfile` contains list of mosaic names: 'mosaic'
    runlist : None, list
        List of the entries to process. None for parameter 'runlist'
    entrylist : None, list
        List of input data entries. None for parameter 'inputlist'
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for parameter 'inputdata'
    datatag : None, list
        List of the tags in input data. None for parameter 'datatag'
    verb : bool
        Verbosity flag

Tags
----------
    Mandatory tags for images:\n\t  NAME=name of the image witout extension .fits\n\t  FWHM=seeing/fwhm
    Other tags see documentation for parameter 'datatag'  
 
Returns
-------
    Number of entries.

Functions
---------
    InputDataExternalLoad

""";
    _name_='InputDataRetrieve';
    if(inputfile is not None and not isinstance(inputfile,(str, tuple)) ): raise TypeError(f"{_name_}: `inputfile` must be a string or None or a tuple <{inputfile.__class__}>");
    if(not re.search('[wa]', mode)): raise ValueError(_name_+": Wrong value for `mode` ('w' to create a new set, 'a' to append/update) <{}>".format(mode));
    if(not isinstance(listof,str)): raise TypeError(_name_+": `listof` must be a string ('image' or 'mosaic') <{}>".format(listof));
    if(not any( x in listof for x in ('image', 'mosaic'))): raise ValueError(_name_+": Wrong value for `listof` <{}>".format(listfor));
  
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": 'entrylist' must be a list.");
    if(runlist is None): runlist=bpar.SkZp_Par['runlist'];
    if(not isinstance(runlist, list)): raise TypeError(_name_+": 'runlist' must be a list.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": 'datatag' must be a list.");
  
    inputdata={};
    inputlist=[];
   #END initialization
  
    stemp= inputfile if(isinstance(inputfile, str) or all(isinstance(x, str) for x in inputfile)) else ''
    print(f"Reading input data   <{stemp}>" , file=bpar.SkZp_Par['stdout']);
    flush_out()
  
   ##%%%%%##
    def _IDRETR_readtag(line=''):
        """function to read the header with tag list.
Parameters
----------
    line : str
        Line of text with sequence of tags.
Return
------
    List of tags
""";
        _name_='InputDataRetrieve:readtag';
        tagl=line.strip('# ').upper().split();   ## strip('# ') => remove from start and end every '#' or ' '
#        for ii in range(len(tagl)):
#            tagl[ii]=tagl[ii].upper(); #USELESS
        missing=[tag for tag in bpar.SkZp_Par['datatag0'] if(tag not in tagl ) ]
        if(missing): 
            if('ENTRYTYPE' in missing and _opt.OptionGet('inputdata:tag:entrytype', otype='S')):
                pass
            else:
                raise SkZpipeError("missing needed tag ("+",".join(missing)+f") in {tagl}\n"+bpar.SkZp_Par['_doc_']['datatag'], _name_);
        return tagl;
   ##%%%%%##
    def _IDRETR_line(line='', tag=[]):
        """function to read a line from input data source, matching the tags in 'tag' with info from 'line'.
Returns: dict with InputData
Parameters
----------
    line : str
        Text with the image information.
    tag : list
        List of the tags corresponding to info in 'line' (same order).
Return
------
    Dictionary with image retrieved information. The values are in the type given by parameter 'datatagtype'.
    """;
        _name_='InputDataRetrieve:line';
        if(isinstance(line,str)): 
            line=line.strip()
            if(line.startswith('(') and line.endswith(')')):
                tmpl=line[1:-1].split(', ')
            else:
                tmpl=line.split() 
        else: tmpl=line 
        dataframe=dict(zip(tag, [None if(datum=='None') else datum for datum in tmpl ]));
  
        
        dataframe['NAME']=remove_extension(dataframe['NAME'], (bpar.SkZp_Par['fitsextension'], bpar.SkZp_Par['mosaicextension']))
        if('.' in dataframe['NAME']): raise SkZpipeError(_name_+": NAME field has a dot inside: "+dataframe['NAME']);
        tmpd=bpar.SkZp_Par['def:dataframe'].copy(); #take a copy of the default values
        tmpd.update(dataframe); #update the default values with the given values
        dataframe=tmpd;
  
        instr=_opt.OptionGet('inputdata:instrument', otype='S'); #if instrument is provided
        if(instr):
            if(_opt.OptionGet('inputdata:instrumentset','Flg') or not dataframe['INSTRUMENT'] ):
                dataframe['INSTRUMENT']=instr;  #then use this value
  
       #fix the value according the type
        for tag in dataframe:
            if(dataframe[tag] == 'None'): dataframe[tag]=None
            if(dataframe[tag] is not None and tag in bpar.SkZp_Par['datatagtype']):
                try:
                    if(callable(bpar.SkZp_Par['datatagconvert'][tag])):
                        dataframe[tag]=bpar.SkZp_Par['datatagconvert'][tag](dataframe[tag]);
                    elif(isinstance(bpar.SkZp_Par['datatagconvert'][tag], str)):
                        tmpt=(dataframe[tag],) if(isinstance(dataframe[tag], str)) else tuple( dataframe[tag] );
                        dataframe[tag]=bpar.SkZp_Par['datatagconvert'][tag].format(*tmpt);
                except:
                    print(dataframe['NAME'], tag, dataframe[tag], file=bpar.SkZp_Par['stdout']);
                    raise;
            
        return dataframe;
   ##%%%%%##
  
    if(taglist is None): 
        taglist=_opt.OptionGet('inputdata:taglist')

    if(not taglist): ##cannot be None
        (hdrL, dataL)=InputDataExternalLoad(inputfile=inputfile, header=1, comment=None, minlen=3);  #from InputDataRetrieve
        if('image' in listof):
            lenT=tuple(set(len(x) for x in dataL))
            if(len(lenT)>1): raise SkZpipeError(f"Inputdata  has not uniform length.   <{lenT}>", exclocus=_name_);
            elif(lenT[0]==1):
                taglist=['NAME']
            else:
                taglist=_IDRETR_readtag(hdrL[0]);
        else: taglist=['NAME']
    else: 
        (hdrL, dataL)=InputDataExternalLoad(inputfile=inputfile, header=0, comment=None, minlen=3);  #from InputDataRetrieve
  
    if(taglist is not None):
        if(isinstance(taglist, list)):
            taglist=[x.upper() for x in taglist] #if empty, no cycle
            bpar.SkZp_Par['datatag0missing']=set(bpar.SkZp_Par['datatag0'])-set(taglist);
            if(bpar.SkZp_Par['datatag0missing']):
                print(f"{_name_}: Warning! Some fundamental tags are missing {bpar.SkZp_Par['datatag0missing']} <{taglist}>", file=bpar.SkZp_Par['stderr'])
                if('ENTRYTYPE' in bpar.SkZp_Par['datatag0missing'] and _opt.OptionGet('inputdata:tag:entrytype', otype='S')):
                    print(f"{_name_}: Missing fundamental tag 'ENTRYTYPE' obtained from options", file=bpar.SkZp_Par['stderr'])
                    

        else:
            raise SkZpipeError("taglist must be a list or not defined (=None)", _name_);
  
    
    style=_opt.OptionGet('inputdata:style', 'S')
    for line in dataL:
        if(style=='txt'):
            tmpd=_IDRETR_line(line, taglist);  #inputline + tag = dict
        else: raise SkZpipeError(f"Wrong value for option 'inputdata:style'.   <{style}>", exclocus=_name_);
       
      #
        if(tmpd['NAME'] in inputlist):
            print(f"\t!!!The entry {tmpd['NAME']} is already present! Overwriting the information!", file=bpar.SkZp_Par['stderr']);
            inputdata.update({tmpd['NAME']:tmpd});
        else:
            isFITS=fits.isfits(line[0])
            if(isFITS['nhdu']>0): #has HDU
                inputdata.update({tmpd['NAME']:tmpd})
                inputlist.append(tmpd['NAME'])
            elif(glob.glob(tmpd['NAME']+'.*')):  #it is the basename of something
                #if(isinstance(tmpd.get('ENTRYTYPE'),str)):
                #    if('cat' in tmpd['ENTRYTYPE']):
                    inputdata.update({tmpd['NAME']:tmpd})
                    inputlist.append(tmpd['NAME'])
            else: 
                if(verb): print(f"\t!!!The entry {tmpd['NAME']} is not valid (neither a FITS or a basename). Rejecting!", file=bpar.SkZp_Par['stderr'])
                
    
    if(mode=='w'):
        dataframe.clear();
        dataframe.update(inputdata);
        entrylist[:]=inputlist;
        runlist[:]=inputlist.copy();
    elif(mode=='a'):
        dataframe.update(inputdata);
        for entry in inputlist:
            if(entry not in entrylist): entrylist.append(entry);
            if(entry not in runlist): runlist.append(entry);
    #AND 'u' ?????
    nd=len(inputdata);
    inputdata={};
    inputlist=[];
    datatag[:]=taglist;
    #
    return nd;

    
##############
def InputDataDefaultFix(entrylist=None, dataframe=None, datatag=None, instr=None): #InputDataImageStatAdd
    """Fix the tag values (and initialize them) in inputdata to have values for all the tag in parameter 'def:datatag' and 'datatag'. If not set, the value of the tag is set to None.

Parameters
----------
    entrylist : None, list
        List of images. None for all entrylist in SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of inputdata. None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags of data that has to be write down. None for SkZp_Par['datatag']
    instr : str, None
        Name of the instrument used to produce the mosaic.
""";
    _name_='InputDataDefaultFix'
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, (list,tuple))): raise TypeError(_name_+": 'entrylist' must be a list or a tuple.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple.");
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe, dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");

  #Adding other tags from default list and set them to None
    for tag in bpar.SkZp_Par['def:datatag']:
        if(tag not in datatag):
            datatag.append(tag);
  ##%%%%%##
    def _roundvalue(tag=None, rnd=6):
        tmpv=dataframe[image].get(tag)
        if(tmpv):
            try:
                if(isinstance(tmpv, str) and ';' in tmpv):
                    dataframe[image][tag]=';'.join([str(round(float(x),rnd)) for x in tmpv.split(';')])
                elif(isinstance(tmpv, tuple)): 
                    dataframe[image][tag]=tuple(round(float(x),rnd) for x in tmpv)
                else: dataframe[image][tag]=round(float(tmpv),rnd);
            except:
                raise
  ##%%%%%##
    bpar.SkZp_Par['instruments']={};
  #Initialization of default tag
    for image in entrylist:
        for tag in datatag:
            dataframe[image].setdefault(tag);
            if(dataframe[image][tag]==''): dataframe[image][tag]=None
            if(dataframe[image][tag] is not None and tag in bpar.SkZp_Par['datatagtype']):
                if(not isinstance(dataframe[image][tag], bpar.SkZp_Par['datatagtype'][tag])):
                        try:
                            dataframe[image][tag]=bpar.SkZp_Par['datatagconvert'][tag](dataframe[image][tag])
                        except:
                            raise TypeError(f"{_name_}: in entry '{image}' the tag '{tag}' has a wrong type and cannot be converted automatically.  <{bpar.SkZp_Par['datatagtype'][tag]}>");

#        if(dataframe[image]['IMGSTAT'] is None):
#        if(os.path.exists(image+".fits")):
#           statD=fits.statimage(image+'.fits');
#           dataframe[image]['IMGSTAT']="{:.1f};{:.2f}".format(statD['med'], statD['std']);
        tmpv=dataframe[image].get('INSTRUMENT');
        if(tmpv): 
            bpar.SkZp_Par['instruments'].setdefault(tmpv, 0);
            bpar.SkZp_Par['instruments'][tmpv]+=1;
      
        _roundvalue('SCALE')
        _roundvalue('OFFSET')
    


      #FIXING my mess!
        if(dataframe[image]['ENTRYTYPE']=='image'): dataframe[image]['ENTRYTYPE']='image:sci';
        if(dataframe[image]['ENTRYTYPE']=='sci-image'): dataframe[image]['ENTRYTYPE']='image:sci';
        if(dataframe[image]['ENTRYTYPE']=='stack-image'): dataframe[image]['ENTRYTYPE']='stack';
        etype=_opt.OptionGet('inputdata:tag:entrytype', otype='S')
        if(etype): dataframe[image]['ENTRYTYPE']=etype

    InputDataImageStatAdd(statkey=_opt.OptionGet('inputdata:imgstat'), ndigits=[1,1,2], singletag='IMGSTAT', override=False, entrylist=entrylist, dataframe=dataframe, datatag=datatag);

        
#  if(not _opt.OptionGet('inputdata:instrument') and len(bpar.SkZp_Par['instruments'])==1): _opt.OptionSet('inputdata:instrument',)=instr;




#############################
#= Extract hdu from mosaic =#
#############################

###
def ExtractFromMosaic(inputdata=None, mode='w', sortby=None, instr=None,  entrylist=None, dataframe=None, datatag=None, autoremove=True, entrytype='image:sci'):  
    """Extract images from a mosaic/multi-hdu FITS.

Parameters
----------
    inputdata : dict, list of dict, list of str, str, tuple of 2 list
        Input source: a filename ('-' for stadard input and/or using filenames passed through command 
        line) or a list of dictionaries or a dictionary, or a list the filename of the mosaics, or a 
        tuple of 2 list (output of InputDataExternalLoad: (header, datalines)).
        The format of the input file (or of datalines from InputDataExternalLoad) is:
            mosaic-filename  output-name  what-to-extract(list of chips, area, ...)
        The dictionary must have the forma:
            {'mosaic': mosaic-filename, 'outname': output-name, 'chip': what-to-extract}
          mosaic-filename : str
              it must contain the extension
          output-name : str
              It can contain shortcuts like:
                %f : filename of the mosaic;
                %F : a short version of the mosaic (instrument dependent; if not defined, just like %f);
                %w : workname stored in the option 'inputdata:workname';
                %n : sequential enumeration of the entries
          what-to-extract : 
              Format of input in file:
                A |-separated list of pairs of keyword and extractiong info, separated by a colon (option 
                'image:extract:select'). The key-words and extracting info must be:
                  ##: a comma-separated list of chip numbers;  or  a semicolon-separated list to describe 
                       an interval of chip numbers: #initial;#final[;step]. Default value for step is 1.
                  #n: a comma-separated list of chip ids/names (string)  or  a semicolon-separated list 
                       to describe an intervalof chip ids: prefix;#initial;#final;step. stap is optional 
                       and its default value for step is 1.
                  area: a semicolon-separated list of comma-separated lists giving equatorial coordinates 
                         of the center and radius in arcmin of the area to extract
                  part: a comma-separated list of part of the mosaic with names instrument dependent 
                         (e.g. stripes for VIRCAM)
                Same format can be used for option 'image:extract:select'.
              Format of input in dictionary (key 'chip'):
                a list of chip numbers or IDs; 
                a tuple or a list of tuples to define an interval of chips: (#initial, #final[, step]). 
                  Default value for step is 1. In the case of an interval of chip IDs, first element 
                  is the prefix, e.g. (prefix,#initial;#final[;step]).
                a dictionary with format {'key-word': info}. The pair key:values must be:
                  '##'    : a list of chip numbers; or a tuple to describe an interval (same as above).
                  '#n'    : a list of chip names; or a tuple to describe an interval (same as above).
                  'area' : a list of tuples or a tuple giving equatorial coordinates of the center and 
                            radius in arcmin of the area to extract
                  'part' : a list of part of the mosaic with instrument-dependent names (e.g. from 
                            a to b for stripes in VIRCAM)
    mode : str
        Mode for the actualization: 'w' to create new set of data, 'a' to append/update to an existing the set of data)

    sortby : str
        Header keys used to sort the data
    instr : str, None
        Name of the instrument used to produce the mosaic.
    entrylist : None, list
        List of input data entries. None for parameter 'inputlist'
    dataframe : None, dict
        Dictionary of input data (dictionary of dictionaries). None for parameter 'inputdata'
    datatag : None, list
        List of the tags in input data. None for parameter 'datatag'
    autoremove : bool
        Flag to remove automatically rejected images
    entrytype : str
        Value for the ENTRYTYPE tag

Returns
-------
    Tuple (list,dict) with the list of the images and a dictionary of dictionaries of the image info.

Functions
---------
    startime
    WaitStop
    namereplacepattern
    FitsHeaderInfoRetrieve
    InputDataExternalLoad

  """;
    _name_="ExtractFromMosaic";
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": `dataframe` must be a dict.");
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": `entrylist` must be a list.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": `datatag` must be a list.");
  
    #instr
    if(instr is not None  and not isinstance(instr,str)): raise TypeError(_name_+": `instr` must be a string, or None.");
    if(not instr):  instr=_opt.OptionGet('inputdata:instrument', otype='S');
    #mode
    if(not re.search('[wa]', mode)): raise ValueError(_name_+": Wrong value for `mode`: 'w' to create a new set, 'a' to append/update");
    #sortby
    if(sortby and not isinstance(sortby,str)): raise TypeError(_name_+": `sortby` must be a string, or None.");
    #inputdata
    if(isinstance(inputdata, tuple) and len(inputdata)==2 and isinstance(inputdata[1], list)): 
        inputdata=inputdata[1]  #if IDEL output, takes only dataline
    if(not isinstance(inputdata,(str, list, dict)) and not (isinstance(inputdata,tuple) and len(inputdata)==2)): 
        raise TypeError(f"{_name_}: `inputdata` must be a string, a list of strings, None, a list of dictionaries or a dictionary, or a tuple of two lists. <{inputdata.__class__}>");
  
    autoremove=bool(autoremove);
    if(_opt.OptionGet('debug', otype='Flg')): autoremove=False;
  
   ##%%%%%##
    def _EFM_fromstring(line=''):
        """Function for ExtractFromMosaic to translate string-selection info into dict for chip selection
        """
        _name_="ExtractFromMosaic";
        line=line.strip();
        if(not line): return {};
        tmpd=dict((key,[]) for key in ['#', 'part', 'area']);
        tmpl=line.split('|');
       #FIXING
        if(len(tmpl)==1 and not ':' in tmpl[0]):
            tmpl[0]="##:"+tmpl[0];
        for bit in tmpl:
            if(not ':' in bit): raise SkZpipeError("'chip' info from input file doesn't have the format key:value.", exclocus=_name_);
            (key,value)=bit.split(':');
            if(re.search('^#.*', key)):
                key=key[1:];
                if(not key or key=='#'): #List/tuple of chip numbers
                    if(';' in value):
                        chpl=value.split(';');
                        if(len(chpl)!=3): chpl+=[1];
                        chpl=[tuple(int(x) for x in chpl)];
                    else: chpl=[int(chp) for chp in value.split(',')];
                elif(key=='n'): #List/tuple of chip names
                    if(';' in value):
                        chpl=value.split(';');
                        if(len(chpl)!=4): chpl+=[1];
                        chpl=[ (chpl[0], )+tuple(int(x) for x in chpl[1:]) ];
                    else: chpl=value.split(',');
                tmpd['#'].extend(chpl);
            elif(key=='area'):
                tmpd['area'].extend([tuple( float(x) for x in xx.split(',') ) for xx in value.split(';') ]);
            elif(key=='part'):
                tmpd['part'].extend( value.split(','));
       #delete empty keys
        for key in list(tmpd.keys()):
            if(not tmpd[key]): del(tmpd[key]);
        return tmpd;
   ##%%%%%##
    outxt=f"{_name_}\nReading inputdata..."
    if(_opt.OptionGet('debug', otype='Flg')):
        startime(outxt);
    else:
        print(outxt, file=bpar.SkZp_Par['stdout']);
    
   ##INPUTDATA => list of dict
    if(inputdata is None or isinstance(inputdata,str) or (isinstance(inputdata,list) and all(isinstance(x,list) for x in inputdata)) ): #None, filename, list of list
     #FIRST: if from file, translate it into dict form
        if(inputdata is None or isinstance(inputdata,str)):
            inputdata=InputDataExternalLoad(inputfile=inputdata, header=None, comment=None, minlen=5)[1]; #just the data lines,  from ExtractFromMosaic
        tmpl=[]  
        for line in inputdata:
            tmpd={'mosaic':line[0], 'outname':None, 'chip':None}.copy();
            if(len(line)>1):
                tmpd['outname']=line[1];
                if(len(line)>2): 
                    tmpd['chip']="|".join(line[2:]);
            if(tmpd['outname'] in ('-', 'None')): 
                tmpd['outname']=None;
            if(isinstance(tmpd['chip'], str)):
                tmpd['chip']=_EFM_fromstring(tmpd['chip']);  ##%%% reading selction option from inputdata
            tmpl.append(tmpd);
        inputdata=tmpl
    elif(isinstance(inputdata,dict)): inputdata=[inputdata];
    elif(isinstance(inputdata,list) and all(isinstance(x,str) for x in inputdata)): inputdata=[{'mosaic':x} for x in inputdata];
  
   ###FROM NOW  inputdata = list of dicts with extracting information
    mosinfo={};
    chipselectopt=_EFM_fromstring(_opt.OptionGet('image:extract:select')); ##%%%  #Get rules from options and put them as dict.
  
   #Fixing inputdata and extracting info from mosaic header
    print("Fixing inputdata...", file=bpar.SkZp_Par['stdout']);
   #INPUTDATA DICT filling and fixing
    for inp in inputdata:
        if(not isinstance(inp, dict)): raise TypeError(_name_+": Wrong type for 'inputdata' (it should  be a list dict by now).");
       #Fix missing entry in dictionary
        for tag in ('outname','chip'):
            if(tag not in inp): inp[tag]=None;
        if(inp['outname']=='-'): inp['outname']=None;
        if(not all(tag  in inp for tag in ('mosaic','outname','chip'))): raise SkZpipeError("inputdata doesn't have all the needed keys", exclocus=_name_);
    
       #Fix 'chip' entry: From list/tuple to dict {'#':[], 'part':[], 'area':[]}
        #No value => default
        if(not inp['chip']): inp['chip']=copy.deepcopy({'#':[], 'part':[], 'area':[]});
        #List
        if(isinstance(inp['chip'], list)): inp['chip']={'#':inp['chip']};
        #Tuple  => Interval of chips (start, end, step=1)
        elif(isinstance(inp['chip'], tuple)):
            if(isinstance(inp['chip'][0], str)):
                inp['chip']= [inp['chip']+(1,)] if(len(inp['chip'])<4) else [inp['chip']];
            else:
                inp['chip']= [inp['chip']+(1,)] if(len(inp['chip'])<3) else [inp['chip']];
            inp['chip']={'#': inp['chip']};
    
        # 'chip' entry NOW should be only a dict and its entry '#' a list
        if(not isinstance(inp['chip'], dict)):  raise TypeError(_name_+": Wrong type for 'chip' entry in 'inputdata': it should  be a dict by now. > {:} <".format(str(inp['chip'])) ); 
    
       # '#': List of chip
       #Opt chipselect : #
        if(chipselectopt.get('#')): inp['chip']['#']=chipselectopt['#'].copy();
        if('#' in inp['chip']):  #Starting to transform the extracting info into just list of chips
            if(not isinstance(inp['chip']['#'], list)): raise TypeError(_name_+": '#' entry of 'chip' entry in 'inputdata' should  be a list by now."); 
            chpl=[];
            for chp in inp['chip']['#']: #merging all the entries in a single list
                if(isinstance(chp, tuple)): 
                    if(isinstance(chp[0], str)):
                        chpl.extend([ chp[0]+str(x) for x in range(chp[1], chp[2]+1, chp[3]) ]);
                    else:
                        chpl.extend(list( range(inp['chip'][0], inp['chip'][1]+1, inp['chip'][2] if(len(inp['chip'])==3) else 1)) );
                else: chpl.append(chp);
            inp['chip']['#']=chpl;
        #all the entry are list
    
       # 'part': List of sensor part
       # 'area': List of sky areas
        for key in ('part', 'area'):
            inp['chip'].setdefault(key, []);
            if(not isinstance(inp['chip'][key], list)): inp['chip'][key]=[ inp['chip'][key] ];
            if(chipselectopt.get(key)): inp['chip'][key].extend( chipselectopt[key].copy() );
      
    
       #NOW 'chip':'#' is a list of chip: 'area' and 'part' will refer to this chip
    
        #Removing empty values
        for key in ['#', 'part', 'area']:
            if(not inp['chip'][key]): del(inp['chip'][key]);
    
       #Extracting info from header
        if(not mosinfo.get(inp['mosaic'])):
            check_file(inp['mosaic']);
            mosinfo[inp['mosaic']]=FitsHeaderInfoRetrieve(image=inp['mosaic'], headertype='mos')[0];
      
  # Sort by hdr entry defined in 'sortby' variable
    if(sortby):
        print("Sorting input list by header card {:}.".format(tag), file=bpar.SkZp_Par['stdout']);
        if(isinstance(sortby,str)): inputdata.sort(key=lambda inp : mosinfo[ inp['mosaic'] ][sortby]);
  
  ####################################################
  # Starting actual selection
    for inp in inputdata:
        WaitStop();
       #get list of EXTNAME in the mosaic
        lstext=fits.listextname(inp['mosaic']); # For chip selection
        nhdu=len(lstext); # For chip selection
        instrm=instr;
        if(not instrm): instrm=mosinfo[inp['mosaic']].get('INSTRUMENT');
    
      ###############  
      #Selecting chip
    
       #set 'chip' default= all (mosaic dependent)
        if(not inp['chip']): inp['chip']={'#':list(range(1,nhdu))};
        elif('#' not in inp['chip']): inp['chip']['#']=list(range(1,nhdu));
        elif( not inp['chip']['#']): inp['chip']['#']=list(range(1,nhdu));
        else:
            for chp in inp['chip']['#']:
                #This check should be correct, without bug
                if(isinstance(chp, int)):
                    if(chp<1 or chp>=nhdu): raise ValueError(_name_+": Wrong value for chip ({:d}) in mosaic {:}".format(chp, inp['mosaic']));
                elif(isinstance(chp,str)):
                    if(chp not in lstext): raise ValueError(_name_+": Wrong value for chip/extname ({chip}) in mosaic {mos} {extl}".format(chip=chp, mos=inp['mosaic'], extl=lstext));
                else: raise TypeError(_name_+": Wrong type for 'chip' key for mosaic {:}.".format(inp['mosaic']));
    
       #by area
        if('area' in inp['chip'] and inp['chip']['area']):
            newchipl=[];
            for area in inp['chip']['area']:
              (xx,yy)=mathfunct.eq2plane(radec=area[:2], radec0=(mosinfo[inp['mosaic']]['RA'], mosinfo[inp['mosaic']]['DEC']), theta=_db.SkZp_DB['chipselect'][instrm]['posang'](mosinfo[inp['mosaic']]));
              chipl=[];
              for chip in inp['chip']['#']:
                  (xpos,ypos)=_db.SkZp_DB['chipselect'][instrm]['pos']({**mosinfo[inp['mosaic']], 'CHIP':chip});
                  if((xpos-xx)**2+(ypos-yy)**2<area[2]**2): chipl.append(chip);
              newchipl.extend(chipl);
            inp['chip']['#']=newchipl;
      
       #by being in a particular 'part' of the mosaic
        if('part' in inp['chip'] and inp['chip']['part']):
            newchipl=[];
            for part in inp['chip']['part']:
                newchipl.extend([ chip for chip in inp['chip']['#'] if( part == _db.SkZp_DB['chipselect'][instrm]['part']({**mosinfo[inp['mosaic']], 'CHIP':chip}) ) ]);
            inp['chip']['#']=newchipl;
          
  
  ################################## 
  # Check uniformity in Observation Sets
  
    if(_opt.OptionGet('image:setcheck', 'Flg') or _opt.OptionGet('image:uniform', 'Flg') ):
       #RUN Instrument specific check
        if(instr in _db.SkZp_DB['obs_set_check']):    _db.SkZp_DB['obs_set_check'](inputdata, mosinfo);
      
         #Additional check for uniformity if not instrument is set
        elif(_opt.SkZp_Opt['Flg']['image:uniform']):
            chipset=set();
            for inp in inputdata:
                if(inp['chip']['#']): chipset|=set(inp['chip']['#']);
            chipset=tuple(chipset);
            for inp in inputdata:
                if(inp['chip']['#']): inp['chip']['#']=chipset;
        
        
              
  ####################################################
  # STARTING  extracting
    if(_opt.OptionGet('debug', otype='Flg')): startime("Extracting chips");
    imgcounter, imglist, imgdict = 0, [], {};
    for inp in inputdata:
        WaitStop();
       #get list of EXTNAME in the mosaic
        instrm=instr;
        if(not instrm): instrm=mosinfo[inp['mosaic']].get('INSTRUMENT');
    
        print('Mosaic -->', inp['mosaic'], ':', end='', file=bpar.SkZp_Par['stdout']);
        if(not inp['chip']['#']):
            print("No chips to extract. Skipping to the next!\n", file=bpar.SkZp_Par['stdout']);
            continue;
       #################
       #set outname
        imgcounter+=1;
        imgcnt=str(imgcounter).zfill(3);
        chipext=False;
    
        if(not inp['outname']): inp['outname']='%F';
        if('%f' in inp['outname'].lower()): chipext=True;  #If outname is '%f' or '%F' set to add chip ID 
        flagL=re.findall('%.', inp['outname']);
        if(len(flagL)!= len(set(flagL))): raise SkZpipeError("a flag in the output name is repetited in {:} for mosaic {:}.".format(inp['outname'], inp['mosaic']), exclocus=_name_);
        inp['outname']=_opt.namereplacepattern(inp['outname'], {'%f':inp['mosaic'], '%F':_db.SkZp_DB['namepattern'][instrm if(instrm in _db.SkZp_DB['namepattern']) else None]['%F'](inp['mosaic']), '%n':imgcnt, '%w':str(_opt.OptionGet('inputdata:workname')) }); #??? Not really updatable
    
    #ACTUAL Extracting chips
        if(len(inp['chip']['#'])>1): chipext=True;
        if(chipext): inp['outname']+="_{chip}";
        for chip in inp['chip']['#']: # ['chip']['#'] can be any iterator
            bname=inp['outname'].format( chip=str(chip).zfill(2) if(isinstance(chip, int)) else chip );
            fname=bname+bpar.SkZp_Par['fitsextension']
            flag='e';
            if(not os.path.exists(fname) or _opt.SkZp_Opt['S']['inputdata:action']=='extractforce'):
                fits.extractchip(inp['mosaic'], chip, fname);
                flag='n';
            print(" {fname} ({flag}) ".format(fname=fname, flag=flag), end='', file=bpar.SkZp_Par['stdout']);
            statD=fits.statimage(fname, typeoutput='dict');
            if(_opt.SkZp_Opt['Flg']['image:autochipreject']):
                if(statD['max']-statD['min']<1000):
                    print('[max-min<1000! Rejected!]  ', file=bpar.SkZp_Par['stdout']);
                    if(autoremove): os.unlink(fname);
                    continue;
            imglist.append(bname);
            imgdict[bname]={'NAME': bname, 'FWHM': None, 'ENTRYTYPE': entrytype};
        print('', file=bpar.SkZp_Par['stdout']);
      
    #############################################################################
    if(mode=='w'):
        entrylist.clear();
        dataframe.clear();
    entrylist.extend(imglist);
    dataframe.update(imgdict);
     #
  
    return (imglist, imgdict);



###########
def InputDataInitialize(inputdata=None, action=None, taglist=None, mode='w', 
    select=None, selectdrop=False, options=None, optfiles=[], instr=None, 
    readheader=None, headeroverride=None, readdatabase=None, onlyloaddb=None, 
    forceMJD=None, forceAM=None, forcenight=None, statkey=None, statndigits=2, 
    statsingletag=None, statoverride=False, sortby=None, verb=True, force=False):
    """Initialize the environment: inputdata database and options.

It runs the functions to read option files, to get input data and extract info from headers and internal database. 
At the end it reload the data from option files (if someone changes values from headers and database).
If the initialization has already been done (parameter 'initializingflag'==True), it will not be operated.
It resets parameter 'store4later'.

Essentially a front-end function.

Parameters
----------
    inputdata : None or str or list of str
        Source of inputdata: filename of database, list of image names or basenames of images.
        If None, standard input or option 'inputdata:file' will be used according to how the procedure is run.
    action : str, None
        Action to operate with the input data. If undetermined (None), the function determines if the input data are for already-extracted images or to extract them.
            None or ''   : The procedure decides by itself (default)
            info         : Just generate the internal information database using the inputdata and, eventually, FITS headers.
            extract      : The images are extracted from mosaic.
            extractforce : The images are extracted even the image already exist
    taglist : list
        List of the tag of the info inside 'inputdata' input data.
    mode : str
        Mode for the creation of the internal data: 'w' to create a new, 'a' to append/update
    select : str, dict, list of str
        Selection options (input for InputDataSelect, see it). 
    selectdrop : bool
        Flag to determine if the selection will replace the complete internal list (parameter `entrylist`),
            or just the selection in `runlist`.
    options : dict
        Dictionary with additional options
    optfiles : list
        List of option files
    readheader : bool or None
        Flag to determine if to read image headers, or just the input file
    headeroverride : bool or None
        Flag to determine if the data from FITS header have to override the existing data
    readdatabase : bool or None
        Flag to determine if to read the internal database, or just the input file
    onlyloaddb : bool or None
        Flag to determine if to read just the input file (if True, it sets readdatabase and onlyloaddb to False);
    forceMJD : bool or None
        If the MJD has to be recalculated even if there is a valid value.
    forceAM : bool or None
        If the airmass has to be recalculated even if there is a valid value.
    forcenight : bool or None
        If the night number has to be recalculates even if there is a valid value.
    statkey : list of str or None
        List of the image statistics to add as single tags. Options are: 'mean', 'med', 'min', 'max', 'std'
    statndigits : int, list of int
        Precision in decimal digits (default 1 digit). One value for each key, or a global one.
    statsingletag : str
        The name of the single tag, if only a single tag is added/set.
    statoverride : bool
        To change the value of an existing tag, even if its value is not None.
    sortby : str
        Inputdata tag used to sort the data
    verb : bool
        Enable full verbosity
    force : bool
        Force the initialization even if it is already done (parameter 'initializingflag')

Return
------
    tuple of 2 int
    Tuple with the length of 'inputlist' and 'runlist' parameters.


Functions
---------
    OptionRead
    InputDataAnalyze
    InputDataRetrieve
    ExtractFromMosaic
    InputDataDefaultFix
    InputDataFromFitsHeader
    InputDataSetMJD
    InputDataSetNightNumber
    InputDataDatabaseRetrieve
    InputDataImageStatAdd
    InputDataSelect
    OptionReload
    InputDataCheckFix

""";
    _name_='InputDataInitialize';

    if(sortby and not isinstance(sortby, str)): raise TypeError(_name_+": `sortby` must be the name of a tag");

    dbgtxt=' => '
    if(_opt.OptionGet('debug', otype='Flg')): startime(dbgtxt+"Starting Initialization...");
  #READING OPTIONS
    _opt.OptionRead(optfiles, options=options);

    if(_opt.OptionGet('output:stderr:hide')):
        if(_opt.OptionGet('output:stderr:hide')>0):
            bpar.SkZp_Par['stderr']=open(os.devnull,"w");
        else:
            sys.stderr=open(os.devnull,"w");
    if(_opt.OptionGet('output:stderr:hide')!=-1 and _opt.OptionGet('output:stderr:shutup')):
        sys.stderr=open(os.devnull,"w");
 #END OPTIONS
 #########################################

    if(force or not bpar.SkZp_Par['initializingflag']):
    ### START INITIALIZATION
        ResetInitialize(really=True)
    
        #####
        if(bpar.SkZp_Par['script']['scriptname'] is None): scriptdefine(auto=True);
      
        if(readheader is None):   readheader  =_opt.SkZp_Opt['Flg']['inputdata:readheader'];
        if(readdatabase is None): readdatabase=_opt.SkZp_Opt['Flg']['inputdata:readdatabase'];
        if(onlyloaddb is None): onlyloaddb=_opt.SkZp_Opt['Flg']['inputdata:onlyloaddb'];
        if(onlyloaddb): readheader, readdatabase=False, False;
        if(not action): action=_opt.OptionGet('inputdata:action')
      
        #####
        #GET THE DATA
        if(_opt.OptionGet('debug', otype='Flg')): time0=startime(dbgtxt+"Loading InputData...")
        inputdata=InputDataExternalLoad(inputfile=inputdata, header=None, comment=None, minlen=1)#, delimiter='\t') #from InputDataInitialiaze
        if(_opt.OptionGet('debug', otype='Flg')): endtime(starttime=time0, verb=True, error=False, tformat='m', ndigit=1)
        #Tuple with: header data, input data .
      
        #If it has to guess what action to take
        if(not action):
            #int,  dict,   int,    dict 
            if(_opt.OptionGet('debug', otype='Flg')): 
                time0=startime(dbgtxt+"Analizing InputData...")
    #            print('INPUTDATA>>> ', inputdata) #@@@@
            IDanal=InputDataAnalyze(inputdata=inputdata)
    #        print('ID ANALYSIS >>>', IDanal)  #@@@@@
            (num, howmuch, fwhmish, lenlines, hdran)=IDanal['nl'], IDanal['1'], IDanal['others'], IDanal['fields'], IDanal['header']
#        Dictionary with information of input data:
#            'nl':number of data lines;
#            '1':dictionary with information about first field.
#                The number of first fields that are: 
#                    'img' :    an existing image
#                    'mos' :   an existing mosaic
#                    'imgfn' :  look-like filename of an image
#                    'mosfn' :  look-like filename of a mosaic
#                    'file' :  a file but not a fits;
#                    'base' :  the basename of a file
#                    'other' : dictionary for a not-existing and not-basename entries, grouped according the presence of a FITS extension:
#                                'img': ending with 'fitsextension'
#                                'mos': ending with 'mosaicextension'
#                                'other': the others
#                                'list' : list of positions of no-fits and no-basename entries.
#
#            'others':dictionary with information about following fields:
#                    'fwhm' : int, number of second fields that are numbers;
#                    'type' : int, number of third fields that are entrytype;
#            'fields':dictionary with information about number of fields: 
#                    'same' : bool, if all the lines have same number of fields,
#                    'mean','min','max': int, the mean, min and max number of fields,
#            'header':dictionary with information about header: 
#                    'same': bool, if also the header present a lines with that same number of fields.
#                    'nhdr': list, list of number of fields of header lines with tags inside (parameter 'def:datatag')
#                    'hdrfld': list, list of sets of tags in common between parameter 'def:datatag' and the header line.
#
            outxt=f"""There are {num} lines {'' if(lenlines['same'])else 'not'} containing the same number of fields (mean:{lenlines['mean']}, min:{lenlines['min']}, max: {lenlines['max']}): 
    in {howmuch['img']} the first field refers to an existing image
    in {howmuch['mos']} the first field refers to an existing multi-HDU FITS
    in {howmuch['file']} the first field refers to an existing file, but not to a FITS file;
    in {howmuch['base']} the first field is a basename of no-image 

    in {sum(howmuch['other'].values())} the first field is unknown:
        {howmuch['other']['img']} end with FITS image extension ({bpar.SkZp_Par['fitsextension']})
        {howmuch['other']['mos']} end with FITS mosaic extension ({bpar.SkZp_Par['mosaicextension']})
        {howmuch['other']['other']} are unkown
    
    in {fwhmish} entries the second field is a number (it could be a FWHM)
The input file to extract images should have as first field the mosaic
The input file to elaborate images should have as first field the image base name and as second field the FWHM.
      """   #####
            if( howmuch['mos']+howmuch['other']['mos'] >0 and  howmuch['img']+howmuch['other']['img'] >0 ): 
                raise SkZpipeError(f"The input file is anomalous: a mix of mosaics and images\n\n"+outxt, exclocus='Inizialization');
    
            elif( howmuch['mos']+howmuch['other']['mos'] >0 ): #mosaics => no images
                if(howmuch['mos']+howmuch['other']['mos']==num): #all are mosaics or mosaic-ish names: 
                                                                 #mosaic are always manage with full name, not basename!
                                                                 #mosaic are always manage alone
                    action='extract'
                    if(lenlines['mean']==1 and not _opt.OptionGet('image:extract:select')): #just a list of mosaic without saying what to extract
                        action='info:mosaic'
                else:
                    raise SkZpipeError(f"The input file is anomalous: a mix of mosaics and something else\n\n"+outxt, exclocus='Inizialization');
    
            elif( howmuch['img']+howmuch['other']['img'] >0 ):  #images => no mosaics
                if(num==(howmuch['img']+howmuch['other']['img'])): #all are images or something that could be
                    if(not lenlines['same']): 
                        raise SkZpipeError(f"The input file is anomalous: the input lines have not the same number of fields\n\n"+outxt, exclocus='Inizialization');
                    if(num==fwhmish): #all are images with "fwhm"
                        action='info:image'
                    else:
                        action='info:image'
                else: #images + others
                    print( f"{_name_}: The input file is anomalous but not wrong.\n",outxt, file=bpar.SkZp_Par['stderr'])
                    action='info:image'
            else: 
                raise SkZpipeError(f"The input file is anomalous:\n"+outxt, exclocus='Inizialization')
            #####
    
            if(verb or _opt.OptionGet('debug')): print("InputData Analysis:\n",outxt, file=bpar.SkZp_Par['stdout'], flush=True)
            if(_opt.OptionGet('debug', otype='Flg')): endtime(time0);
    
        flush_out();
      
        if(action.startswith('extract')): #extract hdu from mosaics/multi-hdu
          # ExtractFromMosaic(inputdata=None, mode='w', sortby=None, instr=None, autoremove=True):
            ExtractFromMosaic(inputdata=inputdata, mode=mode, sortby=sortby, instr=instr, autoremove=True)
            if(not readheader):
                print('WARNING!!! Images are estracted by mosaics and options saying to not extract data from headers! The flag is changed to True.', file=bpar.SkZp_Par['stdout'])
                readheader=True
            if(not readdatabase):
                print('WARNING!!! Images are estracted by mosaics and options saying to not extract data from internal database!', file=bpar.SkZp_Par['stdout'], end='')
                if( bpar.SkZp_Par['saferunbit']&1 ):
                    print(" The flag is changed to True (saferun['base']=1).", file=bpar.SkZp_Par['stdout'])
                    readdatabase=True
                else: print('', file=bpar.SkZp_Par['stdout'])
            listof='image';
    
        elif(action.startswith('info')): #read info from 
            listof= 'mosaic' if('mosaic'in action) else 'image'
          #InputDataRetrieve(inputfile=None, taglist=None, mode='w')
            InputDataRetrieve(inputfile=inputdata, taglist=taglist, mode=mode, listof=listof, verb=verb)
    
        else:
            raise ValueError(f"{_name_}: wrong value for `action` (see help of the function or option 'inputdata:action')   <{action}>")
        flush_out();
      
        InputDataDefaultFix(instr=instr); 
        flush_out();
      
       #If retrieve data from fits header
        if(forceMJD is None): forceMJD=_opt.SkZp_Opt['Flg']['inputdata:mjdset'];
        if(forceAM is None):  forceAM =_opt.SkZp_Opt['Flg']['inputdata:am:set'];
        if(forcenight is None): forcenight=_opt.SkZp_Opt['Flg']['inputdata:nightset'];
        if(readheader):
            if(_opt.OptionGet('debug', otype='Flg')): stime=startime(dbgtxt+"Reading FITS headers, fixing MJd and night number...")
            elif(verb): print('Reading FITS headers, fixing MJd and night number...', file=bpar.SkZp_Par['stdout'])
            InputDataFromFitsHeader(instr=instr, override=headeroverride, listof=listof);

            InputDataSetFix(forceMJD=forceMJD, forceAM=forceAM, forcenight=forcenight, relenum=True)
            if(_opt.OptionGet('debug', otype='Flg')): endtime(starttime=stime, verb=True, error=False, tformat='m', ndigit=1)
        else:
            if(_opt.OptionGet('debug', otype='Flg')): startime(dbgtxt+"Fixing MJd and night number...")
            elif(verb): print('Fixing MJd and night number...', file=bpar.SkZp_Par['stdout']);

            InputDataSetFix(forceMJD=forceMJD, forceAM=forceAM, forcenight=forcenight, relenum=True)
        flush_out();
      
       #If retrieve data from internal database
      
      
        #DatabaseRetrieve(instr=None)
        InputDataDatabaseRetrieve(instr=instr, readmode=readdatabase, verb=verb);
        flush_out();
      
        InputDataImageStatAdd(statkey=statkey, ndigits=statndigits, singletag=statsingletag, override=statoverride)
      
       #Select runlist according to all input data=file+header
        nsel=InputDataSelect(select=select, drop=selectdrop)
        if(nsel<1): raise SkZpipeError("No entries selected in 'runlist'!!!", exclocus=_name_);
      
        #Reload previously read Options
        _opt.OptionReload(optfiles);
        flush_out();
      
        InputDataCheckFix()
      #  InputDataSort();

        bpar.SkZp_Par['initializingflag']=True
    ### END INITIALIZATION
    else:
        #SKIPPING Initializing
        if(verb): print("InputData already initialized! Skipping.", file=bpar.SkZp_Par['stdout']);

    #BUT not skipping sorting
    if(sortby):
        if(sortby in bpar.SkZp_Par['datatag']):
            #sort additionally by name
            for lname in ('inputlist','runlist'):
                tmpl,tmpd=InputDataSplitByTag(tag=sortby, entrylist=lname, dataframe=bpar.SkZp_Par['inputdata'])
                slist=[]
                for val in tmpl:
                    slist.extend(sorted(tmpd[val]))
                bpar.SkZp_Par[lname]=slist


        else:
            print(f"WARNING in {_name_}: `sortby` must be the name of a tag", file=bpar.SkZp_Par['stdout']);
    SpeedUpTest();
  
    if(instr): 
        print("Setting option 'inputdata:instrument' as {instr}", file=bpar.SkZp_Par['stdout'])
        _opt.OptionSet('inputdata:instrument', instr)

    return (len(bpar.SkZp_Par['inputlist']), len(bpar.SkZp_Par['runlist']) )


########################
def InputDataSplitByTag(tag=None, oper=None, sep=':', entrylist=None, dataframe=None, datatag=None):
    """Separate images in 'entrylist' (default SkZp_Par['inputlist']) according to the value of `tag` in inputdata database

Parameters
----------
    tag : str, list, None
        Name or list of names of the tags to be used to separate the file list, following the order of the tags. If None, a list with all the entrylist is return.
    oper : callable, list, None
        Function or list of functions to be applied on the tag value to determined how to separate the entrylist. None to use directly the value. If `tag` is a list', `oper` must be a list of same size.
    sep : str
        Separator used in case `tag` is a list.
    entrylist : None, list, str
        Ordered list of the entries to choose from. None for parameter 'inputlist'. Or the name of the parameter: 'runlist' for parameter 'runlist', 'inputlist' for parameter 'inputlist'.
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags of input data. None for parameter 'datatag'

Returns
-------
    A 2-element tuple with: 
        sorted list of values of the tag; 
        dictionary where the keys are the values of the tag and the values are list of the images with that value.
    If `tag` is a list, the values in the list and keys of the dictionary are a ordered composition of the values of the tags, separated by `sep`.
""";
    _name_='InputDataSplitByTag';
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name. <{}>".format(entrylist));
    if(not isinstance(dataframe,  dict)): raise TypeError(_name_+": `dataframe` must be a dict.");
    if(not isinstance(entrylist, list)): raise TypeError(_name_+": `entrylist` must be a list.");
    if(not isinstance(datatag,   list)): raise TypeError(_name_+": `datatag` must be a list.");
    if(not isinstance(sep, str)): raise TypeError(_name_+": `sep` must be a string.");

    if(tag is not None and not isinstance(tag, (str,list))): raise TypeError(_name_+": `tag` must be a string, None or a list of string");
    if(isinstance(tag, list)):
        for tg in tag:
            if(not isinstance(tg, str)): raise TypeError(_name_+": `tag` must be a string, None or a list of string");
        if(len(tag)==1): tag==tag[0];
    if(not tag): return([None], {None:entrylist.copy()})
    
    if(isinstance(oper, list)):
        for opr in oper:
          if(opr is not None and not callable(opr)): raise TypeError(_name_+": `oper` must be a callable, or None, or a list of callables or None");
        if(len(oper)==1): oper==oper[0];
    else:
        if(oper is not None and not callable(oper)): raise TypeError(_name_+": `oper` must be a callable, or None, or a list of callables or None");
    
    ##%%%%%##
    def _IDSBT_split(tag=None, entrylist=None, oper=None, norm=False):
        """Do the actual split

    norm : bool
        if to transform the values in equally long string.
        """
        tag=tag.upper();
  
        if(tag not in datatag): raise KeyError(_name_+": tag {:} is not present in the input data.".format(tag));
        tagl=[]; tagd={}
        try:
            for fn in entrylist:
                if(fn not in dataframe): raise KeyError(f"{_name_}: file '{fn}' is not present in the input data.");
                val=dataframe[fn][tag];
                if(callable(oper)): val=oper(val)
                if(val not in tagl):
                    tagl.append(val)
                    tagd[val]=[]
                tagd[val].append(fn)
        except TypeError:
            raise TypeError(_name_+": entrylist must be an iterable or None")
        if(norm):
            tmpL,tmpD=[],{}
            maxlen=max( len(str(x)) for x in tagl )
            frmt=f"{{:>{max(len(str(x)) for x in tagl)}}}"
            for tg in tagl:
                ntg=frmt.format(tg)
                tmpL.append(ntg)
                tmpD[ntg]=tagd[tg]
            tagl, tagd=tmpL,tmpD

        tagl.sort()
        return (tagl, tagd);
    ##%%%%%##

    if(isinstance(tag, str)):  #just 1
        return _IDSBT_split(tag=tag, entrylist=entrylist, oper=oper);
    else: #more than 1
        if(not isinstance(oper, list)):
            oper=[oper]*len(tag);
        elif(len(tag)!=len(oper)): 
            ValueError(_name_+": `oper` and `tag` must contain the same number of members.");
        valL0, fileD0 = _IDSBT_split(tag=tag[0], entrylist=entrylist, oper=oper[0], norm=True)
        lenD={tg:max(len(str(x)) for x in InputDataTagValueList(tag=tg, entrylist=entrylist, dataframe=dataframe, datatag=datatag) )  for tg in tag}
        for tg, opr in zip(tag[1:],oper[1:]):
            valL1,fileD1=[],{}
            for val0 in valL0:
                valL2,fileD2=_IDSBT_split(tag=tg, entrylist=fileD0[val0], oper=opr, norm=True)
                for val2 in valL2:
                    valL1.append(sep.join([val0,val2]));
                    fileD1[valL1[-1]]=fileD2[val2];
                
            valL0,fileD0=valL1,fileD1
        return (valL0,fileD0)
          

########################
def InputDataWrite(outfile=None, mode='w', style='all', backup=None, select=None, atleast=None, entrylist=None, dataframe=None, datatag=None, newtag=None, cleantag=False): # backupfile
    """Write the input data into a file for later use.

Parameters
----------
    outfile : str
        Output filename. If it starts with a plus '+', it will be considered as a suffix for the default value option 'inputdata:file'.
    mode : str
        The mode in which the file is opened (same as 'mode' in open built-in function; only 'w' and 'a').
    style : str or list of str
        Type of the output:
          'txt'   : ASCII table (user/machine readable)
          'html'  : HTML file (user readable)
          'all'   : both output user and machine readable (as define by option 'inputdata:out:styleUR' and 'inputdata:out:styleMR')
          (future implementation)
    backup : bool or None
        If an existing `outfile` has to be backed up or overwritten.
    entrylist : None, list, str
        Ordered list of the entries to choose from. None for parameter 'inputlist'. Or the name of the parameter: 'runlist' for parameter 'runlist', 'inputlist' for parameter 'inputlist'.
    select : dict, None
        As `select` of InputDataSelect
    atleast : bool
        Flag to select images that satisfy at least one of the values (True) or all the values (False) 
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags of data that has to be write down. None for SkZp_Par['datatag']
    newtag : dict,None
        Dictionary with the definition of data field not present in dataframe, but included in datatag. The key must be the tag name, the values a callable that takes as input the input data dictionary of the entry.
    cleantag : bool
        Flag to remove unset tags (=None)  

Functions
---------
    backupfile
""";
    _name_='InputDataWrite';
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, (list,tuple))): raise TypeError(_name_+": 'entrylist' must be a list or a tuple.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple.");
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe, dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
  
    if(outfile is None): outfile=_opt.OptionGet('inputdata:file')
    if(not isinstance(outfile,str)): raise TypeError(_name_+": 'outfile' must be a string or None");
    if(outfile[0]=='+'): outfile=_opt.OptionGet('inputdata:file')+outfile[1:];
    if(mode not in ('w','a')): raise ValueError(_name_+": Wrong value for 'mode'. It must be 'w' or 'a'.");
    if(style is None): style=(_opt.OptionGet('inputdata:out:styleUR', otype='S'), _opt.OptionGet('inputdata:out:styleMR', otype='S') )
    elif(isinstance(style,str)): 
        if(style=='all'):
            style=(_opt.OptionGet('inputdata:out:styleUR', otype='S'), _opt.OptionGet('inputdata:out:styleMR', otype='S') )
        else:
            style=(style,);
    else:
        style=tuple(style)
        if(any(not isinstance(x, str) for x in style)): raise  TypeError(_name_+": 'style' must be a string or a list of strings or None")

    if(not newtag): newtag=[]
    if(not isinstance(cleantag, bool)): raise TypeError(f"{_name_}: 'cleantag' must be a bool.");
  
    if(select):
        tmpl=[];
        InputDataSelect(select=select, runlist=tmpl, entrylist=entrylist, dataframe=dataframe, datatag=datatag, atleast=atleast);
        entrylist=tmpl;
   
    everynlines=_opt.OptionGet('inputdata:out:headerdataevery');

    if(backup is None): backup=_opt.OptionGet('backup:inputdata', otype='Flg')

    if(cleantag):
        datatagC=[]
        for tag in datatag:
            tagS=InputDataTagValueSet(tag=tag)
            if(len(tagS)==1 and (tagS=={None} or tagS=={()})): continue
            datatagC.append(tag)
        datatag=datatagC
    if('txt' in  style):
        if(backup):
            backupfile(outfile, keep=False if(mode=='w') else True);
        with open(outfile, mode) as f_out:
            headertxt='# '+'\t'.join(datatag)+'\n';
            ii=0;
            for fn in entrylist:
                if(ii%everynlines==0): f_out.write(headertxt);
                for tag in datatag:
                    if(tag in dataframe[fn]):
                        val=dataframe[fn][tag];
                    elif(tag in newtag):
                        val=newtag[tag](dataframe[fn]);
                    else: raise SkZpipeError("The tag '{}' doesn't exist!".format(tag), exclocus=_name_)

                    if(isinstance(val,(tuple,list,set))): val=';'.join([str(x) for x in val])
                    f_out.write(str(val)+'\t');
                f_out.write('\n');
                ii+=1;

    if('html' in style):
        if(not re.search(r'\.html?$', outfile)): outfile+=".html"
        if(backup):
            backupfile(outfile, keep=False if(mode=='w') else True)
        with open(outfile, mode) as f_out:
            td_tag='<td align=center>';
            tdfile_tag='<td align=left>';
            tr_tag='<tr>';
            f_out.write('<HTML>\n<body>\n<table>\n');
            headertxt='{:} {:}'.format(tr_tag, tdfile_tag) + '</td> {:}'.format(td_tag).join(datatag) + "</td></tr>\n ";
            ii=0;
            for fn in entrylist:
                if(ii%everynlines==0): f_out.write(headertxt);
                f_out.write("\n {:} {:} {:} </td>".format(tr_tag,tdfile_tag, fn));
                for tag in datatag[1:]:
                    if(tag in dataframe[fn]):
                        val=dataframe[fn][tag];
                    elif(tag in newtag):
                        val=newtag[tag](dataframe[fn]);
                    else: raise SkZpipeError("The tag '{}' doesn't exist!".format(tag), exclocus=_name_)
        
                    f_out.write(td_tag+str(val)+'</td>');
        
        #        for tag in dataframe[fn]:
        #          if(tag not in datatag):
        #            f_out.write("</td>"+td_tag+str(dataframe[fn][tag])+'</td>');
                f_out.write('</tr>\n');
                ii+=1;
            f_out.write("\n</table></body></HTML>");
  
####
def InputDataWrite_wfailed(outfile=None, mode='w', style='all', select=None, atleast=None, entrylist=None, dataframe=None, datatag=None, newtag=None):
    """Write the input data into the file `outfile` and the entries that terminate with error into file `outfile`+'_err'. Front-end for InputDataWrite.
  
Parameters
----------
    outfile : str
        Output filename. If it starts with a dot, it will be considered as a suffix for the default value option 'inputdata:file'.
    mode : str
        The mode in which the file is opened (same as 'mode' in open built-in function; only 'w' and 'a').
    style : str
        Type of the output: ASCII table ('txt') or HTML file ('html') or 'all' for both output
    entrylist : None, list, str
        Ordered list of the entries to choose from. None for parameter 'inputlist'. Or the name of the parameter: 'runlist' for parameter 'runlist', 'inputlist' for parameter 'inputlist'.
    select : dict, None
        As `select` of InputDataSelect
    atleast : bool
        Flag to select images that satisfy at least one of the values (True) or all the values (False) 
    dataframe : None, dict
        Dictionary of inputdata (dictionary of dictionaries). None for SkZp_Par['inputdata']
    datatatatag : None, list
        List of the tags of data that has to be write down. None for SkZp_Par['datatag']
    newtag : dict,None
        Dictionary with the definition of data field not present in dataframe, but included in datatag. The key must be the tag name, the values a callable that takes as input the input data dictionary of the entry.

Functions
---------
    InputDataWrite
""";
    _name_='InputDataWrite_wfailed';
    if(outfile is None): outfile=_opt.OptionGet('inputdata:file');
    if(not isinstance(outfile,str)): raise TypeError(_name_+": 'outfile' must be a string or None");
    if(outfile[0]=='.'): outfile=_opt.OptionGet('inputdata:file')+outfile;

    InputDataWrite(outfile=outfile, mode=mode, style=style);
    InputDataWrite(outfile=outfile+'_err', entrylist=bpar.SkZp_Par['errorlist'], mode=mode, style=style);


###
def InputDataPrint(outfile=None, entrylist=None, dataframe=None, datatag=None):
    """print the input data to a file object with a write(string) method in text mode.

Parameters
----------
    outfile : File object
        Stream object. Default value SkZp_Par['stdout'].
    entrylist : None, list
        List of images/inputdata entries. None for all entrylist in SkZp_Par['inputlist']
    dataframe : None, dict
        Dictionary of inputdata. None for SkZp_Par['inputdata']
    datatag : None, list
        List of the tags of data. None for SkZp_Par['datatag']
""";
    _name_='InputDataPrint';
    if(entrylist is None): entrylist=bpar.SkZp_Par['inputlist'];
    if(isinstance(entrylist, str)):
        if(entrylist == 'inputlist'): entrylist=bpar.SkZp_Par['inputlist'];
        elif(entrylist == 'runlist'): entrylist=bpar.SkZp_Par['runlist'];
        else: raise TypeError(_name_+": `entrylist` must be a list, None or a valid parameter name.");
    if(not isinstance(entrylist, (list,tuple))): raise TypeError(_name_+": 'entrylist' must be a list or a tuple.");
    if(datatag is None): datatag=bpar.SkZp_Par['datatag'];
    if(not isinstance(datatag, (list,tuple))): raise TypeError(_name_+": 'datatag' must be a list or a tuple.");
    if(dataframe is None): dataframe=bpar.SkZp_Par['inputdata'];
    if(not isinstance(dataframe, dict)): raise TypeError(_name_+": 'dataframe' must be a dict.");
    if(outfile is None): outfile=bpar.SkZp_Par['stdout'];
    if(not hasattr(outfile, 'write')): raise TypeError(_name_+": outfile must be an object with a write(string) method.");
  
    everynlines=_opt.OptionGet('inputdata:out:headerdataevery');
    headertxt='# '+'\t'.join(datatag)+'\n';
    ii=0;
    for fn in entrylist:
        if(ii%everynlines==0): print(headertxt, end='', file=outfile);
        for tag in datatag:
            print(str(dataframe[fn][tag])+'\t', end='', file=outfile);
#    for tag in dataframe[fn]:
#      if(tag not in datatag):
#       print(str(dataframe[fn][tag])+'\t', end='', file=outfile);
        print(file=outfile);
        ii+=1;

######################
def InputDataInitWrite(inputdata=None, action=None, taglist=None, mode='w', select=None, options=None, optfiles=[], instr=None, readheader=None, readdatabase=None, onlyloaddb=None, forceMJD=False,
    statkey=None, statndigits=2, statsingletag=None, statoverride=False, sortby=None, outfile=None, style='all', atleast=None, datatag=None, newtag=None, storelist=None, force=False, verb=False):
    """Initialize input data and write them down in a file. See also documentation for:   InputDataInitialize, InputDataWrite

Parameters
----------
    See documentation for:
        InputDataInitialize
        InputDataWrite
    inputdata : str, None
        Input file
    taglist : list
        List of the tag of the info inside 'inputdata' input data.
    mode : str
        Mode for the creation of the internal data: 'w' to create a new, 'a' to append/update
    select : str 
        Selection options to discharge images without mandatory caracteristics).
    optfiles : list
        List of option files
    readheader : Bool
        Flag to determine if to read image headers, or just the input file
    readdatabase : Bool
        Flag to determine if to read the internal database, or just the input file
    onlyloaddb : bool
        Flag to determine if to read just the input file (if True, it sets readdatabase and onlyloaddb to False);
    forceMJD : bool
        If the MJD has to be recalculates even if there is a valid value
    outfile : str, None
        Filename for inputdata storage archive.
    style : str
        Style for the storing of InputData
    datatag : None, list
        List of the tags of data that has to be write down. None for SkZp_Par['datatag']
    newtag : dict,None
        Dictionary with the definition of data field not present in dataframe, but included in datatag. The key must be the tag name, the values a callable that takes as input the input data dictionary of the entry.
    storelist : list
        Ordered list of entries to be written down/stored
    force : bool
        Force the initialization even if it is already done (parameter 'initializingflag')
    verb : bool
        Enable full verbosity

Return
------
    tuple of 2 int
    Tuple with the length of 'inputlist' and 'runlist' parameters.

Functions
---------
  InputDataInitialize
  InputDataWrite
""";
    _name_='InputDataInitWrite';

  # InputDataInitialize(inputdata=None, action=None, taglist=None, mode='w', select=None, options=None, optfiles=[], instr=None, readheader=None, headeroverride=None, readdatabase=None, onlyloaddb=None, forceMJD=False, statkey=None, statndigits=2, statsingletag=None, statoverride=False, verb=True):
    lenlst=InputDataInitialize(inputdata=inputdata, action=action, taglist=taglist, mode=mode, select=select, options=options, optfiles=optfiles, instr=instr, 
    readheader=readheader, readdatabase=readdatabase, onlyloaddb=onlyloaddb, 
    forceMJD=forceMJD, statkey=statkey, statndigits=statndigits, statsingletag=statsingletag, statoverride=statoverride, force=force, sortby=sortby, verb=verb);
  # InputDataWrite(output=None, style='all'):
    if(not storelist): storelist=bpar.SkZp_Par['runlist']
    InputDataWrite(outfile=outfile, mode='w', style=style, atleast=atleast, datatag=datatag, entrylist=storelist, newtag=newtag ); #, dataframe=None, ):

    return lenlst
  
InputDataInitializeWrite=InputDataInitWrite;


##########################
#####################
#= GENERIC PROGRAM =#
#####################
def regfromcat(cat=None, nhdr=0, datapos=0, size1=0, size2=None, units=0, color=0, shape=0, output=None, addtext=None):
    """Generate a region file for SAOds9 from a catalog.

Parameters
----------
    cat : str
        Filename of the catalog
    nhdr : int
        number of lines of the initial header (to skip).
    datapos : 
        X
    size1 : float
        X
    size2 : float
        X
    units : int, str
        The unit to use. It can be an integer or a string: 0,'fk5'  [arcsec]; 1,'image'  [pxl].
    color : int, str
        The color of the regions. It can be an integer or a string: 0,'black'; 1,'white'; 2,'red'; 3,'green'; 4,'blue'; 5,'cyan'; 6,'magenta'; 7,'yellow'.
    shape : int, str
        The shape of the regions. It can be an integer or a string:  0,'circle'; 1,'box'; 2,'elipse'; -1,'text'.
    output : str
        Filename of the output region file.
    addtext : 
        a tuple with an additional text to be included to a geometric region. First element must be a string or the number of the column with the value.

Returns
-------
    x
  datapos:    it can be the number of the column with fisrt coordinate or a list/tuple with the number of the columns of first coordinates,
              of the two data to be used to calculate the dimensions of the region (if the second of these two is not given,
              it is assumed as the following column).
  size1,size2:    the size value can be provided as a single value of the size or as a list/tuple (-size0, a, data0) with 3 values
                  to calculate the size with size=size0+a(data0-data);
                  ellipse wants 2 values and box can have 1 or 2. 
""";
    _name_='regfromcat';
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
    if(isinstance(units, str)):
        units=units.lower();
        if('pxl' in units or 'pix' in units): units=1;
        elif(units in systL): units=systL.find(units);
    elif(units<0 or units>=len(systL)): raise ValueError("regfromcat: Wrong value for unit flag! {:}".format(str(units)));
#Shape
    shapeL=["circle", "box", "ellipse", "text"];
    if(isinstance(shape, str)):
        shape=shape.lower();
        if(shape in shapeL):
            shape=-1 if(shape=='text') else shapeL.index(shape);
        else: raise ValueError("regfromcat: Wrong value for shape flag! {:}".format(str(shape)));
    elif(isinstance(shape, int) and shape<-1 or shape>=len(systL)): raise ValueError("regfromcat: Wrong value for shape flag! {:}".format(str(shape)));
    if(shape==-1 and datapos[1]<0): raise ValueError("regfromcat: Wrong value for shape flag or missing a datapos value! (shape flag: {:} ; datapos: {:} )".format(str(shape), str(datapos))); 
#Color
    colorL=["black","white","red","green","blue","cyan","magenta","yellow"];
    if(isinstance(color, str)):
        color=color.lower();
        if(color not in colorL): raise ValueError("regfromcat: Wrong value for color flag! {:}".format(str(color)));
    elif(isinstance(color, int)):
        if(color<0 or color>=len(colorL)): raise ValueError("regfromcat: Wrong value for color flag! {:}".format(str(color)));
        else: color=colorL[color];
#AdditionaText
    if(shape==-1): addtext=None;
    if(addtext is not None):
        if( not isinstance(addtext, tuple)): raise TypeError("regfromcat: addtext must be None or a tuple of 2 elements (text, font size)");
        if((not isinstance(addtext[1], int) or addtext[1]<1) or (not isinstance(addtext[0], str) and not isinstance(addtext[0], int)) or addtext[1]<=0 ): raise ValueError("regfromcat: addtext must be None or a tuple of 2 elements (text, font size)");
    if(not output): output=cat+'.reg';

    with open(output, 'w') as f_out,  open(cat) as f_in:
        fsize=addtext[1] if(addtext) else size1[0];
        f_out.write("""# Region file format: DS9 version 4.0
global color={:} font="helvetica {:d} normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=0 delete=1 include=1 source=1
{:}
""".format(color, int(fsize), systL[units]));
        ii=0;
        for ii in range(nhdr):
            line=f_in.readline();
        if(ii+1<nhdr): raise SkZpipeError("Error! Not enough lines!", exclocus='regfromcat');
        for line in f_in:
            if(len(line)<5 or line[0]=='#'): continue;
            tmpl=line.strip().split();
            x=float(tmpl[datapos[0]]);  y=float(tmpl[datapos[0]+1]);
            if(shape>=0):
                data=(float(tmpl[datapos[1]]) if(datapos[1]>=0)else 0, float(tmpl[datapos[2]]) if(datapos[2]>=0)else 0);
                dim=[size1[0]+size1[1]*(size1[2]-data[0]), size2[0]+size2[1]*(size2[2]-data[1])];
                text= " text={{{:}}}".format(tmpl[addtext[0]-1]) if(addtext) else '';
                if(shape==0): f_out.write("circle({:.6f},{:.6f}, {:.3f}{:}) #tag={{{:}}}{:}\n".format(x, y, dim[0], unitL[units], output, text));
                else: f_out.write("{:}({:.6f},{:.6f}, {:.3f}{:},{:.3f}{:}) #tag={{{:}}}{:}\n".format( shapeL[shape], x, y, dim[0], unitL[units], dim[1], unitL[units], output, text));
            elif(0<=datapos[1]<len(tmpl)):
                f_out.write("# text({:.6f},{:.6f}) text={{{:}}}\n".format( x, y, tmpl[datapos[1]]));


################################
def idmod(fname=None, id0=0, skiprows=0, outfile=None):
    """Reenumerate the id in a file

Parameters
----------
    fname : str
        Name of input file
    id0 : int
        Zero-point for the ID (first ID is 'id0'+1). It must be non-negative.
    skiprows : int
        Number of initial rows to skip
    outfile : str
        Name of the output file. Default value is 'fname'+"_M"
    fname : 
        X

Returns
-------
""";
    _name_='idmod'
    if(not isinstance(fname,str)): raise TypeError("idmod: fname must be a string.");
    check_file(fname, minline=skiprows);
    if(not isinstance(id0,int) or id0<0): raise TypeError("idmod: id0 must be a non-negative integer.");
    if(not isinstance(skiprows,int)): raise TypeError("idmod: skiprows must be an integer.");
    if(outfile is None): outfile=fname+'_M';
    with open(fname) as fin, open(outfile, 'w') as fout:
        for ii in range(skiprows):
            fout.write(fin.readline());
        for line in fin:
            idn=line.split(None,1)[0];
            lenfld=line.find(idn)+len(idn);
            frmt="{{:{:d}d}}".format(lenfld);
            id0+=1;
            fout.write(frmt.format(id0)+line[lenfld:])

#######################
def tableselect(fname=None, rules=None, outfile=None):
    """Select entries of a table according to values of the columns

Parameters
----------
    fname : str
        Name of input file
    rules : dict
        Dictionary with the selection rules. The key  gives the number of the column, 
        while the value gives the range. 
        It is possible to provide also a string with simple arithmetic operation to be performed
        (e.g. '1+2', '5-2')
         A tuple will provides minimum and maximum values. A list will provide central position and maximum distance from it.
         the number of initial lines to skip can be given with the key 0, or 'header', or 'skip'. If the number is negative,
         the lines will not be included in the output file.

    outfile : str
        Name of output file

Returns
-------
    x

Functions
---------
    
""";
    _name_='tableselect';
    oper='*+-/#';
    oppatt='['+oper+']';
    check_file(fname);
    if(outfile is None): outfile=fname+"-S"; 
    if(not isinstance(rules, dict)): raise TypeError(_name_+": rules must be a dictionary");
    nhdr=0;rls={}; rlop={};
    for key in rules:
        if(key in [0, 'hedaer', 'skip']):
            if(not isinstance(rules[key], int)): raise TypeError(_name_+": rule for initial lines to skip must be an integer");
            if(nhdr): raise ValueError(_name_+": double rule");
            nhdr=rules[key];
        elif(isinstance(key, int) and key>0):
            if(not isinstance(rules[key], tuple) and not isinstance(rules[key], list)): raise TypeError(_name_+": selection rules must be a tuple or a list");
            rls[key]=rules[key] if(isinstance(rules[key], tuple)) else (rules[key][0]-rules[key][1], rules[key][0]+rules[key][1]);
        elif(isinstance(key, str) and len(re.findall(oppatt, key))==1):
            if(not isinstance(rules[key], tuple) and not isinstance(rules[key], list)): raise TypeError(_name_+": selection rules must be a tuple or a list");
            tmpl=re.split(oppatt, key);
            if(len(tmpl)!=2 or not isinteger(tmpl[0]) or not isinteger(tmpl[1])): raise ValueError(_name_+": wrong value for key in rules [{:}]".format(key));
            tmpl=[int(x) for x in tmpl];
            tmpl.insert(1,re.search(oppatt, key).group());
            tmpl=tuple(tmpl);
            rlop[key]=[tmpl,rules[key]] if(isinstance(rules[key], tuple)) else [tmpl,(rules[key][0]-rules[key][1], rules[key][0]+rules[key][1])];
        else:
            raise ValueError(_name_+": wrong value for key in rules.");
#  print(rls);
#  print(rlop);
    with open(fname) as fin, open(outfile, 'w') as fout:
        for ii in range(abs(nhdr)):
            line=fin.readline();
            if(nhdr>0): fout.write(line);
        nl=0;
        for line in fin:
            cols=line.split();
            cols.insert(0,0);
            for key in rls:
                if(not rls[key][0]<=float(cols[key])<=rls[key][1]):
                    line='';
                    break;
            for rule in rlop.values():
                if  (rule[0][1]=='+'): val=float(cols[rule[0][0]]) + float(cols[rule[0][2]]);  
                elif(rule[0][1]=='-'): val=float(cols[rule[0][0]]) - float(cols[rule[0][2]]);  
                elif(rule[0][1]=='*'): val=float(cols[rule[0][0]]) * float(cols[rule[0][2]]);  
                elif(rule[0][1]=='/'): val=float(cols[rule[0][0]]) / float(cols[rule[0][2]]);  
                elif(rule[0][1]=='#'): val=math.sqrt(float(cols[rule[0][0]])**2 + float(cols[rule[0][2]])**2);  
                if(not rule[1][0]<=val<=rule[1][1]):
                        line='';
                        break;
            if(line):
                fout.write(line);
                nl+=1;
    return nl;
            
