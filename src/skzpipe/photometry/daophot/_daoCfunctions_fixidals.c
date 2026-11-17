/*     Copyright 2006-2007 Francesco 'SkZ' Mauro */
/*     Any use and redistribution of this software must be authorized by the author*/


/*     This program is distributed in the hope that it will be useful, */
/*     but WITHOUT ANY WARRANTY; without even the implied warranty of */
/*     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  */



#include <Python.h>



#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "format_dao.h"


double get_clp(double m1, double err1, double m2, double err2, double *scl, double magshift){
  double thre[2], dmg;
   
  dmg=m1-m2-magshift;
  if(dmg>=0){
    thre[0]=(scl[0]>0)? (scl[0]*sqrt(err1*err1+err2*err2)):(scl[0]<0)? (-scl[0]) : 0;
    thre[1]=(scl[1]>0)? (scl[1]*sqrt(err1*err1+err2*err2)):(scl[1]<0)? (-scl[1]) : 0;
    if(thre[1]>thre[0]) thre[0]=thre[1];
  }else{
    dmg*=-1;
    thre[0]=(scl[2]>0)? (scl[2]*sqrt(err1*err1+err2*err2)):(scl[2]<0)? (-scl[2]) : 0;
    thre[1]=(scl[3]>0)? (scl[3]*sqrt(err1*err1+err2*err2)):(scl[3]<0)? (-scl[3]) : 0;
    if(thre[1]>thre[0]) thre[0]=thre[1];
  }
  return (thre[0]>0)? dmg/thre[0] : 0;
}

//################################
static char fixidals_docstring[]="fixidals(alsfile, apfile, fwhm, outfile,    fwhmfrac, debugflag)\n\
Fix the id of the stars in a .als file according to the ones in the .ap file\n\
\n\
Parameters\n\
----------\n\
    alsfile : str\n\
        Name of .als file\n\
    apfile : str\n\
        Name of .ap file\n\
    fwhm : float\n\
        FWHM (used as a distance scale)\n\
    outfile : str\n\
        Name of output file\n\
    fwhmfrac : float\n\
        Fraction of FWHM used as maximum difference in distance in the initial match by ID to calculate the shift in magnitude. Optional.\n\
    debugflag : int\n\
        flag (1/0) for additional output. Default 0. Optional.\n\
\n\
\n\
\n\
Return\n\
------\n\
    Tuple of 4 elements: #sources in .als, #sources in .ap, # kept sources, shift in magnitude\n\
    Three files are generated: the allstar output with fixed IDs, an allstar output with the rejected sources (filename as input file plus '_R' at the end), a photometry output with the rejected sources (filename as input file plus '_R' at the end). A debug file could be created (filename as output file plus '_2' at the end).\n\
";

#define FWHMFRAC0 0.03

