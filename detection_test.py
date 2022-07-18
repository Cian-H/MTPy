from julia import Main
from MTPy.mtpy import MeltpoolTomography
import numpy as np
from matplotlib import pyplot as plt
import plotly.express as px
from pathlib import Path

# Include the julia module
Main.include("raster_detection.jl")
rd = Main.raster_detection

if __name__ == "__main__":
    # path to location with datafiles
    dir_path = "~/test_data/layers"
    cwd = Path().cwd()
    dump = f"{str(cwd)}/mptdump"
    # Figure parameters
    width = 19200
    height = 10800
    dpi = 1000
    markersize = 1
    # Prepare mpt object
    mpt = MeltpoolTomography(data_path=dir_path)
    if dump not in (str(x) for x in cwd.iterdir()):
        # Read the data files at dir_path
        mpt.read_layers()
        mpt.dump(dump)
    else:
        mpt.undump(dump)
    # Then plot to confirm success
    data = mpt.data_dict[3.24]
    # Test of collapse coverticals and interactive plot of result
    # data_cc = rd.collapse_coverticals(data)[0]
    # fig = px.scatter(x=data_cc[:, 0], y=data_cc[:, 1])
    # fig.show()
    # exit()
    # Tests of turning point and sample splitting algorithms
    out1 = rd.test1(mpt.data_dict)
    out2 = rd.test2(mpt.data_dict)
    out1_corrected = out1 - 1
    out2_corrected = out2 - 1
    turningpoints = data[out1_corrected, :]
    splitpoints = data[out2_corrected, :]
    plt.scatter(data[:, 0], data[:, 1], s=markersize)
    plt.scatter(turningpoints[:, 0], turningpoints[:, 1], s=markersize)
    plt.savefig("output1.png", figsize=(width/dpi, height/dpi), dpi=dpi)
    plt.clf()
    plt.scatter(data[:, 0], data[:, 1], s=markersize)
    plt.scatter(splitpoints[:, 0], splitpoints[:, 1], s=markersize)
    plt.savefig("output2.png", figsize=(width/dpi, height/dpi), dpi=dpi)
    plt.clf()
    # Plots every second slice of dataset based on splitpoints
    separated1 = np.concatenate([data[out2_corrected[i]:out2_corrected[i+1], :]
                                for i in list(range(0, len(splitpoints)-1, 2))]
                                )
    separated2 = np.concatenate([data[out2_corrected[i]:out2_corrected[i+1], :]
                                for i in list(range(1, len(splitpoints), 2))]
                                )
    plt.scatter(separated1[:, 0], separated1[:, 1], s=markersize)
    plt.savefig("output3.png", figsize=(width/dpi, height/dpi), dpi=dpi)
    plt.clf()
    plt.scatter(separated2[:, 0], separated2[:, 1], s=markersize)
    plt.savefig("output4.png", figsize=(width/dpi, height/dpi), dpi=dpi)
    plt.clf()

# Test 1:
# 277.440952 seconds (5.61 M allocations: 1.643 TiB, 2.83% gc time, 0.12% compilation time)
# (4778,)
# Plot: Success
# Test 2:
# 299.192057 seconds (7.73 M allocations: 1.643 TiB, 3.84% gc time, 0.90% compilation time)
# (4778,)
# ROLLBACK
# Test 3:
# 0.328630 seconds (2.75 M allocations: 353.188 MiB, 20.15% gc time, 10.59% compilation time)
# (4778,)
