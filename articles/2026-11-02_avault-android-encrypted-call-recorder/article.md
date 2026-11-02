---
title: "不用 root 的通话录音金库：AVault 用 Shizuku + 硬件 AES-256-GCM 干了件 Android 官方不让干的事"
date: 2026-11-02
slug: avault-android-encrypted-call-recorder
tags: [Android, AVault, 通话录音, Shizuku, rootless, AES-256-GCM, KeyStore, StrongBox, TEE, 加密金库, 隐私, 供应链安全, 开源项目, Kotlin, JetpackCompose, 审计, 文档核对]
category: 安全/开源项目
author: FreeLAMP.com
original_source: "⭐ 一手核对：arpanjot-coding/AVault 仓库源码（VaultEncryptionManager.kt / AppLockManager.kt / RecordingCodec.kt / ShellRecordingEngine.kt / HierarchicalStorageManager.kt / CallsDashboardScreen.kt）+ README 与 SECURITY.md + GitHub API 元数据（实测）"
original_date: 2026-11-02
original_url: "https://github.com/arpanjot-coding/AVault"
description: "AVault 是一个两天前才创建、已经拿到近 500 star 的开源 Android 项目：用 Shizuku 的 rootless ADB shell 桥接拿到 CAPTURE_AUDIO_OUTPUT 等特权，绕过 Android 14+ 对原生通话录音的限制，录到的音频用硬件 KeyStore 里的 AES-256-GCM 主密钥加密成 .vault 容器。本文逐行核对了它的加密实现（KeyStore AES/GCM/NoPadding、12 字节 CSPRNG IV、128 位 GCM Tag、UID 绑定主密钥），并核对了几处文档与代码不一致的地方：README 写的容器头是 \"AVLT\"+版本字节，代码实际是 8 字节 \"AVAULT01\"；README 说 PBKDF2 迭代 100,000，代码是 150,000；README 与 SECURITY.md 描述的「零明文播放」实际是解密到 cacheDir 的临时文件后删除（不是内存管道，代码里没有任何 zero-fill）。结论是：加密部分实现扎实可信，但 README 的规格描述有几处没跟上代码。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **源码**：`VaultEncryptionManager.kt`、`AppLockManager.kt`、`RecordingCodec.kt`、`ShellRecordingEngine.kt`、`HierarchicalStorageManager.kt`、`CallsDashboardScreen.kt`、`SECURITY.md`、`README.md`
> - **GitHub API 元数据**（实测，2026-11-02）：**`arpanjot-coding/AVault`**，创建于 **2026-10-31**，**498 stars / 32 forks**，Kotlin，MIT，**1 个 release（v2.0.0，2026-10-31）**，**9 次提交全部来自单一作者**
> ⚠️ **本文为**解读**。**只做代码与文档的核对，不做安全审计，也不给任何使用建议。**
> ⚠️ **法律边界**：通话录音在多数司法辖区受「一方同意」或「全部同意」规则约束，**本文不提供任何规避或绕过该规则的方法** —— 项目的 README 自己也写了这条例外声明。

## 一句话结论

**⭐ 而这个项目最值得注意的，不是它做了什么，而是它把三件通常被混为一谈的事拆开了：**

```
① 能不能录到（Android 14+ 封了原生通话录音 → 用 Shizuku 免 root 绕过）
② 录到的东西安不安全（传统方案存明文 mp3 → 硬件 KeyStore + AES-256-GCM）
③ 密钥在哪（服务商持钥 vs 用户持钥 —— 这条它没走极端）
```

**⭐ 而我读完源码后的判断是：⭐ 加密部分实现扎实、可信；但 README 的规格描述有几处已经和代码对不上了。**

## 一、它是什么

**⭐ 先把事实摆清楚（GitHub API 实测）：**

