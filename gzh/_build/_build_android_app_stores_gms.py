# -*- coding: utf-8 -*-
"""生成《从 F-Droid 到应用宝》公众号石墨极简风 HTML。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _gzh_graphite import build

QUOTE = '换一个应用市场，不只是换一个下载入口——你选的是一条依赖链。'
QUOTE_BY = '—— F-Droid 自签名仓库 / Aurora 的 GMS 依赖 / 荣耀应用市场的安装链劫持'

LEAD = ('在这台**荣耀畅玩50**（JDY-AN00，MagicOS 8，Bootloader 未解锁）上折腾了整整一轮：'
        'F-Droid 换镜像、Aurora Store 装官方应用、Gspace 容器跑 GMS、'
        '最后用 `adb` 精简了 **72 个系统包**——然后 F-Droid 的安装按钮**变灰卡死**，'
        'microG 装不上，YouTube 启动报错。本文把这次踩到的坑系统讲一遍：'
        '**应用市场不是一个下载入口，它是一条依赖链的入口。**')

NAV = [('01', '三种底层形态'),
       ('02', 'microG 装不上的真相'),
       ('03', 'adb 精简坏安装'),
       ('04', '容器方案的天花板'),
       ('05', '安全精简清单')]

SEC = [
    ('01', 'TYPES', '应用市场的三种底层形态', [
        ('h3', '形态一：自包含仓库（F-Droid）'),
        ('p', 'F-Droid 的仓库是**自签名的**：每个仓库一对 RSA 密钥，索引文件 `index.xml` 由仓库私钥签名，客户端内置或手动填入的 **fingerprint** 就是公钥指纹。这意味着：'),
        ('ul', [
            '**完全不依赖 GMS**。所有 App 都在 F-Droid 自己的构建机上从源码构建，签名由 F-Droid 掌管，和 Google Play 的签名体系没有交集',
            '**仓库可以通过任意镜像分发**，因为签名保证了完整性。实测：南京大学镜像下载 12.5MB 的 APK 用时 **0.5 秒（约 24MB/s）**，清华 TUNA 约 11MB/s，而官方 `f-droid.org` 直连在国内基本超时（实测 20 秒超时 0 字节）',
            '**代价**：源码构建 + 复现构建，版本更新比上游慢几天到几周。NewPipe 这类 App 甚至不在主仓库，要单独加仓库',
        ]),
        ('h3', '形态二：Play 协议客户端（Aurora Store / Play Store）'),
        ('p', 'Aurora Store 是 **Google Play 协议的第三方客户端**——它和 Play Store 说同一套协议，只是换了 UI 和账号策略（支持匿名下载）。这里有一个被大量教程混淆的点：'),
        ('note', '**Aurora Store 解决的是「下载」，不是「运行」。** 它能把 Play Store 里的 APK 下下来装上，但装出来的 App 和从 Play Store 装的是**同一个包**，运行时的依赖一模一样。凡是需要 GMS 才能跑的 App，从 Aurora 装下来一样跑不起来。'),
        ('p', '实测在无 GMS 的荣耀上用 Aurora 安装官方 YouTube，启动时 logcat 反复刷：'),
        ('code', 'W GooglePlayServicesUtil: com.google.android.youtube requires\n   the Google Play Store, but it is missing.\nW GoogleApiAvailability: GMS core API Availability.\n   ConnectionResult=9   # API_UNAVAILABLE\nW Metadata: NameNotFoundException: com.google.android.gms'),
        ('p', '**Chrome 能用而 YouTube 不能用**，差别就在于 Chrome 对 GMS 依赖极低，而 YouTube 的登录、通知、DRM、播放器内核加载全都调 GMS 的 API。GMS 的签名校验是系统级的：普通应用无法冒充 `com.google.android.gms` 注册系统服务——包名加签名必须同时匹配系统预置的 Google 平台密钥。'),
        ('h3', '形态三：厂商自有服务链（应用宝 / 荣耀应用市场等）'),
        ('p', '国内厂商市场有一个和前两类完全不同的特征：**它不只分发 App，还深度嵌入系统安装链**。以荣耀畅玩50 实测为例：'),
        ('ul', [
            'AOSP 的 `com.android.packageinstaller` 在荣耀上被深度定制，荣耀应用市场（`com.hihonor.appmarket`）注册了 `DownloadInstallService`、`SecureProxyActivity` 等组件，形成**「安全安装代理」层**',
            '**任何第三方来源的 APK 安装，最终都会被引导到这条链上做一遍「安全确认」**',
            '**厂商市场被禁用或损坏时，整个系统的安装功能都可能跟着坏掉**——包括从 F-Droid 装应用',
        ]),
        ('note', '这不是 F-Droid 的 bug，是厂商把安装链做成了和市场绑定的私有实现。腾讯应用宝相对独立（更接近普通 App），荣耀/华为/小米的**系统级市场**和安装器耦合更深。'),
    ]),
    ('02', 'MICROG', 'microG 装不上的真相：不是你操作错了', [
        ('p', 'microG 是 GMS 的开源重实现，思路是用相同的包名和兼容的签名注册系统服务。问题出在「兼容的签名」上——系统里预置的是 Google 的平台签名密钥，microG 不可能拿到。'),
        ('p', '**microG 的安装路径只有几条，每条都有前提：**'),
        ('ul', [
            '**自定义 ROM 内置**（如 LineageOS for microG）：ROM 构建时直接把 microG 打进系统',
            '**开启签名伪装（signature spoofing）**：需要定制 ROM 或 Xposed/LSPosed',
            '**Root 后注入**：Magisk/KernelSU 绕过常规包管理校验',
            '**未解锁的原厂系统：没有路径**——平台签名校验无法绕过，安装直接报 `INSTALL_FAILED_UPDATE_INCOMPATIBLE`',
        ]),
        ('note', '**很多教程会跳过这一行直接教你装 microG 的 APK**，然后你在原厂系统上怎么装都失败，还以为自己下错了版本。真相是：**在 Bootloader 未解锁的原厂系统上，microG 从机制上就无法安装**。判断方法很简单：你能解锁 Bootloader 吗？荣耀（独立后）对绝大多数机型不开放解锁。任何说「不用 root 也能装 microG」的教程，要么省略了前提，要么在骗你。'),
    ]),
    ('03', 'ADB', 'adb 精简厂商预装，可能把「装应用」这件事本身禁掉', [
        ('p', '`pm disable-user` 是无 root 精简的标准手段：不删数据、可逆、不需要解锁。但它有一个教程很少强调的副作用——**你禁用的可能不是「一个 App」，而是「系统功能的一个环节」**。'),
        ('p', '真实案例：为了去广告，用 adb 禁用了 **72 个系统包**。之后出现一个非常诡异的症状：'),
        ('ul', [
            'F-Droid 下载正常，点安装，安全告警弹出，点「继续安装」',
            '**按钮变灰，无任何提示，永远停在那**',
        ]),
        ('p', '排查每一步都在排除一个「想当然」的原因：先怀疑 Clash 代理（关了没用）；怀疑默认打开方式被 Termux 抢占（`pm resolve-activity` 确实解析到 Termux，但这是结果不是原因）；怀疑安装器被禁（恢复了没用）。**最后 logcat 抓到这一行：**'),
        ('code', 'W ActivityManager: Unable to start service Intent {\n  act=com.hihonor.appmarket.intent.action.DownloadInstallService\n  pkg=com.hihonor.appmarket } U=0: not found'),
        ('p', '**安装器每 3 秒重试绑定荣耀应用市场的 `DownloadInstallService`，永远失败。**「继续安装」按钮的背后，不是系统在装包，而是在等厂商市场的服务响应。服务被禁了，它就永远等下去。'),
        ('note', '**结论：在荣耀这类深度定制的系统上，`com.hihonor.appmarket` 不是「可以精简的预装应用市场」，它是系统安装链的一个组件。**禁用它等于禁用了「安装」这个动作的后半段。'),
    ]),
    ('04', 'CONTAINER', '容器方案（Gspace/OurPlay）是临时替代，不是解决方案', [
        ('p', '既然系统层装不了 GMS，容器类 App 的思路是：**在一个 App 内部虚拟一套 GMS 环境**。实测结论：**能用，但别抱期望**。'),
        ('ul', [
            'Gmail、Chrome 这类对 GMS 依赖浅的 App，容器里基本正常',
            'YouTube 这类重度依赖的，容器里**横屏播放直接崩溃**',
        ]),
        ('p', '崩溃的 logcat 实锤：'),
        ('code', 'E cr_ChromiumAndroidLinker: android_dlopen_ext: dlopen failed:\n  reserved address space 6082560 smaller than\n  207409152 bytes needed for ".../libchrome.so"'),
        ('p', '容器虚拟化层为播放器内核预留的连续虚拟地址空间（6MB）远小于实际需求（207MB）。竖屏能用是走了轻量路径，**横屏触发 Activity 重建重载内核就必然失败**。此外**容器内 App 的桌面快捷方式创建经常静默失败**——它靠广播触发系统 shortcut 服务，在荣耀的权限管控下请求根本没到达系统层（`dumpsys shortcut` 显示 `Calls: 0`）。'),
        ('note', '容器是**没有解锁条件下使用 Google App 的唯一现实路径**，但要清楚它的边界：体验差不是你配置错了，是虚拟化层的天花板。'),
    ]),
    ('05', 'CHECKLIST', '给精简党的安全清单', [
        ('p', '如果你打算用 adb 精简国产手机，以下是这次实测换来的红线。**这些包不要碰：**'),
        ('code', '# 安装链（禁了就装不了应用）\ncom.android.packageinstaller          # AOSP 安装器\ncom.hihonor.appmarket                 # 荣耀应用市场\ncom.hihonor.systemappsupdater         # 系统应用自更新\ncom.hihonor.autoinstallapkfrommcc     # 自动装包\n\n# 安全/认证链\ncom.hihonor.behaviorauth              # 行为认证\ncom.hihonor.trustagent                # 信任代理\ncom.hihonor.deviceauth                # 设备认证\ncom.hihonor.securityserver            # 安全服务\ncom.hihonor.securitypluginbase        # 安全插件基座\ncom.hihonor.systemmanager             # 手机管家\ncom.hihonor.iaware                    # 智能资源调度\n\n# 输入法（禁了没键盘）\ncom.sohu.inputmethod.sogou.honor'),
        ('p', '以下这些**通常可以安全禁用**（广告/遥测/预装，禁用不影响安装）：'),
        ('code', 'com.hihonor.hiview / hiviewpush / hiviewtunnel   # 遥测上报\ncom.hihonor.magazine                              # 杂志锁屏\ncom.hihonor.lens                                  # 智慧视觉\ncom.hihonor.gameassistant / game.kitserver        # 游戏中心\ncom.hihonor.baidu.browser / browserhomepage       # 预装浏览器\ncom.hihonor.search / searchservice                # 智慧搜索\ncom.hihonor.ouc                                   # 系统更新推送'),
        ('note', '**精简的正确姿势**：一次禁 3-5 个，重启，用两天，确认没异常再下一批。**不要一次性禁 70 个然后出问题再逐个恢复**——这次 72 个包回滚花了半小时，而如果用二分法定位「哪个才是罪魁」可能要一整天。'),
    ]),
]

FACTS = [
    ('测试设备', '荣耀畅玩50（JDY-AN00，MagicOS 8 / Android 14）'),
    ('Bootloader', '未解锁（荣耀不开放）'),
    ('F-Droid 镜像速度', '南京大学 24MB/s / 清华 11MB/s / 官方直连超时'),
    ('YouTube 直装报错', 'ConnectionResult=9 API_UNAVAILABLE（无 GMS）'),
    ('安装卡死根因', 'DownloadInstallService 被禁，安装器无限重试绑定'),
    ('容器崩溃原因', '虚拟地址空间预留 6MB < 实际需要 207MB'),
    ('本次禁用/恢复', '72 个系统包'),
]

CLOSER = ('应用市场的选择，本质是在选一条依赖链。F-Droid 给你的是一条完全自主的链，代价是更新慢、App 少；Play/Aurora 给你的是 Google 的链，代价是没有 GMS 就白装；厂商市场给你的是一条和手机系统焊死的链，代价是你不能把它当普通 App 对待。那两个坑——microG 装不上、adb 精简坏安装——本质是同一件事的两个面：Android 的安全模型里，包名和签名是身份，系统服务是契约。想替换身份需要改规则，想删掉契约的一端会连累依赖它的人。理解了这一点，很多「教程里没写但就是不行」的问题就有了答案。')

RELATED = [
    '解锁 Bootloader 不等于 Root：Android 刷机链的每一层到底在解什么锁',
    'F-Droid 2.0 发布：十年最大改版，重写为 Kotlin Compose，安装体验终于追上系统商店',
    '在 Linux 上原生跑安卓应用：Waydroid 实操与边界（不是模拟器，是容器化 LineageOS）',
]

CFG = dict(quote=QUOTE, quote_by=QUOTE_BY, lead=LEAD, nav=NAV, sections=SEC,
           facts=FACTS, closer=CLOSER, related=RELATED,
           facts_num='07', facts_en='KEY FACTS', facts_zh='关键事实速查')

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lore', 'gzh',
        '2026-10-12_android-app-stores-gms-pitfalls',
        '排版_石墨极简风(graphite-minimal).html')
    h = build(CFG)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(h)
    print(f'{len(h):7d} 字节  {out}')
