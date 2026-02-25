import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    try:
        db_id = '2bf5eb7be7e480df844fedfd68b5ebe3'
        results = await notion.query_database(db_id)
        matches = []
        for res in results:
            title = ''
            props = res.get('properties', {})
            for k, v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text', '') for t in v.get('title', [])])
            matches.append({'id': res['id'], 'title': title, 'last_edited_time': res.get('last_edited_time')})
        # Sort by last_edited_time descending
        matches.sort(key=lambda x: x.get('last_edited_time', ''), reverse=True)
        with open('db_items.json', 'w') as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)
    except Exception as e:
        with open('error.txt', 'w') as f:
            f.write(str(e))

if __name__ == "__main__":
    asyncio.run(main())
