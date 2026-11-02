---
title: "改一个 APK 的完整链路：从 smali 改一个布尔值，到 zipalign、apksigner，以及那条唯一的顺序铁律"
date: 2026-11-02
slug: patching-apks-smali-dex-rebuild-signing
tags: [Android, APK, DEX, Smali, baksmali, apktool, apksigner, zipalign, 逆向工程, 签名机制, v1v2v3v4签名, aapt2, jadx, 打包, 应用安全, 多dex, 64K限制, 教程, 应用商店]
category: 安全/技术教程
author: FreeLAMP.com
original_source: "⭐ 一手核对：YourDev.net《Patching APKs: Smali, DEX, Rebuild, and Resigning》（Maximilian Cornett，2026-10-29，29 分钟长文）"
original_date: 2026-11-02
original_url: "https://www.yourdev.net/blog.php?post=patching-apks-smali-dex-rebuild-and-signing"
description: "一篇把「改 APK」从玄学变成可复现流程的深度教程：从 APK 到底是什么（ZIP + 编译后的二进制 manifest + resources.arsc + DEX），到 DEX 的六张索引表与 0x70 字节头部每个偏移的含义，再到 smali 作为「DEX 的文本视图」为什么存在（因为反编译的 Java 是有损的，而二进制 DEX 人读不了）、64K 方法/字符串/字段引用上限如何逼出 multidex、以及三条工作流的取舍（apktool 全量重建 / --no-res 只动代码 / 直接改 DEX 二进制）。本文还完整梳理了签名机制：v1 到 v4 各自在证明什么、为什么 Android 11+ 实际要求 v2、以及整条链路上唯一不能违反的顺序铁律 —— build → zipalign → apksigner，一旦倒序 v2/v3 立刻失效。"
published: true
---

> **原文**：Maximilian Cornett，《Patching APKs: Smali, DEX, Rebuild, and Resigning》，YourDev.net，**2026 年 10 月 29 日**
> 原文链接：<https://www.yourdev.net/blog.php?post=patching-apks-smali-dex-rebuild-and-signing>
> **本文为解读与整理**，保留了原文的技术要点、命令与表格结构；⭐ 标记处为笔者的补充说明。
> ⚠️ **法律与伦理边界**（原文自己的声明，我完整保留）：**只修改你自己拥有、自己构建、或获得明确许可的 APK。** **重新打包他人的应用会破坏其签名、更新路径，通常也违反其服务条款，且在某些司法辖区可能违法。**

## 一句话结论

**⭐ 而这篇教程真正的价值，是它把一件通常被当成「玄学」的事拆成了三件可以分别理解的东西：**

```
① DEX 是什么          → 一个**寄存器型**字节码容器（不是 JVM 字节码）
② Smali 为什么存在      → 因为**反编译的 Java 是有损的，而二进制 DEX 人读不了**
③ 签名在证明什么        → **不是「谁签的」，而是「自洽」+「更新必须同钥匙」**
```

**⭐ 而整条链路上，只有一条规则是不能违反的：**

```
build  →  zipalign  →  apksigner  →  （之后绝不再动任何字节）
```

**—— 顺序倒过来，v2/v3 签名立刻失效。**

## 一、60 秒心智模型

**⭐ 原文的第一张图就把整条链路画清了：**

```
Kotlin/Java source
      │  kotlinc / javac
      ▼
JVM .class files            （栈式字节码，一个类一个文件）
      │  d8（发布构建则用 R8）
      ▼
classes.dex                 （寄存器型 Dalvik 字节码，所有类在一个文件里）
      │  zip  +  aapt2（资源） +  apksigner
      ▼
app.apk
```

**⭐ 而 smali 在这个图里的位置，原文说得很准确：**

> **「Smali is not a compilation target. It is a textual rendering of an existing DEX file, produced by a disassembler (baksmali) and consumed by an assembler (smali). **Editing smali is editing the DEX, just in a form you can read.**」**

```
classes.dex  ──baksmali──▶  smali/  （可读文本）
     ▲                          │
     └────────smali─────────────┘   （在中间编辑）
```

**⭐ 而 apktool 的全部秘密，原文一句话就说完了：**

> **「apktool wraps exactly this: `apktool d` = unzip + decode resources + baksmali; `apktool b` = smali + aapt2 + zip. **That is the whole trick.**」**

## 二、APK 里到底有什么

