# 从找回 Thunderbird 密码说起：pwdecrypt 原理与 libnss3-tools 全实操

> 本文源于一次真实需求：需要用阿里云邮件推送的 SMTP 账号给自动化系统发邮件，但密码忘了、也不想重置。密码就存在本机 Thunderbird 的凭据库里。最终用 NSS 自带的 `pwdecrypt` 一行命令解出，顺带把 `libnss3-tools` 这套被低估的证书管理工具链完整梳理了一遍。文中账号一律以 `user@example.com` 代称。

## 一、背景：Mozilla 是怎么存你密码的？

Firefox 和 Thunderbird 共用同一套 NSS（Network Security Services）凭据存储，核心是三个文件：

| 文件 | 内容 | 状态 |
|---|---|---|
| `logins.json` | 各条目：站点 URL + **加密后的**用户名和密码 | 字段全是密文 |
| `key4.db` | 解密用的**主对称密钥** + 盐/KDF 参数 | 受主密码保护 |
| `cert9.db` | 证书信任库 | 明文 |

很多人以为浏览器存的是密码 hash，其实不是。自动填表需要**还原明文**，所以它存的是真加密：

```
logins.json 里每个字段 ≈ base64( 版本号 | 密钥ID | 算法标识 | IV | AES-CBC 密文 )
```

解密链路是三层嵌套：

```
主密码 (Primary Password)
   └─ PBKDF2/scrypt + 全局盐 → KEK（密钥加密密钥）
        └─ 解开 key4.db 里的对称密钥
             └─ 解密 logins.json 各条目
```

**关键点：如果没设置主密码，Mozilla 用一个"空密码"走同样的流程**——KEK 等于任何人都能算出来，等于没加密。

### 用 pwdecrypt 解密实操

`pwdecrypt` 是 NSS 的官方调试工具，随 `libnss3-tools` 包安装：

```bash
# 0) 安装（Debian/Ubuntu）
sudo apt install libnss3-tools

# 1) 不碰正在运行的 Thunderbird（避免 db 锁冲突），拷贝相关文件到临时目录
P=~/.thunderbird/<你的profile>.default-release   # 看 profiles.ini 或挑最近修改的那个
T=$(mktemp -d)
cp "$P/key4.db" "$P/logins.json" "$P/cert9.db" "$P/pkcs11.txt" "$T/"

# 2) 提取目标条目的两个密文字段（encryptedUsername / encryptedPassword）
python3 - <<'EOF' > $T/lines.txt
import json
d = json.load(open("logins.json"))
for l in d["logins"]:
    if "smtp.example.com" in l["hostname"]:     # 换成你要找的主机名
        print(l["encryptedUsername"])
        print(l["encryptedPassword"])
EOF

# 3) 解密
pwdecrypt -d "$T" < $T/lines.txt
# Decrypted: "user@example.com"
# Decrypted: "********"

# 4) 清理现场
rm -rf "$T"
```

`pwdecrypt -d <profile目录>` 做的事就三步：

1. `NSS_Init(profile)` 打开该目录的 `key4.db`，初始化软令牌（softokn）
2. 从内部 slot 按 keyID 取出对称密钥（这一步会触发主密码校验；设了主密码就要 `-p <主密码>` 提供）
3. 对 stdin 每行 base64 解码 → 按 IV/密文结构做 AES/3DES 解密，失败则原样回显

⚠️ **安全启示：不设主密码 = 本机任何程序都能拿走你全部保存的密码**。建议立刻给 Thunderbird 设上主密码（设置 → 隐私与安全），代价只是每次启动输一次。

---

## 二、libnss3-tools 全家桶概览

这个包里有 29 个工具，都是 NSS 加密底座（Firefox/Chrome/大量 Linux 服务共用）的命令行操作面板。按用途分五类：

- **证书管理**：certutil ⭐、vfychain、ocspclnt、derdump、pp、nss-addbuiltin
- **私钥/加密对象**：pk12util ⭐、modutil、symkeyutil、shlibsign、pwdecrypt ⭐
- **PKCS#7/CMS 消息**：p7sign/p7verify/p7content/p7env、cmsutil、crlutil
- **TLS 测试**：selfserv ⭐、tstclnt ⭐、ssltap ⭐、httpserv、strsclnt、rsaperf、vfyserv
- **对象签名（遗留）**：signtool、signver

下面逐个讲高频工具的具体用法。

---

## 三、certutil 深度实操

### 0. 前置概念：`-d` 与 `sql:` 前缀

certutil 所有操作都围绕一个 **NSS 数据库目录**（内含 `cert9.db/key4.db`）：

```bash
-d sql:/path/to/dbdir      # sql: 表示新版 SQLite 格式（cert8/key3 是 legacy 格式，别用）
```

