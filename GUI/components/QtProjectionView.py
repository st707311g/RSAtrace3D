from PyQt5.QtWidgets import QWidget, QGridLayout
from pyqtgraph import  ViewBox, ImageItem, mkColor
from pyqtgraph.widgets.GraphicsLayoutWidget import GraphicsLayoutWidget
from PyQt5.QtCore import pyqtSignal, Qt

from DATA import ID_Object, RSA_Components
import numpy as np

class CoreViewBox(ViewBox):
    pyqtSignal_mouseClickEvent = pyqtSignal(int, object, int, bool)

    def __init__(self, identifier, **kwargs):
        super().__init__(**kwargs)
        self.identifier=identifier

        self.setAspectLocked(True)
        self.invertY()

        self.projection_image = ImageItem()
        self.trace_image = ImageItem()
        self.selected_trace_image = ImageItem()
        self.addItem(self.projection_image)
        self.addItem(self.trace_image)
        self.addItem(self.selected_trace_image)

        self.setBackgroundColor(mkColor('#000000'))

    def clear_all(self):
        self.projection_image.clear()
        self.trace_image.clear()
        self.selected_trace_image.clear()

    def is_empty(self):
        return self.projection_image.image is None

    def mouseClickEvent(self, ev):
        self.pyqtSignal_mouseClickEvent.emit(self.identifier, self.mapToView(ev.pos()), ev.button(), self.projection_image.image is not None)

class MainViewBox(CoreViewBox):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, enableMouse=True)

class SubViewBox(CoreViewBox):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, enableMouse=False)

class CoreViewWidget(GraphicsLayoutWidget):
    def __init__(self, identifier, dimension):
        super().__init__()
        self.identifier = identifier
        self.dimension = dimension

        self.bg_color = mkColor('#000000')
        self.setBackground(self.bg_color)

    def set_projection_image(self, img):
        self.view.projection_image.setImage(img.transpose(1,0))
        self.view.autoRange()

    def set_trace_image(self, img):
        img = None if img is None else img.transpose(1,0,2)
        self.view.trace_image.setImage(img)
        self.setBackground(self.bg_color)

    def set_selected_trace_image(self, img):
        self.view.selected_trace_image.setImage(img.transpose(1,0,2))

    def clear_all(self):
        self.view.clear_all()

    def select_itself(self, flag):
        self.bg_color = mkColor('#444444') if flag else mkColor('#000000')
        self.setBackground(self.bg_color)

