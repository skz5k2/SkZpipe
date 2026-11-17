
#include <Python.h>

#include "format_dao.h"

#include "_daoCfunctions_makenei.c"

#include "_daoCfunctions_fixidals.c"



static PyMethodDef daoCfunctionsMethods[] = {
  {"makenei", daoCfunctions_makenei, METH_VARARGS, makenei_docstring},
  {"fixidals", daoCfunctions_fixidals, METH_VARARGS, fixidals_docstring},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef daoCfunctionsmodule= {PyModuleDef_HEAD_INIT, "_daoCfunctions", NULL, -1, daoCfunctionsMethods};

PyMODINIT_FUNC PyInit__daoCfunctions(void){
  return PyModule_Create(&daoCfunctionsmodule);
}
