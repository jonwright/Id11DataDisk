
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

Years ago there was a suggestion to mount a virtual disk and show 
the hdf5 data is if it was a legacy format. The author (JW) thinks 
it was first mentioned to him at this meeting:

Friday, 17 August 2007, 12:30 - 17:00
Diamond Light Source, Didcot, Chilton
http://www.medsbio.org/nmeetings/BSR_2007_imgCIF_Workshop.html

A few quick google searches have not yet uncovered a professional 
quality implemention for doing this yet. It appears to be a very 
difficult problem and there a very good reasons NOT to do this. 


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

On Linux you hopefully have FUSE already, if not try something
like `apg-get install libfuse2`.

Decide where you want to mount the virtual disk and which folder
you want to use for the passthrough filesystem.

## Example

1) hdf5 file : c:\temp\sucrrose_sx_1.h5
2) scan to process : 3.1/measurement/eiger
3) folder to work in c:\temp\demo
    `mkdir c:\temp\deco`
4) python main.py c:\temp\sucrrose_sx_1.h5 3.1/measurement/eiger c:\temp\demo --format=flat
5) Open crysalis
6) import/export, import unknown, fill all the options, click ok
7)  ... be very patient !
8) control-c to exit the python process

## python fuse wrappers

There seem to be various FUSE wrappers for python with differences
between FUSE2 and FUSE3 and various forks. None of them seem
to be accepting all the pull requests for windows. This means we vendored 
one for now in the hope we will see pip version soon. Perhaps there is a
working version that we did not find yet. A blocking problem is:

https://github.com/pleiszenburg/refuse/pull/29

We did this:

`git clone --single-branch --branch example https://github.com/clach04/refuse/ clach04_refuse_example`
`mkdir vendored_refuse`
`cp clach04_refuse_example/src/refuse/*.py vendored_refuse/`
`cp clach04_refuse_example/*.md vendored_refuse/`
`cp clach04_refuse_example/LICENSE vendored_refuse/`

## Things that have not been done yet

[ ] Make a little gui to select the hdf5 file and group to open and decide where to mount it.

[ ] Setting up CI

[ ] Testing with FUSE3 versus FUSE2

[ ] A native windows setup might have advantages over FUSE? https://github.com/Scille/winfspy

[ ] Test out some other windows FUSE thing like dokan https://dokan-dev.github.io/



