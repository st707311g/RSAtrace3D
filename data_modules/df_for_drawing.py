from copy import deepcopy

import numpy as np
import polars as pl
from skimage.morphology import ball


def get_dilate_df(df: pl.DataFrame, target_np_volume: np.ndarray):
    volume_shape = target_np_volume.shape[:3]

    def get_ofset_list(radius: int):
        b = ball(radius=radius)
        b[1:-1, 1:-1, 1:-1][ball(radius=radius - 1) == 1] = 0
        offset_list = np.array(np.where(b == 1))
        offset_list = [
            [z - b.shape[0] // 2, y - b.shape[1] // 2, x - b.shape[2] // 2]
            for z, y, x in zip(*offset_list)
        ]

        return offset_list

    resulting_df_list = [deepcopy(df)]

    for target_size in range(1, df["size"].max() + 1):
        for offset in get_ofset_list(radius=target_size):
            offset_z, offset_y, offset_x = offset

            offset_df_subset = (
                df.filter(pl.col("size") >= target_size)
                .with_column(pl.col("z") + offset_z)
                .with_column(pl.col("y") + offset_y)
                .with_column(pl.col("x") + offset_x)
            )

            resulting_df_list.append(offset_df_subset)

    resulting_df = (
        pl.concat(resulting_df_list)
        .unique(subset=["z", "y", "x"])
        .filter(pl.col("z") >= 0)
        .filter(pl.col("y") >= 0)
        .filter(pl.col("x") >= 0)
        .filter(pl.col("z") < volume_shape[0])
        .filter(pl.col("y") < volume_shape[1])
        .filter(pl.col("x") < volume_shape[2])
    )

    return resulting_df
