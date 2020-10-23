
import sys, os, signal
os.environ['USE_HFD5_FILE_LOCKING'] = 'FALSE'

import tkinter as Tk
from tkinter.ttk import Treeview
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.simpledialog import Dialog

import hdf5plugin, h5py
import threading
from .main import main

def get_h5( root ):
    h5name = askopenfilename( title="HDF5 File", parent=root, initialdir = os.getcwd() )
    return h5name

class askdataset( Dialog ):
    def __init__(self, parent, h5name, title=None):
        self.h5name = h5name
        Dialog.__init__(self, parent, title=title)

    def body(self, parent):
        Tk.Label(parent, text="HDF5 File: "+self.h5name).pack()
        self.tree = Treeview( parent, selectmode = "browse",
                              columns = ("path",'title',) )
        root = self.tree.insert("","end",text="/", values=('/',"",), open=True)
        self.additems( root )
        self.tree.pack(fill=Tk.BOTH, expand=1)
        self.tree.bind('<<TreeviewOpen>>', self.update_tree)
        self.tree.bind('<<TreeviewSelect>>', self.setresult)

    def additems( self, node ):
        gid = self.tree.set( node )['path']
        self.tree.delete( *self.tree.get_children(node) )
        with h5py.File( self.h5name, "r" ) as h5o:
            if gid == "/":
                grp = h5o
            else:
                grp = h5o[gid]
            if isinstance( grp, h5py.Dataset ):
                return
            for idx, item in enumerate(list(grp)):
                thing = grp[item]
                if isinstance(thing, h5py.Group):
                    if 'title' in grp[item]:
                        title = grp[item]['title'][()]
                    else:
                        title = ""
                elif isinstance(thing, h5py.Dataset):
                    title = str(thing.shape)
                else:
                    title = str(type(thing))
                if gid != "/":
                    fullpath = gid+"/"+item
                else:
                    fullpath = item
                oid = self.tree.insert(node, idx, text=item, values=(
                    fullpath, title,))
                if isinstance(thing, h5py.Group):
                    self.tree.insert( oid, "end" ) # dummy entry

    def update_tree( self, event ):
        self.tree = event.widget
        self.additems( self.tree.focus() )

    def setresult(self, event):
        self.result = self.tree.set( self.tree.focus() )['path']


def getdataset(root, h5name):
    d = askdataset( root, h5name )
    return d.result

def app():
    root = Tk.Tk()
    h5name = None
    if len(sys.argv) > 1 and os.path.exists( sys.argv[1] ):
        h5name = sys.argv[1]
    else:
        h5name = get_h5( root )
    if not os.path.exists(h5name):
        print(h5name,"not found")
        sys.exit()
    Tk.Label(text="HDF: "+h5name).pack()
    if len(sys.argv) > 2:
        dataset = sys.argv[2]
    else:
        dataset = getdataset( root, h5name )
    with h5py.File( h5name, "r" ) as h:
        d = h[dataset]
        assert len(d.shape) == 3, dataset+" in "+h5name+" is not 3d"
    Tk.Label(text="Dataset: "+dataset).pack()
    if len(sys.argv) > 3:
        folder = sys.argv[3]
    else:
        folder = askdirectory( title="Folder", parent=root, initialdir = os.getcwd() )
    assert os.path.exists(folder)
    Tk.Label(text="Target Folder: "+ folder).pack()

    Tk.Label(text="CLOSE ME TO UNMOUNT THE DISK!").pack()

    class myargs:
        pass
    args = myargs()
    args.mount = folder
    args.scan = dataset
    args.h5file = h5name
    args.format = 'flat'

    thd = threading.Thread( target = main,  args = (args, ) )
    thd.start()
    root.mainloop()
    # Tell fuse to stop --- hacky
    # see:    https://github.com/fusepy/fusepy/issues/116
    os.kill(os.getpid(), signal.CTRL_BREAK_EVENT)
    thd.join()

