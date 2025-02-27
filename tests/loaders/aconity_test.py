import io
import lzma
from pathlib import Path
import pickle
import tarfile
from tempfile import TemporaryDirectory

from dask import dataframe as dpd
from dask.distributed import LocalCluster
from mtpy.loaders.aconity import AconityLoader

TEST_CLUSTER = LocalCluster(n_workers=1, threads_per_worker=1)


class TestAconityLoader:
    def test_read_layers_regr(self):
        ground = pickle.load(lzma.open(Path(__file__).parent / "loader_test_data.pickle.xz"))
        with TemporaryDirectory() as td:
            with tarfile.open(
                fileobj=io.BytesIO(
                    lzma.open(
                        Path(__file__).parent / "aconity_test_data.tar.xz"
                    ).read()
                ),
                mode="r"
            ) as tar:
                tar.extractall(path=td)
            td_path = Path(td)
            layers = td_path / "loader_data_aconity"
            cache = td_path / "cache"
            loader = AconityLoader(data_cache=cache)
            loader.read_layers(str(layers))
            assert dpd.assert_eq(loader.data, ground, check_index=False)
