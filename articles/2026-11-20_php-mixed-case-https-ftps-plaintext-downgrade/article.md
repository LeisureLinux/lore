---
title: "PHP 大写 S 漏洞：一行 scheme[4]=='s'，TLS 静默失效了 23 年"
date: 2026-11-20
slug: php-mixed-case-https-ftps-plaintext-downgrade
category: 技术/解读
author: FreeLAMP.com
original_source: "PHP 安全公告 GHSA-f6gg-rchx-xw8j（CVE-2026-128064，2026-11-19）、修复提交 9c0b44ffd6631cea9906db32deca945bcbc93361、php-src PHP-8.4 分支源码（php-8.4.27 tag 与修复后分支对比）、回归测试 ext/standard/tests/http/ghsa-f6gg-rchx-xw8j.phpt 与 ext/standard/tests/streams/ghsa-f6gg-rchx-xw8j.phpt、PHP 8.2.36 / 8.3.37 / 8.4.28 / 8.5.13 / 8.6.0 发布说明。"
description: "拆解 CVE-2026-128064：PHP 的 http/ftp stream wrapper 用 scheme[4] == 's' 判断是否加密，而协议名解析、重定向前缀判断、同源判断全都大小写不敏感。于是 HTTPS://、httpS://、FTPS:// 会退回明文 HTTP/FTP，把 Basic 认证、Cookie、POST body、FTP 口令暴露在网络上。本文给出两条链路的源码位置、重定向如何被利用、修复 diff、回归测试与本地复现方法，并解释为什么 curl、Guzzle、Symfony HttpClient 不受影响。"
published: true
---

一个协议名里的大写字母，把加密关掉了。

2026 年 11 月 19 日，PHP 发布 8.2.36、8.3.37、8.4.28、8.5.13 与 8.6.0，修掉一个听着像段子的问题：只要 URL 的 scheme 里那个 `s` 写成大写，PHP 的 HTTP 与 FTP stream wrapper 就会走明文传输。`HTTPS://`、`httpS://`、`FTPS://` 全都中招，`file_get_contents()`、`fopen()`、`getimagesize()`、`simplexml_load_file()`、`DOMDocument::load()`、`md5_file()`、以及 `SoapClient` 读 WSDL 这些入口一个不落。

漏洞编号 CVE-2026-128064，GitHub 安全公告 GHSA-f6gg-rchx-xw8j，CVSS 4.0 打分 8.2，CWE-319（敏感信息明文传输）。按公告的说法，应用直接传混合大小写 URL 的情况从 PHP 5.2.0 就存在，重定向跳到混合大小写 URL 的情况从 PHP 4.3.0 就存在——这是代码审查得出的结论，不是推测。

值得说清楚的一点是：这不是“忘了转小写”那么简单。同一个 scheme 字符串，在四个地方被判断，前三个都不区分大小写，唯独真正决定要不要加密的那一个区分。这种“语义只做了一半”的错，才是它活了二十三年的原因。

## 一、先看那两行代码

问题出在两个文件、两行赋值。

HTTP 侧，`ext/standard/http_fopen_wrapper.c` 的 `php_stream_url_wrap_http_ex()`，在 php-8.4.27 tag 里是第 471 行：

```c
		use_ssl = (ZSTR_LEN(resource->scheme) > 4) && ZSTR_VAL(resource->scheme)[4] == 's';
		/* choose default ports */
		if (use_ssl && resource->port == 0)
			resource->port = 443;
		else if (resource->port == 0)
			resource->port = 80;
```

FTP 侧，`ext/standard/ftp_fopen_wrapper.c` 的 `php_ftp_fopen_connect()`，第 144 行：

```c
	use_ssl = resource->scheme && (ZSTR_LEN(resource->scheme) > 3) && ZSTR_VAL(resource->scheme)[3] == 's';
```

两处都是“数到第 N 个字符，看它是不是小写 s”。`"HTTPS"[4]` 是 `'S'`，`"FTPS"[3]` 也是 `'S'`，比较结果是假，`use_ssl` 就是 0。

HTTP 那行的后果是连锁的。往下几行，传输层字符串这样拼：

```c
			transport_string = zend_strpprintf(0, "%s://%s:%d", use_ssl ? "ssl" : "tcp", ZSTR_VAL(resource->host), resource->port);
```

`use_ssl` 为 0，transport 变成 `tcp://host:80`。注意默认端口也跟着退到了 80，所以 `HTTPS://example.com/x` 这种没写端口的 URL，会被送到对方的 80 端口去。

