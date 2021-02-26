#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import Base
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm.auto import tqdm


class DataLoader(Base):

    def __init__(self,
                 data_path: str = str(Path().cwd()),
                 **kwargs):
        super().__init__(**kwargs)
        self.data_path = data_path  # stores location from which to read data
        # modifiable file extension to search for, in case needed in future
        self.file_extension = "pcd"
        # add eprocess data_path to make more usable
        if self.data_path[-1] != "/":
            self.data_path += "/"
        if self.data_path[0] == "~":
            self.data_path = str(Path().home()) + self.data_path[1:]

    def read_layers(self):
        """Reads layer files into data structure for processing"""
        self._qprint(f"\nSearching for files at {self.data_path}")
        # glob filenames
        pathlist = Path(self.data_path).glob(f"*.{self.file_extension}")
        data_dict = {}
        files = []

        for path in pathlist:
            path_in_str = str(path)
            file = path_in_str.split("/")[-1:][0]
            files.append(file)

        files = sorted(files)

        self._qprint(f"Reading files from {self.data_path}")

        # Read data from files
        for idx, file in tqdm(enumerate(files), total=len(files),
                              disable=self.quiet):
            try:
                df = pd.read_csv(self.data_path + file,
                                 names=["x", "y", "temp", "temp_duplicate"],
                                 header=None, delimiter=" ")

                df.drop(["temp_duplicate"], axis=1, inplace=True)
                df = df.groupby(["x", "y"], sort=False, as_index=False).mean()
                # Corrects for flipped x axis on aconity output
                df["x"] *= -1
                data_dict[idx] = np.asarray(df)
            except:  # noqa
                self._qprint(f"File {file} not found!")

        self.original_data_dict = data_dict
        self.reset_data()

    def reset_data(self):
        """Undoes all data processing that was performed on loaded data"""
        self.data_dict = self.original_data_dict.copy()