```
app.apk (ZIP)
├── AndroidManifest.xml        二进制 XML（AXML），不是文本
├── resources.arsc             编译后的资源表（二进制）
├── classes.dex                代码（多 dex 时还有 classes2.dex、classes3.dex …）
├── res/                       编译后的资源文件（布局、drawable…）
├── lib/<abi>/lib*.so          原生库
├── assets/                    原样打包的原始文件
└── META-INF/                  v1（JAR）签名文件 —— MANIFEST.MF、*.SF、*.RSA
```

**⭐ 而原文紧接着点出了**「两个决定其他一切的推论」** —— 我认为这是全文最该被记住的一段：**

> **「- AndroidManifest.xml and res/ are **compiled, not plain text**. You cannot edit them with a text editor; you need a decoder (apktool) and a rebuilder (aapt2). **That is why "just unzip and rezip" so often produces an APK that won't install or crashes on startup.**」**
>
> **「- META-INF/ is a **signature over the ZIP's contents**. Any change to any byte invalidates it. So the moment you edit a DEX, the app is unsigned from Android's point of view, and you must re-sign before installing.」**

**⭐ 我认为第一点解释了很多新手最常见的困惑：⭐ **「为什么我 unzip 一下再 zip 回去，APK 就装不上了？」** —— 因为 manifest 和资源都是编译产物，zip 回去之后 Android 读不懂 AXML 和 arsc。**

**⭐ 而第二点是整篇文章的起点：⭐ **「签名是对 ZIP 内容的签名」** —— 这就决定了后面所有的顺序问题。**

**⭐ 还有一个实用细节：** `apktool d` 会把未改动的原件留在 `original/` 目录（`original/META-INF`、`original/AndroidManifest.xml`），而 `apktool b -c`（`--copy-original`）可以复用它们。**

## 三、⭐ DEX 深入：六个索引表与 0x70 字节的头

### 3.1 DEX 是什么

**⭐ 原文的定义很精准：**

> **「DEX ("Dalvik Executable") is the bytecode container that Android Runtime (ART) loads. It is a single flat file holding every class in the app, with all strings, types, prototypes, fields, and methods **interned into shared, indexed tables**. **Cross-class references become 16-bit/32-bit integer indices instead of names**, which is what makes it compact.」**
>
> **「It is an **instruction set architecture**, like x86 or ARM — **not a programming language**. There is no syntax, no expressions, no scoping. There is only a byte stream plus a documented layout.」**

**⭐ 而「DEX 不是 JVM 字节码」这条，原文专门强调了：**

> **「Note: **DEX is not JVM bytecode**. .class files are **stack-based**; DEX is **register-based**. d8 performs that translation. This is why a .class file and a .dex file for the same class **look nothing alike**, and why you cannot just rename one to the other.」**

### 3.2 文件布局

```
┌───────────────┬──────────────────────────────────────────────┐
│ header        │ 0x00 – 0x6F (112 bytes)                      │
├───────────────┼──────────────────────────────────────────────┤
│ string_ids    │ 指向 MUTF-8 字符串的偏移                      │
│ type_ids      │ string_ids 的索引（类型描述符）                │
│ proto_ids     │ 方法签名（返回类型 + 参数）                    │
│ field_ids     │ {class, type, name} 三元组                    │
│ method_ids    │ {class, proto, name} 三元组                   │
│ class_defs    │ 每个类一个：它的数据在哪                      │
├───────────────┼──────────────────────────────────────────────┤
│ data          │ 字符串字节、类型列表、code item、调试信息、      │
│               │ 注解、静态值、map_list                        │
└───────────────┴──────────────────────────────────────────────┘
```

**⭐ 而头部里「值得记住」的字段，原文列了一张表 —— 我挑出**最关键的四条**，因为它们直接决定了「手改 DEX 后为什么加载不了」：**

| 偏移 | 字段 | 含义 |
|---|---|---|
| **0x00** | magic | `dex\n035\0` … `dex\n040\0`（格式版本）** |
| **0x08** | **checksum** | **从 0x0C 到 EOF 的 Adler-32** |
| **0x0C** | **signature** | **从 0x20 到 EOF 的 SHA-1** |
| 0x20 | file_size | 文件总长度 |

**⭐ 而原文对这两个校验字段的说明，是我认为整个 DEX 部分最有价值的一句：**

