
#include <Python.h>

#include "_fitsC.h"

#include "_fits_resize.c"

#include "_fits_average.c"

#include "_fits_hdrerase.c"
#include "_fits_hdredit.c"

#include "_fits_fixbadarea.c"
#include "_fits_findIRsat.c"


static PyMethodDef fitsCMethods[] = {
  {"resize",      fitsC_resize,      METH_VARARGS, resize_docstring   },
  {"average",     fitsC_average,     METH_VARARGS, average_docstring  },
  {"hdrerase",    fitsC_hdrerase,    METH_VARARGS, hdrerase_docstring },
  {"hdredit",     fitsC_hdredit,     METH_VARARGS, hdredit_docstring  },
  {"fixbadarea",  fitsC_fixbadarea,  METH_VARARGS,  fixbadarea_docstring },
  {"findIRsat",   fitsC_findIRsat,   METH_VARARGS, findIRsat_docstring },
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef fitsCmodule= {PyModuleDef_HEAD_INIT, "_fitsC", NULL, -1, fitsCMethods};

PyMODINIT_FUNC PyInit__fitsC(void){
  return PyModule_Create(&fitsCmodule);
}
