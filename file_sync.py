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

def get_file_hash(file_path):
    myhash = hashlib.md5()
    f = open(file_path,'rb')
    while True:
        b = f.read(8096)
        if not b :
            break
        myhash.update(b)
    f.close()
    return str(myhash.hexdigest())

def get_pc_dir_info(path):
    result = []

    for root, dirs, files in os.walk(path, topdown=False):

        for name in files:
            file_info = {}
            file_key = os.path.join(root, name)[len(path) + 1:].replace('\\', '/')
            file_info['name'] = file_key
            file_info['md5'] = get_file_hash(os.path.join(root, name))
            result.append(file_info)

        for name in dirs:
            file_info = {}
            file_key = os.path.join(root, name)[len(path) + 1:].replace('\\', '/')
            file_info['name'] = file_key
            file_info['md5'] = 'dir'

    return result

def get_sync_info(pc_info, dev_info):
    sync_info = {}
    delete_list = []
    sync_list = []
    temp = {}

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

    return sync_info

def file_sync_info(local_path, info_pathname):

    pc_file_info = {}
    dev_file_info = {}

    pc_info = get_pc_dir_info(local_path)

    for item in pc_info:
        pc_file_info[item["name"]] = item["md5"]

    with open(info_pathname, 'r') as f:
        dev_file_info = f.read()

    return get_sync_info(pc_file_info, eval(dev_file_info))



