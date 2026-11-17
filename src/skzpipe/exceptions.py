
#import os, subprocess, sys, shutil, math, re, time
#import datetime, glob, fileinput, tarfile, copy


class SkZpipeException(Exception):
  exc_title='';

class SkZpipeSkip(SkZpipeException):
  exc_title="\n!SKIPPING";
  def __init__(self, message='#-#', exclocus=None):
    txtfile= " {} as request. ".format(exclocus);
    message=self.exc_title+txtfile+message+"\n";
    super(SkZpipeException, self).__init__(message);

class SkZpipeWarning(SkZpipeException):
  exc_title="\n!WARNING";
  def __init__(self, message='#-#', exclocus=None, outxt=''):
    txtfile= " in {}: ".format(exclocus) if(exclocus) else ': ';
    message=outxt+self.exc_title+txtfile+message+"\n";
    super(SkZpipeException, self).__init__(message);

class SkZpipeError(SkZpipeException):
  exc_title="\n!!!ERROR";
  def __init__(self, message='#-#', exclocus=None, outxt=''):
    txtfile= " in {}: ".format(exclocus) if(exclocus) else ': ';
    message=outxt+self.exc_title+txtfile+message+"\n";
    super(SkZpipeException, self).__init__(message);
SkZp_Err=SkZpipeError

class SkZpipePsfErr(SkZpipeException):
  pass;

