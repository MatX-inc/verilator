# DESCRIPTION: Verilator: Verilog Test driver/expect definition
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of either the GNU Lesser General Public License Version 3
# or the Perl Artistic License Version 2.0.
# SPDX-FileCopyrightText: 2026 Wilson Snyder
# SPDX-License-Identifier: LGPL-3.0-only OR Artistic-2.0

import ctypes
import struct
import zlib


def fst_scope_components(test, filename):
    """Parse the FST hierarchy block and return {dotted scope path: component}.

    The scope component (module definition name) is dropped by VCD conversion
    (fst2vcd, wavediff), so read the FST binary directly."""

    def lz4_decompress(data, dstlen):
        for so in ('liblz4.so.1', 'liblz4.so', 'lz4'):
            try:
                lib = ctypes.CDLL(so)
                break
            except OSError:
                continue
        else:
            test.error("liblz4 not found for FST hierarchy decompression")
        dst = ctypes.create_string_buffer(dstlen)
        n = lib.LZ4_decompress_safe(data, dst, len(data), dstlen)
        if n < 0:
            test.error("lz4 decompression of FST hierarchy failed")
        return dst.raw[:n]

    # Find and decompress the hierarchy block
    with open(filename, "rb") as fh:
        blob = fh.read()
    hier = None
    pos = 0
    while pos < len(blob):
        sectype = blob[pos]
        seclen = struct.unpack(">Q", blob[pos + 1:pos + 9])[0]
        body = blob[pos + 9:pos + 1 + seclen]
        if sectype == 4:  # FST_BL_HIER, zlib
            hier = zlib.decompress(body[8:])
        elif sectype == 6:  # FST_BL_HIER_LZ4
            ulen = struct.unpack(">Q", body[:8])[0]
            hier = lz4_decompress(body[8:], ulen)
        elif sectype == 7:  # FST_BL_HIER_LZ4DUO
            ulen = struct.unpack(">Q", body[:8])[0]
            clen = struct.unpack(">Q", body[8:16])[0]
            hier = lz4_decompress(lz4_decompress(body[16:], clen), ulen)
        if hier is not None:
            break
        pos += 1 + seclen
    if hier is None:
        test.error("no hierarchy block found in " + filename)

    def cstr(buf, i):
        j = buf.index(b"\0", i)
        return buf[i:j].decode("latin-1"), j + 1

    def varint(buf, i):
        value = shift = 0
        while True:
            b = buf[i]
            i += 1
            value |= (b & 0x7F) << shift
            if not b & 0x80:
                return value, i
            shift += 7

    # Walk the hierarchy records, collecting scope components
    scopes = {}
    stack = []
    i = 0
    while i < len(hier):
        tag = hier[i]
        i += 1
        if tag == 254:  # FST_ST_VCD_SCOPE
            i += 1  # scope type
            name, i = cstr(hier, i)
            comp, i = cstr(hier, i)
            stack.append(name)
            scopes[".".join(stack)] = comp
        elif tag == 255:  # FST_ST_VCD_UPSCOPE
            stack.pop()
        elif tag == 252:  # FST_ST_GEN_ATTRBEGIN
            i += 2  # attr type, subtype
            _, i = cstr(hier, i)
            _, i = varint(hier, i)
        elif tag == 253:  # FST_ST_GEN_ATTREND
            pass
        else:  # variable
            i += 1  # direction
            _, i = cstr(hier, i)
            _, i = varint(hier, i)  # length
            _, i = varint(hier, i)  # alias
    return scopes
