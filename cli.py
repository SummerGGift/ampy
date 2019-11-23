# Adafruit MicroPython Tool - Command Line Interface
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
#
# Change Logs:
# Date           Author       Notes
# 2019-10-10     SummerGift   Improve the code architecture

from __future__ import print_function
import os
import platform
import posixpath
import re
import serial
import serial.serialutil
import serial.tools.list_ports
import threading
import click
import dotenv
import sys
import time
import hashlib
import json
import ampy.files as files
import ampy.pyboard as pyboard
import gc

from ampy.getch import getch
from ampy.file_sync import file_sync_info
from ampy.file_sync import _get_file_crc32
from ampy.pyboard import stdout

# Load AMPY_PORT et al from .ampy file
# Performed here because we need to beat click's decorators.
config = dotenv.find_dotenv(filename=".ampy", usecwd=True)
if config:
    dotenv.load_dotenv(dotenv_path=config)

serial_reader_running = None
serial_out_put_enable = True
serial_out_put_count = 0

_board = None
_system = None

class CliError(BaseException):
    pass

def windows_full_port_name(portname):
    # Helper function to generate proper Windows COM port paths.  Apparently
    # Windows requires COM ports above 9 to have a special path, where ports below
    # 9 are just referred to by COM1, COM2, etc. (wacky!)  See this post for
    # more info and where this code came from:
    # http://eli.thegreenplace.net/2009/07/31/listing-all-serial-ports-on-windows-with-python/
    m = re.match("^COM(\d+)$", portname)
    if m and int(m.group(1)) < 10:
        return portname
    else:
        return "\\\\.\\{0}".format(portname)


@click.group()
@click.option(
    "--port",
    "-p",
    envvar="AMPY_PORT",
    required=True,
    type=click.STRING,
    help="Name of serial port for connected board.  Can optionally specify with AMPY_PORT environment variable.",
    metavar="PORT",
)
@click.option(
    "--baud",
    "-b",
    envvar="AMPY_BAUD",
    default=115200,
    type=click.INT,
    help="Baud rate for the serial connection (default 115200).  Can optionally specify with AMPY_BAUD environment variable.",
    metavar="BAUD",
)
@click.option(
    "--delay",
    "-d",
    envvar="AMPY_DELAY",
    default=0,
    type=click.FLOAT,
    help="Delay in seconds before entering RAW MODE (default 0). Can optionally specify with AMPY_DELAY environment variable.",
    metavar="DELAY",
)
@click.version_option()
def cli(port, baud, delay):
    """ampy - Adafruit MicroPython Tool

    Ampy is a tool to control MicroPython boards over a serial connection.  Using
    ampy you can manipulate files on the board's internal filesystem and even run
    scripts.
    """
    global _board
    global _system

    if platform.system() == "Windows":
        _system = "Windows"

    if platform.system() == "Linux":
        _system = "Linux"

    if port != "query":
        # On Windows fix the COM port path name for ports above 9 (see comment in
        # windows_full_port_name function).
        if platform.system() == "Windows":
            port = windows_full_port_name(port)
        _board = pyboard.Pyboard(port, baudrate=baud, rawdelay=delay)


@cli.command()
@click.argument("remote_file")
@click.argument("local_file", type=click.File("wb"), required=False)
def get(remote_file, local_file):
    """
    Retrieve a file from the board.

    Get will download a file from the board and print its contents or save it
    locally.  You must pass at least one argument which is the path to the file
    to download from the board.  If you don't specify a second argument then
    the file contents will be printed to standard output.  However if you pass
    a file name as the second argument then the contents of the downloaded file
    will be saved to that file (overwriting anything inside it!).

    For example to retrieve the boot.py and print it out run:

      ampy --port /board/serial/port get boot.py

    Or to get main.py and save it as main.py locally run:

      ampy --port /board/serial/port get main.py main.py
    """
    # Get the file contents.
    board_files = files.Files(_board)
    contents = board_files.get(remote_file)
    # Print the file out if no local file was provided, otherwise save it.
    if local_file is None:
        print(contents.decode("utf-8"))
    else:
        local_file.write(contents)


