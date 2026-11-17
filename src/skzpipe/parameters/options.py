"""Options for the package

"""

import os, re, sys, shutil;
import collections, copy;
from pydoc import pager

from ..exceptions import *
from . import basicpar  as bpar

##  Definition  
##  FUNCTIONS  
##  OPTIONS  VALUES 

##################
##  Definition  ##
##################
def _RF_dict_obj(txt='', vobj=str, kobj=str):
  pass;
#_name_ : Idententication name of the type of values store in the option
#_funct_ : callable that transform a string into a correct value
#_type_ : class of the main object. It must return a empty value with no input
#_stype_ : class of the elements of the main class (only for options with subitems)
#_doc_ : documentation/description of the object store in the option
#WARNING!!!! WHEN ADDING A NEW TYPE, PUT IT ALSO IN '_keys_'
SkZp_Opt={'_name_':'SkZp_Opt', 
          '_keys_':('Flg', 'S','I','F','L', 'L"', 'T','Set', 'LT', 'D','DI', 'DF', 'DL', 'LD', 'DT', 'DFlg'), #list of types
          '_tkeys_':(('_name_', '_type_', '_funct_', '_doc_'), ('_stype_',)  ), #list of keys for definition of a type ( (all), (some))
          '_doc_':{}, #db of documentation

          'Flg':{'_name_':'SkZp_Opt:Flg', '_funct_':( lambda x: False if(re.search("N|n|0|F",str(x)))else True ),               '_type_':bool, '_doc_':"Flag/Bool" },
          'S':{'_name_':'SkZp_Opt:S',   '_funct_':str,                '_type_':str,  '_doc_':"String" },
          'I':{'_name_':'SkZp_Opt:I',   '_funct_':int,                '_type_':int,  '_doc_':"Integer" },
          'F':{'_name_':'SkZp_Opt:F',   '_funct_':float,              '_type_':float,'_doc_':"Float" },
          'L':{'_name_':'SkZp_Opt:L',   '_funct_':( lambda x: re.split(";|,",x)),      '_type_':list,  '_doc_':"List" },
         'L"':{'_name_':'SkZp_Opt:L"',   '_funct_':( lambda x: re.split('"',x)),        '_type_':list,  '_doc_':"List of item with peculiar characters; separated by \"" },

          'T':{'_name_':'SkZp_Opt:T',   '_funct_':( lambda x: tuple(re.split(";|,",x))),      '_type_':tuple,  '_doc_':"Tuple" },
        'Set':{'_name_':'SkZp_Opt:Set', '_funct_':( lambda x: set(re.split(";|,",x))),        '_type_':set,  '_doc_':"Set" },
         'LT':{'_name_':'SkZp_Opt:LT',   '_funct_':( lambda x: [ tuple(y.split(':')) for y in re.split(";|,",x)  ]),  '_type_':list, '_stype_':tuple,  '_doc_':"List of tuples [(:);(:),]" },

          'D':{'_name_':'SkZp_Opt:D',   '_funct_':( lambda x: dict( tuple(y.split(':')) for y in x.split(";") ) ),       '_type_':dict,   '_doc_':"Dictionary of string:string;" },
         'DI':{'_name_':'SkZp_Opt:DI',  '_funct_':( lambda x: _RF_dict_obj(txt=x, vobj=int) ),       '_type_':dict, '_stype_':int,  '_doc_':"Dictionary of string:integer;" },
         'DF':{'_name_':'SkZp_Opt:DF',  '_funct_':( lambda x: _RF_dict_obj(txt=x, vobj=float) ),     '_type_':dict, '_stype_':float,  '_doc_':"Dictionary of string:float;" },
         'DL':{'_name_':'SkZp_Opt:DL',   '_funct_':( lambda x: _RF_dict_obj(txt=x, vobj=list, splitsub=',') ),   '_type_':dict, '_stype_':list, '_doc_':"Dictionary of string:list ('':[,];)" },
         'LD':{'_name_':'SkZp_Opt:LD',   '_funct_':( lambda x: [dict( tuple(y.split(':')) for y in z.split(";") ) for z in x.split('#')] ),   '_type_':list, '_stype_':dict, '_doc_':"List of dictionary 'key:value;key:value#key:value'" },
         'DT':{'_name_':'SkZp_Opt:DT',   '_funct_':( lambda x: _RF_dict_obj(txt=x, vobj=tuple, splitsub=',') ),   '_type_':dict, '_stype_':tuple, '_doc_':"Dictionary of string:tuple ('':(,);)" },
       'DFlg':{'_name_':'SkZp_Opt:DF',  '_funct_':( lambda x: _RF_dict_obj(txt=x, vobj=( lambda x:False if(re.search("N|n|0|F",x))else True )) ),     '_type_':dict, '_stype_':bool,  '_doc_':"Dictionary of string:bool" },
        };


#################
##  FUNCTIONS  ##
#################
def _RF_dict_obj(txt='', vobj=str, kobj=str, splititem=';', splitsub=None):
  retd={};
  for y in txt.split(splititem):
    kk,vv=tuple(y.split(':')) if (':' in y) else (y,None);
    if(splitsub): vv=re.split(splitsub, vv) if(isinstance(vv,str)) else [vv];
    retd[kobj(kk)]=None if(vv is None) else vobj(vv);
  return retd;

##############################################
def namereplacepattern(name=None, conversion={}):
  """Replace in the string 'name' patterns according to directives by default (SkZp_Par['charconversion']) and given by 'conversion' dictionary.

Parameters
----------
    name : str
        Text to process
    conversion : dict
        Dictionary with the conversion map to add to existing in  SkZp_Par['charconversion'].

Return
------
    x
""";
  _name_='namereplacepattern';
  if(not isinstance(name,str)): raise TypeError(_name_+": 'name' must be a string");
  if(not isinstance(conversion,dict)): raise TypeError(_name_+": 'conversion' must be a dict");
  convmap={**bpar.SkZp_Par['charconversion'], **conversion};
  for patt in convmap:
    if(patt in name): name=name.replace(patt, str(convmap[patt]() if(callable(convmap[patt])) else convmap[patt]));
  return name;



######################
# To manage SkZp_Opt #
######################

