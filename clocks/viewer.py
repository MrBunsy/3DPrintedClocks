import io

from OCP.V3d import V3d_Viewer
from OCP.Aspect import Aspect_DisplayConnection, Aspect_TypeOfTriedronPosition
from OCP.OpenGl import OpenGl_GraphicDriver, OpenGl_Caps
from OCP.AIS import AIS_InteractiveContext, AIS_DisplayMode
from OCP.Quantity import Quantity_Color
from OCP.AIS import AIS_Shaded

from .cq_utils import make_AIS


class ViewGenerator:
    '''
    Pinching stuff from widgets/occt_widget.py and widgets/viewer.py from cq-editor, I just want the screenshot ability, trying to unpick what's needed for QT and what's needed for OCT

    also http://analysissitus.org/forum/index.php?threads/how-to-dump-a-picture-png-or-jpg-without-vizualizing-the-situation-first.72/#post-522

    doesn't work yet
    '''

    def __init__(self):
        capabilities = OpenGl_Caps()
        #"don't waste the time waiting for VSync when window is not displayed on the screen"
        capabilities.buffersNoSwap = True
        self.display_connection = Aspect_DisplayConnection()
        self.graphics_driver = OpenGl_GraphicDriver(self.display_connection)
        self.graphics_driver.ChangeOptions().buffersNoSwap = True
        self.viewer = V3d_Viewer(self.graphics_driver)
        self.view = self.viewer.CreateView()
        # self.view.SetViewOn(self.viewer)
        #"// Render immediate structures into back buffer rather than front."
        # self.view.SetImmediateModeDrawToFront(False)

        self.context = AIS_InteractiveContext(self.viewer)
        self.context.SetDisplayMode(AIS_Shaded, True)
        # self.context.Set
        # Trihedorn, lights, etc
        self.prepare_display()

    def prepare_display(self):
        view = self.view

        params = view.ChangeRenderingParams()
        params.NbMsaaSamples = 8
        params.IsAntialiasingEnabled = True

        view.TriedronDisplay(
            Aspect_TypeOfTriedronPosition.Aspect_TOTP_RIGHT_LOWER,
            Quantity_Color(), 0.1)

        viewer = self.viewer

        viewer.SetDefaultLights()
        viewer.SetLightOn()

        ctx = self.context

        ctx.SetDisplayMode(AIS_DisplayMode.AIS_Shaded, True)
        ctx.DefaultDrawer().SetFaceBoundaryDraw(True)

    def display(self, obj,options={}):

        context = self.context

        ais,shape_display = make_AIS(obj, options)
        print("adding shape")
        context.Display(ais, True)

        self.fit()
        self.view.Redraw()


    def fit(self):

        self.view.FitAll()

    def save_screenshot(self, fname):
        print("Saving screenshot to ", fname)
        self.view.Redraw()
        if fname != '':
            self.view.Dump(fname)
            # with open(fname+".json", 'wb') as file:
            #     f = io.BytesIO()
            #     self.view.DumpJson(f)
            #     file.write(f.getbuffer())
