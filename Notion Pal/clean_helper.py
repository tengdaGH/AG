import re
import sys

def clean_haoyu_high_fidelity(text):
    # Fix specific errors only
    errors = {
        "Gramovie": "Grammarly",
        "Mukov": "Mock-up",
        "Q-U-A-R-E-L": "QUARREL",
        "Frictions Corals": "Quarrel",
        "stret的": "strategies",
        "Stringes": "strategies",
        "housey": "healthy",
        "b嘴": "busy",
        "moh": "more"
    }
    for old, new in errors.items():
        text = text.replace(old, new)
    
    # Only remove excessive repetitions (3+ identical words/phrases)
    text = re.sub(r'(那个|然后|就是|那|嗯|呃|对|对吧){2,}', r'\1', text)
    
    return text

def clean_xiaokai_high_fidelity(text):
    # Fix specific patterns
    text = re.sub(r'(那个|然后|就是|对吧|明白了吧|明白了){2,}', r'\1', text)
    return text

if __name__ == "__main__":
    file_path = sys.argv[1]
    student = sys.argv[2]
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    if student == "haoyu":
        print(clean_haoyu_high_fidelity(content))
    else:
        print(clean_xiaokai_high_fidelity(content))
