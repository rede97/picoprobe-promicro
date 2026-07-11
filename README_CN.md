# picoprobe-promicro

[English](README.md)

---

## 项目简介

基于 **RP2040 Pro Micro** 核心板设计的一块 Raspberry Pi 调试探针（Debug Probe）扩展底板。电路完全兼容 [树莓派官方 Debug Probe](https://www.raspberrypi.com/products/debug-probe/)，只需将 RP2040 Pro Micro 插上底板，直接烧录**树莓派官方的 Debug Probe 固件**即可使用，无需任何自定义固件。

RP2040 Pro Micro 板载 **Boot 按键**和 **Reset 按键**，烧录固件极其方便：按住 Boot → 按一下 Reset → 松开 Boot，USB 即弹出 U 盘，拖入 `.uf2` 固件文件即可。无需任何短接跳线等复杂操作。

## 兼容性与可靠性

令人惊讶的是，树莓派 Debug Probe 的兼容性和可靠性远远超出预期。它不仅完美支持 RP2040 系列芯片，对于其他种类的 **ARM 单片机及 SoC**（STM32 全系列、nRF52840 等 Nordic 芯片、各种 Cortex-M 内核 MCU），其调试和烧录体验都极其稳定可靠。

得益于 RP2040 的 **PIO 硬件特性**，Debug Probe 能实现极快的 SWD 传输速度，实测不输甚至超越部分 USB 高速下载器。在多种目标芯片的长时间调试过程中，从未出现断连、超时或不识别等常见问题。

## 项目背景

树莓派官方的 Debug Probe 存在几个问题：

- 到现在仍在使用 **Micro USB** 接口，而非如今更普遍的 USB-C
- 直接用普通 Pico 烧录 Pico 版 Picoprobe 固件会出现**各种不稳定的问题**
- 单独设计一整块调试器 PCB 对许多人来说没有必要
- 本质上只是 RP2040 + 电平转换的简单电路，官方售价对一块固定功能的调试板而言偏高

相比之下，开源社区的各种 DAPLink 方案对各类 ARM 芯片的兼容性和稳定性**远不如树莓派 Debug Probe**。

## 完全开源

这是本项目最大的亮点之一：

- **硬件完全开源**：PCB 设计文件（原理图、布局）全部以 KiCad 格式开源，任何人都可以查看、修改、自行打样
- **固件完全开源**：直接使用树莓派官方的 [debugprobe 固件](https://github.com/raspberrypi/debugprobe)，无任何私有或定制代码。固件由树莓派官方维护，持续更新，质量有保障
- **无闭源负担**：许多市面上的 DAPLink 调试器使用私有固件，出了 bug 找不到人反馈，也无法自行升级修复。而本方案从硬件到固件全链路开源，社区驱动，永不过时

## 关于 JTAG

本项目目前仅支持 **SWD** 调试接口，不支持 JTAG。从实际使用场景来看：

- 绝大多数 Cortex-M 系列 MCU 的调试和烧录只需 SWD，JTAG 并非必需
- 如果确实需要 JTAG 及 Trace、ETM 等高级调试功能，选择成熟的 **J-Link** 是更合理的方案——此时你需要的不仅是接口协议，而是完整的专业调试工具链

未来不排除固件层面支持 JTAG 的可能（RP2040 的 PIO 在硬件上具备能力），但目前没有明确计划。

## 设计思路

与其重新设计一块完整的调试器，不如利用市面上大量流通的 **RP2040 Pro Micro** 核心板，设计一块配套的扩展底板：

- **灵活组合**：使用排针和排母插座将 Pro Micro 临时固定在底板上用于调试，随时可取下用于其他项目
- **也可固定**：直接用短排针将底板和 Pro Micro 永久焊死在一起，作为一块专用的调试器长期使用
- **极低成本**：BOM 成本远低于官方 Debug Probe 的售价
- **无负担**：不必担心损坏昂贵的调试器，甚至可以基于此方案开发自己的功能

## PCB 渲染图

| 正面 | 背面 |
|:---:|:---:|
| ![正面](hardware/picoprobe-front.png) | ![背面](hardware/picoprobe-back.png) |

[下载原理图 PDF](hardware/picoprobe_sch.pdf)

## 项目结构

```
├── hardware/
│   ├── picoprobe.kicad_sch      # 原理图
│   ├── picoprobe.kicad_pcb      # PCB 设计
│   ├── picoprobe.kicad_pro      # KiCad 项目文件
│   ├── picoprobe-front.png      # 正面渲染图
│   ├── picoprobe-back.png       # 背面渲染图
│   ├── picoprobe_sch.pdf        # 原理图 PDF
│   └── kicad_pro_micro_rp2040/  # Pro Micro RP2040 封装库 (submodule)
├── README.md
└── README_CN.md
```

## 依赖

- [kicad_pro_micro_rp2040](https://github.com/rroels/kicad_pro_micro_rp2040) — Pro Micro RP2040 的 KiCad 符号与封装库
