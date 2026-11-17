
#ifndef DAOFORMAT

#define DAOFORMAT 1

#define DAOHDR_DEF " NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD\n"
#define DAOHDR_LEN 3
#define DAOFRMHDR_DEF_I "%3ld%6ld%6ld%8lf%8lf%8lf%8lf%8lf%8lf%8lf"
#define DAOFRMHDR_DEF_O "%3ld%6ld%6ld%8.1lf%8.1lf%8.2lf%8.2lf%8.3lf%8.3lf%8.2lf"

#define DAOLENGHT_ID 7
#define DAOLENGHT_DATA 8
#define DAOLENGHT_PREC 3
#define DAOLINE 300

typedef struct {
    long nl; /* = nl_type */
    long nx, ny;
    double low, high;
    double thresh;
    double ap1;
    double gain, ron;
    double frad;
} HeaderDao;
#define HEADERDAO_0 {0, 0,0, 0.,0., 0, 0, 0,0, 0}

HeaderDao copyheader(FILE *fin, int nout, FILE **fout){
  //copy the header from a file fin to nout files *fout
  char str[DAOLINE+1];
  int i;
  HeaderDao hdr=HEADERDAO_0, err=HEADERDAO_0;

  if(fgets(str, DAOLINE, fin)==NULL) return err;
  for(i=0; i<nout; i++) fputs(str, fout[i]);
  if(fgets(str, DAOLINE, fin)==NULL) return err;
  for(i=0; i<nout; i++) fputs(str, fout[i]);
  sscanf(str, DAOFRMHDR_DEF_I, &hdr.nl, &hdr.nx, &hdr.ny, &hdr.low, &hdr.high, &hdr.thresh, &hdr.ap1,  &hdr.gain, &hdr.ron,  &hdr.frad);
  if(fgets(str, DAOLINE, fin)==NULL) return err;
  for(i=0; i<nout; i++) fputs(str, fout[i]);
  return hdr;
}

typedef struct {
  char *in, *out;
} Doublestring;

typedef struct {
  char *type;               /* type name of the file, usually the extension                           */
  char *hdr;                /* the first line of the header (only text and the same for all, usually) */
  Doublestring frmt_hdr;           /* the format of the info in the secon dline of the header                */
  long lng_hdr;              /* how many lines the header is long                                      */
  long nl_type;              /* the value of NL field                                                  */
  long lng_row;              /* how many lines for each star                                           */
  long ndata;                /* how many data for each star (0 if not fixed)                           */
  long nfld[2];                /* how many field for each line of data for each star (0 if not fixed)                           */
  Doublestring frmt_row[];  /* format of lines of data                                                */
} Daofile;


//Daofile file_xxx={"xxx", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 1, "%8ld %8.3f %8.3f %8.3f", 1};
Daofile file_idpos={"", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 1, 1, 1, {3,0}, {{"%7ld %8lf %8lf", "%7ld %8.3lf %8.3lf"}} };
Daofile file_mag={"", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 1, 1, 1, {2,0}, {{"%8lf %8lf", " %8.3lf %8.4lf"}} };
Daofile file_als={"als", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 1, 1, 1, {9,0}, {{"%7ld %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf", "%7ld %8.3lf %8.3lf %8.3lf %8.4lf %8.3lf %8.0lf %8.3lf %8.3lf"}} };
Daofile file_alf={"alf", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 1, 1, 1, {9,0}, {{"%7ld %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf", "%7ld %8.3lf %8.3lf %8.3lf %8.4lf %8.2lf %8.0lf %8.2lf %8.3lf"}} };
Daofile file_lst={"lst", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 3, 1, 1, {5,0}, {{"%7ld %8lf %8lf %8lf %8lf", "%7ld %8.3lf %8.3lf %8.3lf %8.3lf"}} };
Daofile file_nei={"nei", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 3, 1, 1, {5,0}, {{"%7ld %8lf %8lf %8lf %8lf", "%7ld %8.3lf %8.3lf %8.3lf %8.3lf"}} };
Daofile file_coo={"coo", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 1, 1, 1, {6,0}, {{"%7ld %8lf %8lf %8lf %8lf %8lf", "%7ld %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf"}} };
Daofile file_ap ={ "ap", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 2, 2, 0, {0,0}, {{"%7ld %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf", "%7ld %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf %8.3lf"}, {"%8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf %8lf", "%8.3lf %8.3lf %8.3lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf %8.4lf"}} };
Daofile file_ap1 ={ "ap", DAOHDR_DEF, {DAOFRMHDR_DEF_I, DAOFRMHDR_DEF_O}, 3, 1, 1, 0, {0,0}, {{"%7ld %8lf %8lf %8lf %8lf %9lf %9lf %8lf", "%7ld %8.3lf %8.3lf %8.3lf %8.4lf %9.3lf %9.4lf %8.4lf"}} };


typedef struct {
  long id;
  double x, y;
  double m, err_m;
  double sky;
  double iter, chi, sharp;
} Data_als;


typedef struct {
  long id;
  double x, y;
  double *m, *err_m;
  double sky, skydev, skyskew;
} Data_ap;


typedef struct {
  long id;
  double x, y;
  double m, err_m;
  double sky, skydev, skyskew;
} Data_ap1;


typedef struct {
  long id;
  double x, y;
  double m, err_m;
} Data_lst;


typedef struct {
  long id;
  double x, y;
  double m, sky;
} Data_nei;


typedef struct {
  long id;
  double x, y;
  char data[1][DAOLINE+1];
} Data_star;

typedef struct {
  long id;
  double x, y;
  char data[2][DAOLINE+1];
} Data_star2;


typedef struct{
  FILE *f;
  char *fn;
  long type;
  long ns;
  long idmx;
  double frd, ap1;
  long nd;
  union{
        Data_als *data_als;
        Data_ap  *data_ap;
        Data_ap1 *data_ap1;
        Data_lst *data_lst;
        Data_lst *data_nei;
        Data_star *data_star;
        Data_star2 *data_star2;
      };
} FileDao;
#define FILEDAO_0 {NULL,NULL, 0, 0, 0, 0.,0., 0, {NULL}}


//int Read_Dao_Str(const chr *str, Data_dao star, char *type){
//  
//  if(type==NULL || strlen(type)<2)
//    return 1;
//  else if(strcmp(type, file_als.type)==0)
//    sscanf(str, file_als.frmt_row[0].in, &(star.als->id), &(star.als->x), &(star.als->y), &(star.als->m), &(star.als->dm), &(star.als->sky), &(star.als->nit), &(star.als->c2), &(star.als->sh));
//  else if(strcmp(type, file_ap.type)==0)
//    sscanf(str, file_ap.frmt_row[0].in, &(star.ap->id), &(star.ap->x), &(star.ap->y), &(star.ap->m), &(star.ap->dm), &(star.ap->sky), &(star.ap->nit), &(star.ap->c2), &(star.ap->sh));
//
//  return 0;
//}
//

#endif
