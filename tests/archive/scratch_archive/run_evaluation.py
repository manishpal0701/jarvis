import sys
import os
import json
import time
import traceback

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai.ask_ollama import ask_ollama
from conversation.conversation_manager import ConversationManager
from ai.ai_response_manager import AIResponseManager

OUT_PATH = os.path.join(BASE_DIR, "scratch", "eval_results.json")

def load_results():
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_results(data):
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def reset_session():
    conv_mgr = ConversationManager()
    conv_mgr.clear_history()

def run_single(prompt, reset=True):
    if reset:
        reset_session()
    print(f"\n--- USER: {prompt} ---", flush=True)
    t0 = time.time()
    try:
        resp = ask_ollama(prompt, "Manish", "owner")
    except Exception as e:
        resp = f"[ERROR: {e}]"
        print(f"ERROR: {e}", flush=True)
        traceback.print_exc()
    dt = round(time.time() - t0, 2)
    print(f"JARVIS ({dt}s): {resp}", flush=True)
    return {"prompt": prompt, "response": resp, "latency_sec": dt}

def run_session(prompts):
    reset_session()
    resps = []
    for p in prompts:
        print(f"\n--- USER: {p} ---", flush=True)
        t0 = time.time()
        try:
            resp = ask_ollama(p, "Manish", "owner")
        except Exception as e:
            resp = f"[ERROR: {e}]"
            print(f"ERROR: {e}", flush=True)
            traceback.print_exc()
        dt = round(time.time() - t0, 2)
        print(f"JARVIS ({dt}s): {resp}", flush=True)
        resps.append({"prompt": p, "response": resp, "latency_sec": dt})
    return resps

