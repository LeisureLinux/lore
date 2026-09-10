# libzmq 支持了 VSOCK：ZMQ 应用从此可以跑进 Hypervisor 通信面

> 译文来源：Rémi Jouannet 博客《Use VSOCK with libzmq》（blog.remijouan.net）。原文：<https://blog.remijouan.net/posts/libzmq-vsock-pyzmq/>

## VSOCK 是什么

VSOCK 已不算新东西——**Linux 4.8 起进入内核**。它的前身是 VMware 开发的 VMCI。`AF_VSOCK` 是一个套接字地址族，和 `AF_INET`、`AF_UNIX` 并列，专为**虚拟机（guest）与宿主机（hypervisor/host）之间**的通信设计，同一台宿主机上的多个 guest 之间也可以互通。在这之前，这类通信走的是串口——Proxmox 的 [qemu-guest-agent](https://pve.proxmox.com/wiki/Qemu-guest-agent) 就是典型例子。

VSOCK 用起来的观感是"**Unix socket 的形态 + TCP/UDP 的特性**"：有地址、有端口，也分流式（stream）和数据报（datagram）两种。

- 地址是 32 位的"上下文标识符"（CID），保留值包括 `VMADDR_CID_ANY`、`VMADDR_CID_HYPERVISOR`、`VMADDR_CID_LOCAL`（5.6 新增）、`VMADDR_CID_HOST`；
- 端口也是 32 位，**1024 以下需要 root**——和 TCP/UDP 一个脾气；
- 同一个 CID 可以靠不同端口跑多路通信。

参考手册：[vsock(7)](https://man7.org/linux/man-pages/man7/vsock.7.html)。

多年下来 VSOCK 生态在缓慢生长：Python/C/Go/Rust 都有支持，AWS 的 **Nitro Enclaves** 就靠它做 enclave 与宿主的通信。相关资源：

- socat 的 vsock 支持（[Stefano Garzarella](https://stefano-garzarella.github.io/posts/2021-01-22-socat-vsock/)）
- Go 的 [VM sockets](https://mdlayher.com/blog/linux-vm-sockets-in-go/)、Rust 的 [tokio-vsock](https://github.com/rust-vsock/tokio-vsock)
- [Python socket.AF_VSOCK](https://docs.python.org/3/library/socket.html#socket.AF_VSOCK)

## libzmq 里的 VSOCK：一次"照抄式"贡献

问题在于：想用 VSOCK 时你手里只有**最底层的绑定**——poll、recv、send、bind、listen 全要自己来。这时候自然想起 [ZeroMQ](https://zeromq.org/)：它在几乎所有类型的 socket 上封装了消息模式和工程实践，甚至带安全特性（[CurveZMQ](http://curvezmq.org/)）。

作者的意外发现是：libzmq 里有 [VMCI 实现](https://libzmq.readthedocs.io/en/latest/zmq_vmci.html)，却**没有 VSOCK**。于是他提交了 [PR #4822](https://github.com/zeromq/libzmq/pull/4822)——照着 VMCI 的代码"复制粘贴"级别地补上了 VSOCK。

这个组合的价值：

| 能力 | 说明 |
|---|---|
| 语言全解锁 | 所有有 libzmq 绑定的语言（Python/Ruby/Node.js/Perl/Java/Lua…）都直接能用 `AF_VSOCK` |
| 模式继承 | req/rep、pub/sub 等 ZMQ 消息模式跑在 VSOCK 上 |
| 安全继承 | Curve 认证直接可用 |
| 嵌入式友好 | libzmq 发布节奏慢但极稳，很容易按特定 commit 静态编译进嵌入式系统 |

正式版尚需时日，作者先 fork 了 pyzmq 按最新 libzmq commit 构建：[pyzmq-vsock](https://github.com/remijouannet/pyzmq-vsock)。

## 动手：先在 loopback 上跑通 Hello World

Linux 5.6 起有 loopback CID（`VMADDR_CID_LOCAL`），**不用真开 VM 就能测**。ZMQ 里用 `@` 直接绑定 loopback。要模拟真实 guest/host 场景，QEMU 命令行加一个 vsock 设备即可（libvirt 同理）：

```sh
export CID=100
/usr/local/bin/qemu-system-x86_64 \
    ...
    -device vhost-vsock-pci,id=vhost-vsock-pci0,guest-cid=$CID
```

服务端（REP）与客户端（REQ），改动只有 URI——`vsock://@:5555`：

```python
# rep.py —— Hello World server
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("vsock://@:5555")

while True:
    message = socket.recv()
    print(f"Received request: {message}")
    time.sleep(1)          # 模拟干活
    socket.send(b"World")
```

```python
# req.py —— Hello World client
import zmq

context = zmq.Context()
print("Connecting to hello world server…")
socket = context.socket(zmq.REQ)
socket.connect("vsock://@:5555")

for request in range(5):
    socket.send(b"Hello")
    message = socket.recv()
    print(f"Received reply {request} [ {message} ]")
```

```sh
# vsock_loopback 大概率没加载：
# sudo modprobe vsock_loopback

python3 -m venv venv
venv/bin/pip install <pyzmq-vsock 的 manylinux wheel>

venv/bin/python3 rep.py &
venv/bin/python3 req.py
# Sending request 0 …
# Received request: b'Hello'
# Received reply 0 [ b'World' ]
# ...循环 5 次，全部成功
```

## 进阶：Curve 认证 + asyncio（生产形态）

Hello World 之后，生产大概率是 **asyncio + Curve**。作者把 pyzmq 官方的 [asyncio-ironhouse](https://github.com/zeromq/pyzmq/blob/main/examples/security/asyncio-ironhouse.py) 示例改到了 VSOCK 上：先 `zmq.curve_keypair()` 生成三组密钥（server、client、client2）存 JSON；REP 侧 `curve_server = True`（**必须在 bind 之前设置**），绑 `vsock://@:9000`，用 `AsyncioAuthenticator` 只放行已知 client key；REQ 侧带上自己的密钥对和 server 公钥去 connect。

跑起来，认证通过时：

```sh
[DEBUG] ALLOWED (CURVE) domain=* client_key=b'HhdIwzo4=…'
[DEBUG] ZAP reply code=b'200' text=b'OK'
[INFO] Received b'Hello'
[INFO] Ironhouse test OK
```

换成未授权密钥，服务端直接拒绝：

```sh
[DEBUG] DENIED (CURVE) domain=* client_key=b'P4//#^+&*…'
[DEBUG] ZAP reply code=b'400' text=b'Unknown key'
# 客户端侧：No reply: server rejected this client key
```

## 我们的解读

**VSOCK 的价值是"通信面隔离"。** guest 与 host 之间不需要虚拟网卡、不经过网络栈、不占 IP 规划——这既是便利更是安全边界：guest 无法把 vsock 当跳板去扫 host 的网络。对 enclave、沙箱 agent、guest agent 这类"宿主与受控方点对点对话"的场景，VSOCK 是比 TCP 更贴合的传输层。AWS Nitro Enclaves 选它不是偶然。

**ZMQ 的核心设计此时显现红利：传输与语义解耦。** libzmq 把传输层做成可插拔（inproc/ipc/tcp/pgm/vmci/vsock…），应用层的消息模式、认证、重连逻辑一行不改。这次贡献的成本低到"照抄 VMCI"，正说明传输抽象的成色——对应用开发者，从 `tcp://@:5555` 换到 `vsock://@:5555` 只是换了个 URI。

**两个现实提醒：** 一是 libzmq 发版保守，VSOCK 还在 master，生产要用得像作者一样按 commit 自建（pyzmq-vsock 的 wheel 可以直接用）；二是踩坑点很集中——`vsock_loopback` 模块要手动 modprobe、`curve_server` 必须在 bind 之前设置、端口 1024 以下要 root。

**对国产虚拟化生态的参照：** Proxmox/KVM 系（含国内基于 KVM 的私有云、信创虚拟化平台）里，guest agent 通信长期依赖串口方案。VSOCK + ZMQ 这套组合给出了一个更现代、可加密、可订阅推送的替代模板，值得做云平台 agent 和 EDR/探针类产品的团队参考。

---

*参考：[原文](https://blog.remijouan.net/posts/libzmq-vsock-pyzmq/) · [libzmq vsock 文档](https://github.com/zeromq/libzmq/blob/master/doc/zmq_vsock.adoc) · [PR #4822](https://github.com/zeromq/libzmq/pull/4822)*