| | |
|---|---|
| **仓库** | `arpanjot-coding/AVault` |
| **创建** | **2026-10-31**（⭐ 两天前） |
| **Star / Fork** | **498 / 32** |
| **语言** | Kotlin（76 个 .kt 文件） |
| **License** | MIT |
| **Release** | v2.0.0（2026-10-31） |
| **⭐ 提交** | **9 次，全部来自同一作者（Arpanjot）** |
| **主题** | Android 12–16+、Shizuku、AES-256、rootless、call-recorder |

**⭐ 而「两天 498 star」这个数字，值得单独想一下 —— 它意味着什么？**

**⭐ 我的判断是：⭐ 这更像是「⭐ 需求积压」的信号，而不是「⭐ 技术被认可」的信号。**

**因为：⭐ Android 14 之后原生通话录音基本被废了，而「免 root 录音」这个需求一直有解（Shizuku / ADB shell）。** **所以这个项目吃到的，很可能主要是「⭐ 存量需求」的红利。**

**⭐ 而 9 次提交、单一作者、两个日历日 —— ⭐ 这个项目的成熟度显然还在非常早期。**

## 二、⭐⭐ 核心机制：Shizuku 免 root 拿到特权

### 2.1 为什么需要它

**⭐ README 说得很直接：**

> **「Google introduced strict restrictions on raw call recording in modern Android releases. AVault bypasses these restrictions cleanly without requiring root (`su`), Magisk, or unlocked bootloaders by pairing standard Android Telecom APIs with **Shizuku's rootless ADB shell bridge**.」**

**⭐ 而它用的两个特权是：**
- **`android.permission.CAPTURE_AUDIO_OUTPUT`** —— 抓下行（对方声音）
- **`android.permission.MANAGE_ONGOING_CALLS`** —— 感知通话状态

**⭐ 而 Shizuku 的工作原理，是这个项目最值得理解的一环：**

**⭐ Shizuku 让一个以 UID 2000（shell）运行的守护进程常驻，通过 ADB 启动。** **而 shell 身份天然拥有普通应用拿不到的权限。**

```
AVault（普通应用，无 root）
    ↓ Binder IPC
Shizuku 守护进程（UID 2000 = shell）
    ↓ 执行特权命令
音频捕获 / 通话状态
```

**⭐ 我想强调这一点的原因：⭐ 它解释了为什么这个方案「免 root 但依然有特权」—— **特权来自 shell 身份，而不是来自 root。**

**⭐ 而这也解释了它的一个硬性前提（README 的 Shizuku 章节列了两种启动方式）：**

- **方式 A：设备端无线调试配对**（Android 11+，不需要电脑）
- **方式 B：USB + `adb shell sh /sdcard/Android/data/moe.shizuku.privileged.api/start.sh`**

**⭐ 而「每次重启手机都要重新启动 Shizuku」这个特性，README 把它列进了常见问题：**

> **「'Shizuku Not Running' → Shizuku service was killed by OEM aggressive battery manager. → Open Shizuku and restart via Wireless Debugging.」**

### 2.2 ⭐ 而录音本身，走的是「先编码、再加密」的管线

**⭐ 我核对了编码链（`ShellRecordingEngine.kt` → `AudioEncoder.kt` → `RecordingCodec.kt`）：**

```
PCM 采集 → MediaCodec 编码（Opus/AAC）→ MediaMuxer 写入 ParcelFileDescriptor
```

**⭐ 而这里有个我觉得设计得不错的地方：**

**⭐ `AudioEncoder` 直接把编码后的数据写进 `ParcelFileDescriptor`，而这个 FD 最终指向 `.vault` 文件本身 —— 也就是说 ⭐ 「编码 → 加密 → 落盘」是一条直连的管线，中途不产生明文音频文件。**

**⭐ 代码里 `AudioEncoder` 的注释写得很清楚：**

> **「Encodes PCM audio with Android MediaCodec and writes the encoded samples **directly into the final container** using MediaMuxer.」**

**⭐ 而录音的输出文件创建（`HierarchicalStorageManager.createRecordingFile`）也是直接开 `.vault` 的 FD：**

