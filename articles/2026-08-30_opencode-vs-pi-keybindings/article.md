# 从 Ctrl+X 的两种哲学，看 OpenCode 与 Pi-Coding-Agent 的快捷键设计

> 写完这篇之前，我以为"快捷键不够用"是个伪命题——真要不够，大不了加 Shift 嘛。等我把 OpenCode 和 Pi-Coding-Agent 的整套键位都跑了一遍，才发现这件事没那么简单。

在终端里写代码的人，都会撞上同一个老问题：**快捷键永远不够用**。`Ctrl+A` 要不要做"跳行首"？`Ctrl+B` 要不要做"返回上一个 shell"？`Ctrl+P` 是"上一条命令"还是"命令面板"？同一个 `Ctrl` 组合既要被编辑器霸占，又要被工具霸占——抢键几乎是必然。

最近把两个新潮的 AI 编码工具（OpenCode 1.18.x 和 Pi-Coding-Agent 0.84.x）来回切换着用，发现它们对这个问题给出了**两种截然不同的解法**。一篇讲清楚。

## 一、两个工具是谁

| 工具 | 厂商 | 核心思路 |
|------|------|----------|
| **OpenCode** | Anomaly（之前叫 sst/opencode） | Go 编写的终端/桌面/IDE 三端统一 AI 编码智能体，主打 MIT 开源 + provider 无关（你插什么模型就用什么） |
| **Pi-Coding-Agent** | earendil-works | 用 TypeScript 写、底层是自家 `@earendil-works/pi-tui` 的 TUI 智能体，强调"Emacs 风的键位 + 队列消息流" |

两个都用过一段时间后，最直观的差异不是"哪个更聪明"，而是**按键手感差太多**。下面讲清楚差在哪。

## 二、问题的根源：为什么快捷键会不够用

终端里的快捷键最早是给单用途程序设计的：

- `readline`（bash/PSQL/python REPL 都用它）定义了 `Ctrl+A` 到行首、`Ctrl+E` 到行尾、`Ctrl+K` 删到行尾
- Emacs 定义了一整套 `Ctrl+X <something>` 的"双键组合"
- 浏览器又把所有 `Ctrl+字母` 都征用了一遍

等你想在终端里同时塞进"编辑器 + 工具栏 + 应用命令 + 模型切换 + 会话管理"，传统一按即达（chord-free）的设计就崩了。

两种主流的应对思路：

1. **Leader 键（prefix key）**：先按一个"前缀"，再按命令。tmux 的 `Ctrl+B`、Screen 的 `Ctrl+A`、btop 的 `Ctrl+B` 都是这套。代价是要按两下。
2. **多模态/上下文切换**：在编辑态是一种键位，在命令态是另一种。`vim` 的 normal/insert/visual 三模式就是极致代表。代价是要记当前在哪个状态。

OpenCode 选了第 1 种，Pi 选了第 2 种里的轻量版（用专门的"应用层"快捷键不和编辑器抢）。

## 三、OpenCode：全套 leader 键工作流

OpenCode 的设计一目了然：把 `Ctrl+X` 当成 leader，按下后**等 2 秒**（`leader_timeout` 默认 2000ms）收下一个字母，然后执行对应命令。期间 `Ctrl+X` 本身被"吃掉了"——不传给任何底层组件。

### 3.1 应用层（`Ctrl+X <letter>`）

| 快捷键 | 作用 | 说明 |
|--------|------|------|
| `Ctrl+X n` | 新建会话 | `session_new` |
| `Ctrl+X l` | 会话列表 | `session_list` |
| `Ctrl+X g` | 会话时间线 | `session_timeline` |
| `Ctrl+X c` | 压缩会话 | `session_compact`，把上下文压成摘要腾位置 |
| `Ctrl+X x` | 导出会话 | `session_export` |
| `Ctrl+X ↓` | 跳到第一个子会话 | `session_child_first` |
| `Ctrl+X m` | 模型列表 | `model_list` |
| `Ctrl+X a` | 智能体列表 | `agent_list`，切 build / plan 模式也在这一层 |
| `Ctrl+X b` | 侧边栏开关 | `sidebar_toggle`，左栏会话列表的折叠 |
| `Ctrl+X s` | 状态视图 | `status_view` |
| `Ctrl+X t` | 主题列表 | `theme_list` |
| `Ctrl+X e` | 打开外部编辑器 | `editor_open`，调 `$EDITOR` |
| `Ctrl+X h` | 提示开关 | `tips_toggle`，开关底部"Did you know?" 提示 |
| `Ctrl+X y` | 复制消息 | `messages_copy` |
| `Ctrl+X u` | 消息撤销 | `messages_undo` |
| `Ctrl+X r` | 消息重做 | `messages_redo` |
| `Ctrl+X q` | 退出 | `app_exit` |