> **「The checksum and signature fields are why a **hand-edited DEX is rejected until you recompute them**. Everything from **0x0C** onward is covered by the checksum, and everything from **0x20** onward is covered by the signature — and **the checksum field (at 0x08) is itself inside the signed region**, so **the order matters: signature first, then checksum**.」**

**⭐ 我把这条整理成一个可以直接照做的清单：**

```
改完 DEX 字节后：
  ① signature (0x0C) = SHA-1( bytes[0x20:] )     ← 先算
  ② checksum (0x08) = Adler-32( bytes[0x0C:] )   ← 后算
```

**—— 而「checksum 自己在签名区内」这个细节，是最容易踩的坑。**

### 3.3 code item 与变长指令

**⭐ 原文的关键点：**

> **「Instructions are **1–5 code units long, variable length**, and operate on registers named v0, v1, …」**
>
> ```smali
> const/4 v0, 0x1          # 1 code unit  (2 bytes)
> invoke-virtual {v0}, Ljava/lang/Object;->toString()Ljava/lang/String;   # 3 code units
> ```
>
> **「Because instruction length depends on the encoded value (const/4 vs const/16 vs const), **inserting or growing code changes byte offsets everywhere after it**. **That is the central difficulty of editing DEX directly, and the reason a textual assembler exists.**」**

**⭐ 我认为这句「指令长度依赖编码值 → 插入代码会让后面所有偏移都变」是理解「为什么不能直接改 DEX」的核心。**

### 3.4 ⭐ 硬限制：64K，以及它如何逼出 multidex

| 限制 | 值 | 后果 |
|---|---|---|
| **每个 DEX 引用的方法数** | **65,535**（method_ids 是 16 位）** | **64K 方法上限 → multidex** |
| 每方法的寄存器数 | 65,535 | 只有超大方法才受影响 |
| 字符串索引（非 jumbo） | 65,535 | 汇编器自动切到 `/jumbo` |
| 字段引用数 | 65,535 | 同类问题 |
| 指令索引范围 | 有符号 16 位分支偏移 | 超大方法无法汇编 |

**⭐ 而原文接下来的这句解释了一个很多人不解的现象：**

> **「classes.dex, classes2.dex, … **each have their own 64K budget**. apktool decodes them to `smali/`, `smali_classes2/`, `smali_classes3/`, … and reassembles each directory back into the matching DEX name.」**

**⭐ 我把它当成一条实用规则：⭐ **看到一个 APK 有 `classes3.dex`，你就知道它超过了 64K 方法 —— 而修改时必须改对目录，否则补丁打在了另一个 DEX 上。**

## 四、Smali 深入：它为什么存在

**⭐ 原文对 smali 的定义：**

> **「Smali is the assembly syntax for DEX. Every DEX instruction has a smali mnemonic with the same name (invoke-virtual, iget-object, const-string), and every reference is written **symbolically** instead of as an index:」**
>
> ```smali
> invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
> ```
>
> **「Same instruction, but now you can read the class, the method, the parameter type, and the return type. **That is the entire value proposition.**」**

**⭐ 而第 6 节「为什么两者都存在」给了一个我觉得是全文最好的解释：**

> **「**Why DEX exists**: DEX exists for **density, fast loading, and verifiability**. It is **not meant to be edited by hand**.」**
>
> **「**Why smali exists**: Smali exists because **decompiled Java is lossy** and binary DEX is not human-editable. It is the easiest editable representation.」**

**⭐ 我把这三句话连起来，就得到了整个 smali 工具链存在的理由：**

```
Java 反编译（jadx）  →  有损（控制流被重建，不是原始逻辑）→ 不可用于精确修改
DEX 二进制            →  精确，但人读不了                → 不可用于精确修改
       ↓
    Smali              →  精确 + 可读                     → ✅ 唯一可用的编辑形态
```

**⭐ 而原文还诚实地点出 smali 的一个局限：**

> **「Smali is **lossless in the forward direction**: baksmali → text → smali gives you a semantically equivalent DEX. It is **not guaranteed byte-identical** (the string pool and code-item ordering can be [reordered]).」**

**—— 语义等价，但不保证字节一致。这对「打完补丁后与原版对比」有实际影响。**

## 五、⭐ 三条工作流的取舍

**⭐ 原文给出了三条路径，而它对每条路径的适用场景说得很清楚 —— 这是这篇教程最有实用价值的部分。**