def main():
    print("==================================================", flush=True)
    print("STARTING JARVIS CONVERSATION QUALITY EVALUATION", flush=True)
    print("MODEL: qwen3:8b (think=False, CONVERSATION_OPTIONS)", flush=True)
    print("==================================================", flush=True)

    print("[PREWARMING OLLAMA MODEL]", flush=True)
    ai_mgr = AIResponseManager()
    ai_mgr.prewarm()
    time.sleep(1)

    results = load_results()

    # 1. NATURAL HUMAN LANGUAGE
    if "sec1" not in results:
        print("\n>>> SECTION 1: NATURAL HUMAN LANGUAGE", flush=True)
        sec1_prompts = [
            "Jarvis, aaj mera mood thoda off hai.",
            "Jarvis, tu kya kar raha hai?",
            "Jarvis, aaj bahut thak gaya hoon yaar.",
            "Jarvis, mujhe coding samajh nahi aa rahi.",
            "Jarvis, kal mera exam hai aur mujhe tension ho rahi hai.",
            "Jarvis, bhai ek baat bata.",
            "Jarvis, mujhe aaj kuch karne ka mann nahi kar raha."
        ]
        results["sec1"] = [ run_single(p) for p in sec1_prompts ]
        save_results(results)

    # 2. HUMAN-LIKE CONVERSATION STYLE
    if "sec2" not in results:
        print("\n>>> SECTION 2: HUMAN-LIKE CONVERSATION STYLE", flush=True)
        sec2_prompts = [
            "Jarvis, aaj coding karne ka bilkul mann nahi hai.",
            "haan yaar, bas thak gaya hoon.",
            "tu hota toh kya karta?"
        ]
        results["sec2"] = run_session(sec2_prompts)
        save_results(results)

    # 3. EMOTIONAL EXPRESSION
    if "sec3" not in results:
        print("\n>>> SECTION 3: EMOTIONAL EXPRESSION", flush=True)
        sec3_prompts = [
            "Jarvis, mera project finally chal gaya!",
            "Jarvis, mera code baar baar fail ho raha hai yaar.",
            "Jarvis, aaj bahut bura din tha.",
            "Jarvis, mujhe result ka tension ho raha hai."
        ]
        results["sec3"] = [ run_single(p) for p in sec3_prompts ]
        save_results(results)

    # 4. NO ROBOTIC BULLET-POINT BEHAVIOR
    if "sec4" not in results:
        print("\n>>> SECTION 4: NO ROBOTIC BULLET-POINT BEHAVIOR", flush=True)
        sec4_prompts = [
            "Jarvis kya haal hai?",
            "Aaj kya scene hai?",
            "Bhai ek joke suna.",
            "Mujhe bore lag raha hai.",
            "Kya karu?"
        ]
        results["sec4"] = [ run_single(p) for p in sec4_prompts ]
        save_results(results)

    # 5. RESPONSE LENGTH
    if "sec5" not in results:
        print("\n>>> SECTION 5: RESPONSE LENGTH", flush=True)
        sec5_prompts = [
            "Jarvis, kya haal hai?",
            "Jarvis, mujhe Python seekhna start karna hai, kaha se shuru karu?",
            "Jarvis, mujhe AI engineer banna hai aur Python bhi aati hai, ab next kya seekhu?"
        ]
        results["sec5"] = [ run_single(p) for p in sec5_prompts ]
        save_results(results)

    # 6. FOLLOW-UP QUESTIONS
    if "sec6" not in results:
        print("\n>>> SECTION 6: FOLLOW-UP QUESTIONS", flush=True)
        sec6_prompts = [
            "Jarvis, mujhe project banana hai.",
            "Ek AI project.",
            "Python me."
        ]
        results["sec6"] = run_session(sec6_prompts)
        save_results(results)

    # 7. INTERRUPT / CASUAL LANGUAGE
    if "sec7" not in results:
        print("\n>>> SECTION 7: INTERRUPT / CASUAL LANGUAGE", flush=True)
        sec7_prompts = [
            "haan",
            "nahi yaar",
            "accha",
            "ruk",
            "sun",
            "ek sec",
            "acha ye bata",
            "nahi bhai"
        ]
        results["sec7"] = [ run_single(p) for p in sec7_prompts ]
        save_results(results)

    # 8. HINGLISH QUALITY
    if "sec8" not in results:
        print("\n>>> SECTION 8: HINGLISH QUALITY", flush=True)
        sec8_prompts = [
            "Jarvis mujhe coding me ekdum stuck feel ho raha hai."
        ]
        results["sec8"] = [ run_single(p) for p in sec8_prompts ]
        save_results(results)

    # 9. REPETITION
    if "sec9" not in results:
        print("\n>>> SECTION 9: REPETITION", flush=True)
        p9 = "Jarvis, Python kya hai?"
        results["sec9"] = [ run_single(p9) for _ in range(3) ]
        save_results(results)

    # 11. TECHNICAL CONVERSATION
    if "sec11" not in results:
        print("\n>>> SECTION 11: TECHNICAL CONVERSATION", flush=True)
        sec11_prompts = [
            "Jarvis Provider aur Riverpod me difference kya hai?",
            "mere project me konsa use karu?",
            "agar performance important ho toh?"
        ]
        results["sec11"] = run_session(sec11_prompts)
        save_results(results)

    # 12. MEMORY / CONTEXT
    if "sec12" not in results:
        print("\n>>> SECTION 12: MEMORY / CONTEXT", flush=True)
        sec12_prompts = [
            "My project ka naam Jarvis hai.",
            "Jarvis project me mujhe next kya feature add karna chahiye?"
        ]
        results["sec12"] = run_session(sec12_prompts)
        save_results(results)

    # 13. ERROR / UNKNOWN QUESTION BEHAVIOR
    if "sec13" not in results:
        print("\n>>> SECTION 13: ERROR / UNKNOWN QUESTION BEHAVIOR", flush=True)
        sec13_prompts = [
            "Jarvis, kal Mars par weather kaisa tha?",
            "Jarvis, mujhe samajh nahi aaya."
        ]
        results["sec13"] = [ run_single(p) for p in sec13_prompts ]
        save_results(results)

    # 16. HUMAN-LIKE DIALOGUE TEST
    if "sec16" not in results:
        print("\n>>> SECTION 16: HUMAN-LIKE DIALOGUE TEST", flush=True)
        sec16_prompts = [
            "Jarvis, aaj bahut ajeeb sa lag raha hai.",
            "pata nahi bas mood off hai.",
            "upar se coding bhi nahi ho rahi.",
            "tu bol kya karu?",
            "haan ye sahi hai.",
            "waise kal mujhe website bhi banani hai."
        ]
        results["sec16"] = run_session(sec16_prompts)
        save_results(results)

    print(f"\nALL EVALUATION SECTIONS COMPLETED SUCCESSFULLY. Results saved to {OUT_PATH}", flush=True)

if __name__ == "__main__":
    main()