再往后，`php_stream_xport_crypto_setup()` 只在 `use_ssl` 为真时才调用。也就是说，整条路径上根本没有发起过 TLS 握手——不是握手失败，不是证书校验被跳过，是**压根没打算加密**。

## 二、为什么 `HTTPS://` 能进 http wrapper

有人会问：scheme 写成 `HTTPS`，PHP 怎么知道该用 http wrapper？

答案是 `main/streams/streams.c` 里的 `php_stream_locate_url_wrapper()`，它查 wrapper 注册表时做了小写化（8.4.27 tag 第 2081 行起）：

```c
	if (protocol) {
		if (NULL == (wrapper = zend_hash_str_find_ptr(wrapper_hash, protocol, n))) {
			char *tmp = estrndup(protocol, n);
			zend_str_tolower(tmp, n);
			if (NULL == (wrapper = zend_hash_str_find_ptr(wrapper_hash, tmp, n))) {
```

第一次按原样查（`HTTPS`）失败，转成小写再查（`https`）成功。所以分发阶段是**大小写不敏感**的，URL 顺利进了 http wrapper。

但接下来，wrapper 拿到的是**原始的 path 字符串**，而 `php_url_parse()` 也不会把 scheme 规范化成小写。于是 wrapper 内部看到的 `resource->scheme` 依然是 `"HTTPS"`，第 471 行那句按位置取字符的判断就落空了。

这就是整个 bug 的结构：入口宽容，出口严格，中间没有一次归一化。

## 三、重定向才是真正危险的那条路

应用自己拼出 `HTTPS://` 的概率不高——正常人写代码都是小写。但**重定向目标是别人给的**。

`vuln_http_fopen_wrapper.c` 里处理 `Location` 头的这段（第 1121 行）：

```c
			if (header_info.location_len < 8 ||
					(strncasecmp(header_info.location, "http://",  sizeof("http://")-1) &&
					 strncasecmp(header_info.location, "https://", sizeof("https://")-1) &&
					 strncasecmp(header_info.location, "ftp://",  sizeof("ftp://")-1) &&
					 strncasecmp(header_info.location, "ftps://", sizeof("ftps://")-1)))
			{ /* 相对路径：拼当前 scheme + host */ }
			else { new_path = header_info.location; }
			...
			php_url *new_resource = php_url_parse(new_path);
```

`strncasecmp` 是大小写不敏感的，所以 `Location: HTTPS://attacker.example/` 会被判定为“绝对 URL”，原样丢给 `php_url_parse()`，然后函数**递归调用自己**，第二轮重新算 `use_ssl`，又得到 0。

同一段代码里，判断“是不是同源”用的也是不敏感比较（第 1170 行附近）：

```c
			bool same_origin = zend_string_equals_ci(resource->scheme, new_resource->scheme)
				&& zend_string_equals_ci(resource->host, new_resource->host)
				&& (resource->port ? resource->port : default_port)
					== (new_resource->port ? new_resource->port : default_port);
```

于是 `https://example.com` 跳到 `HTTPS://example.com/other`，会被判成同源，`HTTP_WRAPPER_STRIP_AUTH` 不会加上，`Authorization` 与 `Cookie` 头保留；如果服务端回的是 307，POST body 也保留（代码里 301/302/303 会剥 body，307/308 保留）。

结果就是：一条合法的 HTTPS 请求，被中间人或者一个被攻陷的第三方服务用一行 `Location` 头，诱导 PHP 把带凭证的完整请求明文发出去。公告里特意写了——**即使目标拒绝这条明文连接，数据也已经泄露了**，因为请求已经发完了。

## 四、FTP 侧更直白：`AUTH TLS` 整块被跳过

FTP wrapper 的判断更简单，后果也更直接。第 178 行开始的整段加密协商，被包在 `if (use_ssl) { ... }` 里：

```c
	if (use_ssl)	{
		/* send the AUTH TLS request name */
		php_stream_write_string(stream, "AUTH TLS\r\n");
		...
	}

	if (use_ssl) {
		if (php_stream_xport_crypto_setup(stream,
				STREAM_CRYPTO_METHOD_SSLv23_CLIENT, NULL) < 0
```

`FTPS://` 写错一个大小写，`AUTH TLS` 不发，后面的 `USER` 与 `PASS` 就是明文上线，控制通道和数据通道一起裸奔。FTPS 的登录口令往往是那种“一个账号能读整个对账目录”的服务账号。

