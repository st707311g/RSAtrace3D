import glob
import logging
import os
import sys
from importlib import import_module
from inspect import getmembers, isclass

from PyQt5.QtWidgets import QAction, QActionGroup, QMenu

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    logging.basicConfig(level=logging.INFO)

from mod.Extensions.__backbone__ import ExtensionBackbone
from mod.Interpolation.__backbone__ import InterpolationBackbone
from mod.Traits.__backbone__ import RootTraitBackbone, RSATraitBackbone


class _ClassContainer(list):
    def __init__(self):
        super().__init__()

    def __getitem__(self, key):
        for class_ in self:
            if class_.label == key:
                return class_

        return None

    def append(self, class_):
        class_.check()
        super().append(class_)

    def sort(self, *args, **kwargs):
        super().sort(key=lambda x: (x.index, x.label), *args, **kwargs)

    def labels(self):
        return [c.label for c in self]

    def expotable_list(self):
        return [c.exportable for c in self]


class _ClassLoader(object):
    def __init__(self, backbone, **kwargs):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.backbone = backbone
        self.menu = None
        self.class_container = _ClassContainer()
        self.load_files()

    def load_files(self):
        files = glob.glob(
            pathname=os.path.join(os.path.dirname(__file__), "**/*.py"),
            recursive=True,
        )
        files = [f for f in files if not os.path.basename(f).startswith("_")]
        files.sort()

        for f in files:
            f = f[len(os.path.dirname(os.path.dirname(__file__))) + 1 :]
            try:
                m_path, _ = os.path.splitext(f)
                m_path = m_path.replace("/", ".").replace("\\", ".")
                module = import_module(m_path, self.__module__)

                class_list = list(
                    getmembers(
                        module,
                        lambda x: issubclass(x, self.backbone)
                        if isclass(x)
                        else False,
                    )
                )
                for _, class_instance in class_list:
                    if class_instance != self.backbone:
                        self.class_container.append(class_instance)
            except:
                self.logger.error(
                    f"An unexpected error occurred while importing the module: {f}"
                )

        self.class_container.sort()

    def build_menu(self, menu_label, triggered, action_group=True):
        if self.menu is not None:
            return self.menu

        self.menu = QMenu(menu_label)
        self.act_group = QActionGroup(self.menu)
        self.act_group.setExclusive(True)

        for i, cls_ in enumerate(self.class_container):
            label = cls_.label
            act = QAction(
                text=label,
                parent=self.menu,
                triggered=triggered,
                checkable=True,
            )

            if action_group:
                act.setCheckable(True)
                if i == 0:
                    act.setChecked(True)
                act.setActionGroup(self.act_group)
            else:
                act.setCheckable(False)

            act.setData(label)

            try:
                act.setStatusTip(cls_.status_tip)
            except:
                pass

            self.menu.addAction(act)
        return self.menu

    def get(self, label):
        return self.class_container[label]

    def get_selected_label(self):
        if self.menu is None:
            return

        return self.act_group.checkedAction().data()

    def set_selected_by(self, label):
        if self.menu is None:
            return

        for i, act in enumerate(self.menu.actions()):
            if act.text() == label and not act.isChecked():
                act.setChecked(True)


class RootTraits(_ClassLoader):
    def __init__(self, **kwargs):
        super().__init__(backbone=RootTraitBackbone)


class RSATraits(_ClassLoader):
    def __init__(self, **kwargs):
        super().__init__(backbone=RSATraitBackbone)


class Interpolation(_ClassLoader):
    def __init__(self, **kwargs):
        super().__init__(backbone=InterpolationBackbone)


class Extensions(_ClassLoader):
    def __init__(self, parent, **kwargs):
        super().__init__(backbone=ExtensionBackbone)
        self.__parent = parent
        self.windows = {}

        for c in self.class_container:
            self.windows.update({c.label: c(parent=self.parent())})

    def parent(self):
        return self.__parent

    def build_menu(self, menu_label, triggered):
        return super().build_menu(menu_label, triggered, False)

    def activate_window(self, label):
        ins = self.windows[label]
        ins.show()
        ins.activateWindow()


if __name__ == "__main__":
    root_traits = RootTraits()