@cli.command()
@click.option(
    "--exists-okay", is_flag=True, help="Ignore if the directory already exists."
)
@click.argument("directory")
def mkdir(directory, exists_okay):
    """
    Create a directory on the board.

    Mkdir will create the specified directory on the board.  One argument is
    required, the full path of the directory to create.

    Note that you cannot recursively create a hierarchy of directories with one
    mkdir command, instead you must create each parent directory with separate
    mkdir command calls.

    For example to make a directory under the root called 'code':

      ampy --port /board/serial/port mkdir /code
    """
    # Run the mkdir command.
    board_files = files.Files(_board)
    board_files.mkdir(directory, exists_okay=exists_okay)


@cli.command()
@click.argument("directory", default="/")
@click.option(
    "--long_format",
    "-l",
    is_flag=True,
    help="Print long format info including size of files.  Note the size of directories is not supported and will show 0 values.",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="recursively list all files and (empty) directories.",
)
def ls(directory, long_format, recursive):
    """List contents of a directory on the board.

    Can pass an optional argument which is the path to the directory.  The
    default is to list the contents of the root, /, path.

    For example to list the contents of the root run:

      ampy --port /board/serial/port ls

    Or to list the contents of the /foo/bar directory on the board run:

      ampy --port /board/serial/port ls /foo/bar

    Add the -l or --long_format flag to print the size of files (however note
    MicroPython does not calculate the size of folders and will show 0 bytes):

      ampy --port /board/serial/port ls -l /foo/bar
    """
    # List each file/directory on a separate line.
    board_files = files.Files(_board)
    for f in board_files.ls(directory, long_format=long_format, recursive=recursive):
        print(f)


@cli.command()
@click.argument("local", type=click.Path(exists=True))
@click.argument("remote", required=False)
def put(local, remote):
    """Put a file or folder and its contents on the board.

    Put will upload a local file or folder  to the board.  If the file already
    exists on the board it will be overwritten with no warning!  You must pass
    at least one argument which is the path to the local file/folder to
    upload.  If the item to upload is a folder then it will be copied to the
    board recursively with its entire child structure.  You can pass a second
    optional argument which is the path and name of the file/folder to put to
    on the connected board.

    For example to upload a main.py from the current directory to the board's
    root run:

      ampy --port /board/serial/port put main.py

    Or to upload a board_boot.py from a ./foo subdirectory and save it as boot.py
    in the board's root run:

      ampy --port /board/serial/port put ./foo/board_boot.py boot.py

    To upload a local folder adafruit_library and all of its child files/folders
    as an item under the board's root run:

      ampy --port /board/serial/port put adafruit_library

    Or to put a local folder adafruit_library on the board under the path
    /lib/adafruit_library on the board run:

      ampy --port /board/serial/port put adafruit_library /lib/adafruit_library
    """
    # Use the local filename if no remote filename is provided.
    if remote is None:
        remote = os.path.basename(os.path.abspath(local))
    # Check if path is a folder and do recursive copy of everything inside it.
    # Otherwise it's a file and should simply be copied over.
    if os.path.isdir(local):
        # Directory copy, create the directory and walk all children to copy
        # over the files.
        dir_del_flag = True
        board_files = files.Files(_board)
        for parent, child_dirs, child_files in os.walk(local):
            # Create board filesystem absolute path to parent directory.
            remote_parent = posixpath.normpath(
                posixpath.join(remote, os.path.relpath(parent, local))
            )
            try:
                # if dir already exist, remove that dir, only perform once.
                if dir_del_flag:
                    board_files.rmdir(remote_parent, missing_okay=True)
                    dir_del_flag = False
                # Create remote parent directory.
                board_files.mkdir(remote_parent)
                # Loop through all the files and put them on the board too.
                for filename in child_files:
                    with open(os.path.join(parent, filename), "rb") as infile:
                        remote_filename = posixpath.join(remote_parent, filename)
                        board_files.put(remote_filename, infile.read())
            except files.DirectoryExistsError:
                # Ignore errors for directories that already exist.
                pass

    else:
        # File copy, open the file and copy its contents to the board.
        # Put the file on the board.
        with open(local, "rb") as infile:
            board_files = files.Files(_board)
            board_files.put(remote, infile.read())


