# drvforge

**面向现代 Linux 内核驱动项目的脚手架工具。**

[![CI](https://github.com/zmzzyyds/drvforge/actions/workflows/ci.yml/badge.svg)](https://github.com/zmzzyyds/drvforge/actions/workflows/ci.yml)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

一条命令生成一个**完整、可直接编译**的内核驱动项目：现代内核风格的
驱动源码、Makefile、Kconfig、DKMS 配置、设备树 overlay，以及用户态 C
测试程序。CI 会用真实内核编译每个模板生成的驱动，保证模板随内核演进
始终可用。

> [English](README.md) | **简体中文**

## 为什么需要它

第一次写内核驱动时，往往要从五份年代各异的教程里拼凑样板代码，猜哪个
API 还没过时，手写 DKMS 和设备树 overlay，直到第一次 `insmod` 才发现
问题。drvforge 提供一个一致的、紧跟内核现状的起点，也可以作为学习各
子系统（misc、cdev、IIO……）标准写法的参考。

## 模板

| 模板 | 生成内容 |
| --- | --- |
| `misc` | platform 驱动 + misc 字符设备、内存 echo 缓冲区、sysfs 属性，无需真实硬件 |
| `platform-cdev` | 完整 cdev 的 platform 驱动、内核态/用户态共享 UAPI ioctl 头文件、带参数校验的 ioctl、用户态测试程序 |
| `iio-temp` | 基于 regmap + IIO 子系统的 I2C 温度传感器驱动（`in_temp_raw`/`in_temp_scale`） |

更多子系统模板见下方[路线图](#路线图)；新增一个模板被设计为适合作为
参与内核工具类开源项目的第一个 PR。

## 安装

```sh
# 推荐：用 pipx 隔离安装
pipx install git+https://github.com/zmzzyyds/drvforge.git

# 或使用 pip
pip install git+https://github.com/zmzzyyds/drvforge.git

# 或克隆后以开发模式安装
git clone https://github.com/zmzzyyds/drvforge.git
cd drvforge
pip install -e ".[dev]"
```

## 快速开始

```sh
# 1. 检查内核工具链（内核头文件、gcc、dtc、dkms、qemu）
drvforge env-check

# 2. 查看可用模板
drvforge list

# 3. 生成项目
drvforge new my-sensor -t misc -c acme,my-sensor
#   -> ./my_sensor/

# 4. 在 Linux 主机上编译和测试
cd my_sensor
make          # 针对当前运行内核编译 my_sensor.ko
make test     # 编译、加载、运行用户态测试、卸载
```

生成的目录结构：

```
my_sensor/
├── my_sensor.c            # 驱动源码
├── Makefile               # 树外编译 + 加载/测试/DKMS 目标
├── Kconfig                # 可直接移入内核源码树
├── dkms.conf              # DKMS 打包配置
├── my_sensor-overlay.dts  # 设备树 overlay（QEMU virt 示例）
├── tools/
│   └── test.c             # 用户态 C 测试程序
└── README.md              # 编译、绑定、测试、上游化说明
```

`platform-cdev` 模板还会额外生成 `include/my_sensor.h` —— 驱动和用户态
程序共同包含的 UAPI 头文件。

## 环境要求

- **drvforge 本体**：Python 3.9+，Linux/macOS/Windows 均可运行。
- **编译生成的模块**：Linux 主机（或虚拟机/容器），需要 `build-essential`
  和 `linux-headers-$(uname -r)`。
- 模板使用较新的内核 API（`remove_new`、`dev_err_probe`、单参数 I2C
  `probe`、`devm_iio_device_register` 等），建议内核版本 **6.3+**
  （misc/cdev 模板在 5.19+ 可编译）；CI 基于 Ubuntu 24.04 自带内核
  编译验证。

新手环境搭建可参考：[Linux 驱动开发环境快速上手（中文）](docs/kernel-quickstart.zh-CN.md)。

## 项目状态

v0.1.0：3 个模板、CLI 稳定、CI 对每个生成驱动做真实内核编译。已可用于
实际工作，模板覆盖面将持续扩大。

CI 会编译生成的驱动，并对自包含的那些做冒烟加载。它**不会**运行它们的
`tools/test` 程序，而且在云端 runner 上也做不到：平台驱动只绑定设备树节点，
runner 上没有节点，于是 `insmod` 成功而 `probe()` 从未执行——驱动的代码一行都没跑。
要真正运行生成的驱动需要一个客户机，由
[drv-lab](https://github.com/zmzzyyds/drv-lab) 提供：

```console
$ drvlab run ./my_sensor
```

## 路线图

- [ ] 更多驱动模板：`hwmon`、`leds`、`input`、`pwm`、`rtc`、`watchdog`、
      `net`、USB、DRM 小驱动
- [ ] `drvforge check`：对生成代码运行 `checkpatch.pl` 与 sparse
- [x] 一条命令启动 QEMU arm64、加载 overlay、跑测试 —— 已作为独立项目交付：
      [drv-lab](https://github.com/zmzzyyds/drv-lab)
- [ ] 随 overlay 一起生成 YAML 设备树 binding 文档
- [ ] CI 增加多 LTS 内核版本兼容矩阵
- [ ] 交互模式（`drvforge new` 逐步询问寄存器、中断、sysfs 属性等）

## 参与贡献

欢迎提交 issue、模板需求和 PR。新增模板前请先阅读
[CONTRIBUTING.md](CONTRIBUTING.md) 和
[docs/writing-templates.md](docs/writing-templates.md)（中文可先在 issue
中沟通）。参与即表示同意行为准则。

## 许可证

GPL-2.0-only，与 Linux 内核保持一致（驱动模板属于内核的衍生作品）。
详见 [LICENSE](LICENSE)。
