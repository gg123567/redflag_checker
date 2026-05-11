import os
from openai import OpenAI
import pandas as pd
import re
import streamlit as st
import json
from pathlib import Path

# 页面设置
@st.cache_resource
def get_ai_client():
    api_key = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

client = get_ai_client()


# 小红书风格样式（只保留这一版）
def apply_xhs_style():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #fff7f8 0%, #fffafa 45%, #f9f5f6 100%);
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
        color: #2c2c2c;
    }

    .main .block-container {
        max-width: 860px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    .xhs-hero {
        background: linear-gradient(135deg, #fff1f4 0%, #fffafb 100%);
        border: 1px solid #ffe0e8;
        border-radius: 24px;
        padding: 24px 24px 18px 24px;
        box-shadow: 0 10px 30px rgba(255, 36, 66, 0.06);
        margin-bottom: 18px;
    }

         .xhs-header {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .xhs-logo {
        background: linear-gradient(135deg, #ff2442 0%, #ff5c77 100%);
        color: #fff;
        min-width: 64px;
        height: 64px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 14px;
        box-shadow: 0 10px 20px rgba(255, 36, 66, 0.18);
        flex-shrink: 0;
    }           
    .xhs-title {
        font-size: 30px;
        font-weight: 800;
        line-height: 1.2;
        color: #222;
        margin-bottom: 6px;
    }

    .xhs-subtitle {
        font-size: 14px;
        color: #7a7a7a;
        line-height: 1.7;
    }

    .xhs-card {
        background: rgba(255,255,255,0.92);
        border: 1px solid #ffe3ea;
        border-radius: 22px;
        padding: 20px 20px 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.04);
        backdrop-filter: blur(6px);
    }

    .xhs-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: #fff1f4;
        color: #ff2442;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .xhs-section-title {
        font-size: 18px;
        font-weight: 700;
        color: #222;
        margin-bottom: 4px;
    }

    .xhs-section-desc {
        font-size: 13px;
        color: #8a8a8a;
        margin-bottom: 12px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #ff2442 0%, #ff5c77 100%);
        color: white;
        border: none;
        border-radius: 999px;
        padding: 0.65rem 1.4rem;
        font-weight: 700;
        box-shadow: 0 8px 18px rgba(255, 36, 66, 0.18);
    }

    .stButton > button:hover {
        color: white;
        border: none;
        transform: translateY(-1px);
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 18px !important;
        border: 1px solid #ffd9e3 !important;
        background: #fffdfd !important;
        padding: 16px !important;
        line-height: 1.8 !important;
    }

    div[data-testid="stMetric"] {
        background: #fff;
        border: 1px solid #ffe4ea;
        border-radius: 18px;
        padding: 12px 8px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.03);
    }

    .stAlert {
        border-radius: 16px !important;
    }

    hr {
        border: none;
        height: 1px;
        background: #f4dbe2;
        margin: 18px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 应用小红书样式
apply_xhs_style()

# 顶部红色 Hero 区
st.markdown("""
<div class="xhs-hero">
    <div class="xhs-header">
        <div class="xhs-logo">小红书</div>
        <div>
            <div class="xhs-title">RedFlag 文本风险自检器</div>
            <div class="xhs-subtitle">
像发布小红书笔记一样，先检查表达风险、逻辑冲突和修改建议；
支持单条深度体检，也支持批量笔记一键扫风险。
</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
# 读取规则文件
rules_path = Path("risk_rules_v2.json")

with rules_path.open("r", encoding="utf-8") as f:
    risk_rules = json.load(f)

# 初始化 session state
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# 示例文本
demo_text = "这款面膜烂透了！千万别买，只有XX品牌能救你，效果100%，闭眼入！"

mode = st.radio(
    "选择检测模式",
    ["单条检测", "批量检测（每行一条笔记）"],
    horizontal=True
)
if "batch_rows" not in st.session_state:
    st.session_state["batch_rows"] = []
# 按钮区
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("填入示例笔记"):
        if mode == "单条检测":
            st.session_state.input_text = demo_text
        else:
            st.session_state.input_text = demo_text + "\n" + demo_text.replace("烂透了", "还可以")

with col_btn2:
    if st.button("清空草稿"):
        st.session_state.input_text = ""

# 输入框
st.markdown('<div class="xhs-card">', unsafe_allow_html=True)
st.markdown('<div class="xhs-badge">笔记草稿</div>', unsafe_allow_html=True)
st.markdown('<div class="xhs-section-title">把你准备发布的文案贴进来</div>', unsafe_allow_html=True)
st.markdown('<div class="xhs-section-desc">支持长文检测，系统会识别风险表达、逻辑冲突和发布建议。</div>', unsafe_allow_html=True)

# 输入框
if mode == "单条检测":
    user_text = st.text_area(
        "请输入要检测的文本",
        key="input_text",
        height=250,
        placeholder="例如：这款面膜烂透了！千万别买，只有XX品牌能救你。"
    )
else:
    user_text = st.text_area(
        "请输入要批量检测的文本（每行一条）",
        key="input_text",
        height=250,
        placeholder="每一行视为一条独立笔记进行检测",
    )
st.caption("本工具用于发布前辅助体检，不替代人工最终审核判断。")
st.markdown('</div>', unsafe_allow_html=True)

# 开始检测按钮
run_check = st.button("开始体检")

def passes_context_check(text: str, trigger: str, category: str) -> bool:
    """
    通用上下文检查：
    - 过滤明显正常的时间/次数表达
    - 区分“经验分享” vs “营销夸大”
    - 为高歧义词保留进一步 AI 复核的空间（之后可以再加）
    """

    # 统一小写/全角处理可以按需加，这里先只看原文
    t = text

    # 一类：时间/次数类表达 —— 不当风险源
    time_like_patterns = [
        r"第[一二三四五六七八九十]+次",
        r"第[一二三四五六七八九十]+天",
        r"第[一二三四五六七八九十]+周",
        r"第[一二三四五六七八九十]+个月",
        r"第[一二三四五六七八九十]+晚",
        r"第[一二三四五六七八九十]+回",
    ]

    if trigger in ["第一", "第二", "第三"]:
        for p in time_like_patterns:
            if re.search(p, t):
                # 像“第一次用”“第三周”这类，视为正常用语
                return False

    # 二类：主观体验句子 —— 降低风险权重
    # 后面如果想用，可以在你的打分函数里根据这个再降分
    subjective_markers = ["我觉得", "我用下来", "我个人感觉", "对我来说", "在我这", "我自己用"]
    if any(m in t for m in subjective_markers):
        # 主观体验 + 单个轻微 trigger → 倾向于不过度判
        if trigger in ["最好", "顶级", "神器", "无敌"]:
            # 主观体验里的一些夸张词，放宽一点
            return False

    # 三类：确实有营销夸大的强搭配 —— 保留为真风险
    strong_hype_patterns = [
        r"销量.*第一",
        r"全网.*第一",
        r"第一.*品牌",
        r"行业.*第一",
        r"效果.*百分之百",
        r"效果.*100％",
        r"包治百病",
        r"根治",
        r"永久有效",
    ]
    if any(re.search(p, t) for p in strong_hype_patterns):
        return True

    # 默认：如果只是单独出现一个高歧义短词，不直接判风险
    ambiguous_triggers = {"第一", "最好", "顶级", "神器", "无敌"}
    if trigger in ambiguous_triggers:
        return False

    # 其他情况统一放行给规则（按原来逻辑处理）
    return True

# 检测函数
def detect_risks(text, rules):
    results = []

    for category, rule_list in rules.items():
        for rule in rule_list:
            risk_level = rule["risk_level"]
            description = rule["description"]
            triggers = rule["triggers"]
            suggestions = rule["suggestions"]
            pattern_name = rule["pattern_name"]
            rule_id = rule["rule_id"]

            for trigger in triggers:
                if trigger in text and passes_context_check(text, trigger, category):
                    results.append({
                        "category": category,
                        "pattern_name": pattern_name,
                        "rule_id": rule_id,
                        "level": risk_level,
                        "keyword": trigger,
                        "reason": description,
                        "suggestion": suggestions.get(trigger, "建议改为更稳妥表达")
                    })

    return results

# 风险标签颜色
def get_level_badge(level):
    if level == "高风险":
        return ":red-badge[高风险]"
    elif level == "中高风险":
        return ":orange-badge[中高风险]"
    elif level == "中风险":
        return ":yellow-badge[中风险]"
    else:
        return ":blue-badge[低风险]"
    
def generate_publish_advice_with_ai(user_text, matches):
    if client is None:
        return {
            "status": "建议修改后发布",
            "reason": "未配置 DeepSeek API Key，暂时使用默认建议。"
        }

    try:
        prompt = f"""
你是一名内容审核助手。请根据以下文本给出发布建议。
只返回 JSON，格式如下：
{{"status": "可发布/建议修改后发布/不建议发布", "reason": "一句中文说明"}}

原文：
{user_text}
"""

        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "你是一名擅长中文内容风控判断的助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        
        return json.loads(content)

    except Exception as e:
        return {
            "status": "建议修改后发布",
            "reason": f"AI 判断失败：{str(e)}"
        }
        
def rewrite_text_with_ai(user_text, matches):
    if client is None:
        return "未配置 DeepSeek API Key，当前无法生成 AI 改写版本。"

    try:
        with st.spinner("正在生成 AI 改写...", show_time=True):
            prompt = f"""

你是一名内容优化助手，请基于下面文本生成一版更自然、更适合发布的中文表达。

要求：
1. 保留原意，不夸大，不绝对化
2. 避免违规、极限词、攻击性表达
3. 语气自然，像真实用户分享
4. 直接输出改写结果，不要解释

原文：
{user_text}
"""

            response = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {"role": "system", "content": "你是一名擅长中文内容风控优化的助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            result = response.choices[0].message.content.strip()
            return result

    except Exception as e:
        return f"AI 改写失败：{str(e)}"
    
# 整体风险等级
def calculate_risk_score(matches, logic_conflicts=None):


    if logic_conflicts is None:
        logic_conflicts = []

    score = 0

    for item in matches:
        level = item["level"]
        keyword = item["keyword"]

        if level == "高风险":
            score += 4
        elif level == "中高风险":
            score += 3
        elif level == "中风险":
            score += 2
        else:
            score += 1

        light_keywords = ["70%", "不错", "很好闻", "还可以", "有点", "一丢丢", "感觉不错", "比较清爽"]
        if keyword in light_keywords:
            score -= 1

    if len(matches) >= 3:
        score += 1
    if len(matches) >= 5:
        score += 2

    score += len(logic_conflicts) * 2

    return max(score, 0)

def get_overall_level(matches, logic_conflicts=None):
    if logic_conflicts is None:
        logic_conflicts = []

    score = calculate_risk_score(matches, logic_conflicts)

    # 单点命中保护：只有一个命中且无逻辑冲突时，不直接判高风险
    if len(matches) == 1 and not logic_conflicts:
        if score >= 5:
            return "中高风险"
        elif score >= 2:
            return "中风险"
        else:
            return "低风险"

    if score >= 8:
        return "高风险"
    elif score >= 5:
        return "中高风险"
    elif score >= 2:
        return "中风险"
    else:
        return "低风险"

        # 对一些“比较轻”的表达做降权
        if keyword in ["70%", "不错", "很好闻", "还可以"]:
            score -= 1

    # 同类命中过多，再轻微加权
    if len(matches) >= 3:
        score += 1
    if len(matches) >= 5:
        score += 2

    # 逻辑冲突单独加分
    score += len(logic_conflicts) * 2

    if score >= 8:
        return "高风险"
    elif score >= 5:
        return "中高风险"
    elif score >= 2:
        return "中风险"
    else:
        return "低风险"

# 统计命中类别数
def count_categories(matches):
    categories = set(item["category"] for item in matches)
    return len(categories)

# 按类别汇总
def group_by_category(matches):
    grouped = {}

    for item in matches:
        category = item["category"]
        if category not in grouped:
            grouped[category] = {
                "level": item["level"],
                "reason": item["reason"],
                "keywords": [],
                "suggestions": []
            }

        grouped[category]["keywords"].append(item["keyword"])
        grouped[category]["suggestions"].append(
            f"{item['keyword']} → {item['suggestion']}"
        )

    return grouped

# 生成修改后文本
def generate_revised_text(text, matches):
    revised_text = text

    # 先做词级替换
    for item in matches:
        revised_text = revised_text.replace(item["keyword"], item["suggestion"])

    # 再根据文案风格做自然化改写
    note_style = detect_note_style(text)

    if note_style == "避坑型":
        revised_text = (
            "这是我这次使用后的个人感受，整体体验没有特别惊喜，"
            + revised_text +
            " 如果你也在关注这类产品，建议结合自己的需求和使用习惯再做判断。"
        )
    elif note_style == "推荐型":
        revised_text = (
            "这是我近期使用下来的一些真实感受，"
            + revised_text +
            " 整体来说表现还不错，感兴趣的话可以根据自己的需求进一步了解。"
        )
    else:
        revised_text = (
            "这是一段基于个人体验整理的分享，"
            + revised_text +
            " 如果你也在做选择，可以把它当作一个参考。"
        )

    # 简单清洗重复表达
    revised_text = revised_text.replace("这是我这是我的个人使用感受", "这是我的个人使用感受")
    revised_text = revised_text.replace("欢迎平台内交流，欢迎留言交流", "欢迎留言交流")
    revised_text = revised_text.replace("可以按自身需求考虑了", "可以按自身需求考虑")
    revised_text = revised_text.replace("后选择了", "后选择")
    revised_text = revised_text.replace("！！", "！")

    return revised_text

def detect_note_style(text):
    if any(word in text for word in ["别买", "踩雷", "避坑", "失望", "烂透了"]):
        return "避坑型"
    elif any(word in text for word in ["推荐", "回购", "爱用", "闭眼入", "冲"]):
        return "推荐型"
    else:
        return "分享型"
# 逻辑矛盾检测
def detect_logic_conflicts(text):
    conflicts = []
# 生成总结语
def generate_summary(level, category_count):
    if level == "高风险":
        return f"当前文本整体风险较高，检测到 {category_count} 类风险表达，建议优先修改绝对化、医疗功效或强情绪类表述。"
    elif level == "中高风险":
        return f"当前文本存在较明显的表达风险，共涉及 {category_count} 类风险，建议优化语气和推荐方式。"
    elif level == "中风险":
        return f"当前文本存在一定表达风险，共涉及 {category_count} 类风险，建议对个别推荐用语进行调整。"
    else:
        return "当前文本整体较稳妥，未发现明显高风险表达。"
    
    # 规则1：避坑/吐槽 + 单一品牌强推
    negative_words = ["避坑", "别买", "千万别买", "踩雷", "失望"]
    strong_recommend_words = ["只有", "能救你", "闭眼入", "必须买"]

    if any(word in text for word in negative_words) and any(word in text for word in strong_recommend_words):
        conflicts.append({
            "type": "避坑表达与强推荐并存",
            "reason": "文本一边表达负面避坑态度，一边又出现强导向推荐，容易造成表达逻辑不一致。"
        })

    # 规则2：真实分享 + 绝对化结论
    personal_words = ["真实分享", "个人体验", "仅个人感受", "自用感受"]
    absolute_words = ["100%", "根治", "最强", "唯一", "彻底"]

    if any(word in text for word in personal_words) and any(word in text for word in absolute_words):
        conflicts.append({
            "type": "个人体验与绝对化结论并存",
            "reason": "文本强调是个人体验，但又给出确定性过强的结论，表达可信度存在冲突。"
        })

    # 规则3：客观测评 + 强情绪攻击
    objective_words = ["客观测评", "理性分析", "真实测评", "中立评价"]
    emotion_words = ["烂透了", "气炸了", "恶心", "离谱", "崩溃了"]

    if any(word in text for word in objective_words) and any(word in text for word in emotion_words):
        conflicts.append({
            "type": "客观测评与情绪化表述并存",
            "reason": "文本声称客观或中立，但实际使用了明显情绪化词语，表达风格不一致。"
        })

    return conflicts
# 生成总结语
def generate_creator_tip(user_text, overall_level, logic_conflicts, publish_advice):
    status = publish_advice.get("status", "建议修改后发布")

    if overall_level == "高风险":
        return "这条内容当前风险偏高，更适合先降强度、去绝对化，再决定是否发布。"
    elif overall_level == "中高风险":
        return "这条内容已经有可用信息，但表达偏冲，建议先改语气和推荐方式。"
    elif logic_conflicts:
        return "这条内容的主要问题不一定是敏感词，而是表达逻辑不够统一，建议先统一立场再发布。"
    elif status == "可发布":
        return "这条内容整体较稳，可以作为经验分享型内容发布，再补一点个人场景会更自然。"
    else:
        return "这条内容基础不错，适合再润色一下措辞，让它更像真实分享而不是强引导表达。"

    # 主逻辑
if run_check:
    if not user_text.strip():
        st.warning("请先输入一段文本。")
    else:
        if mode == "单条检测":
            # === 原来的单条逻辑都放在这里 ===
            matches = detect_risks(user_text, risk_rules)
            logic_conflicts = detect_logic_conflicts(user_text)

            if len(matches) == 0:
                st.markdown('<div class="xhs-card">', unsafe_allow_html=True)
                st.markdown('<div class="xhs-badge">体检结果</div>', unsafe_allow_html=True)
                st.subheader("检测结果总览")
                st.success("整体看起来还挺稳的，可以继续润色后发布～")
                st.info("当前文本没有命中明显高风险表达，建议再人工检查一次语气、事实依据和品牌表述。")
                st.subheader("发布建议状态")
                st.success("状态：可发布")
                st.write("说明：当前未发现明显高风险表达，但正式发布前仍建议结合具体场景再确认。")
                st.subheader("优化后文本")
                st.text_area(
                    "这是系统生成的推荐发布版本",
                    value=user_text,
                    height=220
                )
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                overall_level = get_overall_level(matches, logic_conflicts)
                total_hits = len(matches)
                total_categories = count_categories(matches)
                grouped_results = group_by_category(matches)
                summary_text = generate_summary(overall_level, total_categories)

                publish_advice = generate_publish_advice_with_ai(user_text, matches)
                ai_revised_text = rewrite_text_with_ai(user_text, matches)
             
                creator_tip = generate_creator_tip(
                  user_text,
                  overall_level,
                  logic_conflicts,
                  publish_advice
                )
                st.subheader("优化后文本")
                st.text_area(
                    "这是系统生成的推荐发布版本",
                    value=ai_revised_text,
                    height=220
                )
                st.subheader("改写对比")
                st.markdown("左侧是原文，右侧是 AI 改写后版本，系统会高亮发生变化的位置。")
        

                st.markdown('<div class="xhs-card">', unsafe_allow_html=True)
                st.subheader("检测结果总览")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总体风险等级", overall_level)
                with col2:
                    st.metric("命中风险点", total_hits)
                with col3:
                    st.metric("涉及风险类别", total_categories)

                st.info(summary_text)
                st.markdown("### 总结建议")
                st.info(creator_tip)
                st.markdown("### 发布建议状态")

                status = publish_advice.get("status", "建议修改后发布")
                reason = publish_advice.get("reason", "无")

                if status == "可发布":
                    st.success(f"状态：{status}")
                elif status == "不建议发布":
                    st.error(f"状态：{status}")
                else:
                    st.warning(f"状态：{status}")

                st.write(f"说明：{reason}")

                st.markdown("---")
                st.subheader("逻辑矛盾提示")
                st.caption("系统会检查文案中是否同时出现互相矛盾的表达立场，例如一边避坑一边强推。")

                if logic_conflicts:
                  for conflict in logic_conflicts:
                   st.warning(f"**{conflict['type']}**：{conflict['reason']}")
                else:
                   st.success("暂未发现明显逻辑冲突，当前表达主线相对一致。")

                st.markdown("---")

                with st.expander("查看详细风险点", expanded=False):
                    for category, info in grouped_results.items():
                        st.markdown(f"### {category}")
                        st.markdown(f"{get_level_badge(info['level'])}")
                        st.write(f"**原因说明：** {info['reason']}")
                        st.write(f"**命中词：** {', '.join(info['keywords'])}")
                        st.write("**建议替换：**")
                        for suggestion in info["suggestions"]:
                            st.markdown(f"- {suggestion}")
                        st.markdown("---")

                
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            # === 新增：批量检测逻辑 ===
            notes = [line.strip() for line in user_text.splitlines() if line.strip()]
            if not notes:
                st.warning("批量模式下，请至少输入一行内容。")
            else:
                st.markdown('<div class="xhs-card">', unsafe_allow_html=True)
                st.markdown('<div class="xhs-badge">批量体检</div>', unsafe_allow_html=True)
                st.subheader(f"共 {len(notes)} 条笔记的风险总览")

                rows = []
                for idx, note in enumerate(notes, start=1):
                    matches = detect_risks(note, risk_rules)
                    overall_level = get_overall_level(matches, []) if matches else "低风险"
                    publish_advice = generate_publish_advice_with_ai(note, matches)

                    need_rewrite = "是" if overall_level in ["高风险", "中高风险"] else "否"

                need_rewrite = "是" if overall_level in ["高风险", "中高风险"] else "否"

                rows.append({
                     "编号": idx,
                     "笔记开头": (note[:26] + "……") if len(note) > 26 else note,
                     "整体风险": overall_level,
                     "是否需要改写": need_rewrite,
                     "发布建议": publish_advice.get("status", "建议修改后发布"),
                     "说明": publish_advice.get("reason", "无")
                 })
                
                st.session_state["batch_rows"] = rows

                df = pd.DataFrame(rows)

                def highlight_rows(row):
                    if row["整体风险"] == "高风险":
                        color = "background-color: #fde7e7"
                    elif row["整体风险"] == "中高风险":
                        color = "background-color: #fff1df"
                    elif row["整体风险"] == "中风险":
                        color = "background-color: #fff9db"
                    else:
                        color = ""
                    return [color] * len(row)

                styled_df = df.style.apply(highlight_rows, axis=1)
                high_risk_count = sum(1 for row in rows if row["整体风险"] in ["高风险", "中高风险"])
                rewrite_count = sum(1 for row in rows if row["是否需要改写"] == "是")

        
                high_risk_count = sum(1 for row in rows if row["整体风险"] in ["高风险", "中高风险"])
                rewrite_count = sum(1 for row in rows if row["是否需要改写"] == "是")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                   st.metric("总笔记数", len(rows))
                with col_b:
                   st.metric("高优先级", high_risk_count)
                with col_c:
                   st.metric("建议改写", rewrite_count)


                if len(rows) > 3:
                 with st.expander("筛选条件", expanded=False):
                  selected_levels = st.multiselect(
                  "按风险等级筛选",
                  ["高风险", "中高风险", "中风险", "低风险"],
                 default=["高风险", "中高风险", "中风险", "低风险"]
                )

                 selected_rewrite = st.multiselect(
                 "按改写需求筛选",
                ["是", "否"],
               default=["是", "否"]
                )
                else:
                  selected_levels = ["高风险", "中高风险", "中风险", "低风险"]
                  selected_rewrite = ["是", "否"]

                df = pd.DataFrame(rows)

                df = df[
                   df["整体风险"].isin(selected_levels) &
                   df["是否需要改写"].isin(selected_rewrite)
                 ]

                def highlight_rows(row):
                 if row["整体风险"] == "高风险":
                   color = "background-color: #fde7e7"
                 elif row["整体风险"] == "中高风险":
                   color = "background-color: #fff1df"
                 elif row["整体风险"] == "中风险":
                   color = "background-color: #fff9db"
                 else:
                   color = ""
                 return [color] * len(row)

                styled_df = df.style.apply(highlight_rows, axis=1)

                st.subheader("笔记列表")
                st.dataframe(styled_df, width="stretch")

                st.markdown("""
                <div class="xhs-section-desc">
                每一行视为一条独立笔记进行体检，适合小团队在发布前快速扫一遍风险。
                如需查看某条的详细风险和改写，可以切换回单条模式粘贴完整内容。
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
        