### 5.1 工作流 A：标准 apktool 循环（90% 的情况）

```
apktool d app.apk -o decoded  ──▶  decoded/  （编辑 smali）
                                        │ apktool b
                                        ▼
                                  unsigned.apk
                                        │ zipalign
                                        ▼
                                  aligned.apk
                                        │ apksigner
                                        ▼
                                    signed.apk
                                        │ adb install
                                        ▼
                                      device
```

**⭐ 而原文的 12 个步骤里，我认为有三个是「新手最容易漏、但影响最大」的：**

**① Step 0 —— 保留一份原始副本**

```
cp app.apk app.original.apk
sha256sum app.apk app.original.apk
```

**⭐ 原文的话：**

> **「You will compare against this when something breaks. **Never debug on your only copy.**」**

**② Step 4 —— 把解码后的目录纳入版本控制**

```
cd decoded && git init && git add -A && git commit -m "pristine decode" && cd ..
```

**⭐ 原文的评价：**

> **「Now every patch is a **reviewable diff**, and reverting is trivial. **This is the single biggest quality-of-life improvement in this workflow.**」**

**③ Step 5 —— 编辑时的五条规则**

原文列的规则我原样保留（这几条是真正会咬人的）：

> - **保持 `.registers` / `.locals` 与你用到的最高寄存器一致**
> - **保留返回类型** —— `Z` 方法必须用 `v0` 返回 0/1；`V` 方法必须 `return-void`
> - **不要删掉你不需要删的 `.line` / `.local` 指令** —— 它们无害，还能让 diff 更小
> - **⭐ 如果新增了寄存器，在任何可能读到它的分支之前先初始化它**（`const/4 vX, 0x0`），否则验证器可能报「未初始化寄存器」
> - **不要改方法签名或类名**，除非你同时修了所有调用方

**⭐ 而第三条我觉得最值得强调：⭐ **「不要删掉你不需要删的东西」** —— 这和「最小改动原则」是一回事。**新手常犯的错是「顺手清理一下」，结果删掉了 `.line` 指令，虽然语义不变，但 diff 变大、也更容易碰到边界问题。**

### 5.2 工作流 B：只动代码，不重建资源

**⭐ 原文给出的两条子路径：**

- **B1：`apktool d --no-res`**（只解资源则更快，或反过来 `--no-src` 只解资源）
- **B2：完全不用 apktool，直接 `baksmali` / `smali`**
- **B3：程序化重写（dexlib2 / R8 / d8）**

**⭐ 而这一条工作流的适用场景，原文说得很准：⭐ **「Use `-c` / `--copy-original` when you only changed smali and the resource rebuild is causing trouble.」** —— 也就是**只改了代码、但资源重建老出错**时的解法。**

### 5.3 ⭐⭐ 工作流 C：直接改 DEX 二进制（外科手术）

**⭐ 而这是我认为整篇文章里最需要小心读的一节，因为它是「看起来能做，其实限制极多」的那种。**

**⭐ 原文先划了可用边界：**

> **「Only when the patch is **the same number of bytes**: flipping a constant that fits the same encoding, changing a branch target within range, or swapping a register number. Example: `const/4 v0, 0x0` → `const/4 v0, 0x1` is **one changed nibble in a 2-byte instruction**.」**

**⭐ 然后给了定位方法（这个技巧很实用）：**

```
dexdump -d classes.dex | grep -n -A4 "isPro"
xxd -s 0x1234 -l 16 classes.dex
```

**⭐ 而更好的办法是 `baksmali d --code-offsets`，它会给每条指令标出字节偏移。**

**⭐ 改完字节后必须修头部，原文给了完整脚本：**

```python
#!/usr/bin/env python3
"""Recompute DEX checksum + signature after an in-place patch."""
import hashlib, struct, sys, zlib
path = sys.argv[1]
data = bytearray(open(path, "rb").read())
assert data[:4] == b"dex\n", "not a dex file"
# 1) SHA-1 over everything after the 32-byte magic+checksum+signature area
data[12:32] = hashlib.sha1(bytes(data[32:])).digest()
# 2) Adler-32 over everything after the checksum field
struct.pack_into("<I", data, 8, zlib.adler32(bytes(data[12:])) & 0xFFFFFFFF)
open(path, "wb").write(data)
print("fixed", path)
```

