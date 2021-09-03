import logging
from typing import Dict, List

import numpy as np
from DATA import ID_Object, RSA_Components, TraceObject
from GUI.components import QtMain
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QPen
from pyqtgraph import (GraphItem, ImageItem, ImageView, IsocurveItem, TextItem,
                       ViewBox, mkBrush, mkPen)


class _ImageViewBox(ViewBox):
    def __init__(self):
        super().__init__()

    def wheelEvent(self, ev):
        if ev.modifiers() & Qt.ControlModifier:
            super().wheelEvent(ev)

class _ImageItem3D(ImageItem):
    def __init__(self):
        super().__init__()

    def getHistogram(self, **kwds):
        return super().getHistogram(bins=64, **kwds)

class QtSliceView(ImageView):
    def __init__(self, parent: QtMain):
        super().__init__(**{'parent':parent, 'view':_ImageViewBox(), 'imageItem':_ImageItem3D()})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__parent=parent
        self.ui.menuBtn.hide()
        self.ui.roiBtn.hide()

        self.trace3D = ImageItem()
        self.view.addItem(self.trace3D)

        self.isocurve = _IsocurveItem(imageview=self)
        self.view.addItem(self.isocurve)
        self.pos_marks = PosMarks(imageview=self)
        self.view.addItem(self.pos_marks)
        
        self.imageItem.wheelEvent = self.on_mouse_wheeled
        self.imageItem.mouseClickEvent = self.on_mouse_clicked
        self.view.mouseClickEvent = self.on_mouse_clicked_view
        self.scene.sigMouseMoved.connect(self.on_mouse_position_changed)

        self.timeLine.sigPositionChanged.connect(self.on_showing_slice_changed)
        self.view.sigRangeChangedManually.connect(self.onRangeChangedManually)
        self.x_range, self.y_range = ([], [])

    def onRangeChangedManually(self, status):
        self.x_range, self.y_range = self.view.viewRange()

    def parent(self):
        return self.__parent

    def RSA_components(self) -> RSA_Components:
        return self.parent().RSA_components()

    def GUI_components(self):
        return self.parent().GUI_components()

    def keyPressEvent(self, ev):
        ev.ignore()

    def keyReleaseEvent(self, ev):
        ev.ignore()

    def on_spacekey_pressed(self, pressed):
        if self.RSA_components().volume.is_empty() or pressed == True:
            self.pos_marks.hide()
            self.trace3D.hide()
        else:
            self.pos_marks.show()
            self.trace3D.show()

    def on_showing_slice_changed(self):
        trace3d = self.RSA_components().trace.trace3D
        if trace3d is not None:
            self.update_trace3D(trace3d=trace3d)
        self.update_statusbar(z=self.currentIndex)
        self.GUI_components().projectionview.on_showing_slice_changed(index=self.currentIndex)

    def update_statusbar(self, **kwargs):
        self.GUI_components().statusbar.update_mouse_position(**kwargs)

    def on_mouse_position_changed(self, position):
        position = self.view.mapToView(position)
        self.update_statusbar(z=self.currentIndex, y=position.y(), x=position.x())

    def on_mouse_clicked_view(self, ev):
        ev.ignore()

    def on_mouse_clicked(self, ev):
        ev.accept()
        if self.RSA_components().volume.is_empty():
            return

        position = [self.currentIndex, int(ev.pos().y()),int(ev.pos().x())]

        self.logger.debug(f'Mouse clicked: (x={position[2]}, y={position[1]}, z={self.currentIndex})')
        
        if ev.button()==Qt.LeftButton:
            self.parent().set_control(locked=True)
            annotations={'coordinate': position}

            if ev.modifiers() & Qt.ControlModifier and ev.modifiers() & Qt.ShiftModifier:
                self.add_base(annotations=annotations)
            elif ev.modifiers() & Qt.ControlModifier:
                self.add_relay(annotations=annotations)
            else:
                self.add_root(annotations=annotations)

            self.GUI_components().treeview.update_all_text()
            self.parent().set_control(locked=False)
            self.parent().show_default_msg_in_statusbar()

    def add_base(self, annotations):
        if self.RSA_components().vector.base_node_count() != 0:
            return

        ID_string = self.RSA_components().vector.append_base(annotations=annotations)
        self.GUI_components().treeview.add_base(ID_string=ID_string)
        self.pos_marks.draw(ID_string=ID_string)

    def add_root(self, annotations):
        selected_ID_string = self.GUI_components().treeview.get_selected_ID_string()
        if selected_ID_string is None:
            return

        base_node = self.RSA_components().vector.base_node(baseID=selected_ID_string.baseID())
        if base_node is None:
            return

        ID_string = base_node.append()
        self.GUI_components().treeview.add_root(ID_string=ID_string)
        self.add_relay(annotations=annotations, root_ID_string=ID_string)

    def add_relay(self, annotations: dict, root_ID_string: ID_Object=None):
        selected_ID_string = root_ID_string or self.GUI_components().treeview.get_selected_ID_string()
        if selected_ID_string is None or selected_ID_string.is_base():
            return

        base_node = self.RSA_components().vector.base_node(baseID=selected_ID_string.baseID())
        if base_node is None:
            return

        baseID, rootID, _ = selected_ID_string.split()
        ID_string = self.RSA_components().vector.append_relay(baseID=baseID, rootID=rootID, annotations=annotations)
        if ID_string is not None:
            self.GUI_components().treeview.add_relay(ID_string=ID_string)

        self.update_trace_graphics()

    def update_trace_graphics(self):
        selected_ID_string = self.GUI_components().treeview.get_selected_ID_string()

        RSA_vector = self.RSA_components().vector
        root_nodes = self.RSA_components().trace.root_ndoes_to_be_updated(RSA_vector=RSA_vector)

        self.logger.debug(f"Number of root node to be updated: {len(root_nodes)}")

        self.parent().set_control(locked=True)
        if len(root_nodes) == 0: #// in the case of no nodes
            self.RSA_components().trace.init_from_volume(self.RSA_components().volume.data)
        elif len(root_nodes) == 1: #// in the case of adding a node
            self.RSA_components().trace.draw_trace(root_node=root_nodes[0])
        else:
            for i, root_node in enumerate(root_nodes):
                self.GUI_components().statusbar.pyqtSignal_update_progressbar.emit(i, len(root_nodes), 'Redrawing trace volume')
                self.RSA_components().trace.draw_trace(root_node=root_node)

        trace3d = self.RSA_components().trace.trace3D
        if trace3d is not None:
            self.update_trace3D(trace3d)

        self.GUI_components().projectionview.set_trace(projections=self.RSA_components().trace.projections)

        self.pos_marks.draw(ID_string=selected_ID_string)
        if selected_ID_string is not None:
            self.isocurve.draw(ID_string=selected_ID_string)
            self.GUI_components().projectionview.on_selected_item_changed(ID_string=selected_ID_string)
        self.parent().set_control(locked=False)
        
    def update_volume(self, volume):
        self.setImage(img=volume, axes={'t': 0, 'x': 2, 'y': 1, 'c': None})

    def clear(self):
        super().clear()
        self.trace3D.clear()
        self.pos_marks.hide()
        self.isocurve.hide()

    def on_mouse_wheeled(self, ev):
        ev.accept()
        if self.parent().is_control_locked() or \
            self.RSA_components().volume.is_empty():
            return

        if ev.modifiers() & Qt.ControlModifier:
            self.view.wheelEvent(ev)
            return

        index = max(self.currentIndex-1,0) if ev.delta()>0 else min(self.currentIndex+1, self.getProcessedImage().shape[0]-1)
        self.setCurrentIndex(index)

    def update_trace3D(self, trace3d: TraceObject):
        trace_slice = trace3d.volume[self.currentIndex].transpose(1,0,2)
        self.trace3D.setImage(trace_slice)

    def move_position(self, ID_string: ID_Object):
        #// ID_string 分類
        target_coordinate = None
        if ID_string.is_relay():
            relay_node = self.RSA_components().vector.relay_node(ID_string=ID_string)
            if relay_node is not None:
                target_coordinate = relay_node['coordinate']
        elif ID_string.is_root():
            root_node = self.RSA_components().vector.root_node(ID_string=ID_string)
            if root_node is not None:
                target_coordinate = root_node.tip_coordinate()
        else:
            base_node = self.RSA_components().vector.base_node(ID_string=ID_string)
            if base_node is not None:
                target_coordinate = base_node['coordinate']

        if target_coordinate is not None:
            self.setCurrentIndex(target_coordinate[0])

            x_range = self.x_range
            y_range = self.y_range
            if len(x_range) != 0:
                x_len = x_range[1]-x_range[0]+1
                y_len = y_range[1]-y_range[0]+1
                x = target_coordinate[2]
                y = target_coordinate[1]
                x_range = [x-x_len/2, x+x_len/2]
                y_range = [y-y_len/2, y+y_len/2]
                self.view.setRange(xRange=x_range, yRange=y_range)