class MainViewWidget(CoreViewWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.make_viewbox()

    def make_viewbox(self):
        self.view = MainViewBox(identifier=self.identifier)
        self.addItem(self.view)

class SubViewWidget(CoreViewWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.make_viewbox()

    def make_viewbox(self):
        self.view = SubViewBox(identifier=self.identifier)
        self.addItem(self.view)

class QtProjectionView(QWidget):
    def __init__(self, parent):
        super().__init__(**{'parent':parent})
        self.__parent = parent
        self.layout = QGridLayout()
        self.main_view_widget = MainViewWidget(identifier=-1, dimension=None)
        self.layout.addWidget(self.main_view_widget, 0, 0, 3, 1)

        self.sub_view_widgets = []
        for i, dimension in enumerate([[1,2],[0,2],[0,1]]):
            self.sub_view_widgets.append(SubViewWidget(identifier=i, dimension=dimension))
            self.layout.addWidget(self.sub_view_widgets[i], i, 1)

        self.layout.setColumnStretch(0, 3)
        self.layout.setColumnStretch(1, 1)

        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0,0,4,0)

        self.setLayout(self.layout)

        self.current_view_index = -1
        self.dimensions = ((1,2),(0,2),(0,1))
        self.selected_ID_string = None

        for w in self.all_widgets():
            w.view.pyqtSignal_mouseClickEvent.connect(self.on_mouse_clicked)

    def all_widgets(self):
        return [self.main_view_widget]+self.sub_view_widgets

    def parent(self):
        return self.__parent

    def RSA_components(self) -> RSA_Components:
        return self.parent().RSA_components()

    def GUI_components(self):
        return self.parent().GUI_components()

    def update_selected_items(self):
        self.main_view_widget.select_itself(flag=False)
        for i in range(3):
            self.sub_view_widgets[i].select_itself(flag=self.current_view_index==i)

    def update_main_widget(self):
        if self.current_view_index not in [0,1,2]:
            return

        #// update projection
        view = self.sub_view_widgets[self.current_view_index].view
        img = view.projection_image.image
        if img is not None:
            self.main_view_widget.set_projection_image(img=img.transpose(1,0))

        #// update trace
        img = view.trace_image.image
        if img is not None:
            self.main_view_widget.set_trace_image(img=img.transpose(1,0,2))

        #// update selected_trace
        img = view.selected_trace_image.image
        if img is not None:
            self.main_view_widget.set_selected_trace_image(img=img.transpose(1,0,2))
            

        self.main_view_widget.view.autoRange()

    def on_mouse_clicked(self, identifier, coordinate, button, is_valid):
        if is_valid is False or button != Qt.LeftButton:
            return

        if identifier == -1:
            ID_string_list = []
            distance_list = []
            for ID_string in self.RSA_components().vector.iter_all():
                if not ID_string.is_root():
                    continue
                root_node = self.RSA_components().vector.root_node(ID_string=ID_string)
                distance = self.__get_closest_distance(\
                    ref_coordinate=np.array([int(coordinate.y()), int(coordinate.x())]), \
                    from_polyline=root_node.completed_polyline(), \
                    index=self.current_view_index)
                ID_string_list.append(ID_string)
                distance_list.append(distance)

            if len(ID_string_list) == 0:
                return

            argmin = np.argmin(distance_list)
            ID_string_min = ID_string_list[argmin]
            distance_min = distance_list[argmin]

            if distance_min > 20**2:
                return

            self.GUI_components().treeview.select(ID_string=ID_string_min)

        if identifier in [0,1,2]:
            self.current_view_index = identifier
            self.update_selected_items()
            self.update_main_widget()

    def clear(self):
        self.current_view_index = -1
        self.update_selected_items()
        self.main_view_widget.clear_all()
        for i in range(3):
            self.sub_view_widgets[i].clear_all()

    def set_volume(self, volume):
        if volume is None:
            return

        for i in range(3):
            self.sub_view_widgets[i].set_projection_image(img=volume.max(axis=i))

        self.current_view_index = 0
        self.update_selected_items()
        self.update_main_widget()

        self.volume_shape = volume.shape

    def set_trace(self, projections):
        for i in range(3):
            img = None if len(projections) != 3 else projections[i].volume
            self.sub_view_widgets[i].set_trace_image(img=img)

        self.update_main_widget()

    def __get_closest_distance(self, ref_coordinate, from_polyline, index):
        from_polyline = np.array(from_polyline).T
        np_polyline = np.delete(np.array(from_polyline), index, axis=0)
        distance = ((np_polyline.T-ref_coordinate)**2).sum(axis=1).min()
        return distance

    def on_selected_item_changed(self, ID_string: ID_Object):
        if self.current_view_index not in [0,1,2] or ID_string is None:
            return

        if ID_string.is_base():
            for w in self.all_widgets():
                w.view.selected_trace_image.hide()
            return
        
        for w in self.all_widgets():
            w.view.selected_trace_image.show()

        for w in self.sub_view_widgets:
            RSA_vector = self.RSA_components().vector
            selected_trace = self.RSA_components().trace.create_trace_object(
                RSA_vector=RSA_vector,
                ID_string=ID_string, 
                shape=self.volume_shape,
                dimensions=w.dimension)
            
            if selected_trace is not None:
                w.set_selected_trace_image(img=selected_trace.volume)

        self.update_main_widget()

    def on_spacekey_pressed(self, pressed):
        for w in self.all_widgets():
            if pressed == True:
                w.view.trace_image.hide()
            else:
                w.view.trace_image.show()