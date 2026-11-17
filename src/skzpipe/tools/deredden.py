"""Module with tools to manipulate ouput
"""


import math, numpy, random;
from scipy.optimize import curve_fit as sp_curve_fit

from ..exceptions import *
from ..parameters  import basicpar as bpar
from ..parameters  import options as _opt
from ..parameters.classes  import bclasses
from .. import mathfunct 


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

def reddeningpool(ctlg=None, fiducial=None, extlaw=None, mags=None, pos=None):
    """For each source in the catalog it calculates the reddening shift needed to match the fidutial 
line, producing a pool map to create a reddeing map.

Parameters
----------
    ctlg : Catalog
        Catalog with the sources to calculate the shift
    fiducial : XX or tuple of XX
        Data of the fiducial line of tuple of such data.
    extlaw : float or dict
        Value of the extintion law in the considered plane, or a dictionary with for each magnitude 
        the absorption value.
    mags : indexable of str or of tuple of str
        List of the name of the variables used in the plane: 
        the name of the passband or the tuple with the names of the two passband of the color 
        (i.e. ((B,V),V)  for the plane (B-V, V) )
    pos : tuple of 2 str or str
        Tuple with the name of the attributes with the coordinates to be used in the output.
        Also a alias can be used

Return
------
    poolmap : XXX
        For each source return a value (float or tuple of values) of the horizontal component of the shift

"""
    _name_="reddeningpool"

    if(not isinstance(extlaw,(float,dict) ) ): raise TypeError(f"{_name_}: Wrong type for `extlaw` parameter. It must be a float or dict")
    if(isinstance(extlaw,dict) ):
        if(any(not isinstance(x,str) for x in extlaw.keys()) or any(not isinstance(x,float) for x in extlaw.values()) ): 
            raise ValueError(f"{_name_}: Wrong value for `extlaw` parameter. When a dict, keys must be str and values float")
    if(mags is None or any(not isinstance(x,(str,tuple)) for x in mags)): raise TypeError(f"{_name_}: Wrong type for `mags` parameter. It must be an itarable of str")
    if(pos is None or any(not isinstance(x,str) for x in pos)): raise TypeError(f"{_name_}: Wrong type for `pos` parameter. It must be an itarable of str")

    if(isinstance(extlaw,dict)):
        upv= extlaw[mags[1]] if(isinstance(mags[1],str)) else extlaw[mags[1][0]]-extlaw[mags[1][1]]
        dnv= extlaw[mags[0]] if(isinstance(mags[0],str)) else extlaw[mags[0][0]]-extlaw[mags[0][1]]
        slope=upv/dnv
    else: slope=extlaw

    if(not isinstance(fiducial, tuple)): fiducial=(ficucial,)
    fiduL=[]
    for fline in fiducial:
        tmpl=[]
        if(isinstance(fline, bclasses.Catalog)):
            for point in fline:
                val1=getattr(point,mags[0]) if(isinstance(mags[0],str)) else getattr(point,mags[0][0])-getattr(point,mags[0][1])
                val2=getattr(point,mags[1]) if(isinstance(mags[1],str)) else getattr(point,mags[1][0])-getattr(point,mags[1][1])
                tmpl.append( bclasses.Point2( (va1,val2) ) )
        else:
            for point in fline:
                val1=point[0]
                val2=point[1]
                tmpl.append( bclasses.Point2( (va1,val2) ) )
        fiduL.append(tmpl)
    fiducial=tuple(fiduL)

    redpool=[]
    for src in ctlg:
        xs,ys = (getattr(src,pos[0]), getattr(src,pos[1])) 
        val1=getattr(src,mags[0]) if(isinstance(mags[0],str)) else getattr(src,mags[0][0])-getattr(src,mags[0][1])
        val2=getattr(src,mags[1]) if(isinstance(mags[1],str)) else getattr(src,mags[1][0])-getattr(src,mags[1][1])
        Pxy=bclasses.Point2( (va1,val2) )

        tmpl=[]
        for fline in fiducial:
            for ii in range(len(fline)-1):
                test=mathfunct.dointersect(Pxy, slope, fline[ii], fline[ii+1])
                if(test[0] is None or test[0]==1): continue
                xin,yin=mathfunct.findintersect(Pxy, slope, fline[ii], fline[ii+1])  
                tmpl.append( xin-Pxy.x ) #just deltaX: deltaY=slope*deltaX
                break;

        redpool.append( [xs, ys]+tmpl )

    return redpool
    