## 五、修复：两行，改成整串不敏感比较

修复提交是 `9c0b44ffd6631cea9906db32deca945bcbc93361`，作者 Jakub Zelenka（bukka），2026 年 11 月 19 日进各分支：

```diff
--- a/ext/standard/http_fopen_wrapper.c
+++ b/ext/standard/http_fopen_wrapper.c
@@ -439,7 +439,7 @@ static php_stream *php_stream_url_wrap_http_ex(...)
-		use_ssl = resource->scheme && (ZSTR_LEN(resource->scheme) > 4) && ZSTR_VAL(resource->scheme)[4] == 's';
+		use_ssl = zend_string_equals_literal_ci(resource->scheme, "https");

--- a/ext/standard/ftp_fopen_wrapper.c
+++ b/ext/standard/ftp_fopen_wrapper.c
@@ -141,7 +141,7 @@ static php_stream *php_ftp_fopen_connect(...)
-	use_ssl = resource->scheme && (ZSTR_LEN(resource->scheme) > 3) && ZSTR_VAL(resource->scheme)[3] == 's';
+	use_ssl = resource->scheme && zend_string_equals_literal_ci(resource->scheme, "ftps");
```

从“看第 5 个字符”变成“整串比 `https`，不区分大小写”。这样 `https`、`HTTPS`、`httpS`、`HtTpS` 全部命中，而 `http`、`ftp`、`sftp`、以及任何自定义 scheme 都不会被误判成加密。

一个细节：HTTP 那行顺手去掉了 `resource->scheme &&` 判空，因为 `zend_string_equals_literal_ci()` 不接受 NULL——函数上方第 443 行已经有 `ZEND_ASSERT(resource->scheme)` 兜底。FTP 那行保留了判空，因为它所在的位置没有这个断言。

## 六、回归测试：只看第一个字节

新加的两个 phpt 测试写得很利落，值得抄进自己的项目。

`ext/standard/tests/http/ghsa-f6gg-rchx-xw8j.phpt` 起一个裸 TCP server，accept 之后**只读一个字节**：

```php
    $request = fread($conn, 1);
    if ($request === "\x16") {
        $result = 'TLS';
    } else {
        while (($line = stream_get_line($conn, 8192, "\r\n")) !== false) { ... }
        $result = str_contains($request, 'Authorization: Basic ')
            && str_contains($request, 'X-Opensec-Request: validation')
            && str_contains($request, 'opensec-sensitive-body')
                ? 'plaintext credentials and body'
                : 'unexpected plaintext request';
    }
```

`\x16` 是 TLS 记录层 handshake 的类型字节，第一个字节就能判定对方有没有打算加密，不用解析任何协议。

客户端这一侧是完整的攻击面还原：

```php
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'content' => 'opensec-sensitive-body',
            'header' => "X-Opensec-Request: validation\r\n",
        ],
        'ssl' => ['verify_peer' => false, 'verify_peer_name' => false],
    ]);
    var_dump(@file_get_contents('HTTPS://alice:secret@{{ ADDR }}/secret', false, $context));
```

期望输出是 `bool(false)` 加 `TLS`：修复后请求走 TLS，跟这个裸 server 握手失败返回 false，但**至少是 TLS**。修复前这里会打印 `plaintext credentials and body`。

FTP 那个测试更省事，server 只回一句 `220 Ready`，然后读第一条命令，期望是 `AUTH TLS`：

```php
    var_dump(@fopen('FTPS://{{ ADDR }}/secret', 'r'));
```

## 七、本机三十秒复现

不需要装任何扩展，也不需要证书：

```bash
# 终端 A：裸听，不解 TLS
nc -l 8080

# 终端 B
php -r 'var_dump(@file_get_contents("HTTPs://127.0.0.1:8080/t"));'
```

- 老版本：终端 A 直接看到明文 `POST /t HTTP/1.0` 加 `Authorization: Basic ...`，`var_dump` 还能打出响应体。
- 新版本：终端 A 收到一堆二进制（ClientHello），或者连接直接断掉。

对照组把 scheme 改成全小写 `https://`，老版本也会正常走 TLS。这正是它难被测出来的原因——**只有在拼接 URL 的地方大小写不统一时才会触发**，而绝大多数测试用例写的都是小写。

## 八、为什么 curl、Guzzle、Symfony HttpClient 都没事

