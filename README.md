## ampy for RT-Thread MicroPython

Adafruit MicroPython Tool (ampy) - Utility to interact with a CircuitPython or MicroPython board over a serial connection.

Ampy is meant to be a simple command line tool to manipulate files and run code on a CircuitPython or
MicroPython board over its serial connection.
With ampy you can send files from your computer to the
board's file system, download files from a board to your computer, and even send a Python script
to a board to be executed.

## Installation

使用默认源安装依赖包：

```
python -m pip install -r requirements.txt
```

还可以使用国内镜像源安装依赖包：

```
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## Usage

```python
python cli.py -p COM18 repl              # 在当前终端接入 MicroPython 的 repl，在终端使用 CTRL + X 退出 repl 模式
python cli.py -p COM18 ls                # 打印出开发板上 / 目录中的文件列表
python cli.py -p COM18 ls /scripts       # 打印出开发板上 /scripts 文件夹中的文件列表
python cli.py -p COM18 ls -l -r          # 递归打印出 / 目录中文件列表
python cli.py -p COM18 mkdir dir_name    # 创建文件夹，名为 dir_name
python cli.py -p COM18 rmdir dir_name    # 递归地删除 dir_name 文件夹中的所有文件，最终删除文件夹
python cli.py -p COM18 rm filename       # 可以用来删除某个特定文件或者空文件夹
python cli.py -p COM18 run xx.py         # 在开发板上执行本地目录下的 xx.py 文件
python cli.py -p COM18 get xx.py xx.py   # 从开发板中获取 xx.py 到本地，并将该文件命名为 xx.py
python cli.py -p COM18 put xx.py xx.py   # 注意写入的文件必须是 unix 格式，否则读出时会出问题
python cli.py -p COM18 put local remote  # 将本地的 local 推送到开发板上，并且命名为 remote
python cli.py -p com18 sync -l "G:\prj_dir" # 将本地 project_dir 文件夹同步到设备根目录
```

## 设备文件同步

- 第一步执行 `python cli.py -p COM18 ls -l -r` 获取设备文件列表到本地
- 第二步执行`python cli.py -p com18 sync -l "G:\prj_dir"` 进行文件同步

## 在设备上执行文件

- `python cli.py -p com18 run none -d scripts/hello.py` 执行设备上的 `scripts/hello.py`

