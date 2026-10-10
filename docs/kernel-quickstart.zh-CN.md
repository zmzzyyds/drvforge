# Linux 驱动开发环境快速上手（中文）

面向刚接触 Linux 内核驱动的开发者，介绍如何从零搭起一个可以反复
编译、加载、调试驱动的环境。drvforge 生成的项目可以直接在这套环境里
使用。

## 1. 选择开发环境

内核模块只能在 Linux 上编译和加载。按你当前的系统选择：

- **原生 Ubuntu 22.04/24.04（推荐新手）**：最省事。
- **Windows**：安装 WSL2（`wsl --install -d Ubuntu-24.04`），在 WSL2 里
  编译和加载模块。注意 WSL2 使用微软定制内核，默认没有配套头文件，
  学习驱动建议用下面的 QEMU 虚拟机方案，或自行编译 WSL2 内核。
- **macOS**：使用 UTM/Parallels 起一台 Ubuntu 虚拟机，或使用云服务器。

## 2. 安装工具链

```sh
sudo apt update
sudo apt install -y build-essential bc bison flex libssl-dev \
     libelf-dev device-tree-compiler dkms git
# 当前内核的头文件（树外模块编译必需）
sudo apt install -y linux-headers-$(uname -r)
```

验证：

```sh
ls /lib/modules/$(uname -r)/build   # 目录存在即头文件就绪
drvforge env-check                  # drvforge 自带的检查命令
```

## 3. 最小内核模块（Hello World）

`hello.c`：

```c
// SPDX-License-Identifier: GPL-2.0-only
#include <linux/init.h>
#include <linux/module.h>

static int __init hello_init(void)
{
	pr_info("hello, kernel\n");
	return 0;
}

static void __exit hello_exit(void)
{
	pr_info("goodbye, kernel\n");
}

module_init(hello_init);
module_exit(hello_exit);
MODULE_LICENSE("GPL v2");
```

`Makefile`：

```makefile
obj-m := hello.o

all:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```

编译与加载：

```sh
make
sudo insmod hello.ko
dmesg | tail
sudo rmmod hello
dmesg | tail
```

理解了这一步，就理解了 drvforge 生成的 Makefile 在做什么。

## 4. 用 drvforge 生成第一个完整驱动

```sh
pipx install git+https://github.com/__GH_USER__/drvforge.git
drvforge new my-sensor -t misc -c acme,my-sensor
cd my_sensor
make
```

`misc` 模板是 platform 驱动，需要一个匹配 `compatible` 的设备节点才会
执行 probe。两种方式：

### 方式 A：QEMU arm64 虚拟机（推荐，可随意折腾）

```sh
sudo apt install -y qemu-system-arm qemu-efi-aarch64 cloud-image-utils
```

使用 Ubuntu arm64 cloud image 启动一台虚拟机（磁盘、内核均由发行版
提供），把生成的模块和 overlay 拷进去：

```sh
# 在虚拟机内编译（保证内核头文件匹配），或用与虚拟机同版本内核的头文件交叉编译
dtc -O dtb -o my-sensor-overlay.dtbo -@ my-sensor-overlay.dts
sudo mkdir -p /sys/kernel/config/device-tree/overlays/my-sensor
sudo cp my-sensor-overlay.dtbo \
     /sys/kernel/config/device-tree/overlays/my-sensor/dtbo
sudo insmod my_sensor.ko
dmesg | tail
ls /dev/my_sensor
make test
```

> overlay 中的寄存器地址以 QEMU `virt` 机型为例；真机请换成你 SoC 上
> 未占用的地址区间。

### 方式 B：在开发机上用 configfs 加载 overlay

需要内核开启 `CONFIG_OF_CONFIGFS`（x86 发行版内核通常未开启，此时用
QEMU 或自行编译内核）。

## 5. 常用调试手段

| 手段 | 用途 |
| --- | --- |
| `dmesg -w` | 实时观察驱动日志 |
| `/sys/kernel/debug/` | debugfs 视图（需 `CONFIG_DEBUG_FS`） |
| `ftrace` | 函数级追踪，无需额外调试器 |
| `print_hex_dump_debug` | 打印寄存器/缓冲区内容 |
| `gdb + kgdb` | 源码级调试，配置成本较高，建议后期再学 |
| `CONFIG_KASAN` / `LOCKDEP` | 内存越界、锁误用检测，自己编译内核时打开 |

驱动崩溃通常会使当前内核日志出现 Oops，包含调用栈和出错指令；把完整
Oops 贴到 issue 时请一并附上 `uname -r` 和复现步骤。

## 6. 学习路径建议

1. 先吃透 `misc` 模板：platform 总线、设备节点、sysfs、用户态读写。
2. 再看 `platform-cdev`：设备号、cdev、ioctl 与 UAPI 头文件的约定。
3. 然后是 `iio-temp`：真实 I2C 设备、regmap、IIO 子系统。
4. 对照内核源码 `drivers/` 下同类驱动阅读，这是最权威的教材。
5. 尝试为 drvforge 贡献一个新子系统模板（hwmon、leds、input……），
   指南见 [writing-templates.md](writing-templates.md)。

## 7. 常见问题

- **`make[1]: *** /lib/modules/.../build: No such file or directory`**：
  没装对应内核的头文件，安装 `linux-headers-$(uname -r)`。
- **`insmod: ERROR: could not insert module: Invalid module format`**：
  模块与当前内核版本不一致（常见于换内核后没重新 `make clean && make`）。
- **模块加载了但没有 probe**：总线上没有匹配 `compatible` 的设备，检查
  overlay 是否生效、`compatible` 是否与驱动中完全一致。
- **WSL2 里找不到头文件**：WSL2 是定制内核，按第 4 节改用 QEMU 虚拟机。
