
from Id11DataDisk.main import main
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    parser.add_argument('h5file')
    parser.add_argument('scan')
    parser.add_argument("--format", dest='format', default = 'edf')
    args = parser.parse_args()
    main(args)