@cli.command()
@click.argument("remote_file")
def rm(remote_file):
    """Remove a file from the board.

    Remove the specified file from the board's filesystem.  Must specify one
    argument which is the path to the file to delete.  Note that this can't
    delete directories which have files inside them, but can delete empty
    directories.

    For example to delete main.py from the root of a board run:

      ampy --port /board/serial/port rm main.py
    """
    # Delete the provided file/directory on the board.
    board_files = files.Files(_board)
    board_files.rm(remote_file)


@cli.command()
@click.option(
    "--missing-okay", is_flag=True, help="Ignore if the directory does not exist."
)
@click.argument("remote_folder")
def rmdir(remote_folder, missing_okay):
    """Forcefully remove a folder and all its children from the board.

    Remove the specified folder from the board's filesystem.  Must specify one
    argument which is the path to the folder to delete.  This will delete the
    directory and ALL of its children recursively, use with caution!

    For example to delete everything under /adafruit_library from the root of a
    board run:

      ampy --port /board/serial/port rmdir adafruit_library
    """
    # Delete the provided file/directory on the board.
    board_files = files.Files(_board)
    board_files.rmdir(remote_folder, missing_okay=missing_okay)


@cli.command()
@click.argument("local_file")
@click.option(
    "--no-output",
    "-n",
    is_flag=True,
    help="Run the code without waiting for it to finish and print output.  Use this when running code with main loops that never return.",
)
@click.option(
    "--device_file",
    "-d",
    envvar="run file in device",
    default=0,
    type=click.STRING,
    help="run file in device",
    metavar="run file in device",
)
def run(local_file, no_output, device_file):
    """Run a script and print its output.

    Run will send the specified file to the board and execute it immediately.
    Any output from the board will be printed to the console (note that this is
    not a 'shell' and you can't send input to the program).

    Note that if your code has a main or infinite loop you should add the --no-output
    option.  This will run the script and immediately exit without waiting for
    the script to finish and print output.

    For example to run a test.py script and print any output after it finishes:

      ampy --port /board/serial/port run test.py

    Or to run test.py and not wait for it to finish:

      ampy --port /board/serial/port run --no-output test.py
    """

    # Run the provided file and print its output.
    board_files = files.Files(_board)
    try:
        if device_file:
            output = board_files.run_in_device(device_file, not no_output)
        else:
            output = board_files.run(local_file, not no_output)

        if output is not None:
            print(output.decode("utf-8"), end="")
    except IOError:
        click.echo(
            "Failed to find or read input file: {0}".format(local_file), err=True
        )


@cli.command()
@click.option(
    "--bootloader", "mode", flag_value="BOOTLOADER", help="Reboot into the bootloader"
)
@click.option(
    "--hard",
    "mode",
    flag_value="NORMAL",
    help="Perform a hard reboot, including running init.py",
)
@click.option(
    "--repl",
    "mode",
    flag_value="SOFT",
    default=True,
    help="Perform a soft reboot, entering the REPL  [default]",
)
@click.option(
    "--safe",
    "mode",
    flag_value="SAFE_MODE",
    help="Perform a safe-mode reboot.  User code will not be run and the filesystem will be writeable over USB",
)
def reset(mode):
    """Perform soft reset/reboot of the board.

    Will connect to the board and perform a reset.  Depending on the board
    and firmware, several different types of reset may be supported.

      ampy --port /board/serial/port reset
    """
    _board.enter_raw_repl()
    if mode == "SOFT":
        _board.exit_raw_repl()
        return

    _board.exec_(
        """if 1:
        def on_next_reset(x):
            try:
                import microcontroller
            except:
                if x == 'NORMAL': return ''
                return 'Reset mode only supported on CircuitPython'
            try:
                microcontroller.on_next_reset(getattr(microcontroller.RunMode, x))
            except ValueError as e:
                return str(e)
            return ''
        def reset():
            try:
                import microcontroller
            except:
                import machine as microcontroller
            microcontroller.reset()
    """
    )
    r = _board.eval("on_next_reset({})".format(repr(mode)))
    print("here we are", repr(r))
    if r:
        click.echo(r, err=True)
        return

    try:
        _board.exec_("reset()")
    except serial.serialutil.SerialException as e:
        # An error is expected to occur, as the board should disconnect from
        # serial when restarted via microcontroller.reset()
        pass


