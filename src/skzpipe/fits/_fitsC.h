#include <math.h>
#include <string.h>
#include <stdio.h>
#include <fitsio.h>




#define MAXVAL 1e6
#define MAXRAD 15
#define MAXDIA (MAXRAD<<1)
#define VARLIM -10
#define NEGPIXL 5


typedef struct{
  int x;
  int y;
} Coord;


typedef struct{
  double x;
  double y;
  double dx;
  double dy;
  long flg;
  long std;
} SatP;


typedef struct{
  int x;
  int y;
  int son[8];
  int nson;
  int par[8];
  int npar;
} Negp;

double fits_getminval(double val){
  if(val<=0)
    return 0;
  else
    return (val-5*sqrt(val));
}

