
# ID11DataDisk

Beamline ID11 at the ESRF has started saving data in hdf5 format.
Various software packages were not ready for the new files yet.

This package is a proof-of-concept test for making hdf5 data
readable to legacy or closed source applications. It might crash
your computer, cause data loss, etc. Use at your own risk, no
warranty is implied. It is written python and it is doing on the
fly decompression while at the same time pretending to be a
filesystem. It will be slow even without serving files to your
antivirus software.

Why bother? A typical short scan is less than 3GB in the new hdf5
format versus 24GB as uncompressed files. When debugging you can
re-write thousands of fake file headers by restarting the file server
and without needing the 24GB of disk writes.

A few quick google searches have not yet uncovered a professional
quality implemention for doing this yet. This was written using a
trial and error approach, so you should expect to find bugs. It
appears to be a very difficult problem and there are very good
reasons NOT to do this. Reading the hdf5 files would be better.

## What does it do ?

It turns a real folder into a faked folder which has extra files inside.

- you select an existing folder on your disk
- this is renamed to folder_real
- it mounts a FUSE folder that is the union of folder_real and the hdf5 data
- the hdf5 data are supplied as read only in the format you choose
- you can create and write files in the FUSE folder and they show up in folder_real
- it exits when you do ctrl-c in the terminal
- folder_real is now renamed back to folder

The reason it does this is to allow some windows software to
write paths into binary files. It might be equivalent to dumping
the files into a folder and deleting them afterwards.

## Usage

Locate the hdf5 file and data block that you want to present
as legacy files. Something like `silx view` or `pymca` are
good for this.

Install a python3 environment virtualenv or miniconda thing and
grab the package to read hdf5. To serve edfs we are using fabio
(and you might want cryio as well).

`pip install hdf5plugin fabio`

On windows download and install winfsp from here:
http://www.secfs.net/winfsp/rel/
You only need to install the core component.

On Linux you probably have FUSE already, if not try something
like

`apg-get install libfuse2`.

Decide where you want to mount the virtual disk and which folder
you want to use for the passthrough filesystem.

## Example

0) run `git clone https://github.com/jonwright/Id11DataDisk`
1) find a hdf5 file : `c:\temp\sucrose_sx_1.h5`
2) decide on a scan to process : `3.1/measurement/eiger`
3) make folder to save work in : `mkdir c:\temp\demo`
4) run this `python main.py c:\temp\sucrose_sx_1.h5 3.1/measurement/eiger c:\temp\demo --format=flat`
5) Open crysalis ( fit2d / whatever and do your magic )
6) Import as flat binary. Get all the options right. Click ok.
7)  ... be very patient !
8) Exit any software that has these files open
10) control-c to exit the python process

Results from your processing should now be found in `c:\temp\demo`

## Which python fuse wrappers?

There seem to be various FUSE wrappers for python with differences
between FUSE2 and FUSE3 and various forks. None of them seem
to be accepting all the pull requests for windows. This means we vendored
one for now in the hope we will see pip version soon. Perhaps there is a
working version that we did not find yet. A blocking problem is:

https://github.com/pleiszenburg/refuse/pull/29

We did this:

```
git clone --single-branch --branch example https://github.com/clach04/refuse/ clach04_refuse_example
mkdir vendored_refuse
cp clach04_refuse_example/src/refuse/*.py vendored_refuse/
cp clach04_refuse_example/*.md vendored_refuse/
cp clach04_refuse_example/LICENSE vendored_refuse/
```

... and then put an edit on the logging to see if it speeds anything up.

## History

Years ago there was a suggestion to mount a virtual disk and show
the hdf5 data is if it was a legacy format. The author (JW) thinks
it was first mentioned to him at this meeting:

http://www.medsbio.org/nmeetings/BSR_2007_imgCIF_Workshop.html
Diamond Light Source, Didcot, Chilton. Friday, 17 August 2007, 12:30 - 17:00

## Credits

This was built using the loopback example from @clach04 and
it runs on windows due to the winfsp driver from @billziss-gh,
both of whom are on github. Reading the hdf5 files relies on the
very convenient hdf5plugin and the file conversion to edf is
using fabio.
