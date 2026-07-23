<div align="center">

  <h1>dekisugiwin</h1>
  <p><strong>基于 Windows 原生架构的高效 Mihomo (Clash Meta) 运行环境与管控面板</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue?style=flat-square&logo=windows" alt="Platform">
    <img src="https://img.shields.io/badge/Core-Mihomo%20(Clash%20Meta)-purple?style=flat-square" alt="Core">
    <img src="https://img.shields.io/badge/GUI-C%23%20WinForms-brightgreen?style=flat-square" alt="GUI">
    <img src="https://img.shields.io/badge/License-GPL%203.0-blue.svg?style=flat-square" alt="License">
  </p>
</div>

## ✨ 核心特性

- **高度集成的原生架构**: 采用 C# 与 WinForms 构建的单文件（Standalone Executable）管控平台，摒弃了传统跨平台框架所带来的环境依赖与资源开销，提供低延迟的底层系统交互。
- **强制化配置流 (Configuration Enforcement)**: 
  - **自定义模式**：支持多订阅并行介入。针对订阅配置采取动态解析策略，通过底层正则引擎根据参数填入状态自动挂载或卸载路由规则组，避免空载引发的内核异常。
  - **原生模式**：针对第三方下发的未经安全审计的代理配置，执行标准化的配置覆写策略。程序会在拉取配置后，通过流处理自动剔除存在冲突风险的本地端口及外部控制器定义，并重新注入标准化的本地管控参数，确保内核运行的绝对稳定性。
- **模块化前后端分离**: 控制面板 (`dekisugiwin.exe`) 专注于 Windows 底层环境抽象（包含进程守护、权限跃迁、环境预检），而复杂的路由节点渲染及连接监控则交由托管的 Web 引擎 (Zashboard) 处理。
- **UWP 环回隔离解除**: 集成了基于 Windows 底层 API 的 UWP (Universal Windows Platform) 环回隔离豁免工具，可一键赋予本地回环网络权限，解决系统级应用的网络受限问题。

---

## 📂 项目目录结构

```text
dekisugiwin/
├── dekisugiwin.exe             # 控制面板与底层守护服务的主程序
│
├── bin/                        # 二进制运行库依赖目录
│   ├── clash-amd64.exe         # Mihomo (Clash Meta) 代理内核
│   └── ICSharpCode.AvalonEdit.dll # 代码编辑器组件的动态链接库
│
└── config/                     # 配置数据与离线数据库目录
    ├── default.yaml            # 自定义模式的静态基础模板配置
    ├── config.yaml             # 代理核心实际挂载的动态配置文件
    ├── original.yaml           # 原生模式下被程序安全覆写后的配置文件 (运行后生成)
    ├── GeoSite.dat             # 域名路由分流地理数据库 (离线必须)
    ├── geoip.metadb            # IP 路由分流地理数据库 (离线必须)
    └── settings.xml            # 面板持久化状态与出厂参数配置存储
```

> **注**：在程序运行期间，根目录下会自动生成诸如 `proxies/`、`rules/`、`Web/` 等缓存目录与运行时数据库缓存，面板会自动从指定仓库同步 Web UI 资源并进行本地化托管。

---

## 🎮 运行机制与使用指南

### 1. 启动与模式切换
执行根目录下的 **`dekisugiwin.exe`** 以唤起管理界面。
程序提供了两种标准的配置运行逻辑：
- **自定义配置**：面向复杂路由场景。面板会自动根据您填写的订阅地址，在后台重组 YAML 的分流结构并动态解除或挂起指定的 Proxy-Providers。
- **原生配置**：面向标准订阅场景。填入服务商订阅后，程序将在后台内存中执行配置覆写，将外部面板控制权收归本地，剔除危险端口，生成符合本地安全策略的配置文件。

### 2. 状态可视化与路由管理
当内核进程成功拉起后，用户可通过主面板右上角的 **`🌐 打开面板`** 按钮，访问基于浏览器渲染的 Zashboard 控制端。
所有关于节点探测、策略组调度及网络请求日志的分析均在此环境中独立运行，避免干扰主程序的系统级调度。

### 3. UWP 网络层修复
若在代理开启后发现部分 Windows 应用商店程序无法建立网络连接，可使用面板底部的 **`🚀 解除全部应用限制`** 功能。该功能将请求提权并调用系统网络管理命令，对注册表内的所有 AppContainer 容器进行环回网络授权豁免。

---

<div align="center">
  <p>Made with ❤️ by the open-source community</p>
</div>
