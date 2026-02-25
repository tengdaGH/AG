import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    print("Starting script...")
    sys.stdout.flush()
    db_id = '2bf5eb7be7e480df844fedfd68b5ebe3'
    print(f"Querying database {db_id}...")
    sys.stdout.flush()
    try:
        results = await notion.query_database(db_id)
        print(f"Got response with {len(results)} results")
        sys.stdout.flush()
        for res in results:
            props = res.get('properties', {})
            title = ''
            for k,v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text','') for t in v.get('title',[])])
            print(f"{res['id']} | {title}")
            sys.stdout.flush()
    except Exception as e:
        print(f"Error: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
