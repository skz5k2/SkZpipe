import os, sys, shutil, re, requests
import math;

from .std import *
from ...parameters  import options as _opt
from ...parameters  import database as _db
#from ... import functions as funct


bands=['U', 'B', 'V', 'R', 'I'];

dbdir_url="https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/files/vault/STETSON/Standards/";
dbdes_sub="000README/";
dbdes_fn="survey.dat";

if(not os.path.exists(dbdes_fn)):
    import urllib.request
    urllib.request.urlretrieve(dbdir_url+dbdes_sub+dbdes_fn, dbdes_fn )

pbsFldDB={}
def pbsFldDBread(*, verb=False, force=False, source=None):
    """Read the database of Statson Stardard Fields

Parameters
----------
    verb : bool
        Verbosity flag
    force : bool
        Force to overwrite an existing DB
    source : str
        Path of a alternative source
Return
------
    tuple
    Tuple of field names

"""
    _name_='pbsFldDBread'
    if(pbsFldDB and not force):
        return dict((x, pbsFldDB[x]['nV']) for x in pbsFldDB)

    fn_in=source if(source and isinstance(source,str)) else dbdes_fn
    with open(fn_in) as dbdes:
        from ...mathfunct import radec2decdeg
        if(_opt.OptionGet('output:verbose')): print("Loading Stetson Standard database", file=bpar.SkZp_Par['stdout']);
        line=dbdes.readline();
        #  0                              4                         9                       14              17                 20
        #  mch    max      nmg    fet     nU   nB   nV   nR   nI    hU   hB   hV   hR   hI  ra_h ra_m ra_m  dec_g dec_m dec_s  Dx Dy * name
        # n* => actual number of stars in the field that currently meet the acceptance criteria as a potential standard
        # h* => the relative quality of the standard stars in each field in each bandpass
        for line in dbdes:
            tmpl=line.split()
            fld_name=tmpl[-1]
            fld_nm=fld_name.lower()
            pbsFldDB[fld_nm]={'name':fld_name}
#            tmpl=[float(x) for x in tmpl[:-2]]
            pbsFldDB[fld_nm].update( dict( zip(('nU', 'nB', 'nV', 'nR', 'nI'), (int(x) for x in tmpl[4:9])) ) )
            pbsFldDB[fld_nm].update( dict( zip(('hU', 'hB', 'hV', 'hR', 'hI'), (int(x) for x in tmpl[9:14])) ) )
            ra,dec=radec2decdeg(tmpl[14:17], tmpl[17:20])
            ra=round(ra, 6); dec=round(dec, 6)
            pbsFldDB[fld_nm].update({'ra':ra, 'dec':dec})
    return dict((x, (pbsFldDB[x]['hU'],pbsFldDB[x]['hB'],pbsFldDB[x]['hV'],pbsFldDB[x]['hR'],pbsFldDB[x]['hI'])) for x in pbsFldDB)

  
def DataField(name=None, pointing=None, dist=1.):
    """Return usefull data from 'survey.dat' file with description of the Stetson Photometric Standard Database

Parameters
----------
    name : str
        Name of the standard field to look up in the database
    pointing : tuple of float
        Tuple of two float (ra,dec) of the pointing.
    dist : float
        Maximum distance in degree.

Return
------
    x : dict or None, list
        If there is no match, None is returned.
        If a standard field is found, it returns a dictionary with data about the standard field from the database.
        If there is a multiple match by position, a list of tuples (name, dist).
"""
    if(name):
        name=name.lower();
        if(name[:2]=='sa'):
            name=re.sub(r'^\D*', '', name); #lstrip of no number
            if(re.search(r'\D', name)): name=re.sub(r'\D.*$', '', name); #rstrip of no number
            name='L'+name

        lookup=functions.lookup(name, pbsFldDB.keys())
        if(lookup):  return pbsFldDB[lookup]

