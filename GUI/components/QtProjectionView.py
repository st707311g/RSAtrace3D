from typing import Dict, List

import numpy as np
import polars as pl
from DATA.RSA import RSA_Components
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QGridLayout, QWidget
from pyqtgraph import ImageItem, InfiniteLine, ViewBox, mkColor
from pyqtgraph.widgets.GraphicsLayoutWidget import GraphicsLayoutWidget


class CoreViewBox(ViewBox):
    pyqtSignal_mouseClickEvent = pyqtSignal(int, object, int, bool)

    def __init__(self, identifier, **kwargs):
        super().__init__(**kwargs)
        self.identifier = identifier

        self.setAspectLocked(True)
        self.invertY()

        self.projection_image = ImageItem()
        self.trace_image = ImageItem()
        self.addItem(self.projection_image)
        self.addItem(self.trace_image)

        self.setBackgroundColor(mkColor("#000000"))

    def clear_all(self):
        self.projection_image.clear()
        self.trace_image.clear()

    def is_empty(self):
        return self.projection_image.image is None

    def mouseClickEvent(self, ev):
        self.pyqtSignal_mouseClickEvent.emit(
            self.identifier,
            self.mapToView(ev.pos()),
            ev.button(),
            self.projection_image.image is not None,
        )


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

        self.bg_color = mkColor("#000000")
        self.setBackground(self.bg_color)

    def set_projection_image(self, img):
        self.view.projection_image.setImage(img.transpose(1, 0))
        self.view.autoRange()

    def set_trace_image(self, img):
        img = None if img is None else img.transpose(1, 0, 2)
        self.view.trace_image.setImage(img)
        self.setBackground(self.bg_color)

    def clear_all(self):
        self.view.clear_all()

    def select_itself(self, flag):
        self.bg_color = mkColor("#444444") if flag else mkColor("#000000")
        self.setBackground(self.bg_color)