```kotlin
val pfd = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_WRITE)
```

**⭐ 目录结构是分层的：先按应用类型、再按联系人、再按月份分目录，文件名形如「日期_方向_联系人」。**

## 三、⭐⭐⭐ 加密实现核对：扎实，但文档有三处对不上

**⭐ 这一节是我认为本文最值得的部分 —— 因为「宣传的规格」和「代码实际做的」之间的差，是评估任何安全项目时最该先看的东西。**

### 3.1 ✅ 主密钥：硬件 KeyStore，UID 绑定

**代码（`VaultEncryptionManager.kt`）：**

```kotlin
private const val ANDROID_KEYSTORE = "AndroidKeyStore"
private const val TRANSFORMATION = "AES/GCM/NoPadding"
private const val GCM_TAG_LENGTH = 128
private const val IV_SIZE = 12

val keyGenerator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
    ...
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setRandomizedEncryptionRequired(false) // We manage cryptographically secure IVs explicitly
```

**⭐ 逐项核对：**

| README 声称 | 代码实际 | 结论 |
|---|---|---|
| 硬件 KeyStore 生成 256 位主密钥 | `KeyGenerator.getInstance(AES, "AndroidKeyStore")` | ✅ **相符** |
| AES-256-GCM | `AES/GCM/NoPadding` + 256 位 | ✅ **相符** |
| 12 字节 IV | `IV_SIZE = 12` | ✅ **相符** |
| GCM Tag 128 位 | `GCM_TAG_LENGTH = 128` | ✅ **相符** |
| IV 永不复用 | `SecureRandom().nextBytes(iv)` 每次会话新建 | ✅ **相符** |

**⭐ 而 `setRandomizedEncryptionRequired(false)` 这一行值得单独说 —— 因为它是一个「反直觉但正确」的选择：**

**⭐ 默认情况下，Android KeyStore 会自己生成随机 IV，并禁止你提供。** **而这里关掉了它，改为自己用 `SecureRandom` 生成 —— ⭐ 理由代码注释写了：「We manage cryptographically secure IVs explicitly」。**

**⭐ 这是正确的做法（自己控制 IV 才能保证「每次会话唯一」这个 GCM 的硬性要求），但代价是 ⚠️ **这把「IV 唯一性」的责任从 TEE 转移到了应用代码。**

**⭐ 而 GCM 的安全性完全建立在 IV 唯一上 —— ⭐ 所以这是一个「实现正确才有意义」的约定。**

### 3.2 ✅ 密钥与 UID 绑定

**⭐ README 的排障提示里有一句很实在的话：**

> **「Ensure the app has **not been reinstalled with clean data** (KeyStore keys are **UID-bound**).」**

**⭐ 也就是说：⭐ 重装应用（即使保留了数据）会让主密钥失效，旧录音无法解密。** **这是 KeyStore 的固有行为，不是 bug，但用户必须知道。**

### 3.3 ⚠️ 差异一：容器头的实际格式与 README 不一致

**⭐ README 的二进制格式图写的是：**

```text
| Magic Identifier (0x00-0x03) | Format Version (0x04) | Initialization Vector (0x05-0x10) | ... |
|   4 Bytes "AVLT" (ASCII)        |  1 Byte 0x01 (UINT8)  |   12 Bytes CSPRNG Nonce (GCM)   | ... |
```

**⭐ 而代码里的实际定义是：**

```kotlin
private val MAGIC_HEADER = "AVAULT01".toByteArray(Charsets.US_ASCII)
```

**⭐ 也就是 ⭐ **8 字节 `"AVAULT01"`，而不是 4 字节 `"AVLT"` + 1 字节版本号。**

**⭐ 而 `SECURITY.md` 用的也是 `"AVAULT01"`：**

> **「Call logs, contact names, durations, and bookmark flags are stored with encrypted byte buffers starting with the **`AVAULT01`** signature.」**

**⭐ 所以真相是：⭐ 代码和 SECURITY.md 一致（`AVAULT01`），只有 README 的格式图过时了（`AVLT` + 版本字节）。**

