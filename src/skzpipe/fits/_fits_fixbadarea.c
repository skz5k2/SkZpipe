


#define BUF 1000

static char fixbadarea_docstring[]="""Fix problematic areas in the image, like areas with constant value or saturated stars, setting the \n\
pixel value to a proper value.\n\
fixbadarea(filename, sky_value, sat_list, output_filename)\n\
Parameters\n\
----------\n\
    filename : str\n\
        Name of the fits image\n\
    sky_value : float\n\
        Value of the sky (used to calculated a minimum value)\n\
    sat_list : tuple of \n\
        List with position of saturated sources to fix (output of 'findIRsat')\n\
    output_filename : str\n\
        Name of the output image.\n\
";

static PyObject *fitsC_fixbadarea(PyObject *self, PyObject *args){
  fitsfile *ifptr, *outfptr;  /* FITS file pointers */
  char str[BUF+1], fnin[BUF+1], fnout[BUF+1], prg[]="fixbadarea";
  int status = 0;  /* CFITSIO status value MUST be initialized to zero! */
  int anaxis, check = 1;
  long ii, jj, kk, ll, x0, x1, y0, y1;
  long npixels = 1, firstpix[3] = {1,1,1}, anaxes[3] = {1,1,1};
  double **apix=NULL, xx, yy, sky, low;
  int **fpix=NULL, flg=0, nss=0;
  SatP *sat=NULL;
  PyObject *tupleL=NULL, *tuple0=NULL;

  if(!PyArg_ParseTuple(args, "sdOs;fixbadarea(filename, sky_value, sat_list, output_filename)", &fnin, &sky, &tupleL, &fnout)) return NULL;
  if(tupleL!=Py_None){
      if( !PyObject_IsInstance(tupleL, (PyObject *)&PyList_Type)) {
          PyErr_SetString(PyExc_ValueError, "The third argument must be None or a ilist of tuples of 4 floats and 1 integer."); 
          return NULL; 
      }else{
          nss=PyList_Size(tupleL);
          sat=(SatP*)calloc(nss, sizeof(SatP));
          for(ii=0; ii<nss; ii++){
              tuple0=PyList_GetItem(tupleL, ii);
              if(!PyObject_IsInstance(tuple0, (PyObject *)&PyTuple_Type)) {
                      PyErr_SetString(PyExc_ValueError, "The first argument must be None or a tuple of 2 integer with the new origin"); 
                      return NULL; 
              }
              if(!PyArg_ParseTuple(tuple0, "ddddl;The third argument must be None or a ilist of tuples of 4 floats and 1 integer.", &(sat[ii].x), &(sat[ii].y), &(sat[ii].dx), &(sat[ii].dy), &(sat[ii].flg))) return NULL;
              sat[ii].std=-1;
          }
      }
  }


  fits_open_file(&ifptr, fnin, READONLY, &status); /* open input images */
  if(status){ fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; }

  low=fits_getminval(sky);


  fits_get_img_dim(ifptr, &anaxis, &status);  /* read dimensions */
  fits_get_img_size(ifptr, 3, anaxes, &status);
  if(status){ fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; }

  if(anaxis > 2){
    fprintf(stderr, "%s Error: images with > 2 dimensions are not supported\n", prg);
    check = 0;
  }
       /* check that the input 2 images have the same size */

  /* create the new empty output file if the above checks are OK */
  if(check && !fits_create_file(&outfptr, fnout, &status) ){
    /* copy all the header keywords from first image to new output file */
    fits_copy_header(ifptr, outfptr, &status);

    npixels = anaxes[0];  /* no. of pixels to read in each row */

    apix = (double **) malloc(anaxes[1] * sizeof(double*)); 
    fpix = (int **) malloc(anaxes[1] * sizeof(int*)); 
    if(apix == NULL || fpix==NULL){
      printf("Memory allocation error\n");
      return Py_BuildValue("l", 10);
    }
    for(jj=0; jj<anaxes[1]; jj++){
      apix[jj] = (double *) malloc(anaxes[0] * sizeof(double)); /* mem for 1 row */
      fpix[jj] = (int *) calloc(anaxes[0],  sizeof(int));
      if(apix[jj] == NULL || fpix[jj]==NULL){
          printf("Memory allocation error\n");
          return Py_BuildValue("l", 11);
      }
    }


    /* 2D images have 1 plane) */
    firstpix[2] = 1;
    /* loop over all rows of the plane */
    for(firstpix[1] = 1; firstpix[1] <= anaxes[1]; firstpix[1]++){
      /* Read both images as doubles, regardless of actual datatype.  */
      /* Give starting pixel coordinate and no. of pixels to read.    */
      /* This version does not support undefined pixels in the image. */

      if(fits_read_pix(ifptr, TDOUBLE, firstpix, npixels, NULL, apix[firstpix[1]-1], NULL, &status))
        break;   /* jump out of loop on error */
    }
    fits_close_file(ifptr, &status);
    
//#####################################

   
//####################################
    
    
    for(jj=1; jj<anaxes[1]-1; jj++){
      for(ii=1; ii<anaxes[0]-1; ii++){
        for(flg=0,kk=-1; kk<2; kk++)
          for(ll=-1; ll<2; ll++)
            if(apix[jj][ii]==apix[jj+kk][ii+ll]) flg++;
        if(flg>=6)
          for(kk=-1; kk<2; kk++)
            for(ll=-1; ll<2; ll++)
              if(apix[jj][ii]==apix[jj+kk][ii+ll]) fpix[jj+kk][ii+ll]++;
      }

      for(ii=0; ii<anaxes[0]; ii++){
        if(fpix[jj-1][ii] && apix[jj-1][ii]>low && apix[jj-1][ii]<MAXVAL)
          apix[jj-1][ii]=-2*MAXVAL;
      }
    
    }
    for(jj=anaxes[1]-2; jj<anaxes[1]; jj++)
      for(ii=0; ii<anaxes[0]; ii++){
        if(fpix[jj][ii] && apix[jj][ii]>low && apix[jj][ii]<MAXVAL)
          apix[jj][ii]=-2*MAXVAL;
      }

//########### SAT AREAS #########################
    for(kk=0; kk<nss; kk++){
//      if(sat[kk].std<0) continue;
      x1=(long)ceil(sat[kk].x+sat[kk].dx)+1; if(x1>anaxes[0]) x1=anaxes[0];
      y1=(long)ceil(sat[kk].y+sat[kk].dy)+1; if(y1>anaxes[1]) y1=anaxes[1];
      x0=(long)floor(sat[kk].x-sat[kk].dx)-1; if(x0<0) x0=0;
      y0=(long)floor(sat[kk].y-sat[kk].dy)-1; if(y0<0) y0=0;
      for(jj=y0; jj<y1; jj++){
        for(ii=x0; ii<x1; ii++){
          xx=(ii+1-sat[kk].x)/sat[kk].dx; xx*=xx;
          yy=(jj+1-sat[kk].y)/sat[kk].dy; yy*=yy;
          if((xx+yy)<1){
            apix[jj][ii]=MAXVAL;
          }
        }
      }
    }

//######## WRITE ######################################################
    firstpix[2] = 1;
    for(firstpix[1] = 1; firstpix[1] <= anaxes[1]; firstpix[1]++){
      fits_write_pix(outfptr, TDOUBLE, firstpix, npixels, apix[firstpix[1]-1], &status); /* write new values to output image */
    }

    fits_close_file(outfptr, &status);
    for(jj=0; jj<anaxes[1]; jj++)
      free(apix[jj]);
    free(apix);
  }

 
  if(status){ fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; }
  return Py_BuildValue("l", status);
}

