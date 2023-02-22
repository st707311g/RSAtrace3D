import psutil
from DATA.RSA import RSA_Components
from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QSizePolicy, QStatusBar


class QtStatusBarW(QObject):
    pyqtSignal_update_progressbar = Signal(int, int, str)

    def __init__(self, parent):
        super().__init__()
        self.__parent = parent
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.start()

        self.widget = QtStatusBar(parent=parent)
        self.pyqtSignal_update_progressbar.connect(self.widget.update_progress)

    def parent(self):
        return self.__parent

    def set_main_message(self, msg):
        self.widget.set_main_message(msg=msg)

    def update_mouse_position(self, z=-1, y=-1, x=-1):
        self.widget.update_mouse_position(z=z, y=y, x=x)


class QtStatusBar(QStatusBar):
    def __init__(self, parent):
        super().__init__(**{"parent": parent})

        self.progress = QProgressBar()
        self.status_msg = QLabel("")

        self.mouse_msg = QLabel("")
        self.prev_mouse_pos = [0, 0, 0]
        self.mem_msg = QLabel("")
        self.cpu_msg = QLabel("")

        self.addWidget(self.progress)
        self.addWidget(self.status_msg, 2048)

        self.progress.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        )

        self.addPermanentWidget(self.mouse_msg, 200)
        self.addPermanentWidget(self.cpu_msg, 140)
        self.addPermanentWidget(self.mem_msg, 140)

        self.progress.setValue(0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_meter)
        self.timer.start(1000)

        self.update_mouse_position()

    def RSA_components(self) -> RSA_Components:
        return self.parent().RSA_components()

    def update_progress(self, i, maximum, msg):
        self.progress.setMaximum(maximum)
        self.progress.setValue(i)

        self.set_main_message(f"{msg}: {i} / {maximum}")

    def set_main_message(self, msg):
        if self.parent().is_control_locked():
            msg = "BUSY: " + msg
        else:
            msg = "READY: " + msg

        self.status_msg.setText(msg)

    def update_meter(self):
        mem_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()

        if isinstance(mem_percent, float) and isinstance(cpu_percent, float):
            for msg, hard, p in zip(
                [self.mem_msg, self.cpu_msg],
                ["Memory", "CPU"],
                [mem_percent, cpu_percent],
            ):
                bg_color = "yellow" if p > 80 else "transparent"
                msg.setStyleSheet(
                    "QLabel { background-color : %s; color : black; }"
                    % bg_color
                )
                msg.setText(" %s: %.01f %% " % (hard, p))

    def update_mouse_position(self, z=-1, y=-1, x=-1):
        if (
            z < 0 and y < 0 and x < 0
        ) or self.RSA_components().volume.is_empty():
            self.mouse_msg.setText("")
            return

        if z >= 0 and y < 0 or x < 0:
            y = self.prev_mouse_pos[1]
            x = self.prev_mouse_pos[2]

        self.prev_mouse_pos = [int(z), int(y), int(x)]
        self.mouse_msg.setText(f"x:{int(x)}, y:{int(y)}, z:{int(z)}")
