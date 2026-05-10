import os
from dotenv import load_dotenv
# 必须在所有其他 import 之前
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
api_url = os.getenv("DEEPSEEK_API_URL")

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "en_US.UTF-8"

import streamlit as st
import importlib
import sys

# 强制重载 sys 模块（针对某些旧版本 Python 环境的黑科技）
if sys.getdefaultencoding() != 'utf-8':
    importlib.reload(sys)
    # 注意：在 Python 3.x 中 sys.setdefaultencoding 已被移除
    # 但我们可以通过这种方式干扰底层的 io 行为

import streamlit as st
from openai import OpenAI

# 配置 DeepSeek 客户端
# 注意：正式部署到 AWS 时，请通过环境变量设置，不要硬编码 Key
client = OpenAI(
    api_key=api_key,
    base_url=api_url
)

st.set_page_config(page_title="赣江游赛事助手", page_icon="🏊")

# 加载知识库
@st.cache_data
def load_context():
    with open("ganjiang_knowledge.txt", "r", encoding="utf-8") as f:
        return f.read()

context = load_context()

st.title("🏊 赣江游赛事 AI 客服")
st.info("我是基于官网最新数据生成的智能助手。如果问题超出官网信息，我会回答‘不知道’。")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 用户输入
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    safe_context = context.encode('utf-8', errors='ignore').decode('utf-8')
    # 构造 Prompt
    system_instr = f"""你是一个赣江游赛事的在线客服。
请【严格】根据以下提供的背景信息回答。
如果背景信息里没有相关内容，请直接回答“我没有在官网上找到相关信息，建议咨询人工客服”。
严禁胡编乱造，严禁回答与赣江游赛事无关的问题。

背景信息如下：
{safe_context}  
"""

    with st.chat_message("assistant"):
        # 这里的 stream=True 可以让回答像 ChatGPT 一样一个字一个字跳出来
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_instr},
                    *st.session_state.messages # 包含上下文对话
                ],
                stream=True,
                temperature=0 # 关键：确保不胡说八道
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"出错了: {str(e)}")