**⭐ 注意注释里的顺序 —— 「1) SHA-1」在「2) Adler-32」之前 —— ⭐ 这正是前面「checksum 字段本身在签名区内」的必然结果。**

**⭐ 而原文对「为什么这条路径脆弱」列了五条，⭐ 每一条我都认为是真实的坑：**

> - **指令是变长的。插入一个字节会让后续所有偏移、`code_item.insns_size`、try/catch 范围、`map_list` 偏移、以及字符串/类型表的基址全部错位。** ⭐ **「A naive hex insert produces a DEX that parses as garbage.」**
> - **头部的 `file_size` 必须与实际长度一致**
> - **分支偏移是相对且范围受限的** —— 移动代码可能让目标越界
> - **⭐ ART 的验证器会重新做类型检查** —— ⭐ **「a byte-level change that "looks right" can still throw VerifyError」**
> - **多 dex 时必须改对 `classesN.dex`**，而且跨 DEX 的引用是运行时解析的

**⭐ 而原文的结论句非常克制但很到位：**

> **「direct DEX patching is a **scalpel for same-size edits**. For anything else, **use smali (Workflow A/B) or dexlib2**.」**

## 六、⭐⭐⭐ 签名：v1 到 v4 各自在证明什么

### 6.1 ⭐ 而最该先想明白的：签名到底证明什么

**⭐ 原文这句话是整个签名部分的题眼：**

> **「Android does not care **who** signed the APK; it cares that **the signature is self-consistent** and that **updates use the same key as the installed app**.」**

**⭐ 我把它拆成四个直接后果：**

| | |
|---|---|
| **任何修改都会使签名失效** | ⭐ **「There is no "edit and keep the signature" shortcut (that would break the cryptography).」** |
| **重新打包的应用装不到原版之上** | ⭐ **因为钥匙不同** |
| **⭐ 自检签名的应用会立刻发现** | ⭐ **「`PackageManager.getPackageInfo` with `GET_SIGNATURES`/`GET_SIGNING_CERTIFICATES`、Play Integrity、SafetyNet、证书固定（certificate pinning）」** —— ⭐ **「That is a server/attestation problem, not a packaging problem.」** |
| **上 Play 商店需要原始上传钥匙** | |

**⭐ 我认为第三条最容易被低估，而原文那句「这是服务端/证明问题，不是打包问题」点得非常准：**

**—— 就算你把客户端的签名自检全 patch 掉了，⭐ 服务端的 Play Integrity 校验你改不了。**

### 6.2 v1 / v2 / v3 / v4 各是什么

**⭐ 原文用四段话讲清了，我原样保留（这是全文最难记住的部分）：**

**⭐ v1（JAR 签名）**
> **「META-INF/MANIFEST.MF lists SHA-256 digests of every entry; CERT.SF signs the manifest; CERT.RSA holds the signer's certificate and signature. Verification is **per-entry**, which is slow and vulnerable to "master key"-style ZIP parsing bugs. **Still required for API < 24.**」**

**⭐ v2**
> **「A signature block embedded just before the ZIP central directory, covering the **entire APK** (all bytes, including the central directory). Fast, whole-file verification; detects any modification. **Required for installs on Android 11+ (targetSdk 30+) in practice.**」**

**⭐ v3**
> **「Same idea as v2 with a **key-rotation proof**, allowing an app to change signing keys across versions. **Android 9+.**」**

**⭐ v4**
> **「A detached `.idsig` file used for **incremental/streaming installs via adb**; it is **not part of the APK** and is not required for normal distribution.」**

**⭐ 我把这四个版本的差别压成一张对照表：**

| | 签名在哪 | 覆盖范围 | 校验粒度 | 用途 |
|---|---|---|---|---|
| **v1** | `META-INF/` 内 | ZIP 每个条目 | ⭐ **逐条目** | **API < 24 必需** |
| **v2** | ⭐ **中央目录之前** | ⭐ **整个 APK（含中央目录）** | 整文件 | ⭐ **Android 11+ 实际必需** |
| **v3** | 同 v2 | 同 v2 | 整文件 | ⭐ **支持换签名钥匙**（Android 9+）** |
| **v4** | ⭐ **独立的 `.idsig`** | — | — | **adb 增量/流式安装** |

### 6.3 ⭐⭐⭐ 而整条链路上唯一的顺序铁律

**⭐ 原文把它称为「the one ordering rule」，而且给了理由：**

```
build → zipalign → apksigner → (never modify again)
```

