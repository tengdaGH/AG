import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    db_id = '2bf5eb7be7e480df844fedfd68b5ebe3'
    try:
        results = await notion.query_database(db_id)
        for res in results:
            props = res.get('properties', {})
            title = ''
            for k, v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text', '') for t in v.get('title', [])])
            print(f"{res['id']} | {title} | {res['last_edited_time']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
