import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    response = await notion.search('')
    results = response.get('results', [])
    matches = []
    for res in results:
        if res['object'] == 'page':
            last_edited = res.get('last_edited_time', '')
            title = ''
            props = res.get('properties', {})
            for k, v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text', '') for t in v.get('title', [])])
            # Checking for recent dates (manually updated for the current context if needed)
            if last_edited.startswith('2026-02-24') or last_edited.startswith('2026-02-25'):
                matches.append({'id': res['id'], 'title': title, 'last_edited': last_edited})
    print(json.dumps(matches, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
