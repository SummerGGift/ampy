## ampy for RT-Thread MicroPython

Adafruit MicroPython Tool (ampy) - Utility to interact with a CircuitPython or MicroPython board over a serial connection.

Ampy is meant to be a simple command line tool to manipulate files and run code on a CircuitPython or
MicroPython board over its serial connection.
With ampy you can send files from your computer to the
board's file system, download files from a board to your computer, and even send a Python script
to a board to be executed.

## Installation

pip install -r requirements.txt

## Usage

```python
python cli.py -p COM18 ls

python cli.py -p COM18 ls /scripts

python cli.py -p COM18 ls -l -r        # 递归打印出文件列表

python cli.py -p COM18 mkdir 6666

python cli.py -p COM18 rmdir 6666

python cli.py -p COM18 rm filename

python cli.py -p COM18 run py.py

python cli.py -p COM18 put py.py py.py  # 注意写入到文件系统中的文件必须是 unix 格式，否则读出时会出问题

python cli.py -p COM18 get py.py 123456

python cli.py -p COM18 put local_library remote_library
```
