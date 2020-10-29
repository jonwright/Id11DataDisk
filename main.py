
from Id11DataDisk.main import main, makeArgs

if __name__ == '__main__':
    parser = makeArgs()
    args = parser.parse_args()
    main(args)
