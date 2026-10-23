> 这是 php2shell 两个 CVE 里被讨论得最少、但性质最严重的那一个的复现记录。
>
> 上一篇讲的是 `CVE-2026-109619`：靠 session 序列化器不一致，让一个会话变量的**名字**变成被反序列化的对象。那一条需要应用里存在一个 `__destruct` 有用的类。
>
> 这一篇讲 `CVE-2026-109619` 的兄弟：`CVE-2026-109618`。它的官方描述只有一句「PHP 用 `longjmp()` 处理内存耗尽，导致请求状态在结构还没填完时就被发布出去」。听起来像一个崩溃 bug。实际上它是一条**纯 HTTP 的地址泄漏链** —— 攻击者能让目标把堆地址和 PHP 模块基址编码进一个 `Set-Cookie` 响应头。

## 先说结论

两个请求，不写任何文件：

```
① POST /   →  在内存里留下一个悬垂的会话 id（send_cookie 也被留下来）
② POST /   →  伪造那个 id 的长度字段，让 PHP 把 4096 字节内存 URL 编码进 Set-Cookie
```

结果：

```
Set-Cookie: PHPSESSID=LAAAA...%9B%CA0%3E%DF3hY%A...
                     ↑ 伪造的 len        ↑ 越界读到的堆数据
```

把长度从 `0x1000` 加到 `0x10000`，读出来的 64KB 里就包含了 PHP 模块的
`pDestructor` 指针 —— 那个值减去它在模块内的固定偏移，就是 **libphp 的加载基址**。

在 Debian 13 的官方 `php8.4 8.4.26` 包上，这一步 **5 次全部首轮成功**，泄漏出来的
基址和 `/proc/<worker>/maps` 逐字节一致。

**本文的大部分内容会是我走错的路。** 因为这条链真正的难点不在漏洞本身，
而在三处 PHP 内部行为和两个我自己造的测量错误。

---

## 一、漏洞：桶被"数成活的"之后，OOM 了

`Zend/zend_hash.c` 里加一个哈希表桶的代码，顺序是这样的：

```c
add_to_hash:
    idx = ht->nNumUsed++;          /* ① 桶先被计为"活的" */
    ht->nNumOfElements++;
    p = ht->arData + idx;
    p->key = key = zend_string_init(str, len, ...);  /* ② 这里 OOM */
    p->h = ZSTR_H(key) = h;                          /* ③ longjmp 跳过以下全部 */
    ZVAL_COPY_VALUE(&p->val, pData);
```

第 ② 步是给键分配内存。如果这一步撞上 `memory_limit`，PHP 会 `longjmp`
直接跳出当前上下文。于是第 ③ 步之后的所有赋值都没发生 —— 但 `nNumUsed`
已经加过了。

**结果：哈希表里有一个被算作"活的"桶，它的 `key`、`h`、`val` 全是那块回收
堆槽里的垃圾。** 请求关闭阶段去销毁这张表时，就会把垃圾当指针用。

### 一个必须记住的判别信号

失败的那次分配，大小必须是 `len + 24` 向上取整到页。

比如字段名 1MB，那么 `tried to allocate` 应该是 **1052672**
（1048576 + 24 → 向上取整到 4096 的倍数）。

如果你看到的是 `tried to allocate 40960` 或 `20480`，那不是这个 bug ——
那是 `ZEND_HASH_IF_FULL_DO_RESIZE`（桶数组扩容），它发生在第 ① 步**之前**，
此时表完全一致，什么都不会坏。

我在这上面耗了很久：一直在让 OOM 落在扩容上，然后奇怪为什么"漏洞不触发"。

---

## 二、8.2 和 8.4 之间，有一个让整条链不可能的差异

这条链的第一环需要 `PS(send_cookie)` 在请求结束后**仍然保持 1**。

`php_session_reset_id()` 里有这么一段：

```c
/* 8.2.32 —— 无条件清零 */
if (PS(use_cookies) && PS(send_cookie)) {
    php_session_send_cookie();
    PS(send_cookie) = 0;
}

/* 8.4.26 —— 失败才保留 */
if (PS(use_cookies) && PS(send_cookie)) {
    zend_result cookies_sent = php_session_send_cookie();
    if (UNEXPECTED(cookies_sent == FAILURE)) {
        return FAILURE;          /* ← send_cookie 保持 1 */
    }
    PS(send_cookie) = 0;
}
```

在 8.2 上，无论你怎么摆布 `headers_sent`、怎么调 `memory_limit`，
`send_cookie` 都会被清零。**这不是参数问题，是代码结构问题。**