> 上面这张表是 OpenCode 1.18.25 的当前默认，所有键位都可在 `~/.config/opencode/tui.json` 的 `keybinds.<key>` 字段重写；想禁用某个键，写成 `"none"`。

leader 键工作机制的伪代码（来自 `cli/cmd/tui/context/keybind.tsx`）：

```typescript
// 按下 Ctrl+X 时进入"等待后续键"状态
keypress('ctrl+x') → mode = 'awaiting-leader'
// 2 秒内按下任意键，否则超时
// 2 秒后再按 <letter> 查表得到 Action
// 若 2 秒内没按，恢复成普通编辑态
setTimeout(() => mode = 'normal', leader_timeout)
```

这就是为什么在 herdr / kitty 这种"按键需要穿过两层 PTY"的环境里偶尔会失灵——任何一环引入的延迟都可能让 leader 键超时。验证方法：按 `Ctrl+X b`，左栏立刻消失/出现，说明链路通；否则就是哪一层把 `Ctrl+X` 吞了。

### 3.2 不带 leader 的高频单键

为了避免每个动作都"先按两次键"太累，OpenCode 把**真正高频的几个动作**留成单键：

| 快捷键 | 作用 |
|--------|------|
| `Ctrl+P` | 命令面板 `command_list`，可搜索所有动作 |
| `Ctrl+R` | 重命名当前会话 `session_rename` |
| `Ctrl+D` | 删除（会话/暂存条目） `session_delete` / `stash_delete` |
| `Ctrl+A` | 模型提供商列表 `model_provider_list` |
| `Ctrl+F` | 收藏/取消收藏模型 `model_favorite_toggle` |
| `Ctrl+T` | 切换模型变体 `variant_cycle`（比如在 high / medium / low 推理档位之间切） |
| `Esc` | 中断当前会话 `session_interrupt` |
| `Tab` / `Shift+Tab` | 切换主智能体 `agent_cycle`（build ↔ plan 模式） |
| `F2` / `Shift+F2` | 切换最近用过的模型 `model_cycle_recent` |

### 3.3 编辑器 / 翻页类

| 快捷键 | 作用 |
|--------|------|
| `PageUp` / `PageDown` | 翻页 |
| `Ctrl+Alt+B` / `Ctrl+Alt+F` | 翻半页 |
| `Ctrl+G` / `Home` | 跳到第一条消息 |
| `Ctrl+Alt+G` / `End` | 跳到最后一条消息 |

> **注意点**：`Ctrl+P` 在 OpenCode 里是"命令面板"，但 bash/readline 里也是"上一条命令"。如果你在 shell 嵌套里把这个键从外部传过去，可能和 shell 抢。这是终端类工具永远逃不开的痛。

### 3.4 配置方式

OpenCode 1.18 之后，**TUI 专属配置**独立到了 `~/.config/opencode/tui.json`（`tui.jsonc` 也行）。`opencode.json` 里的 legacy `theme` / `keybinds` / `tui` 字段已经被废弃，会自动迁移。

```jsonc
// ~/.config/opencode/tui.json
{
  "$schema": "https://opencode.ai/tui.json",
  "leader_timeout": 2000,        // Ctrl+X 后等多久
  "keybinds": {
    "leader": "ctrl+x",          // leader 键改成别的
    "sidebar_toggle": "<leader>b",
    "tips_toggle": "<leader>h",
    "app_exit": "ctrl+c,ctrl+d,<leader>q"
  },
  "scroll_speed": 3,
  "diff_style": "auto",          // "auto" / "stacked"
  "attention": {
    "enabled": true,
    "notifications": true,
    "sound": true,
    "sound_pack": "opencode.default"
  }
}
```

