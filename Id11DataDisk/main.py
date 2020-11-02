

from . import id11diskmounter, files_from_3d, id11esperanto, LRU_CACHE_SIZE
import argparse, logging, sys, os

def main(args):

    for k,v in vars(args).items():
        print(k,':',v)

    if args.dump:
        LRU_CACHE_SIZE=1

    if args.format == 'edf':
        data = files_from_3d.EdfFrom3d( args.h5file, args.scan, **vars(args) )
    elif args.format == 'flat':
        data = files_from_3d.FlatFrom3d( args.h5file, args.scan, **vars(args) )
    elif args.format == 'esperanto':
        data = id11esperanto.EsperantoFrom3d( args.h5file, args.scan, **vars(args) )
    else:
        print("Not recognised format ",args.format)
        sys.exit()

    if args.dump:
        if not os.path.exists( args.mount ):
            os.mkdir( args.mount )
        print("Dumping files into", args.mount)
        for filename in data.filename_list:
            outname = os.path.join( args.mount, filename)
            print( outname )
            with open( outname, "wb" ) as fout:
                fout.write( data[filename] )
        sys.exit(0)


    root = args.mount + "_real"
    # root is a real existing disk folder
    try:
        # we do it this way around so that when we are finished
        # the path used by the legacy software still sees args.mount
        # when it goes back to being the real folder.
        print("Renaming your folder from:", args.mount, "to:", root)
        if os.path.exists( args.mount ):
            os.rename( args.mount, root )
        else:
            if not os.path.exists( root ):
                os.mkdir( root )
    except:
        print("Failed!! to rename from:", args.mount, "to:", root, 'exiting')
        raise
        sys.exit()
    try:
        # Put any other FUSE options here:
        kwds = { 'foreground' : True, }
        if os.name == 'nt':
            assert not os.path.exists(args.mount), args.mount+" already exists?"
            kwds['allow_other'] = True   # on windows everyone is root
            kwds['uid'] = -1             # really, everyone
        else:
            # windows does not want the mount point to exist
            # linux does want it to exist already
            os.mkdir( args.mount )
        disk = id11diskmounter.ID11DiskMounter( root, data )
        fuse = id11diskmounter.FUSE( disk, args.mount, **kwds )
    except KeyboardInterrupt:
        print("Quitting")
    finally:
        # put it back
        print("Renaming your folder back:", root, "to:", args.mount)
        os.rename( root, args.mount )
        # close h5 and free
        del disk

def makeArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    parser.add_argument('h5file')
    parser.add_argument('scan')
    parser.add_argument("--stem",dest="stem", default='data')
    parser.add_argument("--format", dest='format', default = 'edf')
    parser.add_argument("--startangle", dest='startangle', default = 0.0)
    parser.add_argument("--stepangle", dest='stepangle', default = 0.25)
    parser.add_argument("--expotime", dest='expotime', default=1.0)
    parser.add_argument("--wavelength", dest='wavelength', default=0.308)
    parser.add_argument("--x0", dest='x0', default=1024.)
    parser.add_argument("--y0", dest='y0', default=1024.)
    parser.add_argument("--distance", dest='distance', default=140.)
    parser.add_argument("--run", dest='run', default = 1)
    parser.add_argument("--dump", dest='dump', default=False, action='store_true')
    return parser

if __name__ == '__main__':
    parser = makeArgs()
    args = parser.parse_args()
    main(args)

