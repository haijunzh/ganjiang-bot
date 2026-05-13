import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
# Use gpt-4o as the 'Judge' for higher evaluation accuracy
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_knowledge_base():
    """Reads the local knowledge base file."""
    try:
        with open("ganjiang_knowledge.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("Error: ganjiang_knowledge.txt not found.")
        return ""

def get_bot_answer(question, context):
    """Simulates the bot's logic to generate an answer based on context."""
    system_instruction = (
        f"You are a professional customer service for the Ganjiang Swim event.\n"
        f"Answer the question STRICTLY based on the following context:\n{context}\n"
        f"If the info is not in the context, say 'Information not found'."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # You can change this to "deepseek-chat" to test DeepSeek
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": question}
            ],
            temperature=0  # Zero temperature for consistent, reproducible results
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def judge_answer(question, bot_answer, ideal_answer):
    """
    The 'LLM-as-a-Judge' logic. 
    Compares bot output with ground truth and assigns a score.
    """
    evaluation_prompt = f"""
    You are a strict quality auditor for an AI chatbot.
    Compare the [Bot Answer] against the [Ideal Answer] based on the [Question].

    Scoring Rules:
    - 1.0: The answer is accurate and matches the ideal answer's key points.
    - 0.5: The answer is partially correct or misses minor details.
    - 0.0: The answer is wrong, irrelevant, or contains hallucinations.

    ---
    Question: {question}
    Ideal Answer: {ideal_answer}
    Bot Answer: {bot_answer}
    ---

    Output ONLY the numerical score (1, 0.5, or 0). Do not include any explanation.
    """
    
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0
        )
        score_str = res.choices[0].message.content.strip()
        return float(score_str)
    except Exception:
        return 0.0

def run_evaluation():
    # 1. Setup
    knowledge = load_knowledge_base()
    if not knowledge:
        return

    # 2. Load test cases
    try:
        with open("test_cases.json", "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    except Exception as e:
        print(f"Failed to load test_cases.json: {e}")
        return

    # 3. Execution loop
    total_score = 0
    num_cases = len(test_cases)
    print(f"--- Starting Evaluation on {num_cases} cases ---")

    for i, case in enumerate(test_cases):
        q = case.get("question")
        ideal = case.get("ideal_answer")
        
        # Get response from the bot
        bot_ans = get_bot_answer(q, knowledge)
        
        # Judge the response
        score = judge_answer(q, bot_ans, ideal)
        total_score += score
        
        print(f"[{i+1}/{num_cases}] Score: {score}")
        print(f"Q: {q}")
        print(f"Bot: {bot_ans}")
        print("-" * 20)

    # 4. Final Report
    accuracy = (total_score / num_cases) * 100
    print(f"\nEvaluation Complete!")
    print(f"Total Score: {total_score} / {num_cases}")
    print(f"Accuracy Rate: {accuracy:.2f}%")

if __name__ == "__main__":
    run_evaluation()