def repl_serial_to_stdout(serial):

    global _system
    global serial_out_put_count

    def hexsend(string_data=''):
        hex_data = string_data.decode("hex")
        return hex_data

    try:
        data = b''
        while serial_reader_running:
            count = serial.inWaiting()

            if count == 0:
                time.sleep(0.01)
                continue

            if count > 0:
                try:
                    data += serial.read(count)

                    if len(data) < 20:
                        try:
                            data.decode()
                        except UnicodeDecodeError:
                            continue

                    if data != b'':
                        if serial_out_put_enable and serial_out_put_count > 0:
                            if _system == "Linux":
                                sys.stdout.buffer.write(data)
                            else:
                                sys.stdout.buffer.write(data.replace(b"\r", b""))
                            sys.stdout.buffer.flush()
                    else:
                        serial.write(hexsend(data))

                    data = b''
                    serial_out_put_count += 1

                except serial.serialutil.SerialException:
                    # This happens if the pyboard reboots, or a USB port
                    # goes away.
                    return
                except TypeError:
                    # This is a bug in serialposix.py starting with python 3.3
                    # which causes a TypeError during the handling of the
                    # select.error. So we treat this the same as
                    # serial.serialutil.SerialException:
                    return
                except ConnectionResetError:
                    # This happens over a telnet session, if it resets
                    return

    except KeyboardInterrupt:
        if serial != None:
            serial.close()

@cli.command()
@click.option(
    "--query",
    "-q",
    envvar="query_is_can_be_connected",
    # required=True,
    default=None,
    type=click.STRING,
    help="Query whether the com port can be connected",
    metavar="query",
)

def repl(query = None):

    global serial_reader_running
    global serial_out_put_enable
    global serial_out_put_count

    serial_out_put_count = 1

    serial_reader_running = True

    if query != None:
        return

    _board.read_until_hit()

    serial = _board.serial

    repl_thread = threading.Thread(target = repl_serial_to_stdout, args=(serial,), name='REPL_serial_to_stdout')
    repl_thread.daemon = True
    repl_thread.start()

    try:
        # Wake up the prompt
        serial.write(b'\r')

        count = 0

        while True:
            char = getch()
            count += 1
            if count == 1000:
                time.sleep(0.1)
                count = 0

            if char == b'\x07':
                serial_out_put_enable = False
                continue

            if char == b'\x0F':
                serial_out_put_enable = True
                serial_out_put_count = 0
                continue

            if char == b'\x00':
                continue

            if not char:
                continue

            if char == b'\x18':   # enter ctrl + x to exit repl mode
                serial_reader_running = False
                # When using telnet with the WiPy, it doesn't support
                # an initial timeout. So for the meantime, we send a
                # space which should cause the wipy to echo back a
                # space which will wakeup our reader thread so it will
                # notice the quit.
                serial.write(b' ')
                # Give the reader thread a chance to detect the quit
                # then we don't have to call getch() above again which
                # means we'd need to wait for another character.
                time.sleep(0.1)
                # Print a newline so that the rshell prompt looks good.
                print('')
                # We stay in the loop so that we can still enter
                # characters until we detect the reader thread quitting
                # (mostly to cover off weird states).
                return

            if char == b'\n':
                serial.write(b'\r')
            else:
                serial.write(char)
    except DeviceError as err:
        # The device is no longer present.
        self.print('')
        self.stdout.flush()
        print_err(err)
        print("exit repl")

    repl_thread.join()


@cli.command()
@click.option(
    "--local_path",
    "-l",
    envvar="local_path",
    required=True,
    default=0,
    type=click.STRING,
    help="local_path",
    metavar="local_path",
)

@click.option(
    "--file_pathname",
    "-f",
    envvar="file_pathname",
    required=True,
    default=0,
    type=click.STRING,
    help="file pathname",
    metavar="file_pathname",
)

@click.option(
    "--remote_path",
    "-r",
    envvar="remote_path",
    required=True,
    default=0,
    type=click.STRING,
    help="remote_path",
    metavar="remote_path",
)

