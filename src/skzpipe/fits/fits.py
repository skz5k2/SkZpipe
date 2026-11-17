"""Module with funtions to manipulate FITS images
"""

import os, re, math, shutil, datetime
import astropy.io.fits as pyfits
from astropy import wcs
import numpy

from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters  import options as _opt
from .. import functions as funct
from . import _fitsC 

##TEMPLATE for function (20 lines)
############
def TEMPXXYYZZ(image=None):
    """Template of function and its Description

Parameters
----------
    image : str
        Name of the image
    x : obj
        X

Returns
-------
    x
""";
    _name_='XXYYZZ';
    if(not os.path.exists(image)):
        if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
        else: raise IOError(_name_+": No input file "+image);

############
def basenameFITS(image=None):
    """Check the input name for existance and return the fullname and basename

Parameters
----------
    image : str
        Name of the image. Dot must be used only to separate the extension.

Returns
-------
    Tuple with basename and full name
""";
    _name_='basenameFITS'

    import pathlib
    pathfn=pathlib.Path(image)
    basen=None
    exten=None

    if(not os.path.exists(image)):
        if(pathfn.suffix in bpar.SkZp_Par['FITSextension']):
            return None,None

        for ext in bpar.SkZp_Par['FITSextension']:
            if(os.path.exists(image+ext)): exten=ext
        if(exten):
            basen=image
    else:
        if(pathfn.suffix in bpar.SkZp_Par['FITSextension']):
            basen,exten=pathfn.stem,pathfn.suffix

    return basen,exten

############
def isfits(image=None):
    """Check if a file is related to FITS.

Parameters
----------
    image : str
        Name of the image
    

Returns
-------
    result : dict
        Dictionary with
            'name' : str
                Input filename
            'flag' : int
                Flag (4-bit integer) resuming the characteristics.
                First bit set to 1 (+1), if it can be open as a fits (and exists, obviously).
                Second bit set to 1 if it has 3 or more HDU (+2).  (First bit has to be 1; forth bit 0 if it has 1 or 2 HDU )
                Third bit set to 1 if it has a classic FITS extension (parameter 'image_extension') (+4)
                Forth bit set to 1 if it has a mosaic FITS extension (parameter 'mosaic_extension') (+8)
                0 if it is none of the above.
            'nhdu' : int
                Number of HDU ( 0 if errors; -1 if not exists)
            'ext' : int
                Flag about if the filename includes a FITS extension as defined by parameters 'image_extension' (1) or 'mosaic_extension' (-1)
            'check' : int
                Exitcode of check_file
            'base' : int
                Flag (4 bit integer) about if the filename is the basename of a FITS 
                If `image` doesn't exist, the function checks if the file exists adding a FITS extension:
                    First bit set to 1 if it exist adding parameter 'image_extension' (+1)
                    Second bit set to 1 if if it can be open as a fits adding parameter 'image_extension' (+2)

                    Third bit set to 1 if it exists adding parameter 'mosaic_extension' (+4)
                    Forth bit set to 1 if it can be open as a fits adding parameter 'mosaic_extension' (+8)
        If `image` is not defined, the dictionary is empty

""";
    _name_='isfits';
    flag=0; base=0; chk=-1
    ret={'name': image, 'flag':flag, 'nhdu':0, 'ext': 0, 'check':-1}
    if(not image): return {} #No input
    from ..functions import check_file
    chk=check_file(image, raisexc=False) # 0 if OK; tuple(name, exitcode); exitcode= 255 name toolong, -1 not exist or too short, 1 None
    nhdu=-1
    try:
        with pyfits.open(image) as fitso:
            flag+=1
            nhdu=len(fitso)
            if(nhdu>2): flag+= 2
    except FileNotFoundError:
        pass
    except:
        print(f">> Error in {image} <<", file=bpar.SkZp_Par['stderr'], flush=True)
        raise
    if(  image.endswith(bpar.SkZp_Par['image_extension'])):   flag+=4; ret['ext']=1
    elif(image.endswith(bpar.SkZp_Par['mosaic_extension'])): flag+=8; ret['ext']=-1

    if(chk):
        chk=chk[1]
        if(chk==-1 and ret['ext']==0 ):
                chkb=check_file(image+bpar.SkZp_Par['image_extension'], raisexc=False); #again with +.fits
                if(chkb==0): #exists
                    base+=1
                    try:
                        with pyfits.open(image+bpar.SkZp_Par['image_extension']) as fitso: #check if fits
                            if(len(fitso)>0): base+=2
                    except:
                        pass
                chkb=check_file(image+bpar.SkZp_Par['mosaic_extension'], raisexc=False); #again with +.fit
                if(chkb==0): #exists
                    base+=4
                    try:
                        with pyfits.open(image+bpar.SkZp_Par['mosaic_extension']) as fitso: #check if fits
                            if(len(fitso)>0): base+=8
                    except:
                        pass

    ret.update({'flag':flag, 'nhdu':nhdu, 'check':chk, 'base':base})

    return ret

############
def listextname(image=None):
    try:
        with pyfits.open(image) as fitso:
            return [x[1] for x in fitso.info(False)];
    except:
        return [];

