# Adafruit MicroPython Tool - File Operations
# Author: Tony DiCola
# Copyright (c) 2016 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import ast
import textwrap
import json

from ampy.pyboard import PyboardError


BUFFER_SIZE = 32  # Amount of data to read or write to the serial port at a time.
# This is kept small because small chips and USB to serial
# bridges usually have very small buffers.


class DirectoryExistsError(Exception):
    pass


class Files(object):
    """Class to interact with a MicroPython board files over a serial connection.
    Provides functions for listing, uploading, and downloading files from the
    board's filesystem.
    """

    def __init__(self, pyboard):
        """Initialize the MicroPython board files class using the provided pyboard
        instance.  In most cases you should create a Pyboard instance (from
        pyboard.py) which connects to a board over a serial connection and pass
        it in, but you can pass in other objects for testing, etc.
        """
        self._pyboard = pyboard

    def get(self, filename):
        """Retrieve the contents of the specified file and return its contents
        as a byte string.
        """
        # Open the file and read it a few bytes at a time and print out the
        # raw bytes.  Be careful not to overload the UART buffer so only write
        # a few bytes at a time, and don't use print since it adds newlines and
        # expects string data.
        command = """
            import sys
            with open('{0}', 'rb') as infile:
                while True:
                    result = infile.read({1})
                    if result == b'':
                        break
                    len = sys.stdout.write(result)
        """.format(
            filename, BUFFER_SIZE
        )
        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command), "get")
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. file doesn't exist and
            # rethrow it as something more descriptive.
            if ex.args[2].decode("utf-8").find("OSError: [Errno 2] ENOENT") != -1:
                raise RuntimeError("No such file: {0}".format(filename))
            else:
                raise ex
        self._pyboard.exit_raw_repl()
        return out

    def ls(self, directory="/", long_format=True, recursive=False, pathname=None):
        """List the contents of the specified directory (or root if none is
        specified).  Returns a list of strings with the names of files in the
        specified directory.  If long_format is True then a list of 2-tuples
        with the name and size (in bytes) of the item is returned.  Note that
        it appears the size of directories is not supported by MicroPython and
        will always return 0 (i.e. no recursive size computation).
        """

        # Make sure directory starts with slash, for consistency.
        if not directory.startswith("/"):
            directory = "/" + directory

        command = """\
                try:        
                    import os
                    import gc
                except ImportError:
                    import uos as os\n"""

        if recursive:
            command += """\
                def listdir(directory):
                    result = set()

                    def _listdir(dir_or_file):
                        try:
                            # if its a directory, then it should provide some children.
                            children = os.listdir(dir_or_file)
                        except OSError:                        
                            # probably a file. run stat() to confirm.
                            os.stat(dir_or_file)
                            result.add(dir_or_file) 
                        else:
                            # probably a directory, add to result if empty.
                            if children:
                                # queue the children to be dealt with in next iteration.
                                for child in children:
                                    # create the full path.
                                    if dir_or_file == '/':
                                        next = dir_or_file + child
                                    else:
                                        next = dir_or_file + '/' + child
                                    
                                    _listdir(next)
                            else:
                                result.add(dir_or_file)                     

                    _listdir(directory)
                    gc.collect()
                    return sorted(result)\n"""
        else:
            command += """\
                def listdir(directory):
                    if directory == '/':
                        gc.collect()                
                        return sorted([directory + f for f in os.listdir(directory)])
                    else:
                        gc.collect()
                        return sorted([directory + '/' + f for f in os.listdir(directory)])\n"""

        # Execute os.listdir() command on the board.
        if long_format:
            command += """
                def _get_file_crc32(file_path):
                    import binascii
                    dwPolynomial = 0xEDB88320
                    m_pdwCrc32Table = [0 for x in range(0, 256)]
                    for i in range(0, 255):
                        dwCrc = i
                        for j in [8, 7, 6, 5, 4, 3, 2, 1]:
                            if dwCrc & 1:
                                dwCrc = (dwCrc >> 1) ^ dwPolynomial
                            else:
                                dwCrc >>= 1
                        m_pdwCrc32Table[i] = dwCrc

                    def _calc_crc32(szString, dwCrc32):
                        dwCrc = 0
                        dwCrc32 = dwCrc32 ^ 0xFFFFFFFF

                        for i in szString:
                            b = ord(i)
                            dwCrc32 = ((dwCrc32) >> 8) ^ m_pdwCrc32Table[(b) ^ ((dwCrc32) & 0x000000FF)]
                        dwCrc32 = dwCrc32 ^ 0xFFFFFFFF
                        return dwCrc32

                    with open(file_path, "rb") as infile:
                        file_crc_value = 0xFFFFFFFF
                        while True:
                            ucrc = infile.read(200)
                            if len(ucrc) == 0:
                                break
                            ucrc = binascii.b2a_base64(ucrc)
                            file_crc_value = _calc_crc32(ucrc.decode(), file_crc_value)
                            gc.collect()
                    return ('%x' % (file_crc_value))

                try:
                    os_crc_flag = True
                    from os import file_crc32
                except ImportError:
                    os_crc_flag = False

                # from __sync import _get_file_crc32

                r = []
                for f in listdir('{0}'):
                    size = os.stat(f)[6]
                    if size == 0:
                        md5 = "dir"
                    else:
                        if os_crc_flag:
                            md5 = os.file_crc32(f)
                        else:
                            md5 = _get_file_crc32(f)
                    r.append('{{0}} - {{1}} - {{2}}'.format(f, size, md5))
                print(r)
            """.format(
                directory
            )
        else:
            command += """
                print(listdir('{0}'))
            """.format(
                directory
            )
        self._pyboard.enter_raw_repl()

        if pathname == None:
            pathname = "temp_file_info.json"

        try:
            out = self._pyboard.exec_(textwrap.dedent(command), "ls")

            if long_format:
                file_info = out.decode("utf-8")
                info_end = file_info.find("]")
                file_info = file_info.rstrip()[1:info_end].replace("\'","")

                file_dict = {}

                count = 0
                while(count < len(file_info.split(", "))):
                    file_dict[file_info.split(", ")[count].split(" - ")[0][1:]] = file_info.split(", ")[count].split(" - ")[2]
                    count += 1

                with open(pathname, 'w') as f:
                    f.write(str(file_dict))

        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            if ex.args[2].decode("utf-8").find("OSError: [Errno 2] ENOENT") != -1:
                raise RuntimeError("No such directory: {0}".format(directory))
            else:
                raise ex
        self._pyboard.exit_raw_repl()
        # Parse the result list and return it.
        return ast.literal_eval(out.decode("utf-8"))

    def _ls_sync(self, directory="/", long_format=True, recursive=False, pathname=None):
        """List the contents of the specified directory (or root if none is
        specified).  Returns a list of strings with the names of files in the
        specified directory.  If long_format is True then a list of 2-tuples
        with the name and size (in bytes) of the item is returned.  Note that
        it appears the size of directories is not supported by MicroPython and
        will always return 0 (i.e. no recursive size computation).
        """

        # Make sure directory starts with slash, for consistency.
        if not directory.startswith("/"):
            directory = "/" + directory

        command = """\
                try:        
                    import os
                    import gc
                    import sys
                except ImportError:
                    import uos as os
                cwd_dir = os.getcwd()\n"""

        if recursive:
            command += """\
                if sys.platform == "MaixPy":
                    def listdir(directory):
                        if directory == '/':
                            gc.collect()
                            return sorted([directory + f for f in os.listdir(directory)])
                        else:
                            gc.collect()
                            return sorted([directory + '/' + f for f in os.listdir(directory)])
                else:
                    def listdir(directory):
                        result = set()

                        def _listdir(dir_or_file):
                            try:
                                # if its a directory, then it should provide some children.
                                children = os.listdir(dir_or_file)
                            except OSError:                        
                                # probably a file. run stat() to confirm.
                                os.stat(dir_or_file)
                                result.add(dir_or_file) 
                            else:
                                # probably a directory, add to result if empty.
                                if children:
                                    # queue the children to be dealt with in next iteration.
                                    for child in children:
                                        # create the full path.
                                        if dir_or_file == '/':
                                            next = dir_or_file + child
                                        else:
                                            next = dir_or_file + '/' + child
                                        
                                        _listdir(next)
                                else:
                                    result.add(dir_or_file)                     

                        _listdir(directory)
                        gc.collect()
                        return sorted(result)\n"""
        else:
            command += """\
                def listdir(directory):
                    if directory == '/':
                        gc.collect()                
                        return sorted([directory + f for f in os.listdir(directory)])
                    else:
                        gc.collect()
                        return sorted([directory + '/' + f for f in os.listdir(directory)])\n"""

        # Execute os.listdir() command on the board.
        if long_format:
            command += """
                def _get_file_crc32(file_path):
                    import binascii
                    dwPolynomial = 0xEDB88320
                    m_pdwCrc32Table = [0 for x in range(0, 256)]
                    for i in range(0, 255):
                        dwCrc = i
                        for j in [8, 7, 6, 5, 4, 3, 2, 1]:
                            if dwCrc & 1:
                                dwCrc = (dwCrc >> 1) ^ dwPolynomial
                            else:
                                dwCrc >>= 1
                        m_pdwCrc32Table[i] = dwCrc

                    def _calc_crc32(szString, dwCrc32):
                        dwCrc = 0
                        dwCrc32 = dwCrc32 ^ 0xFFFFFFFF

                        for i in szString:
                            b = ord(i)
                            dwCrc32 = ((dwCrc32) >> 8) ^ m_pdwCrc32Table[(b) ^ ((dwCrc32) & 0x000000FF)]
                        dwCrc32 = dwCrc32 ^ 0xFFFFFFFF
                        return dwCrc32

                    with open(file_path, "rb") as infile:
                        file_crc_value = 0xFFFFFFFF
                        while True:
                            ucrc = infile.read(200)
                            if len(ucrc) == 0:
                                break
                            ucrc = binascii.b2a_base64(ucrc)
                            file_crc_value = _calc_crc32(ucrc.decode(), file_crc_value)
                            gc.collect()
                    return ('%x' % (file_crc_value))

                try:
                    os_crc_flag = True
                    from os import file_crc32
                except ImportError:
                    os_crc_flag = False

                r = []
                l = len(cwd_dir)

                if cwd_dir != '/':
                    l += 1

                for f in listdir(cwd_dir):
                    size = os.stat(f)[6]
                    if size == 0:
                        md5 = "dir"
                    else:
                        if os_crc_flag:
                            md5 = os.file_crc32(f)
                        else:
                            md5 = _get_file_crc32(f)
                    r.append('{{0}} - {{1}} - {{2}}'.format(f[l:], size, md5))
                print(r)
            """.format(
                directory
            )
        else:
            command += """
                print(listdir(cwd_dir))
            """.format(
                directory
            )
        self._pyboard.enter_raw_repl()

        if pathname == None:
            pathname = "temp_file_info.json"

        try:
            out = self._pyboard.exec_(textwrap.dedent(command), "ls")

            if long_format:
                file_info = out.decode("utf-8")
                info_end = file_info.find("]")
                file_info = file_info.rstrip()[1:info_end].replace("\'","")

                file_dict = {}

                count = 0
                while(count < len(file_info.split(", "))):
                    file_dict[file_info.split(", ")[count].split(" - ")[0]] = file_info.split(", ")[count].split(" - ")[2]
                    count += 1

        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            if ex.args[2].decode("utf-8").find("OSError: [Errno 2] ENOENT") != -1:
                raise RuntimeError("No such directory: {0}".format(directory))
            else:
                raise ex
        self._pyboard.exit_raw_repl()

        with open(pathname, 'w') as f:
            f.write(str(file_dict))

        # Parse the result list and return it.
        return ast.literal_eval(out.decode("utf-8"))

    def mkdir(self, directory, exists_okay=False):
        """Create the specified directory.  Note this cannot create a recursive
        hierarchy of directories, instead each one should be created separately.
        """
        # Execute os.mkdir command on the board.
        command = """
            try:
                import os
            except ImportError:
                import uos as os
            os.mkdir('{0}')
        """.format(
            directory
        )
        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            # Check if this is an OSError #17, i.e. directory already exists.
            if ex.args[2].decode("utf-8").find("OSError: [Errno 17] EEXIST") != -1:
                if not exists_okay:
                    self._pyboard.exit_raw_repl()
                    raise DirectoryExistsError(
                        "Directory already exists: {0}".format(directory)
                    )
            else:
                raise ex
        self._pyboard.exit_raw_repl()

    def put(self, filename, data):
        """Create or update the specified file with the provided data.
        """
        # Open the file for writing on the board and write chunks of data.
        self._pyboard.enter_raw_repl()
        self._pyboard.exec_("import gc")
        self._pyboard.exec_("f = open('{0}', 'wb')".format(filename))
        size = len(data)
        # Loop through and write a buffer size chunk of data at a time.
        for i in range(0, size, BUFFER_SIZE):
            chunk_size = min(BUFFER_SIZE, size - i)
            chunk = repr(data[i : i + chunk_size])
            # Make sure to send explicit byte strings (handles python 2 compatibility).
            if not chunk.startswith("b"):
                chunk = "b" + chunk
            self._pyboard.exec_("f.write({0})".format(chunk))
        self._pyboard.exec_("f.close()")
        self._pyboard.exec_("gc.collect()")
        self._pyboard.exit_raw_repl()

    def init_sync(self, filename):
        """Put crc clac func."""

        # Calculates the CRC value of the file
        command = """
            try:
                import os
                import binascii
            except ImportError:
                import uos as os

            os.stat('{0}')

            def _calc_crc32(szString, dwCrc32):
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

            with open('{0}', "rb") as infile:
                file_crc_value = 0xFFFFFFFF
                while True:
                    ucrc = infile.read(500)
                    if len(ucrc) == 0:
                        break
                    ucrc = binascii.b2a_base64(ucrc)
                    file_crc_value = _calc_crc32(ucrc.decode(), file_crc_value)

            print('%x' % (file_crc_value))
        """.format(
            filename
        )

        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command), "ls")
        except PyboardError as ex:
            message = ex.args[2].decode("utf-8")
            # Check if this is an OSError #2, i.e. file/directory doesn't exist
            # and rethrow it as something more descriptive.
            if message.find("OSError: [Errno 2] ENOENT") != -1:
                # raise RuntimeError("No such file/directory: {0}".format(filename))
                print("No such file/directory: {0}".format(filename))
            else:
                print(ex)

            self._pyboard.exit_raw_repl()
            return False

        self._pyboard.exit_raw_repl()
        return out

    def rm(self, filename):
        """Remove the specified file or directory."""
        command = """
            try:
                import os
                import gc
            except ImportError:
                import uos as os

            def rmdir(directory):
                os.chdir(directory)
                for f in os.listdir():
                    try:
                        os.remove(f)
                    except OSError:
                        pass
                for f in os.listdir():
                    rmdir(f)
                os.chdir('..')
                os.rmdir(directory)

            file_name = '{0}'

            try:
                size = os.stat(file_name)[6]
            except:
                file_name = '/' + file_name
                size = os.stat(file_name)[6]

            if size == 0:
                rmdir(file_name)
            else:
                os.remove(file_name)

            gc.collect()
        """.format(
            filename
        )
        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            message = ex.args[2].decode("utf-8")
            # Check if this is an OSError #2, i.e. file/directory doesn't exist
            # and rethrow it as something more descriptive.
            if message.find("OSError: [Errno 2] ENOENT") != -1:
                # raise RuntimeError("No such file/directory: {0}".format(filename))
                pass
            # Check for OSError #13, the directory isn't empty.
            if message.find("OSError: [Errno 13] EACCES") != -1:
                raise RuntimeError("Directory is not empty: {0}".format(filename))
            else:
                raise ex
        self._pyboard.exit_raw_repl()

    def rmdir(self, directory, missing_okay=False):
        """Forcefully remove the specified directory and all its children."""
        # Build a script to walk an entire directory structure and delete every
        # file and subfolder.  This is tricky because MicroPython has no os.walk
        # or similar function to walk folders, so this code does it manually
        # with recursion and changing directories.  For each directory it lists
        # the files and deletes everything it can, i.e. all the files.  Then
        # it lists the files again and assumes they are directories (since they
        # couldn't be deleted in the first pass) and recursively clears those
        # subdirectories.  Finally when finished clearing all the children the
        # parent directory is deleted.
        command = """
            try:
                import os
                import gc
            except ImportError:
                import uos as os
            def rmdir(directory):
                os.chdir(directory)
                for f in os.listdir():
                    try:
                        os.remove(f)
                    except OSError:
                        pass
                for f in os.listdir():
                    rmdir(f)
                os.chdir('..')
                os.rmdir(directory)
            rmdir('{0}')
            gc.collect()
        """.format(
            directory
        )
        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            message = ex.args[2].decode("utf-8")
            # Check if this is an OSError #2, i.e. directory doesn't exist
            # and rethrow it as something more descriptive.
            if message.find("OSError: [Errno 2] ENOENT") != -1:
                if not missing_okay:
                    raise RuntimeError("No such directory: {0}".format(directory))
            else:
                raise ex
        self._pyboard.exit_raw_repl()

    def run(self, filename, wait_output=True):
        """Run the provided script and return its output.  If wait_output is True
        (default) then wait for the script to finish and then print its output,
        otherwise just run the script and don't wait for any output.
        """
        self._pyboard.enter_raw_repl()
        out = None
        if wait_output:
            # Run the file and wait for output to return.
            out = self._pyboard.execfile(filename)
        else:
            # Read the file and run it using lower level pyboard functions that
            # won't wait for it to finish or return output.
            with open(filename, "rb") as infile:
                self._pyboard.exec_raw_no_follow(infile.read())
        self._pyboard.exit_raw_repl()
        return out

    def run_in_device(self, filename, wait_output=True):
        """Run the provided script and return its output.  If wait_output is True
        (default) then wait for the script to finish and then print its output,
        otherwise just run the script and don't wait for any output.
        """

        command = """
            with open('{0}') as __py:
                exec(__py.read(),globals())
        """.format(
            filename
        )

        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command), "ls")
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            if ex.args[2].decode("utf-8").find("OSError: [Errno 2] ENOENT") != -1:
                raise RuntimeError("No such directory: {0}".format(directory))
            else:
                raise ex
        self._pyboard.exit_raw_repl()
        # Parse the result list and return it.
        # return ast.literal_eval(out.decode("utf-8"))
        return out