我一开始在 8.2.32 上折腾了很久，一直以为是某个配置不对，直到把这个函数
两个分支的源码并排看才明白：这条路在那个版本上根本不存在。

---

## 三、最容易被漏掉的一行配置：`output_buffering`

上面说 `send_cookie` 只有 `php_session_send_cookie()` **失败**时才保留。
而这个函数只有一个失败分支：

```c
static zend_result php_session_send_cookie(void) {
    if (SG(headers_sent)) { ...; return FAILURE; }
    ...
}
```

所以需要 `headers_sent` 为真。

我用了标准套路：发 1001 个表单字段，让 PHP 报
`Input variables exceeded 1000` 的警告，并在 `display_errors=On` 下把警告写进响应。

警告确实出现在响应体里了。**但 `headers_sent` 仍然是 0。**

原因是这个警告走的是 `php_printf` → `php_output_write` ——
它只写进**输出缓冲区**，并不会发送响应头。

在 php.ini 里加上两行之后，一切立刻变了：

```ini
output_buffering = Off
implicit_flush   = On
```

响应里出现了两条警告：

```
Warning: PHP Request Startup: Input variables exceeded 1000
Warning: Session cookie cannot be sent after headers have already been sent
```

第二条正是我们要的 —— 它说明 `send_cookie` 真的失败了，值被保留下来了。

```bash
$ sudo bash verify/read_psid.sh
true 0x7f...a7000 0x7f...a00000 0xa7000
↑    ↑            ↑               ↑
send_cookie=1    悬垂的 id       chunk 基址    它在 chunk 里的偏移
```

### 这个配置的副作用会咬人

`output_buffering=Off` 是全局设置。它会让**所有**请求在很早的阶段就置位
`headers_sent`，于是任何应用里的 `session_start()` 都会报
`Session cannot be started after headers have already been sent`。

这一条在我把两个 CVE 拼到一起时造成了很大麻烦（细节见另一篇文章）。
当时的解法是给需要读会话的那个目录单独把缓冲打开：

```apache
<Directory .../serialized>
    php_value output_buffering 4096
    php_value implicit_flush 0
</Directory>
```

---

## 四、第一个请求：怎么在内存里留下一个悬垂指针

`PS(id)` 是会话 id 的 `zend_string`。正常情况下请求结束会释放它。
但如果 OOM 的 `longjmp` 跳过了请求清理，它就变成悬垂指针。

请求 A 的形状：

| 部件 | 作用 |
|---|---|
| 1001 个普通字段 | 触发 `max_input_vars` 警告 → `headers_sent=1` |
| `PHPSESSID` 值 = 单字节 `\x00` | 让 `!ZSTR_VAL(PS(id))[0]` 成立 → 走"新建 id"分支 → `send_cookie=1` |
| `PHP_SESSION_UPLOAD_PROGRESS` | 启用上传进度机制 |
| 一个文件部件 | `MULTIPART_EVENT_FILE_START` 才会创建进度数据 |
| 末尾一个大字段 | 制造 OOM → `longjmp` 跳过 shutdown → `PS(id)` 悬垂 |

注意那个单字节 `\x00` —— 这是让 PHP 认为"没有 id，需要新建"的关键。
`send_cookie` 因此被置 1，然后因为 `headers_sent` 发不出去，于是被留下来。

---

## 五、第二个请求：伪造长度，让 PHP 帮你把内存编码出来

B 请求要做的只有一件事：**让悬垂的 `PS(id)` 那块内存落到一个我们能控制的
分配上，并让它的长度字段变成一个很大的值。**

`zend_string` 的结构：

```c
struct _zend_string {
    zend_refcounted_h gc;   /* +0x00 */
    zend_ulong        h;    /* +0x08 */
    size_t            len;  /* +0x10  ← 这个字段就是 ZSTR_LEN() */
    char              val[];/* +0x18 */
};
```

而 `php_session_send_cookie()` 里是：

```c
e_id = php_url_encode(ZSTR_VAL(PS(id)), ZSTR_LEN(PS(id)));
```

所以只要 `PS(id)` 指向一块**我们写过内容的内存**，`+0x10` 处就是任意的
长度，`+0x18` 往后就是任意的读取起点。

### 铺页 + 精确重占

具体做法（这套技巧不是我发明的，是从公开实现里学来的）：

- 发 841 个 48 字符的值。`zend_string_alloc(48)` = 24+48+1 = 73 字节，
  落在 80 字节的 bin 里。这些值把 80B bin 的页铺开。
- 最后一个值写 **79 字节**。它的 raw buffer 是 `emalloc(80)`，同样落在
  80B bin —— 于是它接住那个悬垂槽。
