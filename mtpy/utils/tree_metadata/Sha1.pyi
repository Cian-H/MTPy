"""An autogenerated submodule.

Contains the code for parsing Sha1 entries in the tree_metadata flatbuffer schema.
"""

from typing import Optional, Type

import flatbuffers
import numpy as np
from numpy.typing import NDArray

class Sha1(object):
    __slots__ = ["_tab"]

    @classmethod
    def SizeOf(cls: Type[Sha1]) -> int:
        """Gets the size of the the Sha1 buffer.

        Args:
            cls (Type[Sha1]): A reference to the Sha1 buffer class

        Returns:
            int: The size of the buffer in bytes
        """
        ...

    def Init(self: "Sha1", buf: bytes, pos: int) -> None:
        """Initialises a new Sha1 class.

        Args:
            self (Sha1): The instance to initialise
            buf (bytes): The buffer to read/write to/from with this class
            pos (int): The position at which to begin reading/writing
        """
        ...

    def Bytearray(self: "Sha1", j: Optional[int] = None) -> Optional[bytearray]:
        """Gets the bytearray field from the current Sha1 buffer.

        Args:
            self (Sha1): The instance to get the tree for
            j (int): The index of the TreeFile to get

        Returns:
            bytearray, Optional: The file at index j in the Tree
        """
        ...

    def BytearrayAsNumpy(self: "Sha1") -> NDArray[np.uint8]:
        """Gets the bytearray field from the current Sha1 buffer.

        Args:
            self (Sha1): The instance to get the tree for

        Returns:
            NDArray[np.uint8], Optional: The file at index j in the Tree
        """
        ...

    def BytearrayLength(self: "Sha1") -> int:
        """Gets the length of the bytearray.

        Args:
            self (Sha1): The instance to get the tree for

        Returns:
            int: the length of the bytearray in bytes
        """
        ...

    def BytearrayIsNone(self: "Sha1") -> bool:
        """Checks if bytearray field in current Sha1 buffer is None.

        Args:
            self (Sha1): The instance to check the bytearray for

        Returns:
            bool: True if bytearray is None else False
        """
        ...

def CreateSha1(builder: flatbuffers.Builder, bytearray: bytes | bytearray) -> int:  # noqa: A002
    """Create a new Sha1 buffer.

    Args:
        builder (flatbuffers.Builder): The flatbuffer Builder object
        bytearray (bytes | bytearray): The bytearray result of the hashing function

    Returns:
        int: an exit code for the flatbuffer builder process
    """
    ...