class MainViewWidget(CoreViewWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.make_viewbox()

    def make_viewbox(self):
        self.view = MainViewBox(identifier=self.identifier)
        self.infinite_line = InfiniteLine(angle=0, movable=True)
        self.infinite_line.hide()
        self.addItem(self.view)
        self.view.addItem(self.infinite_line)


class SubViewWidget(CoreViewWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.make_viewbox()

    def make_viewbox(self):
        self.view = SubViewBox(identifier=self.identifier)
        self.addItem(self.view)


class QtProjectionView(QWidget):
    def __init__(self, parent):
        super().__init__(**{"parent": parent})
        self.__parent = parent
        self.layout = QGridLayout()
        self.main_view_widget = MainViewWidget(identifier=-1, dimension=None)
        self.layout.addWidget(self.main_view_widget, 0, 0, 3, 1)

        self.sub_view_widgets: List[SubViewWidget] = []
        for i, dimension in enumerate([[1, 2], [0, 2], [0, 1]]):
            self.sub_view_widgets.append(
                SubViewWidget(identifier=i, dimension=dimension)
            )
            self.layout.addWidget(self.sub_view_widgets[i], i, 1)

        self.layout.setColumnStretch(0, 3)
        self.layout.setColumnStretch(1, 1)

        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 4, 0)

        self.setLayout(self.layout)

        self.current_view_index = -1
        self.dimensions = ((1, 2), (0, 2), (0, 1))
        self.selected_ID_string = None

        for w in self.all_widgets():
            w.view.pyqtSignal_mouseClickEvent.connect(self.on_mouse_clicked)

        self.main_view_widget.infinite_line.sigDragged.connect(
            self.on_infinite_line_pos_changed
        )

    def all_widgets(self):
        return [self.main_view_widget] + self.sub_view_widgets

    def parent(self):
        return self.__parent

    def RSA_components(self) -> RSA_Components:
        return self.parent().RSA_components()

    def GUI_components(self):
        return self.parent().GUI_components()

    def update_selected_items(self):
        self.main_view_widget.select_itself(flag=False)
        for i in range(3):
            self.sub_view_widgets[i].select_itself(
                flag=self.current_view_index == i
            )

    def update_main_widget(self):
        if self.current_view_index not in [0, 1, 2]:
            return

        # // update projection
        view = self.sub_view_widgets[self.current_view_index].view
        img = view.projection_image.image
        if img is not None:
            self.main_view_widget.set_projection_image(img=img.transpose(1, 0))

        # // update trace
        img = view.trace_image.image
        if img is not None:
            self.main_view_widget.set_trace_image(img=img.transpose(1, 0, 2))

        if self.current_view_index != 0:
            self.main_view_widget.infinite_line.show()
        else:
            self.main_view_widget.infinite_line.hide()

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
                root_node = self.RSA_components().vector.root_node(
                    ID_string=ID_string
                )
                if root_node is not None:
                    distance = self.__get_closest_distance(
                        ref_coordinate=np.array(
                            [int(coordinate.y()), int(coordinate.x())]
                        ),
                        from_polyline=root_node.completed_polyline(),
                        index=self.current_view_index,
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

            self.GUI_components().treeview.select(ID_string=ID_string_min)

        if identifier in [0, 1, 2]:
            self.current_view_index = identifier
            self.update_selected_items()
            self.update_main_widget()

    def clear(self):
        self.current_view_index = -1
        self.update_selected_items()
        self.main_view_widget.clear_all()
        for i in range(3):
            self.sub_view_widgets[i].clear_all()
        self.main_view_widget.infinite_line.hide()

    def set_volume(self, volume):
        if volume is None:
            return

        for i in range(3):
            self.sub_view_widgets[i].set_projection_image(
                img=volume.max(axis=i)
            )

        self.current_view_index = 0
        self.update_selected_items()
        self.update_main_widget()

        self.volume_shape = volume.shape
        self.main_view_widget.infinite_line.setBounds(
            (0, self.volume_shape[0])
        )

    def set_view_layer(self, df_dict_for_drawing: Dict[str, pl.DataFrame]):
        if len(df_dict_for_drawing) == 0:
            for i, dimension in enumerate([[1, 2], [0, 2], [0, 1]]):
                sub_view_widget = self.sub_view_widgets[i]
                projection_image = sub_view_widget.view.projection_image.image
                if projection_image is None:
                    continue
                else:
                    np_layer = np.zeros(
                        projection_image.shape + (4,), dtype=np.uint8
                    )
                    sub_view_widget.set_trace_image(img=np_layer)

            self.update_main_widget()
            return

        df_list_for_drawing = [v for k, v in df_dict_for_drawing.items()]
        df_for_drawing = pl.concat(df_list_for_drawing)

        z_array = df_for_drawing["z"].to_numpy()
        y_array = df_for_drawing["y"].to_numpy()
        x_array = df_for_drawing["x"].to_numpy()
        array_list = [z_array, y_array, x_array]
        color_array = np.array(df_for_drawing["color"].to_list())

        for i, dimension in enumerate([[1, 2], [0, 2], [0, 1]]):
            sub_view_widget = self.sub_view_widgets[i]
            projection_image = sub_view_widget.view.projection_image.image
            if projection_image is None:
                continue

            shape = (projection_image.shape[1], projection_image.shape[0], 4)

            np_layer = np.zeros(shape, dtype=np.uint8)
            if len(df_list_for_drawing) == 0:
                self.sub_view_widgets[i].set_trace_image(img=np_layer)
                continue

            if len(z_array) != 0:
                np_layer[
                    array_list[dimension[0]], array_list[dimension[1]]
                ] = color_array

            self.sub_view_widgets[i].set_trace_image(img=np_layer)

        self.update_main_widget()

    def __get_closest_distance(self, ref_coordinate, from_polyline, index):
        from_polyline = np.array(from_polyline).T
        np_polyline = np.delete(np.array(from_polyline), index, axis=0)
        distance = ((np_polyline.T - ref_coordinate) ** 2).sum(axis=1).min()
        return distance

    def on_spacekey_pressed(self, pressed):
        for w in self.all_widgets():
            if pressed is True:
                w.view.trace_image.hide()
            else:
                w.view.trace_image.show()

    def on_showing_slice_changed(self, index: int):
        if self.main_view_widget.infinite_line.pos().y() != index:
            self.main_view_widget.infinite_line.setPos(index)

    def on_infinite_line_pos_changed(self, infinite_line: InfiniteLine):
        z_pos = int(infinite_line.pos().y())
        self.GUI_components().sliceview.timeLine.setPos(z_pos)