###
############
def headeredit(image=None, hdu=0, values=None):
    """Edir the header of a HDU in a FITS file.

Parameters
----------
    image : str
        Name of the FITS image file
    hdu : int,str
        Number or name of the hdu whose header has to be edited.
    values : dict
        Directory with the new values for the cards. None to delete the card. 

Return
------
   ret : tuple of int
        Tuple with number of edited and deleted cards.
""";
    _name_='headeredit';
    if(not os.path.exists(image)):
        if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
        else: raise IOError(_name_+": No input file "+image);
    if(not (isinstance(hdu, int) and hdu>=0) and not isinstance(hdu, str)): raise TypeError(_name_+": 'hdu' must be an no-negative integer or the name of the HDU.");
    if(not isinstance(values, dict)): raise TypeError(_name_+": 'values' must be a dictionary.");


  
#  return _fitsC.hdredit(image, hdu, values);

#  kdelL=[];
#  for key in tuple(values.keys()):
#    if(values[key] is None):
#      kdelL.append(key);
#      del values[key];
    nedit,ndel=0,0;
    if(values):
        with pyfits.open(image, 'update') as hdulist:
            nhdu=len(hdulist);
            if(isinstance(hdu,int)):
                if(hdu>nhdu): raise IndexError("There are just {:d} hdu. Asked for {:d}.".format(nhdu, hdu));
            elif(not hdu in hdulist): raise IndexError("Asked for {:d}, but not present.".format(nhdu, hdu));
      
            for key,value in values.items():
                if(key in hdulist[hdu].header):
                    if(value is None):
                        del hdulist[hdu].header[key];
                        ndel+=1;
                    else:
                        hdulist[hdu].header[key]=value;
                        nedit+=1;
            hdulist.close(output_verify="fix+warn" if( _opt.SkZp_Opt['Flg']['debug']) else "silentfix" );
#  if(kdelL): _fitsC.hdrerase(image, kdelL);

    return (nedit,ndel);

###
############
def headerextract(image=None, hdu=0, output=None, samepath=False, cards=None):
  """Extract the header from a HDU in a FITS file. It writes it down as a text file, or return as a dict.

Parameters
----------
    image : str
        Name of the FITS image file
    hdu : int,str
        Number or name of the hdu whose header has to be extracted.
    output : str, None
        Filename of the output, or None (default) to return the header as a dict. If it is '', the filename 
        is based on the input filename.
    samepath : bool
        True to store the file with header data in the same directory of the image. False to store it in the current directory.
    cards : None, list of str
        If `output` is None, the list of the card keys to return.

Return
------
   ret : None, dict
        If `output` is set, it returns None (and it writes the header to a file.
        If `output` is None, it return the header as dict
""";
  _name_='headerextract';
  if(not isinstance(image,str)): raise TypeError(_name_+": `image` must be a string");
  if(output is not None and not isinstance(output,str)): raise TypeError(_name_+": `output` must be a string or None");
  if(output is None and cards is not None):
    if(not isinstance(cards,(list,tuple))): raise TypeError(_name_+": `cards` must be a list or tuple of str, or None");
    for card in cards:
      if(not isinstance(card,str)): raise TypeError(_name_+": `cards` must be a list or tuple of str, or None");

  if(not os.path.exists(image)):
    if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
    else: raise IOError(_name_+": No input file "+image);
  if(not (isinstance(hdu, int) and hdu>=0) and not isinstance(hdu, str)): raise TypeError(_name_+": hdu must be an no-negative integer or the name of the HDU.");
  (dirname, basenamext)=(os.path.dirname(image), os.path.basename(image)); 
  chdr=bpar.SkZp_Par['chipheaderext'];
  mhdr=bpar.SkZp_Par['mosheaderext'];
  basename=basenamext.rsplit('.',1)[0] 
  with pyfits.open(image) as hdulist:
    nhdu=len(hdulist);
    if(isinstance(hdu,int)):
      if(hdu>nhdu): raise IndexError("There are just {:d} hdu. Asked for {:d}.".format(nhdu, hdu));
    elif(not hdu in hdulist): raise IndexError("Asked for {:d}, but not present.".format(nhdu, hdu));
#    ocard=hdulist[0].header['OBJECT'];
    if(hdu==0 or nhdu>1):
      if(output is None):
        if(hdu==0):
          if(cards is not None):
            return dict( (key,val) for key,val in hdulist[hdu].header.items() if(key in cards and key in hdulist[hdu].header) );
          else:
            return dict(hdulist[hdu].header);
      else:
        fn_out=(output if(output) else (dirname+os.sep if(samepath) else '') + basename ) + (mhdr if(nhdu>1) else chdr);
        with open(fn_out, 'w') as f_out:
          f_out.write(repr(hdulist[0].header));
          f_out.write("END\n");
   #########################
    if(hdu>0):
      if(output is None):
        if(cards is not None):
          return dict( (key,val) for key,val in hdulist[hdu].header.items() if(key in cards and key in hdulist[hdu].header) );
        else: return dict(hdulist[hdu].header);
      else:
        fn_out=(output if(output) else (dirname+os.sep if(samepath) else '') + basename ) + chdr;
        with open(fn_out, 'w') as f_out:
          f_out.write(repr(hdulist[hdu].header));
          f_out.write("END\n");
      
