import logging
import weakref
from copy import deepcopy
from typing import List

import numpy as np
from PyQt5.QtGui import QColor
from skimage.morphology import ball, disk

from .rinfo import ID_Object, RootNode, RSA_Vector


class Trace(object):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.clear()

    def is_empty(self):
        return self.trace3D is None

    def clear(self):
        self.trace3D = None
        self.projections = []
        self.histry = []

        self.logger.debug("The trace data cleared.")

    def init_from_volume(self, volume):
        self.clear()
        self.trace3D = TraceObject(
            shape=volume.shape, dimensions=[0, 1, 2], pen_size=3
        )
        for dimensions in [[1, 2], [0, 2], [0, 1]]:
            self.projections.append(
                TraceObject(
                    shape=volume.shape, dimensions=dimensions, pen_size=3
                )
            )

    def root_ndoes_to_be_updated(
        self, RSA_vector: RSA_Vector
    ) -> List[RootNode]:
        modified = any([ref() is None for ID_string, ref in self.histry])

        if modified:
            for trace_obj in [self.trace3D] + self.projections:
                if trace_obj is not None:
                    trace_obj.clear()
            self.histry = []

        base_node = RSA_vector.base_node(baseID=1)
        if base_node is None:
            return []

        root_nodes = base_node.child_nodes()
        return_list = []
        for root_node in root_nodes:
            if root_node.ID_string() in [i[0] for i in self.histry]:
                continue

            return_list.append(root_node)

        return return_list

    def draw_trace(self, root_node: RootNode):
        ID_string = root_node.ID_string()
        completed_polyline = root_node.completed_polyline()
        for trace_obj in [self.trace3D] + self.projections:
            if trace_obj is not None:
                trace_obj.draw_trace_single(
                    completed_polyline, color=QColor("#8800ff00")
                )
        self.histry.append([ID_string, weakref.ref(completed_polyline)])

    def create_trace_object(
        self, RSA_vector: RSA_Vector, ID_string: ID_Object, **kwargs
    ):
        trace_obj = TraceObject(**kwargs)

        if ID_string.is_base():
            return None

        if ID_string.is_relay:
            ID_string = ID_string.to_root()

        baseID, rootID, _ = ID_string.split()
        root_node = RSA_vector.root_node(baseID, rootID)
        if root_node is None:
            return None

        completed_polyline = root_node.completed_polyline()

        if completed_polyline is not None:
            trace_obj.draw_trace_single(
                completed_polyline, color=QColor("#ffffffff")
            )

        return trace_obj


class TraceObject:
    def __init__(self, shape, dimensions=[0, 1, 2], pen_size=3):
        self.dimensions = deepcopy(dimensions)
        self.shape_full = tuple(shape + (4,))
        self.shape = tuple([shape[d] for d in self.dimensions]) + (4,)
        self.pen_size = pen_size

        self.clear()

    def clear(self):
        self.volume = np.zeros(self.shape, dtype=np.uint8)

    def get_slice_generator(self, polyline):
        S = self.pen_size * 2 + 1

        for pos in polyline:
            # // skip invalid values
            if any(
                [pos[d] < 0 or pos[d] >= self.shape_full[d] for d in range(3)]
            ):
                continue

            # // slices for cropping
            slices = []
            pad_slices = []
            for d in range(3):
                slices.append(
                    slice(
                        max(pos[d] - self.pen_size, 0),
                        min(pos[d] + self.pen_size + 1, self.shape_full[d]),
                    )
                )
                pad_slices.append(
                    slice(
                        -min(pos[d] - self.pen_size, 0),
                        S
                        + min(
                            self.shape_full[d] - pos[d] - self.pen_size - 1, 0
                        ),
                    )
                )

            not_index = [d for d in range(3) if d not in self.dimensions]
            for d in not_index:
                del slices[d]
                del pad_slices[d]

            yield (slices, pad_slices)

    def draw_trace(self, polyline, color=QColor("#ffffffff")):
        for slices, pad_slices in self.get_slice_generator(polyline=polyline):
            croped = self.volume[tuple(slices)]
            pen = ball if len(self.dimensions) == 3 else disk
            pen = pen(self.pen_size)[tuple(pad_slices)]
            m_ball = [pen * color for color in color.getRgb()]
            m_ball = np.stack(m_ball, axis=len(self.dimensions))

            croped = np.maximum(croped, m_ball)
            self.volume[tuple(slices)] = croped

    def draw_trace_single(self, polyline, **kwargs):
        self.draw_trace(polyline, **kwargs)

    def redraw_trace_all(self, polyline_list, **kwargs):
        self.clear()
        for polyline in polyline_list:
            self.draw_trace(polyline, **kwargs)
