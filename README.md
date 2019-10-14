## Tools For RT-Thread MicroPython 

本仓库为 `RT-Thread MicroPython` 串口命令行工具源代码，欢迎使用 [RT-Thread MicroPython](https://marketplace.visualstudio.com/items?itemName=RT-Thread.rt-thread-micropython) 进行 MicroPython 项目开发。

## 安装方式

输入安装依赖命令：

```python
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple click pyserial python-dotenv
```

## 使用方法

### MicroPython 开发板通用命令

```python
# 在当前终端接入 MicroPython 的 repl，在终端使用 CTRL + X 退出 repl 模式
# 此时如果选择的端口不是一个 mpy 开发板，将会报出异常 Error: This not a MicroPython board no bytes
python cli.py -p COM18 repl
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

#### 打印设备中的文件信息
递归打印出设备指定目录下的文件列表、大小、md5 值，如果没有指定目录，默认为根目录。

```python
python cli.py -p COM18 ls -r -l
```
#### 查询是否需要文件同步

```
python cli.py -p "query" sync -l "G:\sync_dir" -i "G:\file_list_cache" -q "ifneedsync"
```

#### 执行文件夹或者文件同步同步时

```python
python cli.py -p com18 sync -l "G:\sync_dir" -i "G:\file_list_cache"
```

- `-l` 参数后面跟想要同步到远端根目录的本地文件夹地址

- `-i` 参数后面 **设备文件系统中文件列表，缓存在本地的存储文件**

  对每一个开发板需要指定一个新的文件，否则会导致无法正确同步文件，如果不能确定指定的缓存文件是否正确，可以删除掉本地的缓存文件，并重新指定一个新的文件地址，同步代码会重新从设备文件系统中读取先关信息，并写入到这个文件里。

## 关闭 repl 命令行回显的方法

向串口发送 b'\xe8' 字符将会关闭回显功能，向串口发送 b'\xe9' 将会重新打开回显功能。该功能可用在按下 `CTRL + E` 进入粘贴模式前，关闭回显，使得输入的内容不显示在终端上。

### Package cli on Windows

`pyinstaller.exe -F .\cli.py -p ampy`

### Package cli on Linux

`pyinstaller -F cli.py -p ampy`

### linux 下将当前用话加入到 dialout 用户组

执行下面的命令，当使用 your_username 进行串口操作时，就不需要再输入 sudo 来频繁获取权限了。

`sudo usermod -aG dialout your_username`