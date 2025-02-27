import io
import lzma
from pathlib import Path
import pickle
import tarfile
from tempfile import TemporaryDirectory

from dask import dataframe as dpd
from dask.distributed import LocalCluster
from mtpy.loaders.csv import CSVLoader

TEST_CLUSTER = LocalCluster(n_workers=1, threads_per_worker=1)


class TestCSVLoader:
    def test_read_layers_regr(self):
        ground = pickle.load(lzma.open(Path(__file__).parent / "loader_test_data.pickle.xz"))
        with TemporaryDirectory() as td:
            td_path = Path(td)
            layers_dir = td_path / "loader_data_csv"
            layers_csv = td_path / "loader_data_csv.csv"
            dir_cache = td_path / "dir_cache"
            csv_cache = td_path / "csv_cache"

            # Test path that loads directly from monolithic csv files
            with open(layers_csv, "wb+") as csv_file:
                csv_file.write(
                    lzma.open(Path(__file__).parent / "csv_test_data.csv.xz").read()
                )
            csv_loader = CSVLoader(data_cache=csv_cache)
            csv_loader.read_layers(str(layers_csv))
            assert dpd.assert_eq(csv_loader.data, ground, check_index=False)

            # Test path that loads from directories containing chunked csv files
            with tarfile.open(
                fileobj=io.BytesIO(
                    lzma.open(
                        Path(__file__).parent / "csv_test_data.tar.xz"
                    ).read()
                ),
                mode="r"
            ) as tar:
                tar.extractall(path=td)
            dir_loader = CSVLoader(data_cache=dir_cache)
            dir_loader.read_layers(str(layers_dir))
            assert dpd.assert_eq(dir_loader.data, ground, check_index=False)
