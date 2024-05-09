import lzma
from pathlib import Path
import pickle
from tempfile import TemporaryDirectory

from dask import dataframe as dpd
from dask.distributed import LocalCluster
from hypothesis import given, settings
from hypothesis.extra import pandas as hpd
from mtpy.loaders.abstract import AbstractLoader
import numpy as np
import pandas as pd

TEST_CLUSTER = LocalCluster(n_workers=1, threads_per_worker=1)


test_dfs = hpd.data_frames(
    (
        hpd.column("x", dtype=np.float64),
        hpd.column("y", dtype=np.float64),
        hpd.column("z", dtype=np.float64),
        hpd.column("t", dtype=np.float64),
    )
)


class Loader(AbstractLoader):
    def construct_cached_ddf(self: "Loader", data_path: str, chunk_size: int = 3276800) -> None:
        pass


class TestAbstractLoader:
    @staticmethod
    def create_loader(df):
        l = Loader(cluster=TEST_CLUSTER)
        l.data = dpd.from_pandas(df)
        l.read_layers("/")
        return l

    @staticmethod
    def cal_curve1(x, y, z, t):
        return x + y + z + t

    @staticmethod
    def cal_curve2(x, y, z, t):
        return x * y * z * t

    @staticmethod
    def cal_curve3(x, y, z, t):
        return 2 * t

    @settings(deadline=None)
    @given(test_dfs)
    def test_apply_calibration_curve_hyp(self, df):
        l = self.create_loader(df)
        l.apply_calibration_curve(self.cal_curve1)
        l.apply_calibration_curve(self.cal_curve2)
        l.apply_calibration_curve(self.cal_curve3)

    def test_apply_calibration_curve_regr(self):
        l = self.create_loader(
            df=pd.DataFrame(
                data=np.arange(-1_000_000.0, 1_000_000.0, 0.1).reshape(-1, 4),
                columns=["x", "y", "z", "t"],
            )
        )
        ground1, ground2, ground3 = pickle.load(lzma.open(Path(__file__).parent / "data.pickle.xz"))
        d0 = l.data.copy()
        l.apply_calibration_curve(calibration_curve=self.cal_curve1)
        assert (l.data["t"].compute() == ground1).all()
        l.data = d0.copy()
        l.apply_calibration_curve(calibration_curve=self.cal_curve2)
        assert (l.data["t"].compute() == ground2).all()
        l.data = d0.copy()
        l.apply_calibration_curve(calibration_curve=self.cal_curve3)
        assert (l.data["t"].compute() == ground3).all()

    @given(test_dfs)
    def test_commit(self, df):
        with TemporaryDirectory() as td:
            l = self.create_loader(df)
            l._data_cache = td