常见数据库位置：

```bash
~/.mozilla/firefox/*.default-release          # Firefox
~/.thunderbird/*.default-release              # Thunderbird
/etc/pki/nssdb                                # RHEL 系系统级库
~/sql:./mydb                                  # 自己建的
```

### 1. 列出证书库内容 + 看懂信任位

```bash
certutil -L -d sql:$HOME/.mozilla/firefox/abc123.default-release
```

输出形如：

```
Certificate Nickname                Trust Attributes
                                    SSL,S/MIME,JAR/XPI

DigiCert Global Root CA             CT,C,C
GlobalSign Root CA                  CT,C,C
My Company Internal CA              u,u,u        ← 你导入但未授信的
```

**信任位三个位置分别对应 SSL / S/MIME(邮件) / 代码签名**，每个位置的字母含义：

| 字母 | 含义 |
|---|---|
| `p` | 有效 peer 证书（可对端验证） |
| `P` | 可信 peer（隐含 p，用于直接导入的服务器证书） |
| `c` | 有效 CA |
| `C` | 可信 CA——可以签发**服务器**证书 |
| `T` | 可信 CA——可以签发**客户端**证书（SSL 位）/ 邮件签名证书（Email 位） |
| `u` | 该证书本身可用于当前会话 |
| `w` | 发送告警 |

所以一个标准根 CA 通常标 `CT,C,C`；只信任它签服务器证书就是 `,C,`。

### 2. 创建新的空 NSS 数据库

```bash
mkdir -p ~/nssdb && certutil -N -d sql:~/nssdb
# 交互提示输入库密码；想免交互：
echo 'your-db-pass' > ~/nssdb.pwd
certutil -N -d sql:~/nssdb -f ~/nssdb.pwd
```

> 后面示例统一用 `-d sql:~/nssdb` 和 `-f ~/nssdb.pwd`，实际路径按需替换。

### 3. 自建根 CA（一条命令）

```bash
certutil -S \
  -s "CN=Example Internal Root CA,O=Example Corp,C=CN" \
  -n "Example Root CA" \
  -k rsa -g 3072 \
  -x \                      # -x = 自签名（没有上级签发者）
  -w 120 \                  # 有效期 120 个月
  -t "CT,C,C" \
  --extNC \
  -z sha256 \
  -v 120 \                  # 同样是月数（不同子命令取不同参数，见 --help）
  -d sql:~/nssdb -f ~/nssdb.pwd
```

几个关键参数：

- `-s` subject DN；`-n` 库内昵称（后续所有操作引用它）
- `-x` 自签；不加 `-x` 就必须配合 `-c <签发者昵称>`
- `-t` 导入时的信任位
- `-z sha256` 指定摘要算法（默认可能还是 SHA-1，务必显式指定）

### 4. 生成 CSR 并由 CA 签发（含 SAN）

生成密钥对和请求（密钥留在库里不出域）：

```bash
certutil -R \
  -d sql:~/nssdb -f ~/nssdb.pwd \
  -s "CN=internal.example.com,O=Example Corp" \
  -k rsa -g 2048 \
  -8 "internal.example.com,api.internal.example.com" \   # -8 = SAN DNS 名，逗号分隔
  -o server.csr
```

CA 签发（`-C` 直接消费 CSR，无需 openssl 中转）：

```bash
certutil -C \
  -d sql:~/nssdb -f ~/nssdb.pwd \
  -c "Example Root CA" \       # 签发者昵称
  -i server.csr \              # 输入 CSR
  -o server.crt \              # 输出证书
  -m 7 \                       # 序列号（每张唯一）
  -v 24                        # 有效期 24 个月
```

### 5. 导入 / 导出 / 详情 / 改信任位 / 删除

```bash
# 导入外部证书并授信（比如把公司根 CA 装进 Firefox）
certutil -A -n "Company Root CA" -t "CT,C,C" -i company-ca.crt -d sql:$HOME/.mozilla/firefox/xxx.default-release

# 只当普通服务器证书用（不可再签发）：注意 P 大写
certutil -A -n "My Server Cert" -t "P,," -i server.crt -d sql:~/nssdb

# 导出为 PEM 文本格式（给别人或程序用）
certutil -L -n "Example Root CA" -a -d sql:~/nssdb > example-ca.pem

# 查看某张证书完整详情（指纹、有效期、扩展、SAN……）
certutil -L -n "Example Root CA" -d sql:~/nssdb

# 改信任位（不用删了重导）
certutil -M -n "My Server Cert" -t "P,," -d sql:~/nssdb

# 删除
certutil -D -n "My Server Cert" -d sql:~/nssdb
```

