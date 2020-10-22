#!/usr/bin/env python3

# This code is mostly copied from:
# https://github.com/clach04/refuse/blob/example/src/examples/loopback.py
#
# These imports are from stdlib
import logging, os
import stat, io, threading, errno

from .vendored_refuse.high import FUSE, FuseOSError, Operations, LoggingMixIn

def no_op(self, *args, **kwargs):
    pass  # NOOP

class ID11DiskMounter( LoggingMixIn, Operations):

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
        self.st = dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mtime',
            'st_nlink', 'st_uid'))
        self.st['st_mode'] = stat.S_IFREG | 0o444 # everyone can read these files
        self.st['st_size'] = self.data.filesize()   # assume all are the same size
        #
        # Create a mapping of file descriptors, system files versus our fake files
        # keys in here are the open files
        self.openfds = {0:None, 1:None, 2:None}

    def __call__(self, op, path, *args):
        """ for FUSE """
        return super(ID11DiskMounter, self).__call__(op, self.root + path, *args)

    def access(self, path, mode):
        if not os.access(path, mode):
            raise FuseOSError(errno.EACCES)

    def open(self, path, *args, **kwds):
        """ Open a file - system pass through or one of ours """
        with self.rwlock:
            direc, fname = os.path.split( path )
            # new file descriptor is:
            outfd = max(self.openfds.keys()) + 1
            if fname in self.data.filenames and not os.path.exists(path):
                self.openfds[outfd] = fname
            else:
                if args[0] & os.O_TEXT:
                    logging.WARNING("Opening as text")
                    newfd = os.open(path, args[0], **kwds)
                else:
                    newfd = os.open(path, os.O_BINARY | args[0], **kwds )
                self.openfds[outfd] = newfd
            return outfd

    def read(self, path, size, offset, outfd):
        """ Read a file, system pass through or one of ours """
        with self.rwlock:
            if outfd in self.openfds: # file is open
                sysfd = self.openfds[outfd]
                if sysfd not in self.data.filenames:
                    os.lseek(sysfd, offset, 0)
                    myret = os.read(sysfd, size)
                else:
                    frm = self.data[sysfd]
                    frm.seek( offset, 0 )
                    myret = frm.read( size )
            else:
                logging.ERROR("Read on a closed file %d %s"%(outfd, str(self.openfds)))
                myret = b""
            return myret

    # Pass through 
    mkdir = os.mkdir

    def truncate(self, path, length, fh=None):
        """ Not too sure about this one - clips a file to size ? """
        with self.rwlock:
            # Case of a file descriptor
            if fh is not None and fh in self.openfds:
                return os.ftruncate( self.openfds[fh], length  )
            # otherwise a path
            with open(path, 'r+') as f:
                f.truncate(length)

    def create(self, path, mode):
        """ Creates a new file - the O_BINARY seems to be critical for windows? """
        with self.rwlock:
            newfd = os.open(path, os.O_BINARY | os.O_RDWR | os.O_CREAT | os.O_TRUNC , mode)
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
                if sysfd in self.data.filenames:
                    return 0
                else:
                    if datasync != 0:
                        return os.fdatasync(sysfd)
                    else:
                        return os.fsync(sysfd)

    def readdir(self, path, fh):
        with self.rwlock:
            p = os.path.realpath(path)
            locals = ['.', '..']
            if p == self.root:
                locals += self.data.filenames
            return locals +  os.listdir(path)

    def getattr(self, path, fh=None):
        # FIXME the st_gid and st_uid are problematic still
        direc, fname = os.path.split( path )
        if fname in self.data.filenames and not os.path.exists(path):
            std = self.st
        else:
            st = os.lstat(path)
            std = dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
            'st_nlink', 'st_size', 'st_uid'))
        return std

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
                if sysfd in self.data.filenames:
                    logging.ERROR("You cannot write these! %s %d"%(path, fh))
                    raise FuseOSError(errno.EPERM)
                pos = os.lseek(sysfd, offset, 0)
                return os.write(sysfd, data)


