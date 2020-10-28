
from pywinauto.application import Application
import time
def run_crysalis(
    headerbytes = 256,
    ny = 2162,
    nx = 2068,
    y0 = 1170.,
    x0 = 1023.,
    outname = "data",
    firstframe = r"c:\temp\flat\data0001.raw",
    lastframe =  r"c:\temp\flat\data0010.raw",
    run = 1,
    wvln= 0.308,
    distance = 117.23,
    startang = -180,
    stepang = 0.25,
    exptime = 0.2,
    reverse = False,
    ):
    """ This is going to be nasty to maintain """
    assert stepang > 0, "step must be greater than 0, set reverse true and try again"
    app = Application().start( "C:\Xcalibur\CrysalisPro171.40_64.67a\pro.exe -offline" )
    app.window(title_re='Open CrysAlis experiment.*')['Experiment selectionListView'].send_keystrokes("{END}")
    time.sleep(1)
    app.window(title_re="Open CrysAlis experiment.*")['Open selected'].click()
    time.sleep(1)
    app.top_window().type_keys('{F5}') # opens command window
    time.sleep(1)
    app.window( title_re = "Shell command window*.").type_keys('DC{SPACE}RIT{ENTER}\n')

    dcrit =  app.window( title_re = "Esperanto importer.*") # .wrapper_object()
    # First the modal selections :
    dcrit['Generic uncompressed imageRadioButton'].check_by_click_input() ; time.sleep(.1)
    dcrit['Pixel typeComboBox'].select("LONG (4 BYTES)") ; time.sleep(.1)
    dcrit['Frame digitsComboBox'].select("4") ; time.sleep(.1)
    dcrit['0RadioButton'].click()       ; time.sleep(.1)   # no rotation
    dcrit['MirrorCheckBox'].uncheck()    ; time.sleep(.1)   # no mirror
    dcrit['Use Auto-gap detection with value -1CheckBox'].check_by_click_input() ; time.sleep(.1)
    dcrit['Synchrotron: 0.7107CheckBox'].check_by_click_input() ; time.sleep(.1)
    time.sleep(0.5) ; time.sleep(.1)
    dcrit['Edit lambdaButton'].click() ; time.sleep(.1)
    app["Editing X-ray wavelength"]["Edit"].set_edit_text("%.6f"%(wvln)) ; time.sleep(.1)
    app["Editing X-ray wavelength"]["Ok"].click() ; time.sleep(.1)

    dcrit['Skip header bytes:Edit'].set_text(str(headerbytes)) ; time.sleep(.1)
    dcrit['y=Edit'].set_text(str(ny)) ; time.sleep(.1)
    dcrit['x=Edit'].set_text(str(nx)) ; time.sleep(.1)

    dcrit['Browse'].click() ; time.sleep(.5)
    app['Locate first image']['File nameEdit'].set_edit_text( firstframe ) ; time.sleep(.1)
    app['Locate first image']['File nameEdit'].send_keystrokes("{ENTER}")
    dcrit['Browse2'].click() ; time.sleep(.5)
    app['Locate last image']['File nameEdit'].set_edit_text( lastframe ) ; time.sleep(.1)
    app['Locate last image']['File nameEdit'].send_keystrokes("{ENTER}")

    dcrit['Images base name:Edit'].set_edit_text( outname ) ; time.sleep(.1)
    dcrit['Run #Edit'].set_edit_text(str(run)) ; time.sleep(.1)
    dcrit['Pixel size [mm]:Edit'].set_edit_text("0.075") ; time.sleep(.1)
    dcrit['x0=Edit'].set_edit_text("%.3f"%(x0)) ; time.sleep(.1)
    dcrit['y0=Edit'].set_edit_text("%.3f"%(y0)) ; time.sleep(.1)
    ### OVERFLOW HANDLING ?
    dcrit['>CheckBox'].uncheck_by_click_input() ; time.sleep(.1)
    # dcrit['>Edit'].set_edit_text("10000000")
    dcrit['Button10'].click() ; time.sleep(.1) ## check ...
    app["Editing instrument parameters"]['Edit'].set_edit_text( "%.3f"%(distance) ) ; time.sleep(.1)
    app["Editing instrument parameters"]['Ok'].click() ; time.sleep(.1)
    # Alpha, Beta : | ['Edit10', 'Button8', 'EditButton', 'EditButton0', 'EditButton1']
    # Omega0,Theta0, Kappa0 [deg]: | ['Edit11', 'Button9', 'EditButton2']
    # Beam b2: | ['Edit13', 'Button11', 'EditButton4']
    # Gain: ['Edit14', 'Button12', 'EditButton5']
    dcrit['Thickn.: 0.3200mmCheckBox'].check_by_click_input() ; time.sleep(.1)
    dcrit['Edit thkButton'].click() ; time.sleep(.1)
    app["Editing instrument parameters"]['Edit'].set_edit_text( "0.75" ) ; time.sleep(.1)  ## ID11 CdTe
    app["Editing instrument parameters"]['Ok'].click() ; time.sleep(.1)
    #   | CheckBox - ''    (L227, T804, R242, B820)
    #   | ['CheckBox5', 'Gain:CheckBox']
    #   | child_window(class_name="Button")
    # 'PhiRadioButton'
    dcrit['OmegaRadioButton'].check_by_click_input() ; time.sleep(.1)
    #   | ['Edit16', 'Phi=Edit']
    # scan information:
    dcrit['Button14'].click() ; time.sleep(.1)
    app['Editing scan information']['Edit'].set_edit_text( "%.4f %.4f %.4f"%(startang, stepang, exptime)) ; time.sleep(.1)
    app['Editing scan information']['Ok'].click() ; time.sleep(.1)
    #  'Theta=Edit'
    #  'Kappa=Edit'
    if reverse:
        dcrit['Use frames in inverse order 1=last, 2=last-1...CheckBox'].check_by_click_input() ; time.sleep(.1)
    else:
        dcrit['Use frames in inverse order 1=last, 2=last-1...CheckBox'].uncheck_by_click_input() ; time.sleep(.1)
    #    | ['Scan scale err', 'CheckBox7', 'Scan scale errCheckBox']
    #    | Button - 'Edit'    (L680, T880, R731, B901)
#    dcrit['OKButton'].click() ; time.sleep(.1)



if __name__=="__main__":
    run_crysalis()