### 6. 完整闭环案例：给内网服务签一张受信证书并部署

这是 certutil 最典型的实战组合拳：

```bash
# ① 建 CA 库 + 自建根 CA
certutil -N -d sql:~/ca-db -f ~/ca-db.pwd
certutil -S -s "CN=Home Lab Root CA" -n "Lab CA" -k rsa -g 3072 -x -w 120 -t "CT,C,C" -z sha256 -d sql:~/ca-db -f ~/ca-db.pwd

# ② 给服务建独立库，生成 CSR（SAN 必须有，否则现代浏览器直接拒）
certutil -N -d sql:~/web-db -f ~/web-db.pwd
certutil -R -d sql:~/web-db -f ~/web-db.pwd \
  -s "CN=router.lan" -k rsa -g 2048 -8 "router.lan,192.168.1.1" -o router.csr

# ③ CA 签发，导出证书链
certutil -C -d sql:~/ca-db -f ~/ca-db.pwd -c "Lab CA" -i router.csr -o router.crt -m 1 -v 12
certutil -L -n "Lab CA" -a -d sql:~/ca-db > lab-ca.crt

# ④ 私钥从 NSS 库导出成通用格式（下一节 pk12util 的活儿）
pk12util -o router.p12 -n "router.lan" -d sql:~/web-db -W exportpass

# ⑤ openssl 拆成 nginx 要的 key/crt，拼 fullchain
openssl pkcs12 -in router.p12 -nocerts -nodes -passin pass:exportpass -out router.key
openssl pkcs12 -in router.p12 -clcerts -nokeys -passin pass:exportpass -out router-cert.pem
cat router-cert.pem lab-ca.crt > fullchain.pem

# ⑥ 客户端（手机/笔记本）导入 lab-ca.crt 并授信后，
#    https://router.lan 就是绿锁了
```

---

## 四、pk12util：私钥搬运工

`.p12/.pfx`（PKCS#12）是带口令保护的"证书+私钥"打包格式。pk12util 负责 NSS 库与 `.p12` 文件之间的双向搬运。

### 常用命令

```bash
# 导出：把库里的证书+私钥打包成 .p12
pk12util -o backup.p12 -n "Server Cert" -d sql:~/nssdb
#   提示输入两次 PKCS12 口令（-W 可非交互指定）

# 导入：.p12 进 NSS 库
pk12util -i backup.p12 -d sql:~/newdb
#   提示输入 .p12 口令和新库口令（-W / -K 分别对应）

# 参数速查：
#   -o file    导出文件
#   -i file    导入文件
#   -n name    库内证书昵称
#   -d dbdir   目标/源 NSS 库
#   -K pass    NSS 库密码
#   -W pass    p12 文件口令
#   -n ...     见上
```

### 典型场景一：备份/迁移客户端证书

企业发的 VPN/WiFi EAP-TLS 登录证书往往只有一份私钥。先从原机器 NSS 库导出 `.p12`，在新机器导入即可完成迁移——这也是 Windows「导出证书」向导背后干的事。

### 典型场景二：给 nginx/postfix 等 Linux 服务供证书

NSS 库里的私钥不能直接被 nginx 读，走 pk12util + openssl 两步拆包（见上一节第④⑤步），是最稳的路径。

### 与 openssl 互转

```bash
openssl pkcs12 -in backup.p12 -clcerts -nokeys            -passin pass:x -out cert.pem
openssl pkcs12 -in backup.p12 -ca         -nokeys          -passin pass:x -out chain.pem
openssl pkcs12 -in backup.p12 -nocerts    -nodes           -passin pass:x -out key.pem   # 无口令私钥，注意权限
```

反向也可以用 `openssl pkcs12 -export` 打包后再让 pk12util 导入 NSS 库。

---

## 五、TLS 调试三件套：selfserv / tstclnt / ssltap

### selfserv：一行起本地 HTTPS 测试服务器

不用配 nginx，秒起一个 TLS 服务来测客户端行为：

```bash
# 建库 + 一张自签 localhost 证书
certutil -N -d sql:~/testdb -f ~/testdb.pwd
certutil -S -n testrsa -s "CN=localhost" -w 24 -t "CT,C,C" -x \
  -8 "localhost,127.0.0.1" -z sha256 -d sql:~/testdb -f ~/testdb.pwd

# 起 HTTPS 服务（-p 端口，-V 限定协议版本）
selfserv -n testrsa -p 8443 -d sql:~/testdb -V tls1.2:tls1.3 &

# 测试（curl 或自带 tstclnt）
curl -k https://localhost:8443/
tstclnt -h localhost -p 8443 -d sql:~/testdb <<<'GET / HTTP/1.0'
```

