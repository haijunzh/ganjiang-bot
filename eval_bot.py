import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from websockets import client

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
# Initialize clients
chatgpt_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))    
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_URL") # Usually https://api.deepseek.com
)

# bot_client = deepseek_client
# bot_model="deepseek-chat"
# judge_client = chatgpt_client
# judge_model="gpt-4o"

bot_client = chatgpt_client
bot_model="gpt-5.5"
judge_client = chatgpt_client
judge_model="gpt-4o"

# bot_client = chatgpt_client
# bot_model="gpt-4o"
# judge_client = chatgpt_client
# judge_model="gpt-4o"

def load_knowledge_base():
    """Reads the local knowledge base file."""
    try:
        with open("ganjiang_knowledge.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("Error: ganjiang_knowledge.txt not found.")
        return ""

def get_bot_answer(question, context, bot_client=bot_client, bot_model=bot_model):
    """
    Simulates the DeepSeek bot's logic.
    """
    system_instruction = (
        f"You are a professional customer service for the Ganjiang Swim event.\n"
        f"Answer the question STRICTLY based on the following context:\n{context}\n"
        f"If the info is not in the context, say that you have not found any information about that.\n"
        f"Please reply in the language the user is using."
    )
    
    try:
        response = bot_client.chat.completions.create(
            model=bot_model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": question}
            ],
            temperature=1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"DeepSeek Error: {str(e)}"

def judge_answer(question, bot_answer, ideal_answer, judge_client=judge_client, judge_model=judge_model):
    evaluation_prompt = f"""
    You are a strict quality auditor. 
    Compare the [Bot Answer] against the [Ideal Answer].

    Scoring Rules:
    - 1.0: Excellent, matches key facts.
    - 0.5: Partially correct or missing minor details.
    - 0.0: Incorrect or hallucinated.

    ---
    Question: {question}
    Ideal Answer: {ideal_answer}
    Bot Answer: {bot_answer}
    ---

    Output ONLY the numerical score (1, 0.5, or 0).
    """
    
    try:
        # Always use a powerful model like GPT-4o to judge
        res = judge_client.chat.completions.create(
            model=judge_model,
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0
        )
        score_str = res.choices[0].message.content.strip()
        return float(score_str)
    except Exception:
        return 0.0

def run_evaluation(bot_client=bot_client, bot_model=bot_model, judge_client=judge_client, judge_model=judge_model):
    knowledge = load_knowledge_base()
    if not knowledge: return

    # Load the 10 test cases from test_cases.json
    try:
        with open("test_cases.json", "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    except Exception as e:
        print(f"Failed to load test_cases.json: {e}")
        return

    total_score = 0
    num_cases = len(test_cases)
    print(f"Bot Model: {bot_model}, Judge Model: {judge_model}")
    print(f"--- Starting Bot Evaluation ({num_cases} cases) ---")

    for i, case in enumerate(test_cases):
        q = case.get("question") #[cite: 1]
        ideal = case.get("ideal_answer") #[cite: 1]
        
        bot_ans = get_bot_answer(q, knowledge, bot_client=bot_client, bot_model=bot_model)
        score = judge_answer(q, bot_ans, ideal, judge_client=judge_client, judge_model=judge_model)
        total_score += score
        
        print(f"[{i+1}/{num_cases}] Score: {score}")
        print(f"Q: {q}")
        print(f"Bot Answer: {bot_ans}")
        print(f"Ideal Answer: {ideal}")
        print("-" * 20)

    accuracy = (total_score / num_cases) * 100
    print(f"\nBot Evaluation Complete!")
    print(f"Total Score: {total_score} / {num_cases}")
    print(f"Accuracy Rate: {accuracy:.2f}%")

if __name__ == "__main__":
    run_evaluation()