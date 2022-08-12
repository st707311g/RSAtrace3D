import os
from typing import ClassVar, List

from DATA import RSA_Vector


class ModuleTest(object):
    def __init__(self, module_class=None):
        rinfo_dir = os.path.join(os.path.dirname(__file__), "__test_rinfo__")
        assert os.path.isdir(rinfo_dir)

        rinfo_files = [
            f for f in os.listdir(rinfo_dir) if f.lower().endswith(".rinfo")
        ]
        rinfo_files.sort()

        self.rsa_vector_list: List[RSA_Vector] = []
        for f in rinfo_files:
            rsa_vector = RSA_Vector()
            try:
                rsa_vector.load_from_file(os.path.join(rinfo_dir, f))
                self.rsa_vector_list.append(rsa_vector)
            except:
                pass

        if module_class is not None:
            self.apply(module_class=module_class)

    def apply(self, module_class):
        print(f"** calculation test: {module_class.label} **")

        for rsa_vector in self.rsa_vector_list:
            print(
                f"calculation results: {rsa_vector.annotations.volume_name()}"
            )
            if module_class.class_type == "root":
                for ID_string in rsa_vector.iter_all():
                    ins = module_class(
                        RSA_vector=rsa_vector, ID_string=ID_string
                    )
                    calc_result = ins.str_value()
                    print(f"{ID_string=}, {calc_result=}")
            elif module_class.class_type == "RSA":
                ins = module_class(RSA_vector=rsa_vector)
                calc_result = ins.str_value()
                print(f"{calc_result=}")
