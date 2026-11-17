#include <string.h>
#include <stdio.h>
#include <fitsio.h>

#define BUFSTR 256
#define KEYSZ  50


static char hdrerase_docstring[]="""Erase entries in header\n\
hdrerase(image, list-of-keys)\n\
Parameters\n\
----------\n\
    image : str\n\
        Name of the image.\n\
    list-of-keys : list of str\n\
        List of keys to erase\n\
\n\
";


static PyObject *fitsC_hdrerase(PyObject *self, PyObject *args){
  char str[BUFSTR], prg[]="hdrerase", *img=NULL, **keys=NULL;
  fitsfile *fptr=NULL;  /* FITS file pointers */
  int status = 0;  /* CFITSIO status value MUST be initialized to zero! */
  PyObject *listkey=NULL, *pyobj=NULL;
  Py_ssize_t  ii=0, nkey=0;
  
  if(!PyArg_ParseTuple(args, "sO!:fits.hdrerase", &img, &PyList_Type, &listkey)){
    PyErr_Clear();
    nkey=1;
    keys=(char**) malloc(1*sizeof(char*));
    if(keys==NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str); return NULL; }
    keys[0]=(char*) malloc(KEYSZ*1*sizeof(char));
    
    if(!PyArg_ParseTuple(args, "ss:fits.hdrerase", &img, keys[0])){
      free(keys[0]);
      free(keys);
      sprintf(str, "%s: Error: the second argument must be a header key or a list of header keys", prg);
      PyErr_SetString(PyExc_TypeError, str);
      return NULL;
    }

  }else{
    nkey=PyList_Size(listkey);
    keys=(char**) malloc(nkey*sizeof(char*));
    if(keys==NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str); return NULL; }
    keys[0]=(char*) malloc(KEYSZ*nkey*sizeof(char));
    if(keys[0]==NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str); free(keys); return NULL; }
    for(ii=1; ii<nkey; ii++)
       keys[ii]=keys[0]+(ii*KEYSZ);

    for(ii=0; ii<nkey; ii++){
      pyobj=PyList_GetItem(listkey, ii);
      if(!PyObject_IsInstance(pyobj, (PyObject *)&PyUnicode_Type)){
        PyErr_SetString(PyExc_ValueError, "The second argument must be a list of header keys");
        free(keys[0]);
        free(keys);
        return NULL;
      }
      strncpy(keys[ii], PyUnicode_AsUTF8(pyobj), KEYSZ-1); 
    }
  }
  

  if(!fits_open_file(&fptr, img, READWRITE, &status)){
    for(ii=0; ii<nkey; ii++){
      /* check if this is a protected keyword that must not be changed */
      if (keys[ii] && fits_get_keyclass(keys[ii]) != TYP_STRUC_KEY){
        fits_delete_key(fptr, keys[ii], &status);
        if(status==202) status=0;  //Skip "keyword not found in header" error
      }
    }
    fits_close_file(fptr, &status);
  } 
  free(keys[0]);
  free(keys);

  /* if error occured, print out error message */
  if (status) {fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL;}; /* print any error message */
 return Py_BuildValue("l", status);
}