禁用某个键的方法：把它的值设成 `"none"` 或 `false`：

```jsonc
{
  "keybinds": {
    "session_compact": "none",
    "tips_toggle": "none"
  }
}
```

环境变量 `OPENCODE_TUI_CONFIG` 可以指向任意自定义路径（适合做多套配置切换）。

## 四、Pi-Coding-Agent：没有 leader 键，直接绑定

Pi 的设计哲学完全是另一个方向：**没有 leader 键**。所有应用层动作都是 `Ctrl+<key>` 直接绑，所有编辑器动作也直接绑，靠"动作语义互不重叠"来避免抢键。

### 4.1 编辑器层（Emacs 风格）

`@earendil-works/pi-coding-agent@0.84.4` 的 `dist/core/keybindings.d.ts` 里把所有 `tui.editor.*` 的键位都写死了：

| 快捷键 | 作用 | `tui.editor.*` key |
|--------|------|--------------------|
| `←` / `→` | 移动光标 | `cursorLeft` / `cursorRight` |
| `Ctrl+B` / `Ctrl+F` | 等价于左右键 | `cursorLeft` / `cursorRight` |
| `Alt+←` / `Alt+→`（或 `Ctrl+←/→`、`Alt+B/F`） | 按词移动 | `cursorWordLeft` / `cursorWordRight` |
| `Home` / `End`（或 `Ctrl+Home/End`、`Ctrl+A`/`Ctrl+E`） | 行首/行尾 | `cursorLineStart` / `cursorLineEnd` |
| `Ctrl+]` | 跳到下一个指定字符 | `jumpForward` |
| `Ctrl+Alt+]` | 反向跳 | `jumpBackward` |
| `Backspace` | 向后删字符 | `deleteCharBackward` |
| `Delete` / `Ctrl+D` | 向前删字符 | `deleteCharForward` |
| `Ctrl+W` / `Alt+Backspace` | 向后删词 | `deleteWordBackward` |
| `Alt+D` / `Alt+Delete` | 向前删词 | `deleteWordForward` |
| `Ctrl+U` | 删到行首 | `deleteToLineStart` |
| `Ctrl+K` | 删到行尾 | `deleteToLineEnd` |
| `Ctrl+Y` | 粘贴（yank） | `yank` |
| `Alt+Y` | yank 循环 | `yankPop` |
| `Ctrl+Z` / `Alt+Z` / `Ctrl+-` | 撤销 | `undo` |
| `Tab` | 自动补全 | `tab` |
| `Shift+Enter`（或 `Ctrl+J`） | 插入换行 | `newLine` |
| `Enter` | 发送 | `submit` |
| `Ctrl+C` | 复制选中文本 | `copy` |

这套就是 readline / Emacs 标准键位，**没有任何应用层语义**。

### 4.2 应用层

