

import collections, functools, time, io, numpy as np
from .files_from_3d import H5As3d
"""
# write out an eiger frame in esperanto format

    As described in Table 2 of https://doi.org/10.1107/S0909049513018621
    "Single-crystal diffraction at the Extreme Conditions beamline P02.2: procedure for collecting and analyzing high-pressure single-crystal data"
    André Rothkirch, G. Diego Gatta, Mathias Meyer, Sébastien Merkel, Marco Merlini and Hanns-Peter Liermann
    Journal of Synchrotron Radiation, 2013, 20(5), 711-720
"""

def pad_4( ar ):
    """ Pad the image to be NxN where N is a multiple of 4 """
    npx = max(ar.shape)
    np4 = 4*((npx+3)//4)
    ar4 = np.zeros( (np4, np4), ar.dtype )
    st0 = (ar4.shape[0] - ar.shape[0])//2
    st1 = (ar4.shape[1] - ar.shape[1])//2
    ar4[st0:st0+ar.shape[0],st1:st1+ar.shape[1]] = ar[:,:]
    return ar4

hlines = collections.OrderedDict( [ (k,v.split()) for k,v in [
        ("IMAGE", "lnx lny lbx lby spixelformat"),
        ("SPECIAL_CCD_1","delectronsperadu ldarkcorrectionswitch lfloodfieldcorrectionswitch/mode dsystemdcdb2gain ddarksignal dreadnoiserms"),
        ("SPECIAL_CCD_2","ioverflowflag ioverflowafterremeasureflag inumofdarkcurrentimages inumofmultipleimages loverflowthreshold"),
        ("SPECIAL_CCD_3","ldetector_descriptor lisskipcorrelation lremeasureturbomode bfsoftbinningflag bflownoisemodeflag"),
        ("SPECIAL_CCD_4","lremeasureinturbo_done lisoverflowthresholdchanged loverflowthresholdfromimage lisdarksignalchanged lisreadnoisermschanged lisdarkdone lisremeasurewithskipcorrelation lcorrelationshift"),
        ("SPECIAL_CCD_5","dblessingrej ddarksignalfromimage dreadnoisermsfromimage dtrueimagegain"),
        ("TIME","dexposuretimeinsec doverflowtimeinsec doverflowfilter"),
        ("MONITOR","lmon1 lmon2 lmon3 lmon4"),
        ("ABSTORUN","labstorunscale"),
        ("PIXELSIZE","drealpixelsizex drealpixelsizey dthickness"),
        ("TIMESTAMP","timestampstring"),
        ("GRIDPATTERN","filename"),
        ("STARTANGLESINDEG","dom_s dth_s dka_s dph_s"),
        ("ENDANGLESINDEG","dom_e dth_e dka_e dph_e"),
        ("GONIOMODEL_1","dbeam2indeg dbeam3indeg detectorrotindeg_x detectorrotindeg_y detectorrotindeg_z dxorigininpix dyorigininpix dalphaindeg dbetaindeg ddistanceinmm"),
        ("GONIOMODEL_2","dzerocorrectionsoftindeg_om dzerocorrectionsoftindeg_th dzerocorrectionsoftindeg_ka dzerocorrectionsoftindeg_ph"),
        ("WAVELENGTH","dalpha1 dalpha2 dalpha12 dbeta1"),
        ("MONOCHROMATOR","ddvalue–prepolfac orientation–type"),
        ("HISTORY","historystring"),
    ] ] )

hitems_help = {
        "lnx":"(M)	Image dimension in x direction in pixel count",
        "lny":"(M)	Image dimension in y direction in pixel count",
        "lbx":"(M)	Binning of the image in x direction in pixel",
        "lby":"(M)	Binning of the image in y direction in pixel",
        "spixelformat":"(M)	Bit depth of the binary stream (currently allowed 4BYTE_LONG)",

        "delectronsperadu":"(O)	Conversion electrons/ADU in case of scaled images (CCS camera has 2.1, fip60 cameras 1.0, ApexII 10-15)",
        "ldarkcorrectionswitch":"(O)	0,1 to indicate dark correction",
        "lfloodfieldcorrectionswitch/mode":"(O)	Specifier for type of flood correction (Agilent internal, 0 can be used for all non-Agilent)",
        "dsystemdcdb2gain":"(O)	System gain for DCDB2 (`double correlated divided by 2') mode. Note: historically, CrysAlisPro correlated images and divided them by 2; such images have half of the camera gain. For example, Atlas has a camera gain of 180, but its dsystemdcdb2gain is 90. See also SPECIAL_CCD_5 dtrueimagegain",
        "ddarksignal":"(O)	In ADUs",
        "dreadnoiserms":"(O)	In ADUs",

        "ioverflowflag":"(O)	Indicator for overflow occurrence in base exposure. Options are: 0: No; 1: Yes; 0x0: unused",
        "ioverflowafterremeasureflag":"(O)	Indicator for overflow occurrence in fastest/highest filter remeasure. Options are: 0: No; 1: Yes",
        "inumofdarkcurrentimages":"(O)	Number of dark current images taken",
        "inumofmultipleimages":"(O)	The image is the result of an image pile-up. inumofmultipleimages gives the number of images added together",
        "loverflowthreshold":"(O)	ADU level at which the image is considered an overflow in base exposure",

        "ldetector_descriptor":"(O)	Description for type of detector (Agilent internal): 0 can be used for all non-Agilent, remaining entries are then ignored for processing",
        "lisskipcorrelation":"(O)	Indicator for skipped image correlation. Options are: 0: No; 1: Yes; 0x0: unused",
        "lremeasureturbomode":"(O)	Indicator for usage of `remeasure turbo' (Agilent internal). 0 can be used for all non-Agilent",
        "bfsoftbinningflag":"(O)	Indicator for soft binning. Options are: 0: No; 1: Yes; 0x0: unused",
        "bflownoisemodeflag":"(O)	Indicator for usage of `low noise mode' (Agilent internal). 0 can be used for all non-Agilent",

        "lremeasureinturbo_done":"(O)	Indicator for usage of `remeasure turbo' (Agilent internal). 0 can be used for all non-Agilent",
        "lisoverflowthresholdchanged":"(O)	Indicator for changing overflow threshold. Options are: 0: No; 1: Yes; 0x0: unused",
        "loverflowthresholdfromimage":"(O)	Indicator that overflow threshold is from image. Options are: 0: No; 1: Yes; 0x0: unused",
        "lisdarksignalchanged":"(O)Indicator for changing dark signal. Options are: 0: No; 1: Yes; 0x0: unused",
        "lisreadnoisermschanged":"(O)	Indicator for changing read noise. Options are: 0: No; 1: Yes; 0x0: unused",
        "lisdarkdone":"(O)	Indicator that a dark image was done. Options are: 0: No; 1: Yes; 0x0: unused",
        "lisremeasurewithskipcorrelation":"(O)	Indicator that a remeasure procedure was done without correlation. Options are: 0: Yes; 1: No",
        "lcorrelationshift":"(O)	Value for correlation shift operation (Agilent internal). 0 can be used for all non-Agilent",

        "dblessingrej":"(O)	Blessing reject parameter (Agilent internal). 0 can be used for all non-Agilentv",
        "ddarksignalfromimage":"(O)	Self-explaining (Agilent internal)",
        "dreadnoisermsfromimage":"(O)	Self-explaining (Agilent internal)",
        "dtrueimagegain":"(O)	Actual gain for the image (Agilent internal)",

        "dexposuretimeinsec":"(M)	Base exposure time in seconds. For correlated frames the time of one frame",
        "doverflowtimeinsec":"(O)	Time used to bring frame in range",
        "doverflowfilter":"(O)	Overflow filter used. Options are: 0: No; 1: Yes",

        "lmon1":"(O)	Monitor signal channel 1",
        "lmon2":"(O)	Monitor signal channel 2",
        "lmon3":"(O)	Monitor signal channel 3",
        "lmon4":"(O)	Monitor signal channel 4",

        "labstorunscale":"(O)	Value for abstorun procedure (Agilent internal). 0 can be used for all non-Agilent",

        "drealpixelsizex":"(M)	Pixel size along x direction in mm",
        "drealpixelsizey":"(M)	Pixel size along y direction in mm Note: drealpixelsizex = drealpixelsizey is a requirement",
        "dthickness": "(O)  Sensor thickness?",

        "timestampstring":"(O)	A string containing a time stamp (not used by CrysAlisPro, but useful for documentation purpose)",

        "filename":"(O)	The Esperanto images have to be distortion free. The filename documents the grid name (Agilent internal)",

        "dom_s": "(M) start goniometer angle ω in degrees, see Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dth_s": "(M) start goniometer angle θ in degrees, see Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dka_s": "(M) start goniometer angle κ in degrees, see Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dph_s": "(M) start goniometer angle φ in degrees, see Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",

        "dom_e":"(M) end goniometer angles in degrees, see start",
        "dth_e":"(M) end goniometer angles in degrees, see start",
        "dka_e":"(M) end goniometer angles in degrees, see start",
        "dph_e":"(M) end goniometer angles in degrees, see start",

        "dbeam2indeg":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dbeam3indeg":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "detectorrotindeg_x":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "detectorrotindeg_y":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "detectorrotindeg_z":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dxorigininpix":"(M)	Beam center in x direction given in pixel (counting from 0); see Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dyorigininpix":"(M)	Beam center in y direction given in pixel (counting from 0); see Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dalphaindeg":"(M)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dbetaindeg":"(M)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "ddistanceinmm":"(M)	Sample to detector distance in millimeter (sample to detection surface, e.g. in CCDs the scintillator); see Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",

        "dzerocorrectionsoftindeg_om":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dzerocorrectionsoftindeg_th":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dzerocorrectionsoftindeg_ka":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",
        "dzerocorrectionsoftindeg_ph":"(O)	See Paciorek et al. (1999[Paciorek, W. A., Meyer, M. & Chapuis, G. (1999). Acta Cryst. A55, 543-557.]) for details",

        "dalpha1":"(M)	Self-explaining (in Å)",
        "dalpha2":"(O)	Self-explaining (in Å)",
        "dalpha12":"(O)	Self-explaining (in Å)",
        "dbeta1":"(O)	Self-explaining (in Å) Note: for synchrotron radiation one can provide the same wavelength for all four entries. In case one provides a single value for dalpha1, the optional arguments have to be 0x0",

        "ddvalue–prepolfac":"(O)	For `E1E3PLANE', `E1E2PLANE' ddvalue; for `SYNCHROTRON' prepolfac",
        "orientation–type":"(O)	Keywords: E1E2PLANE, E1E3PLANE, or SYNCHROTRON. Note: SYNCHROTRON also comprises mirrors",

        "historystring":"(O)	Some image processing history for documentation. Note: limited to single line",
    }

def eiger2_defaults(wvln):
    return { "lnx": 2164,"lny":2164, "lbx":1, "lby":1, "spixelformat":"4BYTE_LONG",
        "delectronsperadu": 1.0, "ldarkcorrectionswitch":0, "lfloodfieldcorrectionswitch/mode":0, "dsystemdcdb2gain":1.0, "ddarksignal":0.0, "dreadnoiserms":0.0,
        "ioverflowflag": 0, "ioverflowafterremeasureflag":0, "inumofdarkcurrentimages":0, "inumofmultipleimages":0,  "loverflowthreshold":90000000,
        "ldetector_descriptor":0, "lisskipcorrelation":0, "lremeasureturbomode":0, "bfsoftbinningflag":0, "bflownoisemodeflag":0,
        "lremeasureinturbo_done":0, "lisoverflowthresholdchanged":0, "loverflowthresholdfromimage":0, "lisdarksignalchanged":0, "lisreadnoisermschanged":0, "lisdarkdone":0, "lisremeasurewithskipcorrelation":0, "lcorrelationshift":0,
        "dblessingrej":0., "ddarksignalfromimage":0., "dreadnoisermsfromimage":0., "dtrueimagegain":0.,
        "dexposuretimeinsec":0.1, "doverflowtimeinsec":0., "doverflowfilter":0.,
        "lmon1":0, "lmon2":0, "lmon3":0, "lmon4":0,
        "labstorunscale": 0,
        "drealpixelsizex":0.075, "drealpixelsizey":0.075, "dthickness": 1.0,
        "timestampstring": time.asctime(),
        "filename": "notvalidstring",
        "dom_s": 0., "dth_s": 0., "dka_s": 0., "dph_s": 0.,
        "dom_e": 0., "dth_e": 0., "dka_e": 0., "dph_e": 0.,
        "dbeam2indeg": 0., "dbeam3indeg": 0., "detectorrotindeg_x": 0., "detectorrotindeg_y": 0., "detectorrotindeg_z": 0., "dxorigininpix": 1024.,
        "dyorigininpix": 1171, "dalphaindeg": 50.0, "dbetaindeg":0.0, "ddistanceinmm": 117.26,
        "dzerocorrectionsoftindeg_om": 0., "dzerocorrectionsoftindeg_th": 0., "dzerocorrectionsoftindeg_ka": 0., "dzerocorrectionsoftindeg_ph": 0.,
        "dalpha1": wvln, "dalpha2": wvln, "dalpha12": wvln, "dbeta1":wvln,
        "ddvalue–prepolfac": 0.98, "orientation–type": "SYNCHROTRON",
        "historystring": "from by %s"%(__file__)
        }

def hungfmt( item, value ):
    """ Try to format the strings
    #  b, byte (1 byte); i, short (2 bytes); l, long (4 bytes); d, double (8 bytes).
    """
    try:
        if item[0] in 'bil':
            return '%d'%(value)
        if item[0] == 'd':
            return '%.6f'%(value)
        return '"%s"'%(value)
    except:
        print(item,repr(value),type(value))
        raise

def esperanto_write_header( hd, hlines ):
    """ Write the keys in hd using the layout in hlines to a byte string """
    bio = [b"%-254s"%(b"ESPERANTO FORMAT   1 CONSISTING OF   25 LINES OF   256 BYTES EACH"),]
    nl = 1
    for key in hlines.keys():
        tokens = [key,]
        for item in hlines[key]:
            tokens.append(hungfmt(item, hd[item]))
        line = " ".join(tokens)
        bio.append(  b"\r\n%-254s"%( line.encode('ASCII') ) )
        nl += 1
    blank = b"\r\n" + b" "*254
    while nl < 25:
        bio.append( blank )
        nl += 1
    bio.append( b"\r\x1A" )
    return b"".join(bio)


class EsperantoFrom3d( H5As3d ):
    extn=".esperanto"

    def __init__(self, h5filename, scan, stem='data_1_', reverse=True,
                startangle = -180., stepangle=0.25, expo=1.0 ):
        H5As3d.__init__(self, h5filename, scan, stem='data_1_' )
        nframes = self.data.shape[0]
        self.startangle = startangle
        self.stepangle = abs(stepangle)
        self.expo = expo
        self.reverse = reverse

    def name(self, i):
        """ Generate some filename pattern """
        return "%s%d%s"%(self.stem, i+1, self.extn)

    @functools.lru_cache(maxsize=None) # grows without bound. Beware.
    def makeheader(self, i):
        hd = eiger2_defaults( 0.308 )
        hd["lny"] , hd["lny"] = self.padded.shape
        hd[ 'dom_s' ] = i*self.stepangle + self.startangle        # etc
        hd[ 'dom_e' ] = (i+1)*self.stepangle + self.startangle
        return esperanto_write_header( hd, hlines )

    def toBlob(self, i):
        """ Convert the numpy array to a file """
        blob = io.BytesIO( )
        if self.reverse:
            j = len(self.data) - 1 - i
        else:
            j = i
        self.padded = pad_4( self.data[j] )   # slow ?
        blob = bytearray( self.makeheader(i) + self.padded.tobytes() )
        return blob