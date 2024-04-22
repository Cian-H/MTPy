from hypothesis import given
from hypothesis import strategies as hs
import hypothesis.extra.numpy as hnp
from tempfile import TemporaryDirectory
from mtpy.base.feedback.dummy import DummyLogger, DummyProgressBar
from mtpy.loaders.aconity import AconityLoader
import numpy as np

array_generator = hs.integers(0, 1_000_000).flatmap(
    lambda n: hnp.arrays(np.int64, (n, 4))
)


@given(array_generator, hs.integers(1, 3276800))
def test_read_layers(ar, chunk_size):
    with TemporaryDirectory() as tmp_dir:
        datafile = f"{tmp_dir}/data.pcd"
        np.savetxt(datafile, ar, delimiter=" ", fmt="%i")
        loader = AconityLoader(data_cache=f"{tmp_dir}/cache")
        loader.progressbar = DummyProgressBar
        loader.read_layers(datafile, chunk_size=chunk_size)
        assert (loader.data == ar).all().compute()
