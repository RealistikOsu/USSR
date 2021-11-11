# Binary Serialisation lib.
import struct
from typing import Union

class BinaryWriter:
    """A binary writer used for serialisation. Primarily includes osu!'s types."""

    def __init__(self) -> None:
        self.buffer = bytearray()
    
    def write_uleb128(self, value: int) -> None:
        """Write a uleb128 value to the buffer."""
        while value > 0x7F:
            self.buffer.append(value | 0x80)
            value >>= 7
        self.buffer.append(value)
    
    def write_u64_le(self, value: int) -> None:
        """Write a 64-bit unsigned integer to the buffer."""
        self.buffer += struct.pack("<Q", value)
    
    def write_i64_le(self, value: int) -> None:
        """Write a 64-bit integer to the buffer."""
        self.buffer += struct.pack("<q", value)
    
    def write_i32_le(self, value: int) -> None:
        """Write a 32-bit integer to the buffer."""
        self.buffer += struct.pack("<i", value)
    
    def write_u32_le(self, value: int) -> None:
        """Write a 32-bit unsigned integer to the buffer."""
        self.buffer += struct.pack("<I", value)
    
    def write_i16_le(self, value: int) -> None:
        """Write a 16-bit integer to the buffer."""
        self.buffer += struct.pack("<h", value)
    
    def write_u16_le(self, value: int) -> None:
        """Write a 16-bit unsigned integer to the buffer."""
        self.buffer += struct.pack("<H", value)
    
    def write_i8_le(self, value: int) -> None:
        """Write a 8-bit integer to the buffer."""
        self.buffer += struct.pack("<b", value)
    
    def write_u8_le(self, value: int) -> None:
        """Write a 8-bit unsigned integer to the buffer."""
        self.buffer += struct.pack("<B", value)
    
    def write_raw(self, data: Union[bytes, bytearray]) -> None:
        """Write raw data to the buffer."""
        self.buffer += data
    
    def write_osu_string(self, string: str) -> None:
        """Write an osu! protocol style string.
        
        An osu! protocol string consists of an 'exists' byte, followed 
        by a uleb128 length, followed by the string itself.
        """
        if string:
            self.buffer += b"\x0B"
            self.write_uleb128(len(string))
            self.write_raw(string.encode("utf-8"))
        else: self.buffer += b"\x00"
