import glob
import json
import logging
import os
from typing import Generator, List, Union

import config
import numpy as np


class RinfoFiles(object):
    def __init__(self, files:List[str]=None):
        self.files = files or []

    def list_files(self) -> List[str]:
        ret = []
        for f in sorted(self.files):
            if os.path.isfile(f) and f.endswith('.rinfo'):
                ret.append(f)

            if os.path.isdir(f):
                rinfo_list = sorted(glob.glob(f'{f}/**/*.rinfo', recursive=True))
                ret.extend(rinfo_list)

        return ret

class ID_Object(str):
    def __new__(cls, key: Union[str, list, tuple]):
        def __raise_exception():
            raise Exception('The arguments must be a list or tuple of length 3, three numbers, or a string in ID_Object format.')

        if type(key) is str:
            if key.count('-') != 2:
                __raise_exception()
            return super().__new__(cls, *(key,))
        elif type(key) in [list, tuple]:
            if len(key) != 3:
                __raise_exception()
            ID_string = '-'.join([f'{i:02}' for i in key])
            return super(ID_Object, cls).__new__(cls, *(ID_string,))
        else:
             __raise_exception()

    def split(self, sep:str='-'):
        return [int(it) for it in super().split(sep=sep)]

    def is_base(self):
        baseID, rootID, relayID = self.split()
        return baseID != 0 and rootID == 0 and relayID == 0

    def is_root(self):
        baseID, rootID, relayID = self.split()
        return baseID != 0 and rootID != 0 and relayID == 0

    def is_relay(self):
        baseID, rootID, relayID = self.split()
        return baseID != 0 and rootID != 0 and relayID != 0

    def to_base(self):
        baseID, *_ = self.split()
        return ID_Object([baseID, 0, 0])

    def to_root(self):
        baseID, rootID, _ = self.split()
        return ID_Object([baseID, rootID, 0])

    def baseID(self):
        return self.split()[0]

    def rootID(self):
        return self.split()[1]

    def relayID(self):
        return self.split()[2]

class Node(list):
    def __init__(self):
        super().__init__()
        self.annotations = {}

    def __str__(self):
        return json.dumps(self.dictionary(), indent=1)

    def __eq__(self, other):
        if other is None or not isinstance(other, Node): 
            return False
        
        return self is other

    def child_dictionary(self):
        return {child.ID: child.dictionary() for child in self}

    def dictionary(self):
        dictionary = {'#annotations': self.annotations}
        dictionary.update(self.child_dictionary())
        return dictionary

    def next_id(self):
        id_list = [child.ID for child in self]
        i = 1
        while i in id_list:
            i += 1

        return i

    def child_count(self):
        return len(self)