**⭐ 而这个差异的实际影响：⭐ 任何第三方工具想解析 `.vault` 文件，按 README 写会解析错。** **好在还有 `ensureNoMediaFile` 那套 `.nomedia` 机制做索引抑制，文件不会被相册扫到。**

**⭐ 而且要注意：⭐ README 里那个「Format Version 字节」的设计意图是好的（为将来的密码学迁移留版本位），但代码里被字符串吃掉了 —— 所以 ⭐ **「可向后兼容的密码学迁移」这个能力目前实际上不存在。**

### 3.4 ⚠️ 差异二：PBKDF2 迭代次数

**README 声称：**
> **「PIN Hashing: PBKDF2 with HMAC-SHA256, 128-bit cryptographic salt, **100,000 iterations**.」**

**代码（`AppLockManager.kt`）：**
```kotlin
private const val PBKDF2_ITERATIONS = 150_000
```

**⭐ 实际是 150,000 次，比 README 写的多 50%。** **这个方向是好的（更强），只是文档没跟上。**

**⭐ 而 salt 的位数与 README 一致（16 字节 = 128 位）：**
```kotlin
val salt = ByteArray(16).also { SecureRandom().nextBytes(it) }
```

**⭐ 而锁定策略：**
```kotlin
if (failedAttempts >= 5) {
    val lockoutDurationMs = if (failedAttempts >= 8) 60_000L else 30_000L
```

**⭐ 与 README 的「5 次失败 → 30 秒指数退避」基本相符（代码里 8 次以上变成 60 秒）。**

### 3.5 ⚠️ 差异三：「零明文播放」在实现上是「解密到临时文件」

**⭐ 这是我认为最需要说明的一处，因为它是安全宣传里的关键一条。**

**README 的说法很强：**

> **「**Zero-Plaintext Ephemeral Playback**: Decryption occurs on-the-fly directly in **volatile memory** into an isolated POSIX file descriptor (`0600` access) … **The temporary stream is cryptographically shredded the millisecond playback halts.**」**
>
> **「Plaintext audio is **never written to public storage**. Decryption uses **ephemeral in-memory pipes** with instant cryptographic zero-fill upon playback completion.」**

**⭐ 而代码里的实现是（`decryptToTempPlaybackFile`）：**

```kotlin
val cacheDir = File(context.cacheDir, "secure_playback").apply { mkdirs() }
val tempAudio = File(cacheDir, "playback_${System.currentTimeMillis()}_${vaultFile.nameWithoutExtension}.ogg")
return if (decryptFile(vaultFile, tempAudio)) {
    tempAudio.deleteOnExit()
    tempAudio
} else null
```

**⭐ 我把三处不一致列清楚：**

| README 声称 | 代码实际 |
|---|---|
| **「on-the-fly directly in volatile memory」** | ⭐ **解密到 `cacheDir` 下的一个 `.ogg` 文件**（磁盘上的明文文件）** |
| **「isolated POSIX file descriptor (`0600` access)」** | ⭐ **是 `File` 对象，不是 FD**；**代码里没有看到 0600 权限设置** |
| **「cryptographically shredded」「instant cryptographic zero-fill」** | ⭐ **`deleteOnExit()` + `listFiles().forEach { it.delete() }` —— 就是普通删除，没有 zero-fill** |

**⭐ 我在整个仓库里搜过 `fill(0)` / `zeroize` / `shred` / `RandomAccessFile` / `setLength(0)` —— ⭐ 一个都没有。**

**⭐ 而 `clearTempPlayback` 的实现是：**
```kotlin
cacheDir.listFiles()?.forEach { it.delete() }
```

**⭐ 我必须说清楚这意味着什么：**