> **「Signing **hashes** bytes; alignment **moves** bytes. **Reverse the order and v2/v3 fail.** If you must re-zipalign a signed APK, **re-sign it afterwards.**」**

**⭐ 我想把这句再翻译得更直白一点：**

**—— 签名是对「某一时刻的字节」算的哈希。而 zipalign 会移动字节。所以如果你先签名再对齐，⭐ 签名算的是对齐前的内容，对齐后全变了。**

### 6.4 ⭐ 而 zipalign 那一步为什么存在（以及它救过多少人）

**⭐ 原文的说明：**

> **「- zipalign makes every uncompressed entry start at a **4-byte boundary** so ART can **mmap them directly instead of copying**.」**
>
> **「- `-p` **page-aligns uncompressed .so files** (required for `extractNativeLibs=false` and for API 23+ in practice).」**
>
> **「- Android 11+ (API 30) additionally requires `resources.arsc` to be **stored uncompressed and 4-byte aligned**. apktool writes it stored; **zipalign fixes the offset**.」**
>
> **「- ⭐ **apksigner must run after zipalign**: the v2+ signature covers the whole file, so any later byte move destroys it.」**

**⭐ 而原文还给了一条非常实用的排错经验：**

> **「If you ever see `Failure: resources.arsc not stored uncompressed`, the APK was **rezip'd with a tool that compressed it**; **rebuild with apktool rather than fighting zip**.」**

**⭐ 我觉得这一条的价值在于它区分了两类错误：**

| 症状 | 真正的原因 | 正确做法 |
|---|---|---|
| `resources.arsc not stored uncompressed` | ⭐ **不是 zipalign 没跑，是重新打包的工具把它压缩了** | ⭐ **用 apktool 重建，别跟 zip 较劲** |
| 装不上 / 启动崩溃 | ⭐ **manifest 和资源是编译产物** | ⭐ **必须用 apktool 解码 + aapt2 重建** |

## 七、⭐⭐ 排错与验证清单

**⭐ 原文的第 14、15 节是「照着做就不用踩坑」的部分，我挑最实用的列出来。**

**⭐ 验证签名与安装：**

```
apksigner verify --verbose --print-certs signed.apk
adb install -r signed.apk
adb logcat -c && adb logcat -s AndroidRuntime:E
```

**⭐ 而「验证补丁的完整性」这一组命令，我觉得是原文最容易被忽略但最有价值的：**

```
cd decoded && git diff          # ⭐ 看清楚你到底改了什么
sha256sum app.apk app.original.apk signed.apk
```

**—— 把原版、补丁版、签名版三个哈希放在一起，才能确认「我改的确实是我以为改的那点」。**

### 7.1 ⭐⭐ 而「现实检查」这一节，是全文最有价值的收尾

**⭐ 原文列了一堆「你改不动」的东西，我按「能不能改」分类：**

| 障碍 | 能不能客户端绕过 | 说明 |
|---|---|---|
| **签名自检 / Play Integrity / SafetyNet** | ⚠️ **客户端能 patch 服务端不能** | ⭐ **原文：「server-side validation cannot be patched on the client at all」** |
| **代码混淆（R8/ProGuard）** | ✅ 可以，但难读 | ⭐ **「smali is still readable as instructions but names are meaningless」—— 改用行为（字符串、API 调用、控制流）定位，而不是靠名字** |
| **原生代码（`lib/*/lib*.so`）** | ⚠️ **要 native RE（IDA/Ghidra/radare2）** | ⭐ **「often invalidates more invariants」** |
| **资源完整性自检** | ⚠️ 很难 | ⭐ **有些应用启动时对自己的资源或 DEX 做哈希 —— **任何重建都会触发**** |
| **Split APK / App Bundle** | ⚠️ **要先转 universal** | ⭐ **「Bundles must be converted (`bundletool build-apks --mode=universal`) before patching」** |
| **⭐ 更新** | ❌ **不可能** | ⭐ **「A patched app cannot receive Play updates; the store's signature will not match. **Keep an unmodified copy.**」** |

**⭐ 我认为最后一条值得单独强调：⭐ **改过的应用从此拿不到官方更新了** —— 这不是技术限制，是 Android 更新机制的必然结果（⭐ **商店的签名对不上**）。**

## 八、⭐⭐⭐ 我的评价

