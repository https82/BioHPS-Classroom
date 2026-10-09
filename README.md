# 探知·BioHPS V6.2：课程知识增强版

**产品主线：** 初中生物自由提问、互动练习、错误诊断、教师备课。**特色模块：** HPS 科学探究（原有三个深度实验）。

## 本次实做功能

- 原有35张加原创118张，**共153张初中生物课程概要卡**，按七大课程主题组织。
- 每张卡包含主题、标题、核心解释、易混淆点、引导问题、关键词和审核状态。
- **离线混合检索：** 明确的专业词语匹配、人工整理同义表达和字符级 TF-IDF 文本相似度。**不是**预训练嵌入模型、独立深度学习模型、已建好的向量数据库或联网文献检索。
- 未命中课程卡时继续调用 DeepSeek 进行通用生物辅导，并明确告知未匹配到本地卡；不伪造引用。
- 课程侧栏显示本轮检索到的卡片、审核状态、相对匹配分和官方**课程主题参考链接**。匹配分不是科学准确率。
- 保留旧有课程对话、教师模式、HPS实验和导出功能。
- `python tools/audit_knowledge.py`：检查资料结构和未审核状态（不是科学事实核验）。
- `python tools/evaluate_retrieval.py`：对开发者准备的离线测试题检查检索命中，不发模型请求、不产生API费用。

## 本地 Windows 升级

建议停止程序后先完整备份当前 `BioHPS_project`。解压本包后，将**完整项目文件**覆盖到原文件夹，保留旧 `.venv` 和 `.streamlit/secrets.toml`，不要重新配置 DeepSeek。

这次**需要同时复制** `retrieval_index.py`、`curriculum.py`、`app.py` 和**整个** `knowledge` 文件夹；缺少任一文件会报错。也可复制所有项目文件/文件夹，避免漏文件。

在原项目 PowerShell 中运行：

```powershell
Test-Path .\retrieval_index.py
Test-Path .\knowledge\curriculum_cards.json
.\.venv\Scripts\python.exe tools\audit_knowledge.py
.\.venv\Scripts\python.exe tools\evaluate_retrieval.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

前两行应均为 `True`。在网页“💬 全课程AI课堂”保持“自动识别”，提问“为什么秋天叶子会变黄？”“细菌没有细胞核却有遗传物质吗？”“鲸为什么不是鱼？”。这三题应匹配相应课程卡；调用真实DeepSeek才会产生费用。

## 资料来源边界

课程主题框架参考 [教育部《义务教育生物学课程标准（2022年版）》](https://www.moe.gov.cn/srcsite/A26/s8001/202204/W020220420582359998122.pdf)。**这是课程组织层面的来源，不是153张卡每条科学事实的直接文献来源。** 内容为原创课程概要；所有卡片均标为“待教师审核”，不应在PPT上称为“教师审核的权威知识库”。不同教材版次、学校教学进度和术语深度仍需人工映射。

项目不保存个人身份信息；不要上传真实学生个人信息，不要把 `.streamlit/secrets.toml`、密钥、`.venv` 或学生学习记录放进公开仓库。已有 `.gitignore` 保留。

## 验证与后续

测试：`python -m pytest -q tests`；页面离线模拟：`python tools/smoke_offline.py`。这些验证不能替代 Windows 本机 Streamlit 浏览器+DeepSeek 端到端测试，或学科教师审核。长期计划可引入经过验证的嵌入式向量检索、出版社授权的教材章节映射、学生学习闭环与学习记录持久化。

**参赛提醒：** 先确保公网网页可打开、可提问，再完成PPT与MP4演示。部署指引见 `DEPLOYMENT_GUIDE.md`。
