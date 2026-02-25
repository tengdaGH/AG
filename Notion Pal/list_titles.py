import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    ds_id = '2bf5eb7b-e7e4-803a-a69e-000bc3e9c4c2'
    try:
        # Note: MCP server tools might use different names or wrappers for raw request
        # ds_id query might need specific tool if available, or use the existing query_database
        # for data_source as it's often aliased in MCP.
        results = await notion.query_database(ds_id)
        if not results:
            print("No results found in data source")
        for res in results:
            props = res.get('properties', {})
            title = ''
            for k,v in props.items():
                if v.get('type') == 'title':
                    title = ''.join([t.get('plain_text','') for t in v.get('title',[])])
            print(f"{res['id']} | {title}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
