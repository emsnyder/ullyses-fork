import argparse
import os
import glob
import numpy as np

from astropy.io import fits

from coadd import COSSegmentList, STISSegmentList
from coadd import abut

version = 'v0.1'

'''
This wrapper goes through each target folder in the ullyses data directory and find
the data and which gratings are present. This info is then fed into coadd.py.
'''


def main(indir, outdir, version_=version):
    for root, dirs, files in os.walk(indir, topdown=False):

        print(root)
        targetname = root.split('/')[-1]
        print(f"   {targetname}")

        # collect the gratings that we will loop through
        # coadd.py will find the correct files itself,
        # but we need to know which gratings are present
        uniqmodes = []

        for myfile in glob.glob(os.path.join(root, '*_x1d.fits')):
            f1 = fits.open(myfile)
            prihdr = f1[0].header
            obsmode = (prihdr['INSTRUME'], prihdr['OPT_ELEM'])
            if obsmode not in uniqmodes:
                uniqmodes.append(obsmode)

        if not uniqmodes:
            print(f'No data to coadd for {targetname}.')
            continue

        products = {}
        products['G130M'] = None
        products['G160M'] = None
        products['G185M'] = None
        products['E140M'] = None
        products['E230M'] = None
        products['E140H'] = None
        products['E230H'] = None
        products['cos_fuv_m'] = None
        products['cos_m'] = None
        products['stis_m'] = None
        products['stis_h'] = None
        products['all'] = None

        for instrument, grating in uniqmodes:
            # this instantiates the class
            if instrument == 'COS':
                prod = COSSegmentList(grating, path=root)
            elif instrument == 'STIS':
                prod = STISSegmentList(grating, path=root)
            else:
                print(f'Unknown mode [{instrument}, {grating}]')

            # these two calls perform the main functions
            if len(prod.members) > 0:
                prod.create_output_wavelength_grid()
                prod.coadd()
                # this writes the output file
                if not os.path.exists(outdir):
                    os.mkdir(outdir)
                outname = create_output_file_name(prod, version_)
                outname = outdir + '/' + outname
                prod.write(outname)
                print(f"   Wrote {outname}")
                products[grating] = prod
            else:
                print(f"No valid data for grating {grating}")
            products[grating] = prod

        # Create Level 3 products by abutting level 2 products
#            products['cos_fuv_m'] = coadd.abut(products['g130m'], products['g160m'])
#            products['cos_m'] = coadd.abut(products['cos_m'], products['g185m'])
#            products['stis_m'] = coadd.abut(products['e140m'], products['e230m'])
#            products['stis_h'] = coadd.abut(products['e140h'], products['e230h'])

        # Create Level 3 products by abutting level 2 products
        if products['G130M'] is not None and products['G160M'] is not None:
            products['cos_fuv_m'] = abut(products['G130M'], products['G160M'])
            filename = create_output_file_name(products['cos_fuv_m'])
            filename = outdir + '/' + filename
            products['cos_fuv_m'].write(filename)
            print(f"   Wrote {filename}")
        elif products['G130M'] is not None:
            products['cos_fuv_m'] = products['G130M']
        elif products['G160M'] is not None:
            products['cos_fuv_m'] = products['G160M']

        if products['cos_fuv_m'] is not None and products['G185M'] is not None:
            products['cos_m'] = abut(products['cos_fuv_m'], products['G185M'])
            if products['cos_m'] is not None:
                filename = create_output_file_name(products['cos_m'])
                filename = outdir + '/' + filename
                products['cos_m'].write(filename)
                print(f"   Wrote {filename}")
        elif products['cos_fuv_m'] is not None:
            products['cos_m'] = products['cos_fuv_m']
        elif products['G185M'] is not None:
            products['cos_m'] = products['G185M']
        
        if products['E140M'] is not None and products['E230M'] is not None:
            products['stis_m'] = abut(products['E140M'], products['E230M'])
            if products['stis_m'] is not None:
                filename = create_output_file_name(products['stis_m'])
                filename = outdir + '/' + filename
                products['stis_m'].write(filename)
                print(f"   Wrote {filename}")
        elif products['E140M'] is not None:
            products['stis_m'] = products['E140M']
        elif products['E230M'] is not None:
            products['stis_m'] = products['E230M']
        
        if products['E140H'] is not None and products['E230H'] is not None:
            products['stis_h'] = abut(products['E140H'], products['E230H'])
            if products['stis_h'] is not None:
                filename = create_output_file_name(products['stis_h'])
                filename = outdir + '/' + filename
                products['stis_h'].write(filename)
                print(f"   Wrote {filename}")
        elif products['E140H'] is not None:
            products['stis_h'] = products['E140H']
        elif products['E230H'] is not None:
            products['stis_h'] = products['E230H']

        if products['cos_m'] is not None and products['stis_h'] is not None:
            products['all'] = abut(products['cos_m'], products['stis_h'])
        elif products['cos_m'] is not None and products['stis_m'] is not None:
            products['all'] = abut(products['cos_m'], products['stis_m'])
        if products['all'] is not None:
            filename = create_output_file_name(products['all'])
            filename = outdir + '/' + filename
            products['all'].write(filename)
            print(f"   Wrote {filename}")


def create_output_file_name(prod):
    instrument = prod.instrument.lower()
    grating = prod.grating.lower()
    target = prod.target.lower()
    name = "hlsp_ullyses_hst_{}_{}_{}_{}_cspec.fits".format(instrument, target, grating, version)
    return name

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--indir", default="/astro/ullyses/ULLYSES_DATA/",
                        help="Directory(ies) with data to combine")
    parser.add_argument("-o", "--outdir", default=".",
                        help="Directory for output HLSPs")
    parser.add_argument("-v", "--version", default=version, 
    					help="Version number of the HLSP")
    args = parser.parse_args()

    main(args.indir, args.outdir, version_=args.version)
