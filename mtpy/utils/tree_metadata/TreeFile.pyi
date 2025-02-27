from typing import Optional, Type

import flatbuffers
from tree_metadata.Sha1 import Sha1

class TreeFile(object):
    __slots__ = ["_tab"]

    @classmethod
    def GetRootAs(cls: Type[TreeFile], buf: bytes, offset: int = 0) -> "TreeFile":
        """Gets the root of the flatbuffer as a TreeFile class.

        Args:
            cls (TreeFile): A reference to the TreeFile class
            buf (bytes): The buffer of bytes to write to
            offset (int): The offset at which to start writing

        Returns:
            TreeFile: A reference to the root TreeFile class
        """
        ...

    @classmethod
    def GetRootAsTreeFile(cls: Type[TreeFile], buf: bytes, offset: int = 0) -> "TreeFile":
        """This method is deprecated. Please switch to GetRootAs.

        Args:
            cls (TreeFile): A reference to the TreeFile class
            buf (bytes): The buffer of bytes to write to
            offset (int): The offset at which to start writing

        Returns:
            TreeFile: A reference to the root TreeFile class
        """
        ...

    def Init(self: "TreeFile", buf: bytes, pos: int) -> None:
        """Initialises a new Metadata class.

        Args:
            self (Metadata): The instance to initialise
            buf (bytes): The buffer to read/write to/from with this class
            pos (int): The position at which to begin reading/writing
        """
        ...

    def Filepath(self: "TreeFile") -> Optional[str | bytes]:
        """Gets the filepath field from the current TreeFile buffer.

        Args:
            self (TreeFile): The instance to get the filepath for

        Returns:
            str | bytes, Optional: The filepath of the file
        """
        ...

    def Hash(self: "TreeFile") -> Optional[Sha1]:
        """Gets the hash field from the current TreeFile buffer.

        Args:
            self (TreeFile): The instance to get the hash for

        Returns:
            Sha1, Optional: The hash of the file as a Sha1 flatbuffer
        """
        ...

    def IsDir(self: "TreeFile") -> bool:
        """Gets the isdir field from the current TreeFile buffer.

        Args:
            self (TreeFile): The instance to get the isdir field for

        Returns:
            bool: True if path is a directory, False if a file
        """
        ...

    def Size(self: "TreeFile") -> int:
        """Gets the size of the the TreeFile buffer.

        Args:
            self (TreeFile): A reference to the Sha1 buffer class

        Returns:
            int: The size of the buffer in bytes
        """
        ...

def TreeFileStart(builder: flatbuffers.Builder) -> None:
    """Add an empty TreeFile field to the buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
    """
    ...

def Start(builder: flatbuffers.Builder) -> None:
    """Add an empty TreeFile field to the buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
    """
    ...

def TreeFileAddFilepath(builder: flatbuffers.Builder, filepath: int) -> None:
    """Add a filepath field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        filepath (int): The filepath buffer to add
    """
    ...

def AddFilepath(builder: flatbuffers.Builder, filepath: int) -> None:
    """Add a filepath field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        filepath (int): The filepath buffer to add
    """
    ...

def TreeFileAddHash(builder: flatbuffers.Builder, hash: int) -> None:  # noqa: A002
    """Add a hash field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        hash (int): The hash buffer to add
    """
    ...

def AddHash(builder: flatbuffers.Builder, hash: int) -> None:  # noqa: A002
    """Add a hash field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        hash (int): The hash buffer to add
    """
    ...

def TreeFileAddIsDir(builder: flatbuffers.Builder, isDir: bool) -> None:
    """Add an isdir field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        isDir (bool): The value of isdir to be added
    """
    ...

def AddIsDir(builder: flatbuffers.Builder, isDir: bool) -> None:
    """Add an isdir field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        isDir (bool): The value of isdir to be added
    """
    ...

def TreeFileAddSize(builder: flatbuffers.Builder, size: int) -> None:
    """Add an isdir field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        size (int): The size of the file in bytes
    """
    ...

def AddSize(builder: flatbuffers.Builder, size: int) -> None:
    """Add an isdir field to the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        size (int): The size of the file in bytes
    """
    ...

def TreeFileEnd(builder: flatbuffers.Builder) -> int:
    """Finalize the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object

    Returns:
        int: an exit code for the flatbuffer builder process
    """
    ...

def End(builder: flatbuffers.Builder) -> int:
    """Finalize the TreeFile buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object

    Returns:
        int: an exit code for the flatbuffer builder process
    """
    ...
