# automatically generated by the FlatBuffers compiler, do not modify

# namespace: tree_metadata

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class Sha1(object):
    __slots__ = ['_tab']

    @classmethod
    def SizeOf(cls):
        return 20

    # Sha1
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # Sha1
    def Bytearray(self, j = None):
        if j is None:
            return [self._tab.Get(flatbuffers.number_types.Uint8Flags, self._tab.Pos + flatbuffers.number_types.UOffsetTFlags.py_type(0 + i * 1)) for i in range(self.BytearrayLength())]
        elif j >= 0 and j < self.BytearrayLength():
            return self._tab.Get(flatbuffers.number_types.Uint8Flags, self._tab.Pos + flatbuffers.number_types.UOffsetTFlags.py_type(0 + j * 1))
        else:
            return None

    # Sha1
    def BytearrayAsNumpy(self):
        return self._tab.GetArrayAsNumpy(flatbuffers.number_types.Uint8Flags, self._tab.Pos + 0, self.BytearrayLength())

    # Sha1
    def BytearrayLength(self):
        return 20

    # Sha1
    def BytearrayIsNone(self):
        return False


def CreateSha1(builder, bytearray):
    builder.Prep(1, 20)
    for _idx0 in range(20 , 0, -1):
        builder.PrependUint8(bytearray[_idx0-1])
    return builder.Offset()
