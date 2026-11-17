"""This package is designed to help in the photometric processing of images.

Use funcion HelpMe() to get basic info
"""
__all__=['exceptions', 'parameters', 'functions']
#from . import exceptions
from . import parameters
from . import functions
from . import mathfunct
from . import pipes
from . import fits
from . import photometry
#from . import match
#from . import stacking
##from . import 
#

from .parameters.basicpar import ParameterList 

def HelpMe():
  """Quick help and information:List modules, parameters and options."""

  _name_='HelpMe'
  import pydoc

  pydoc.pager(functions.FramedText('SkZpipe')+"""

This package is designed to help in the photometric processing of images.

PACKAGE CONTENTS
    parameters:
                -  basicpar
                -  daoparameters
                -  database
                -  options
                -  classes:
                            - bclasses
                            - fileclass:
                                         - basefile
                                         - daofile
    exceptions
    photometry:
                - photo
                - photofunctions
                - daophot:
                           - daophals
                           - allframe
                           - daofunctions
                - standards:
                             - std
                             - stetson
                             - twomass
    functions
    compare
    fits
    match
    mathfunct
    stacking
    pipes:
           - catalogpipe
           - matchstackpipe
           - pbsstdmatch
           - photopipe
           - vspipe/vvvskzpipeline

  
The package functioning is centered mainly on the internal inputdata database, that provides the list 
of images that the user want to process and all the related information for the procedures. 

The list of images can be produced through the elaboration of two different kind of input data:
  * the actual list of images with attitional information for the database
  * a list of mosaic from which to extract the images, with extraction info
 
The main function is functions.InputDataInitialize, that initializes the internal database of input data. 
It can be run manually, or by the scripts in 'pipes' module.

""")
  help(functions.InputDataInitialize);

  pydoc.pager(functions.FramedText('Parameters') +'\n\n'+ ParameterList(viewer='return'))

  pydoc.pager(functions.FramedText('Options')+"""

The options are setted in several subsets:
          debugging : debugging options
          output    : options to manage standard output and error
          progr     : options for external programs
          mp        : options for multiprocessing
          image     : options for image extraction from mosaics
          inputdata : options for creation of input database
          photo     : option for photometric procedures
          match     : options for matching procedures
          stack     : options for stacking procedures

Each subset can have other subsets.
The name of an option is determined by the subsets names and its name joined by a colon (e.g. 
'output:stderr:hide', 'stack:match:improvepos:param').
The parameters.options module also includes all the fuctions to manage them.

          """)
  help(parameters.options);
  parameters.options.OptionApropos('progr:')
  parameters.options.OptionApropos('image:')
  parameters.options.OptionApropos('inputdata:')