static PyObject *daoCfunctions_fixidals(PyObject *self, PyObject *args){
  char str[DAOLINE+1], outxt[2*DAOLINE+1], *fnals, *fnap, *fnout, prg[]="fixidals";
  FILE *fout=NULL, *fdbg=NULL, *frej=NULL;
  long i=0, j=0;
  long nmtc=0, nd=0, idm=-1, tmpl=0, *apos=NULL, dbgflg=0, nmgs; //, nmgsmin;
  double fwhm, x, y, r=100, r0=100, ri, rm=10000, tmpd, clp, scl[4]={0,0,0,0}, magshift=0, mgs, ers, *idst;
  double fwhmfrac=FWHMFRAC0;
  FileDao Fst=FILEDAO_0, Snd=FILEDAO_0;
  HeaderDao hdr;

  if(!PyArg_ParseTuple(args, "ssds|dl", &fnals, &fnap, &fwhm, &fnout,    &fwhmfrac, &dbgflg)) return NULL;


  if((Fst.f=fopen(fnals, "r"))==NULL) {sprintf(outxt,"%s: problems opening .als input file %s", prg, fnals); PyErr_SetString(PyExc_IOError, outxt); return NULL;}
  if((Snd.f=fopen(fnap, "r"))==NULL) {sprintf(outxt,"%s: problems opening .ap input file %s", prg, fnap);   PyErr_SetString(PyExc_IOError, outxt); return NULL;}

  if((fout=fopen(fnout, "w"))==NULL) {sprintf(outxt,"%s: problems opening output file %s", prg, fnout); PyErr_SetString(PyExc_IOError, outxt); return NULL;}
  if(dbgflg)
    if((fdbg=fopen(strcat(strncpy(str,fnout, DAOLINE),"_2"), "w"))==NULL){sprintf(outxt, "Error: problems opening output file %s\n", str); PyErr_SetString(PyExc_IOError, outxt); return NULL;}
  if((frej=fopen(strcat(strncpy(str, fnals, DAOLINE),"_R"), "w"))==NULL){ sprintf(outxt, "Error: problems opening output file %s\n", str); PyErr_SetString(PyExc_IOError, outxt); return NULL;}

//##########################
  fputs(fgets(str, DAOLINE, Fst.f), fout);    fputs(str, frej);
  fputs(fgets(str, DAOLINE, Fst.f), fout);    fputs(str, frej);
  sscanf(str, DAOFRMHDR_DEF_I, &Fst.type, &hdr.nx, &hdr.ny, &hdr.low, &hdr.high, &hdr.thresh, &Fst.ap1,  &hdr.gain, &hdr.ron,  &Fst.frd);
  if(fwhm==0) fwhm=Fst.frd;
  if(fwhm<0) fwhm*=-Fst.frd;
  if(Fst.type!=1){
    sprintf(outxt, "%s Error: the first file %s must be a allstar-type output\n", prg, fnals); PyErr_SetString(PyExc_IOError, outxt); return NULL;
  }
  fputs(fgets(str, DAOLINE, Fst.f), fout);    fputs(str, frej);
  
  for(Fst.idmx=i=0; fgets(str, DAOLINE, Fst.f); i++){
    j=atol(str);
    if(Fst.idmx<j) Fst.idmx=j;
  }
  Fst.ns=i; 
  rewind(Fst.f);

  //####
  for(i=0; i<3 && fgets(str, DAOLINE, Snd.f); i++) if(i==1) sscanf(str, DAOFRMHDR_DEF_I, &Snd.type, &tmpl, &tmpl, &tmpd, &tmpd, &tmpd, &tmpd, &tmpd, &tmpd, &Snd.frd);
  if(Snd.type!=2){
    sprintf(outxt, "%s Error: the second file %s must be a photo-type output\n", prg, fnap);  PyErr_SetString(PyExc_IOError, outxt); return NULL;
  }
  
  for(Snd.idmx=i=0; fgets(str, DAOLINE, Snd.f) && fgets(str, DAOLINE, Snd.f) && fgets(outxt, DAOLINE, Snd.f); i++){
    j=atol(str);
    if(Snd.idmx<j) Snd.idmx=j;
  }
  Snd.ns=i; 
  rewind(Snd.f);

  if(Fst.ns>Fst.idmx || Snd.ns>Snd.idmx){
    sprintf(outxt, "%s: In a input file the maximum star ID is smaller than the number of stars!!!", prg); PyErr_SetString(PyExc_ValueError, outxt); return NULL;
  }

  for(i=0; i<3 && fgets(str, DAOLINE, Fst.f); i++);
  for(i=0; i<3 && fgets(str, DAOLINE, Snd.f); i++);
  
  Fst.nd=Fst.idmx+1; 
  Snd.nd=Snd.idmx+1; 
  nd=(Fst.nd<Snd.nd) ? Fst.nd : Snd.nd;

//################ LOAD #########################
  //Allocate as much as idmax+1
  apos= (long*)   calloc(Fst.nd, sizeof(long));
  idst= (double*)   calloc(nd, sizeof(double));
  Fst.data_als= (Data_als*) calloc(Fst.nd, sizeof(Data_als));
  Snd.data_ap1= (Data_ap1*) calloc(Snd.nd, sizeof(Data_ap1));
  //Als
  for(i=0; fgets(str, DAOLINE, Fst.f); i++){
    j=atol(str); //ID => position in array
    sscanf(str, file_als.frmt_row[0].in, &(Fst.data_als[j].id), &(Fst.data_als[j].x), &(Fst.data_als[j].y), &(Fst.data_als[j].m), &(Fst.data_als[j].err_m), &(Fst.data_als[j].sky), &(Fst.data_als[j].iter), &(Fst.data_als[j].chi), &(Fst.data_als[j].sharp));
  }
  Fst.ns=i;
  fclose(Fst.f);

  //Ap
  for(i=0; fgets(str, DAOLINE, Snd.f); i++){
    j=atol(fgets(str,  DAOLINE, Snd.f)); //ID => position in array
    sscanf(str, "%ld %lf %lf %lf", &(Snd.data_ap1[j].id),  &(Snd.data_ap1[j].x),      &(Snd.data_ap1[j].y),       &(Snd.data_ap1[j].m)    );
    sscanf(fgets(outxt, DAOLINE, Snd.f), "%lf %lf %lf %lf", &(Snd.data_ap1[j].sky), &(Snd.data_ap1[j].skydev), &(Snd.data_ap1[j].skyskew), &(Snd.data_ap1[j].err_m));
  }
  Snd.ns=i;
  fclose(Snd.f);

//################################################
//################ START #########################
//################################################
//### Delta Mag and ID Match for really near
  if(fwhmfrac==0) fwhmfrac=FWHMFRAC0;
  r0=fwhmfrac*fwhm;
  r0*=r0;
//  nmgsmin=100;
//  if(nmgsmin> 0.01*Fst.ns) nmsmin= 0.01*Fst.ns
  mgs=ers=nmgs=0;
  for(i=1; i<nd; i++){
    if(Fst.data_als[i].id==0) continue;
    if(Snd.data_ap1[i].id==0) continue;

    x=Snd.data_ap1[i].x-Fst.data_als[i].x;
    y=Snd.data_ap1[i].y-Fst.data_als[i].y;
    idst[i]=x*x+y*y;

    r=idst[i];
    if(r>r0) continue;
     
    fprintf(fout, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
    putc('\n', fout);
if(fdbg){  fprintf(fdbg, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
fprintf(fdbg, "     %.3f    ", sqrt(r));
fprintf(fdbg, file_ap1.frmt_row[0].out, Snd.data_ap1[i].id, Snd.data_ap1[i].x, Snd.data_ap1[i].y, Snd.data_ap1[i].m, Snd.data_ap1[i].err_m, Snd.data_ap1[i].sky, Snd.data_ap1[i].skydev, Snd.data_ap1[i].skyskew);
fputs(" 1 \n", fdbg);}
    nmtc++;  
    apos[i]=i;
    Fst.data_als[i].id=0;
    Snd.data_ap1[i].id=0;
    if(Snd.data_ap1[i].m>0 && Snd.data_ap1[i].m<90 && Snd.data_ap1[i].err_m>0){
      mgs+=(Fst.data_als[i].m-Snd.data_ap1[i].m)/(Fst.data_als[i].err_m*Fst.data_als[i].err_m+Snd.data_ap1[i].err_m*Snd.data_ap1[i].err_m);
      ers+=1/(Fst.data_als[i].err_m*Fst.data_als[i].err_m+Snd.data_ap1[i].err_m*Snd.data_ap1[i].err_m);
      nmgs++;
    }
  }
/*  for(j=2; j<10; j++){
    //if(nmgs>nmgsmin) break;
    for(i=1; i<nd; i++){
      if(Fst.data_als[i].id==0) continue;
      if(Snd.data_ap1[i].id==0) continue;
  
      r=idst[i];
      if(r>r0*j) continue;
       
      fprintf(fout, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
      putc('\n', fout);
if(fdbg){  fprintf(fdbg, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
  fprintf(fdbg, "    %.3f    ", sqrt(r));
  fprintf(fdbg, file_ap1.frmt_row[0].out, Snd.data_ap1[i].id, Snd.data_ap1[i].x, Snd.data_ap1[i].y, Snd.data_ap1[i].m, Snd.data_ap1[i].err_m, Snd.data_ap1[i].sky, Snd.data_ap1[i].skydev, Snd.data_ap1[i].skyskew);
  fputs(" 1 \n", fdbg);}
      nmtc++;  
      apos[i]=i;
      Fst.data_als[i].id=0;
      Snd.data_ap1[i].id=0;
      if(Snd.data_ap1[i].m>0 && Snd.data_ap1[i].m<90 && Snd.data_ap1[i].err_m>0){
        mgs+=(Fst.data_als[i].m-Snd.data_ap1[i].m)/(Fst.data_als[i].err_m*Fst.data_als[i].err_m+Snd.data_ap1[i].err_m*Snd.data_ap1[i].err_m);
        ers+=1/(Fst.data_als[i].err_m*Fst.data_als[i].err_m+Snd.data_ap1[i].err_m*Snd.data_ap1[i].err_m);
        nmgs++;
      }
    }
  }*/
  magshift=mgs/ers;  //weighted mean of delta mag
//#####################################################################################
//#####################################################################################
//###MATCH BY ID
  r0=.1*fwhm;  r0*=r0;
  scl[0]=-.6; scl[2]=-.5;   scl[1]=scl[3]=0; 
  for(i=1; i<nd; i++){
    if(Fst.data_als[i].id==0) continue;
    if(Snd.data_ap1[i].id==0) continue;

//    x=Snd.data_ap1[i].x-Fst.data_als[i].x;
//    y=Snd.data_ap1[i].y-Fst.data_als[i].y;
//    r=x*x+y*y;
    r=idst[i];
    if(r>r0) continue;
    clp=get_clp(Fst.data_als[i].m, Fst.data_als[i].err_m, Snd.data_ap1[i].m, 0*Snd.data_ap1[i].err_m, scl, magshift);
    if(clp<=1){
      fprintf(fout, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
      putc('\n', fout);
if(fdbg){  fprintf(fdbg, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
  fprintf(fdbg, "    %.3f    ", sqrt(r));
  fprintf(fdbg, file_ap1.frmt_row[0].out, Snd.data_ap1[i].id, Snd.data_ap1[i].x, Snd.data_ap1[i].y, Snd.data_ap1[i].m, Snd.data_ap1[i].err_m, Snd.data_ap1[i].sky, Snd.data_ap1[i].skydev, Snd.data_ap1[i].skyskew);
  fputs(" 2 \n", fdbg);}
      nmtc++;  
      apos[i]=i;
      Fst.data_als[i].id=0;
      Snd.data_ap1[i].id=0;
    }
  }

//#################################
//printf("CICLE\n");fflush(stdout);
//###MATCH BY PROXIMITY Up to 0.5 FWHM  with SCL but not for 99.999
  for(ri=.125; ri<=.5; ri+=.125){
    r0=ri*fwhm;  r0*=r0;
    for(i=1; i<Fst.nd; i++){
      if(Fst.data_als[i].id==0) continue;
      for(idm=-1,rm=10000,j=1; j<Snd.nd; j++){
        if(Snd.data_ap1[j].id==0) continue;
        x=Snd.data_ap1[j].x-Fst.data_als[i].x;
        y=Snd.data_ap1[j].y-Fst.data_als[i].y;
        r=x*x+y*y;
        if(r>r0) continue;
        clp=get_clp(Fst.data_als[i].m, Fst.data_als[i].err_m, Snd.data_ap1[j].m, Snd.data_ap1[j].err_m, scl, magshift);
        if((Snd.data_ap1[j].m>90 || Snd.data_ap1[j].m<-90)) clp=1;
        if(r<rm && clp<=1){idm=j; rm=r;}
      }
      if(idm>=0){
        fprintf(fout, file_als.frmt_row[0].out, Snd.data_ap1[idm].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
        putc('\n', fout);
            if(fdbg){  fprintf(fdbg, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
              fprintf(fdbg, "    %.3f    ", sqrt(r));
              fprintf(fdbg, file_ap1.frmt_row[0].out, Snd.data_ap1[idm].id, Snd.data_ap1[idm].x, Snd.data_ap1[idm].y, Snd.data_ap1[idm].m, Snd.data_ap1[idm].err_m, Snd.data_ap1[idm].sky, Snd.data_ap1[idm].skydev, Snd.data_ap1[idm].skyskew);
              fprintf(fdbg, "  %.3f  \n", 3+ri);}
        nmtc++;  
        apos[i]=idm;
        Fst.data_als[i].id=0;
        Snd.data_ap1[idm].id=0;
      }   
    }
    fflush(fout);
  }
//#####
//###MATCH BY ID  At 0.5 FWHM and SCL bigger
  r0=0.5*fwhm;  r0*=r0;
  scl[0]=-.75; scl[2]=-.65;   scl[1]=scl[3]=5;
  for(i=1; i<nd; i++){
    if(Fst.data_als[i].id==0) continue;
    if(Snd.data_ap1[i].id==0) continue;

    r=idst[i];
    if(r>r0) continue;
    clp=get_clp(Fst.data_als[i].m, Fst.data_als[i].err_m, Snd.data_ap1[i].m, 0*Snd.data_ap1[i].err_m, scl, magshift);
    if(clp<=1){
      fprintf(fout, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
      putc('\n', fout);
if(fdbg){  fprintf(fdbg, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
  fprintf(fdbg, "    %.3f    ", sqrt(r));
  fprintf(fdbg, file_ap1.frmt_row[0].out, Snd.data_ap1[i].id, Snd.data_ap1[i].x, Snd.data_ap1[i].y, Snd.data_ap1[i].m, Snd.data_ap1[i].err_m, Snd.data_ap1[i].sky, Snd.data_ap1[i].skydev, Snd.data_ap1[i].skyskew);
  fputs(" 4 \n", fdbg);}
      nmtc++;  
      apos[i]=i;
      Fst.data_als[i].id=0;
      Snd.data_ap1[i].id=0;
    }
  }
  fflush(fout);
//################
//printf("LAST\n");fflush(stdout);
  for(i=1; i<Fst.nd; i++){
    if(Fst.data_als[i].id==0) continue;
    for(idm=-1,rm=10000,j=1; j<Snd.nd; j++){
      if(Snd.data_ap1[j].id==0) continue;
      x=Snd.data_ap1[j].x-Fst.data_als[i].x;
      y=Snd.data_ap1[j].y-Fst.data_als[i].y;
      r=x*x+y*y;
      if(r>r0) continue;
      clp=get_clp(Fst.data_als[i].m, Fst.data_als[i].err_m, Snd.data_ap1[j].m, Snd.data_ap1[j].err_m, scl, magshift);
      if((Snd.data_ap1[j].m>90 || Snd.data_ap1[j].m<-90) && Fst.data_als[i].err_m<0.01) clp=1;
      if(r<rm && clp<=1){idm=j; rm=r;}
    }
    if(idm>=0){
      fprintf(fout, file_als.frmt_row[0].out, Snd.data_ap1[idm].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
      putc('\n', fout);
if(fdbg){  fprintf(fdbg, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
  fprintf(fdbg, "    %.3f    ", sqrt(r));
  fprintf(fdbg, file_ap1.frmt_row[0].out, Snd.data_ap1[idm].id, Snd.data_ap1[idm].x, Snd.data_ap1[idm].y, Snd.data_ap1[idm].m, Snd.data_ap1[idm].err_m, Snd.data_ap1[idm].sky, Snd.data_ap1[idm].skydev, Snd.data_ap1[idm].skyskew);
  fputs(" 5 \n", fdbg);}
      nmtc++;  
      apos[i]=idm;
      Fst.data_als[i].id=0;
      Snd.data_ap1[idm].id=0;
    }   
  }
//#####################################################################################
//###MATCH BY ID
  r0=.5*fwhm;  r0*=r0;
  scl[0]=-.6; scl[2]=-.5;   scl[1]=scl[3]=0; 
  for(i=1; i<nd; i++){
    if(Fst.data_als[i].id==0) continue;
    if(Snd.data_ap1[i].id==0) continue;

//    x=Snd.data_ap1[i].x-Fst.data_als[i].x;
//    y=Snd.data_ap1[i].y-Fst.data_als[i].y;
//    r=x*x+y*y;
    r=idst[i];
    if(r>r0 && Fst.data_als[i].err_m>0.01 && fabs(Fst.data_als[i].sharp)>1) continue;
    fprintf(fout, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
    putc('\n', fout);
if(fdbg){  fprintf(fdbg, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
  fprintf(fdbg, "    %.3f    ", sqrt(r));
  fprintf(fdbg, file_ap1.frmt_row[0].out, Snd.data_ap1[i].id, Snd.data_ap1[i].x, Snd.data_ap1[i].y, Snd.data_ap1[i].m, Snd.data_ap1[i].err_m, Snd.data_ap1[i].sky, Snd.data_ap1[i].skydev, Snd.data_ap1[i].skyskew);
  fputs(" 6 \n", fdbg);}
    nmtc++;  
    apos[i]=i;
    Fst.data_als[i].id=0;
    Snd.data_ap1[i].id=0;
  }


//######################
  free(apos);
  free(idst);
  fclose(fout);
if(fdbg) fclose(fdbg);
//##############################################
//################ END #########################
//##############################################
//#####################################################################################

  for(i=1; i<Fst.nd; i++){
    if(Fst.data_als[i].id==0) continue;
    fprintf(frej, file_als.frmt_row[0].out, Fst.data_als[i].id, Fst.data_als[i].x, Fst.data_als[i].y, Fst.data_als[i].m, Fst.data_als[i].err_m, Fst.data_als[i].sky, Fst.data_als[i].iter, Fst.data_als[i].chi, Fst.data_als[i].sharp);
    putc('\n', frej);
  }
  fclose(frej);
  free(Fst.data_als);

//#########
  if((frej=fopen(strcat(strncpy(str, fnap, DAOLINE),"_R"), "w"))==NULL){sprintf(outxt, "%s Error: problems opening output file %s of rejected sources\n", prg, str); PyErr_SetString(PyExc_IOError, outxt); return NULL;}
  for(j=1; j<Snd.nd; j++){
    if(Snd.data_ap1[j].id==0) continue;
    fprintf(frej, file_ap1.frmt_row[0].out, Snd.data_ap1[j].id, Snd.data_ap1[j].x, Snd.data_ap1[j].y, Snd.data_ap1[j].m, Snd.data_ap1[j].err_m, Snd.data_ap1[j].sky, Snd.data_ap1[j].skydev, Snd.data_ap1[j].skyskew);
    putc('\n', frej);
  }
  fclose(frej);
  free(Snd.data_ap1);
  
 return Py_BuildValue("llld", Fst.ns, Snd.ns, nmtc, magshift);
}
  
  
