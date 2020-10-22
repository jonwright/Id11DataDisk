

# This is to read hdf5 files and serve them as edfs
import os
import collections, functools
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"
import numpy
import hdf5plugin, h5py
import fabio, io

class H5As3d( object ):
    """ Maps a 3D array in a hdf5 file to stack of 2D image files """
    
    extn = ""

    def __init__(self, h5filename, scan, stem='data' ):
        self.stem = stem
        self.h5o = h5py.File( h5filename, "r" )
        self.data = self.h5o[scan]
        assert len(self.data.shape) == 3, "We need a 3D array please!"
        # Decide on which frame has which filename:
        rng = range(self.data.shape[0])
        self.filenames = [ self.name(i) for i in range(len(self)) ]
        self.filenames = set( self.filenames )
        self.current = 0
        self._file_size = None

    def name(self, i):  # to override
        """ Generate some filename pattern """
        return "%s%04d%s"%(self.stem, i+1, self.extn)

    def num(self, name): # to override
        """ Get the frame index from the filenane """
        return int( name[len(self.stem):-len(self.extn)] )-1

    def toBytesIO(self, i): # to override
        """ Convert the numpy array to a file """
        return io.BytesIO( self.data[i].tobytes() )

    def filesize(self, arg = 0): # to override
        """ Size of the files """
        if self._file_size is None:
            blob = self[arg]
            self._file_size = blob.getbuffer().nbytes
        return self._file_size

    # The rest is hopefully common to most 3D data arrays
    #  ... changes if you piece together scans in a h5 etc
    def __len__(self):
        """ Number of frames """
        return self.data.shape[0]

    def __iter__(self):
        self.current = 0
        return self

    def __next__(self):
        if self.current < len(self):
            blob = self[ None ]
            self.current += 1
            return blob
        else:
            return StopIteration

    @functools.lru_cache(maxsize=3)
    def __getitem__(self, arg):
        """
        Given a filename : return a bytesio
        """
        if arg is None:
            i = self.current
        elif isinstance( arg, int):
            i = arg
        else:
            i = self.num( arg ) # raises KeyError if missing
        if i < 0 or i > len(self):
            raise KeyError("Not found %s"%(arg))
        return self.toBytesIO(i)


class EdfFrom3d( H5As3d ):

    extn=".edf"

    def toBytesIO(self, i):
        """ Convert the numpy array to a file """
        edf = fabio.edfimage.edfimage( self.data[i] )
        # TODO: headers:
        edf.header["Omega"] = i
        edf._frames[0]._index = 0   # strange that we need to do this?
        blob = io.BytesIO( edf._frames[0].get_edf_block() )
        return blob
 
class FlatFrom3d( H5As3d ):

    extn=".raw"

    def toBytesIO( self, i):
        """ Convert the numpy array to a file """
        frm = self.data[i]
        h1 = b"BINARY slow %5d x fast %5d header 256 bytes type "%( frm.shape[0], frm.shape[1])
        header = b"%-253s\r\n\x1A"%(h1 + frm.dtype.name.encode("ASCII"))
        assert len(header)==256
        blob = io.BytesIO( header + frm.tobytes() )
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
