from mod import (
    ExtensionBackbone,
    InterpolationBackbone,
    RootTraitBackbone,
    RSATraitBackbone,
    _ClassLoader,
)

if __name__ == "__main__":
    backbone_list = [
        RootTraitBackbone,
        RSATraitBackbone,
        InterpolationBackbone,
        ExtensionBackbone,
    ]

    for backbone in backbone_list:
        class_loader = _ClassLoader(backbone=backbone)
        for c in class_loader.class_container:
            print(f"{backbone.__name__}, {c}")
