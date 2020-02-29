# Tools For RT-Thread MicroPython 

本仓库为 `RT-Thread MicroPython IDE` 串口命令行工具后端源代码，欢迎使用 [RT-Thread MicroPython](https://marketplace.visualstudio.com/items?itemName=RT-Thread.rt-thread-micropython) 进行 MicroPython 项目开发。其功能为连接 MicroPython 设备，并基于该设备执行 MicroPython 开发过程中的各种操作。

## 1. 安装方式

在命令行中输入如下命令，安装该工具所依赖的软件包：

```python
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple click pyserial python-dotenv pyinstaller
```

## 2. 命令使用方式

- 运行功能脚本

安装后可以直接运行 cli.py 脚本来操作 MicroPython 设备。 

例如 `python cli.py -p COM18 repl` 的意思是连接 COM18 串口并进入 repl 模式。

- 运行可执行文件

可执行文件存放在 dist 文件夹下，里面存放了不同操作系统下的可执行文件：

例如 `./cli.exe -p COM18 repl` 的意思是连接 COM18 串口并进入 repl 模式。

### 2.1 连接串口

使用任何命令都需要指定本次操作的串口，例如 `python cli.py -p COM18` 的意思是对 COM18 串口的设备进行操作，后续所有的命令前也都需要添加该格式。

### 2.2 查询系统中可用串口

- python cli.py -p query portscan

### 2.3 进入 repl 模式

连接串口并打开 repl 模式的命令如下：

- python cli.py -p COM18 repl

在当前终端接入 MicroPython 的 repl ，在终端使用 `ctrl +x` 退出 repl 模式。

### 2.4 查询文件系统列表

| 命令        | 功能                                       |
| ----------- | ------------------------------------------ |
| ls          | 打印出开发板上 / 目录中的文件列表          |
| ls -r       | 递归打印出 / 目录中文件列表                |
| ls -r -l    | 递归打印出 / 目录中文件列表以及 crc 校验值 |
| ls /scripts | 打印出开发板上 /scripts 文件夹中的文件列表 |

例如：

- python cli.py -p COM18 ls

### 2.5 创建删除文件夹/文件

| 命令           | 功能                                                   |
| -------------- | ------------------------------------------------------ |
| mkdir dir_name | 创建文件夹，名为 dir_name                              |
| rmdir dir_name | 递归地删除 dir_name 文件夹中的所有文件，最终删除文件夹 |
| rm filename    | 可以用来删除某个特定文件                               |

例如：

- python cli.py -p COM18 mkdir dir_test_name

### 2.6 文件传输操作

| 命令                | 功能                                                       |
| ------------------- | ---------------------------------------------------------- |
| get xx.py xx.py     | 从开发板中获取 xx.py 到本地，并将该文件命名为 xx.py        |
| put xx.py xx.py     | 将本地文件传入到开发板中（注意写入的文件必须是 unix 格式） |
| put dir_name remote | 将本地的 dir_name文件夹推送到开发板上，并且重命名为 remote |

例如：

- python cli.py -p COM18 get board.py local.py

### 2.7 代码文件运行

| 命令                 | 功能                                                         |
| -------------------- | ------------------------------------------------------------ |
| run xx.py            | 在开发板上执行本地目录下的 xx.py 文件                        |
| run none -d hello.py | 执行设备上的 `hello.py` 文件，注意如果该程序不返回，则程序无法从终端返回 |

### 2.8 文件夹同步

```python
python cli.py -p com18 sync -l "G:\sync_dir" -i "G:\file_list_cache"
```

- `-l` 参数后面跟想要同步到远端根目录的本地文件夹地址

- `-i` 参数后面**设备文件系统中文件列表，缓存在本地的存储文件**

  对每一个开发板需要指定一个新的文件，否则会导致无法正确同步文件，如果不能确定指定的缓存文件是否正确，可以删除掉本地的缓存文件，并重新指定一个新的文件地址，同步代码会重新从设备文件系统中读取先关信息，并写入到这个文件里。

### 2.9 关闭 repl 命令行回显的方法

向串口发送 b'\xe8' 字符将会关闭回显功能，向串口发送 b'\xe9' 将会重新打开回显功能。该功能可用在按下 `CTRL + E` 进入粘贴模式前，关闭回显，使得输入的内容不显示在终端上。

## 3. 重新打包 cli 工具

cli 在不同的系统上运行，可能需要重新打包，如果该工具在您的系统上无法运行，可以尝试用如下命令重新打包，然后在插件中重新替换 cli 工具即可。插件后端一般路径如下：

```
.vscode\extensions\rt-thread.rt-thread-micropython-1.x.x\ampy
```

### 3.1 在 windows 系统上打包 cli 

`pyinstaller.exe -F .\cli.py -p ampy`

### 3.2 在 linux（包括 Deepin Mac 等类 linux 操作系统） 系统上打包 cli  

`pyinstaller -F cli.py -p ampy`

### 3.3 linux 下将当前用话加入到 dialout 用户组

执行下面的命令，当使用 your_username 进行串口操作时，就不需要再输入 sudo 来频繁获取权限了。

`sudo usermod -aG dialout your_username`
