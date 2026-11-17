from setuptools import setup, Extension, find_packages

###photometry/daophot###
module_daoCfunctions=Extension('skzpipe.photometry.daophot._daoCfunctions',
                               sources=['src/skzpipe/photometry/daophot/_daoCfunctions.c' ]);




###fits###
module_fitsC=Extension('skzpipe.fits._fitsC',
                               libraries=['cfitsio'],
                               sources=['src/skzpipe/fits/_fitsC.c' ]);


setup(
        ext_modules        = [ module_daoCfunctions, module_fitsC ],
        ) 
#setup(
#        name               = 'SkZpipe',
#        version            = '0.7.dev1', 
#        description        = 'Enviroment for photometric reduction',
#        author             = 'Francesco SkZ Mauro',
#        author_email       = 'skz5k2@gmail.com',
#        url                = 'https://github.com/skz5k2/SkZpipe',
#        packages           = find_packages(),
#        ext_modules        = [ module_daoCfunctions, module_fitsC ],
#        python_requires    = '>3.5.2',
#        install_requires   = ['astropy>=2.0.3', 'numpy>=1.11', 'psutil>=1.0.0'],
#        entry_points       = {'console_scripts':['OptionCheckInput=skzpipe.parameters.options:OptionCheckInput',
#                                  'InputDataInitWrite=skzpipe.functions:InputDataInitWrite',
#                                  'ExtractFromMosaic=skzpipe.functions:ExtractFromMosaic',
##
#                                  'DAO_FindThre=skzpipe.pipes.photopipe:DAO_FindThre',
#                                  'DAO_psfcal=skzpipe.pipes.photopipe:DAO_psfcal',
#                                  'DAO_srclst=skzpipe.pipes.photopipe:DAO_psfcal',
#                                  'DAO_photo_GetAph=skzpipe.pipes.photopipe:DAO_GetAph',
#                                  'DAO_photo_GetFph=skzpipe.pipes.photopipe:DAO_GetFph',
#                                  'DpFindThre=skzpipe.pipes.photopipe:DpFindThre',
#                                  'DpAls_psfcal=skzpipe.pipes.photopipe:DAO_psfcal',
#                                  'DpAls_srclst=skzpipe.pipes.photopipe:DAO_psfcal',
#                                  'DpAls_photo_GetAph=skzpipe.pipes.photopipe:DAO_GetAph',
#                                  'DpAls_photo_GetFph=skzpipe.pipes.photopipe:DAO_GetFph',
#                                  'MakeStack=skzpipe.pipes.matchstackpipe:MakeStack',
#                                  'DaoMaster=skzpipe.pipes.matchstackpipe:daomasterpipe',
#                                  'PbsStdMatch=skzpipe.pipes.pbsstdmatch:PbsStdMatch',
#                                  'CatalogPhoto=skzpipe.pipes.catalogpipe:CatalogPhoto',
##
#                                  'VVVGetImgInfo=skzpipe.pipes.vvvskzpipeline:VVVGetImgInfo',
#                                  'VVVImgdataWrite2Old=skzpipe.pipes.vvvskzpipeline:VVVImgdataWrite2Old',
#                                  'VVVImgdataTransl2Old=skzpipe.pipes.vvvskzpipeline:VVVImgdataTransl2Old',
#                                  'VVVPhoto_psfcal=skzpipe.pipes.vvvskzpipeline:VVVPhoto_psfcal',
#                                  'VVVDpAls_psfcal=skzpipe.pipes.vvvskzpipeline:VVVDpAls_psfcal',
#                                  'VVVMakeStack=skzpipe.pipes.vvvskzpipeline:VVVMakeStack',
#                                  'VVVPhoto_srclst=skzpipe.pipes.vvvskzpipeline:VVVPhoto_srclst',
#                                  'VVVDpAls_srclst=skzpipe.pipes.vvvskzpipeline:VVVDpAls_srclst',
#                                  'VVVCatalogPhoto=skzpipe.pipes.vvvskzpipeline:VVVCatalogPhoto',
#                                  'VVVAllframePhoto=skzpipe.pipes.vvvskzpipeline:VVVAllframePhoto',
##                                  'VVVMetrCalibMatch=skzpipe.pipes.vvvskzpipeline:VVVMetrCalibMatch',
#                                 ]},
#        classifiers=['Programming Language :: Python',
#                     'Programming Language :: Python :: 3',
#                     'Programming Language :: C',
#                     'Operating System :: POSIX :: Linux',
#                     'License :: Free To Use But Restricted',
#                     'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
#                     'Development Status :: 4 - Beta',
#                     'Intended Audience :: Science/Research',
#                     'Topic :: Scientific/Engineering :: Astronomy'
#                    ]
#)