class _Annotations(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.set_resolution(0.3)
        self.update({'version': config.version_string()})

    def set_resolution(self, resolution):
        self.update({'resolution': resolution})

    def resolution(self) -> float:
        return self.get('resolution', None)

    def set_interpolation(self, interpolation):
        self.update({'interpolation': interpolation})

    def interpolation(self):
        return self.get('interpolation', None)

    def set_volume_shape(self, shape):
        self.update({'volume shape': shape})

    def volume_shape(self):
        return self.get('volume shape', None)

    def set_volume_name(self, name):
        self.update({'volume name': name})

    def volume_name(self):
        return self.get('volume name', None)

    def import_from(self, info_dict: dict):
        del info_dict['version']
        self.update(info_dict)
        self['volume shape'] = tuple(self['volume shape'])

class Polyline(list):
    pass

class RelayNode(Node):
    def __init__(self, ID: int, parent, annotations: dict):
        super().__init__()
        self.ID = ID
        self.__parent = parent
        self.annotations = annotations.copy()
        self.annotations.update({'ID_string': self.ID_string()})

    def __getitem__(self, key: str):
        for k, v in self.annotations.items():
            if k == key:
                return v
            return None

    def ID_string(self):
        return ID_Object([self.baseID(), self.rootID(), self.ID])

    def parent(self):
        return self.__parent

    def delete(self):
        self.parent().remove(self)

    def base_node(self):
        return self.root_node().parent()

    def root_node(self):
        return self.parent()

    def baseID(self):
        return self.base_node().ID

    def rootID(self):
        return self.root_node().ID

class RootNode(Node):
    def __init__(self, ID: int, parent, annotations: dict):
        super().__init__()
        self.ID = ID
        self.__parent = parent
        self.annotations = annotations.copy()
        self.annotations.update({'ID_string': self.ID_string()})

        self.__raw_polyline = []
        self.__interpolated_polyline = []
        self.__completed_polyline = []

    def __getitem__(self, key: str):
        for k, v in self.annotations.items():
            if k == key:
                return v
            return None

    def ID_string(self):
        return ID_Object([self.baseID(), self.ID, 0])

    def append(self, annotations, relayID = None, interpolation=True):
        relayID = relayID or self.next_id()
        node = RelayNode(relayID, parent=self, annotations=annotations)
        super().append(node)
        self.__update_registered_pos_list()
        if interpolation:
            self.interpolate_polyline(interpolation_cls=self.RSA_vector().interpolation.get(label=self.RSA_vector().annotations.interpolation()))
            self.complete_polyline()
        else:
            self.__interpolated_polyline = self.annotations['polyline']

        return node.annotations["ID_string"]

    def parent(self):
        return self.__parent

    def base_node(self):
        return self.parent()

    def RSA_vector(self):
        return self.base_node().parent()

    def remove(self, *args, **kwargs):
        super().remove(*args, **kwargs)
        self.__update_registered_pos_list()
        self.interpolate_polyline(interpolation_cls=self.RSA_vector().interpolation.get(label=self.RSA_vector().annotations.interpolation()))
        self.complete_polyline()

    def delete(self):
        del self.__completed_polyline
        self.parent().remove(self)

    def baseID(self):
        return self.base_node().ID

    def child_ID_strings(self):
        return [node.annotations['ID_string'] for node in self]

    def __reorder_polyline(self, polyline: List[List[int]]):
        ordered = []
        ordered.append(polyline.pop(0))
        while(len(polyline) != 0):
            ref_node = np.array(ordered[-1])
            closest_index = np.argmin([np.sum((np.array(node)-ref_node)**2) for node in polyline])
            ordered.append(polyline.pop(closest_index))

        return ordered

    def __update_registered_pos_list(self):
        pos_list = [self.base_node()['coordinate']]
        pos_list.extend([relay_node['coordinate'] for relay_node in self])

        self.__raw_polyline = pos_list
        self.__raw_polyline = self.__reorder_polyline(self.__raw_polyline)

    def RSA_components(self):
        return self.base_node().parent().RSA_components()

    def interpolate_polyline(self, interpolation_cls):
        self.__interpolated_polyline = interpolation_cls(self.RSA_components()).interpolate(self.__raw_polyline)
        self.annotations.update({'polyline': self.__interpolated_polyline})

    def interpolated_polyline(self):
        return self.__interpolated_polyline

    def complete_polyline(self):
        polyline = self.__interpolated_polyline
        polyline_node_count = len(polyline)

        def complete(node1: List[int], node2: List[int]):
            max_dif: int = max([abs(n2-n1) for n1,n2 in zip(node1,node2)])
            return np.stack([np.linspace(node1[i], node2[i], max_dif+1, dtype=np.int32) for i in range(3)]).T.tolist()

        self.__completed_polyline = Polyline()
        
        for i in range(polyline_node_count-1):
            self.__completed_polyline.extend(complete(polyline[i], polyline[i+1]))

    def completed_polyline(self):
        return self.__completed_polyline

    def tip_coordinate(self):
        return self.__raw_polyline[-1]

class BaseNode(Node):
    def __init__(self, ID: int, parent, annotations: dict):
        super().__init__()
        self.ID = ID
        self.__parent = parent
        self.annotations = annotations.copy()
        self.annotations.update({'ID_string': self.ID_string()})

    def __getitem__(self, key: str):
        for k, v in self.annotations.items():
            if k == key:
                return v
            return None

    def parent(self):
        return self.__parent

    def ID_string(self):
        return ID_Object([self.ID, 0, 0])

    def delete(self):
        for root_node in self.child_nodes():
            root_node.delete()

        self.parent().remove(self)

    def append(self, annotations:dict={}, rootID = None):
        rootID = rootID or self.next_id()
        node = RootNode(rootID, parent=self, annotations=annotations)
        super().append(node)
        return node.annotations["ID_string"]

    def child_ID_strings(self):
        return [node['ID_string'] for node in self]

    def child_nodes(self) -> List[RootNode]:
        return [node for node in self]

class RSA_Vector(Node):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.annotations = _Annotations()
        self.__RSA_components = None

    def register_interpolation(self, interpolation):
        self.interpolation = interpolation

    def __getitem__(self, ID_string: ID_Object):
        if ID_string.is_base():
            return self.base_node(ID_string=ID_string)
        if ID_string.is_root():
            return self.root_node(ID_string=ID_string)
        if ID_string.is_relay():
            return self.relay_node(ID_string=ID_string)

    def clear(self):
        super().clear()
        self.annotations = _Annotations()

    def append(self, annotations={}, baseID = None):
        if len(self) != 0:
            raise Exception('Number of base should be 1.')

        baseID = baseID or 1
        node = BaseNode(baseID, parent=self, annotations=annotations)
        super().append(node)
        return node.annotations["ID_string"]

    def base_node_count(self):
        return len(self)

    def base_node(self, baseID: int = 1, ID_string: ID_Object = None) -> Union[BaseNode, None]:
        if ID_string is not None:
            baseID, rootID, relayID = ID_string.split()

        for base_node in self:
            if base_node.ID == baseID:
                return base_node

        return None

    def root_node(self, baseID: int = 1, rootID: int = 1, ID_string: ID_Object = None) -> Union[RootNode, None]:
        if ID_string is not None:
            baseID, rootID, relayID = ID_string.split()

        base_node = self.base_node(baseID=baseID)
        if base_node is None:
            return None

        for root_node in base_node:
            if root_node.ID == rootID:
                return root_node

        return None

    def relay_node(self, baseID: int = 1, rootID: int = 1, relayID: int = 1, ID_string: ID_Object = None) -> Union[RelayNode, None]:
        if ID_string is not None:
            baseID, rootID, relayID = ID_string.split()

        root_node = self.root_node(ID_string=ID_string)
        if root_node is None:
            return None

        for relay_node in root_node:
            if relay_node.ID == relayID:
                return relay_node
        
        return None

    def append_base(self, annotations:dict={}):
        return self.append(annotations=annotations)

    def append_root(self, baseID, annotations:dict={}):
        for node in self:
            if node.ID == baseID:
                return node.append(annotations=annotations)
        return None

    def append_relay(self, baseID, rootID, annotations:dict={}):
        for node in self:
            if node.ID == baseID:
                for node2 in node:
                    if node2.ID == rootID:
                        return node2.append(annotations=annotations)
        return None

    def RSA_components(self):
        return self.__RSA_components

    def register_RSA_components(self, RSA_components):
        self.__RSA_components = RSA_components

    def load_from_file(self, fname: str):
        with open(fname, 'r') as f:
            trace_dict = json.load(f)

        return self.load_from_dict(trace_dict=trace_dict, file=fname)

    def load_from_dict(self, trace_dict: dict = {}, file=''):
        try:
            general_annotations = trace_dict['#annotations']

            version, revision = config.parse_version_string(general_annotations['version'])
            if version < config.version: 
                self.logger.error(f'[Version error] {file}')
                return False

            self.annotations.import_from(general_annotations)

            baseID_list = sorted([int(k) for k in trace_dict.keys() if not k.startswith('#')])

            for baseID in baseID_list:
                base_dict = trace_dict[f'{baseID}']
                ID_string = ID_Object(base_dict['#annotations']['ID_string'])
                self.append(annotations=base_dict['#annotations'], baseID=ID_string.baseID())
                base_node = self.base_node(ID_string=ID_string)
                if base_node is None:
                    continue
                rootID_list = sorted([int(k) for k in base_dict.keys() if not k.startswith('#')])

                for rootID in rootID_list:
                    root_dict = base_dict[f'{rootID}']
                    ID_string = ID_Object(root_dict['#annotations']['ID_string'])
                    base_node.append(annotations=root_dict['#annotations'], rootID=ID_string.rootID())
                    root_node = self.root_node(ID_string=ID_string)
                    if root_node is None:
                        continue
                    relayID_list = sorted([int(k) for k in root_dict.keys() if not k.startswith('#')])

                    for relayID in relayID_list:
                        relay_dict = root_dict[f'{relayID}']
                        ID_string = ID_Object(relay_dict['#annotations']['ID_string'])
                        root_node.append(annotations=relay_dict['#annotations'], interpolation=False, relayID=ID_string.relayID())

                    root_node.complete_polyline()

            self.logger.info(f'[Loading succeeded] {file}')
            return True
        except:
            self.logger.error(f'[Format error] {file}')
            return False

    def save(self, rinfo_file_name: str):
        class encoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return super().default(obj)

        try:
            with open(rinfo_file_name, 'w') as j:
                json.dump(self.dictionary(), j, cls=encoder)
            self.logger.info(f'[Saving succeeded] {rinfo_file_name}')
            return True
        except:
            self.logger.error(f'[Saving failed] {rinfo_file_name}')
            return False

    def iter_all(self) -> Generator[ID_Object, None, None]:
        for base_node in self:
            yield base_node.ID_string()
            for root_node in base_node:
                yield root_node.ID_string()
                for relay_node in root_node:
                    yield relay_node.ID_string()
