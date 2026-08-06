from unittest.mock import MagicMock

import dask.dataframe as dd
import numpy as np
import pandas as pd

from mtpy.proc.processor import Processor


def test_annotator_processor():
    # Create test x, y raster data
    x = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    y = np.array([0.0, 1.0, 2.0, 2.0, 1.0, 0.0, 0.0, 1.0, 2.0], dtype=np.float64)
    pdf = pd.DataFrame({"x": x, "y": y})
    ddf = dd.from_pandas(pdf, npartitions=2)

    mock_loader = MagicMock()
    mock_loader.data = ddf
    mock_loader.logger = MagicMock()

    processor = Processor(loader=mock_loader)
    processor.annotate_scanlines(x_col="x", y_col="y", output_col="scanline_id")

    result_df = mock_loader.data.compute()
    assert "scanline_id" in result_df.columns
    assert result_df["scanline_id"].dtype == np.int32
    assert len(result_df) == len(x)
