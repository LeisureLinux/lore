#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文章标题规范检查器。

检查两条硬性规则（2026-11-06 用户明确要求）：

1. **标题必须以具体产品名开头做主语**——主语越具体越好，不让读者猜。
   涉及 Linux 的用「Linux」开头。**禁止把产品名放到标题末尾**。
2. 标题长度适中（参考 45 字上限），不堆砌夸大词。

用法：
    python3 tools/check_title.py <article.md> [<article.md> ...]
    python3 tools/check_title.py --all           # 检查全部文章
    python3 tools/check_title.py --all --newest  # 只检查最近 10 篇

退出码: 1 = 有 ERROR（标题不合规，发布前必须改）; 0 = 通过。
"""
import argparse
import os
import re
import sys

LORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(LORE, "articles")

# ---- 产品名词表 -----------------------------------------------------------
# 规则：标题开头命中其中任一即视为「以产品名开头」。
# 分两类：
#   CORE   —— 通用产品/项目名（OpenSSH、Debian…）
#   LINUX  —— 涉及 Linux 的统一用这些词开头（Linux 内核 / Linux 发行版 / Linux 桌面…）
CORE = {
    # 虚拟化 / 虚拟化平台
    "xen", "kvm", "qemu", "vmware", "virtualbox", "hyperv", "proxmox",
    "xcp-ng", "qubes", "openstack", "cloudstack", "nutanix", "esxi",
    # 安全 / 加密
    "openssh", "ssh", "openssl", "gnupg", "gpg", "letsencrypt", "certbot",
    "age", "sops", "vault", "keycloak", "authy", "pam", "sudo",
    "alpine", "debian", "ubuntu", "fedora", "rhel", "centos", "suse",
    "opensuse", "arch", "gentoo", "void", "nixos", "manjaro", "mint",
    "kali", "raspberry", "raspberrypi", "pop-os", "zorin", "elementary",
    "eMudhra".lower(), "digicert", "entrust", "globalsign", "sectigo",
    "comodo", "letencrypt", "cloudflare", "fastly", "akamai",
    # 语言 / 运行时
    "rust", "go", "golang", "python", "php", "ruby", "perl", "node",
    "nodejs", "deno", "bun", "java", "kotlin", "swift", "zig", "nim",
    "c", "c++", "cpp", "javaScript".lower(), "typescript", "lua",
    # 工具链 / 数据库 / 中间件
    "git", "gcc", "llvm", "clang", "cmake", "make", "bazel", "ninja",
    "docker", "podman", "kubernetes", "k8s", "containerd", "runc",
    "podman-compose", "helm", "terraform", "ansible", "puppet", "chef",
    "nix", "nixpkgs", "guix", "redis", "postgres", "postgresql", "mysql",
    "mariadb", "sqlite", "mongodb", "elasticsearch", "kafka", "rabbitmq",
    "nginx", "apache", "caddy", "envoy", "traefik", "haproxy",
    "systemd", "dbus", "glibc", "musl", "coreutils", "busybox",
    "openssl", "curl", "wget", "bash", "zsh", "fish", "tmux", "screen",
    "vim", "neovim", "emacs", "nano", "kitty", "alacritty", "wezterm",
    "ghostty", "iterm", "terminator", "ripgrep", "fd", "bat", "fzf",
    "htop", "btop", "glances", "nmap", "wireshark", "tcpdump", "strace",
    "ltrace", "gdb", "lldb", "perf", "valgrind", "eBPF".lower(),
    "bpf", "systemtap", "bpftrace", "openssl",
    # 桌面 / 显示
    "xorg", "wayland", "gnome", "kde", "plasma", "xfce", "mate", "cinnamon",
    "lxde", "lxqt", "tde", "sway", "hyprland", "niri", "river", "i3",
    "dwm", "qt", "gtk", "sdl", "wayfire", "labwc", "cosmic",
    "nvidia", "amd", "intel", "arm", "riscv", "loongarch", "mips",
    "raspberrypi", "jetson", "orangepi", "rockchip", "allwinner",
    # AI / 模型
    "openai", "anthropic", "claude", "gpt", "chatgpt", "gemini", "llama",
    "mistral", "deepseek", "kimi", "qwen", "gemini", "copilot", "codex",
    "cursor", "windsurf", "zed", "vscode", "codeberg", "github", "gitlab",
    "gitea", "sourcehut",
    # 其它
    "postman", "insomnia", "curl", "wget", "redis", "elasticsearch",
    "grammarly", "notion", "obsidian", "logseq", "joplin",
    "wikimedia", "wikipedia", "phantomjs", "nodejs",
    "eBPF".lower(), "io_uring", "kvm", "kexec", "systemd-oomd",
    "freebsd", "netbsd", "openbsd", "dragonfly", "midnightbsd",
    "illumos", "solaris", "aix", "hpux", "hp-ux", "truenas", "openmediavault",
    "unraid", "synology", "qnap", "esxi", "proxmox",
    "wireshark", "burpsuite", "metasploit", "nmap", "zgrab",
    "cve", "ghsa", "cert", "tls", "ssl", "dns", "bgp", "ospf",
    "wireguard", "openvpn", "tailscale", "zerotier", "netsh",
    "nftables", "iptables", "ebpf", "cilium", "calico", "flannel",
    "vscode", "jetbrains", "eclipse", "netbeans",
    "docker", "podman", "lxc", "incus", "systemd-nspawn",
    "syncthing", "nextcloud", "owncloud", "seafile",
    "bitwarden", "keepass", "lastpass", "1password",
    "prometheus", "grafana", "zabbix", "nagios", "icinga",
    "haproxy", "keepalived", "consul", "etcd", "zookeeper",
    "openssl", "wolfssl", "mbedtls", "bearssl",
    "jupyter", "colab", "kaggle", "huggingface", "pytorch", "tensorflow",
    "ollama", "vllm", "llama.cpp", "langchain", "litellm", "mcp",
    # ---- 从本仓库历史文章标题反查补充（2026-11-06）----
    "google", "chrome", "firefox", "windows", "bsd", "unix", "gnu",
    "bytedance", "bytespider", "tiktok", "doubao", "volcano engine",
    "control web panel", "cwp", "cwpsrv", "cwpdoor", "centos web panel",
    "vercel", "chrome", "dbsc", "device bound session", "tpm", "secure enclave",
    "gputaskman", "nvml", "wddm", "rocm", "hip", "amdgpu", "kfd", "vram",
    "secwrap", "seccomp", "ebpf", "bpf", "kprobe", "kretprobe", "ptrace",
    "virtme-ng", "virtme", "vng", "qemu", "kvm", "virtiofs", "virtiofsd",
    "darling", "darlinghq", "wine", "proton", "winetricks", "appkit",
    "asahi linux", "asahi", "omarchy", "m1n1", "honeykrisp", "borealis",
    "saas", "rd&d", "ip", "artcraft", "gimp", "jevons", "baumol",
    "gravity linux", "aurora silicon", "dhh", "omacom", "copyleft",
    "gpl", "lgpl", "mit", "bsd", "sourcehut",
    "corecrypto", "dynarmic", "vibedarling", "tiobe", "flutter", "dart",
    "clean-room", "quirk", "agentsmd",
    "overlayfs", "microvm", "bzimage", "vmlinuz", "initrd", "libvirt",
    "virsh", "kexec", "cow", "copy-on-write", "9p", "virtio-blk",
    "strace", "landlock", "firejail", "bubblewrap", "tetragon", "falco",
    "opensnitch", "sandlock", "cgroup", "lsm", "quickshell", "noctalia",
    "forgerock", "openidm", "ping identity", "pingidm", "openam", "apache felix",
    "felix", "osgi", "crest", "ropc", "mfa", "waf", "idm", "saml", "oauth",
    "llamacpp", "ollama", "pytorch", "cuda", "nvidia", "radeon", "npu",
    "unigine", "valley", "drm", "sysfs", "procfs", "huggingface", "vllm",
    "cachyos", "omarchy", "arch linux", "archlinux", "manjaro", "endeavouros",
    "hyprbsd", "freebsd", "openbsd", "netbsd", "dragonfly", "ghostbsd",
    "illumos", "opensolaris", "openindiana", "solaris", "hellosystem", "pc-bsd",
    "hyprland", "sway", "lumina", "cde", "illumosfb", "zfs", "bectl",
    "forgejo", "pkg", "freebsd-pkg", "opensource", "illumos-gate",
    "garuda", "mint", "pop os", "nixos", "framework", "strix halo",
    "kde plasma", "plasma", "gnome", "hyprland", "sway", "xfce", "budgie",
    "mesa", "wayland", "xorg", "radeon", "ryzen", "ryzen ai", "nvidia geforce",
    "infostealer", "cookie", "google workspace", "bitwarden", "okta", "auth0",
    "entra id", "microsoft entra", "keycloak", "jumpcloud", "onelogin",
    "fastly", "akamai", "imperva", "f5", "citrix", "netscaler", "zscaler",
    "varonis", "saviynt", "beyondtrust", "cyberark", "sailpoint", "keeper",
    "cpanel", "plesk", "webmin", "webmin", "plesk", "directadmin",
    "barracuda", "qanxin", "xlab", "e943a", "cwpdoor",
    "cloudflare", "spider", "crawler", "metasploit", "burp", "zap", "w3af",
    "pwnescape", "omarchy", "loongleak", "reactos", "samba", "budgie",
    "netscaler", "noctalia", "esp32", "plex", "tp-link", "vite+",
    "zram", "gartner", "libreoffice", "ext4", "icann", "snapdragon",
    "rembrandt", "lineageos", "linus", "asterinas", "npm", "npu",
    "nothing", "risc-v", "riscv", "libreboot", "timescale", "rpki",
    "starling", "acpi", "flatpak", "tee", "magento", "secure",
    "pingcap", "qbittorrent", "emaki", "freedns", "ghostbsd", "goahead",
    "hakios", "stalwart", "php2shell", "ipfs", "freerdp", "gitbook",
    "windowsupdate", "microsoft", "apple", "oracle", "meta", "opencl",
    "mesa", "wayland-security", "pipewire", "wireguard-go", "tpm",
    "tpm2", "ima", "evm", "selinux", "apparmor", "seccomp",
    "crun", "youki", "firecracker", "cloudhypervisor", "nomad",
    "consul-template", "vault", "boundary", "teleport",
    "rustls", "boringssl", "wolfssl", "mbedtls",
    "clickhouse", "doris", "starrocks", "tidb", "oceanbase",
    "temporal", "airflow", "dagster", "prefect",
    "grafana-loki", "tempo", "mimir", "victoria", "clickhouse-operator",
    "cilium-cli", "cilium-cni", "calico-typha", "tigera",
    "openshift", "rke2", "k3s", "microk8s", "k0s", "kubespray",
    "flux", "argocd", "tekton", "spinnaker",
    "pulsar", "kafka-connect", "debezium", "flink", "spark",
    "hadoop", "hive", "presto", "trino", "duckdb",
    "parquet", "arrow", "iceberg", "delta", "hudi",
    "nvme", "sata", "scsi", "mmc", "ufs", "bluetooth", "wifi",
    "waydroid", "anbox", "termux", "postmarketos",
    "nixos-flake", "home-manager", "devbox", "guix-system",
    "alacritty", "wezterm", "contour", "foot", "warp", "hyper",
    "nvim", "lua", "rustls", "deno", "bun",
    "podman-compose", "buildah", "skopeo", "umoci",
    "zpool", "zfs", "btrfs", "xfs", "f2fs", "nilfs", "jfs",
    "bcachefs", "erofs", "squashfs", "cramfs", "initramfs",
    "dracut", "mkinitcpio", "systemd-boot", "grub", "shim", "sbverify",
    "ukify", "systemd-sysupdate", "rauc", "swupdate", "mender",
    "coreboot", "seabios", "ovmf", "edk2", "tpm2-tools",
}

# 涉及 Linux 的：允许以这些组合开头
LINUX = {
    "linux",                      # Linux xxx
    "linux 内核", "linux内核",      # Linux 内核 xxx
    "linux 发行版", "linux发行版",
    "linux 桌面", "linux桌面",
    "linux 基金会",
    "linux 内核作者", "linux 鼻祖", "linux鼻祖",
    "linux 上游", "linux 社区",
}

# 中文起头的具体主体（机构 / 产品 / 专有名词），也算「以产品名开头」
CN_PRODUCT = {
    # 机构 / 政府
    "白宫", "欧盟", "美国", "中国", "工信部", "网信办", "国家安全部",
    "openssh基金会", "linux基金会", "apache基金会", "rust基金会",
    "免费软件基金会", "gnome基金会", "debian", "canonical",
    # 中文技术名词（够具体的）
    "内核", "发行版", "桌面环境", "容器", "虚拟机", "镜像", "引导程序",
    "固件", "内核模块", "系统调用", "文件系统", "存储池",
    "浏览器", "终端", "包管理器", "构建系统", "编译器", "解释器",
    "开源项目", "开源社区", "社区", "基金会",
}

# 非产品开头 —— 这些词开头基本等于「没点名产品」
NON_PRODUCT_START = {
    "一个", "一条", "一张", "一次", "一份", "一段", "一组", "一款", "一份",
    "为什么", "怎么", "如何", "什么", "哪些", "谁", "是",
    "从", "把", "让", "用", "我", "你", "它", "他们", "我们",
    "关于", "对", "在", "这", "那", "这个", "那个", "这些", "那些",
    "别", "不要", "不再", "所有", "每个", "更多", "更好", "最",
    "当", "如果", "因为", "所以", "然后", "于是",
}

# 夸大词（标题禁区）
HYPE = {"颠覆", "革命", "新纪元", "史诗", "终极", "最强", "无敌", "震撼",
        "炸裂", "逆天", "王炸", "降维打击"}

MAX_LEN = 45


def _norm(t):
    """归一化：去书名号内的内容标记、压空白。"""
    return re.sub(r"\s+", " ", t).strip()


def starts_with_product(title):
    """判断标题是否以具体产品名开头。返回 (bool, 命中的产品名)。"""
    t = _norm(title)
    if not t:
        return False, ""

    # 去掉开头的引号/书名号
    t = t.lstrip("「『\"'《（(").strip()

    low = t.lower()

    # Linux 组合优先
    for k in LINUX:
        if low.startswith(k.lower()):
            return True, k

    # 中文具体主体
    for k in CN_PRODUCT:
        if low.startswith(k.lower()):
            return True, k

    # 直接匹配核心产品名（允许后接空格、冒号、版本号、顿点等）
    for k in CORE:
        kl = k.lower()
        if low == kl:
            return True, k
        if low.startswith(kl):
            nxt = low[len(kl):len(kl) + 1]
            # 后面是分隔符或空白 → 认为是以该产品名开头
            if nxt == "" or nxt in " ：:，,、·—-/（(「" or nxt.isspace():
                return True, k

    return False, ""


def product_at_end(title):
    """检测「产品名被放在标题末尾」。

    判定：标题的**最后一段**（冒号/破折号之后）是否**基本就是**一个产品名。
    若末段还带着谓语（「OpenAI 把漏洞研究做成…」），则产品名在中间，不算末尾。
    """
    t = _norm(title)
    low = t.lower().rstrip("。．.！!？?，,、 ")
    tail = re.split(r"[：:]|——|—", t)[-1].strip()
    tail_low = tail.lower()
    for k in CORE:
        kl = k.lower()
        # 整个标题以该产品名结尾
        if low.endswith(kl):
            return k
        # 末段几乎就是一个产品名（允许版本号/编号等尾巴，不允许带谓语）
        if tail_low.startswith(kl):
            rest = tail_low[len(kl):].strip()
            # rest 只能是版本号 / 编号 / 修饰性字符（不能有谓语或实词）
            if len(rest) <= 16 and not re.search(r"[\u4e00-\u9fff]", rest) \
                    and not re.search(r"\b(is|are|was|were|has|have|and|or|the)\b", rest):
                return k
    return ""


def check_title(title):
    """返回 (errors, warnings)。"""
    errors, warnings = [], []
    t = _norm(title)

    if not t:
        return ["标题为空"], []

    ok, product = starts_with_product(t)

    if not ok:
        first = t.lstrip("「『\"'《（(").split(" ")[0].split("，")[0]
        if first in NON_PRODUCT_START or not product:
            errors.append(
                f"标题未以具体产品名开头（当前开头「{first}」）——"
                f"主语要越具体越好，不要让读者猜。"
                f"涉及 Linux 的用「Linux」开头"
                f"（如「Linux 内核 7.4 …」「Linux 发行版 …」）；"
                f"产品名不要放末尾")

    tail_prod = product_at_end(t)
    if tail_prod and ok:
        warnings.append(
            f"产品名「{tail_prod}」出现在标题末尾——"
            f"建议提到最前面做主语（如「{tail_prod} ……」）")

    if len(t) > MAX_LEN:
        warnings.append(f"标题 {len(t)} 字，超过 {MAX_LEN} 字参考上限")

    hits = [h for h in HYPE if h in t]
    if hits:
        warnings.append(f"标题含夸大词 {hits}（标题禁区）")

    return errors, warnings


def article_title(path):
    """从 article.md 读 front matter 的 title。"""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None
    m = re.match(r"^\s*---[ \t]*\n(.*?)\n---[ \t]*$", content, re.S | re.M)
    if m:
        mt = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', m.group(1), re.M)
        if mt:
            return mt.group(1)
    mt = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.M)
    return mt.group(1) if mt else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="article.md 路径")
    ap.add_argument("--all", action="store_true", help="检查全部文章")
    ap.add_argument("--newest", type=int, default=0,
                    help="只检查最近 N 篇（配合 --all）")
    ap.add_argument("--quiet", action="store_true", help="只输出问题项")
    args = ap.parse_args()

    targets = list(args.files)
    if args.all or not targets:
        dirs = sorted(d for d in os.listdir(ARTICLES)
                      if os.path.isdir(os.path.join(ARTICLES, d)))
        if args.newest:
            dirs = dirs[-args.newest:]
        targets = [os.path.join(ARTICLES, d, "article.md") for d in dirs]

    n_err = n_warn = 0
    for p in targets:
        if not os.path.exists(p):
            print(f"❌ 文件不存在: {p}")
            n_err += 1
            continue
        title = article_title(p)
        if title is None:
            print(f"❌ 读不到 title: {p}")
            n_err += 1
            continue
        errs, warns = check_title(title)
        slug = os.path.basename(os.path.dirname(p))
        if errs or warns:
            if errs:
                n_err += 1
            if warns:
                n_warn += 1
            print(f"\n{'❌' if errs else '⚠️ '} {slug}")
            print(f"   标题：{title}")
            for e in errs:
                print(f"   ERROR: {e}")
            for w in warns:
                print(f"   WARN:  {w}")
        elif not args.quiet:
            ok, prod = starts_with_product(_norm(title))
            print(f"✅ {slug}  [产品名: {prod}]")

    print(f"\n{'=' * 50}")
    print(f"检查 {len(targets)} 篇：有 ERROR {n_err} 篇，有 WARNING {n_warn} 篇")
    if n_err:
        print("❌ 有标题不符合规范，发布前必须修改")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