###
############
def extractchip(image=None, hdu=None, output=None, output_verify='ignore'):
  """Extract a chip from a FITS file.

Parameters
----------
    image : str
        Name of the FITS image file
    hdu : int,str
        Number or name of the hdu that has to be extracted.
    output : str
        Name of output image

Return
------
   None
""";
  _name_='extractchip';
  if(not os.path.exists(image)):
    if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
    else: raise IOError(_name_+": No input file "+image);
  if(not output): raise ValueError(_name_+": output name not given");
  if(not (isinstance(hdu, int) and hdu>0) and not isinstance(hdu, str)): raise TypeError(_name_+": hdu must be a positive integer or the name of the HDU.");
  with pyfits.open(image) as hdulist:
    nhdu=len(hdulist);
    if(nhdu<2): return -1;
    if(os.path.exists(output)): os.unlink(output);
    pyfits.writeto(output, data=hdulist[hdu].data.astype(numpy.float32), header=hdulist[hdu].header, output_verify=output_verify);
    headerextract(output, output=''); #extract chip header
    headerextract(image, 0, output=''); #extract mos header
    os.symlink(image.rsplit('.',1)[0]+bpar.SkZp_Par['mosheaderext'], output.rsplit('.',1)[0]+bpar.SkZp_Par['mosheaderext'])

###########
def statimage(image=None, hdu=None, area=None, minval=None, maxval=None, sigmaclip=None, niter=None, typeoutput='dict'):
    """Returns stastistics of the FITS

Parameters
----------
    image : str
        Name of the FITS image file
    hdu : int or tuple of 2 int or list of 2 int
        Selection of the chips to be analized. None or '*' for all.
    area : None
        Not implemented
    minval : float
        Minimum value of a pixel to be used in the statistics
    maxval : float
        Maximum value of a pixel to be used in the statistics
    sigmaclip : float, None
        Value of sigma clipping to apply to pixel values. If None, then 'sigmgaclip' and 'niter' will be set to 0.
    niter : int, None
        Number of iteration of the sigma clipping. If None, then 'sigmgaclip' and 'niter' will be set to 0.
    typeoutput : tuple, dict
        Tuple/dict

Return
------
   A list of tuple or dict, according to parameter 'typeoutput', one for each hdu analysed;
   dict  => {'#hdu':hdu_id, 'nx':naxis[0], 'ny':naxis[1], 'npxl':naxis[0]*naxis[1], 'sum':sumpxl, 'mean':mean, 'med':median, 'std':std-dev, 'min':minpxl, 'max':maxpxl, 'npxl':npxl }
   tuple follows the same order.

""";
    _name_='statimage';
    if(not os.path.exists(image)):
        if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
        else: raise IOError(_name_+": No input file "+image);
    if(not re.search('tuple|dict', typeoutput)): raise ValueError(_name_+": Wrong value for 'typeoutput' (a string 'tuple'/'dict')");
    try:
        with pyfits.open(image) as hdulist:
            nhdu=len(hdulist);
            if(hdu is None or hdu=='*'): hdu=(0,0) if(nhdu==1) else (1,nhdu-1);
            elif(isinstance(hdu,int) and 0<=hdu<nhdu): hdu=(hdu,hdu);
            elif( isinstance(hdu, (list,tuple)) and len(hdu)!=2 ): raise ValueError(_name_+": 'hdu' must be a tuple of 2 elements with first and last hdu.");
            if((minval is not None and not isinstance(minval, (float,int))) or (maxval is not None and not isinstance(maxval, (float,int))) ): raise ValueError(_name_+": 'minval' and 'maxval' must be None or a number");
            if(sigmaclip is None or niter is None): sigmaclip, niter=0,0;
            if(not isinstance(sigmaclip, (float,int)) or sigmaclip<0): raise TypeError(_name_+": 'sigmaclip' must be a no-negative number or None ");
            if(not isinstance(niter, int) or niter<0): raise TypeError(_name_+": 'niter' must be a no-negative integer or None ");
            
            statL=[];
            hduiter=hdu if(isinstance(hdu,list)) else range(hdu[0], hdu[1]+1);
            for hdi in hduiter:
                ndim=hdulist[hdi].header['naxis'];
                if(ndim!=2):
                    statL.append(() if('tuple' in typeoutput) else {});
                    continue;
                naxis=hdulist[hdi].data.shape;
                naxis=(naxis[1], naxis[0]);
                if(minval is not None or maxval is not None):
                    tmpa=hdulist[hdi].data.copy();
                    if(minval is not None): tmpa=tmpa[tmpa>=minval];
                    if(maxval is not None): tmpa=tmpa[tmpa<=maxval];
                    sumpxl, mean, med, std, minpxl, maxpxl, npxl =  tmpa.sum(), tmpa.mean(), numpy.median(tmpa), tmpa.std(dtype=numpy.float64), tmpa.min(), tmpa.max(), tmpa.size;
                else:
                    sumpxl, mean, med, std, minpxl, maxpxl, npxl = hdulist[hdi].data.sum(), hdulist[hdi].data.mean(), numpy.median(hdulist[hdi].data), hdulist[hdi].data.std(dtype=numpy.float64), hdulist[hdi].data.min(), hdulist[hdi].data.max(),  hdulist[hdi].data.size;
                for ii in range(niter):
                    minval, maxval=mean-sigmaclip*std, mean+sigmaclip*std;
                    tmpa=hdulist[hdi].data.copy();
                    tmpa=tmpa[tmpa>=minval];
                    tmpa=tmpa[tmpa<=maxval];
                    sumpxl, mean, med, std, minpxl, maxpxl, npxl = tmpa.sum(), tmpa.mean(), numpy.median(tmpa), tmpa.std(dtype=numpy.float64), tmpa.min(), tmpa.max(), tmpa.size;
                  
                if('tuple' in typeoutput):
                    statL.append( (hdi, naxis[0], naxis[1], naxis[0]*naxis[1], sumpxl, mean, med, std, minpxl, maxpxl, npxl, (sigmaclip,niter)) );
                else:
                    statL.append( {'#hdu':hdi, 'nx':naxis[0], 'ny':naxis[1], 'npxl':naxis[0]*naxis[1], 'sum':sumpxl, 'mean':mean, 'med':med, 'std':std, 'min':minpxl, 'max':maxpxl, 'npxl':npxl, 'sigmaclip':(sigmaclip,niter)} );
    except:
        print(f">> Error in {image} <<", file=bpar.SkZp_Par['stderr'], flush=True)
        raise
    if(len(statL)>1):
        return statL;
    else:
        return statL[0];

