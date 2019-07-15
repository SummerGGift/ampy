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

name = 'name'
md5 = 'md5'

def get_pc_dir_info(path):
    result = []
    paths = os.listdir(path)
    for i, item in enumerate(paths):
        sub_path = os.path.join(path, item)
        if os.path.isdir(sub_path):
            file_info = {}
            file_info[name] = os.path.join(path[len(local) - 1:], item).replace('\\', '/')
            file_info[md5] = 'dir'
            result.append(file_info)
            result += get_pc_dir_info(sub_path + '/')
        else:
            myhash = hashlib.md5()
            f = open(sub_path,'rb')
            while True:
                b = f.read(8096)
                if not b :
                    break
                myhash.update(b)
            f.close()
            file_info = {}
            file_info[name] = os.path.join(path[len(local) - 1 :], item).replace('\\', '/')
            file_info[md5] = str(myhash.hexdigest())
            result.append(file_info)
    return result

def get_sync_info(pc_info, dev_info):
    sync_info = {}
    delete_list = []
    sync_list = []
    temp = {}

    for filename, md5 in pc_info.items():
        # print(filename, md5)
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

def file_sync_info(local_path, remote_path):

    global local
    local = os.path.basename(local_path.replace('\\', '/'))   
    pc_file_info = {}
    dev_file_info = {}

    pc_info = get_pc_dir_info(local_path)

    for item in pc_info:
        pc_file_info[item["name"]] = item["md5"]

    with open("file_info.json", 'r') as f:
        dev_file_info = f.read()

    return get_sync_info(pc_file_info, eval(dev_file_info))