| 快捷键 | 作用 |
|--------|------|
| `Ctrl+C` | 清空编辑器（当编辑器非空时） / 中断（当运行中时） `app.clear` / `app.interrupt` |
| `Ctrl+D` | 编辑器为空时退出 `app.exit` |
| `Ctrl+Z` | 挂起到后台 `app.suspend` |
| `Ctrl+P` | 循环切到下一个模型 `app.model.cycleForward` |
| `Alt+P` / `Shift+Ctrl+P` | 循环切到上一个模型 `app.model.cycleBackward` |
| `Ctrl+L` | 打开模型选择器 `app.model.select` |
| `Ctrl+T` | 开关"思考块"折叠 `app.thinking.toggle` |
| `Shift+Tab` | 循环切思考层级（low / medium / high）`app.thinking.cycle` |
| `Ctrl+O` | 展开/收起工具输出 `app.tools.expand` |
| `Ctrl+N` | 切换已命名的会话过滤器 `app.session.toggleNamedFilter` |
| `Ctrl+R` | 重命名当前会话 `app.session.rename` |
| `Ctrl+D` | 删除会话 `app.session.delete`（编辑器为空时） |
| `Ctrl+Backspace` | 编辑器为空时非侵入式删除会话 `app.session.deleteNoninvasive` |
| `Alt+L` / `Alt+R` | 树视图折叠/展开 `app.tree.foldOrUp` / `app.tree.unfoldOrDown` |
| `Shift+L` | 编辑树标签 `app.tree.editLabel` |
| `Shift+T` | 切换树标签上的时间戳 `app.tree.toggleLabelTimestamp` |
| `Ctrl+S` | 保存模型选择 `app.models.save` / 切换会话排序 `app.session.toggleSort` |
| `Ctrl+A` | 启用所有模型 `app.models.enableAll` |
| `Ctrl+X` | **清空所有模型** `app.models.clearAll`（注意：Pi 这里不是 leader 键） |
| `Alt+↑` / `Alt+↓` | 模型重排序 `app.models.reorderUp` / `reorderDown` |
| `Ctrl+Q` | 把消息加入队列（继续编辑下一条，自动衔接） `app.message.followUp` |
| `Alt+Q` / `Alt+↑` | 恢复队列里的消息 `app.message.dequeue` |
| `Ctrl+X` | **复制消息** `app.message.copy`（同一个 `Ctrl+X`，不同上下文！） |
| `Ctrl+V` / `Alt+V` | 粘贴图片（剪贴板是图时），否则粘贴文本 `app.clipboard.pasteImage` |
| `Ctrl+G` | 打开外部编辑器 `app.editor.external` |

> **坑预警**：Pi 的 `Ctrl+X` 同时绑了"清空所有模型"和"复制消息"——这是 keybindings.ts 里我见过最让人困惑的双重绑定。实际行为是按上下文分：在模型管理界面按下是清空，在聊天主界面按下是复制。如果你经常用 `Ctrl+X` 复制（Emacs 老用户），请改 keybindings 配置把 `app.message.copy` 拆到别的键上。

### 4.3 视图 / 搜索

| 快捷键 | 作用 |
|--------|------|
| `PageUp` / `PageDown` | 翻页 |
| `Ctrl+F` / `Ctrl+Shift+F` | 打开搜索 |
| `Enter` | 搜索：下一个匹配 |
| `Shift+Enter` / `Ctrl+Shift+G` | 搜索：上一个匹配 |
| `Home` / `End` | 滚到顶 / 底 |
| `Ctrl+↑` / `Ctrl+↓` | 跳到上一个 / 下一个语义提示位置 |

### 4.4 配置方式

Pi 的键位配置在 `~/.pi/agent/keybindings.json`（v0.84 起的位置；更老版本可能在 `~/.config/pi/keybindings.json`）：

```json
{
  "app.model.cycleForward": "ctrl+p",
  "app.message.copy": "ctrl+y",
  "app.thinking.toggle": "ctrl+t"
}
```

迁移函数 `migrateKeybindingsConfig` 会自动兼容老格式。

## 五、关键差异一张表

| 维度 | OpenCode | Pi-Coding-Agent |
|------|----------|-----------------|
| **leader 键** | `Ctrl+X` 默认 2s 超时 | ❌ 无 |
| **调出命令面板** | `Ctrl+P` | 通过 `app.message.copy` / 应用层快捷键分布 |
| **撤销模型** | 消息级（`Ctrl+X u` / `r`） | 文本级（`Ctrl+Z`），消息级通过工具层 |
| **模型切换** | 单独 `Ctrl+X m` / `F2` | `Ctrl+P`（循环）/ `Ctrl+L`（选择器） |
| **思考块** | 通过 `Ctrl+T` 切变体 | 独立的 `Ctrl+T` 折叠 + `Shift+Tab` 切层级 |
| **消息队列** | 无显式队列 | `Ctrl+Q` 入队、`Alt+Q` 出队（很 Emacs） |
| **编辑器风格** | 自家实现 + readline 习惯 | 纯 Emacs 风格（`Ctrl+B/F/A/E` 直接是光标） |
| **键位冲突** | 用 leader 隔离 | 双绑 `Ctrl+X`（复制 vs 清空模型）需要避坑 |
| **可重定义** | `tui.json` 完整覆盖 | `keybindings.json` 部分覆盖 |
| **可关闭单个键** | `"key": "none"` | 同上 |

