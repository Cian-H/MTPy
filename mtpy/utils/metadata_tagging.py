"""A module for adding and reading metadata tags to and from files."""

from fsspec.spec import AbstractFileSystem
import h5py

from mtpy.utils.hdf5_operations import read_bytes_from_hdf_dataset
from mtpy.utils.tree_metadata import Metadata
from mtpy.utils.types import PathMetadataTree


def read_tree_metadata(fs: AbstractFileSystem, filepath: str) -> PathMetadataTree:
    """Reads cache tree metadata from HDF5 file.

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        filepath (str): The path to the HDF5 file to read from.

    Returns:
        PathMetadataTree: A typed dict containing tree metadata for the cache path.
    """
    with h5py.File(fs.open(filepath), "r", swmr=True) as f:
        meta = read_bytes_from_hdf_dataset(f["cache"]["metadata"])
    mbuffer = Metadata.Metadata.GetRootAs(meta, 0)
    meta_dict = {"size": mbuffer.Size(), "tree": (tree_meta := {})}
    if not mbuffer.TreeIsNone():
        for i in range(mbuffer.TreeLength()):
            tree_entry = mbuffer.Tree(i)
            if tree_entry is None:
                continue
            path = tree_entry.Filepath()
            if path is None:
                continue
            if isinstance(path, bytes):
                path = path.decode()
            entry_hash = tree_entry.Hash()
            entry_hash_bytes = bytes() if entry_hash is None else entry_hash.Bytearray()
            tree_meta[path] = {
                "is_dir": tree_entry.IsDir(),
                "size": tree_entry.Size(),
                "hash": int.from_bytes(entry_hash_bytes),
            }

    from mtpy.utils.type_guards import guarded_pathmetadatatree

    return guarded_pathmetadatatree(meta_dict)