###########
def freqpxlval(image=None, hdu=None, area=None, minval=None, maxval=None, width=None, nbin=None):
    """Returns stastistics of the FITS

Parameters
----------
    image : str
        Name of the FITS image file
    hdu : int or tuple of 2 int or list of 2 int
        Selection of the chips to be analized. None or '*' for all.
    area : None
        Not implemented
    minval : float
        Minimum value of a pixel to be used in the statistics
    maxval : float
        Maximum value of a pixel to be used in the statistics
    width : float
        Width of the bins
    nbin : int
        Number of bins

Return
------
    Tuple with array of the pixel values and frequencies. Or a list of tuples.

""";
    _name_='freqpxlval';
    if(not os.path.exists(image)):
        if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
        else: raise IOError(_name_+": No input file "+image);
    
    outL=[];
    from ..mathfunct  import convfreq2d, freq_index2val, freq_val2index
    with pyfits.open(image) as hdulist:
        nhdu=len(hdulist);
        if(hdu is None or hdu=='*'): hdu=(0,0) if(nhdu==1) else (1,nhdu-1);
        elif(isinstance(hdu,int) and 0<=hdu<nhdu): hdu=(hdu,hdu);
        elif( isinstance(hdu, (list,tuple)) and len(hdu)!=2 ): raise ValueError(_name_+": `hdu` must be a tuple of 2 elements with first and last hdu.");
        if( (minval is not None and not isinstance(minval, (float,int))) or (maxval is not None and not isinstance(maxval, (float,int))) ): 
            raise ValueError(_name_+": `minval` and `maxval` must be None or a number");
        if( width is not None): 
            if(not isinstance(width, (float,int)) ): raise ValueError(_name_+": `width` must be None or a positive number");
            if( width<=0 ): raise ValueError(_name_+": `width` must be None or a positive number");
        if( nbin is not None): 
            if(not isinstance(nbin, int) ): raise ValueError(_name_+": `nbin` must be None or a positive integer");
            if( nbin<=0 ): raise ValueError(_name_+": `nbin` must be None or a positive integer");
      
        hduiter=hdu if(isinstance(hdu,list)) else range(hdu[0], hdu[1]+1);
        for hdi in hduiter:
            ndim=hdulist[hdi].header['naxis'];
           # if(ndim!=2):
           #     outL.append(numpy.array([]));
           #     continue;
            tmpa=hdulist[hdi].data.flatten();
            wd,nb=width,nbin
            if(minval is not None or maxval is not None):
                if(minval is not None): tmpa=tmpa[tmpa>=minval];
                if(maxval is not None): tmpa=tmpa[tmpa<=maxval];
            minpxl, maxpxl, npxl = tmpa.min(),tmpa.max(),tmpa.size;
            if(not wd): 
                wd=(maxpxl-minpxl+1)/nb if(nb) else 1
            convfr=convfreq2d(datain=tmpa, options=[{'min':minpxl, 'max':maxpxl+1, 'wd':wd, 'st':wd*0.25}], excl=None, shape='box', verb=False)
            outL.append( ( freq_index2val(numpy.arange(0,len(convfr)), minpxl, wd, 0.25*wd) , convfr) )

    if(len(outL)>1):
        return outL;
    else:
        return outL[0];
  
#######
def testimage(image=None):
  """

Parameters
----------
    image : str
        Name of the FITS image file
    
Return
------
   out : bool
        Return if the image seems valid.
""";
  _name_='testimage';
  statD=statimage(image);
  if(statD['std']==0): return False;
  if(statD['max']==statD['min']): return False;
  if(statD['npxl']==0): return False;

  return True;


