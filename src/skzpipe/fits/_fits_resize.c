#include <string.h>
#include <stdio.h>
#include <math.h>
#include <time.h>
//#include "../cfitsio/fitsio.h"
#include <fitsio.h>

#define EXTRVAL 2e2
#define STRBUF 259


static char resize_docstring[]="""Resize a fits image changing size and first pixel (pixel for 1;1 position). The binning is applied at the end.\n\
resize(filename, (new_x0,y0), (new_nx,ny), (bin_x,y), filling_value, output_filename)\n\
Parameters\n\
----------\n\
    filename : str\n\
        Name of the fits image\n\
    (new_x1,y1) : tuple of int\n\
        Coordinate of the new first pixel (1,1)\n\
    (new_nx,ny) : tuple of int\n\
        Values of the new size\n\
    (bin_x,y) : tuple of int\n\
        Value for the binning of the final image (after change in size and origin).\n\
    filling_value : float\n\
        Value to be used for the new part the image\n\
    scaling : float\n\
        Scaling factor to be applied to pixel values (*scale)\n\
    output_name : str\n\
        Name of the output image.\n\
";

static PyObject *fitsC_resize(PyObject *self, PyObject *args){
  fitsfile *ifptr=NULL, *outfptr=NULL;  /* FITS file pointers */
  char prg[]="resize", *fnin=NULL, *fnout=NULL, str[STRBUF]="",  card[FLEN_CARD]="", comment[FLEN_COMMENT]="";
  int status = 0;  /* CFITSIO status value MUST be initialized to zero! */
  int flg=0, anaxis, check = 1;
  Py_ssize_t ii=0, jj=0, kk=0, ll=0;
  long  firstpix[3] = {1,1,1}, anaxes[3] = {1,1,1}, onaxes[3] = {1,1,1};
  long x0=1, y0=1, nx=0, ny=0, bx=1, by=1;
  long sx=0, sy=0, fx=0, fy=0;
  double **apix=NULL, **opix=NULL, fval, value, scale=1;
  time_t t=0;
  struct tm *tmp=NULL;
  PyObject *tuple0=NULL, *tupleN=NULL, *tupleB=NULL;
  
  if(!PyArg_ParseTuple(args, "sOOOdds;resize(filename, (new_x0,y0), (new_nx,ny), (bin_x,y), filling_value, output_filename)", &fnin, &tuple0, &tupleN, &tupleB, &fval, &scale, &fnout)) return NULL;
  if(tuple0!=Py_None && !PyObject_IsInstance(tuple0, (PyObject *)&PyTuple_Type)) {PyErr_SetString(PyExc_ValueError, "The first argument must be None or a tuple of 2 integer with the new origin"); return NULL; }
  if(tupleN!=Py_None && !PyObject_IsInstance(tupleN, (PyObject *)&PyTuple_Type)) {PyErr_SetString(PyExc_ValueError, "The first argument must be None or a tuple of 2 integer with the new size"); return NULL; }
  if(tupleB!=Py_None && !PyObject_IsInstance(tupleB, (PyObject *)&PyTuple_Type)) {PyErr_SetString(PyExc_ValueError, "The first argument must be None or a tuple of 2 integer with binning values"); return NULL; }

  fits_open_file(&ifptr, fnin, READONLY, &status); /* open input images */
  if(status){ fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; }
  fits_get_img_dim(ifptr, &anaxis, &status);  /* read dimensions */
  fits_get_img_size(ifptr, 3, anaxes, &status);
  if(status){ fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; }
  if(anaxis > 2){
    printf("Error: images with > 2 dimensions are not supported\n");
    check = 0;
  }
       /* check that the input 2 images have the same size */

  nx=anaxes[0];
  ny=anaxes[1];

  if(scale<=0){ sprintf(str, "%s: Error: scaling value must be positive!", prg); PyErr_SetString(PyExc_IOError, str); return NULL; }

  if(tuple0!=Py_None){
    if(!PyArg_ParseTuple(tuple0, "ll;The first argument must be None or a tuple of 2 integer with the new origin", &x0, &y0)) return NULL;
    flg+=1;
  }

  if(tupleN!=Py_None){
    if(!PyArg_ParseTuple(tupleN, "ll;The first argument must be None or a tuple of 2 integer with the new size", &nx, &ny)) return NULL;
    flg+=2;
  }

  if(tupleB!=Py_None){
    if(!PyArg_ParseTuple(tupleN, "ll;The first argument must be None or a tuple of 2 integer with binning values", &bx, &by)) return NULL;
    flg+=4;
  }

  putchar('\n');
  if(flg==0){ sprintf(str, "%s: Error: No options used!", prg); PyErr_SetString(PyExc_IOError, str); return NULL; }
  
  if(flg&4){
    sx=(x0<1)?(1-x0) : 0;
    sy=(y0<1)?(1-y0) : 0;
    if(sx%bx || sy%by){ sprintf(str, "%s: Error: binning value is not compatible with new X0,Y0\n", prg); PyErr_SetString(PyExc_IOError, str); return NULL; }

    fx=(x0>0)? (anaxes[0]-x0+1> nx)? nx: (anaxes[0]+1-x0) : (anaxes[0]>nx+x0-1)? nx+x0-1: anaxes[0];
    fy=(y0>0)? (anaxes[1]-y0+1> ny)? ny: (anaxes[1]+1-y0) : (anaxes[1]>ny+y0-1)? ny+y0-1: anaxes[1];
    if(fx%bx || fy%by){ sprintf(str, "%s: Error: binning value is not compatible with resizing\n", prg); PyErr_SetString(PyExc_IOError, str); return NULL; }

    fx=(anaxes[0]-x0+1< nx)? nx-anaxes[0]+x0-1 : 0;
    fy=(anaxes[1]-y0+1< ny)? ny-anaxes[1]+y0-1 : 0;
    if(fx%bx || fy%by){ sprintf(str, "%s: Error: binning value is not compatible with new size\n", prg); PyErr_SetString(PyExc_IOError, str); return NULL; }
  }


  
  if(flg&1 && !(flg&2)){
    nx+=1-x0;
    ny+=1-y0;
  }
 
  onaxes[0]=nx/bx;
  onaxes[1]=ny/by;


  /* create the new empty output file if the above checks are OK */
  str[0]='!';
  memcpy(str+1, fnout, 256);
  if(check && !fits_create_file(&outfptr, str, &status)){
    /* copy all the header keywords from first image to new output file */
    fits_copy_header(ifptr, outfptr, &status);
    sprintf(card, "NAXIS1  = %ld", onaxes[0]);
    fits_update_card(outfptr, "NAXIS1", card, &status);
    sprintf(card, "NAXIS2  = %ld", onaxes[1]);
    fits_update_card(outfptr, "NAXIS2", card, &status);
    sprintf(card, "ORIGIN  = '%s by Francesco SkZ Mauro' / FITS file originator", prg);
    fits_update_card(outfptr, "ORIGIN", card, &status);
    t = time(NULL);
    tmp = localtime(&t);
    strftime(str, STRBUF, "%F %T (%Z %z)", tmp);
    sprintf(card, "LAST_MOD= '%.60s'", str);
    fits_update_card(outfptr, "LAST_MOD", card, &status);

    if(!fits_read_key(ifptr, TDOUBLE, "CRPIX1", &value, comment, &status)){
      value-=(x0-1.);
      value/=bx;
      sprintf(card, "CRPIX1  = %.8le", value);
      fits_update_card(outfptr, "CRPIX1", card, &status);

      fits_read_key(ifptr, TDOUBLE, "CRPIX2", &value, comment, &status);
      value-=(y0-1.);
      value/=by;
      sprintf(card, "CRPIX2  = %.8le", value);
      fits_update_card(outfptr, "CRPIX2", card, &status);
    }else{
      status=0;
    }
    if(!fits_read_key(ifptr, TDOUBLE, "CD1_1", &value, comment, &status)){
      value*=bx;
      sprintf(card, "CD1_1   = %.8le", value);
      fits_update_card(outfptr, "CD1_1", card, &status);

      fits_read_key(ifptr, TDOUBLE, "CD1_2", &value, comment, &status);
      value*=bx;
      sprintf(card, "CD1_2   = %.8le", value);
      fits_update_card(outfptr, "CD1_2", card, &status);

      fits_read_key(ifptr, TDOUBLE, "CD2_2", &value, comment, &status);
      value*=by;
      sprintf(card, "CD2_2   = %.8le", value);
      fits_update_card(outfptr, "CD2_2", card, &status);

      fits_read_key(ifptr, TDOUBLE, "CD2_1", &value, comment, &status);
      value*=by;
      sprintf(card, "CD2_1   = %.8le", value);
      fits_update_card(outfptr, "CD2_1", card, &status);
    }else{
      status=0;
    }


    apix = (double **) malloc(anaxes[1] * sizeof(double*)); 
    if(apix == NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str); return NULL; }
    opix = (double **) malloc(onaxes[1] * sizeof(double*)); 
    if(opix==NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str); free(apix); return NULL; }

    for(jj=0; jj<anaxes[1]; jj++){
      apix[jj] = (double *) malloc(anaxes[0] * sizeof(double)); /* mem for 1 row */
      if(apix[jj] == NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str);
        for(ii=0; ii<jj; ii++) free(apix[ii]);
        free(apix);
        free(opix);
        return NULL; }
    }
    for(jj=0; jj<onaxes[1]; jj++){
      opix[jj] = (double *) malloc(onaxes[0] * sizeof(double)); /* mem for 1 row */
      if(opix[jj] == NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str);
        for(ii=0; ii<jj; ii++) free(opix[ii]);
        free(opix);
        for(ii=0; ii<anaxes[1]; ii++) free(apix[ii]);
        free(apix);
        return NULL; }
      for(ii=0; ii<onaxes[0]; ii++)
        opix[jj][ii]=fval;
    }


    /* 2D images have 1 plane) */
    firstpix[2] = 1;
    /* loop over all rows of the plane */
    for(firstpix[1] = 1; firstpix[1] <= anaxes[1]; firstpix[1]++){
      /* Read both images as doubles, regardless of actual datatype.  */
      /* Give starting pixel coordinate and no. of pixels to read.    */
      /* This version does not support undefined pixels in the image. */

      if(fits_read_pix(ifptr, TDOUBLE, firstpix, anaxes[0], NULL, apix[firstpix[1]-1], NULL, &status))
        break;   /* jump out of loop on error */
    }
    fits_close_file(ifptr, &status);
//##############################################################
//##############################################################

    if(bx==1 && by==1){
      sx=(x0<1)?(1-x0) : 0;
      sy=(y0<1)?(1-y0) : 0;
      fx=(anaxes[0]+1-x0> onaxes[0])? onaxes[0]: (anaxes[0]+1-x0);
      fy=(anaxes[1]+1-y0> onaxes[1])? onaxes[1]: (anaxes[1]+1-y0);
//  printf("%4ld %4ld : %4ld %4ld ; %4ld %4ld\n", x0, y0, sx, sy, fx, fy);fflush(stdout);
//  printf("%4ld %4ld : %4ld %4ld ; %4ld %4ld\n", bx, by, sx+x0, sy+y0, x0+fx-1, y0+fy-1);fflush(stdout);
  
      for(jj=sy; jj<fy; jj++)
        for(ii=sx; ii<fx; ii++)
          opix[jj][ii]=scale*apix[jj+y0-1][ii+x0-1];
    }else{
      sx=(x0<1)?(1-x0)/bx : 0;
      sy=(y0<1)?(1-y0)/by : 0;
      fx=(anaxes[0]+1-x0> onaxes[0]*bx)? onaxes[0]: (anaxes[0]+1-x0)/bx;
      fy=(anaxes[1]+1-y0> onaxes[1]*by)? onaxes[1]: (anaxes[1]+1-y0)/by;
//  printf("%4ld %4ld : %4ld %4ld ; %4ld %4ld\n", x0, y0, sx+1, sy+1, fx, fy);fflush(stdout);
//  printf("%4ld %4ld : %4ld %4ld ; %4ld %4ld\n", bx, by, sx+1+x0, sy+1+y0, x0+fx-1, y0+fy-1);fflush(stdout);
  
      for(jj=sy; jj<fy; jj++)
        for(ii=sx; ii<fx; ii++)
          for(opix[jj][ii]=ll=0; ll<by; ll++)
            for(kk=0; kk<bx; kk++)
              opix[jj][ii]+=scale*apix[jj*by+y0-1+ll][ii*bx+x0-1+kk];
    }

//##############################################################
//printf("WRITE HERE\n");fflush(stdout);
//##############################################################
    firstpix[2] = 1;
    for(firstpix[1] = 1; firstpix[1] <= onaxes[1]; firstpix[1]++){
      fits_write_pix(outfptr, TDOUBLE, firstpix, onaxes[0], opix[firstpix[1]-1], &status); /* write new values to output image */
    }

    fits_close_file(outfptr, &status);
    for(jj=0; jj<anaxes[1]; jj++)
      free(apix[jj]);
    for(jj=0; jj<onaxes[1]; jj++)
      free(opix[jj]);
    
    free(apix);
    free(opix);
  }

 
  if(status){ fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; }

 return Py_BuildValue("l", status);
}
