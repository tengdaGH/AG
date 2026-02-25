import os
import time
import sys

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', printEnd="\r"):
    if total == 0:
        return
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total: 
        print()

def main():
    total_files = 651
    parsed_dir = "/Users/tengda/Antigravity/IELTS/parsed_v2"
    broken_dir = "/Users/tengda/Antigravity/IELTS/broken"
    
    print("🚀 Monitoring Minimax Batch Processing...\n")
    
    try:
        while True:
            parsed = len([f for f in os.listdir(parsed_dir) if f.endswith('.json')]) if os.path.exists(parsed_dir) else 0
            broken = len([f for f in os.listdir(broken_dir) if f.endswith('.json')]) if os.path.exists(broken_dir) else 0
            
            processed = parsed + broken
            
            status_text = f"[{parsed} parsed, {broken} broken, {total_files - processed} remaining]"
            print_progress_bar(processed, total_files, prefix='Progress:', suffix=status_text, length=40)
            
            if processed >= total_files:
                print("\n✅ Batch Processing Complete!")
                break
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\nStopped monitoring.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Just print once and exit (for non-interactive reporting)
        total_files = 651
        parsed_dir = "/Users/tengda/Antigravity/IELTS/parsed_v2"
        broken_dir = "/Users/tengda/Antigravity/IELTS/broken"
        parsed = len([f for f in os.listdir(parsed_dir) if f.endswith('.json')]) if os.path.exists(parsed_dir) else 0
        broken = len([f for f in os.listdir(broken_dir) if f.endswith('.json')]) if os.path.exists(broken_dir) else 0
        processed = parsed + broken
        print(f"Processed: {processed}/{total_files} | Parsed: {parsed} | Broken: {broken}")
    else:
        main()