###########
def maskval(image=None, minval=None, maxval=None, outval=None, output=None):
  """Create an image changing the pixel values according their position respect the specified range [minval;maxval]. 

Parameters
----------
    image : str
        Filename of the first image with or without '.fits' extension.
    minval : float
        Minimum value for the pixel value to be selected
    maxval : float
        Maximum value for the pixel value to be selected
    outval : tuple
        Tuple of three value to be used for the output image, respectevely in order: less than the selected range, inside the selected range, greater than the selected range. The values must be a float or None to use the original value.
  
""";
  _name_='maskval';
  if(not os.path.exists(image)):
    if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
    else: raise IOError(_name_+": No input file "+image);
  basename=func.remove_extension(image) 
  if(minval is None and maxval is None): raise ValueError(_name_+": both 'minval' and 'maxval' are undefined");
  if(minval is not None and not isinstance(minval, (int,float)) ): raise TypeError(_name_+": 'minval' must be None or int/float.")
  if(maxval is not None and not isinstance(maxval, (int,float)) ): raise TypeError(_name_+": 'maxval' must be None or int/float.")
  if( not isinstance(outval, (list,tuple)) or len(outval)!=3 ): raise TypeError(_name_+": 'outval' must be a list/tuple of 3 elements.");
  for val in outval:
    if(val is not None and not isinstance(val, (int, float))): raise TypeError(_name_+": 'outval' must be a 3-element list/tuple of None or int/float.")

  if(output is None): output=basename+"-0.fits";

  shutil.copy(image, output);
  with pyfits.open(output, 'update') as image:
    if(minval is not None and outval[0] is not None): image[0].data[image[0].data<minval]=outval[0];
    if(maxval is not None and outval[2] is not None): image[0].data[image[0].data>maxval]=outval[2];
    if(all(x is not None for x in (minval, maxval, outval[1]))): image[0].data[minval<=image[0].data<=maxval]=outval[1];
    image.close(output_verify="fix+warn" if( _opt.SkZp_Opt['Flg']['debug']) else "silentfix" );
      

###########
def arith(elem1=None, oper=None, elem2=None, output=None, output_type=numpy.float32, output_verify='silentfix+warn', overwrite=True):
  """Do arithmetic calculation among fits images.

Parameters
----------
    elem1 : str
        Filename of the first image with or without `.fits` extension.
    oper : str
        Operation: `aA+` for sum, `sS-` for subtraction, `mMx*` for
        moltiplication, `dD/` for division, 'e^' for power, `lL` for logarithm, `iI` for ???? 
    elem2 : str, float
        Filename of the second image with or without `.fits` extension, or numeric value
    output : str
        Filename of the output image
    output_type : Numpy data type
        Data type for the output. Default: float32
    overwrite : bool
        If `True`, and if filename already exists, it will overwrite
        the file.  Default is `True`.

""";
  _name_='arith';
  if(not os.path.exists(elem1)):
    if(os.path.exists(elem1+bpar.SkZp_Par['image_extension'])): elem1+=bpar.SkZp_Par['image_extension'];
    else: raise IOError(_name_+": No input file "+elem1);
  if(isinstance(elem2, str)): 
    if(not os.path.exists(elem2)):
      if(os.path.exists(elem2+bpar.SkZp_Par['image_extension'])): elem2+=bpar.SkZp_Par['image_extension'];
      else: raise IOError(_name_+": No input file "+elem2);
  elif(not isinstance(elem2, (int,float))): raise TypeError(_name_+": elem2 must be an existing image or a numerical value");
  if(output is None): raise ValueError(_name_+": 'output' must be a filename")

  if  (re.search('[aA+]',oper[0])): oper='+';
  elif(re.search('[sS-]',oper[0])): oper='-';
  elif(re.search('[mM*x]',oper[0])): oper='*';
  elif(re.search('[dD/]',oper[0])): oper='/';
  elif(re.search('[e^]',oper[0])): oper='e';
  elif(re.search('[lL]',oper[0])): oper='l';
  elif(re.search('[iI]',oper[0])): oper='i';
  else: raise ValueError(_name_+": wrong operation");

  
  with pyfits.open(elem1) as image1:
    nhdu=len(image1);
    if(nhdu>1):   raise SkZpipeError("NHDU>1! Not working well", exclocus=_name_);
    if(isinstance(elem2, str)):
      with pyfits.open(elem2) as image2:
        if(len(image2)!=nhdu): raise SkZpipeError(_name_+": the two fits have different number of hdu.");
        itr=range(1) if(len(image1)==1) else range(1,len(image1));
        for hdu in itr:
          if(image2[hdu].data.shape!=image1[hdu].data.shape): raise SkZpipeError(_name_+": the two images {} and {} have different shape at hdu={:d}.".format(elem1, elem2, hdu));
          if(  oper=='+'): data=image1[hdu].data.astype(output_type) + image2[hdu].data.astype(output_type);
          elif(oper=='-'): data=image1[hdu].data.astype(output_type) - image2[hdu].data.astype(output_type);
          elif(oper=='*'): data=image1[hdu].data.astype(output_type) * image2[hdu].data.astype(output_type);
          elif(oper=='/'): data=image1[hdu].data.astype(output_type) / image2[hdu].data.astype(output_type);
    else:
      itr=range(1) if(nhdu) else range(1,nhdu);
      for hdu in itr:
        if(  oper=='+'): data=image1[hdu].data.astype(output_type)+elem2;
        elif(oper=='-'): data=image1[hdu].data.astype(output_type)-elem2;
        elif(oper=='*'): data=image1[hdu].data.astype(output_type)*elem2;
        elif(oper=='/'): data=image1[hdu].data.astype(output_type)/elem2;
    pyfits.writeto(output, data=data, header=image1[0].header, output_verify=output_verify, overwrite=overwrite);
  with pyfits.open(output, 'update') as image:
    image[0].header.set('operatio', "{:} {:} {:}".format(elem1, oper, str(elem2)), 'Created with SkZpipe');
    image.close(output_verify="fix+warn" if( _opt.SkZp_Opt['Flg']['debug']) else "silentfix" );
  

