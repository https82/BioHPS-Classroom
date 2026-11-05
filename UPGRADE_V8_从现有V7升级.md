# V8.0 极简升级（适用于已能启动的 F:\ai2\BioHPS_V6_2）

## 第一步：备份旧页面并复制4个文件

如果当前Streamlit正在运行，先在那个终端按 `Ctrl+C` 停止。

在 `F:\ai2\BioHPS_V6_2` 的PowerShell窗口执行：

```powershell
Copy-Item .\app.py .\app_v7_backup.py -Force
Copy-Item .\curriculum.py .\curriculum_v7_backup.py -Force
```

解压 `BioHPS_V8_0_四文件安全升级包.zip`，只复制：

- `app.py` → `F:\ai2\BioHPS_V6_2\app.py`（覆盖）
- `curriculum.py` → `F:\ai2\BioHPS_V6_2\curriculum.py`（覆盖）
- `senior_practice.py` → `F:\ai2\BioHPS_V6_2\senior_practice.py`（新增）
- `knowledge\high_school_cards.json` → `F:\ai2\BioHPS_V6_2\knowledge\high_school_cards.json`（新增）

不要删 `.venv` / `knowledge\curriculum_cards.json` / `knowledge\library.json` / 原有秘钥配置。**不必重新运行pip安装**。

## 第二步：检查文件并启动

```powershell
Test-Path .\senior_practice.py
Test-Path .\knowledge\high_school_cards.json
.\.venv\Scripts\python.exe -m streamlit run app.py
```

应能看到五个常用页面，进入“学课程”可切换初中、高中；选“高中→遗传与进化→减数分裂”可以跳转问AI。

AI问答沿用原有配置。如果本地仍然提示未设置模型，这与本次升级无关，需要把原有配置在本地正确恢复；不要将API Key粘贴到公开聊天或GitHub。

**请先不要上传GitHub**。本机实测后，再一起按需更新线上版本。

### 回滚

将 `app_v7_backup.py` 复制回 `app.py`，将 `curriculum_v7_backup.py` 复制回 `curriculum.py`；无需删除新加的高中资料文件，旧版不会加载它们。
