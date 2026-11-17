#include <string.h>
#include <stdio.h>
#include <fitsio.h>

#define BUFSTR 256
#define KEYSZ  50

typedef struct{
  char key[KEYSZ];
  char val[KEYSZ];
} Card;

static char hdredit_docstring[]="""Edit entries in header\n\
hdredit(image, dict-of-newvalues)\n\
Parameters\n\
----------\n\
    image : str\n\
        Name of the image.\n\
    hdu : int\n\
        Number of the hdu (starting with 0)\n\
    dict-of-newvalues : dict\n\
        Dict with the new values {key:value}:\n\
          key: str\n\
              cardname\n\
          value: int or float or str\n\
              value to use to update\n\
\n\
";



static PyObject *fitsC_hdredit(PyObject *self, PyObject *args){
  char str[BUFSTR], prg[]="hdredit", *img=NULL;
  char card[FLEN_CARD], newcard[FLEN_CARD], oldvalue[FLEN_CARD], comment[FLEN_COMMENT];
  fitsfile *fptr=NULL;  /* FITS file pointers */
  int status = 0;  /* CFITSIO status value MUST be initialized to zero! */
  int type, nhdu, exists=0;
  PyObject *dictkey=NULL, *pkey=NULL, *pvalue=NULL;
  Py_ssize_t  pp=0, ii=0, nkey=0;
  Card *cards;
  long hdu;
  
  if(!PyArg_ParseTuple(args, "slO!:fits.hdredit", &img, &hdu, &PyDict_Type, &dictkey)){
    sprintf(str, "%s: Error: the second argument must be a dict of header keys", prg);
    PyErr_SetString(PyExc_TypeError, str);
    return NULL;

  }
  nkey=PyDict_Size(dictkey);
  cards=(Card*) malloc(nkey*sizeof(Card));
  if(cards==NULL){sprintf(str, "%s: Error: Problems with memory allocation", prg); PyErr_SetString(PyExc_MemoryError, str); return NULL; }

  
  for(pp=ii=0; PyDict_Next(dictkey, &pp, &pkey, &pvalue); ii++){
    if(!PyObject_IsInstance(pkey, (PyObject *)&PyUnicode_Type)){
      PyErr_SetString(PyExc_ValueError, "The cardname must be a str");
      free(cards);
      return NULL;
    }
    strncpy(cards[ii].key, PyUnicode_AsUTF8(pkey), KEYSZ-1);

    if(PyObject_IsInstance(pvalue, (PyObject *)&PyUnicode_Type)){
      cards[ii].val[0]='\'';
      strncpy(cards[ii].val+1, PyUnicode_AsUTF8(pvalue), KEYSZ-3);
      strcat(cards[ii].val, "'");
    }else{
      if(pvalue==Py_None)
        cards[ii].val[0]='\0';
      else
        strncpy(cards[ii].val, PyUnicode_AsUTF8(PyObject_Str(pvalue)), KEYSZ-1);
    }
  }

  dictkey=PyDict_New();
//  for(ii=0; ii<nkey; ii++)
//    PyDict_SetItemString(dictkey,  cards[ii].key, Py_None);
     

  if(!fits_open_file(&fptr, img, READWRITE, &status)){
    fits_get_num_hdus(fptr, &nhdu, &status);
    if(hdu<0 || hdu>=nhdu){
      PyErr_SetString(PyExc_ValueError, "Wrong value for the hdu number.");
      free(cards);
      return NULL;
    }
    fits_movabs_hdu(fptr, hdu+1, &type, &status);

    for(ii=0; !status && ii<nkey; ii++){
      *str=*card=*newcard=*oldvalue=*comment='\0';
      fits_read_card(fptr, cards[ii].key, card, &status);
      if(status==202){  //Skip "keyword not found in header" error
        status=0;
        strcat(str, "ADD:");
        exists=0;
      }else{
        strcat(str, "MOD:");
        exists=1;
      }

      /* check if this is a protected keyword that must not be changed */
      if(*card && fits_get_keyclass(cards[ii].key) == TYP_STRUC_KEY){
        strcat(str, "!PROTECT!");
        PyDict_SetItemString(dictkey,  cards[ii].key, PyUnicode_FromString(str));
        continue;
      }
      
      if(*card){ //If it exists, delete or copy comment
        if(cards[ii].val[0]=='\0'){
          if(exists){
            fits_delete_key(fptr, cards[ii].key, &status);
            strcat(str, "!DELETED!");
          }else{
            strcat(str, "!NONE!");
          }
          PyDict_SetItemString(dictkey,  cards[ii].key, PyUnicode_FromString(str));
          continue;
        }
        fits_parse_value(card, oldvalue, comment, &status);
      }

      /* construct template for new keyword */
      strcpy(newcard, cards[ii].key);     /* copy keyword name */
      strcat(newcard, " = ");       /* '=' value delimiter */
      strcat(newcard, cards[ii].val);     /* new value */
      if(*comment){
        strcat(newcard, " / ");  /* comment delimiter */
        strcat(newcard, comment);     /* append the comment */
      }

      /* reformat the keyword string to conform to FITS rules */
      fits_parse_template(newcard, card, &type, &status);

      /* overwrite the keyword with the new value */
      fits_update_card(fptr, cards[ii].key, card, &status);
      strcat(str, cards[ii].val);
      PyDict_SetItemString(dictkey,  cards[ii].key, PyUnicode_FromString(str));
  

    }



  }
  fits_close_file(fptr, &status);
  free(cards);

  /* if error occured, print out error message */
  if (status) {fits_get_errstatus(status, str); PyErr_SetString(PyExc_Exception, str); return NULL;}; /* print any error message */
 return dictkey;
}