#def avrg(images=None, output=None, minval=None, maxval=None, output_type=numpy.float32):
#  """Calculate the average of a list of images
#
#Parameters
#----------
#    images : list,tuple of str
#        List/tuple of filenames or basenames of the images
#    output : str
#        Filename of the output image
#    minval : float
#        Minimum values to be include in the median (not yet implemented)
#    maxval : float
#        Maximum values to be include in the median (not yet implemented)
#    output_type : Numpy data type
#        Data type for the output. Default: float32
#""";
#  _name_='avrg';
#  if(not isinstance(images, (list, tuple)) ): raise TypeError(_name_+": images must be a list o tuple of at least 2 elements");
#  if(len(images)<2): raise ValueError(_name_+": images must be a list o tuple of at least 2 elements");
#  if(output is None): raise ValueError(_name_+": output must be a filename")
#
#  for img in images:
#    if(not os.path.exists(img)): raise IOError("No input file "+img);
#  shutil.copy(images[0], output);
#  with pyfits.open(output, 'update') as out:
#    imgL=[pyfits.open(images[0])];
#    for img in images:
#      imgL.append(pyfits.open(img))
#      if(len(imgL[0])!=len(imgL[-1])): raise SkZpipeError(_name_+": two fits have different number of hdu.");
#      

def median(images=None, output='median.fits', output_type=numpy.float32, output_verify='silentfix+warn'):
  """Calculate the median of a list of images

Parameters
----------
    images : list,tuple of str
        List/tuple of filenames or basenames of the images
    output : str
        Filename of the output image (default 'median.fits')
    output_type : Numpy data type
        Data type for the output. Default: float32
    output_verify : str
        PyFITS option to manage problems in the creation of a FITS file.
""";
  _name_='median';
  if(not isinstance(images, (list, tuple)) ): raise TypeError(_name_+": 'images' must be a list o tuple of at least 2 elements");
  if(len(images)<2): raise ValueError(_name_+": 'images' must be a list o tuple of at least 2 elements ({img})".format(img=images));
  if(not isinstance(output,str)): raise ValueError(_name_+": 'output' must be a str")

  for img in images:
    if(not os.path.exists(img) and not os.path.exists(img+bpar.SkZp_Par['image_extension'])): raise IOError("No input file "+img);
  imgL=[pyfits.open(images[0] if(os.path.exists(images[0])) else images[0]+bpar.SkZp_Par['image_extension'])];
  nhdu=len(imgL[0]);
  for img in images:
    imgL.append( pyfits.open(img if(os.path.exists(img)) else img+bpar.SkZp_Par['image_extension']) );
    if(nhdu!=len(imgL[-1])): raise SkZpipeError(_name_+": image {img} has different number of hdu respect previous".format(img=img));

  if(nhdu>1): 
    raise SkZpipeError("NHDU>1! Not working well", exclocus=_name_);
#    pyfits.writeto(output, header=imgL[0][0].header, output_verify=output_verify, overwrite=True);
    #primary_hdu = fits.PrimaryHDU(header=imgL[0][0].header);
  itr=range(1) if(nhdu==1) else range(1,nhdu);
  for ihdu in itr:
    data=[];
    for img in imgL:
      data.append(img[ihdu].data.astype(output_type));
#    pyfits.append( output, data=numpy.median(numpy.array(data), axis=0).astype(output_type), header=imgL[0][ihdu].header, output_verify=output_verify, overwrite=True);
    data=numpy.array(data);
    pyfits.writeto(output, data=numpy.median(data, axis=0, overwrite_input=True).astype(output_type), header=imgL[0][ihdu].header, output_verify=output_verify, overwrite=True);