典型用途：测试老设备/老库对新 cipher suite 的兼容性、验证客户端 SNI 行为、CI 里的 TLS 回归。

### tstclnt：命令行 TLS 探针

相当于 `openssl s_client` 的 NSS 版：

```bash
tstclnt -h smtp.example.com -p 465 -d sql:~/nssdb <<<'QUIT'
```

能直观看到协商结果、证书链、协议版本，排查"为什么连不上"比翻日志快。

### ssltap：TLS 握手透视镜

本地起个代理，客户端连代理，代理转发真实服务器，**同时把整个握手过程打印在终端**：

```bash
# 终端 A：起代理，监听 9443，转发到真实服务器 443
ssltap -l -p 9443 real-server.example.com:443

# 终端 B：把客户端指向代理
curl -vk https://localhost:9443/
```

终端 A 会输出每一轮 ClientHello/ServerHello/证书交换的明文解析。排查"哪一步握手断了"、"对方支持哪些 cipher"时非常好用，也是理解 TLS 握手的最佳教具。

---

## 六、crlutil：证书吊销列表管理

CRL（Certificate Revocation List）是 PKI 运维里离线分发吊销信息的标准方式。crlutil 常用四板斧：

```bash
# 列出数据库中已有的 CRL/KRL
crlutil -L -d sql:~/nssdb

# 导入 CRL 文件（DER 或 PEM）
crlutil -I -d sql:~/nssdb -i revoked-list.crl

# 交互式生成/更新 CRL（会引导填 issuer、有效期、吊销条目）
crlutil -G -d sql:~/nssdb

# 删除库中的 CRL
crlutil -D -d sql:~/nssdb -i crl.der
```

日常主要出现在企业内部 PKI：CA 定期出新 CRL，各主机用 `-I` 导入，NSS 在验证证书链时会参考吊销状态。

---

## 七、其余工具速览表

| 工具 | 功能 | 典型用法 |
|---|---|---|
| vfychain | 验证证书链能否验通 | `vfychain -d sql:~/nssdb leaf.pem intermediate.pem`，排查"中间证书缺失"类故障 |
| ocspclnt | 手动向 OCSP 服务器查吊销状态 | 安全审计单张证书是否已被吊销 |
| derdump | DER 二进制结构 dump 成可读形式 | `derdump -i cert.der`，看证书扩展字段原始结构 |
| pp | 证书/CRL 等对象的 pretty-printer | `pp -t certificate -i cert.der`，快速人读 |
| modutil | 管理 PKCS#11 模块（智能卡/U盾驱动接入） | `modutil -list -dbdir sql:~/nssdb`；`modutil -add "MyHSM" -libfile /path/to/lib.so -dbdir sql:~/nssdb` |
| shlibsign | 为自定义 NSS 模块生成 .chk 完整性校验 | 自编译 softokn 后必须执行一次 |
| symkeyutil | 对称密钥对象的创建/删除 | 少用，调试 HSM 时偶尔需要 |
| nss-addbuiltin | 向内置信任模块追加根证书 | 发行版维护者定制信任锚 |
| signtool/signver | Netscape 对象签名/验签（历史遗留） | 现代场景基本被 Authenticode/JAR 签名替代 |
| p7sign/p7verify/p7content/p7env/cmsutil | PKCS#7/CMS 签名与信封 | S/MIME 邮件底层处理、文件分离签名 |
| strsclnt/rsaperf/vfyserv/chktest/nss-dbtest/nss-pp | 并发压测/RSA 基准/回归自检 | 主要供 NSS 开发者使用 |

---

## 八、写在最后：这套工具的价值定位

一句话总结：**libnss3-tools 是 NSS 加密底座的命令行操作面板**。日常最高频的组合拳：

1. `certutil` —— 管证书（建库、自建 CA、签发、授信）
2. `pk12util` —— 搬私钥（.p12 进出 NSS 世界）
3. `selfserv/tstclnt/ssltap` —— 调 TLS（起服务、探连接、看握手）
4. `crlutil` —— 管吊销
5. `pwdecrypt` —— 找回 Mozilla 存的密码（本文起点）

相比 openssl，它的独特价值在于：**直接操作浏览器/邮件客户端正在使用的同一个证书与密钥库**——你在命令行的每一次授信、导入，Firefox/Thunderbird 立即生效，不需要任何中间转换。做企业内网 PKI、批量部署可信 CA、排查客户端 TLS 故障时，这套工具几乎是必选项。

最后再强调一次安全底线：**给你的 Firefox/Thunderbird 设主密码**。否则任何拿到这两个文件的程序——包括恶意脚本——都能像本文一样轻松还原你的全部密码。
