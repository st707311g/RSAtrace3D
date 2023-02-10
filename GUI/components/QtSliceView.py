from __future__ import annotations

import logging
import time
from typing import List

import numpy as np
import polars as pl
from DATA.RSA import RSA_Components
from DATA.RSA.components.rinfo import ID_Object
from GUI.components import QtMain
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QMouseEvent, QPen
from PyQt5.QtWidgets import QGraphicsSceneWheelEvent
from pyqtgraph import (
    GraphItem,
    ImageItem,
    ImageView,
    IsocurveItem,
    Point,
    TextItem,
    ViewBox,
    mkBrush,
    mkPen,
)

try:
    from pyqtgraph import fn
except ImportError:
    from pyqtgraph import functions as fn


class _ImageViewBox(ViewBox):
    def __init__(self, parent: QtSliceView):
        super().__init__()
        self.sliceview = parent

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent, axis=None):
        if not (ev.modifiers() & Qt.ControlModifier):
            ev.accept()
            self.sliceview.on_mouse_wheeled(ev)
            return

        if axis in (0, 1):
            mask = [False, False]
            mask[axis] = self.state["mouseEnabled"][axis]
        else:
            mask = self.state["mouseEnabled"][:]
        s = 1.02 ** (
            ev.delta() * self.state["wheelScaleFactor"]
        )  # actual scaling factor
        s = [(None if m is False else s) for m in mask]
        center = Point(
            fn.invertQTransform(self.childGroup.transform()).map(ev.scenePos())
        )

        self._resetTarget()
        self.scaleBy(s, center)
        ev.accept()
        self.sigRangeChangedManually.emit(mask)


