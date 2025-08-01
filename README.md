# Graph Service for Read-ily

本项目构建于 Advanture-X 2025，是团队Read-ily主项目的知识图谱服务子模块，使用 Python Flask 构建，基于 [Zep Cloud](https://docs.getzep.com/) 提供的图谱能力，实现在阅读过程中渐进更新知识图谱、笔记管理、知识搜索与图谱可视化等功能。
<p align="center">
  <img src="assets/preview.png" alt="Graph Service Preview" width="60%">
</p>


---

## 项目功能

- 接收用户提交的原文与笔记内容，并将其更新进知识图谱
- 可获取用户边和节点信息，生成可视化的交互式图谱页面（基于 pyvis）
- 可检索节点或笔记
- 图谱服务模块独立部署、独立维护，方便团队协作

---

## 🔧 使用环境

- **Python version**：Python 3.12 is recommended
- **requirement**：

```txt
Flask
flask_cors
python-dotenv
pyvis
zep-cloud
```