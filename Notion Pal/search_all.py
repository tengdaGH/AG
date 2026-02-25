import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    response = await notion.search('')
    results = response.get('results', [])
    for r in results:
        if r['object'] == 'page':
            title = ''
            props = r.get('properties', {})
            for k,v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text','') for t in v.get('title',[])])
            print(f"{r['id']} | {title} | {r.get('created_time')}")

if __name__ == "__main__":
    asyncio.run(main())