def OptionStartswith(keyword=None, strict=False, optiondb=None):
  """Return list of options related to a certain keyword. Options are grouped in sections characterized by keyword (e.g. 'progr, 'debugging', 'image') followed by colon (as 'debugging:logfile').

Parameters
----------
    keyword : str
        Name of the section
    strict : bool
        Flag to return any option starting with `keyword` (False, default), or only the options of the section identified by `keyword` (True)
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt

Return
------
    return : list
        List of option names
"""
  _name_='OptionStartswith'
  if(optiondb is None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
  optl=[]
  if(not keyword): return optl;
  for key in optiondb['_keys_']:
      for option in optiondb[key]:
          if(option.startswith(keyword)):
              if(strict):
                  if(':' not in option[len(keyword)+1:]):  optl.append(option);
              else:  optl.append(option);
  return optl;


## INFO ##
#################################################
def OptionTypeHelp(viewer=None, optiondb=None):
    """Show information about option types

Parameters
----------
    viewer ; str or None
        How to visualize the information. None (default) or 'pager' to use the pager (from pydoc.pager), 
        'print' to use built-in function print, 'return' to return the text.
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt

Return
------
    Type name and description
""";
    _name_='OptionTypeHelp';
    if(optiondb is None): optiondb=SkZp_Opt;
    if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");

    outxt=''
    for key in optiondb['_keys_']:
        outxt+=f"{key:6}:"+optiondb[key]['_doc_'] +'\n'

    if(viewer is None or viewer=='pager'):
        pager(outxt);
    elif(viewer=='print'):
        print(outxt, file=bpar.SkZp_Par['stdout'])
    elif(viewer=='return'): return outxt
    else: raise ValueError(_name_+": wrong value for `viewer` (None/'pager', 'print', or 'return')")


#################################################
def OptionHelp(option=None, viewer=None, optiondb=None):
    """Print the description of a option

Parameters
----------
    option : str
        Name of the option
    viewer ; str or None
        How to visualize the information. None (default) or 'pager' to use the pager (from pydoc.pager), 
        'print' to use built-in function print, 'return' to return the text.
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt

Return
------
    Type, value and description (if present);
""";
    _name_='OptionHelp';
    if(optiondb is None): optiondb=SkZp_Opt;
    if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
    optype=None;
    if(not option): return;
    outxt=''
    for key in optiondb['_keys_']:
        if(option in optiondb[key]):
            optype=key;
            outxt+=f"The option '{option}' is of type '{optype}':" + optiondb[key]['_doc_'] +'\n'
            break;
    if(optype is None): 
        outxt+="The option '{opt}' does not exist.".format(opt=option) +'\n'
    else:
        outxt+="It is set as: "+ repr(optiondb[optype][option]) +'\n'
        if(option in optiondb['_doc_']): outxt+=optiondb['_doc_'][option] +'\n'
        else: outxt+="No description.\n"
    
    if(viewer is None or viewer=='pager'):
        pager(outxt);
    elif(viewer=='print'):
        print(outxt, file=bpar.SkZp_Par['stdout'])
    elif(viewer=='return'): return outxt
    else: raise ValueError(_name_+": wrong value for `viewer` (None/'pager', 'print', or 'return')")
  

#################################################
def OptionApropos(keyword=None, viewer=None, optiondb=None):
  """Print the description of options that start with `keyword`

Parameters
----------
    keyword : str
        Initial part of the option name
    viewer ; str or None
        How to visualize the information. None (default) or 'pager' to use the pager (from pydoc.pager), 
        'print' to use built-in function print, 'return' to return the text.
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt

Raises
------
    TypeError
        Incorrect type for `optiondb`
""";
  _name_='OptionApropos';
  if(optiondb is None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
  
  key=keyword[:-1] if(keyword[-1]==':') else keyword
  outxt=key+":\n"
  if(key in optiondb['_doc_']): outxt+="    General description:  "+optiondb['_doc_'][key]+"\n\n"
  for option in OptionStartswith(keyword=keyword, optiondb=optiondb):
      for key in optiondb['_keys_']:
          if(option in optiondb[key]): break;
      outxt+="'{opt}' : type '{optyp}' ".format(opt=option, optyp=key)+ optiondb[key]['_doc_'] +'\n'
      outxt+="    =>"+ repr(optiondb[key][option]) +'\n'
      outxt+="    Documentation:\n"+str(optiondb['_doc_'].get(option)) +"\n\n"
  
  if(viewer is None or viewer=='pager'):
      pager(outxt);
  elif(viewer=='print'):
    print(outxt, file=bpar.SkZp_Par['stdout'])
  elif(viewer=='return'): return outxt
  else: raise ValueError(_name_+": wrong value for `viewer` (None/'pager', 'print', or 'return')")

  

############################################################
def OptionPrint(option=None, otype=None, verb=True, optiondb=None):
    """Return and print the value of a option and its type

Parameters
----------
    option : str
        Name of the option.
    otype : str
        Type of the option (list stored in '_keys_' of option database). 
        For example: 'S' for string, 'I' for integer, 'F' for float). 
        If not provide, it will be determined.
    verb : bool
        If to print brief information about the option. Default True.
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt

Return
------
    ret : tuple or None
        Tuple with type and value, or None if option doesn't exist.
""";
    _name_='OptionPrint';
    if(optiondb is None): optiondb=SkZp_Opt;
    if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
    if(not option): return tuple();
    if(otype):
        if(otype in optiondb['_keys_'] and option in optiondb[otype]): 
            if(verb): print(f"The option '{option}' (type '{otype}':{optiondb[key]['_doc_']}):", optiondb[otype][option], file=bpar.SkZp_Par['stdout']);
        else: 
            raise SkZpipeError(f"Option '{option}' is not of type {otype} or {otype} is not a valid type", exclocus=_name_);
    else:
        for key in optiondb['_keys_']:
            if(option in optiondb[key]):
                otype=key
                if(verb): print(f"The option '{option}' (type '{otype}':{optiondb[key]['_doc_']}):", optiondb[otype][option], file=bpar.SkZp_Par['stdout']);

    if(otype is None):
        if(verb): print("The option '{opt}' does not exist.".format(opt=option), file=bpar.SkZp_Par['stdout']);
        return;
    else: return ( otype, copy.deepcopy(optiondb[otype][option]) )


#################################################
def OptionGet(option=None, otype=None, optiondb=None, raisexc=True):
    """Return the value of a option

Parameters
----------
    option : str
        Name of the option.
    otype : str
        Type of the option (list stored in '_keys_' of option database). 
        For example: 'S' for string, 'I' for integer, 'F' for float). 
        If not provide, it will be determined.
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt
    raisexc : bool
        Flag to set if raise an exception or just returning None.

Return
------
    ret : object
        The value. If option doesn't exist, it raises KeyError.
""";
    _name_='OptionGet';
    if(optiondb is None): optiondb=SkZp_Opt;
    if(not isinstance(option, str)): raise TypeError(_name_+": `option` must be a string");
    if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
    if(not option):  raise KeyError("The option '{opt}' does not exist.".format(opt=option));
    if(otype):
        if(otype in optiondb['_keys_'] and option in optiondb[otype]): 
            return copy.deepcopy(optiondb[otype][option]);
        else: 
            raise SkZpipeError(f"Option '{option}' is not of type {otype} or {otype} is not a valid type", exclocus=_name_);
    else:
        for otype in optiondb['_keys_']:
              if(option in optiondb[otype]):
                  return copy.deepcopy(optiondb[otype][option]);
    if(raisexc):
        raise KeyError("The option '{opt}' does not exist.".format(opt=option));
    else: return;

  
  
## CHECK ##
###############################################
def OptionIntegrityCheck(optiondb=None, raisexc=True):
    """Check the internal dict SkZ_Opt for integrity, to avoid that a option appears in more than one type.

Parameters
----------
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt
    raisexc : bool
        Flag to set if raise an exception or just print a warning message.

Return
------
    0 if no duplications are found, otherwise it returns the number of duplicated options.
"""
  
    _name_='OptionIntegrityCheck';
    if(optiondb is None): optiondb=SkZp_Opt;
    if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
    msgL=[];
  #Check if option types are listed in _keys_
    setk=set(x for x in optiondb if(not x.startswith('_')))-set(optiondb['_keys_'])
    if(setk):
        if(raisexc):
            raise SkZpipeError(f"Option database not configured properly: entry '_keys_' doesn't contain items <{setk}>", exclocus=_name_)
        else: 
            print('Error in internal option!!!\n', f"Option database not configured properly: entry '_keys_' doesn't contain items <{setk}>", file=bpar.SkZp_Par['stderr']);
            return 1
    setD={};
   #checking among types in _keys_
    for key in optiondb['_keys_']:
       #if not used
        if(key not in optiondb): 
            msgL.append(f"Option database not configured properly: entry '_keys_' contains item <{key}> not present")
        else:
           #list of options in each type
            setD[key]=set(x for x in optiondb[key].keys() if(not x.startswith('_') and not x.endswith('_')) );
        for tkey in optiondb['_tkeys_'][0]:
            if(tkey not in  optiondb[key]):
                msgL.append(f"Option database not configured properly: type {key} doesn't have entry {tkey}")
    if(msgL):
        if(raisexc): raise SkZpipeError('\n'.join(msgL), exclocus='Internal options');
        else: print('Error in internal option!!!','\n'.join(msgL), file=bpar.SkZp_Par['stderr']);
        return len(msgL);
  
   #checking for name collision among options
    for ii in range(1,len(optiondb['_keys_'])):
        ikey=optiondb['_keys_'][ii];
        for jj in range(ii):
            jkey=optiondb['_keys_'][jj];
            inters=setD[ikey].intersection(setD[jkey]);
            if(inters): 
                msgL.append('The option {opt!s} appears in the types {tp!s}!'.format(opt=inters, tp=(ikey,jkey) ) );
    if(msgL):
        if(raisexc): raise SkZpipeError('\n'.join(msgL), exclocus='Internal options');
        else: print('Error in internal option!!!','\n'.join(msgL), file=bpar.SkZp_Par['stderr']);
        return len(msgL);
    return 0;
      

##############################################
def OptionCoder(optiondb=None):
    """Set SkZ-coder options in the given option dataframe (default SkZ_Opt).

Parameters
----------
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt
    raisexc : bool
        Flag to set if raise an exception or just print a warning message (and in case a quick fix of the values).

Return
------
"""
    
    _name_='OptionCoder'
    optiondb['Flg']['butler'  ]=True

    optiondb['S']['progr:exec:daophot'  ]="daophot95"
    optiondb['S']['progr:exec:allstar'  ]="allstar95"
    optiondb['S']['progr:exec:allframe' ]="allframe95"
    optiondb['S']['progr:exec:daomaster']="daomaster95"
    optiondb['S']['progr:exec:daomatch' ]="daomatch"  
    optiondb['S']['progr:exec:montage2' ]="montage95"

##############################################
def OptionButler(optiondb=None):
    """Set options in the given option dataframe (default SkZ_Opt).

Parameters
----------
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt
    raisexc : bool
        Flag to set if raise an exception or just print a warning message (and in case a quick fix of the values).

Return
------
"""
    
    _name_='OptionButler'
    if(_opt.SkZp_Opt['I']['mp:nproc']<2):
        _opt.SkZp_Opt['I']['mp:nproc']=len(os.sched_getaffinity(0))-1

##############################################
def OptionFixCheck(optiondb=None, raisexc=True):
    """Fix and check the values in the given option dictionary (default SkZ_Opt).

Parameters
----------
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt
    raisexc : bool
        Flag to set if raise an exception or just print a warning message (and in case a quick fix of the values).

Return
------
"""
    
    _name_='OptionFixCheck'
    from .classes  import bclasses
    #Function code
    if(optiondb is None): optiondb=SkZp_Opt
    if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");

    #set correctly the undefined value if the option is set as None
    for key in optiondb['_keys_']:
        for opt in optiondb[key]:
            if(optiondb[key][opt] is None):  optiondb[key][opt]=optiondb[key]['_type_']();

   #CODER option setting
    if(optiondb['Flg']['skzopt']):
        OptionCoder(optiondb=optiondb)

    if(optiondb['Flg']['butler']):
        OptionButler(optiondb=optiondb)

    optiondb['S']['inputdata:workname']=namereplacepattern(optiondb['S']['inputdata:workname'])
    temps=optiondb['S']['inputdata:tag:entrytype']
    if(temps):
        if(temps not in bpar.SkZp_Par['entrytypelist']):
            raise ValueError(f"{_name_}: option 'inputdata:tag:entrytype' value not present in parameter 'entrytypelist' <{temps}>")

    if(optiondb['S']['progr:path:dir'] and optiondb['S']['progr:path:dir'][-1]!=os.path.sep): optiondb['S']['progr:path:dir']+=os.path.sep;
    if(optiondb['S']['progr:path:DAO'] and optiondb['S']['progr:path:DAO'][-1]!=os.path.sep): optiondb['S']['progr:path:DAO']+=os.path.sep;

    if(optiondb['DFlg']['saferun']):
        if(optiondb['DFlg']['saferun'].get('base')): bpar.SkZp_Par['saferunbit']|=1;

    if(optiondb['Flg']['debugging:full']): optiondb['Flg']['debugging:log']=True;
    if(not optiondb['S']['debugging:logfile']): optiondb['Flg']['debugging:log']=False;
    if(optiondb['Flg']['debugging:log']):
        bpar.SkZp_Par['stdout']=bclasses.GlobalOutPut(otype='out');
        bpar.SkZp_Par['stderr']=bclasses.GlobalOutPut(otype='err');
    else:
        if(isinstance(bpar.SkZp_Par['stdout'], bclasses.GlobalOutPut)): bpar.SkZp_Par['stdout']=sys.stdout;
        if(isinstance(bpar.SkZp_Par['stderr'], bclasses.GlobalOutPut)): bpar.SkZp_Par['stderr']=sys.stderr;
  
  #PHOTO
    optv=OptionGet('photo:psf:maxellipticity',optiondb=optiondb, raisexc=raisexc);
    if(optv<=0 or optv>1):
        if(raisexc): raise ValueError(_name_+": option 'photo:psf:maxellipticity' should be greater than 0 and less or equal to 1 <{}>".format(optv));
        else:
            OptionSet('photo:psf:maxellipticity', 1, optiondb=optiondb);
            print(_name_+": Fixing option 'photo:psf:maxellipticity' to 1", file=bpar.SkZp_Par['stderr']);
    optv=OptionGet('image:standard', optiondb=optiondb);
    if(len(optv)>1):
        if(raisexc): raise ValueError(_name_+": option 'image:standard' can have just one entry <{}>".format(optv));
        else:
            key=optv.keys()[0]
            OptionSet('image:standard', {key:optv[key]}, optiondb=optiondb)
            print(_name_+": Fixing option 'image:standard' to 1 entry", file=bpar.SkZp_Par['stderr']);

  #STACK
    if(SkZp_Opt['S'  ]['stack:substacktag'] and SkZp_Opt['S'  ]['stack:bytag']==SkZp_Opt['S'  ]['stack:substacktag']):
        SkZp_Opt['S'  ]['stack:substacktag']='';
        print(_name_+": Fixing option: 'stack:substacktag'=='stack:bytag'! Resetting 'stack:substacktag'.", file=bpar.SkZp_Par['stderr']);

  
    #Check external programm
    progrL=OptionStartswith(keyword='progr:exec:', strict=True, optiondb=optiondb)
    for oprg in progrL:
        prg=OptionGet(option=oprg, optiondb=optiondb)
        if(isinstance(prg, str)):
            if( not shutil.which(prg)): 
                if(False and raisexc):
                    raise SkZpipeError("External program '{prg}' from option '{opt}' is not define properly or its path is not present in envinment variable PATH".format(prg=prg, opt=oprg), file=bpar.SkZp_Par['stderr'], exclocus=_name_)
                else:
                    print(_name_+": External program '{prg}' from option '{opt}' is not define properly or its path is not present in envinment variable PATH".format(prg=prg, opt=oprg), file=bpar.SkZp_Par['stderr']);


##############################################
def OptionFileCreate(optfile=None):
    """Create an option file with basic option (parameter 'optfile') commented out.

Parameters
----------
    optfile : str
        Filename of the option file to which append the commented basic options. Default first value in SkZp_Par['optfilenames'].

Return
------
    out : file 'SkZpipe.opt'
        
""";
    _name_='OptionFileCreate';
    if(optfile is None): optfile=bpar.SkZp_Par['optfilenames'][0];
    if(not isinstance(optfile, str) or not optfile): raise TypeError(_name_+": 'optfile' must be a not-empty string");
    if(not isinstance(bpar.SkZp_Par['optfile'], str) or not bpar.SkZp_Par['optfile']): 
        raise SkZpipeError("Problems with default value of option file in parameter 'optfile'", exclocus=_name_);
    with open(optfile, 'a') as fopt:
        fopt.write(bpar.SkZp_Par['optfile']);



## SET/READ ###
###############################################
def OptionSet(option=None, value=None, optdict=None, otype=None, optiondb=None):   #RAISE SkZpipeErr
    """Set option in the system from a dictionary or giving the name and its value. None value will be interpreted as not to define (i.e. to skip).

Parameters
----------
    option : str
        Option name
    value : 
        Value of the option. If None, the option will be not defined.
    otype : str, list of str
        List of types of the options (for example: 'S' for string, 'I' for integer, 'F' for float). 
        List of values stored in '_keys_' of option database.
        If not provide, it will be determined.
    optdict : dict
        Dictionary with options. Format:
          key : option name
          value : option value
    optiondb : as SkZp_Opt
        Database of the options to update. Default SkZp_Opt

Return
------
    nopt : int
        Number of option succeffully set.

Functions
---------
    None
""";
    _name_='OptionSet';
    if(optiondb is None): optiondb=SkZp_Opt;
    if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
    if(optdict is None):
        if(option is not None): optdict={option:value};
        else: return 0
    if(otype is not None and not isinstance(otype, (str, list))):  raise TypeError(_name_+": `otype` must be a list or a string, or None")
    if(isinstance(otype, str)): otype=[otype]
    nopt=0;
    optL=list(optdict.keys())
    otypeL=otype if(otype) else optiondb['_keys_']
    for opt,value in optdict.items():
        if(value is None): continue;
        for key in otypeL:
            if(opt in optiondb[key]):
                optL.remove(opt)
                if(isinstance(value,optiondb[key]['_type_'])):
                    optiondb[key][opt]=value;
                else:
                    #empty value given by class in _type_; value by _funct_
                    optiondb[key][opt]=optiondb[key]['_funct_'](value) if(value and value!='None') else optiondb[key]['_type_']();
                if(optiondb['Flg']['debug']): print("\t", opt, ':', optiondb[key][opt], file=bpar.SkZp_Par['stderr']);
                nopt+=1;
                break;
    if(optL): print(f"Some options were not set: {optL}." f"Only these types were considered {otype}" if(otype) else "They doesn't seem to exist.", file=bpar.SkZp_Par['stderr']);

    return nopt;

##############################################
def OptionCheckInput(optfile=None, options=None, output='stdout', verb=True, optiondb=None):
  """Read an option file to check if the names are corrcect

Parameters
----------
    optfile : str or list of str
        Name or list of names of the option files to check. Default arguments passed 
    options : dict
        Dictionary with the options to check.
    output : str or 
        Where to write the messages. 'stdout' or 'stderr' to write in the corresponding streams, or an object with write attribute. Default 'stdout'
    verb : bool
        If True, it will print the number of valid options.
    optiondb : as SkZp_Opt
        Database of the options to check. Default SkZp_Opt

Return
------
    Write in `output` the number of unique read options. -1 if the file doesn't exist.

Funtions
--------
    None
""";
  _name_='OptionCheckInput';
  if(optiondb is None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
  if(output not in ('stdout', 'stderr') and not hasattr(output, 'write')): raise ValueError(_name_+": Wrong value for `output` <{output}>".format(output=output));
  if(isinstance(output,str)): output=bpar.SkZp_Par[output];

  if(optfile is None and options is None):
    if(len(sys.argv)>1): optfile=sys.argv[1:];
  
  optkeyset=set();
  for key in optiondb['_keys_']:
    optkeyset=optkeyset.union( x for x in optiondb[key].keys() if(not x.startswith('_') and not x.endswith('_')) );
#  optkeyset-=set(bpar.SkZp_Par['_skeys_']);

  if(optfile):
    if( not isinstance(optfile, list)): optfile=[optfile];
    for optf in optfile:
      print("Checking {:} ... ".format(optf), file=output);
      if(os.path.exists(optf)):
        with open(optf) as f_opt:
          optset=set();
          for line in f_opt:
            line=line.strip()
            if(len(line)<3 or line[0]=='#' or not '=' in line):  continue;
            tmpl=[s.strip() for s in line.split('=')];
            if(not tmpl[0]):  continue;
            if(tmpl[0] not in optkeyset): print("\tWrong option line! >>", line, file=output);
            else: optset=optset.union(tmpl[0]);
        print("\tNumber of valid options:", len(optset), file=output);
      else: print("\tNot exist!", file=output);
  if(options):
    if(not isinstance(options, dict)): raise TypeError(_name_+": `options` must be a dictionary <{options}>".format(options=options));
    if(optiondb['Flg']['debug'] or bpar.SkZp_Par['saferunbit']&1): verb=True;
  
    optset=set();
    print("Checking options ... ", file=output);
    for opt in options:
      if(not opt):  continue;
      if(opt not in optkeyset): print("\tWrong option! <{opt}>:<{vopt}>".format(opt=opt, vopt=options[opt]), file=output);
      else: optset=optset.union(opt);
    if(verb): print("\tNumber of valid options:", len(optset), file=output);


##############################################
def OptionLoadFile(optfile=None, verb=True, output='stdout', optiondb=None):   #RAISE SkZpipeErr
  """Read options from option file to store the values in the parameter 'optfiledata'

Parameters
----------
    optfile : str
        Name of the file where the options are stored.
    verb : bool
        Flag to set the verbosity of the command.
    output : str or 
        Where to write the messages. 'stdout' or 'stderr' to write in the corresponding streams, or an object with write attribute. Default 'stdout'
    optiondb : as SkZp_Opt
        Database of the options. Default SkZp_Opt

Return
------
    Number of unique read options. -1 if the file doesn't exist.

Funtions
--------
    None
""";
  _name_='OptionLoadFile';
  if(output not in ('stdout', 'stderr') and not hasattr(output, 'write')): raise ValueError(_name_+": Wrong value for `output` <{output}>".format(output=output));
  if(isinstance(output,str)): output=bpar.SkZp_Par[output];
  if(optiondb is None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be a object as SkZp_Opt");

  if(os.path.exists(optfile)):
    if(verb): print("Reading {:} ...".format(optfile), file=output);
    with open(optfile) as f_opt:
      bpar.SkZp_Par['optfilelist'].append(optfile);
      bpar.SkZp_Par['optfiledata'][optfile]={};
      optkeyset=set()
      for key in optiondb['_keys_']:
        optkeyset=optkeyset.union( x for x in optiondb[key].keys() if(not x.startswith('_') and not x.endswith('_')) );
#      optkeyset-=set(bpar.SkZp_Par['_skeys_']);
      for line in f_opt:
        line=line.strip()
        if(len(line)<3 or line[0]=='#'):  continue;
        if('=' in line):
            tmpl=[s.strip() for s in line.split('=')]
        elif(' ' in line or '\t' in line):
            tmpl=[s.strip() for s in line.split(None,1)]
        if(not tmpl[0]):  continue
        if(len(tmpl)==1): tmpl.append(1)
        if(tmpl[0] in optkeyset):
          bpar.SkZp_Par['optfiledata'][optfile][tmpl[0]]=tmpl[1];
        elif(optiondb['Flg']['debug'] or bpar.SkZp_Par['saferunbit']&1): print("\tIn {optf} wrong option line! >{line}<".format(optf=optfile, line=line), file=output);
    return len(bpar.SkZp_Par['optfiledata'][optfile]);
  return -1;


##############################################
def OptionReload(optfiles=None, output='stdout', optiondb=None, raisexc=True):   #RAISE SkZpipeErr
  """Reload options previously recovered from option files (default: SkZ_pipeline.opt, SkZpipe.opt)

Parameters
----------
    optfiles : list
        List of filenames of option files
    output : str or 
        Where to write the messages. 'stdout' or 'stderr' to write in the corresponding streams, or an object with write attribute. Default 'stdout'
    optiondb : as SkZp_Opt
        Database of the options to update. Default SkZp_Opt
    raisexc : bool
        Flag to set if raise an exception or just print a warning message.

Functions
---------
    OptionSet
""";
  _name_='OptionReload';
  if(optiondb is None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
  if(output not in ('stdout', 'stderr') and not hasattr(output, 'write')): raise ValueError(_name_+": Wrong value for `output` <{output}>".format(output=output));
  if(isinstance(output,str)): output=bpar.SkZp_Par[output];
  if(optfiles is None): optfiles=[];

  tmpl= bpar.SkZp_Par['optfilelist'].copy();
  for optf in optfiles:
    if(optf not in tmpl): tmpl.append(optf);
  for optfile in tmpl:
    if(optfile in bpar.SkZp_Par['optfilelist']):
      print("Reloading {:} ...".format(optfile), file=output);
      OptionSet(optdict=bpar.SkZp_Par['optfiledata'][optfile], optiondb=optiondb);
      if(optiondb['Flg']['debug']): print(bpar.SkZp_Par['optfiledata'][optfile], file=output);
  if(None in bpar.SkZp_Par['optfiledata']):
      print("Reloading options ...", file=output);
      OptionSet(optdict=bpar.SkZp_Par['optfiledata'][None], optiondb=optiondb);
      if(optiondb['Flg']['debug']): print(bpar.SkZp_Par['optfiledata'][None], file=output);
  OptionFixCheck(raisexc=raisexc);
  OptionIntegrityCheck(raisexc=raisexc);


##############################################
def OptionReadFile(optfile=None, force=False, verb=True, optiondb=None):
  """Read options from an option file. By default, if the file is already loaded internally, it will be just reload.

Parameters
----------
    optfile : str
        Filenames of option file.
    force : bool
        Flag to force an actual reading of the file, instead of just reloading it from memory.
    verb : bool
        Flag to increase the verbosity
    optiondb : as SkZp_Opt
        Database of the options to update. Default SkZp_Opt

Return
------
    int : 
            0: nothing done
            1: file is reread; options are reset
            2: options are reset from previously loaded data
Functions
---------
    OptionSet
""";
  _name_='OptionReadFile';
  if(optiondb is None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
  if(not optfile): return -1;
  if(not force and optfile in bpar.SkZp_Par['optfilelist']):
    OptionReload([optfile]);
    return 2;
  elif(OptionLoadFile(optfile=optfile, verb=verb)>0):
    OptionSet(optdict=bpar.SkZp_Par['optfiledata'][optfile], optiondb=optiondb);
    return +1;
  return 0;


##############################################
def OptionRead(optfiles=None, options=None, instr=None, force=False, raisexc=True, verb=True, optiondb=None):   #RAISE SkZpipeErr
  """Read options from available input. Default in SkZp_Par['optfilenames'], plus the ones listed in 'optfiles', plus the ones given with option 'optfiles', plus the ones in SkZp_DB['SkZp_Opt'][*]['optfiles'].

Parameters
----------
    optfiles : list
        List of filenames of option files
    options : dict
        Dictionary of additional options
    instr : str
        Name of the instrument
    force : bool
        Flag to force an actual reading of the file, instead of just reloading it from memory.
    raisexc : bool
        Flag to set if raise an exception or just print a warning message.
    verb : bool
        Flag to increase the verbosity
    optiondb : as SkZp_Opt
        Database of the options to update. Default SkZp_Opt

Functions
---------
    OptionReadFile
    OptionCheckInput
    OptionSet
    OptionFixCheck
    OptionIntegrityCheck

""";
  _name_='OptionRead';
  from . import database as _db

  if(optiondb is None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");
  if(isinstance(optfiles, str)): optfiles=[optfiles];
  elif(optfiles is None): optfiles=[];
  elif(isinstance(optfiles, collections.abc.Sequence)): optfiles=list(optfiles);
  if(not instr):
      if(optiondb['S']['inputdata:instrument']): instr=optiondb['S']['inputdata:instrument'];

  optfiles=bpar.SkZp_Par['optfilenames']+optfiles;
  for optfile in optfiles:
    OptionReadFile(optfile=optfile, force=force, verb=verb, optiondb=optiondb);

  optfL=optiondb['L']['optfiles'].copy();
  if(instr in _db.SkZp_DB['SkZp_Opt']):
    #Get additional optfiles set for the used instrument
    if(verb): print(_name_+": loading option file for instrumrent {instr} in the internal dataBase".format(instr=instr), file=bpar.SkZp_Par['stdout']);
    optfL=_db.SkZp_DB['SkZp_Opt'][ instr ].get('optfiles', []) + optfL;
  optfL=[x for x in optfL if x not in optfiles];
  for optfile in optfL:
    OptionReadFile(optfile=optfile, force=force, verb=verb, optiondb=optiondb);

  if(options):
    OptionCheckInput(options=options, optiondb=optiondb);
    if(OptionSet(optdict=options, optiondb=optiondb)):
      bpar.SkZp_Par['optfiledata'][None]=options;

  OptionFixCheck(optiondb=optiondb, raisexc=raisexc);
  OptionIntegrityCheck(optiondb=optiondb, raisexc=raisexc);

##############################################
def OptionPhotoFix(optiondb=None, raisexc=True):   #RAISE SkZpipeErr
  """Set internal option database properly for photometry

Parameters
----------
    optiondb : as SkZp_Opt
        Database of the options to fix. Default SkZp_Opt
    raisexc : bool
        Flag to set if raise an exception or just returning None.

""";
  _name_='OptionPhotoFix';
  if(optiondb==None): optiondb=SkZp_Opt;
  if(not isinstance(optiondb, SkZp_Opt.__class__)): raise TypeError(_name_+": `optiondb` must be as SkZp_Opt");

  OptionFixCheck(optiondb=optiondb, raisexc=raisexc);

  for key in ['photo:DAO:pickdeltamag','photo:fittingradius','photo:psf:psfradius','in-outskyradius','photo:psf:inskyradius'] + [ 'photo:thre:'+rt for rt in bpar.SkZp_Par['photo:runtypelist'] ]:
    if(key in optiondb['F']): optiondb['F'][key]= round(optiondb['F'][key], 2);
  optiondb['L']['photo:DAO:varpsf']=[ int(x) for x in optiondb['L']['photo:DAO:varpsf'] ];
  for rt in bpar.SkZp_Par['photo:runtypelist']:
    for key in optiondb['L']['photo:Steps:'+rt]:
      if(not key in bpar.SkZp_Par['photo:StepL']):
        key='';
        break;
    if(not key): optiondb['L']['photo:Steps'+rt]=[];
  
  if(optiondb['S']['progr:path:dir'] and optiondb['S']['progr:path:dir'][-1]!=os.path.sep): optiondb['S']['progr:pathdir']+=os.path.sep;
  if(optiondb['S']['progr:path:DAO'] and optiondb['S']['progr:path:DAO'][-1]!=os.path.sep): optiondb['S']['progr:path:DAO']+=os.path.sep;

  
  if(optiondb['I']['photo:psf:starmin']>=optiondb['I']['photo:psf:starmax'] or optiondb['I']['photo:psf:starmin']>=optiondb['I']['photo:psf:starinit'] or optiondb['I']['photo:psf:starmax']>=optiondb['I']['photo:psf:starinit']):
    raise ValueError("The minimum number of psf stars must be lesser than their inital number or the maximum number of them to be left after the first psf, which must be lesser than initial number.");

  if(optiondb['Flg']['debug']): optiondb['Flg']['debuglog']=True;
  
  if(optiondb['L']['photo:aperture']):
    try:
      optiondb['L']['photo:aperture']=[float(x) for x in optiondb['L']['photo:aperture']];
      if(optiondb['L']['photo:aperture'][0]<0):
        optiondb['L']['photo:aperture']=[int(optiondb['L']['photo:aperture'][0])];
      if(optiondb['L']['photo:aperture'][0]==-1): optiondb['L']['photo:aperture']=[12];
      elif(optiondb['L']['photo:aperture'][0]==0): optiondb['L']['photo:aperture']=[];
    except:
      if(re.search("^N|n|0|F|f",optiondb['L']['photo:aperture'][0])):
        optiondb['L']['photo:aperture']=[];
      elif(':' in optiondb['L']['photo:aperture'][0]):
        tmpl=[float(x) for x in optiondb['L']['photo:aperture'][0].split(':')];
        if(len(tmpl)==2 or tmpl[2]>12): tmpl.append(12);
        else: tmpl[2]=int(tmpl[2]);
        optiondb['L']['photo:aperture']=[];
        step=(tmpl[1]-tmpl[0])/(tmpl[2]-1);
        for ii in range(tmpl[2]):
          optiondb['L']['photo:aperture'].append(round(tmpl[0]+ii*step,2));
        else: optiondb['L']['photo:aperture']=[12];

##############################################
def OptionPassed():   #RAISE SkZpipeErr
  """Print to screen the options that have been set.

Parameters
----------

""";
  _name_='OptionInserted';
  for optfile in bpar.SkZp_Par['optfilelist'].copy():
    print("Origin:", optfile, file=bpar.SkZp_Par['stdout']);
    for key,value in bpar.SkZp_Par['optfiledata'][optfile].items(): 
      print('\t', key,':=', value, file=bpar.SkZp_Par['stdout']);
  if(None in bpar.SkZp_Par['optfiledata']):
    print("As parameter:", file=bpar.SkZp_Par['stdout']);
    for key,value in bpar.SkZp_Par['optfiledata'][None].items(): 
      print('\t', key,':=', value, file=bpar.SkZp_Par['stdout']);



########################################################
########################################################

#??????????????
# LOST options
#??????????????
#SkZp_Opt['S'  ]['extractinput']="extrinput";       SkZp_Opt['_doc_']['extractinput']="""""";
#SkZp_Opt['D'  ]['tagvalue']={};                  SkZp_Opt['_doc_']['tagvalue']="""""";
#SkZp_Opt['L'  ]['justdo']=[];                      SkZp_Opt['_doc_']['justdo']="""""";
#SkZp_Opt['S'  ]['inputdata:project']='';                   SkZp_Opt['_doc_']['inputdata:project']="""name of the project/dataset""";
#SkZp_Opt['S'  ]['chipheaderext']=bpar.SkZp_Par['chipheaderext'];    SkZp_Opt['_doc_']['chipheaderext']="""""";
#SkZp_Opt['S'  ]['mosheaderext'] =bpar.SkZp_Par['mosheaderext'];    SkZp_Opt['_doc_']['mosheaderext']="""""";

#######################
##  OPTIONS  VALUES  ##
#######################
SkZp_Opt['Flg']['skzopt']=False;                  SkZp_Opt['_doc_']['skzopt']="""Set options for the developer""";
SkZp_Opt['L'  ]['optfiles']=[];                    SkZp_Opt['_doc_']['optfiles']="""List of additional option files to read""";
SkZp_Opt['Flg']['butler']=False;                  SkZp_Opt['_doc_']['butler']="""Set options for some automatic setting to make the workflow better""";



 ########################
 ##  Debug Parameters  ##
 ########################
SkZp_Opt['Flg']['debug']        =False;                 SkZp_Opt['_doc_']['debug']="""To quickly activate debug feature. It will set all the verbosity flag to True. """;
SkZp_Opt['_doc_']['debugging']="""Options for debugging. See also option 'debug'.""";
SkZp_Opt['D'  ]['debugging:opt']    ={};                    SkZp_Opt['_doc_']['debugging']="""Dictionary with debugging option""";
SkZp_Opt['Flg']['debugging:full']   =False;                 SkZp_Opt['_doc_']['']="""If activate all the debug features""";
SkZp_Opt['Flg']['debugging:log']    =False;                 SkZp_Opt['_doc_']['']="""If to log all the output and activate verbosity in exception handling""";
SkZp_Opt['S'  ]['debugging:logfile']='skzpipe_debug.log';   SkZp_Opt['_doc_']['']="""Name of the debuglog file""";
SkZp_Opt['I'  ]['debugging:level']   =0;                     SkZp_Opt['_doc_']['']="""""";

SkZp_Opt['S']['debugging:test']='';                      SkZp_Opt['_doc_']['debugging:test']="""""";


SkZp_Opt['_doc_']['output']="""Option for output management""";
SkZp_Opt['Flg']['output:verbose']=False;                SkZp_Opt['_doc_']['output:verbose']="""If the verbosity must be activated""";
SkZp_Opt['I']['output:verbosity']=1;                SkZp_Opt['_doc_']['output:verbosity']="""Set the verbosity level""";


SkZp_Opt['_doc_']['output:stderr']="""Standard error management""";
SkZp_Opt['I'  ]['output:stderr:hide']=0;    SkZp_Opt['_doc_']['']="""To hide the standard error,  redirecting it to /dev/null: 0 normal; 1 the internal standard error is redirect; -1 system standard error is redirect""";
SkZp_Opt['Flg']['output:stderr:shutup']=False;    SkZp_Opt['_doc_']['']="""Silent standard error. As 'stderr:hide'=-1 """;


 #########################
 ##  External Programs  ##
 #########################
SkZp_Opt['_doc_']['progr']="""Options about external programs""";
SkZp_Opt['_doc_']['progr:path']="""Options to specify a particular directory (full path) where the programs of a particular suite are located. To use as defined in PATH, set it as a null string ('').""";
SkZp_Opt['S'  ]['progr:path:dir']="";                     SkZp_Opt['_doc_']['progr:path:dir']="""To specify a particular directory (full path) where external local programs are located. To use as defined in PATH, set it as a null string ('').""";
SkZp_Opt['S'  ]['progr:path:DAO']="";                  SkZp_Opt['_doc_']['progr:path:DAO']="""To specify a particular directory (full path) where DAOPhot programs are located. To use as defined in PATH, set it as a null string ('').""";

SkZp_Opt['_doc_']['progr:exec']="""Options to specify the executable associated with the programs of a particular suite."""
SkZp_Opt['S'  ]['progr:exec:daophot']="daophot";            SkZp_Opt['_doc_']['progr:exec:daophot']="""to specify a particular program or using the one in PATH shell variable """;
SkZp_Opt['S'  ]['progr:exec:allstar']="allstar";            SkZp_Opt['_doc_']['progr:exec:allstar']="""""";
SkZp_Opt['S'  ]['progr:exec:allframe']="allframe";          SkZp_Opt['_doc_']['progr:exec:allframe']="""""";
SkZp_Opt['S'  ]['progr:exec:daomaster']="daomaster";        SkZp_Opt['_doc_']['progr:exec:daomaster']="""""";
SkZp_Opt['S'  ]['progr:exec:daomatch']="daomatch";          SkZp_Opt['_doc_']['progr:exec:daomatch']="""""";
SkZp_Opt['S'  ]['progr:exec:montage2']="montage2";          SkZp_Opt['_doc_']['progr:exec:montage2']="""""";
#
  
SkZp_Opt['I'  ]['progr:maxlogsize']=5;                  SkZp_Opt['_doc_']['progr:maxlogsize']="""Maximum disk space in megabytes for a log file (Some external programs can enter in a loop and chacking the size of their output can help to detect these situations)""";

SkZp_Opt['Flg'  ]['progr:runtimecheck']=True;            SkZp_Opt['_doc_']['progr:runtimecheck']="""Flag to set the check during runtime of some process for log size, rutime, ...""";
SkZp_Opt['DI'  ]['progr:timeout']={};                     SkZp_Opt['_doc_']['progr:timeout']="""Time out for external programs to avoid they got stuck and block the running""";


 ##################
 ##  Management  ##
 ##################
SkZp_Opt['I'  ]['speedup']=0;    SkZp_Opt['_doc_']['speedup']="""Integer to indicate how much to accelerate the procedures. Higher values, less procedure are run:
    -1 : completely disable. Redoing everything, also products of procedures that terminate correctly
     0 : Avoid to redo most obvious existing products, like psf calculation source-list, existing coordinate-transformation file.
     1 : Skip some additional step to improve accuracy.
""";
SkZp_Opt['_doc_']['speedingup']="""Options to accelerate the procedures."""
SkZp_Opt['Flg']['speedingup:ramdisk']=False;                    SkZp_Opt['_doc_']['speedingup:ramdisk']="""If to use a ramdisk to speed up the execution"""

SkZp_Opt['Flg']['justdata']=False;                    SkZp_Opt['_doc_']['justdata']="""It abiltate only the procedures to collect the inputdata, without photometry procedure. It block any photometric procedure, so avoid check of external program."""


SkZp_Opt['I'  ]['minspace']=160;                    SkZp_Opt['_doc_']['minspace']="""Minimum disk space in megabytes required to work (approx: the size of 4 images + the size of 5 catalogs)""";

SkZp_Opt['DFlg']['saferun']={'base':True};                    SkZp_Opt['_doc_']['saferun']="flags for safety of the run. It is used to calculate parameter saferunbit";

SkZp_Opt['_doc_']['locking']="""Option to prevent that 2 scripts are working on the same data""";
#SkZp_Opt['S'  ]['locking:file']="SkZpipe.lock";       SkZp_Opt['_doc_']['locking:file']="""Name of the lock file to prevent the running of another run""";
SkZp_Opt['S'  ]['locking:ext']=".lock";               SkZp_Opt['_doc_']['locking:ext']="""Extension for local  lock file to prevent the running of another run""";



###

SkZp_Opt['S'  ]['SkZp_log']=".SkZpLog";            SkZp_Opt['_doc_']['SkZp_log']="""Extension of the global log file of the procedures"""

SkZp_Opt['_doc_']['backup']="""Options for backup"""
SkZp_Opt['Flg']['backup:image']=False;                SkZp_Opt['_doc_']['backup:image']="""At the end of photometry, if to backup also the image"""
SkZp_Opt['Flg']['backup:inputdata']=True;                SkZp_Opt['_doc_']['backup:inputdata']="""If InputDataWrite will create a backup copy of an existing output file"""

 #######################
 ##  Multiprocessing  ##
 #######################
SkZp_Opt['_doc_']['mp']="""Options for multiprocessing and parallelization""";
SkZp_Opt['I'  ]['mp:nproc']=0;                    SkZp_Opt['_doc_']['mp:nproc']="""Number of processes to use in the parallelization""";
SkZp_Opt['S'  ]['mp:method']='pool';              SkZp_Opt['_doc_']['mp:method']="""Method to use in the parallelization: pool """;




 ##################
 ##  Environment ##
 ##################



 ##################
 ##  Input Data  ##
 ##################

#GLOBAL

SkZp_Opt['_doc_']['image']="""Options for image management  to extract and select them for the run""";

SkZp_Opt['Flg']['image:setcheck']=False;   SkZp_Opt['_doc_']['image:setcheck']="""Check if the observation sets has the same extracting/selecting chip list""";
SkZp_Opt['Flg']['image:uniform']=False;   SkZp_Opt['_doc_']['image:uniform']="""Uniform the chip extraction/selection among the mosaic
    If the instrument has its own 'obs_set_check' in the internal database, for every observation set it will extract/select the same chip set (the biggest set of chips).
    Otherwise for each mosaic it will extract/select the same chip set (the biggest set of chips)""";


#IMAGE Extraction   from mosaic
SkZp_Opt['_doc_']['image:extract']="""Options to select which chip to extract from mosaics. See documentation for function ExtractFromMosaic (parameter `inputdata`, key 'chip':what-to-extract)""";
SkZp_Opt['S'  ]['image:extract:select']="";                  SkZp_Opt['_doc_']['image:extract:select']="""Options in string format to select which chip to extract from mosaics. See documentation for function ExtractFromMosaic (about parameter `inputdata`, description of key 'chip':what-to-extract, string version)""";
SkZp_Opt['D'  ]['image:extract:what']={};                  SkZp_Opt['_doc_']['image:extract:what']="""Dictionary with options to select which chip to extract from mosaics. See documentation for function ExtractFromMosaic (about parameter `inputdata`, description of key 'chip':what-to-extract, dictionary version)""";
SkZp_Opt['DL' ]['image:extract:bytag']={};                  SkZp_Opt['_doc_']['image:extract:bytag']="""Options to select which images to extract: list of values of a tag (as 'tag' key for `select` in function InputDataSelect)""";


#IMAGE Selection   from inputdata
SkZp_Opt['_doc_']['image:select']="""Options to select entries for the run. See documentation for function InputDataSelect (parameter `select`)""";
SkZp_Opt['DL' ]['image:select:bytag']={};                  SkZp_Opt['_doc_']['image:select:bytag']="""Options to select which entries use in the run: list of values of a tag (as 'tag' key for `select` in function InputDataSelect)""";
SkZp_Opt['L'  ]['image:select:bysuffix']=[];                  SkZp_Opt['_doc_']['image:select:bysuffix']="""Options to select which entries use in the run: list of suffix that must exist for each entry (as 'suffix' key for `select` in InputDataSelect funtion)""";
SkZp_Opt['L'  ]['image:select:bymode']=[];                  SkZp_Opt['_doc_']['image:select:bymode']="""Options to select which entries use in the run: a determined set of option for selection (as 'mode' key for `select` in InputDataSelect funtion)""";



SkZp_Opt['F'  ]['image:fwhm']=();                  SkZp_Opt['_doc_']['image:seeing']="""Tuple with minimum and maximum value for FWHM tag. If set, this value is copy in options 'image:select:bytag' and """;

SkZp_Opt['Flg']['image:autochipreject']=False;         SkZp_Opt['_doc_']['autochipreject']="""To reject automatically bad sensors or bad images""";
#
SkZp_Opt['DL' ]['image:standard']={};                 SkZp_Opt['_doc_']['image:standard']="""Dictionary with as only key the name of the tag used to discern standard fields, and  as its value a list of descriptor for standard fields (usually key='OBJECT', value=[names-of-stadard-fields])""";


############################################################################################
#INPUT DATA
SkZp_Opt['_doc_']['inputdata']="""Options regarding inputdata retrievement and processing""";

SkZp_Opt['S'  ]['inputdata:file']="imgdata";          SkZp_Opt['_doc_']['inputdata:file']="""Name of file with inputdata table""";
SkZp_Opt['S'  ]['inputdata:style']="txt";          SkZp_Opt['_doc_']['inputdata:style']="""Style of the file with inputdata table (as `style` of InputDataWrite function)""";
SkZp_Opt['S'  ]['inputdata:delimeter']="\t";          SkZp_Opt['_doc_']['inputdata:delimeter']="""Field delimeter for inputdata""";

SkZp_Opt['S'  ]['inputdata:instrument']='';                SkZp_Opt['_doc_']['inputdata:instrument']="""Name of the instrument""";   #
SkZp_Opt['Flg']['inputdata:instrumentset']=True;           SkZp_Opt['_doc_']['inputdata:instrumentset']="""Set the name of the instrument according to option `instrument` for all the images""";   #

SkZp_Opt['S'  ]['inputdata:sort']='';                 SkZp_Opt['_doc_']['inputdata:sort']="""The name of the tag to use to sort inputlist""";
SkZp_Opt['L' ]['inputdata:taglist']=[];           SkZp_Opt['_doc_']['inputdata:taglist']="""General list of the names of the tags for files with image data without header."""
SkZp_Opt['DL' ]['inputdata:taglist_file']={};           SkZp_Opt['_doc_']['inputdata:taglist_file']="""Dictionary providing the list of the names of the tags for each file with image data. 
Format: filename:['NAME', 'TAG1','TAG2','TAG3']
key None for general tag list or provided not through a file.""";
SkZp_Opt['D'  ]['inputdata:tagdefault']={};        SkZp_Opt['_doc_']['inputdata:tagdefault']="""Dictionary with default values for entry tags. The name of the entry is the same of the tag (upper case). Alternative way to 'inputdata:tag:*' options."""


###################################
SkZp_Opt['_doc_']['inputdata:tag']="""Default values for entry tags. The name of the entry is the same of the tag, but lowercase""";
SkZp_Opt['S'  ]['inputdata:tag:entrytype']='';          SkZp_Opt['_doc_']['inputdata:tag:entrytype']="""Default value for ENTRYTYPE tag. '' for None""";
SkZp_Opt['S'  ]['inputdata:tag:chip']='-';          SkZp_Opt['_doc_']['inputdata:tag:chip']="""Default value for CHIP tag""";
SkZp_Opt['F'  ]['inputdata:tag:sitelat']=-1e3;          SkZp_Opt['_doc_']['inputdata:tag:sitelat']="""Default value for SITELAT tag""";
SkZp_Opt['F'  ]['inputdata:tag:sitelong']=-1e3;          SkZp_Opt['_doc_']['inputdata:tag:sitelong']="""Default value for SITELONG tag""";
###################################


SkZp_Opt['S'  ]['inputdata:action']='';       SkZp_Opt['_doc_']['inputdata:action']="""What to do with the input list:
None/''      : The initialiazing procedure decides by itself (Default)
info         : Just generate the internal information database.
extract      : The images are extracted from mosaic.
extractforce : The images are extracted even the image already exist""";


SkZp_Opt['Flg']['inputdata:readheader']=True;              SkZp_Opt['_doc_']['inputdata:readheader']="""If initialization command has to retrieve data from headers and if to set MJD""";
SkZp_Opt['Flg']['inputdata:readdatabase']=True;            SkZp_Opt['_doc_']['inputdata:readdatabase']="""If initialization command has to retrieve data from headers and database, and if to set MJD""";
SkZp_Opt['Flg']['inputdata:onlyloaddb']=False;           SkZp_Opt['_doc_']['inputdata:onlyloaddb']="""If initialization command has to only read the input database""";
SkZp_Opt['Flg']['inputdata:appendupdate']=False;           SkZp_Opt['_doc_']['inputdata:appendupdate']="""If initialization command has to read the input database, then append and update additional entries""";
SkZp_Opt['Flg']['inputdata:aliasingfix']=True;             SkZp_Opt['_doc_']['inputdata:aliasingfix']="""""";


SkZp_Opt['D'  ]['inputdata:extraheaderkey']={};              SkZp_Opt['_doc_']['inputdata:extraheaderkey']="""""";
SkZp_Opt['L'  ]['inputdata:extradatatag']=[];                SkZp_Opt['_doc_']['inputdata:extradatatag']="""""";
SkZp_Opt['Flg']['inputdata:headeroverride']=False;       SkZp_Opt['_doc_']['inputdata:headeroverride']="""Flag to determine if the data from FITS header have to override the existing data""";

SkZp_Opt['S'  ]['inputdata:workname']='%d';                  SkZp_Opt['_doc_']['inputdata:workname']="""""";

SkZp_Opt['L']['inputdata:imgstat']=['med','mean','std'];          SkZp_Opt['_doc_']['inputdata:imgstat']="""List of the value to be stored in the tag IMGSTAT.\navailable:\n\t'med' : median of the pixel values\n\t'mean' : mean pixel value\n\t'std' : standard deviation of the pixel values\n\t'min' : minimum of the pixel values\n\t'max' : maximum of the pixel values\n""";

#TIME
SkZp_Opt['F'  ]['inputdata:utfix']=0;              SkZp_Opt['_doc_']['inputdata:utfix']="""Correction in hours to apply to 'TIME' tag info to set it in UT time""";
SkZp_Opt['Flg']['inputdata:mjdfix']=True;          SkZp_Opt['_doc_']['inputdata:mjdfix']="""Flag to set Modified Julian Date using 'DATE' and 'TIME' tag info if it is not defined"""  ## ???? always true?
SkZp_Opt['Flg']['inputdata:mjdset']=False;         SkZp_Opt['_doc_']['inputdata:mjdset']="""Flag to set Modified Julian Date using 'DATE' and 'TIME' tag info even if present""";

SkZp_Opt['Flg']['inputdata:nightset']=True;        SkZp_Opt['_doc_']['inputdata:nightset']="""True to set the night number for all the entries""";
SkZp_Opt['F'  ]['inputdata:nightstart']=0.5;       SkZp_Opt['_doc_']['inputdata:nightstart']="""Moment of the day when 'night' starts. Default 0.5 (noon)""";
SkZp_Opt['Flg']['inputdata:nightrel']=True;        SkZp_Opt['_doc_']['inputdata:nightrel']="""True to set the night number as relative (the observation night will be enumerated); False to set the night number as temporal distance (MJD-MJD0+1)""";

###################################
SkZp_Opt['_doc_']['inputdata:am']="""Options for airmass calculation"""
SkZp_Opt['S']['inputdata:am:method']='DR-1';         SkZp_Opt['_doc_']['inputdata:am:set']="""Method to calculate airmass"""
SkZp_Opt['Flg']['inputdata:am:set']=False;         SkZp_Opt['_doc_']['inputdata:am:set']="""Flag to inconditionally set the value of the airmass using 'DATE', 'TIME', 'SITELAT', and 'SITELONG' even if present"""
SkZp_Opt['I']['inputdata:am:check']=-1;         SkZp_Opt['_doc_']['inputdata:am:check']="""Flag to check and conditionally set the value of the airmass.\n  0: no check;\n  -1: check but only warn;\n  +1: check and eventually warn and fix"""
SkZp_Opt['F']['inputdata:am:diff']=0.05;             SkZp_Opt['_doc_']['inputdata:am:diff']="""Reference value to raise a warn/fix the stored airmass. Positive values are for the maximum absolute differences; negative values are for relative differediff. 0 will disable the check."""
###################################


###################################
SkZp_Opt['_doc_']['inputdata:gainronhigh']="""Options for getting GAIN, RON and HIGH tag values"""
SkZp_Opt['S'  ]['inputdata:gainronhigh:file']="gain_ron_high"; SkZp_Opt['_doc_']['inputdata:gainronhigh:file']="""Name of the file with gain, ron(in e-) and highgood value for each chip"""
SkZp_Opt['Flg']['inputdata:gainronhigh:dbforce']=False; SkZp_Opt['_doc_']['inputdata:gainronhigh:dbforce']="""Force to use the values from internal database"""
###################################


###################################
#OUTPUT
SkZp_Opt['_doc_']['inputdata:out']="""Option for the storing of inputdata""";
SkZp_Opt['I'  ]['inputdata:out:headerdataevery']=16;             SkZp_Opt['_doc_']['inputdata:out:headerdataevery']="""The header with names of the tags/fields is written every <value> lines""";
SkZp_Opt['S'  ]['inputdata:out:styleMR']='txt';             SkZp_Opt['_doc_']['inputdata:out:styleMR']="""Default style for machine readable storing (to be used with 'all')""";
SkZp_Opt['S'  ]['inputdata:out:styleUR']='html';             SkZp_Opt['_doc_']['inputdata:out:styleUR']="""Default style for user readable storing (to be used with 'all')"""



##########################
##  PHOTOMETRY OPTIONS  ##
##########################
SkZp_Opt['_doc_']['photo']="Option about photometry";
SkZp_Opt['S'  ]['photo:method']='DAOphot';     SkZp_Opt['_doc_']['photo:method']="""Method to use for the photometric procedures: DAOphot""";
SkZp_Opt['S'  ]['photo:file:tabletype']='astropy';     SkZp_Opt['_doc_']['photo:file:tabletype']="Type of the table to use in PhotoFile: 'numpy' for a simple structured array; 'astropy' for a Table from astropy; 'panda' for a panda table";

SkZp_Opt['D'  ]['photo:gain']={};                        SkZp_Opt['_doc_']['photo:gain']="""""";
SkZp_Opt['D'  ]['photo:ron']={};                         SkZp_Opt['_doc_']['photo:ron']="""""";
SkZp_Opt['D'  ]['photo:high']={};                        SkZp_Opt['_doc_']['photo:high']="""""";

SkZp_Opt['L'  ]['photo:Steps:psfcal']=["Ground", "AddCoo", "AddFph", "ChkAdd", "Refine"];    SkZp_Opt['_doc_']['photo:Steps:psfcal']="""Step for photometric procedure to produce PSF""";
SkZp_Opt['L'  ]['photo:Steps:srclst']=["Ground", "AddCoo", "AddFph", "AddFph", "Refine"];    SkZp_Opt['_doc_']['photo:Steps:srclst']="""Step for photometric procedure to produce source list""";
SkZp_Opt['L'  ]['photo:Steps:photo']=["GetAph"];                                             SkZp_Opt['_doc_']['photo:Steps:photo']="""Step for photometric procedure to produce photometry""";

SkZp_Opt['S'  ]['photo:runtype']="";     SkZp_Opt['_doc_']['photo:runtype']="Default type of image processing (see parameter 'photo:runtypelist')";


SkZp_Opt['Flg']['photo:autofix']=True;           SkZp_Opt['_doc_']['photo:autofix']="""Automatic fix of photometric parameters""";
SkZp_Opt['F'  ]['photo:fittingradius']=0;          SkZp_Opt['_doc_']['photo:fittingradius']="""Fixed fitting radius to be used instead of calculated from fwhm""";
SkZp_Opt['F'  ]['photo:fittingfwhmratio']=1.4;     SkZp_Opt['_doc_']['photo:fittingfwhmratio']="""Ratio fitting radius/fwhm""";
SkZp_Opt['F'  ]['photo:inoutradiusmin']=2;         SkZp_Opt['_doc_']['photo:inoutradiusmin']="""Minimum difference between inner and outer radius""";
SkZp_Opt['F'  ]['photo:in-outskyradius']=11;             SkZp_Opt['_doc_']['photo:in-outskyradius']="""fixed (outer sky radius)-(inner sky radius)""";
SkZp_Opt['F'  ]['photo:psf-inskyradius']=3;              SkZp_Opt['_doc_']['photo:psf-inskyradius']="""fixed (inner sky radius)-(psf radius)""";

SkZp_Opt['F'  ]['photo:find:maxdensity']=0.33;          SkZp_Opt['_doc_']['photo:find:maxdensity']="""Maximum stellar density per FWHM^2. Finding procedure could be wrongly set up. If its result exceeds this density, the procedure will stop. For example, if you expect the mean distance among stars to be greater than 2FWHM, then put 0.25 (=1/2^2)""";

#PSFCAL
SkZp_Opt['_doc_']['photo:psf']="Option about PSF calculation";
SkZp_Opt['S'  ]['photo:psf:done']=".PsfEnded";     SkZp_Opt['_doc_']['photo:psf:done']="Extension for file created when PSF calculation terminates correctly";
SkZp_Opt['Flg']['photo:psf:keep']=True;          SkZp_Opt['_doc_']['photo:psf:keep']="If to protect a PSF calculation that terminated correctly";

SkZp_Opt['I'  ]['photo:psf:starinit']=300;          SkZp_Opt['_doc_']['photo:psf:starinit']="""for daophot/pick: initial number of star to be used to calculate psf."""
SkZp_Opt['I'  ]['photo:psf:starmax']=150;           SkZp_Opt['_doc_']['photo:psf:starmax']="""max number of stars to keep after psf calculation and check after.""";
SkZp_Opt['I'  ]['photo:psf:starmin']=50;            SkZp_Opt['_doc_']['photo:psf:starmin']="""least number of stars to use for psf calculation.""";
SkZp_Opt['I'  ]['photo:psf:starsel_itermax']=10;    SkZp_Opt['_doc_']['photo:psf:starsel_itermax']="""for daophot/pick: maximum number of iteration for selection of PSF stars""";

SkZp_Opt['Flg']['photo:psf:starprereduce']=False;    SkZp_Opt['_doc_']['photo:psf:starprereduce']="""If doing a reduction of number of the psf stars, before the one at the end od the PSF-calculation routine""";

SkZp_Opt['F'  ]['photo:psf:chi2lim']=0;            SkZp_Opt['_doc_']['photo:psf:chi2lim']="""enough-value for chi2 of psf calculation""";
SkZp_Opt['F'  ]['photo:psf:fwhmratio']=1.4;        SkZp_Opt['_doc_']['photo:psf:fwhmratio']="""Maximum ratio between mean fwhm calculated by PSF calculation and given one; to detect error in the process""";
SkZp_Opt['F'  ]['photo:psf:maxellipticity']=1;     SkZp_Opt['_doc_']['photo:psf:maxellipticity']="""Maximum elipticity (actually, flattening 1-b/a) in calculated PSF; to detect error in the process""";



SkZp_Opt['F'  ]['photo:psf:psfradius']=15;         SkZp_Opt['_doc_']['photo:psf:psfradius']="""Fixed psf radius.""";

SkZp_Opt['I'  ]['photo:psf:itermax']=100;          SkZp_Opt['_doc_']['photo:psf:itermax']="""Maximum number of iterations to calculate PSF.""";

#SkZp_Opt['I']['psfresetmax']=20;    SkZp_Opt['_doc_']['']="""maximum number of reiterations to calculate PSF resetting default function.""";





SkZp_Opt['_doc_']['photo:srclst']="Option about source-list creation";
SkZp_Opt['S'  ]['photo:srclst:done']=".SLstDone";     SkZp_Opt['_doc_']['photo:srclst:done']="Extension for file created when source-list creation terminates correctly";
SkZp_Opt['Flg']['photo:srclst:keep']=True;             SkZp_Opt['_doc_']['photo:srclst:keep']="If to protect source-list creation terminated correctly";

SkZp_Opt['Flg']['photo:reg:pos']=False;             SkZp_Opt['_doc_']['photo:reg:src']="""create a .reg file from source-position file""";
SkZp_Opt['Flg']['photo:reg:psf']=False;             SkZp_Opt['_doc_']['photo:reg:psf']="""create a .reg file from psf-source file""";
SkZp_Opt['Flg']['photo:reg:fph']=False;             SkZp_Opt['_doc_']['photo:reg:fph']="""create a .reg file from psf-fitting file""";


SkZp_Opt['S'  ]['photo:initialsrclist']='dao';        SkZp_Opt['_doc_']['photo:initialsrclist']="""How to create the initial source list: 'file' to use '.coooo' file, or give the extension; or uning a specific program"""
SkZp_Opt['S'  ]['photo:createsrclist']='dao';


SkZp_Opt['S'  ]['photo:newsrcto']='';                       SkZp_Opt['_doc_']['newsrcto']="""Append new sources to 'src' or 'fph' files or nothing '' """; 
#

SkZp_Opt['S'  ]['photo:DAO:psfsubsuff']="SS";                SkZp_Opt['_doc_']['photo:DAO:psfsubsuff']="""suffix to the basename for the PSF star-subtracted image""";



SkZp_Opt['Flg']['photo:postfitfix']=True;           SkZp_Opt['_doc_']['']="""Check the new postions after the psf fitting and fix for sources that moved too much away from initial value.""";
SkZp_Opt['Flg']['photo:rejectmoved']=False;            SkZp_Opt['_doc_']['']="""If to reject sources that after psf-fitting photometry have their position moved by more that a given value""";
SkZp_Opt['F'  ]['photo:rejectmovedby:src']=-0.75;            SkZp_Opt['_doc_']['']="""For all the sources: Value of the shift in position to reject a source. Positive values are in unit of the coordinates; negative value are in unit of FWHM.""";
SkZp_Opt['F']['photo:rejectmovedby:psf']=-0.75;            SkZp_Opt['_doc_']['']="""For the sources used to calculate PSF: Value of the shift in position to reject a source. Positive values are in unit of the coordinates; negative value are in unit of FWHM.""";



SkZp_Opt['L'  ]['photo:aperture']=[];                    SkZp_Opt['_doc_']['photo:aperture']="""List of the aperture to use for the photometry.""";
SkZp_Opt['S'  ]['photo:apertureunit']='pixel';           SkZp_Opt['_doc_']['photo:apertureunit']="""Unit for `photo:aperture` values: pixel or arcsec""";


SkZp_Opt['S'  ]['photo:ext:aperture']='.aph';            SkZp_Opt['_doc_']['photo:ext:aperture']="""Extension for aperture photometry file""";
SkZp_Opt['S'  ]['photo:ext:fitting']='.fph';             SkZp_Opt['_doc_']['photo:ext:fitting']="""Extension for psf-fitting photometry file""";
SkZp_Opt['S'  ]['photo:ext:coord']='.koo';               SkZp_Opt['_doc_']['photo:ext:coord']="""Extension for sorce-coordinate file""";
SkZp_Opt['S'  ]['photo:ext:srclst']='.srclst';               SkZp_Opt['_doc_']['photo:ext:srclst']="""Extension for source-list file of stacks""";

##
SkZp_Opt['_doc_']['photo:apcorr']="""About aperture correction for calibration. Exp-time correction will not be applied.""";
SkZp_Opt['S'  ]['photo:apcorr:method']='';
SkZp_Opt['_doc_']['photo:apcorr:method']="""Procedure to calculate the aperture photometry at standard radius for the correction. Exp-time correction will not be applied to the output of the aperture photometry.""";
SkZp_Opt['S'  ]['photo:apcorr:ap0']='';
SkZp_Opt['_doc_']['photo:apcorr:ap0']="""The extension of the file respect to what aperture correction is calculated; in this case the aperture radius will be set to the option 'photo:std:aperture', if 'photo:aperture' is left unset.""";
SkZp_Opt['S'  ]['photo:apcorr:coord']='.alf';
SkZp_Opt['_doc_']['photo:apcorr:coord']="""The extension of the file with the coordinates of the sources that will be used to calculate the aperture correction""";
SkZp_Opt['S'  ]['photo:apcorr:fph']='.alf';
SkZp_Opt['_doc_']['photo:apcorr:fph']="""The extension of the file with psf-fittig photometry that will be used during the aperture photometry""";
SkZp_Opt['S'  ]['photo:apcorr:calc']='dao';
SkZp_Opt['_doc_']['photo:apcorr:calc']="""Procedure to calculate the aperture correction:
   'dao' to use DAOmaster (it use a syntax similarly to the Match method 'makemch', allowing to include the same selection options);
   'lsq' to use a least square fit.""";

##
SkZp_Opt['F'  ]['photo:thre:psfcal']=4;                  SkZp_Opt['_doc_']['photo:thre:psfcal']="""threashold value to be used in psf-calculation procedure""";
SkZp_Opt['F'  ]['photo:thre:srclst']=4.5;                SkZp_Opt['_doc_']['photo:thre:srclst']="""threashold value to be used in source-list procedure""";
SkZp_Opt['F'  ]['photo:thre:photo']=4;                   SkZp_Opt['_doc_']['photo:thre:photo']="""threashold value to be used in photometry procedure""";
SkZp_Opt['DF' ]['photo:thre:range']={'min':0.5,'max':15,'step':1};
SkZp_Opt['_doc_']['photo:thre:range']="""Dictionary defining the range for threashold values to be used in the procedure to determine the most reasonable value. Keys: 'min', 'max','step'.""";

SkZp_Opt['Flg']['photo:exptimecorr']=True;             SkZp_Opt['_doc_']['']="""Apply to photometry obtain with GetAph and GetFph exp-time correction. The new file has '0' at the end.""";
SkZp_Opt['Flg']['photo:ap1line']=False;                 SkZp_Opt['_doc_']['']="""""";

SkZp_Opt['S'  ]['photo:averagedsummed']="1,1";            SkZp_Opt['_doc_']['photo:averagedsummed']="""number of avareged,summed images for find (actually to calculate true values of gain and ron)""";

#Catalogs
SkZp_Opt['Flg']['photo:ctlg']=True;              SkZp_Opt['_doc_']['']="""Options for the realization of final products, catalogs after final photometry""";
SkZp_Opt['Flg']['photo:ctlg:method']='DAOallframe';              SkZp_Opt['_doc_']['']="""Method to produce the catalog photometry: DAOallframe""";
SkZp_Opt['Flg']['photo:ctlg:skip']=False;             SkZp_Opt['_doc_']['']="""Skip the photometric procedure, if the output exists""";
SkZp_Opt['Flg']['photo:ctlg:exptimecorr']=True;             SkZp_Opt['_doc_']['']="""Apply to photometry obtain with GetAph and GetFph exp-time correction. The new file has '0' at the end.""";
SkZp_Opt['Flg']['photo:ctlg:matching']=True;              SkZp_Opt['_doc_']['']="""""";


#Calibration and standars
SkZp_Opt['_doc_']['photo:std']="Option about standards and calibrations";
SkZp_Opt['F'  ]['photo:std:maxellipt']=0.5;                  SkZp_Opt['_doc_']['photo:std:maxellipt']="""Maximum value for ellipticity to use the image as standard field""";
SkZp_Opt['F'  ]['photo:std:aperture']=0;                  SkZp_Opt['_doc_']['photo:std:maxellipt']="""Aperture for the photometry for the calibration""";
SkZp_Opt['DT' ]['photo:std:colorcalibration']={};                  SkZp_Opt['_doc_']['photo:std:colorcalibration']="""For each filter a tuple with the passband to use for the color in the calibration""";
SkZp_Opt['S'  ]['photo:std:storefile']='calibration.coeff';                  SkZp_Opt['_doc_']['photo:std:storefile']="""Filename for the file where save the calibration coefficients""";


##  DAOPHOT OPTIONS  ##
SkZp_Opt['S'  ]['photo:DAO:psfdef']="MOFFAT35";           SkZp_Opt['_doc_']['photo:DAO:psfdef']="""default psf analitic type. """;

SkZp_Opt['L'  ]['photo:DAO:psfother']=["PENNY1", "PENNY2", "MOFFAT25", "GAUSSIAN", "ALLPSF", "MOFFAT15", "LORENTZ"];    SkZp_Opt['_doc_']['photo:DAO:psfother']="""if psf failed, then change ANALITIC following this sequence.""";

SkZp_Opt['I'  ]['photo:DAO:psfothergood']=0;              SkZp_Opt['_doc_']['photo:DAO:psfothergood']="""if default psf continues to fail, how many of the first other psf can be used anyway as definitive psf""";

SkZp_Opt['F'  ]['photo:DAO:pickdeltamag']=1;              SkZp_Opt['_doc_']['photo:DAO:pickdeltamag']="""for daophot/pick: delta mag to be subtracted to the minimum magnitude.""";

SkZp_Opt['S'  ]['photo:DAO:psfsubsuff']="SS";             SkZp_Opt['_doc_']['photo:DAO:psfsubsuff']="""suffix to the basename for the PSF star-subtracted image""";

SkZp_Opt['L'  ]['photo:DAO:varpsf']=[-1, 0, 1, 2];        SkZp_Opt['_doc_']['photo:DAO:varpsf']="""define the order of the Var value during the iterations""";

SkZp_Opt['S'  ]['photo:DAO:allstarinput']="nei";                 SkZp_Opt['_doc_']['photo:DAO:allstarinput']="""Which file allstar should use "ap" (all stars) or "nei" (only the stars near psf stars""";

SkZp_Opt['L']['photo:DAO:daophot_opt']=[];              SkZp_Opt['_doc_']['']="""DAOPhot Option to be passed""";
SkZp_Opt['L']['photo:DAO:photo_opt']=[];                SkZp_Opt['_doc_']['']="""DAOPhot/photometry Option to be passed""";
SkZp_Opt['L']['photo:DAO:allstar_opt']=[];              SkZp_Opt['_doc_']['']="""DAOPhot/Allstar Option to be passed""";

#Allframe
SkZp_Opt['I']['allframe_id0']=0;                 SkZp_Opt['_doc_']['allframe_id0']="""""";
SkZp_Opt['S']['allframe_mchsuff']='_AlfPh';      SkZp_Opt['_doc_']['allframe_mchsuff']="""""";
SkZp_Opt['I']['photo:allframe:niter']=200;      SkZp_Opt['_doc_']['photo:allframe:niter']="""""";
#maximum value for OS Outer Sky radius, from allframe.f


#############################################
#Matching
SkZp_Opt['S'  ]['match:extension']='.mch';        SkZp_Opt['_doc_']['match:extension']="""Extension (with dot) of the file with coordinate relations""";
SkZp_Opt['I'  ]['match:minraditer']=50;        SkZp_Opt['_doc_']['match:extension']="""Extension (with dot) of the file with coordinate relations""";


#############################################
#STACK
 #matching
SkZp_Opt['_doc_']['stack:match']="""Options to produce the coordinate transformations for the stacking""";
SkZp_Opt['S'  ]['stack:match:srcext']='.als';        SkZp_Opt['_doc_']['stack:match:srcext']="""Extension (with dot) of the photometric file to be used to calculate the first matching relations""";
SkZp_Opt['S'  ]['stack:match:suff']='_S0';        SkZp_Opt['_doc_']['stack:match:suff']="""Suffix for the basename of the file with the first matching relations""";
SkZp_Opt['L"' ]['stack:match:makemode']=['dao:<p20,[1', 'dao:<p25,[0.75', 'dao:<p33,[0.5'];    SkZp_Opt['_doc_']['stack:match:makemode']="""Match.makemch mode to create the first matching relations""";
SkZp_Opt['Flg']['stack:match:refineforce']=False;         SkZp_Opt['_doc_']['stack:match:refineforce']="""If to refine anyway (but skipping the first "looser" one), or only if the matching relations are created""";
SkZp_Opt['LD' ]['stack:match:refineparam']=[];         
SkZp_Opt['_doc_']['stack:match:refineparam']="""\
List of dictionaries with parameters for each run of DAOmaster to refine the coordinmate transformations. Each dictionary can contain some of the following (o none): 
    'flag', 'sigma', 'ncoeff' : as the DAOmaster parameters
  from parameter `radius`, split in three:
    'radius' : starting value only,
    'minradius : final matching radius,
    'step' : if positive, step of the decrease; if negative, number of steps
  from parameter `opt`:
    'magperc' : cut in magnitude using percentile,
    'sharpcut' : simmetric cut in sharp.
The first refining is for the new made table (usually a little looser, default using 6 coefficients).
The number of elements of the list (parameter sets) determines how many iteration of DAOmaster will be done: giving just 1 set will do only one refine run, the first.
Any missing values will be replaced with the one used in the previous set, so an empty dictionary ({}) will casue to copy the previous set of parameters. 
""";

SkZp_Opt['_doc_']['stack:match:improvepos']="""Options for the source-position improvement to produce better  coordinate transformations""";
SkZp_Opt['S'  ]['stack:match:improvepos:with']='allframe';    SkZp_Opt['_doc_']['stack:match:improvepos:with']="""Procedure to improve the positions of the sources for a better coordinate transformations and stack""";
SkZp_Opt['S'  ]['stack:match:improvepos:suff']='_S1';  SkZp_Opt['_doc_']['stack:match:improvepos:suff']="""Suffix for the matching file using the source-position improve procedure """;
SkZp_Opt['I'  ]['stack:match:improvepos:mode']=-1;      SkZp_Opt['_doc_']['stack:match:improvepos:mode']="""Mode for the source-position position: 1 always doing it; 0 not doing it; -1 doing it only if the products are missing""";

SkZp_Opt['D'  ]['stack:match:improvepos:param']={'allframe':{'niter':50}};    SkZp_Opt['_doc_']['stack:match:improvepos:param']="""Parameter for the program to use to improve the positions""";
SkZp_Opt['D'  ]['stack:match:improvepos:refineparam']={};         SkZp_Opt['_doc_']['stack:match:improvepos:refineparam']="""Same as 'stack:match:refine, but for just 1 run of DAOmaster'.\n"""+SkZp_Opt['_doc_']['stack:match:refineparam'];

 #stacking
SkZp_Opt['_doc_']['stack']="""Options for the stacking""";
SkZp_Opt['S'  ]['stack:bytag']='';               SkZp_Opt['_doc_']['stack:bytag']="""Name of the tag to determined how to group the frames for the stacking""";
SkZp_Opt['S'  ]['stack:suff']='_S';              SkZp_Opt['_doc_']['stack:suff']="""Suffix to add for the filename of the stack image""";
SkZp_Opt['S'  ]['stack:substacktag']='';         SkZp_Opt['_doc_']['stack:substacktag']="""Name of the tag to determined how to subgroup the frames for a additional substacking (the final stack will be obtained averaging the substack images)""";
SkZp_Opt['I'  ]['stack:par:minframe']=2;               SkZp_Opt['_doc_']['stack:par:minframe']="""Stacking parameter: minimum number of frames where a pixel must appear to be included in the stack""";
SkZp_Opt['I'  ]['stack:par:maxframe']=13;               SkZp_Opt['_doc_']['stack:par:maxframe']="""Stacking parameter: maximum number of frames to use in the stack (montage2)""";
SkZp_Opt['F'  ]['stack:par:percentile']=0.5;         SkZp_Opt['_doc_']['stack:par:percentile']="""Stacking parameter: percentile of the pixel values to select the valued for the pixel in the stack image""";
SkZp_Opt['DI'  ]['stack:tagpar:minframe']={};               SkZp_Opt['_doc_']['stack:tagpar:minframe']="""Stacking parameter for specific tag value: minimum number of frames where a pixel must appear to be included in the stack""";
SkZp_Opt['DI'  ]['stack:tagpar:maxframe']={};               SkZp_Opt['_doc_']['stack:tagpar:maxframe']="""Stacking parameter: maximum number of frames to use in the stack (montage2)""";
SkZp_Opt['DF'  ]['stack:tagpar:percentile']={};         SkZp_Opt['_doc_']['stack:tagpar:percentile']="""Stacking parameter for specific tag value: percentile of the pixel values to select the valued for the pixel in the stack image""";

SkZp_Opt['F'  ]['stack:sky0']=2000.;             SkZp_Opt['_doc_']['stack:sky0']="""Constant value to be added to the sky (to all the pixels) of the stack image""";
SkZp_Opt['Flg']['stack:wcsfix']=True;            SkZp_Opt['_doc_']['stack:wcsfix']="""Whether the WCS has to be fix correcting the CRPIX values by the offset""";
SkZp_Opt['F'  ]['stack:mask:low']=-1.0e3;         SkZp_Opt['_doc_']['stack:mask:low']="""Minimum valid pixel value for the stack image (pixels with lower values will be set to it)""";
SkZp_Opt['F'  ]['stack:mask:high']=+2.5e5;        SkZp_Opt['_doc_']['stack:mask:high']="""Maximum valid pixel value for the stack image (pixels with higher values will be set to it)""";
SkZp_Opt['F'  ]['stack:mask:fill']=-1.05;         SkZp_Opt['_doc_']['stack:mask:fill']="""Value to be used to fill pixels without valid result during averanging substack images""";







OptionFixCheck(raisexc=False)
