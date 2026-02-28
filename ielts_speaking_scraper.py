import requests
import json
import os
from bs4 import BeautifulSoup

def fetch_ieltsbro_part2_3():
    print("Fetching Part 2 & 3 from ieltsbro API...")
    url = "https://hcp-server.ieltsbro.com/hcp/qsBank/oralTopic/listV3"
    headers = {
        "Content-Type": "application/json",
        "Source": "2",
        "Origin": "https://www.ieltsbro.com",
        "Referer": "https://www.ieltsbro.com/"
    }
    data = {"oralTopCatalog": "all", "part": 1}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        res_json = response.json()
        if res_json.get("status") == 0:
            topics = res_json["content"]["list"]
            parsed_topics = []
            for t in topics:
                parsed_topics.append({
                    "topic_id": t["oralTopicId"],
                    "title": t["oralTopicName"],
                    "part": "Part 2 & 3",
                    "cue_card": t["oralQuestion"],
                    "validity": t["timeTag"],
                    "source": "ieltsbro"
                })
            return parsed_topics
        else:
            print(f"API Error: {res_json.get('message')}")
            return []
    except Exception as e:
        print(f"Error fetching from ieltsbro: {e}")
        return []

def scrape_laokaoya_part1():
    print("Scraping Part 1 from laokaoya.com...")
    url = "https://www.laokaoya.com/60261.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find('div', class_='content')
        if not content_div:
            content_div = soup.find('article') or soup.find('div', id='content')
            
        if not content_div:
            print("Could not find content div on laokaoya.")
            return []

        topics = []
        current_topic = None
        
        # New Logic:
        # 1. p containing an 'a' tag is often a topic (e.g. "Work 工作")
        # 2. Other p tags containing '?' are questions.
        
        for element in content_div.find_all('p'):
            text = element.get_text(strip=True)
            if not text:
                continue
            
            # Detect if it's a topic: contains a link and is usually bolded/italicized
            # Or matches a known pattern like "Work 工作"
            a_tag = element.find('a')
            if a_tag and len(text) < 100: # Topic titles are usually short
                if current_topic and current_topic["questions"]:
                    topics.append(current_topic)
                
                current_topic = {
                    "title": text,
                    "part": "Part 1",
                    "questions": [],
                    "source": "laokaoya"
                }
            elif current_topic:
                # Add question if it ends with ? or looks like a question
                if '?' in text or text.endswith('?'):
                    # Sometimes multiple questions are in one p tag
                    if '?' in text[:-1]: # Check for internal ?
                        # Split by ? but keep the ?
                        parts = [p.strip() + '?' for p in text.split('?') if p.strip()]
                        current_topic["questions"].extend(parts)
                    else:
                        current_topic["questions"].append(text)
        
        if current_topic and current_topic["questions"]:
            topics.append(current_topic)
            
        return topics
    except Exception as e:
        print(f"Error scraping laokaoya: {e}")
        return []

def main():
    os.makedirs("output/ielts_speaking", exist_ok=True)
    
    p2_data = fetch_ieltsbro_part2_3()
    p1_data = scrape_laokaoya_part1()
    
    full_bank = {
        "season": "2026年1-4月",
        "part_1": p1_data,
        "part_2_3": p2_data
    }
    
    output_path = "output/ielts_speaking/2026_jan_apr_bank.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_bank, f, ensure_ascii=False, indent=2)
    
    print(f"\nSuccessfully scraped {len(p1_data)} Part 1 topics and {len(p2_data)} Part 2/3 topics.")
    print(f"Data saved to {output_path}")

if __name__ == "__main__":
    main()
