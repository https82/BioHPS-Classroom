# BioHPS V10.12 · Streamlit Cloud 发布文件

本压缩包的根目录即为 GitHub 仓库根目录：`app.py` 必须位于根目录，不要把整个 ZIP 上传到仓库作为单个文件，也不要再套一层目录。

## 更新现有网站
1. 登录原有 GitHub 仓库 `BioHPS-Classroom`，确认当前 Streamlit Cloud 绑定的分支（一般为 main）。
2. 打开 `Add file → Upload files`，把本压缩包解压后的**所有文件和文件夹**拖进上传区域，提交到对应分支。
3. 现有 Streamlit Cloud 站点会自动拉取变更。保留原站点域名 `https://biohps-classroom.streamlit.app/`。
4. 在 Streamlit Cloud `App settings → Secrets` 核对现有有效的 `BIOHPS_API_BASE`, `BIOHPS_MODEL`, `BIOHPS_API_KEY`。不要把密钥写到 GitHub 文件。
5. 打开站点验收初中／高中切换，学生A／B／C／D与教师，课程、AI连续提问、章节练习、科学探究、教师统计及PPT下载。

## 技术与安全边界
- 演示身份可被所有访问者切换，并非真实的师生登录权限。不要输入真实学生数据、个人信息或隐私。
- 演示数据写入云端本地 SQLite；云实例重启可能清空，本项目没有持久化数据库。
- 在线 AI 请求会消耗模型账户额度；请做好配额和费用管理。
- 历史上已公开过的 API 密钥必须撤销并替换为新的有效密钥。
- `knowledge/learning_resources_5000.jsonl` 包含5,000条课程微资源，不等同于5,000篇经教师审核的完整讲义。

本部署包只保留网页运行文件，不含 `.venv`、本地数据库、`secrets.toml`、测试源码及本地录制资料。
