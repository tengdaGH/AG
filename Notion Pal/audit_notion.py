import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("NOTION_TOKEN")
    if not token:
        print("Error: NOTION_TOKEN not found in .env")
        return

    params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={**os.environ, "NOTION_TOKEN": token}
    )
    
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                for t in tools.tools:
                    print(f"Tool: {t.name}")
                    print(f"  Description: {t.description}")
                    print(f"  Input Schema: {t.inputSchema}")
                    print("-" * 20)
    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    asyncio.run(main())
