import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    response = await notion.search('')
    results = response.get('results', [])
    for r in results:
        title = 'Untitled'
        if r['object'] == 'page':
            props = r.get('properties', {})
            for k, v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text','') for t in v.get('title',[])])
        elif r['object'] == 'database':
            title = ''.join([t.get('plain_text','') for t in r.get('title', [])])
        print(f"{r.get('id')} | {title} | {r.get('last_edited_time')}")

if __name__ == "__main__":
    asyncio.run(main())