class QtSliceView(ImageView):
    def __init__(self, parent: QtMain):
        iv = _ImageViewBox(parent=self)
        super().__init__(
            **{
                "parent": parent,
                "view": iv,
            }
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__parent = parent
        self.ui.menuBtn.hide()
        self.ui.roiBtn.hide()

        self.slice_layer_item = ImageItem()
        self.slice_layer_item.setLevels((0, 255))
        self.view.addItem(self.slice_layer_item)

        self.isocurve = _IsocurveItem()
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
        self.prev_click_time = -1

    def onRangeChangedManually(self, status):
        self.x_range, self.y_range = self.view.viewRange()

    @property
    def main_window(self):
        return self.__parent

    def RSA_components(self):
        return self.main_window.RSA_components()

    def GUI_components(self):
        return self.main_window.GUI_components()

    @property
    def treeview(self):
        return self.GUI_components().treeview

    @property
    def projectionview(self):
        return self.GUI_components().projectionview

    def keyPressEvent(self, ev):
        ev.ignore()

    def keyReleaseEvent(self, ev):
        ev.ignore()

    def on_spacekey_pressed(self, pressed):
        if self.RSA_components().volume.is_empty() or pressed is True:
            self.pos_marks.hide()
            self.slice_layer_item.hide()
        else:
            self.pos_marks.show()
            self.slice_layer_item.show()

    def on_showing_slice_changed(self):
        self.update_slice_layer()
        self.update_statusbar(z=self.currentIndex)
        self.projectionview.on_showing_slice_changed(index=self.currentIndex)

    def update_statusbar(self, **kwargs):
        self.GUI_components().statusbar.update_mouse_position(**kwargs)

    def on_mouse_position_changed(self, position):
        position = self.view.mapToView(position)
        self.update_statusbar(
            z=self.currentIndex, y=position.y(), x=position.x()
        )

    def on_mouse_clicked_view(self, ev: QMouseEvent):
        ev.ignore()

    def on_mouse_clicked(self, ev: QMouseEvent):
        ev.accept()
        if self.RSA_components().volume.is_empty():
            return

        position = [self.currentIndex, int(ev.pos().y()), int(ev.pos().x())]

        self.logger.debug(
            f"Mouse clicked: (x={position[2]}, y={position[1]}, z={self.currentIndex})"
        )

        if ev.button() == Qt.LeftButton:
            annotations = {"coordinate": position}

            if ev.modifiers() & Qt.ControlModifier:
                # // add base node
                if ev.modifiers() & Qt.ShiftModifier:
                    self.main_window.set_control(locked=True)
                    self.add_base(annotations=annotations)
                    self.treeview.update_all_text()
                    self.main_window.set_control(locked=False)
                    self.main_window.show_default_msg_in_statusbar()
                # // add relay node
                else:
                    self.main_window.set_control(locked=True)
                    self.add_relay(annotations=annotations)
                    self.treeview.update_all_text()
                    self.main_window.set_control(locked=False)
                    self.main_window.show_default_msg_in_statusbar()
            else:
                # // select root
                if ev.modifiers() & Qt.ShiftModifier:
                    t1 = self.prev_click_time
                    t2 = time.time()
                    if t2 - t1 <= 0.2:
                        v = self.slice_layer_item.image[
                            position[2], position[1]
                        ].max()
                        if v:
                            self.select_root_by_clicks(position)
                    self.prev_click_time = t2
                    return
                # // add root node
                else:
                    self.main_window.set_control(locked=True)
                    self.add_root(annotations=annotations)
                    self.treeview.update_all_text()
                    self.main_window.set_control(locked=False)
                    self.main_window.show_default_msg_in_statusbar()

    def __get_closest_distance(self, ref_coordinate, from_polyline):
        from_polyline = np.array(from_polyline).T
        np_polyline = np.array(from_polyline)
        distance = ((np_polyline.T - ref_coordinate) ** 2).sum(axis=1).min()
        return distance

    def select_root_by_clicks(self, position):
        ID_string_list = []
        distance_list = []
        for ID_string in self.RSA_components().vector.iter_all():
            if not ID_string.is_root():
                continue
            root_node = self.RSA_components().vector.root_node(
                ID_string=ID_string
            )
            if root_node is not None:
                distance = self.__get_closest_distance(
                    ref_coordinate=np.array(position),
                    from_polyline=root_node.completed_polyline(),
                )
                ID_string_list.append(ID_string)
                distance_list.append(distance)

        if len(ID_string_list) == 0:
            return

        argmin = np.argmin(distance_list)
        ID_string_min = ID_string_list[argmin]
        distance_min = distance_list[argmin]

        if distance_min > 20**2:
            return

        self.main_window.set_control(locked=True)
        self.treeview.select(ID_string=ID_string_min)
        self.main_window.on_selected_item_changed(
            selected_ID_string=ID_string_min
        )
        self.main_window.set_control(locked=False)

    def add_base(self, annotations):
        ID_string = self.RSA_components().vector.append_base(
            annotations=annotations
        )
        self.treeview.add_base(ID_string=ID_string)
        self.pos_marks.draw(ID_string=ID_string)

        self.main_window.on_selected_item_changed(selected_ID_string=ID_string)

    def add_root(self, annotations):
        selected_ID_string = self.treeview.get_selected_ID_string()
        if selected_ID_string is None:
            return

        base_node = self.RSA_components().vector.base_node(
            baseID=selected_ID_string.baseID()
        )
        if base_node is None:
            return

        ID_string = base_node.append()
        self.treeview.add_root(ID_string=ID_string)
        self.add_relay(annotations=annotations, root_ID_string=ID_string)

    def add_relay(self, annotations: dict, root_ID_string: ID_Object = None):
        selected_ID_string = (
            root_ID_string or self.treeview.get_selected_ID_string()
        )
        if selected_ID_string is None or selected_ID_string.is_base():
            return

        base_node = self.RSA_components().vector.base_node(
            baseID=selected_ID_string.baseID()
        )
        if base_node is None:
            return

        baseID, rootID, _ = selected_ID_string.split()
        ID_string = self.RSA_components().vector.append_relay(
            baseID=baseID, rootID=rootID, annotations=annotations
        )
        if ID_string is not None:
            self.treeview.add_relay(ID_string=ID_string)

        self.main_window.update_df_dict_for_drawing(
            target_ID_string=ID_string.to_root()
        )
        self.main_window.on_selected_item_changed(
            selected_ID_string=selected_ID_string
        )

    def update_volume(self, volume):
        self.setImage(img=volume, axes={"t": 0, "x": 2, "y": 1, "c": None})

    def clear(self):
        super().clear()
        self.pos_marks.hide()
        self.isocurve.hide()

    def on_mouse_wheeled(self, ev: QGraphicsSceneWheelEvent):
        ev.accept()
        if (
            self.main_window.is_control_locked()
            or self.RSA_components().volume.is_empty()
        ):
            return

        if ev.modifiers() & Qt.ControlModifier:
            self.view.wheelEvent(ev)
            return

        processed_image = self.getProcessedImage()
        if not isinstance(processed_image, np.ndarray):
            return

        index = (
            max(self.currentIndex - 1, 0)
            if ev.delta() > 0
            else min(self.currentIndex + 1, processed_image.shape[0] - 1)
        )
        self.setCurrentIndex(index)

    def update_slice_layer(self):
        np_volume = self.RSA_components().volume.data
        df_dict_for_drawing = self.__parent.df_dict_for_drawing
        slice_layer = np.zeros((np_volume.shape[1:3] + (4,)), dtype=np.uint8)

        df_list_for_drawing = [v for k, v in df_dict_for_drawing.items()]
        if len(df_list_for_drawing) != 0:
            df_for_drawing = pl.concat(df_list_for_drawing).filter(
                pl.col("z") == self.currentIndex
            )
            z_array = df_for_drawing["z"].to_numpy()
            y_array = df_for_drawing["y"].to_numpy()
            x_array = df_for_drawing["x"].to_numpy()
            color_array = np.array(df_for_drawing["color"].to_list())

            if len(z_array) != 0:
                slice_layer[x_array, y_array] = color_array

        self.slice_layer_item.setImage(slice_layer, autoLevels=False)

    def move_position(self, ID_string: ID_Object):
        # // ID_string 分類
        target_coordinate = None
        if ID_string.is_relay():
            relay_node = self.RSA_components().vector.relay_node(
                ID_string=ID_string
            )
            if relay_node is not None:
                target_coordinate = relay_node["coordinate"]
        elif ID_string.is_root():
            root_node = self.RSA_components().vector.root_node(
                ID_string=ID_string
            )
            if root_node is not None:
                target_coordinate = root_node.tip_coordinate()
        else:
            base_node = self.RSA_components().vector.base_node(
                ID_string=ID_string
            )
            if base_node is not None:
                target_coordinate = base_node["coordinate"]

        if target_coordinate is not None:
            self.setCurrentIndex(target_coordinate[0])

            x_range = self.x_range
            y_range = self.y_range
            if len(x_range) != 0:
                x_len = x_range[1] - x_range[0] + 1
                y_len = y_range[1] - y_range[0] + 1
                x = target_coordinate[2]
                y = target_coordinate[1]
                x_range = [x - x_len / 2, x + x_len / 2]
                y_range = [y - y_len / 2, y + y_len / 2]
                self.view.setRange(xRange=x_range, yRange=y_range)


class PosMarks(GraphItem):
    def __init__(self, imageview: QtSliceView):
        self.imageview = imageview
        self.dragPoint = None
        self.dragOffset = None
        self.textItems = []
        super().__init__()
        self.scatter.sigClicked.connect(self.clicked)

    @property
    def rsa_components(self) -> RSA_Components:
        return self.imageview.RSA_components()

    @property
    def gui_components(self):
        return self.imageview.GUI_components()

    @property
    def treeview(self):
        return self.gui_components.treeview

    @property
    def ct_volume(self):
        return self.rsa_components.volume

    @property
    def rsa_vector(self):
        return self.rsa_components.vector

    def make_draw_parameter_class(self):
        class DrawParameterClass(object):
            def __init__(self):
                self.__dict = {
                    "size": 10,
                    "pxMode": True,
                    "antialias": True,
                    "pos": [],
                    "symbol": [],
                    "symbolPen": [],
                    "symbolBrush": [],
                    "text": [],
                }

            def to_dict(self):
                return_dict = self.__dict.copy()
                return_dict["pos"] = np.array(return_dict["pos"])

                return return_dict

            def is_empty(self):
                return len(self.__dict["pos"]) == 0

            def add_node(
                self,
                pos: List,
                symbolPen: QPen,
                symbolBrush: QBrush,
                text: str,
                symbol: str = "o",
            ):
                self.__dict["pos"].append(pos)
                self.__dict["symbolPen"].append(symbolPen)
                self.__dict["symbolBrush"].append(symbolBrush)
                self.__dict["text"].append(text)
                self.__dict["symbol"].append(symbol)

        return DrawParameterClass()

    def draw(self, ID_string: ID_Object = None):
        if ID_string is None or self.ct_volume.is_empty():
            self.data = {}
            self.setTexts([])
            self.updateGraph()
            return

        draw_parameters = self.make_draw_parameter_class()

        def add_marks(ID_string, pen: QPen, brush: QBrush):
            node = self.rsa_vector[ID_string]
            if node is not None:
                clicked_coordinate = node["coordinate"]
                if clicked_coordinate is None:
                    return

                draw_parameters.add_node(
                    pos=[
                        clicked_coordinate[2] + 0.5,
                        clicked_coordinate[1] + 0.5,
                    ],
                    symbolPen=pen,
                    symbolBrush=brush,
                    text=ID_string,
                )

        add_marks(
            ID_string.to_base(), mkPen((255, 0, 0)), mkBrush((255, 0, 0, 64))
        )

        if not ID_string.is_base():
            root_node = self.rsa_vector.root_node(ID_string=ID_string)
            if root_node is not None:
                relay_ID_strings = root_node.child_ID_strings()
                selected_ID_string = self.treeview.get_selected_ID_string()

                for ID_string in relay_ID_strings:
                    if (
                        selected_ID_string not in relay_ID_strings
                        or ID_string == selected_ID_string
                    ):
                        add_marks(
                            ID_string,
                            mkPen((0, 255, 0)),
                            mkBrush((0, 255, 0, 64)),
                        )
                    else:
                        add_marks(
                            ID_string,
                            mkPen((0, 128, 0)),
                            mkBrush((0, 255, 0, 32)),
                        )

        if draw_parameters.is_empty():
            return

        self.setData(**draw_parameters.to_dict())
        self.show()

    def setData(self, **kwds):
        self.text = kwds.pop("text", [])
        self.data = kwds
        if "pos" in self.data:
            npts = self.data["pos"].shape[0]
            self.data["data"] = np.empty(npts, dtype=[("index", int)])
            self.data["data"]["index"] = np.arange(npts)
        self.setTexts(self.text)
        self.updateGraph()

    def setTexts(self, text):
        for i in self.textItems:
            i.scene().removeItem(i)
        self.textItems = []
        self.ID_strings = text.copy()
        for t in text:
            item = TextItem(f"{t.split()[2]:02}", color=(100, 100, 200))
            self.textItems.append(item)
            item.setParentItem(self)

    def updateGraph(self):
        GraphItem.setData(self, **self.data)
        for i, item in enumerate(self.textItems):
            item.setPos(*self.data["pos"][i])

    def clicked(self, scatter_plot_item, spot_items):
        clicked_ID_string = self.ID_strings[spot_items[0].data()[0]]
        if clicked_ID_string.is_base():
            clicked_ID_string = self.ID_strings[-1]
            self.treeview.select(ID_string=clicked_ID_string.to_root())
        else:
            self.treeview.select(ID_string=clicked_ID_string)


class _IsocurveItem(IsocurveItem):
    def __init__(self):
        super().__init__()
        self.setLevel(255)
        self.setPen(mkPen([255, 255, 255, 64]))

    def draw(self, projection_image: np.ndarray):
        if projection_image is None:
            self.setData(None)
            return

        self.show()

        self.setData(projection_image.transpose(1, 0))