def debias(image=None, dataframe=None, datasec=None, output=None, output_type=numpy.float32, output_verify='ignore', trim=True):
  """Correct for bias.

Parameters
----------
    image : str
        Basename of the image (as present in `dataframe`)
    dataframe : dict
        Dictionary with input data for the image. If not given the data will be extract from SkZp_Par['inputdata'].
    datasec : list,tuple
        A 4-elements tuple/list containing minimum and maximum X coordinates and minimum and maximum Y coordinate of the image with actual data.
    output : str,None
        Filename of output image. Default is image+'b'
    output_type : Numpy data type
        Data type for the output. Default: float32

""";
  _name_='debias';
  if(dataframe is not None and not isinstance(dataframe,dict)): raise TypeError(_name_+": 'dataframe' must be None or a dict");
  if(datasec  is not None and not isinstance(dataframe, (list,tuple))):   raise TypeError(_name_+": 'datasec' must be a list/tuple of 4 elements (i.e. [xmin, xmax, ymin, ymax] )");
  if(isinstance(datasec, (list,tuple)) and len(datasec)!=4):             raise TypeError(_name_+": 'datasec' must be a list/tuple of 4 elements (i.e. [xmin, xmax, ymin, ymax] )");
  if(not dataframe):
    if(image in bpar.SkZp_Par['inputdata']): dataframe=bpar.SkZp_Par['inputdata'][image].copy();
    elif(datasec is None): raise ValueError(_name_+": Image {} has no information about overscan ('datasec' or 'in 'dataframe')".format(str(image)));
  if(not datasec):
    if(dataframe['DATASEC']): datasec=[int(x) for x in re.split('[:,]',re.sub('[\[\]]', '',dataframe['DATASEC']))];
  if(not output): output=image+'b.fits';

  nx,ny=int(dataframe['NX']),int(dataframe['NY']);

  ovrx, ovry=dataframe['OVERSCAN'] if(dataframe['OVERSCAN']) else (None,None);

  overzone=0;
  if(datasec):
    if(datasec[1]<nx): overzone+=1;
    if(datasec[3]<ny): overzone+=2;
    if(datasec[0]> 1): overzone+=4;
    if(datasec[2]> 1): overzone+=8;
    
  if(overzone>0):
    medianL=[];
    with pyfits.open(image+bpar.SkZp_Par['image_extension']) as img:
      data=img[0].data.copy();
      hdr=img[0].header.copy();
    if(overzone & 2):
      medline=numpy.median(data[datasec[3]:], axis=0);
      data=data-numpy.ones(data.shape)*medline;
      medianL.append(numpy.median(medline));
    if(overzone & 1):
      medline=numpy.median(data[: , datasec[1]:], axis=1);
      medline.shape=(ny,1);
      data=data-numpy.ones(data.shape)*medline;
      medianL.append(numpy.median(medline));
    if(overzone & 4):
      medline=numpy.median(data[: , :datasec[0]], axis=1);
      medline.shape=(ny,1);
      data=data-numpy.ones(data.shape)*medline;
      medianL.append(numpy.median(medline));
    if(overzone & 8):
      medline=numpy.median(data[:datasec[2]], axis=0);
      data=data-numpy.ones(data.shape)*medline;
      medianL.append(numpy.median(medline));
      
    
    hdr.append(('OVERSCAN', '{:} Overscan section has median {:} '.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), ";".join(["{:.1f}".format(x) for x in medianL]))), end=True)
    hdr.append(('ZEROCOR', '{:} Zero level correction'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')), 'Bias Subtraction'), end=True)
    if(trim):
      data=data[datasec[2]-1:datasec[3],datasec[0]-1:datasec[1]];
      hdr.append(('TRIM', '{:} Trim data section is [{:d}:{:d},{:d}:{:d}]'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), datasec[0], datasec[1], datasec[2], datasec[3])), end=True)
      hdr.append(('CCDSEC', '[{:d}:{:d},{:d}:{:d}]'.format(datasec[0], datasec[1], datasec[2], datasec[3])), end=True)
    pyfits.writeto(output, data=data.astype(output_type), header=hdr, output_verify=output_verify, overwrite=True);
  


def normalize(image=None, normtype='median', dataframe=None, output=None, output_type=numpy.float32, output_verify='ignore'):
  """Normalize.

Parameters
----------
    image : str
        Filename of the image
    normtype : str
        Type of normalization: 'median', 'mean',
    dataframe : dict
        Dictionary with input data for the image. If not given the data will be extract from SkZp_Par['inputdata'].
    output : str,None
        Filename of output image. Default is image+'b'
    output_type : Numpy data type
        Data type for the output. Default: float32

""";
  _name_='normalize';
  normtypeL=['median', 'mean'];
#  if(not dataframe or not isinstance(dataframe,dict)):
#    if(image in bpar.SkZp_Par['inputdata']): dataframe=bpar.SkZp_Par['inputdata'][image].copy();
#    else: raise ValueError(_name_+': Image {} has no inputdata'.format(str(image)));
  if(not normtype): normtype=normtypeL[0];
  if(not isinstance(normtype, str) or normtype not in normtypeL):  raise ValueError(_name_+": normtype must be '{:}', ...".format("', '".join(normtypeL)));
  if(not output): output=image+'n.fits';



  with pyfits.open(image+'.fits') as img:
    data=img[0].data.copy();
    hdr=img[0].header.copy();

  if(normtype=='median'):
    normvalue=numpy.median(data);
  elif(normtype=='mean'):
    normvalue=numpy.mean(data);

  data=data/normvalue;
      
  hdr.append(('NORMALIZ', '{:} Normalization with {:} at {:.1f} '.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), normtype, normvalue), 'Normalization'), end=True)
  pyfits.writeto(output, data=data.astype(output_type), header=hdr, output_verify=output_verify, overwrite=True);
  

