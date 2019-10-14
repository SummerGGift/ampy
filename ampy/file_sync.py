#
# Copyright (c) 2006-2019, RT-Thread Development Team
#
# SPDX-License-Identifier: MIT License
#
# Change Logs:
# Date           Author       Notes
# 2019-07-15     SummerGift   first version
#

import os
import hashlib
import binascii


def get_file_hash(file_path):
    myhash = hashlib.md5()
    f = open(file_path, 'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        myhash.update(b)
    f.close()
    return str(myhash.hexdigest())


def big_small_end_convert(data):
    tmp0 = data[:2]
    tmp1 = data[2:4]
    tmp2 = data[4:6]
    tmp3 = data[6:8]

    value = tmp3 + tmp2 + tmp1 + tmp0
    return value


def get_file_crc32(file_path):
    try:
        with open(file_path, "rb") as infile:
            ucrc = binascii.crc32(infile.read())

        if ucrc > 0:
            uoutint = ucrc
        else:
            uoutint = ~ ucrc ^ 0xffffffff
        return '%x' % (uoutint)
    except:
        print("crc calc error.\r\n")
        return ''
        print("error")


def _get_file_crc32(file_path):
    import binascii

    def mycrc32(szString, dwCrc32):
        m_pdwCrc32Table = [0 for x in range(0, 256)]
        dwPolynomial = 0xEDB88320
        dwCrc = 0
        dwCrc32 = dwCrc32 ^ 0xFFFFFFFF

        for i in range(0, 255):
            dwCrc = i
            for j in [8, 7, 6, 5, 4, 3, 2, 1]:
                if dwCrc & 1:
                    dwCrc = (dwCrc >> 1) ^ dwPolynomial
                else:
                    dwCrc >>= 1
            m_pdwCrc32Table[i] = dwCrc

        for i in szString:
            b = ord(i)
            dwCrc32 = ((dwCrc32) >> 8) ^ m_pdwCrc32Table[(b) ^ ((dwCrc32) & 0x000000FF)]
        dwCrc32 = dwCrc32 ^ 0xFFFFFFFF
        return dwCrc32

    with open(file_path, "rb") as infile:
        file_crc_value = 0xFFFFFFFF
        while True:
            ucrc = infile.read(500)
            if len(ucrc) == 0:
                break
            ucrc = binascii.b2a_base64(ucrc)
            file_crc_value = mycrc32(ucrc.decode(), file_crc_value)

    return ('%x' % (file_crc_value))

def get_pc_dir_info(path, rtt_version):
    result = []

    for root, dirs, files in os.walk(path, topdown=False):

        for name in files:
            file_info = {}
            file_key = os.path.join(root, name)[len(path) + 1:].replace('\\', '/')
            file_info['name'] = file_key

            if rtt_version:
                big_small = get_file_crc32(os.path.join(root, name)).upper()
            else:
                big_small = _get_file_crc32(os.path.join(root, name)).upper()

            if len(big_small) == 8:
                convert_value = big_small_end_convert(big_small).upper()
            else:
                convert_value = "Invalid"

            file_info['md5'] = convert_value
            result.append(file_info)

        for name in dirs:
            file_info = {}
            file_key = os.path.join(root, name)[len(path) + 1:].replace('\\', '/')
            file_info['name'] = file_key
            file_info['md5'] = 'dir'
            result.append(file_info)

    return result


def get_sync_info(pc_info, dev_info):
    sync_info = {}
    delete_list = []
    sync_list = []
    temp = {}

    # print("pcinfo：%s"%pc_info)
    # print("dev_info:%s"%dev_info)

    for filename, md5 in pc_info.items():
        if filename in dev_info.keys():         # If the file exists on both the PC and device side
            if md5 == 'dir':
                continue
            else:
                if md5 == dev_info[filename]:
                    continue
                else:
                    sync_list.append(filename)
        else:
            if md5 == 'dir':
                continue
            else:
                sync_list.append(filename)

    for filename, md5 in dev_info.items():
        if filename in pc_info.keys():           # If the file exists on both the PC and device side
            continue
        else:
            delete_list.append(filename)

    sync_info['delete'] = delete_list
    sync_info['sync'] = sync_list

    # print(sync_info)
    return sync_info

def file_sync_info(local_path, info_pathname, rtt_version):

    pc_file_info = {}
    dev_file_info = {}

    pc_info = get_pc_dir_info(local_path, rtt_version)

    for item in pc_info:
        pc_file_info[item["name"]] = item["md5"]

    with open(info_pathname, 'r') as f:
        dev_file_info = f.read()

    return get_sync_info(pc_file_info, eval(dev_file_info)), pc_file_info