| | |
|---|---|
| ✅ **好消息** | ⭐ **临时文件在 `cacheDir`（应用私有目录），不是公共存储**；**`.nomedia` 抑制索引**；**播放结束/暂停/应用退到后台时会被清掉**（我在 `CallsDashboardScreen.kt` 里确认了 4 处 `clearTempPlayback` 调用，含 `onDispose`）** |
| ⚠️ **需要修正的说法** | ⭐ **不是「volatile memory」，不是「POSIX FD」，也不是「cryptographically shredded」** —— **是「应用私有目录里的临时明文文件，用普通 delete 删除」** |

**⭐ 而这个差别在什么场景下重要？**

**⭐ **在文件系统未加密的设备上，被 root / 恢复镜像 / 取证的人，有可能在文件被删除前抓到那段明文音频。** **而这恰恰是本项目要防的攻击者能力。**

**⭐ 所以我的判断是：⭐ 加密保存那一步是可靠的；⭐ 「零明文」这一步是宣传过头了。**

### 3.6 ✅ 而「安装介质」的加密流程倒是真的做了

**⭐ 我还发现一个 README 没细说、但代码里确实有的东西 —— `encryptExistingRecordings`：**

```kotlin
/**
 * Scans storage for existing unencrypted recordings, encrypts them into .vault files,
 * securely removes the plain audio, and updates the repository.
 */
fun encryptExistingRecordings(context: Context): Int
```

**⭐ 也就是说：⭐ 已经存在的明文录音可以被扫描、加密进 `.vault`、然后删掉明文。** **这是对「升级前录的旧文件」的一次补救 —— 而这恰恰是很多同类项目会漏掉的一环。**

## 四、⭐ 威胁模型：它防什么、不防什么

**⭐ README 有一张威胁模型表，我核对后认为**整体是诚实的**，但有两处值得单独说。**

| 威胁 | 项目的缓解 | 我的核对 |
|---|---|---|
| **物理提取设备** | 硬件 AES-256-GCM，无 TEE 主密钥 + PIN/生物识别则磁盘字节是随机熵 | ✅ 相符 |
| **恶意 App 扫媒体库** | `.vault` 扩展名 + `.nomedia` | ✅ 相符（代码里有 `ensureNoMediaFile`）** |
| **⭐ 冷启动 / 内存转储** | 「解密用易失内存管道 + 播放后立即 zero-fill」 | ⚠️ **不成立** —— 见 3.5 |
| **间谍软件截屏** | `FLAG_SECURE` | ✅ 相符 |
| **PIN 暴力破解** | PBKDF2 + 指数退避 | ✅ 相符（迭代次数是 150,000 而非 100,000）** |

**⭐ 而我认为需要补充的两条「它不防的」：**

**① 通话另一端的对方，并不知道自己的声音被录了。** **⭐ 而「双方同意」在这里不成立。**

**② ⭐ Shizuku 守护进程本身是个高价值目标。** **它以 shell 身份常驻，是这个方案的信任根。** **如果手机上装了恶意应用、或者用户自己从可疑来源装了另一个 Shizuku 风格的 shell 守护进程 —— ⭐ 那么「加密保存」这层的意义会被绕过（因为攻击者可以直接读明文音频流）。**

**⭐ 而这一点在 README 的威胁模型里没有出现。**

## 五、⭐⭐ 而我更想说的是：这个项目的「文档 vs 代码」差距

**⭐ 我在核对时发现的规律很一致：⭐ **README 的「理念描述」和代码的「实际实现」之间存在系统性偏移。**

| 维度 | README 的描述 | 代码的实际 |
|---|---|---|
| 容器头 | `AVLT` + 版本字节 | `AVAULT01`（8 字节，无版本位）** |
| PIN 迭代 | 100,000 | **150,000**（更强）** |
| 播放 | 内存管道 / FD / zero-fill | **cacheDir 临时文件 + 普通 delete**（更弱）** |
| PIN 哈希 | PBKDF2 | **PBKDF2（带 legacy SHA-256 兼容路径，自动升级）**（更复杂）** |

**⭐ 而 SECURITY.md 又和 README 不一致（SECURITY.md 说 `AVAULT01`、说「custom SHA-256 salted PIN」）。**

