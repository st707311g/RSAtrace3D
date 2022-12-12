import logging

import pandas as pd
from DATA.RSA import RSA_Components
from DATA.RSA.components.rinfo import ID_Object
from GUI.components import QtMain
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QHeaderView, QTreeView

try:
    from PyQt5.QtGui import QAbstractItemView
except ImportError:
    from PyQt5.QtWidgets import QAbstractItemView


class TreeViewHeader(QHeaderView):
    def __init__(self):
        super().__init__(*(Qt.Horizontal,))

        self.setSectionsMovable(False)
        self.setDefaultAlignment(Qt.AlignLeft)


class TreeModel(QStandardItemModel):
    def __init__(self):
        super().__init__()

    def get_logical_index(self, label):
        for i in range(self.columnCount()):
            if self.horizontalHeaderItem(i).text() == label:
                return i

        return None

    def get_iter_all_items(self, column, parent=None):
        if type(column) == str:
            logical_index = None
            for i in range(self.columnCount()):
                if self.horizontalHeaderItem(i).text() == column:
                    logical_index = i
                    break

            column = logical_index

        if parent is None:
            for row in range(self.rowCount()):
                yield self.item(row, column)
                yield from self.get_iter_all_items(
                    column=column, parent=self.item(row, 0)
                )
        else:
            for row in range(parent.rowCount()):
                yield parent.child(row, column)
                yield from self.get_iter_all_items(
                    column=column, parent=parent.child(row, 0)
                )

    def get_iter_all_texts(self, column, parent=None):
        for item in self.get_iter_all_items(column, parent):
            yield item.text()

    def get_iter_all_indexes(self, column, parent=None):
        for item in self.get_iter_all_items(column, parent):
            yield item.index()

    def get_selected_base_index(self, selection_model, column=0):
        if not selection_model.hasSelection():
            return None

        index = selection_model.selectedRows(0)[0]
        item = self.itemFromIndex(index)

        while item.parent() is not None:
            item = item.parent()

        return self.indexFromItem(item)

    def get_index(self, ID_string, column=0):
        ID_iter = self.get_iter_all_texts(column="ID string")
        index_iter = self.get_iter_all_indexes(column=column)

        for ID_string_, index in zip(ID_iter, index_iter):
            if ID_string_ == ID_string:
                return index

        return None

    def get_item(self, ID_string, column=0):
        index = self.get_index(ID_string=ID_string, column=column)
        return self.itemFromIndex(index) if index is not None else None


