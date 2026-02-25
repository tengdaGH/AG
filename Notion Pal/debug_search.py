import asyncio, sys, json
from notion_tools import MCPNotionClient

async def main():
    notion = MCPNotionClient()
    # Note: Sorting isn't explicitly in the simple search tool, but we can process results.
    response = await notion.search('')
    results = response.get('results', [])
    # Sort locally if needed, but search usually does this.
    with open('raw_search_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())