class PosMarks(GraphItem):
    def __init__(self, imageview):
        self.imageview = imageview
        self.dragPoint = None
        self.dragOffset = None
        self.textItems = []
        super().__init__()
        self.scatter.sigClicked.connect(self.clicked)

    def RSA_components(self) -> RSA_Components:
        return self.imageview.RSA_components()

    def GUI_components(self):
        return self.imageview.GUI_components()

    def make_draw_parameter_class(self):
        class DrawParameterClass(object):
            def __init__(self):
                self.__dict = {
                    'size': 10,
                    'pxMode': True, 
                    'antialias': True,
                    'pos': [],
                    'symbol': [],
                    'symbolPen': [],
                    'symbolBrush': [],
                    'text': []
                }

            def to_dict(self):
                return_dict = self.__dict.copy()
                return_dict['pos'] = np.asarray(return_dict['pos'])

                return return_dict

            def is_empty(self):
                return len(self.__dict['pos']) == 0

            def add_node(self, pos: List, symbolPen: QPen, symbolBrush: QBrush, text:str, symbol: str='o'):
                self.__dict['pos'].append(pos)
                self.__dict['symbolPen'].append(symbolPen)
                self.__dict['symbolBrush'].append(symbolBrush)
                self.__dict['text'].append(text)
                self.__dict['symbol'].append(symbol)

        return DrawParameterClass()

    def draw(self, ID_string: ID_Object=None):
        if ID_string is None or self.RSA_components().volume.is_empty():
            self.data = {}
            self.setTexts([])
            self.updateGraph()
            return

        draw_parameters = self.make_draw_parameter_class()
        
        def add_marks(ID_string, pen: QPen, brush: QBrush):
            node = self.RSA_components().vector[ID_string]
            if node is not None:
                clicked_coordinate = node['coordinate']
                if clicked_coordinate is None :
                    return

                draw_parameters.add_node(
                    pos=[clicked_coordinate[2]+0.5, clicked_coordinate[1]+0.5],
                    symbolPen=pen, 
                    symbolBrush=brush, 
                    text=ID_string
                    )

        add_marks(ID_string.to_base(), mkPen((255,0,0)), mkBrush((255, 0, 0, 64)))

        if not ID_string.is_base():
            root_node = self.RSA_components().vector.root_node(ID_string=ID_string)
            if root_node is not None:
                relay_ID_strings = root_node.child_ID_strings()
                selected_ID_string = self.GUI_components().treeview.get_selected_ID_string()

                
                for ID_string in relay_ID_strings:
                    if selected_ID_string not in relay_ID_strings or ID_string == selected_ID_string:
                        add_marks(ID_string,mkPen((0,255,0)), mkBrush((0, 255, 0, 64)))
                    else:
                        add_marks(ID_string, mkPen((0,128,0)), mkBrush((0, 255, 0, 32)))

        if draw_parameters.is_empty():
            return

        self.setData(**draw_parameters.to_dict())
        self.show()
        
    def setData(self, **kwds):
        self.text = kwds.pop('text', [])
        self.data = kwds
        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)
        self.setTexts(self.text)
        self.updateGraph()
        
    def setTexts(self, text):
        for i in self.textItems:
            i.scene().removeItem(i)
        self.textItems = []
        self.ID_strings=text.copy()
        for t in text:
            item = TextItem(f'{t.split()[2]:02}', color=(100,100,200))
            self.textItems.append(item)
            item.setParentItem(self)
        
    def updateGraph(self):
        GraphItem.setData(self, **self.data)
        for i,item in enumerate(self.textItems):
            item.setPos(*self.data['pos'][i])
        
    def clicked(self, scatter_plot_item, spot_items):
        clicked_ID_string = self.ID_strings[spot_items[0].data()[0]]
        if clicked_ID_string.is_base():
            clicked_ID_string = self.ID_strings[-1]
            self.GUI_components().treeview.select(ID_string=clicked_ID_string.to_root())
        else:
            self.GUI_components().treeview.select(ID_string=clicked_ID_string)

class _IsocurveItem(IsocurveItem):
    def __init__(self, imageview: QtSliceView):
        super().__init__()
        self.imageview = imageview
        self.setLevel(255)
        self.setPen(mkPen([255,255,255,128]))

    def RSA_components(self) -> RSA_Components:
        return self.imageview.RSA_components()

    def GUI_components(self):
        return self.imageview.RSA_components()

    def draw(self, ID_string: ID_Object):
        if ID_string is None:
            self.setData(None)
            return

        self.show()

        RSA_vector = self.RSA_components().vector

        if ID_string.is_base():
            self.setData(None)
            return
            
        trace_obj = self.RSA_components().trace.create_trace_object(
            RSA_vector=RSA_vector,
            ID_string=ID_string, 
            shape=RSA_vector.annotations.volume_shape(), 
            dimensions=[1,2])

        if trace_obj is not None:
            img = trace_obj.volume[:,:,1]

            if img is None:
                self.setData(None)
            else:
                self.setData(img.transpose(1,0))
