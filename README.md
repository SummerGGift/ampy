## Cli For RT-Thread MicroPython 

`RT-Thread MicroPython` 串口连接方式 `Cli` 命令行工具。

## 安装方式

使用默认源安装依赖包：

```
python -m pip install -r requirements.txt
```

还可以使用国内镜像源安装依赖包：

```
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

或者直接输入安装依赖命令：

```python
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple click pyserial python-dotenv
```

## 使用方法

### MicroPython 开发板通用命令

```python
# 在当前终端接入 MicroPython 的 repl，在终端使用 CTRL + X 退出 repl 模式
# 此时如果选择的端口不是一个 mpy 开发板，将会报出异常 Error: This not a MicroPython board no bytes
python cli.py -p COM18 repl

# 查询该开发板是否使用了 RT-Thread 固件，如果是则打印 Yes，没有使用则打印 No。在进行 repl 连接时，可以先调用此接口判断该开发板是否烧录有 MPY 固件，以及是否是 RT-Thread 固件，从而判断出该应该使用怎样的文件同步策略来操作文件同步。
# 同时会返回该固件是否开启了 uos 模块的反馈信息，如果开启了 uos 模块则返回 Yes: The uos module has been enableded，没有开启则返回 No: The uos module is not enabled
python cli.py -p COM18 repl -q rtt

python cli.py -p COM18 ls                   # 打印出开发板上 / 目录中的文件列表
python cli.py -p COM18 ls /scripts          # 打印出开发板上 /scripts 文件夹中的文件列表
python cli.py -p COM18 ls -r                # 递归打印出 / 目录中文件列表
python cli.py -p COM18 mkdir dir_name       # 创建文件夹，名为 dir_name
python cli.py -p COM18 rmdir dir_name       # 递归地删除 dir_name 文件夹中的所有文件，最终删除文件夹
python cli.py -p COM18 rm filename          # 可以用来删除某个特定文件或者空文件夹
python cli.py -p COM18 run xx.py            # 在开发板上执行本地目录下的 xx.py 文件
python cli.py -p COM18 get xx.py xx.py      # 从开发板中获取 xx.py 到本地，并将该文件命名为 xx.py
python cli.py -p COM18 put xx.py xx.py      # 注意写入的文件必须是 unix 格式，否则读出时会出问题
python cli.py -p COM18 put local remote     # 将本地的 local 推送到开发板上，并且命名为 remote
python cli.py -p com18 run none -d hello.py # 执行设备上的 `hello.py` 文件，注意如果该程序不返回，则程序无法从终端返回
```

### RT-Thread 固件专用命令

递归打印出设备指定目录下的文件列表、大小、md5 值，如果没有指定目录，默认为根目录。

```python
python cli.py -p COM18 ls -r -l
```
设备文件同步执行如下命令。

```python
python cli.py -p com18 sync -l "G:\ampy\scripts" -i "G:\file_info"
```

- `-l` 参数后面跟想要同步到远端根目录的本地文件夹地址

- `-i` 参数后面**设备文件系统中文件列表，缓存在本地的存储文件**

  对每一个开发板需要指定一个新的文件，否则会导致无法正确同步文件，如果不能确定指定的缓存文件是否正确，可以删除掉本地的缓存文件，并重新指定一个新的文件地址，同步代码会重新从设备文件系统中读取先关信息，并写入到这个文件里。

查询是否需要文件同步。

windows 下命令如下：

```
python .\cli.py -p "query" sync -l "G:\ampy\ampy" -i "G:\file_info" -q "ifneedsync"
```

Linux 下命令如下：

```
python cli.py -p "query" sync -l "/home/summergift/work/ampy/tests" -i "file_info" -q "ifneedsync"
```

如果不需要文件同步，则会收到返回值 `<no need to sync>`。

## 关闭 repl 命令行回显的方法

向串口发送 b'\xe8' 字符将会关闭回显功能，向串口发送 b'\xe9' 将会重新打开回显功能。该功能可用在按下 `CTRL + E` 进入粘贴模式前，关闭回显，使得输入的内容不显示在终端上。

### exe 打包命令

`pyinstaller.exe -F .\cli.py -p ampy`