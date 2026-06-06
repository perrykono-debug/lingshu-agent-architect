# 灵枢技能包 (Ling Shu Skills)

Agent 设计师灵枢的专用技能集合。

## 技能列表

### ling-shu-agent-designer (v1.3.0)
灵枢主技能 - Agent 设计师工作流与规范

**触发场景：**
- 用户要求设计 AI Agent 方案
- 需要创建新的 Agent
- 需要优化现有 Agent
- 需要发布/更新技能包到 GitHub & ClawHub

**核心能力：**
- 5步工作流：需求沟通 → 场景大纲 → 创建基础版 → 后续深化 → 自动发布
- 7项大纲模板：行业定位、核心功能、数据源、交互渠道、定时任务、Skill规划、治理边界
- 三大思想体系：吴明辉（组织）+ 吴恩达（方法）+ 傅盛（落地）
- 自动发布：一键推送到 GitHub & ClawHub（发布前 diff 预览确认）

### enterprise-agent-planner (v1.0.0)
企业 Agent 体系规划器

**触发场景：**
- 输入企业介绍，自动输出 AI Agent 体系规划方案
- 用户提供企业官网、企业介绍文档、行业报告

**核心能力：**
- 企业解析 → 行业场景映射 → Agent 体系规划 → MVP 落地建议

## 设计原则

融合三大 AI Agent 思想体系：
- **吴明辉（组织视角）**：Multi-Agent 协作、组织结构重塑
- **吴恩达（方法视角）**：Agentic Workflow、迭代优于完美
- **傅盛（落地视角）**：场景为王、窄场景切入、人机协作

## 自动发布

灵枢支持一键发布技能包：

**触发词：**
- "将某个 agent 更新发布"
- "发布到 clawhub"
- "推送到 github"
- "更新技能包"

**发布流程：**
1. 给用户看 diff 预览
2. 用户确认后执行
3. 自动推送到 GitHub
4. 自动发布到 ClawHub

**固定配置：**
- GitHub: `perrykono-debug/lingshu-agent-architect`
- ClawHub: `lingshu-agent-architect`

## 版本历史

- v1.3.0 (2025-06-06): 自动发布能力融入主技能，支持一键推送到 GitHub & ClawHub
- v1.2.0 (2025-06-06): 新增 skill-publisher 技能（已合并入主技能）
- v1.1.0 (2025-06-06): 新增 enterprise-agent-planner 技能
- v1.0.0 (2025-05-29): 初始版本，ling-shu-agent-designer 基础功能
