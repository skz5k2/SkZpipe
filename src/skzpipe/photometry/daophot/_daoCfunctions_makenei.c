/*     Copyright 2006-2007 Francesco 'SkZ' Mauro */
/*     Any use and redistribution of this software must be authorized by the author*/


/*     This program is distributed in the hope that it will be useful, */
/*     but WITHOUT ANY WARRANTY; without even the implied warranty of */
/*     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  */



#include <Python.h>

#include <stdio.h>
#include <stdlib.h>
#include <math.h>


static char makenei_docstring[]="""Create .nei file\n\
makenei(file.lst, file.ap, file.nei, first_dist [, second_dist])\n\
It includes all the sources in lstfile, plus the ones nearer than first radius respect to them, then also the ones nearer then second radius respect to the previously selected\n\
In Daophot first radius=1.5*psfrad+2*fittrad+1; second radius=2*fittrad+1";

static PyObject *daoCfunctions_makenei(PyObject *self, PyObject *args){
  FILE *fap, *flst, *fnei;
  char str[DAOLINE+1], *fnlst, *fnap, *fnnei;
  Data_nei *star, *nei;
  long i, j, k, nlst, nall, nnei=0, *idlst;
  double dist, dx, dy, radius[2]={0,0};

  if(!PyArg_ParseTuple(args, "sssd|d", &fnlst, &fnap, &fnnei, radius, radius+1)) return NULL;

  if(radius[0]==0) radius[1]=0 ;
  radius[0]*=radius[0]; radius[1]*=radius[1];
  
  fap=fopen(fnap,"r");
  flst=fopen(fnlst,"r");
  fnei=fopen(fnnei,"w");

  if(fap==NULL || flst==NULL || fnei==NULL){
    PyErr_SetString(PyExc_IOError, "makenei: Error: Problems with input/output files");
    return NULL;
  }

  for(i=0;fgets(str, DAOLINE, flst); i++);
  nlst=i-3;
  rewind(flst);
  for(i=0; i<3; i++)
    fputs(fgets(str, DAOLINE, flst),fnei); 
    

  for(i=0;fgets(str, DAOLINE, fap); i++);
  nall=i/3-1;
  rewind(fap);
  for(i=0; i<3 && fgets(str, DAOLINE, fap); i++);

  
  idlst=(long *) calloc(nlst, sizeof(long));
  nei=(Data_nei *) calloc(nall, sizeof(Data_nei));
  star=(Data_nei *) calloc(nall, sizeof(Data_nei));
  if(idlst==NULL || nei==NULL || star==NULL){
    PyErr_SetString(PyExc_MemoryError, "makenei: Error: Problems with input/output files");
    return NULL;
  }
  
  for(i=0;i<nlst && fgets(str, DAOLINE, flst); i++)
    idlst[i]=strtol(str, NULL, 10);
  fclose(flst);
  
  for(i=0; fgets(str, DAOLINE, fap); i++){ 
    sscanf(fgets(str, DAOLINE, fap),"%ld %lf %lf %lf", &(star[i].id), &(star[i].x), &(star[i].y), &(star[i].m));
    sscanf(fgets(str, DAOLINE, fap), "%lf", &(star[i].sky));
    for(j=0; j<nlst; j++){
      if(star[i].id==idlst[j]) {
	nei[j]=star[i];
        i--;
	break;
      }
    }
  }
  fclose(fap);  

  /* put star nearer than fstdist to nei stars (lst) */
  nnei=nlst;
  for(k=0; k<2; k++){
    if(radius[k]==0) break;
    for(nlst=nnei, j=0; j<nall; j++)
      if (star[j].id)
	for(i=0;i<nlst; i++){    
	  dx=(star[j].x-nei[i].x), dy=(star[j].y-nei[i].y);
	  dist=(dx*dx+dy*dy);
	  if (dist<radius[k]){
	    nei[nnei]=star[j];
	    nnei++;
	    star[j].id=0;
	    break;
	  }
	}
  }
  
  for(i=0; i<nnei; putc('\n', fnei), i++)
    fprintf(fnei, file_nei.frmt_row[0].out, (nei[i].id), (nei[i].x), (nei[i].y), (nei[i].m), (nei[i].sky));

  fclose(fnei);
  free(idlst);
  free(nei);
  free(star);
 
 return Py_BuildValue("l", nnei);
}

