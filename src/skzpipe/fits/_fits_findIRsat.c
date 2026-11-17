

#define DBG 0

static char findIRsat_docstring[]="""Localize saturated stars in IR images.\n\
findIRsat(filename, sky_value, max_value, output_list)\n\
Parameters\n\
----------\n\
    filename : str\n\
        Name of the fits image\n\
    sky_value : float\n\
        Value of the sky\n\
    max_value : float \n\
        Value of saturation or maximum value for the image\n\
    output_list : list or None\n\
        List where to append the data of the saturated stars.\n\
Return\n\
------\n\
    output_list : list of tuples\n\
        Return the list of the saturated sources. For each source\n\
                                              \n\
          min_value = val-5*sqrt(sky_value)\n\
        val =(sky_value+max_value)/2\n\
";

static PyObject *fitsC_findIRsat(PyObject *self, PyObject *args){
    char str[BUF+1], fnin[BUF+1], prg[]="findIRsat";
    fitsfile *ifptr; 
    int status = 0, anaxis;
    long npix = 1, firstpix[3] = {1,1,1}, anaxes[3] = {1,1,1};
    long ii, jj, kk, ll, nn, i, iii, jjj, x0, x1, y0, y1;
    long flg=0, flgc=0, nsat=0, nneg=0, mxrd=0;
    double **apix=NULL, **vpix=NULL, maxval=-1, minval=MAXVAL, sky=0, val=0, xx, yy, ww;
    Coord brd[3][3];
    SatP *sat;
    Negp negp[(NEGPIXL+2)*(NEGPIXL+2)];
    PyObject *outL=NULL; //, *tuple0=NULL;
  
    if(!PyArg_ParseTuple(args, "sddO;findIRsat(filename, sky_value, max_value, output_list)", &fnin, &sky, &maxval, &outL)) return NULL;
    if(outL!=Py_None){
        if( !PyObject_IsInstance(outL, (PyObject *)&PyList_Type)) {
            PyErr_SetString(PyExc_ValueError, "The last argument must be None or list");
            return NULL;
        }
    }
    else outL=PyList_New(0);

    fits_open_file(&ifptr, fnin, READONLY, &status); /* open input images */
    if(status){ fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; }

    if(sky>=maxval){
        sprintf(str, "%s Error: sky>=maxval!\n", prg);
        PyErr_SetString(PyExc_ValueError, str);
        return NULL;
    }
    minval=fits_getminval(sky);
    val=.5*(maxval+sky);



    fits_get_img_dim(ifptr, &anaxis, &status);  /* read dimensions */
    fits_get_img_size(ifptr, 3, anaxes, &status);
    if(status){
        fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL; 
    }

    if(anaxis > 2){
        sprintf(str, "%s Error: images with > 2 dimensions are not supported\n", prg);
        PyErr_SetString(PyExc_ValueError, str);
        return NULL;
    }


    sat=(SatP *) calloc((long)ceil(anaxes[0] *anaxes[1]/25), sizeof(SatP)); 
    apix=(double **) malloc(anaxes[1] * sizeof(double*)); 
    vpix=(double **) malloc(anaxes[1] * sizeof(double*)); 
    if(apix==NULL || vpix==NULL){
        sprintf(str,"%s: Memory allocation error", prg);
        PyErr_SetString(PyExc_ValueError, str);
        return NULL;
    }
    for(jj=0; jj<anaxes[1]; jj++){
      apix[jj] = (double *) malloc(anaxes[0] * sizeof(double)); /* mem for 1 row */
      vpix[jj] = (double *) calloc(anaxes[0],  sizeof(double));
      if(apix[jj] == NULL || vpix[jj]==NULL){
          sprintf(str,"%s Memory allocation error\n", prg);
          PyErr_SetString(PyExc_ValueError, str);
          return NULL;
      }
    }
  
  
    /* 2D images have 1 plane */
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
  //printf("By deep hole\n");fflush(stdout);
  //##############################################################
    for(jj=0; jj<anaxes[1]; jj++)
      for(ii=0; ii<anaxes[0]; ii++){
          if(apix[jj][ii]>=minval || apix[jj][ii]<=-MAXVAL) continue;
          flg=0;
  //printf("\n%4ld %4ld", ii+1, jj+1);
          for(kk=0; kk<nsat; kk++){
              xx=(ii-sat[kk].x)/sat[kk].dx; xx*=xx;
              yy=(jj-sat[kk].y)/sat[kk].dy; yy*=yy;
              if(xx<=1 && yy<=1){
                  flg=-1;
                  ii+=(int)floor(sat[kk].dx);
                  break;
              }
          }
          if(flg==-1){ flg=0; continue;}
    //#############CENTER##############
          for(y1=jj+1; y1<anaxes[1] && !(apix[y1][ii]>=minval || apix[y1][ii]<=-MAXVAL); y1++);
          y0=jj-2; if(y0<0) y0=0;
          if(y1<jj+5+1) y1=jj+5+1; 
          if(y1>anaxes[1]) y1=anaxes[1];
          jjj=((y1-y0)>>1)+1; if(jjj<5+1) jjj=5+1; 
          x0=ii-jjj; if(x0<0) x0=0;
          x1=ii+jjj; if(x1>anaxes[0]) x1=anaxes[0];
          xx=yy=npix=0;
          for(jjj=y0; jjj<y1; jjj++)
            for(iii=x0; iii<x1; iii++)
              if(apix[jjj][iii]<minval && apix[jjj][iii]>-MAXVAL){
                xx+=iii;
                yy+=jjj;
                npix++;
              }
          memset(brd, 0, 3*3*sizeof(Coord));
          brd[0][0].x=(int)floor(xx/npix+.5);
          brd[0][0].y=(int)floor(yy/npix+.5);
          iii=brd[0][0].x;
          jjj=brd[0][0].y;
          x0=(long)floor(sqrt(npix)*.5+.5);
          mxrd=(long)ceil(sqrt(npix<<1)); if(mxrd<10) mxrd=10;
          
    //printf("  P:%4ld %4ld (%2ld)", iii+1, jjj+1, mxrd);
    //###############XXXXXX######################
          for(kk=x0; kk<mxrd && iii+kk+2<anaxes[0]; kk++){
              if(apix[jjj][iii+kk]<=minval) continue;
              for(flgc=0,ll=-1; ll<2; ll++)
                  if(jjj+ll>=0 && jjj+ll<anaxes[1] && apix[jjj+ll][iii+kk]>=val){flgc=1; break;}
              if(flgc && apix[jjj][iii+kk]>apix[jjj][iii+kk+1] && apix[jjj][iii+kk+1]>apix[jjj][iii+kk+2]){
                  flg=1;
                  brd[2][0].x=iii+kk, brd[2][0].y=jjj;
                  break;
              }
          }
          if(flg!=1 && kk==mxrd){ flg=0; continue;}
          if(flg!=1 && kk!=mxrd){
              flg=1;
              brd[2][0].x=-kk, brd[2][0].y=jjj;
          }
          
    
          for(kk=x0; kk<mxrd && iii-kk-1>0; kk++){
              if(apix[jjj][iii-kk]<=minval) continue;
              for(flgc=0,ll=-1; ll<2; ll++)
                  if(jjj+ll>=0 && jjj+ll<anaxes[1] && apix[jjj+ll][iii-kk]>=val){flgc=1; break;}
              if(flgc && apix[jjj][iii-kk]>apix[jjj][iii-kk-1] && apix[jjj][iii-kk-1]>apix[jjj][iii-kk-2]){
                  flg=2;
                  brd[1][0].x=iii-kk, brd[1][0].y=jjj;
                  break;
              }
          }
          if(flg!=2 && kk==mxrd){ flg=0; continue;}
          if(flg!=2 && kk!=mxrd){
              brd[1][0].x=-kk, brd[1][0].y=jjj;
          }
    
          if(brd[2][0].x<0){
              brd[2][0].x=iii+((iii-brd[1][0].x+brd[2][0].x>0)? iii-brd[1][0].x: -brd[2][0].x);
          }
          if(brd[1][0].x<0){
              brd[1][0].x=iii+((brd[2][0].x-iii+brd[1][0].x>0)? iii-brd[2][0].x: brd[1][0].x);
          }
          brd[0][0].x=(int)floor(.5*(brd[1][0].x+brd[2][0].x)+.5);
          iii=brd[0][0].x;
    //printf("  x:%4ld %4ld", iii+1, jjj+1);
    //###############YYYYYYYYY######################
    
          for(kk=x0; kk<mxrd && jjj+kk+2<anaxes[1]; kk++){
              if(apix[jjj+kk][iii]<=minval) continue;
              for(flgc=0,ll=-1; ll<2; ll++)
                  if(iii+ll>=0 && iii+ll<anaxes[0] && apix[jjj+kk][iii+ll]>=val){flgc=1; break;}
              if(flgc && apix[jjj+kk][iii]>apix[jjj+kk+1][iii] && apix[jjj+kk+1][iii]>apix[jjj+kk+2][iii]){
                  flg=3;
                  brd[0][2].x=iii, brd[0][2].y=jjj+kk;
                  break;
              }
          }
          if(flg!=3 && kk==mxrd){ flg=0; continue;}
          if(flg!=3 && kk!=mxrd){
              brd[0][2].x=iii, brd[0][2].y=-kk;
          }
    
          for(kk=x0; kk<mxrd && jjj-kk-1>0; kk++){
              if(apix[jjj-kk][iii]<=minval) continue;
              for(flgc=0,ll=-1; ll<2; ll++)
                  if(iii+ll>=0 && iii+ll<anaxes[0] && apix[jjj-kk][iii+ll]>=val){flgc=1; break;}
              if(flgc && apix[jjj-kk][iii]>apix[jjj-kk-1][iii] && apix[jjj-kk-1][iii]>apix[jjj-kk-2][iii]){
                  flg=4;
                  brd[0][1].x=iii, brd[0][1].y=jjj-kk;
                  break;
              }
          }
          if(flg!=4 && kk==mxrd){ flg=0; continue;}
          if(flg!=4 && kk!=mxrd){
              brd[0][1].x=iii, brd[0][1].y=-kk;
          }
    
          if(brd[0][2].y<0){
              brd[0][2].y=jjj+((jjj-brd[0][1].y+brd[0][2].y>0)? jjj-brd[0][1].y: -brd[0][2].y);
          }
          if(brd[0][1].y<0){
              brd[0][1].y=jjj+((brd[0][2].y-jjj+brd[0][1].y>0)? jjj-brd[0][2].y: brd[0][1].y);
          }
          brd[0][0].y=(int)floor(.5*(brd[0][1].y+brd[0][2].y)+.5);
          jjj=brd[0][0].y;
    //        xx=brd[2][0].y-brd[1][0].x+1;
    //        yy=brd[0][2].y-brd[0][1].y+1;
    //printf("  y:%4ld %4ld", iii+1, jjj+1);
    //#################################################################
          for(kk=0; kk<nsat; kk++){
            xx=(brd[0][0].x-sat[kk].x)/sat[kk].dx; xx*=xx;
            yy=(brd[0][0].y-sat[kk].y)/sat[kk].dy; yy*=yy;
            if(xx<=1 && yy<=1){
              flg=0;
              ii+=(int)floor(sat[kk].dx);
              break;
            }
          }
          if(!flg){ flg=0; continue;}
    //printf("  P:%4ld %4ld", iii+1, jjj+1);
    //###########################
          sat[nsat].flg=-1;
          sat[nsat].x=.5*(brd[2][0].x+brd[1][0].x);
          sat[nsat].y=.5*(brd[0][2].y+brd[0][1].y);
          sat[nsat].dx=.5*(brd[2][0].x-brd[1][0].x);
          sat[nsat].dy=.5*(brd[0][2].y-brd[0][1].y);
    
          if( PyList_Append(outL, Py_BuildValue("(d,d, d,d, l)", sat[nsat].x+1, sat[nsat].y+1,  sat[nsat].dx, sat[nsat].dy,  sat[nsat].flg) )) return NULL;
    
          nsat++;
          ii=brd[2][0].x;
      }
    
    //##############################################################
    //printf("By deep variation\n");fflush(stdout);
  //##############################################################
  //Variation map
    for(jj=0; jj<anaxes[1]; jj++)
        for(ii=0; ii<anaxes[0]; ii++){
            if(apix[jj][ii]<=minval){
                vpix[jj][ii]=-1e3;
            }else if(apix[jj][ii]>=MAXVAL){
                vpix[jj][ii]=+1e3;
            }else{
                for(npix=-1,xx=-apix[jj][ii],kk=-1; kk<2; kk++)
                    for(ll=-1; ll<2; ll++)
                        if(jj+kk>=0 && jj+kk<anaxes[1] && ii+ll>=0 && ii+ll<anaxes[0]){
                            xx+=apix[jj+kk][ii+ll];
                            npix++;
                        }
                vpix[jj][ii]=(apix[jj][ii]-xx/npix)/sqrt(apix[jj][ii]);
            }
        }
  
  //##############################
  //#############FIND#############
    for(jj=5; jj+5<anaxes[1]; jj++)
      for(ii=5; ii+5<anaxes[0]; ii++){
  //      if(apix[jj][ii]<minval) continue;
        flg=0;
        if(vpix[jj][ii]<-10){
        //##CHECK FOR KNOWN##
          for(kk=0; kk<nsat; kk++){
            xx=(ii-sat[kk].x)/sat[kk].dx; xx*=xx;
            yy=(jj-sat[kk].y)/sat[kk].dy; yy*=yy;
            if(xx<=1 && yy<=1){
              flg=-1;
              ii+=(int)floor(sat[kk].dx);
              break;
            }
          }
          if(flg==-1){ flg=0; continue;}
        //#####CHECK FOR ENOUGH POSITIVE#############
          for(flgc=0,kk=-2; kk<4; kk++)
            for(ll=-2; ll<4; ll++)
              if(jj+kk>=0 && jj+kk<anaxes[1] && ii+ll>=0 && ii+ll<anaxes[0] && vpix[jj+kk][ii+ll]>7) flgc++;
          if(flgc<12){ flg=0; continue;}
  //#############CHECK##############
          memset(brd, 0, 3*3*sizeof(Coord));
          memset(negp, 0, (NEGPIXL+2)*(NEGPIXL+2)*sizeof(Negp));
          nneg=1;
          negp[0].x=ii;
          negp[0].y=jj;
          for(nn=0; nn<nneg && nn<NEGPIXL*NEGPIXL; nn++){
            iii=negp[nn].x;
            jjj=negp[nn].y;
            for(kk=-1; kk<2; kk++)
              for(ll=-1; ll<2; ll++)
                if((!kk || !ll) && jjj+kk>=0 && jjj+kk<anaxes[1] && iii+ll>=0 && iii+ll<anaxes[0] && (kk || ll) && vpix[jjj+kk][iii+ll]<0){
                  for(i=0; i<nneg; i++){
                    if(i!=nn && negp[i].x==iii+ll && negp[i].y==jjj+kk){
                      negp[nn].son[negp[nn].nson++]=i;
                      negp[i].par[negp[i].npar++]=nn;
                      break;
                    }
                  }
                  if(nneg<(NEGPIXL+2)*(NEGPIXL+2) && i==nneg){
                    negp[nneg].x=iii+ll;
                    negp[nneg].y=jjj+kk;
  
                    negp[nn].son[negp[nn].nson++]=nneg;
                    negp[nneg].par[negp[nneg].npar++]=nn;
  
                    nneg++;
                  }
                }
          }
  //##################
          if(nneg==1){ 
            flg=0;
            xx=ii;
            yy=jj;
            brd[0][0].x=ii;
            brd[0][0].y=jj;
          }else{
            for(flgc=i=0; i<nneg; i++)
              if(negp[i].npar==negp[i].nson) flgc++;
            if(flgc==nneg){
              flg=0;
              for(ww=xx=yy=i=0; i<nneg; i++){
                xx+=vpix[negp[i].y][negp[i].x]*negp[i].x;
                yy+=vpix[negp[i].y][negp[i].x]*negp[i].y;
                ww+=vpix[negp[i].y][negp[i].x];
              }
              xx/=ww;
              yy/=ww;
              brd[0][0].x=(int)floor(xx+.5);
              brd[0][0].y=(int)floor(yy+.5);
            }else{
              flg=0; continue;
            }
          }
          if(flg){flg=0; continue;}
  
  //###############XXXXXX######################
          iii=brd[0][0].x;
          jjj=brd[0][0].y;
          x0=1;
          for(flgc=0,kk=x0; kk<MAXRAD && iii+kk+2<anaxes[0]; kk++){
            if(vpix[jjj][iii+kk]>5) flgc++;
            if(flgc && vpix[jjj][iii+kk+1]<0 && ((vpix[jjj-1][iii+kk+1]<0 && vpix[jjj+1][iii+kk+1]<0) || vpix[jjj][iii+kk+2]<0)){
              flg=1;
              brd[2][0].x=iii+kk, brd[2][0].y=jjj;
              break;
            }
          }
          if(flg!=1 && kk==MAXRAD){ flg=0; continue;}
          if(flg!=1 && kk!=MAXRAD){
            flg=1;
            brd[2][0].x=-kk, brd[2][0].y=jjj;
          }
          
  
          for(flgc=0,kk=x0; kk<MAXRAD && iii-kk-1>0; kk++){
            if(vpix[jjj][iii-kk]>5) flgc++;
            if(flgc && vpix[jjj][iii-kk-1]<0 && ((vpix[jjj-1][iii-kk-1]<0 && vpix[jjj+1][iii-kk-1]<0) || vpix[jjj][iii-kk-2]<0)){
              flg=2;
              brd[1][0].x=iii-kk, brd[1][0].y=jjj;
              break;
            }
          }
          if(flg!=2 && kk==MAXRAD){ flg=0; continue;}
          if(flg!=2 && kk!=MAXRAD){
            brd[1][0].x=-kk, brd[1][0].y=jjj;
          }
  
          if(brd[2][0].x<0){
            brd[2][0].x=iii+((iii-brd[1][0].x+brd[2][0].x>0)? iii-brd[1][0].x: -brd[2][0].x);
          }
          if(brd[1][0].x<0){
            brd[1][0].x=iii+((brd[2][0].x-iii+brd[1][0].x>0)? iii-brd[2][0].x: brd[1][0].x);
          }
         //###### 0.X #########
          brd[0][0].x=(int)floor(.5*(brd[1][0].x+brd[2][0].x)+.5);
  /*        if(fabs(brd[0][0].x-xx) > 2){
            if(2*xx>(brd[1][0].x+brd[2][0].x)){
              brd[1][0].x=(int)floor(2*x-brd[2][0].x+.5);
            }else{
              brd[2][0].x=(int)floor(2*x-brd[1][0].x+.5);
            }
          }  */
          iii=brd[0][0].x;
  //###############YYYYYYYYY######################
          for(flgc=0,kk=x0; kk<MAXRAD && jjj+kk+1<anaxes[1]; kk++){
            if(vpix[jjj+kk][iii]>5) flgc++;
            if(flgc && vpix[jjj+kk+1][iii]<0 && ((vpix[jjj+kk+1][iii-1]<0 && vpix[jjj+kk+1][iii+1]<0) || vpix[jjj+kk+2][iii]<0)){
              flg=3;
              brd[0][2].x=iii, brd[0][2].y=jjj+kk;
              break;
            }
          }
          if(flg!=3 && kk==MAXRAD){ flg=0; continue;}
          if(flg!=3 && kk!=MAXRAD){
            brd[0][2].x=iii, brd[0][2].y=-kk;
          }
          
          for(flgc=0,kk=x0; kk<MAXRAD && jjj-kk>0; kk++){
            if(vpix[jjj-kk][iii]>5) flgc++;
            if(flgc && vpix[jjj-kk-1][iii]<0 && ((vpix[jjj-kk-1][iii-1]<0 && vpix[jjj-kk-1][iii+1]<0) || vpix[jjj-kk-2][iii]<0)){
              flg=4;
              brd[0][1].x=iii, brd[0][1].y=jjj-kk;
              break;
            }
          }
          if(flg!=4 && kk==MAXRAD){ flg=0; continue;}
          if(flg!=4 && kk!=MAXRAD){
            brd[0][1].x=iii, brd[0][1].y=-kk;
          }
          
          if(brd[0][2].y<0){
            brd[0][2].y=jjj+((jjj-brd[0][1].y+brd[0][2].y>0)? jjj-brd[0][1].y: -brd[0][2].y);
          }
          if(brd[0][1].y<0){
            brd[0][1].y=jjj+((brd[0][2].y-jjj+brd[0][1].y>0)? jjj-brd[0][2].y: brd[0][1].y);
          }
  
         //###### 0.Y #########
          brd[0][0].y=(int)floor(.5*(brd[0][1].y+brd[0][2].y)+.5);
          jjj=brd[0][0].y;
  
  //##########################
        //##CHECK FOR KNOWN##
          for(kk=0; kk<nsat; kk++){
            xx=(brd[0][0].x-sat[kk].x)/sat[kk].dx; xx*=xx;
            yy=(brd[0][0].y-sat[kk].y)/sat[kk].dy; yy*=yy;
            if(xx<=1 && yy<=1){
              flg=0;
              ii+=(int)floor(sat[kk].dx);
              break;
            }
          }
          if(!flg){ flg=0; continue;}
  //###########################
          sat[nsat].flg=0;
          sat[nsat].x=.5*(brd[2][0].x+brd[1][0].x);
          sat[nsat].y=.5*(brd[0][2].y+brd[0][1].y);
          sat[nsat].dx=.5*(brd[2][0].x-brd[1][0].x);
          sat[nsat].dy=.5*(brd[0][2].y-brd[0][1].y);
  
          if( PyList_Append(outL, Py_BuildValue("(d,d, d,d, l)", sat[nsat].x+1, sat[nsat].y+1,  sat[nsat].dx, sat[nsat].dy,  sat[nsat].flg) )) return NULL;
          
          nsat++;
          ii=brd[2][0].x;
        }
      }
      
      
  
  
    free(sat);
    for(jj=0; jj<anaxes[1]; jj++){
      free(apix[jj]);
      free(vpix[jj]);
    }
    free(apix);
    free(vpix);
  
   
  //  return Py_BuildValue("(d,d,d)", minval, val, maxval);
    return outL;
}
  
