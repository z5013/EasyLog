# 📦 easylogz 发布与更新标准流程文档  
> 📅 最后更新：2025-09-18  
> ✍️ 作者：你  
> 🎯 目标：确保每次版本更新安全、规范、零失误！

---

## 🧭 一、准备工作（首次发布后只需做一次）

✅ **1. 获取 PyPI API Token（Entire Account 权限）**

- 登录 [PyPI 账户](https://pypi.org/)
- 进入：https://pypi.org/manage/account/token/
- 创建 Token，Scope 选 **Entire account**
- 复制并**安全保存**（只显示一次！）
- Token 格式：`pypi-AgEIcHlwaS5vcmc...`

> 💡 建议保存在密码管理器或本地加密文件中，**不要上传到 GitHub！**

✅ **2. 安装必要工具（只需一次）**

```bash
pip install build twine
```

---

## 🔄 二、每次更新的标准流程（5步走）

### ✅ Step 1：修改版本号

打开 `pyproject.toml`：

```toml
[project]
name = "easylogz"
version = "0.1.0"  👈 修改为新版本，如 "0.1.1" 或 "0.2.0"
```

> 📌 **语义化版本建议：**
> - `MAJOR.MINOR.PATCH`
> - `0.1.0` → 初始版本
> - `0.1.1` → 修复 bug / 小优化
> - `0.2.0` → 新增功能
> - `1.0.0` → 稳定版，API 冻结

---

### ✅ Step 2：更新 CHANGELOG.md（推荐）

在项目根目录创建或更新 `CHANGELOG.md`：

```markdown
# Changelog

## [0.1.1] - 2025-09-18
### Fixed
- 修复默认日志目录为 site-packages 的问题，默认改为 `./logs/`
- 优化日志初始化提示信息

## [0.1.0] - 2025-09-18
### Added
- 首次发布！支持 setup_logging 配置和 get_logger 使用
- 支持控制台 + 文件双输出
- 支持日志轮转（max_bytes + backup_count）
```

> 💡 用户和协作者会感谢你！

---

### ✅ Step 3：清理旧构建 + 重新构建

```bash
# 删除旧的构建产物
rmdir /s /q dist

# 重新构建（生成 .whl 和 .tar.gz）
python -m build
```

> ✅ 确认输出：
> ```
> Successfully built easylogz-0.1.1.tar.gz and easylogz-0.1.1-py3-none-any.whl
> ```

---

### ✅ Step 4：本地测试安装（强烈推荐）

```bash
# 从官方源安装测试（避免镜像延迟）
pip install easylogz==0.1.1 -i https://pypi.org/simple --force-reinstall

# 验证导入和功能
python -c "from easylogz import get_logger; logger = get_logger(); logger.info('✅ 本地测试通过')"
```

> 🧪 如果报错，立即修复，不要上传！

---

### ✅ Step 5：上传到 PyPI

```bash
twine upload --username __token__ --password pypi-你的完整token字符串 dist/*
```

> ✅ 成功标志：
> ```
> View at:
> https://pypi.org/project/easylogz/0.1.1/
> ```

---

## 🚨 三、常见错误 & 解决方案速查表

| 错误现象 | 原因 | 解决方案 |
|----------|------|----------|
| `403 Forbidden` | Token 无效/权限不足 | 重新生成 Entire Account 权限 Token |
| `400 File already exists` | 重复上传同版本 | 修改 `pyproject.toml` 版本号，重新构建上传 |
| `No module named 'easylogz'` | 未暴露接口 | 检查 `easylogz/__init__.py` 是否导出函数 |
| `清华源找不到包` | 镜像未同步 | 临时用 `-i https://pypi.org/simple` 安装 |

---

## 📚 四、推荐项目结构（供参考）

```
easylogz/
├── easylogz/
│   ├── __init__.py          # 暴露 setup_logging, get_logger
│   └── logger.py            # 核心日志实现
├── pyproject.toml           # 项目元数据 + 依赖
├── README.md                # 项目介绍 + 安装使用说明
├── CHANGELOG.md             # 版本更新日志（强烈推荐！）
├── example.py               # 快速体验脚本
├── LICENSE                  # 开源协议（推荐 MIT）
└── .gitignore               # 忽略文件（dist/, __pycache__ 等）
```

---

## 🛡️ 五、安全 & 最佳实践

- ✅ **永远不要提交 Token 到 Git！**
- ✅ 使用 `.gitignore` 忽略 `dist/`, `*.pyc`, `.env`
- ✅ 每次更新前先本地测试
- ✅ 更新 `CHANGELOG.md`，方便用户了解变更
- ✅ 使用语义化版本号，用户依赖更稳定

---

## 🎁 Bonus：一键发布脚本（可选）

创建 `release.bat`（Windows）或 `release.sh`（Linux/macOS）：

```bat
@echo off
echo 🚀 开始发布新版本...

rem Step 1: 用户手动修改 pyproject.toml 版本号

rem Step 2: 清理旧构建
rmdir /s /q dist

rem Step 3: 重新构建
python -m build

rem Step 4: 上传（请替换为你的 Token）
twine upload --username __token__ --password pypi-你的完整token字符串 dist/*

echo 🎉 发布完成！
pause



```