这三个是公告里点名的“不受影响”，原因很简单：它们不走 PHP 的 stream wrapper。

- curl 自己解析 URL、自己决定 TLS。libcurl 早就对 scheme 做了大小写不敏感处理，同类问题在 2018 年就修过（CVE-2018-1000007 是另一件事：重定向时跨源转发凭证，PHP 的 stream wrapper 直到 2026 年 9 月的 GHSA-fpwc-w8rq-cr92 才对上）。
- Guzzle 底层是 curl。
- Symfony HttpClient 走 curl 或自己实现的 native client，不碰 `http_fopen_wrapper.c`。

所以这个漏洞的边界非常清晰：**只影响用 PHP 自带 stream wrapper 的那条路**。判断方法不是看你用哪个 HTTP 客户端，而是看代码里有没有 `file_get_contents`、`fopen`、`getimagesize` 这类函数接收 URL。

## 九、影响面清单

按公告与源码，走这条路、可能被喂进混合大小写 URL 的函数至少包括：

- `file_get_contents()`、`fopen()`、`readfile()`、`copy()` 的 URL 形式
- `getimagesize()`、`exif_read_data()`、`md5_file()`、`sha1_file()`——图片与文件校验场景里极常见
- `simplexml_load_file()`、`DOMDocument::load()` / `loadHTMLFile()`、`XMLReader::open()`——解析远程 XML、RSS、SVG
- `SoapClient` 拉取 WSDL
- 任何自己 `stream_context_create()` 之后调 stream 函数的代码
- 开了 `allow_url_include` 的场景（虽然默认关闭）

暴露的数据按公告列举：Basic 认证凭证、Bearer token、Cookie、POST body、FTP 登录凭证、传输的文件内容。

## 十、这个 bug 真正草的地方

把四处判断排在一起看，问题就很清楚了：

| 环节 | 大小写处理 |
|---|---|
| `php_stream_locate_url_wrapper` 查注册表 | 不敏感（`zend_str_tolower`） |
| `Location:` 前缀判定 | 不敏感（`strncasecmp`） |
| `same_origin` 同源判定 | 不敏感（`zend_string_equals_ci`） |
| **`use_ssl` 是否加密** | **敏感（`scheme[4] == 's'`）** |

所有“这是不是 https”的判断都不敏感，唯独唯一真正决定要不要加密的那一处敏感。

而且这个写法从 PHP 4.3 / 5.2 一路抄到今天，二十三年没人动过。原因不难理解：正常代码里 scheme 永远是小写，测试也只写小写，边界输入——用户可控的 URL、第三方返回的 `Location`——根本没人试。代码审查时，`scheme[4] == 's'` 看起来甚至像个聪明的微优化：不分配字符串、不做比较，直接取一个字节。

同类问题在别的项目里也有先例。凡是“协议名/枚举值从字符串里解析出来”的地方，只要有一处按位置取字符，就迟早会遇到大小写、空白、编码变体。正确的做法只有一条：**在解析入口把 scheme 归一化一次，之后全流程只认归一化后的值**。PHP 这次选择了在每个判断点各自做不敏感比较，能修掉这个 CVE，但没有消除“同一个字符串被判断四次”的结构。

## 十一、现在该做什么

1. **升级**。8.2.36、8.3.37、8.4.28、8.5.13、8.6.0。8.1 及更早没有官方补丁，只能等发行版回移植，或者按下面的办法自己挡。
2. **临时缓解（不能马上升级时）**：在把 URL 交给 stream 函数之前，强制把 scheme 转小写；如果允许自动重定向，把 `follow_location` 关掉，自己校验并归一化每一个跳转目标。注意：**只归一化初始 URL 不管用**，重定向那条路照样能把你送进明文。
3. **代码审计**：grep 一遍 `file_get_contents(`、`fopen(`、`getimagesize(`、`simplexml_load_file(`、`new SoapClient(`，看这些调用的 URL 是从哪来的。用户可控、数据库里存的、第三方 API 返回的，都算不可信来源。
4. **别把“用了 HTTPS”当成“加密了”**。这条漏洞的全部杀伤力，就建立在“代码里写着 https，运行时却是 tcp”这个错觉上。抓包验证一次，比读十遍配置有用。

一句话收尾：加密这件事，判断依据必须是完整、归一化后的 scheme，而不是某个位置上的一个字符。少写一个 `tolower`，代价是二十三年的静默明文。