### 8.1 ⭐⭐ 而这篇教程最值得学的是它的「反面教材」写法

**⭐ 我注意到原文在讲每个坑的时候，都先说「为什么会这样」，而不是直接给命令。**

**⭐ 举三个例子：**

| 原文的讲法 | 为什么重要 |
|---|---|
| **「指令长度依赖编码值 → 插入代码会改变后面所有偏移 → 所以需要文本汇编器」** | ⭐ **先讲清「为什么不能直接改」，你才知道「为什么推荐 smali」** |
| **「checksum 字段本身在签名区内 → 所以要先算签名再算校验和」** | ⭐ **顺序不是随意的，是被布局强制的** |
| **「签名哈希字节，对齐移动字节 → 顺序反了 v2/v3 就失败」** | ⭐ **同理，顺序是机制决定的，不是习惯** |

**⭐ 我认为这比「记住这个命令序列」有价值得多 —— 因为命令序列会变（apktool 3.x、新的 zipalign 行为），但机制不会变。**

### 8.2 ⭐⭐ 而「三视图」这个框架，是我认为全文最漂亮的一个组织方式

```
DEX    → 二进制、精确、寄存器型、人读不了、专为密度/快速加载/可验证而生
Smali  → 文本、精确（语义等价）、符号化、人可读 —— 唯一可用的编辑形态
Java   → 文本、有损（控制流被重建）、人可读 —— 只用于「理解」，不用于「修改」
```

**⭐ 而原文的分工说得极清楚：**

> **「Use **jadx to understand, smali to locate the exact instructions.**」**
>
> **「jadx-gui is better for browsing; note that when jadx **fails to decompile a method it prints the smali instead** — **that is your bridge.**」**

**⭐ 我想指出「jadx 解不出来时就打印 smali」这个细节 —— ⭐ 它实际上把 jadx 和 smali 串成了一条连续的路径，而不是两个竞争的工具。**

### 8.3 ⭐⭐ 而关于「合法边界」，我认为原文的措辞值得原样保留

**⭐ 原文开头那段法律声明，我认为比很多同类文章写得都更到位：**

> **「Only patch APKs you own, that you built yourself, or that you have explicit permission to modify. **Repackaging someone else's app breaks its signature, its update path, and usually its terms of service, and can be illegal depending on where you live.**」**

**⭐ 我注意到的关键点：⭐ 原文没有用「仅供教育用途」这种含糊的免责 —— 而是把**实际后果**列了出来：签名、更新路径、服务条款、以及司法辖区。**

**⭐ 而我认为这一条也正好接上了本号此前写过的几篇：⭐ **《选择无聊的技术》里那句「多语言编程是蛇油」，和这里的「重新打包别人的 app」其实是同一类提醒 —— ⭐ **有些事情技术上完全可行，但它的可行本身不构成理由。**

**⭐ 而我特别想指出：⭐ **这篇文章里最实用的技术 —— 直接改 DEX 二进制、patch 签名自检 —— 恰好也是最不该被用在别人软件上的那些。** **因为那些技术**唯一有意义的场景**，就是修改别人加了保护的应用。**

**⭐ 而这正是「文档写了 = 应该会有人做」和「文档写了 = 应该标清边界」的差别。**

## Sources

- ⭐ 一手：[YourDev.net — Patching APKs: Smali, DEX, Rebuild, and Resigning](https://www.yourdev.net/blog.php?post=patching-apks-smali-dex-rebuild-and-signing)（Maximilian Cornett，2026-10-29，29 分钟长文，17 个章节）
- 一手：[Android 开发者文档 — APK 格式与签名](https://developer.android.com/studio/publish/app-signing)
- 一手：[apktool 官方文档](https://apktool.org/docs/)
- 一手：[Android `apksigner` 文档](https://developer.android.com/studio/command-line/apksigner)
- 一手：[Android `zipalign` 文档](https://developer.android.com/studio/command-line/zipalign)
- 一手：[smali / baksmali（JesusFreke）](https://github.com/JesusFreke/smali)
- 相关：本号此前的《不用 root 的通话录音金库：AVault》—— ⭐ **同一个 Android 生态，一个是消费级应用（加密金库），一个是底层打包与逆向的工具链**

---

（说明：本文为原文的解读与整理，保留了原文的技术要点、命令、表格与「现实检查」一节；**第八节的「三视图框架」「反例教学法」与「合法边界」分析为笔者观点**。）