class QtTreeView(QTreeView):
    pyqtSignal_selected_item_changed = pyqtSignal(object)

    def __init__(self, parent: QtMain):
        super().__init__(**{"parent": parent})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__parent = parent
        self.root_traits = self.parent().root_traits
        self.model = TreeModel()
        self.tv_header = TreeViewHeader()
        self.setHeader(self.tv_header)
        self.model.setHorizontalHeaderLabels(
            self.root_traits.class_container.labels()
        )

        for ci, cls_ in enumerate(self.root_traits.class_container):
            item = self.model.horizontalHeaderItem(ci)
            try:
                item.setToolTip(cls_.tool_tip)
            except:  # noqa
                pass

        self.setModel(self.model)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAllColumnsShowFocus(True)

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

    def clear(self):
        for i in range(self.model.rowCount()):
            self.model.removeRow(0)

    def create_row(self, ID_string: ID_Object):
        row = []
        for class_ in self.root_traits.class_container:
            ret = class_(
                self.RSA_components().vector, ID_string
            ).QStandardItem()
            row.append(ret)

        return row

    def add_base(
        self, ID_string: ID_Object, annotations={}, auto_selection=True
    ):
        row = self.create_row(ID_string=ID_string)
        self.model.appendRow(row)

        if auto_selection:
            self.select(ID_string=ID_string)

        self.logger.debug(f"A base node added: {ID_string}")

    def add_root(
        self, ID_string: ID_Object, annotations={}, auto_selection=True
    ):
        base_index = self.model.get_selected_base_index(
            selection_model=self.selectionModel()
        )
        if base_index is None:
            return

        row = self.create_row(ID_string=ID_string)
        base_item = self.model.itemFromIndex(base_index)
        base_item.appendRow(row)

        if not self.isExpanded(base_index):
            self.setExpanded(base_index, True)

        if auto_selection:
            self.select(ID_string=ID_string)

        self.logger.debug(f"A root node added: {ID_string}")

    def add_relay(
        self, ID_string: ID_Object, annotations={}, auto_selection=True
    ):
        root_ID_string = ID_string.to_root()

        base_index = self.model.get_selected_base_index(
            selection_model=self.selectionModel()
        )
        if base_index is None:
            return False

        base_item = self.model.itemFromIndex(base_index)

        logical_index = self.model.get_logical_index(label="ID string")
        result_item = None
        for r in range(base_item.rowCount()):
            item = base_item.child(r, logical_index)
            if item.text() == root_ID_string:
                result_item = base_item.child(r, 0)
                break

        if result_item is None:
            return False

        row = self.create_row(ID_string=ID_string)
        result_item.appendRow(row)

        if auto_selection:
            self.select(ID_string=root_ID_string)

        self.update_text(ID_string=root_ID_string)

        self.logger.debug(f"A relay node added: {ID_string}")

    def update_text(self, ID_string: ID_Object):
        item = self.model.get_item(ID_string=ID_string)
        if item is None:
            return

        nrow = item.row()
        parent = item.parent()

        for icol in range(self.model.columnCount()):
            if parent is None:
                target_index = self.model.index(nrow, icol)
                target_item = self.model.itemFromIndex(target_index)
            else:
                target_item = parent.child(nrow, icol)
                data = target_item.data()
                data.update()

    # // updating all item texts
    def update_all_text(self):
        ID_iter = self.model.get_iter_all_texts(column="ID string")
        item_iter = self.model.get_iter_all_items(column=0)

        for ID_string, item in zip(ID_iter, item_iter):
            nrow = item.row()
            parent = item.parent()

            for icol in range(self.model.columnCount()):
                if parent is None:
                    target_index = self.model.index(nrow, icol)
                    target_item = self.model.itemFromIndex(target_index)
                else:
                    target_item = parent.child(nrow, icol)
                    data = target_item.data()
                    data.update()

    def delete(self, ID_string: ID_Object):
        if ID_string is None:
            return

        item = self.model.get_item(ID_string=ID_string)
        if item is not None:
            parent = item.parent()
            nr = item.row()

            parent = parent or self.model
            parent.removeRow(nr)

            return self

    def select(self, ID_string: ID_Object):
        if ID_string is None:
            return

        selection_model = self.selectionModel()

        if selection_model.hasSelection():
            index = selection_model.selectedRows(1)[0]
            if self.model.itemFromIndex(index).text() == ID_string:
                return

        ID_iter = self.model.get_iter_all_texts(column="ID string")
        index_iter = self.model.get_iter_all_indexes(column=0)

        for ID_string_, index in zip(ID_iter, index_iter):
            if ID_string_ == ID_string:
                self.setCurrentIndex(index)
                self.scrollTo(index)

        self.repaint()
        self.setFocus()

    def get_selected_ID_string(self):
        logical_index = self.model.get_logical_index(label="ID string")
        index = self.currentIndex().siblingAtColumn(logical_index)
        item = self.model.itemFromIndex(index)

        return (
            None
            if item is None
            else ID_Object(self.model.itemFromIndex(index).text())
        )

    def selectionChanged(self, selected, deselected):
        index = selected.indexes()
        if len(index) == 0:
            return

        logical_index = self.model.get_logical_index(label="ID string")
        item = self.model.itemFromIndex(index[logical_index])
        super().selectionChanged(selected, deselected)
        ID_string = ID_Object(item.text())
        self.logger.debug(f"The selected item changed: {ID_string}")

        if not self.parent().is_control_locked():
            self.__parent.on_selected_item_changed(
                selected_ID_string=ID_string
            )
            # self.GUI_components().sliceview.pos_marks.draw(ID_string=ID_string)
            # self.GUI_components().sliceview.isocurve.draw(ID_string=ID_string)
            # self.GUI_components().projectionview.on_selected_item_changed(
            #    ID_string=ID_string
            # )
            self.GUI_components().sliceview.move_position(ID_string=ID_string)

    def to_pandas_df(self):
        labels = []
        column_data = []

        exportable_list = self.root_traits.class_container.expotable_list()
        for ci in range(self.model.columnCount()):
            if exportable_list[ci] is False:
                continue

            label = self.model.horizontalHeaderItem(ci).text()
            cls_ = self.root_traits.get(label=label)

            sublabels = cls_.sublabels
            n_sublabel = len(sublabels)

            if n_sublabel == 0:
                labels.append(label)
                ID_iter = self.model.get_iter_all_texts(column="ID string")
                item_iter = self.model.get_iter_all_items(column=ci)

                data = []
                for ID_string, item in zip(ID_iter, item_iter):
                    ID_string = ID_Object(ID_string)
                    if ID_string.is_root():
                        data.append(item.data().value)

                column_data.append(data)
            else:
                for i in range(n_sublabel):
                    labels.append(f"{label}_{sublabels[i]}")
                    ID_iter = self.model.get_iter_all_texts(column="ID string")
                    item_iter = self.model.get_iter_all_items(column=ci)

                    data = []
                    for ID_string, item in zip(ID_iter, item_iter):
                        ID_string = ID_Object(ID_string)
                        if ID_string.is_root():
                            v = item.data().value
                            v = v[i] if v is not None else ""
                            data.append(v)

                    column_data.append(data)

        df = pd.DataFrame(column_data, index=labels)
        df = df.transpose()

        return df
