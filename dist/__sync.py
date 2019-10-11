def _get_file_crc32(file_path):
    import binascii

    def mycrc32(szString):
        m_pdwCrc32Table = [0 for x in range(0, 256)]
        dwPolynomial = 0xEDB88320
        dwCrc = 0
        for i in range(0, 255):
            dwCrc = i
            for j in [8, 7, 6, 5, 4, 3, 2, 1]:
                if dwCrc & 1:
                    dwCrc = (dwCrc >> 1) ^ dwPolynomial
                else:
                    dwCrc >>= 1
            m_pdwCrc32Table[i] = dwCrc
        dwCrc32 = 0xFFFFFFFF
        for i in szString:
            b = ord(i)
            dwCrc32 = ((dwCrc32) >> 8) ^ m_pdwCrc32Table[(b) ^ ((dwCrc32) & 0x000000FF)]
        dwCrc32 = dwCrc32 ^ 0xFFFFFFFF
        return '%x' % (dwCrc32)

    try:
        with open(file_path, "rb") as infile:
            ucrc = infile.read()
            ucrc = binascii.b2a_base64(ucrc)
        return mycrc32(ucrc.decode())
    except:
        print("file crc calc error.\r\n")
        return ''
