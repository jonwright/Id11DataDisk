#!/usr/bin/env python3

# This code is mostly copied from:
# https://github.com/clach04/refuse/blob/example/src/examples/loopback.py
#
# These imports are from stdlib
import logging, os, ctypes, collections
import stat, io, threading, errno
from timeit import default_timer
from .vendored_refuse.high import FUSE, FuseOSError, Operations, LoggingMixIn

def no_op(self, *args, **kwargs):
    pass  # NOOP

class iterstat(object):
    ik = ['st_atime', 'st_ctime',  'st_gid', 'st_mtime',
          'st_nlink', 'st_uid', 'st_mode', 'st_size']
    def __init__(self, vals):
        self.vals = vals
    def items(self):
        for i,k in enumerate(self.ik):
            yield k, self.vals[i]

def stat_to_iter(st):
    return iterstat( [st.st_atime, st.st_ctime,  st.st_gid, st.st_mtime,
                      st.st_nlink, st.st_uid, st.st_mode, st.st_size] )


class ID11DiskMounter( Operations):

    CALLS = collections.defaultdict( int )
    ELAPS = collections.defaultdict( float )
    GAS = collections.defaultdict( int )

    def __init__(self, root, data):
        """
        root = where in the file system are we going to create this disk?
        data = a source of datafiles in memory: e.g. edf_from_3d
        """
        self.root = os.path.realpath(root)
        self.rwlock = threading.Lock()
        self.data = data
        #
        st = os.lstat(root) # folder stat defaults for creation time etc
        vals = [ getattr(st, key) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mtime',
            'st_nlink', 'st_uid')]
        vals.append(stat.S_IFREG | 0o444) # everyone can read files
        vals.append(self.data.filesize()) # assume all are the same size
        self.st = iterstat( vals )
        # Create a mapping of file descriptors, system files versus our
        # fake files
        # keys in here are the open files
        self.openfds = {0:None, 1:None, 2:None}
        #  int : int    == system files
        #  int : string == our files

    def __call__(self, op, path, *args):
        """ for FUSE """
        self.CALLS[op] += 1
        start = default_timer()
        ret = super(ID11DiskMounter, self).__call__(
            op, self.root + path, *args)
        end = default_timer()
        self.ELAPS[op] += (end-start)
        return ret

    def __del__(self):
        print("Runtime statistics")
        print("Operation   Ncalls   Time")
        for key in self.CALLS.keys():
            print(key,self.CALLS[key],self.ELAPS[key],self.ELAPS[key]/self.CALLS[key])
        print("Getattr calls")
        for key in self.GAS.keys():
            print(key,self.GAS[key])

    def access(self, path, mode):
        if not os.access(path, mode):
            raise FuseOSError(errno.EACCES)

    def open(self, path, *args, **kwds):
        """ Open a file - system pass through or one of ours """
        with self.rwlock: # because we modify openfds
            # new file descriptor is:
            outfd = max(self.openfds.keys()) + 1
            if path.endswith(self.data.extn):
                direc, fname = os.path.split( path )
                if fname in self.data.filenames and not os.path.exists(path):
                    self.openfds[outfd] = fname
                    return outfd
            flags = args[0]
            if hasattr(os, "O_BINARY") and not (args[0] & os.O_TEXT):
                flags |= os.O_BINARY
            newfd = os.open(path, flags, **kwds)
            self.openfds[outfd] = newfd
            return outfd

    def read(self, path, size, offset, outfd):
        """ Read a file, system pass through or one of ours """
        with self.rwlock:
            sysfd = self.openfds[outfd]
            if isinstance( sysfd, int ):
                os.lseek(sysfd, offset, 0)
                return os.read(sysfd, size)
        # free the lock now, this is slow but not vulnerable to writes
        frm = self.data[sysfd]
        if offset > len(frm):
            print("attempt to read past end",path)
        if (size+offset) > len(frm):
            size = len(frm) - offset
        return (ctypes.c_char * size).from_buffer(frm, offset)

    # Pass through method
    mkdir = os.mkdir

    def truncate(self, path, length, fh=None):
        """ Not too sure about this one - clips a file to size ? """
        with self.rwlock:
            # Case of a file descriptor
            if fh is not None and fh in self.openfds:
                return os.ftruncate( self.openfds[fh], length  )
            # otherwise a path
            with open(path, 'r+') as f:
                return f.truncate(length)

    def create(self, path, mode):
        """ Creates a new file -
        the O_BINARY seems to be critical for windows?
        """
        with self.rwlock:
            flags = os.O_RDWR | os.O_CREAT | os.O_TRUNC
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            newfd = os.open(path, flags , mode)
            outfd = max(self.openfds.keys()) + 1
            self.openfds[ outfd ] = newfd
            return outfd

    def flush(self, path, fh):
        """ Probably important for the pass through """
        with self.rwlock:
            if fh in self.openfds:
                sysfd = self.openfds[fh]
                if sysfd in self.data.filenames:
                    return 0
                else:
                    try:
                        return os.fsync(sysfd)
                    except:
                        return 0

    def fsync(self, path, datasync, fh):
        """ Probably important for the pass through """
        with self.rwlock:
            if fh in self.openfds:
                sysfd = self.openfds[fh]
                if isinstance(sysfd, int):
                    if datasync != 0:
                        return os.fdatasync(sysfd)
                    else:
                        return os.fsync(sysfd)
                else:
                    return 0

    def readdir(self, path, fh):
        with self.rwlock:
            p = os.path.realpath(path)
            locals = ['.', '..']
            if p == self.root:
                locals += self.data.filename_list
            return locals +  os.listdir(path)

    def getattr(self, path, fh=None):
        # FIXME the st_gid and st_uid are problematic still
        if fh is not None:
            sysfd = self.openfds[fh]
            if isinstance( sysfd, int ):
                st = os.fstat( sysfd )
                self.GAS['fstat']+=1
                return stat_to_iter( st )
            self.GAS['fake']+=1
            return self.st
        else:
            if path.endswith( self.data.extn ):
                direc, fname = os.path.split( path )
                if fname in self.data.filenames and not os.path.exists(path):
                    self.GAS['fake']+=1
                    return self.st
            st = os.lstat(path)
            self.GAS['lstat']+=1
            return stat_to_iter( st )

    def release(self, path, fh):
        """ Closes a file """
        with self.rwlock:
            if fh in self.openfds:
                if fh < 3:
                    return
                sysfd = self.openfds[fh]
                self.openfds.pop(fh)
                if sysfd not in self.data.filenames:
                    return os.close(sysfd)
                else:
                    #  we do nothing - might be this one is opened to read next
                    pass

    def write(self, path, data, offset, fh):
        with self.rwlock:
            if fh in self.openfds:
                sysfd = self.openfds[fh]
                if isinstance( sysfd, int ):
                    pos = os.lseek(sysfd, offset, 0)
                    return os.write(sysfd, data)
                else:
                    logging.ERROR("You cannot write these! %s %d"%(path, fh))
                    raise FuseOSError(errno.EPERM)