## 六、实战：herdr / kitty / tmux 嵌套环境下的注意事项

很多人把 OpenCode / Pi 跑在 herdr 终端多路复用器里，herdr 又跑在 kitty 里。**三层 PTY** 时，按键可能丢在任一环。

### 6.1 按键传递链路

```
键盘 → kitty → herdr (PTY) → agent pane (PTY) → OpenCode / Pi (TUI)
```

每经过一层就多一次"是否吃掉按键"的判断。`Ctrl+X` 是最容易出问题的——它本身是 XON/XOFF 历史上的特殊字符（`Ctrl+S`/`Ctrl+Q` 是 XOFF/XON），很多终端默认把它当 raw 字节转给上层，但某些嵌套层会把它当"自己留着用"。

### 6.2 验证方法

按 `Ctrl+X b`：

- **正常**：OpenCode 的左栏会话列表消失/出现。说明 leader 键链路通。
- **无反应**：链路在某处断了。检查：
  1. 是不是 `Ctrl+X` 被 kitty 的 `key_bindings` 抢了（`kitty.conf` 里搜 `ctrl+x`）
  2. 是不是 herdr pane focus 不在（点一下 opencode 窗口再试）
  3. 是不是 OpenCode 的 leader 超时太短，herdr 引入的延迟超过了 2s。把 `leader_timeout` 调大到 5000 试试：
     ```jsonc
     // tui.json
     { "leader_timeout": 5000 }
     ```

### 6.3 推荐自定义配置（结合两者优点）

```jsonc
// ~/.config/opencode/tui.json
{
  "$schema": "https://opencode.ai/tui.json",
  "leader_timeout": 3000,
  "keybinds": {
    // 把复制改成不会被抢的键，避免和 readline 冲突
    "messages_copy": "<leader>y",
    "messages_undo": "<leader>u",
    // 关闭提示面板（底部"Did you know?"）
    "tips_toggle": "none",
    // 调出命令面板改键，避免和 bash 的 Ctrl+P 抢
    "command_list": "ctrl+grave"
  }
}
```

```json
// ~/.pi/agent/keybindings.json
{
  "app.message.copy": "ctrl+y",
  "app.models.clearAll": "ctrl+shift+x",
  "app.model.cycleForward": "f6",
  "app.model.cycleBackward": "shift+f6"
}
```

## 七、小结

两个工具都在试图解决"终端里键位不够用"的老问题：

- **OpenCode** 用 leader 键隔离了"应用层命令"和"编辑器命令"，代价是要先按 `Ctrl+X`。一旦适应，体验最干净，因为可绑的命令数是**字母数 × 修饰键组合**，几乎无限。
- **Pi** 走纯 Emacs 路线，编辑器和应用层都直接绑。代价是双绑（`Ctrl+X` 既是复制又是清空模型），需要手动拆开。

如果你是个 Vim/Emacs 老炮，选 Pi 会觉得"我熟悉的键都还在"；如果你想快速自定义大量动作、或者不想记忆太多键，OpenCode 的 leader 键 + 命令面板（`Ctrl+P`）组合更省脑。

最后一条建议：不管选哪个，**第一次装上之后的第一件事**，都是打开它的快捷键配置文件对照自己最常用的 5 个动作调一遍。默认键位是"通用最优"，不是"为你最优"。

---

**参考资料**

- OpenCode 官方文档：[TUI](https://opencode.ai/docs/tui/)、[Keybinds](https://opencode.ai/docs/keybinds/)
- Pi-Coding-Agent 源码：`@earendil-works/pi-coding-agent/dist/core/keybindings.d.ts`（v0.84.4）
- Leader 键设计原型：GNU Screen 手册 / tmux `prefix` / btop `Ctrl+B`
