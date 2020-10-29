

# This is to read hdf5 files and serve them as edfs
import os
import collections, functools
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"
import numpy
import hdf5plugin, h5py
import fabio, io
from . import LRU_CACHE_SIZE

class H5As3d( object ):
    """ Maps a 3D array in a hdf5 file to stack of 2D image files """

    extn = ""
    fmt = "%s%04d%s"
    def __init__(self, h5filename, dataset, stem='data', **kwds):
        """
        h5filename = h5file to get the data from
        dataset = 3d array to map
        stem = output name stem
        """
        self.stem = stem
        self.h5o = h5py.File( h5filename, "r" )
        self.data = self.h5o[dataset]
        assert len(self.data.shape) == 3, "We need a 3D array please!"
        # Decide on which frame has which filename:
        self.filename_list = [ self.name(i) for i in range(len(self)) ]
        self.filename_lut = { fname : i for i,fname in enumerate(self.filename_list) }
        self.filenames = set( self.filename_list )
        self.current = 0
        for key in kwds.keys():
            setattr( self, key, kwds[key] )
        self._file_size = None

    def name(self, i):  # to override
        """ Generate some filename pattern """
        return self.fmt%(self.stem, i+1, self.extn)

    def num(self, name): # to override
        """ Get the frame index from the filenane """
        return self.filename_lut[name]

    def toBlob(self, i): # to override
        """ Convert the numpy array to a file """
        return bytearray( self.data[i].tobytes() )

    def filesize(self, arg=0): # to override
        """ Size of the files """
        if self._file_size is None:
            blob = self[arg]
            self._file_size = len(blob) #getbuffer().nbytes
        return self._file_size

    # The rest is hopefully common to most 3D data arrays
    #  ... changes if you piece together scans in a h5 etc
    def __len__(self):
        """ Number of frames """
        return self.data.shape[0]

    @functools.lru_cache(maxsize=LRU_CACHE_SIZE) #
    def __getitem__(self, arg):
        """
        Given a filename : return a Blob
        """
        if isinstance( arg, int ):
            i = arg
        else:
            i = self.num( arg ) # raises KeyError if missing
        if i < 0 or i >= len(self):
            raise KeyError("Not found %s"%(arg))
        return self.toBlob(i)


class EdfFrom3d( H5As3d ):

    extn=".edf"

    def toBlob(self, i):
        """ Convert the numpy array to a file """
        edf = fabio.edfimage.edfimage( self.data[i] )
        edf._frames[0]._index = 0   # strange that we need to do this?
        edf.header['Omega'] = self.startangle + i*self.stepangle
        edf.header['OmegaStep'] = self.stepangle
        blob = bytearray( edf._frames[0].get_edf_block() )
        return blob

class FlatFrom3d( H5As3d ):

    extn=".raw"

    def toBlob( self, i):
        """ Convert the numpy array to a file """
        frm = self.data[i]
        h1 = b"BINARY slow %5d x fast %5d header 256 bytes type "%( frm.shape[0], frm.shape[1])
        header = b"%-253s\r\n\x1A"%(h1 + frm.dtype.name.encode("ASCII"))
        assert len(header)==256
        blob = bytearray( header + frm.tobytes() )
        return blob

if __name__=="__main__":
    # Potential program here: write the blobs to disk
    import sys
    e = EdfFrom3d( sys.argv[1], sys.argv[2] )
    blob = e[0]
    print(len(e), e.filenames[0], e.filesize() )
    e = FlatFrom3d( sys.argv[1], sys.argv[2] )
    blob = e[0]
    print(len(e), e.filenames[0], e.filesize() )
