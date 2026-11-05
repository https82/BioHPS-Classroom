# V10.4本机部署与AI配置

本次版本采用独立目录，**请勿覆盖正在参赛展示的旧版**。

## 启动

解压到 `F:\ai2\BioHPS_V10_4`。在文件夹中打开PowerShell：

```powershell
& 'F:\ai2\BioHPS_V6_2\.venv\Scripts\python.exe' -m streamlit run app.py
```

或者双击 `启动_V10.cmd`。若提示缺少 Python/Streamlit，请先用 `python --version` 确认本机环境，再使用原虚拟环境安装 `requirements.txt`，不必删除旧项目。

## 旧AI密钥安全迁移（可选但使用真实AI必需）

```powershell
powershell -ExecutionPolicy Bypass -File '.\配置AI_安全迁移.ps1'
```

如脚本未找到旧版本地 Secrets，则参考 `.streamlit/secrets.example.toml`，在当前项目创建 `.streamlit/secrets.toml` 并复制你已在原项目验证有效的三个参数。不要将任何真实密钥写入代码或截图上传。云端保存的密钥不会自动转移到本地。

## 现有学习记录

独立文件夹会新建自己的 `demo_data/class_demo.sqlite`。如果你希望保留旧版V10.3演示的答题及实验记录，在**两个网页均已停止**的情况下，将旧版 `demo_data` 整个文件夹备份，然后复制到新版同名位置。新版数据库初始化时会兼容旧表并增加本版学习记录字段。请勿把包含活动记录的数据库加入GitHub。

## 线上演示提醒

这里只测试单机模拟的多身份功能，身份下拉选择不具有真正登录鉴权；多人同时使用、权限隔离以及未成年人的隐私安全需要正式部署前单独设计。不要把当前版本宣称为已完成学校级上线。
