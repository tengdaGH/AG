import os
import json
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class MCPNotionClient:
    def __init__(self, token=None):
        self.token = token or os.getenv("NOTION_TOKEN")
        if not self.token:
            # For this specific refactor, we still need a token to pass to the MCP server
            # unless the MCP server is already running as a persistent service.
            # But here we start it via stdio.
            raise ValueError("NOTION_TOKEN not found in environment variables.")
        
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={**os.environ, "NOTION_TOKEN": self.token}
        )

    async def _call_tool(self, tool_name, arguments):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool(tool_name, arguments)
                if getattr(response, "isError", False):
                    raise Exception(f"MCP Tool Error ({tool_name}): {response.content}")
                
                # The response content is a list of content objects.
                # Use the first one and parse its text as JSON.
                if not response.content:
                    return None
                return json.loads(response.content[0].text)

    async def get_page(self, page_id):
        """Retrieve a page by ID."""
        return await self._call_tool("API-retrieve-a-page", {"page_id": page_id})

    async def search(self, query):
        """Search for pages or databases."""
        return await self._call_tool("API-post-search", {"query": query})

    async def get_block_children(self, block_id):
        """Retrieve children blocks of a page or block."""
        return await self._call_tool("API-get-block-children", {"block_id": block_id})

    async def get_page_text(self, block_id):
        """Retrieve all text content from a page, including nested blocks."""
        response = await self.get_block_children(block_id)
        blocks = response.get("results", [])
        return await self.parse_blocks(blocks)

    async def parse_blocks(self, blocks):
        """Parse Notion blocks into a clean text string, recursively."""
        text_content = []
        for block in blocks:
            block_type = block.get("type")
            text = ""
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "quote"]:
                rich_text = block.get(block_type, {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
            elif block_type == "to_do":
                rich_text = block.get("to_do", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                checked = "[x]" if block.get("to_do", {}).get("checked") else "[ ]"
                text = f"{checked} {text}"
            elif block_type == "callout":
                rich_text = block.get("callout", {}).get("rich_text", [])
                text = "> " + "".join([t.get("plain_text", "") for t in rich_text])
            
            if text:
                text_content.append(text)
            
            # Recursive check
            if block.get("has_children"):
                child_text = await self.get_page_text(block["id"])
                if child_text:
                    indented_child = "\n".join(["  " + line for line in child_text.split("\n")])
                    text_content.append(indented_child)
        
        return "\n".join(text_content)

    async def update_page_properties(self, page_id, properties):
        """Update properties of a page."""
        return await self._call_tool("API-patch-page", {"page_id": page_id, "properties": properties})

    async def query_database(self, database_id, filter=None):
        """Query a database for its items."""
        args = {"data_source_id": database_id}
        if filter:
            args["filter"] = filter
        response = await self._call_tool("API-query-data-source", args)
        return response.get("results", [])

    async def delete_block(self, block_id):
        """Delete a block (or page/database)."""
        return await self._call_tool("API-delete-a-block", {"block_id": block_id})

    async def append_block_children(self, block_id, children):
        """Append blocks to a page or parent block."""
        return await self._call_tool("API-patch-block-children", {"block_id": block_id, "children": children})

    async def replace_page_content(self, page_id, md_text):
        """Delete all existing blocks and replace with new content from markdown."""
        response = await self.get_block_children(page_id)
        results = response.get("results", [])
        for block in results:
            try:
                await self.delete_block(block["id"])
            except Exception as e:
                print(f"Warning: Could not delete block {block['id']}: {e}")
        
        lines = md_text.split("\n")
        new_blocks = []
        for line in lines:
            if not line.strip():
                continue
            
            if line.startswith("# "):
                type = "heading_1"
                text = line[2:]
            elif line.startswith("## "):
                type = "heading_2"
                text = line[3:]
            elif line.startswith("### "):
                type = "heading_3"
                text = line[4:]
            elif line.startswith("- ") or line.startswith("* "):
                type = "bulleted_list_item"
                text = line[2:]
            elif line.startswith("> "):
                type = "quote"
                text = line[2:]
            else:
                type = "paragraph"
                text = line
            
            chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
            for chunk in chunks:
                new_blocks.append({
                    "object": "block",
                    "type": type,
                    type: {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
        
        for i in range(0, len(new_blocks), 100):
            await self.append_block_children(page_id, new_blocks[i:i+100])

async def main():
    if len(sys.argv) < 2:
        return

    # Use the verified token directly for testing if you want to skip .env
    # token = "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"
    # notion = MCPNotionClient(token=token)
    
    notion = MCPNotionClient()
    command = sys.argv[1]
    
    if command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        response = await notion.search(query)
        results = response.get("results", [])
        output = []
        for res in results:
            title = "Untitled"
            if res["object"] == "page":
                properties = res.get("properties", {})
                for prop_name, prop_val in properties.items():
                    if prop_val.get("type") == "title":
                        title_list = prop_val.get("title", [])
                        title = "".join([t.get("plain_text", "") for t in title_list])
            elif res["object"] == "database":
                title_list = res.get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_list])
            
            output.append({
                "id": res["id"],
                "object": res["object"],
                "title": title
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif command == "get":
        page_id = sys.argv[2]
        print(await notion.get_page_text(page_id))
    elif command == "query":
        db_id = sys.argv[2]
        filter_json = sys.argv[3] if len(sys.argv) > 3 else None
        notion_filter = json.loads(filter_json) if filter_json else None
        results = await notion.query_database(db_id, filter=notion_filter)
        output = []
        for res in results:
            title = "Untitled"
            properties = res.get("properties", {})
            for prop_name, prop_val in properties.items():
                if prop_val.get("type") == "title":
                    title_list = prop_val.get("title", [])
                    title = "".join([t.get("plain_text", "") for t in title_list])
            output.append({
                "id": res["id"],
                "title": title
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif command == "update-props":
        page_id = sys.argv[2]
        props_json = sys.argv[3]
        props = json.loads(props_json)
        print(json.dumps(await notion.update_page_properties(page_id, props)))
    elif command == "replace-content":
        page_id = sys.argv[2]
        file_path = sys.argv[3]
        with open(file_path, "r") as f:
            content = f.read()
        await notion.replace_page_content(page_id, content)
        print(json.dumps({"status": "success"}))

if __name__ == "__main__":
    asyncio.run(main())