#    for ii in range(len(name)-1, 3, -1):
#      if(name[:ii] in pbsFldDB):  return pbsFldDB[name[:ii]];
#    if('_' in name):
#      name=name.replace('_','');
#      if(name in pbsFldDB): return pbsFldDB[name];
#      for ii in range(len(name)-1, 3, -1):
#        if(name[:ii] in pbsFldDB):  return pbsFldDB[name[:ii]];
     
    if(pointing):
        ra,dec=pointing;
        dist*=dist;
        tmpl=[];
        for fld_nm in pbsFldDB:
            dra=(ra-pbsFldDB[fld_nm]['ra'])*math.cos(math.radians(dec));
            ddec=dec-pbsFldDB[fld_nm]['dec'];
            delta=dra**2+ddec**2;
            if(delta<dist):
                tmpl.append( (fld_nm, math.sqrt(delta)) );
        if(len(tmpl)==1): return pbsFldDB[tmpl[0][0]];
        elif(tmpl):
            tmps=set();
            for ii in range(len(tmpl)):
                fld_ii=tmpl[ii];
                for jj in range(ii+1,len(tmpl)):
                    fld_jj=tmpl[jj];
                    if(pbsFldDB[fld_ii]['name']==pbsFldDB[fld_jj]['name']):
                        if(pbsFldDB[fld_ii]['name'].lower()==fld_ii): tmps.add(fld_ii);
                        elif(pbsFldDB[fld_jj]['name'].lower()==fld_jj): tmps.add(fld_jj);
            return list(tmps);
        
    return;


class PbsStdStar(StdStar):
    def __init__(self, line=None):
        if(isinstance(line,tuple)): line=line[0]+line[1];
        if(isinstance(line,dict)): line=line['pos']+line['pho'];
        pos={'id':13, 'ra':1, 'dec':2, 'x':9, 'y':10, 'mag':[15,19,23,27,31]};
        super().__init__(line=line, pos=pos, coordtransf=bclasses.CoordTransf(flip=(1,0)) );
        if(isinstance(line, PbsStdStar)):
            self.var=line.var;
            self.n=line.n.copy();
            self.N=line.N.copy();
        else:
            tmpl=line.strip().split();
            self.var=float(tmpl[-1]);
            self.n,self.N=[],[];
            for ii in pos['mag']:
                self.N.append(int(tmpl[ii+1]));
                self.n.append(int(tmpl[ii+2]));
    def __str__(self):
        txt="{:} {:f} {:f} {:f} {:f}".format(self.idn, self.ra, self.dec, self.x, self.y);
        for ii in range(len(self.mag)):
            txt+=" {:f} {:f} {:d} {:d}".format(self.mag[ii], self.err[ii], self.N[ii], self.n[ii]);
        return txt+" {:f}".format(self.var);

class PbsStdField(StdField):
    """Class to create a standard field from Stetson database

Parameters
----------
    field : str, StdField
        Name of the field or a StdField object
    pointing : tuple of float 
        Coordinates of the pointing (alternative way to find it)
    dist : float
        Maximum distance in degrees to find it with pointing
Attributes
----------


""";
    def __init__(self, field=None, pointing=None, dist=1.):
        """Initialization of PbsStdField(StdField) object

""";
        _name_='PbsStdField object';
        self.bands=bands;
        if(isinstance(field, str) or pointing):

            info=DataField(name=field, pointing=pointing, dist=1.)
            if(not info): raise SkZpipeError("No Standard field was found <{field}> <{pointing}>".format(field=field, pointing=pointing), exclocus=_name_);
            if(_opt.OptionGet('output:verbose') and _opt.OptionGet('output:verbosity')>5): print('Standard field info:', info, file=bpar.SkZp_Par['stdout']);

            self.field=info['name'];
          #if there are not the file, download them
            if(funct.check_file([self.field+'.pos', self.field+'.pho'], raisexc=False)):
                for suff in ('.pos', '.pho'):
                    fnstd=self.field+suff;
                    with open(fnstd, 'wb') as fstd:
                      fstd.write(requests.get(dbdir_url+self.field+'/'+fnstd).content);
          #Create the internal catalog of standard stars
            self.stdL=[];
            with open(self.field+'.pos') as fpos, open(self.field+'.pho') as fpho:
                line=fpos.readline();
                self.ref=tuple(float(x) for x in line.split()[0:2])
                line=fpho.readline();
                for line in fpos:
                    if(re.search(r' - \d\.',line)): line=re.sub(r' - (\d\.)', r' -0\1', line);
                    self.stdL.append(PbsStdStar(line+fpho.readline()));
        elif(isinstance(field, PbsStdField)):
            self.field=field.field;
            self.ref=field.ref;
            self.stdL=[];
            for std in field.stdL:
                    self.stdL.append(PbsStdStar(std));
        else: raise TypeError(f"PbsStdField: Wrong type for 'field' <{field.__class__}>")
        
###########
bpar.SkZp_Par['stdfield']=PbsStdField