@click.option(
    "--info_pathname",
    "-i",
    envvar="info_pathname",
    # required=True,
    default=None,
    type=click.STRING,
    help="info_pathname",
    metavar="info_pathname",
)

@click.option(
    "--query",
    "-q",
    envvar="query",
    # required=True,
    default=None,
    type=click.STRING,
    help="query",
    metavar="query",
)

def sync(local_path, file_pathname, remote_path = None, info_pathname = None, query = None):
    def _sync_file(sync_info, local, remote = None):
        local = local.replace('\\', '/')
        delete_file_list = sync_info["delete"]
        sync_file_list = sync_info["sync"]

        if delete_file_list == [] and sync_file_list == []:
            return

        board_files = files.Files(_board)

        # Directory copy, create the directory and walk all children to copy
        # over the files.
        for parent, child_dirs, child_files in os.walk(local):
            # Create board filesystem absolute path to parent directory.
            remote_parent = posixpath.normpath(
                posixpath.join(local, os.path.relpath(parent, local))
            )

            try:
                # Create remote parent directory.
                dir_name = remote_parent[len(local_path) + 1:]

                if dir_name != "":
                    board_files.mkdir(dir_name)
                # Loop through all the files and put them on the board too.

            except files.DirectoryExistsError:
                # Ignore errors for directories that already exist.
                pass

            # add sync files
        for item in sync_file_list:
            # File copy, open the file and copy its contents to the board.
            # Put the file on the board.
            print("file to add:%s"%item)
            item_local = os.path.join(local_path, item).replace('\\', '/')
            with open(item_local, "rb") as infile:
                board_files = files.Files(_board)
                board_files.put(item, infile.read())

        # delete files
        for item in delete_file_list:
            # Delete the provided file/directory on the board.
            # board_files.rmdir(item, True)
            print("file to del:%s"%item)
            if item != '':
                board_files.rm(item)

    # check if need sync
    if query == "ifneedsync":
        if not os.path.exists(info_pathname):
            print("<file need sync>")
        else:
            # Gets file synchronization information
            sync_info, pc_file_info = file_sync_info(local_path, info_pathname)
            if sync_info['delete'] == [] and sync_info['sync'] == []:
                print("<no need to sync>")
            else:
                print("<file need sync>")
        return

    # check repl rtt uos
    _board.get_board_identity()

    if not _board.is_have_uos():
        raise PyboardError('Error: The uos module is not enabled')

    rtt_version_flag = False
    if _board.is_rtt_micropython():
        rtt_version_flag = True

    # ready to sync
    if info_pathname == None:
        info_pathname = "file_info.json"

    if not os.path.exists(info_pathname):
        # List each file/directory on a separate line.
        board_files = files.Files(_board)
        board_files._ls_sync(long_format=True, recursive=True, pathname = info_pathname)

    # Gets file synchronization information
    sync_info, pc_file_info = file_sync_info(local_path, info_pathname, rtt_version_flag)

    # print("sync_info------------------------------")
    # print(sync_info)
    # print("pc_file_info------------------------------")
    # print(pc_file_info)

    if sync_info['delete'] == [] and sync_info['sync'] == []:
        print("<no need to sync>")
        return

    try:
        # Perform file synchronization
        _sync_file(sync_info, local_path)
    except:
        raise CliError("error: _file_sync failed, please restart and retry.")

    # After successful file synchronization, update the local cache file information
    with open(info_pathname, 'w') as f:
        f.write(str(pc_file_info))

    _board.soft_reset_board()


@cli.command()
def portscan(port=None):
    """Scan all serial ports on your system."""

    port_list = list(serial.tools.list_ports.comports())

    if len(port_list) <= 0:
        print("can't find any serial in system.")
    else:
        print([list(port_list[i])[0] for i in range(0, len(port_list))])

    del port_list
    gc.collect()
    os._exit(0)


if __name__ == "__main__":
    try:
        cli()
    finally:
        # Try to ensure the board serial connection is always gracefully closed.
        if _board is not None:
            try:
                _board.close()
            except:
                # Swallow errors when attempting to close as it's just a best effort
                # and shouldn't cause a new error or problem if the connection can't
                # be closed.
                pass