##
def pix2world_fromfile(infile=None):
    """Transform coordinates inside a file from XY to celestial coordinates.

Parameters
----------
    infile : dict, str
        Dictionary with description of input file:
          'name' : [str] filename
          'hdr'  : [int] number of lines of the header. Default 0
          'xy'   : [tuple, int] Column position of the x coordinates (or tuple of the two column positions for x and y). Default 2 (second column).
          'fits' : [str] Extension (with initial dot) for the image, or the name of the images with WCS. Default '.fits'.

Return
------
    Numpy array with the world coordinates.

""";
    _name_='pix2world_file';
    keyT=('name', 'hdr', 'xy', 'fits');
    infile_def={'hdr':0, 'xy':2, 'fits':'.fits'};
    if(not isinstance(infile, (str, dict))): raise TypeError(_name_+": infile must be a str or dict. [{}]".format(infile));
    if(isinstance(infile, str)): infile={'name':infile, 'hdr':0, 'xy':2, 'fits':'.fits'};
    for key in infile_def:
        if(key not in infile): infile[key]=infile_def[key];
    if(any(key not in infile for key in keyT)): raise SkZpipeError(_name_+":there are missing some of the keys in 'infile' {:}".format(keyT));
    if(infile['fits'][0]=='.'): infile['fits']=infile['name'][0:infile['name'].rfind('.')]+infile['fits'];
    if(isinstance(infile['xy'],int)): infile['xy']=(infile['xy'], infile['xy']+1);
    infile['xy']=(infile['xy'][0]-1, infile['xy'][1]-1);

    with open(infile['name']) as fin:
        for ii in range(infile['hdr']):
            fin.readline();
        xycrd = [];
        for line in fin:
            tmpl=line.strip().split();
            xycrd.append([float(tmpl[infile['xy'][0]]),float(tmpl[infile['xy'][1]])]);

    with pyfits.open(fn) as hdul:
        return wcs.WCS(hdul[0].header).wcs_pix2world(numpy.array(xycrd, numpy.float_), 1);


##
def correctcrpix(image=None, shift=None):
    """Correct the value of CRPIX* adding the given values

Parameters
----------
    image : str
        Name of the image
    shift : tuple of float
        Tuple with the shift to add to the CRPIX* values in the header
""";

    _name_='correctcrpix';
    if(not os.path.exists(image)):
        if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
        else: raise IOError(_name_+": No input file "+image);

    crpix=[None,None];
    with pyfits.open(image, 'update') as img:
        crpix[0]=img[0].header.get('CRPIX1');
        crpix[1]=img[0].header.get('CRPIX2');
        if(crpix[0] is not None):
            crpix[0]-=shift[0];
            crpix[1]-=shift[1];
            img[0].header['CRPIX1']=crpix[0];
            img[0].header['CRPIX2']=crpix[1];
        img.close(output_verify="fix+warn" if( _opt.SkZp_Opt['Flg']['debug']) else "silentfix" );

    if(crpix[0] is not None): return 0;
    return 1;


############
def highgooddatum(image=None, width=None, size=None):
    """Determine highest value for good datum

Parameters
----------
    image : str
        Name of the image
    x : obj
        X

Returns
-------
    x
""";
    _name_='highgooddatum'
    if(not os.path.exists(image)):
        if(os.path.exists(image+bpar.SkZp_Par['image_extension'])): image+=bpar.SkZp_Par['image_extension'];
        else: raise IOError(_name_+": No input file "+image);

    if(not width): width=100
    if(width<1): width=100

    imgstat=statimage(image)
    fpv=freqpxlval(image, width=width)

    data=numpy.concatenate( (fpv[0].reshape((fpv[0].size,1)),fpv[1].reshape((fpv[1].size,1))), axis=1 )
    maxval=data[ numpy.where(data[:,1]==data[:,1].max()) ][0]


    xmin=imgstat['med']
    xmin=maxval[0]-1
    if(xmin<=0): xmin=0
    data=data[ data[:,0]>xmin ] #pxl value >0
    zerovals=data[ numpy.where(data[:,1]<=0) ] # no pxl with that value
    firstzero=numpy.min(zerovals[:,0])

    from scipy.ndimage import uniform_filter1d
    datf=data.copy()
    tmpa=datf.copy()
    nflt=int(data.shape[0]/200)*2+1
    nflt=3
    for ii in range(3):
        uniform_filter1d(tmpa, nflt, mode='nearest', axis=0, output=datf)
        tmpa=datf.copy()
    datf[:,0]-=xmin  # zero to sky level

    mindata=5
    npxl_cut=250
    if(mindata<0): mindata=0
    datf=datf[ datf[:,1]>mindata ] #freq >0
    datf0=datf[ datf[:,0]<firstzero ]
    datf0=datf0[ datf0[:,1]<imgstat['npxl']/npxl_cut ]

    from ..mathfunct  import bestpolyfit
    besti=bestpolyfit(x=datf0[:,0], y=1/datf0[:,1], deg=4 )
    bestl=bestpolyfit(x=numpy.log10(datf0[:,0]), y=numpy.log10(datf0[:,1]), deg=3 )

    from ..mathfunct  import movingpolyfit
    fsize=datf[datf[:,1]>10].shape[0]
    size=int(fsize*.4)
    size=50
    #size=int(datf.shape[0]/5)
    mcoef0=movingpolyfit(x=numpy.log10(datf[:,0]), y=numpy.log10(datf[:,1]), deg=1, size=size, step=size>>1 , fixedlow=False, full=True)
    mcoef1=movingpolyfit(x=numpy.log10(datf[:,0]), y=numpy.log10(datf[:,1]), deg=1, size=size, step=size>>1 , fixedlow=True, full=True)




    return {'data':data, 'datf':datf, 'datf0':datf0, 'mcoef0':mcoef0, 'mcoef1':mcoef1, 'besti':besti, 'bestl':bestl, 'size':size, 'width':width}
###
hgd=highgooddatum


