import streamlit as st

# --- 页面设置 ---
st.set_page_config(page_title="赣江游赛事客服", page_icon="🚣")

# --- 模拟知识库 (后面我们会换成真正的网站抓取数据) ---
FAKE_KNOWLEDGE = {
    "报名": "赣江游赛事报名通常在官网首页的‘在线报名’入口进行，需准备身份证件。",
    "费用": "根据往年信息，报名费用约为200元，具体以官网最新公告为准。",
    "路线": "赛事路线覆盖赣江核心水域，起点设在八一桥附近，终点在南昌之星摩天轮。"
}

# --- 侧边栏 ---
with st.sidebar:
    st.title("关于项目")
    st.info("这是赣江游赛事的原型机器人。目前处于本地开发阶段。")
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

# --- 主界面 ---
st.title("🚣 赣江游赛事客服 (本地版)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入逻辑
if prompt := st.chat_input("您可以问我关于报名、费用或路线的问题"):
    # 展示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 简单的逻辑处理
    with st.chat_message("assistant"):
        response = ""
        # 模拟检索逻辑
        found = False
        for key in FAKE_KNOWLEDGE:
            if key in prompt:
                response = FAKE_KNOWLEDGE[key]
                found = True
                break
        
        if not found:
            response = "我没有找到相关信息。"
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        