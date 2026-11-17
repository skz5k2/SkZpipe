#include <string.h>
#include <stdio.h>
//#include "../cfitsio/fitsio.h"
#include <fitsio.h>

#define BUFSTR 256

typedef struct{
  fitsfile *fptr;
  char fname[BUFSTR+1];
  int naxis;
  long naxes[3];
  double *dpix;
  long   *lpix;
} FitsImg;

static char average_docstring[]="""Calculates average considering only pixels with value in\n\
average((lim_inf,limsup,filling_value), list-of-images, output_name)\n\
Parameters\n\
----------\n\
    (lim_inf,limsup,filling_value) : tuple of float\n\
        Minimum and maximum value to be used for the average and filling value for the pixel without valid result.\n\
    filename : list of str\n\
        List of the names of the images to average\n\
    output_name : str\n\
        Name of the output image.\n\
";


static PyObject *fitsC_average(PyObject *self, PyObject *args){
  char str[BUFSTR+1]="", prg[]="average", *fnout=NULL, card[FLEN_CARD]="";
  FitsImg *images=NULL;
  fitsfile *outfptr=NULL;  /* FITS file pointers */
  int status = 0;  /* CFITSIO status value MUST be initialized to zero! */
  long check = 1;
  long npixels = 1, firstpix[3] = {1,1,1}; 
  double *opix=NULL, val_t[3]={-1e99, 1e99, 0};
  PyObject *listfn=NULL, *tupleval=NULL, *pyobj=NULL;
  Py_ssize_t pyn=0, ii=0, jj=0, *nn=NULL, nimg=0;
  int flg_t[3]={0,0,0}, flg=0;
  
  if(!PyArg_ParseTuple(args, "O!O!s:fits.average", &PyTuple_Type, &tupleval, &PyList_Type, &listfn, &fnout)){
    PyErr_Clear();
    if(!PyArg_ParseTuple(args, "OO!s", &tupleval, &PyList_Type, &listfn, &fnout)) return NULL;
    if(tupleval!=Py_None){PyErr_SetString(PyExc_TypeError, "The first argument must be None or a tuple of 3 float/None"); return NULL; }
  }else{
    flg=1;
  }
  //if( F ==NULL ){ sprintf(str, "%s: Error: Problems with input/output file %s", prg, fnin); PyErr_SetString(PyExc_IOError, str); return NULL; }


  if(flg){
    pyn=PyTuple_Size(tupleval);
    if(pyn!=3){PyErr_SetString(PyExc_ValueError, "The first argument must be None or a tuple of 3 double/None"); return NULL; }
    for(ii=0; ii<pyn; ii++){
      pyobj=PyTuple_GetItem(tupleval, ii);
      if(pyobj==Py_None) flg_t[ii]=0;
      else if(PyObject_IsInstance(pyobj, (PyObject *)&PyFloat_Type)){
        flg_t[ii]=1;
        val_t[ii]=PyFloat_AsDouble(pyobj);
      }else{
        PyErr_SetString(PyExc_ValueError, "The first argument must be None or a tuple of 3 float/None"); return NULL;
      }
    }
    if(val_t[0]>=val_t[1]){
      fprintf(stderr, "Error!! Inferior limit must be less than superion limit\n");
      return NULL;
    }
  }


  nimg=PyList_Size(listfn);
  if(nimg<2){PyErr_SetString(PyExc_ValueError, "The second argument must be a list of 2 or more filenames"); return NULL; }
  images=(FitsImg*) malloc(nimg*sizeof(FitsImg));
  if(images==NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str); return NULL; }

  for(ii=0; ii<nimg; ii++){
    pyobj=PyList_GetItem(listfn, ii);
//    if(! PyObject_TypeCheck(pyobj, &PyUnicode_Type) ){
    if(!PyObject_IsInstance(pyobj, (PyObject *)&PyUnicode_Type)){ PyErr_SetString(PyExc_ValueError, "The second argument must be a list of 2 or more filenames"); return NULL; }
    strncpy(images[ii].fname, PyUnicode_AsUTF8(pyobj), BUFSTR); 
  }

  for(ii=0; ii<nimg; ii++){
    fits_open_file(&images[ii].fptr, images[ii].fname, READONLY, &status); /* open input images */
    if(status){
       fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str);   free(images); return NULL; /* print error message */
    }
    fits_get_img_dim(images[ii].fptr, &images[ii].naxis, &status);  /* read dimensions */
    if(status){
       fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); free(images); return NULL; /* print error message */
    }
    if(images[ii].naxis > 3){
       PyErr_SetString(PyExc_TypeError, "Error: images with > 3 dimensions are not supported\n"); free(images); return NULL;
    }else{
      images[ii].naxes[0]=images[ii].naxes[1]=images[ii].naxes[2]=1;
      fits_get_img_size(images[ii].fptr, 3, images[ii].naxes, &status);
      if( ii>0 && (images[ii].naxes[0] != images[ii-1].naxes[0] || 
                   images[ii].naxes[1] != images[ii-1].naxes[1] || 
                   images[ii].naxes[2] != images[ii-1].naxes[2])){
        PyErr_SetString(PyExc_TypeError, "Error: input images don't have same size\n"); free(images); return NULL;
      }
    }
  }


  /* create the new empty output file if the above checks are OK */
  str[0]='!';
  strcat(str+1, fnout);
  if(!fits_create_file(&outfptr, str, &status) ){
    /* copy all the header keywords from first image to new output file */
    fits_copy_header(images[0].fptr, outfptr, &status);
    sprintf(card, "ORIGIN  = 'SkZpipe' / FITS file originator");
    fits_update_card(outfptr, "ORIGIN", card, &status);
    sprintf(card, "AVERAGED= %ld", nimg);
    fits_update_card(outfptr, "AVERAGED", card, &status);
    for(ii=0; ii<nimg; ii++){
      sprintf(str, "AVERAG%c%c", (char)('A'+(ii-(ii%26))/26), (char)('A'+(ii%26)));
      sprintf(card, "%.8s=  '%.60s'", str, images[ii].fname);
      fits_update_card(outfptr, str, card, &status);
    }


    npixels = images[0].naxes[0];  /* no. of pixels to read in each row */

    for(ii=0; ii<nimg; ii++){
      images[ii].dpix = (double *) malloc(npixels * sizeof(double)); /* mem for 1 row */
      if(images[ii].dpix == NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str);
      for(jj=0; jj<ii; jj++) free(images[jj].dpix); 
      free(images); return NULL; }
    }
    opix = (double *) malloc(npixels * sizeof(double));
    nn = (Py_ssize_t *) malloc(npixels * sizeof(Py_ssize_t));
    if(opix==NULL || nn==NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str);
      if(opix!=NULL) free(opix);
      if(nn!=NULL) free(nn);
      for(ii=0; ii<nimg; ii++) free(images[ii].dpix); 
      free(images); return NULL;
    }
  
    /* loop over all planes of the cube (2D images have 1 plane) */
    for(firstpix[2] = 1; firstpix[2] <= images[0].naxes[2]; firstpix[2]++){
      /* loop over all rows of the plane */
      for(firstpix[1] = 1; firstpix[1] <= images[0].naxes[1]; firstpix[1]++){
        memset(opix, 0, npixels * sizeof(double));
        memset(nn, 0, npixels * sizeof(Py_ssize_t));
        for(ii=0; ii<nimg; ii++){
          if(fits_read_pix(images[ii].fptr, TDOUBLE, firstpix, npixels, NULL, images[ii].dpix, NULL, &status)){
            check=0;
            fprintf(stderr, "Problems reading image %ld at line %ld !!\n", ii+1, firstpix[1]);
            break;
          }
          if(flg){
            for(jj=0; jj<npixels; jj++)
              if( (flg_t[0]==1 && flg_t[1]==1 && images[ii].dpix[jj]>=val_t[0] && images[ii].dpix[jj]<=val_t[1]) ||
                  (flg_t[0]==1 && flg_t[0]==0 && images[ii].dpix[jj]>=val_t[0]) ||
                  (flg_t[0]==0 && flg_t[1]==1 && images[ii].dpix[jj]<=val_t[1]) ){
                opix[jj]+=images[ii].dpix[jj];
                nn[jj]++;
              }
          }else{
            for(jj=0; jj<npixels; jj++)
              opix[jj]+=images[ii].dpix[jj]/nimg;
          }
        }
        if(check==0) break;
        if(flg)
          for(jj=0; jj<npixels; jj++)
            opix[jj]=(nn[jj]>0)? opix[jj]/nn[jj] : val_t[2];
        fits_write_pix(outfptr, TDOUBLE, firstpix, npixels, opix, &status); /* write new values to output image */
      }
      if(check==0) break;
    }    /* end of loop over planes */

    fits_close_file(outfptr, &status);
    free(opix);
    free(nn);
    for(ii=0; ii<nimg; ii++)
      free(images[ii].dpix);
  }

  for(ii=0; ii<nimg; ii++)
    fits_close_file(images[ii].fptr, &status);
  free(images);
 
  if (status) {fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL;}; /* print any error message */

 return Py_BuildValue("l", status);
}

