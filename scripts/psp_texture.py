"""4bpp PSP swizzle for the observed square 256/512 font texture profiles."""
def decode_4bpp(data, width):
    if width not in (256, 512) or len(data) != width * width // 2:
        raise ValueError('Unsupported dimensions or truncated texture')
    pixels = bytearray(width * width)
    for y in range(width):
        for x in range(width):
            byte_x = x // 2
            pos = (y // 8) * (width * 4) + (byte_x // 16) * 128 + (y % 8) * 16 + byte_x % 16
            pixels[y * width + x] = (data[pos] >> (4 * (x % 2))) & 15
    return pixels

def encode_4bpp(pixels, width):
    if width not in (256, 512) or len(pixels) != width * width or any(p > 15 for p in pixels):
        raise ValueError('Unsupported dimensions, length or palette index')
    out = bytearray()
    for by in range(width // 8):
        for bx in range(width // 32):
            for line in range(8):
                row = (by * 8 + line) * width + bx * 32
                for pair in range(16):
                    out.append(pixels[row + pair * 2] | pixels[row + pair * 2 + 1] << 4)
    return bytes(out)
