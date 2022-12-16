import json
import logging
import os
from pathlib import Path

from PyQt5.QtWidgets import QAction, QMenu

import config


class History:
    def __init__(self, max_count, menu_label):
        self.max_count = max_count
        self.menu = QMenu(menu_label)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.clear()

    def clear(self):
        self.data = []

    def add(self, item):
        if item in self.data:
            del self.data[self.data.index(item)]
        if len(self.data) >= self.max_count:
            del self.data[0]
        self.data.append(item)

    def item_count(self):
        return len(self.data)

    def iter_forward(self):
        for i in self.data:
            yield i

    def iter_reverse(self):
        for i in self.data[::-1]:
            yield i

    def get_dict(self):
        dict_ = {}
        for i, item in enumerate(self.iter_forward()):
            dict_.update({f"{i+1:02}": str(item)})

        return dict_

    def update(self, dict_):
        self.clear()
        for v in dict_.values():
            self.add(v)

    def save(self, file_name):
        dst = os.path.join(config.config_dir, file_name)
        dict_ = self.get_dict()
        with open(dst, "w") as j:
            json.dump(dict_, j)

    def load(self, file_name):
        src = os.path.join(config.config_dir, file_name)
        if not os.path.isfile(src):
            return False

        self.clear()

        if Path(file_name).is_file():
            try:
                with open(src, "r") as f:
                    dict_ = json.load(f)
                    for v in dict_.values():
                        self.add(v)

                return True
            except json.decoder.JSONDecodeError:
                self.logger.error(
                    "[loading failed] History file could not be loaded. "
                    "The history data has been cleared."
                )
            return False

    def build_menu(self, parent, triggered):
        self.parent = parent
        self.triggered = triggered
        return self.update_menu()

    def update_menu(self):
        self.menu.clear()
        for name in self.iter_reverse():
            volume_path: str = str(name)
            act = QAction(
                text=volume_path, parent=self.parent, triggered=self.triggered
            )
            act.setData(volume_path)
            act.setEnabled(
                os.path.isdir(volume_path)
                or (
                    os.path.isfile(volume_path)
                    and volume_path.lower().endswith(".tar.gz")
                )
            )
            self.menu.addAction(act)

        return self.menu
