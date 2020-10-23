

from Id11DataDisk import id11diskmounter, files_from_3d
import argparse, logging, sys, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    parser.add_argument('h5file')
    parser.add_argument('scan')
    parser.add_argument("--format", dest='format', default = 'edf')
    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR)
#    logging.basicConfig(level=logging.DEBUG)

    if args.format == 'edf':
        data = files_from_3d.EdfFrom3d( args.h5file, args.scan )
    elif args.format == 'flat':
        data = files_from_3d.FlatFrom3d( args.h5file, args.scan )
    else:
        print("Not recognised format ",args.format)
        sys.exit()

    root = args.mount + "_real"
    # root is a real existing disk folder
    try:
        # we do it this way around so that when we are finished
        # the path used by the legacy software still sees args.mount
        # when it goes back to being the real folder.
        print("Renaming your folder from:", args.mount, "to:", root)
        os.rename( args.mount, root )
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

if __name__ == '__main__':
    main()

