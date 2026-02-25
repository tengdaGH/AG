import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    response = await notion.search('')
    results = response.get('results', [])
    items = []
    for res in results:
        if res['object'] == 'page':
            title = ''
            props = res.get('properties', {})
            for k, v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text', '') for t in v.get('title', [])])
            items.append({'id': res['id'], 'title': title, 'created_time': res.get('created_time')})
    # Sort by created_time descending
    items.sort(key=lambda x: x['created_time'], reverse=True)
    print(json.dumps(items[:20], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
