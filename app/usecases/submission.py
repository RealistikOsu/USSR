from __future__ import annotations

from typing import SupportsInt

class OverflowInt:
    """A class that allows the simulation of overflowing in Python."""
    
    __slots__ = (
        "_value",
        "_frame",
    )
    
    def __init__(self, bits: int, value: int = 0) -> None:
        if bits <= 1:
            raise ValueError("You may only have integers with more than 1 bit.")
        self._value = value
        self._frame = 0b1
        
        for _ in range(bits - 1):
            self._frame <<= 1
            self._frame |= 0b1
    
    def __str__(self) -> str:
        return str(self._value)
    
    def __repr__(self) -> str:
        return f"<OverflowInt({self._value}, {bin(self._frame)})>"

    def __int__(self) -> int:
        return self._value
    
    def __bool__(self) -> bool:
        return bool(self._value)
    
    def __index__(self) -> int:
        return self._value
    
    def __iadd__(self, val: SupportsInt) -> OverflowInt:
        self._value += int(val)
        self.__enforce_frame()
        return self
    
    def __ior__(self, val: SupportsInt) -> OverflowInt:
        self._value |= int(val)
        self.__enforce_frame()
        return self
    
    def __iand__(self, val: SupportsInt) -> OverflowInt:
        # No need to enforce frame here as it was alr enforced before
        # and this wont make it any larger
        self._value &= int(val)
        return self
    
    def __ilshift__(self, val: SupportsInt) -> OverflowInt:
        self._value <<= int(val)
        self.__enforce_frame()
        return self
    
    def __irshift__(self, val: SupportsInt) -> OverflowInt:
        self._value >>= int(val)
        return self
    
    def __ixor__(self, val: SupportsInt) -> OverflowInt:
        self._value ^= int(val)
        self.__enforce_frame()
        return self
    
    def __enforce_frame(self) -> None:
        """Forces the value to fit within the initially specified bits."""
        
        self._value &= self._frame
    
    def bits(self) -> int:
        """Calculates the capacity of the integer."""
        
        res = 0
        frame_cpy = self._frame
        while frame_cpy & 0b1:
            res += 1
            frame_cpy >>= 1
        return res

DELTA = 0x9e3779b9

def encrypt_xxtea(buffer: bytearray, key: bytearray) -> None:
    """Encrypts the buffer using osu's variant of XXTEA."""
    
    n_max = 16
    n_max_bytes = n_max * 4
    buff_len = len(buffer)
    
    
    word_count = OverflowInt(
        32,
        buff_len // n_max_bytes
    )
    leftover = OverflowInt(
        32,
        buff_len % n_max_bytes
    )
    
    rounds = 6 + (52 // n_max)
    
    buff_ptr = 0
    
    for _ in range(word_count):
        y = z = sum = p = e = 0
        z = buffer[buff_ptr + n_max - 1]
        for _ in range(rounds):
            sum += DELTA
            e = (sum >> 2) & 3;
            
            for p in range(n_max):
                y = buffer[buff_ptr + p + 1]
                buffer[buff_ptr + p] += ((z>>5^y<<2) + (y>>3^z<<4)) ^ ((sum^y) + (key[(p&3)^e] ^ z))
                z = buffer[buff_ptr + p]
            
            y = buffer[buff_ptr]
            buffer[buff_ptr + n_max - 1] += ((z>>5^y<<2) + (y>>3^z<<4)) ^ ((sum^y) + (key[(p&3)^e] ^ z))
            z = buffer[buff_ptr + n_max - 1]
        
        buff_ptr += n_max
        
    if not leftover:
        return
    # TODO: Handle leftovers
    