- 在这个 raw buffer 的 `+0x10` 写伪造的长度。

结果：

```
Set-Cookie: PHPSESSID=LAAAA...%9B%CA0%3E%DF3hY%A...
```

（`L` 是数据起点放的标记，一串 `A` 是填充，后面是越界读到的堆内容。）

把这 4096 字节 URL 解码，里面能数出近百个候选指针；按 2MB 对齐取众数，
就是 Zend MM 的 **chunk 基址**。

---

## 六、第二个请求（续）：为什么长度必须跨过 64KB

这一步我卡了最久。

要泄漏 libphp 基址，需要读到一个函数指针 —— 哈希表的 `pDestructor`
（值是 `zval_ptr_dtor`）。

我把长度设成 `0x1000`，结果读回来的全是同一页里的字符串。改成 `0x10000`
（64KB）之后立刻成功。

原因是 **Zend MM 按 bin 分页**：

- 80 字节的 bin 有自己的页，只放 80 字节的块
- 56 字节的 bin 有自己的页，只放 `HashTable` 本体

`PS(id)` 在 80B 页，而 `pDestructor` 所在的 `HashTable` 在 56B 页。
**页不同，只有长度足够大才能跨过去。**

### 还有一个小陷阱：原地替换

`zend_hash_update` 对已经存在的键是**原地替换**，不会释放旧块。
所以第一次尝试时，那个槽一直被活着的新值占着，我们的 raw buffer 拿不到。

公开实现里的解法是发三段同名值：

```
D0 占住目标槽
... 一堆填充 ...
D1 同名 → 原地替换，复用 D0 的块
D2 再同名 → 强制换块，D0/D1 那块才真正被释放
forge 接住刚释放的槽
```

### 怎么从 64KB 里认出 libphp 基址

不用猜。`zval_ptr_dtor` 在这个构建里位于模块内偏移 `0x426130`。
所以扫这 64KB：凡是满足

```
(v - 0x426130) & 0x1fffff == 0
```

的 8 字节值，其 `v` 就是 `libphp + 0x426130`。命中 58 次，取众数。

结果和 `/proc/<worker>/maps` 里 `libphp8.4.so` 的起始地址**逐字节相同**。

> 模块内的偏移必须按实际构建重新取。发行版包和自编译版的偏移完全不同 ——
> 同一个版本号 8.4.26，Debian 包的 `zif_system` 是 `0x24d710`，
> 自己编译的是 `0x43a870`。用 Debian 的 `-dbgsym` 包取：
>
> ```bash
> BID=$(readelf -n /usr/lib/apache2/modules/libphp8.4.so | awk '/Build ID/{print $3}')
> nm -C --defined-only /usr/lib/debug/.build-id/${BID:0:2}/${BID:2}.debug \
>    | grep -wE 'zif_system|zval_ptr_dtor'
> ```

---

## 七、两个我自己造的测量错误

这两个坑都不是 PHP 的问题，但各浪费了我一整轮排查。

### 7.1 gdb 的指针运算

```gdb
(gdb) x/8gx ps_globals.id - 0x10
```

看起来是在往前看 16 个字节。实际上 `ps_globals.id` 的类型是
`zend_string *`，gdb 会按 `sizeof(zend_string)` 缩放 —— 于是它跳到的是
`-0x180`。dump 出来的内存完全错位。

正确写法是先强转成字节指针：

```gdb
(gdb) x/8gx (char*)ps_globals.id - 0x10
```

因为这一条，我把哈希表的结构偏移算错了整整一轮，得出过一堆互相矛盾的结论。

### 7.2 选错进程

```bash
pgrep -u www-data apache2
```

`www-data` 用户下**不止** PHP 的 worker。Apache 的磁盘缓存清理进程
`htcacheclean` 也属于这个用户，**而且它也加载了 libphp**。

于是 gdb 附上去了，符号也对，读出来全是垃圾。

正确的过滤方式：

```bash
for p in $(pgrep -u www-data apache2); do
    sudo grep -q libphp8.4.so /proc/$p/maps 2>/dev/null && echo $p
done
```

---

## 八、这条链能做什么，不能做什么

**能做的**：纯 HTTP 泄漏堆基址和模块基址。这是 ASLR 绕过的核心，
也是任何后续代码执行的前置条件。

**不能做的（至少在这个构建上我没做到）**：直接接上代码执行。

公开资料里描述过第三条链：伪造一个 `HashTable`，把 `pDestructor`
换成 `zif_system`，从 `php_session_track_init()` 里触发。

我没打通，而且找到了原因：