**⭐ 我的总体评价是：⭐ **这个项目的安全设计思路是对的，代码实现也基本可靠；但它的文档没有跟上代码 —— 而对于一个主打「高保障加密」的项目，这一点尤其不该发生。**

**⭐ 因为 README 里那张二进制格式图，是唯一能让第三方工具解析 `.vault` 的规范 —— ⭐ 而它写错了。**

**⭐ 而反过来也要说公道话：⭐ 三处差异里有两处（迭代次数、legacy SHA-256 兼容）是代码比文档更谨慎。** **这说明作者是「先写实现、后补文档」，而不是「文档吹得比实现好」—— ⭐ 这两者的性质完全不同。**

## 六、⭐⭐ 我想提的一个更根本的问题

**⭐ 而看完全部代码后，我最想说的其实不是实现细节，而是这个项目暴露出的一个结构性事实：**

**⭐ 传统通话录音 App 的问题不是「没有加密」，而是 ⭐ 「明文文件躺在公共存储里，任何有存储权限的 App 都能读」。**

**⭐ 而 Android 14 之后，真正的问题变成了 ⭐ **「连录都录不成了」**。**

**⭐ 于是出现了这个很有意思的组合：**

```
需求：「我要合法地录下自己的通话，并且不泄露」
  ↓
Android 14+ 的原生限制 → 必须绕
  ↓
绕过手段 = Shizuku（UID 2000 的 shell 守护进程）
  ↓
⭐ 而「UID 2000 的 shell 守护进程」这个信任根，
   它的可用性完全依赖「开发者选项 + 无线调试配对」这两件事
```

**⭐ 我认为这暴露了一个更深的问题：⭐ **在移动操作系统把「通话录音」列为受限能力之后，围绕它的所有「合规需求」都只能靠「非官方特权通道」来满足 —— 而这条通道的安全等级，恰好等于它所替代的那个方案。**

**⭐ 而这才是这个项目真正值得被讨论的地方 —— 不是它的加密做得好不好（做得不错），而是 ⭐ **它的存在本身说明了 Android 权限模型的一个缺口。**

## Sources

- ⭐ 一手：[arpanjot-coding/AVault](https://github.com/arpanjot-coding/AVault)（GitHub API 元数据实测：创建于 2026-10-31、498 stars / 32 forks、Kotlin、MIT、9 次提交单一作者、v2.0.0 release）
- ⭐ 一手（源码核对）：
  - `system/security/VaultEncryptionManager.kt` —— KeyStore / AES-GCM / IV / `AVAULT01` 头 / `decryptToTempPlaybackFile` / `encryptExistingRecordings`
  - `system/security/AppLockManager.kt` —— PBKDF2 150,000 次、16 字节 salt、锁定退避、legacy SHA-256 兼容
  - `data/recording/RecordingCodec.kt`、`services/shell/recording/ShellRecordingEngine.kt`、`services/shell/recording/encoding/AudioEncoder.kt` —— 编码直写 FD 管线
  - `system/storage/HierarchicalStorageManager.kt` —— `.vault` 创建与目录分层
  - `ui/screens/CallsDashboardScreen.kt` —— 播放与 `clearTempPlayback` 调用点
  - `SECURITY.md`、`README.md` —— 与代码的对照
- 一手：[Shizuku](https://shizuku.rikka.app) —— rootless ADB shell 桥接
- 一手：[Android KeyStore 文档](https://developer.android.com/privacy-and-security/keystore)
- 一手：[NIST SP 800-38D（GCM）](https://csrc.nist.gov/publications/detail/sp/800-38d/final)

---

（说明：本文所有关于代码行为的描述均来自**实测拉取的仓库源码**，所有关于仓库元信息的数字来自 **GitHub API 实测（2026-11-02）**；**第三、五节的差异分析为笔者核对结论**；**本文不构成安全审计，也不提供任何使用或法律合规建议**。）
