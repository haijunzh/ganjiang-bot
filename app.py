import os
from dotenv import load_dotenv
import streamlit as st
import importlib
import sys
from openai import OpenAI

# 1. 基础配置与环境加载
# 1. Basic configuration and environment loading
load_dotenv()
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "en_US.UTF-8"

if sys.getdefaultencoding() != 'utf-8':
    importlib.reload(sys)

st.set_page_config(page_title="Ganjiang Swim AI", page_icon="🏊", layout="wide")

# --- 2. 双语字典配置 ---
# --- 2. Bilingual dictionary configuration ---
LANG_DICT = {
    "中文": {
        "title": "🏊 赣江游赛事 AI 客服",
        "sidebar_title": "控制面板",
        "select_model": "选择 AI 模型",
        "select_lang": "选择语言 / Language",
        "project_info": "🏊 赣江游赛事 AI 客服\n基于官网数据构建",
        "clear_history": "🗑️ 清除聊天记录",
        "caption": "当前运行大脑: {model} | 数据源: 赣江游官网",
        "info": "我是基于官网最新数据生成的智能助手。如果问题超出官网信息，我会回答‘没有找到相关信息’。",
        "input_placeholder": "请输入您想咨询的问题...",
        "error_msg": "调用 {model} 出错了: {error}",
        "no_info": "我没有在官网上找到相关信息，建议咨询人工客服",
        "system_role": "你是一个赣江游赛事的在线客服。请【严格】根据背景信息回答。严禁胡编乱造。"
    },
    "English": {
        "title": "🏊 Ganjiang Open Water Swim AI Assistant",
        "sidebar_title": "Control Panel",
        "select_model": "Select AI Model",
        "select_lang": "Language / 选择语言",
        "project_info": "🏊 Ganjiang Open Water Swim AI Assistant\nBuilt on Official Website Data",
        "clear_history": "🗑️ Clear Chat History",
        "caption": "Current Model: {model} | Source: Official Site",
        "info": "I am an intelligent assistant based on official data. If the question exceeds the data, I will say 'No information found'.",
        "input_placeholder": "Type your question here...",
        "error_msg": "Error with {model}: {error}",
        "no_info": "I couldn't find relevant information on the official website. Please contact human support.",
        "system_role": "You are a customer service assistant for the Ganjiang Swim event. Reply strictly based on the background information. Do not hallucinate."
    }
}

# --- 3. 侧边栏：语言与模型选择 ---
# --- 3. Sidebar: Language and Model Selection ---
with st.sidebar:
    st.title("Settings")
    
    # 语言选择
    lang_choice = st.selectbox("Language / 语言", ("中文", "English"), index=0)
    T = LANG_DICT[lang_choice]  # 所有的文本都从这个变量获取
    
    # 模型选择
    model_choice = st.selectbox(T["select_model"], ("DeepSeek", "ChatGPT"), index=0)
    
    st.info(T["project_info"])
    
    if st.button(T["clear_history"], use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 4. 初始化 API 客户端 ---
# --- 4. Initialize API Client ---
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
            "client": OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
            "model_name": "gpt-4o"
        }

config = get_api_config(model_choice)
client = config["client"]
model_name = config["model_name"]

# --- 5. 加载知识库 ---
# --- 5. Load Knowledge Base ---
@st.cache_data
def load_context():
    try:
        with open("ganjiang_knowledge.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "No background information available."

context = load_context()

# --- 6. 主界面渲染 ---
# --- 6. Main Interface Rendering ---
st.title(T["title"])
st.caption(T["caption"].format(model=model_choice))
st.info(T["info"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- 7. 聊天交互逻辑 ---
# --- 7. Chat Interaction Logic ---
if prompt := st.chat_input(T["input_placeholder"]):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    safe_context = context.encode('utf-8', errors='ignore').decode('utf-8')
    
    # 根据语言动态调整系统指令
    system_instr = f"""{T['system_role']}
Background Information:
{safe_context}
Default reply for missing info: {T['no_info']}
Please reply in the language the user is using.
"""

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
                temperature=0 
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(T["error_msg"].format(model=model_choice, error=str(e)))