import os
from dotenv import load_dotenv
import streamlit as st
import importlib
import sys
from openai import OpenAI

# 1. 基础配置与环境加载
load_dotenv()
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "en_US.UTF-8"

# 强制编码重载（针对特定环境）
if sys.getdefaultencoding() != 'utf-8':
    importlib.reload(sys)

st.set_page_config(page_title="赣江游赛事助手", page_icon="🏊", layout="wide")

# 2. 侧边栏配置：信息展示 + 模型切换 + 清除记录
with st.sidebar:
    st.title("控制面板")
    
    # --- 新增功能：模型选择 ---
    model_choice = st.selectbox(
        "选择 AI 模型",
        ("DeepSeek", "ChatGPT"),
        index=0,
        help="DeepSeek 中文理解强，ChatGPT 逻辑严密"
    )
    
    st.info("🏊 赣江游赛事 AI 客服\n基于官网数据构建")
    
    # 清除按钮
    if st.button("🗑️ 清除聊天记录", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 3. 初始化对应的 API 客户端
def get_api_config(choice):
    if choice == "DeepSeek":
        return {
            "client": OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
            ),
            "model_name": "deepseek-chat"
        }
    else:
        return {
            "client": OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            ),
            "model_name": "gpt-4o"  # 推荐使用 gpt-4o
        }

config = get_api_config(model_choice)
client = config["client"]
model_name = config["model_name"]

# 4. 加载知识库
@st.cache_data
def load_context():
    try:
        with open("ganjiang_knowledge.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "暂无官网具体背景信息。"

context = load_context()

# 5. 主界面标题
st.title("🏊 赣江游赛事 AI 客服")
st.caption(f"当前运行大脑: {model_choice} | 数据源: 赣江游官网")
st.info("我是基于官网最新数据生成的智能助手。如果问题超出官网信息，我会回答‘没有找到相关信息’。")

# 6. 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 7. 用户输入与 AI 响应逻辑
if prompt := st.chat_input("请输入您想咨询的问题..."):
    # 记录用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 准备上下文背景（严格限制）
    safe_context = context.encode('utf-8', errors='ignore').decode('utf-8')
    system_instr = f"""你是一个赣江游赛事的在线客服。
请【严格】根据以下提供的背景信息回答。
如果背景信息里没有相关内容，请直接回答“我没有在官网上找到相关信息，建议咨询人工客服”。
严禁胡编乱造，严禁回答与赣江游赛事无关的问题。

背景信息如下：
{safe_context}  
"""

    # AI 生成回答 (Stream 流式输出)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instr},
                    *st.session_state.messages 
                ],
                stream=True,
                temperature=0  # 保持答案的确定性
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"调用 {model_choice} 出错了: {str(e)}")