```c
static void php_session_track_init(void) {
    zend_delete_global_variable(var_name);
    if (!Z_ISUNDEF(PS(http_session_vars))) {
        zval_ptr_dtor(&PS(http_session_vars));   /* refcount 2 → 1，不析构 */
    }
    array_init(&session_vars);
    ZVAL_NEW_REF(&PS(http_session_vars), &session_vars);
    ...
}
```

`$_SESSION` 这个全局变量还持有那个 reference，所以 `zval_ptr_dtor`
只把引用计数从 2 降到 1，**块根本不会被释放**。伪造的 reference 没有落点。

我试过不同长度的伪 reference（48/52/55 字节）配合不同数量（1/4/16/64），
那块内存的引用计数一直是 5，从没被覆盖过。

公开实现的底层笔记里也有同样的记录：那条路径通常表现为文件句柄被踩坏，
"不是可控的 `pDestructor`"。

所以这篇的交付是"纯 HTTP 的地址泄漏"，这本身是完整可复现的；
把泄漏接到执行上，我用的是另一个 CVE 的原语（另一篇里讲）。

---

## 九、复现

靶机是 Debian，PHP 用**发行版官方包**而不是自己编译 —— 因为真实目标就是这样。

关键在于：仓库里的候选版通常**已经修好**了（8.4.27），要从官方 pool 取旧的
（8.4.26），然后**锁住版本**：

```bash
apt-mark hold php8.4-common php8.4-cli libapache2-mod-php8.4 \
              php8.4-opcache php8.4-readline
```

不锁的话，任何一次 `apt-get -f install` 都会把它悄悄升回去，复现就"突然失效"。

⚠️ 顺带一提：`opcache` 和 `readline` 也必须一起降级。只降 `mod_php` 的话，
新版的 `opcache.so` 在旧版引擎里会报 `undefined symbol`，Apache 直接起不来。

攻击侧：

```bash
python3 cve-2026-109618/exploit/run_all.py --target <target-ip> --port 8080
```

```
[1] attempt 1: read=4096   chunk=0x7f011b600000
[2] attempt 1: read=65536  libphp=0x7f572ac00000

CHUNK_BASE  = 0x7f011b600000
LIBPHP_BASE = 0x7f572ac00000
zif_system  = 0x7f572ae4d710
```

完整靶机、攻击脚本和一个白盒校验工具（自动按 build-id 找 dbgsym）
都放在 `github.com/LeisureLinux/php2shell`，同一个仓库里还有另一个 CVE。

---

## 十、怎么修

| 措施 | 说明 |
|---|---|
| **升级 PHP** | 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12。8.1 及更早已 EOL，不会修 |
| **`memory_limit = -1`** | 官方推荐的第一条，也是最容易被忽略的一条 |

第二条值得多说一句。**把内存限制关掉，看起来像"放弃防御"。**

它的逻辑是：没有每请求的内存上限，攻击者就失去了那个可预测的失败点 ——
而这条链完全建立在"能在指定位置制造一次 OOM"上。

⚠️ 但**不要**用 `RLIMIT_AS` / `RLIMIT_DATA` 当替代方案。那会让 `mmap()`
在到达限制时失败，正好触发有漏洞的 `longjmp` 路径 —— 等于自己把开关打开了。

最后一条，也是网上最容易误传的一条：

**`session.upload_progress.enabled = Off` 对 109618 毫无作用。**
那是 109619 的缓解措施。两个漏洞根因完全不同，缓解措施不能互相套用。
官方公告里特意写了这一点，而它是最常被读错的一句。

---

## 附：踩坑速查

| 现象 | 根因 |
|---|---|
| `send_cookie` 一直是 false | `output_buffering` 没关，startup 警告不置位 `headers_sent` |
| gdb 读出的结构全错位 | `ps_globals.id - 0x10` 按 26 字节元素缩放；要写 `(char*)… - 0x10` |
| gdb 附上了但全是垃圾 | `htcacheclean` 也是 `www-data`，也加载 libphp；要查 maps 过滤 |
| 越界读只读到同页字符串 | Zend MM 按 bin 分页，长度要 ≥64KB 才跨得过去 |
| 伪造的 `len` 不生效 | `zend_hash_update` 原地替换不释放旧块，要用三段同名值 |
| OOM 了但漏洞不触发 | 落在 `ZEND_HASH_IF_FULL_DO_RESIZE` 上，不是 key 分配 |
| 复现隔天失效 | `apt-get -f install` 把包升回修复版，要 `apt-mark hold` |
| 只降 `mod_php` 后 Apache 起不来 | `opcache` / `readline` 也必须同版本 |
