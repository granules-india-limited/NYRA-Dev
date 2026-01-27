import asyncio
from typing import Dict, Any
from core.utils.logger import logger


class MCPToolExecutor:

    def __init__(self, mcp_config: Dict[str, Any]):
        self.mcp_config = mcp_config
        custom_type = mcp_config.get("customType", mcp_config.get("type", "standard"))
        self.server_type = custom_type
        
        self.tool_info = {
            'custom_type': custom_type,
            'custom_config': mcp_config.get('config', {}),
            'original_name': None
        }
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        try:
            self.tool_info['original_name'] = tool_name
            
            if self.server_type == "composio":
                return await self._execute_composio_tool(tool_name, args)
            elif self.server_type == "sse":
                return await self._execute_sse_tool(tool_name, args)
            elif self.server_type == "http":
                return await self._execute_http_tool(tool_name, args)
            elif self.server_type == "json":
                return await self._execute_json_tool(tool_name, args)
            else:
                return await self._execute_http_tool(tool_name, args)
                
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] Failed to execute {tool_name}: {e}")
            raise
    
    async def _execute_composio_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from core.composio_integration.composio_profile_service import ComposioProfileService
        from core.services.supabase import DBConnection
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession
        from core.agentpress.tool import ToolResult
        import os
        
        # Check if COMPOSIO_API_KEY is configured
        composio_api_key = os.getenv("COMPOSIO_API_KEY")
        if not composio_api_key:
            error_msg = "COMPOSIO_API_KEY is not configured. Please add it to backend/.env to enable Composio tools."
            logger.error(f"❌ [MCP EXEC] {error_msg}")
            return ToolResult(
                success=False,
                output=error_msg
            )
        
        custom_config = self.tool_info['custom_config']
        profile_id = custom_config.get('profile_id')
        
        if not profile_id:
            error_msg = "Missing profile_id for Composio tool. The integration may not be properly configured."
            logger.error(f"❌ [MCP EXEC] {error_msg}")
            return ToolResult(
                success=False,
                output=error_msg
            )
        
        try:
            db = DBConnection()
            profile_service = ComposioProfileService(db)
            mcp_url = await profile_service.get_mcp_url_for_runtime(profile_id)
            
            if not mcp_url:
                error_msg = f"Could not retrieve MCP URL for Composio profile {profile_id}. The integration may need to be reconnected."
                logger.error(f"❌ [MCP EXEC] {error_msg}")
                return ToolResult(
                    success=False,
                    output=error_msg
                )
            
            logger.debug(f"⚡ [MCP EXEC] Executing {tool_name} via Composio (profile: {profile_id})")
            
            async with streamablehttp_client(mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=args)
                    content = self._extract_result_content(result)
                    
                    logger.debug(f"✅ [MCP EXEC] Composio tool {tool_name} executed successfully")
                    # Preserve JSON structure - convert to formatted JSON string for LLM
                    import json
                    if isinstance(content, (dict, list)):
                        # Convert to nicely formatted JSON string for LLM consumption
                        output = json.dumps(content, ensure_ascii=False, indent=2)
                        logger.debug(f"📦 [MCP EXEC] Extracted structured data: {type(content).__name__} with {len(str(content))} chars")
                        # Log a preview of the data structure
                        if isinstance(content, dict):
                            logger.debug(f"📦 [MCP EXEC] Data keys: {list(content.keys())[:10]}")
                            if 'messages' in content:
                                logger.debug(f"📦 [MCP EXEC] Found {len(content.get('messages', []))} messages in data")
                    else:
                        output = str(content)
                        logger.debug(f"📦 [MCP EXEC] Extracted text content: {len(output)} chars")
                    return ToolResult(success=True, output=output)
            
        except ValueError as e:
            # Handle missing API key or configuration errors
            error_msg = f"Composio configuration error: {str(e)}"
            logger.error(f"❌ [MCP EXEC] {error_msg}")
            return ToolResult(
                success=False,
                output=error_msg
            )
        except Exception as e:
            error_msg = f"Failed to execute Composio tool '{tool_name}': {str(e)}"
            logger.error(f"❌ [MCP EXEC] {error_msg}", exc_info=True)
            return ToolResult(
                success=False,
                output=error_msg
            )
    
    async def _execute_sse_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from mcp.client.sse import sse_client
        from mcp import ClientSession
        from core.agentpress.tool import ToolResult
        
        custom_config = self.tool_info['custom_config']
        url = custom_config.get('url')
        
        if not url:
            return ToolResult(
                success=False,
                output="Missing 'url' in SSE MCP config"
            )
        
        headers = custom_config.get('headers', {})
        
        try:
            async with asyncio.timeout(30):
                try:
                    async with sse_client(url, headers=headers) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(tool_name, arguments=args)
                            content = self._extract_result_content(result)
                            logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via SSE")
                            return ToolResult(success=True, output=str(content))
                except TypeError as e:
                    if "unexpected keyword argument" in str(e):
                        async with sse_client(url) as (read, write):
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                result = await session.call_tool(tool_name, arguments=args)
                                content = self._extract_result_content(result)
                                logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via SSE (no headers)")
                                return ToolResult(success=True, output=str(content))
                    else:
                        raise
        except asyncio.TimeoutError:
            logger.error(f"❌ [MCP EXEC] SSE execution timeout for {tool_name}")
            return ToolResult(
                success=False,
                output=f"SSE tool execution timeout after 30 seconds"
            )
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] SSE execution failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                output=f"Failed to execute SSE tool: {str(e)}"
            )
    
    async def _execute_http_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession
        from core.agentpress.tool import ToolResult
        
        custom_config = self.tool_info['custom_config']
        url = custom_config.get('url')
        
        if not url:
            return ToolResult(
                success=False,
                output="Missing 'url' in HTTP MCP config"
            )
        
        try:
            async with asyncio.timeout(30):
                async with streamablehttp_client(url) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=args)
                        content = self._extract_result_content(result)
                        logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via HTTP")
                        return ToolResult(success=True, output=str(content))
        except asyncio.TimeoutError:
            logger.error(f"❌ [MCP EXEC] HTTP execution timeout for {tool_name}")
            return ToolResult(
                success=False,
                output=f"HTTP tool execution timeout after 30 seconds"
            )
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] HTTP execution failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                output=f"Failed to execute HTTP tool: {str(e)}"
            )
    
    async def _execute_json_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from core.agentpress.tool import ToolResult
        
        custom_config = self.tool_info['custom_config']
        command = custom_config.get('command')
        
        if not command:
            return ToolResult(
                success=False,
                output="Missing 'command' in JSON/stdio MCP config"
            )
        
        try:
            server_params = StdioServerParameters(
                command=command,
                args=custom_config.get("args", []),
                env=custom_config.get("env", {})
            )
            
            async with asyncio.timeout(30):
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=args)
                        content = self._extract_result_content(result)
                        logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via JSON/stdio")
                        return ToolResult(success=True, output=str(content))
        except asyncio.TimeoutError:
            logger.error(f"❌ [MCP EXEC] JSON/stdio execution timeout for {tool_name}")
            return ToolResult(
                success=False,
                output=f"JSON/stdio tool execution timeout after 30 seconds"
            )
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] JSON/stdio execution failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                output=f"Failed to execute JSON/stdio tool: {str(e)}"
            )
    
    def _extract_result_content(self, result: Any) -> Any:
        """Extract content from MCP tool result, preserving JSON structure when possible."""
        import json
        
        # If result has content attribute (MCP standard format)
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, list):
                # Handle list of content items
                text_parts = []
                json_parts = []
                for item in content:
                    if hasattr(item, 'text'):
                        text = item.text
                        # Try to parse as JSON (Composio returns JSON strings)
                        try:
                            parsed = json.loads(text)
                            # Extract 'data' field from Composio responses
                            if isinstance(parsed, dict) and 'data' in parsed:
                                json_parts.append(parsed['data'])
                            else:
                                json_parts.append(parsed)
                        except (json.JSONDecodeError, TypeError):
                            text_parts.append(text)
                    else:
                        # Try to preserve structure if it's already a dict/list
                        if isinstance(item, (dict, list)):
                            json_parts.append(item)
                        else:
                            text_parts.append(str(item))
                
                # If we have JSON parts, return them as structured data
                if json_parts:
                    # If single JSON object, return it directly; otherwise return list
                    return json_parts[0] if len(json_parts) == 1 else json_parts
                # Otherwise return joined text
                return "\n".join(text_parts) if text_parts else ""
            elif hasattr(content, 'text'):
                text = content.text
                # Try to parse as JSON (Composio returns JSON strings)
                try:
                    parsed = json.loads(text)
                    # If Composio response format, extract the 'data' field
                    if isinstance(parsed, dict):
                        if 'data' in parsed:
                            logger.debug(f"📦 [MCP EXEC] Extracted 'data' field from Composio response")
                            return parsed['data']
                        # Check for nested structure
                        if 'successful' in parsed and 'data' in parsed:
                            logger.debug(f"📦 [MCP EXEC] Found Composio response structure, extracting 'data'")
                            return parsed['data']
                    return parsed
                except (json.JSONDecodeError, TypeError):
                    return text
            elif isinstance(content, (dict, list)):
                # Already structured, return as-is
                return content
            else:
                return str(content)
        elif isinstance(result, dict):
            # If it's already a dict, try to extract meaningful data
            # Composio returns: {"successful": true, "data": {...}, "error": null, ...}
            if 'data' in result:
                logger.debug(f"📦 [MCP EXEC] Extracting 'data' field from dict result")
                return result['data']  # Return the actual data, not the wrapper
            elif 'content' in result:
                content = result['content']
                # Try to parse if it's a JSON string
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        # Extract 'data' if it's a Composio response
                        if isinstance(parsed, dict) and 'data' in parsed:
                            logger.debug(f"📦 [MCP EXEC] Extracted 'data' from parsed content")
                            return parsed['data']
                        return parsed
                    except (json.JSONDecodeError, TypeError):
                        return content
                # If content is already a dict, check for 'data' field
                if isinstance(content, dict) and 'data' in content:
                    logger.debug(f"📦 [MCP EXEC] Extracted 'data' from content dict")
                    return content['data']
                return content
            else:
                # Return the whole dict as structured data
                return result
        elif isinstance(result, (list, str)):
            # Lists and strings as-is
            return result
        else:
            # Fallback to string
            return str(result)