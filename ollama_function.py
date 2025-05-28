from ollama import ChatResponse, chat
from custom_scrapper import search_and_scrape
from custom_yfinance import get_stock_summary
import json

query = input("Ask quesiton")

# Real web search tool definition
web_search_tool = {
    "type": "function",
    "function": {
        "name": "search_and_scrape",
        "description": (
            "Search the internet using a query and scrape the content of the top results, "
            "returning their title, URL, and snippet content."
        ),
        "parameters": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string to perform the DuckDuckGo search and scrape results from."
                },
            }
        }
    }
}
stock_fetch_tool = {
    "type": "function",
    "function": {
        "name": "get_stock_summary",
        "description": (
            "Get the latest stock quotes for one or more NSE stock symbols. "
            "The symbols must be returned ONLY as a list of strings ending with '.NS' "
            "and WITHOUT any extra information or company names. "
            "Example output: [\"RELIANCE.NS\", \"TATASTEEL.NS\", \"INFY.NS\"]"
        ),
        "parameters": {
            "type": "object",
            "required": ["stock_symbols"],
            "properties": {
                "stock_symbols": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^[A-Z]+\\.NS$"
                    },
                    "description": (
                        "A list of NSE stock symbols ending with '.NS'. "
                        "Each item must be a string like 'RELIANCE.NS', 'TATASTEEL.NS', etc. "
                        "DO NOT use a single comma-separated string."
                    )
                }
            }
        }
    }
}


# Dummy skip tool — used when AI can answer without external data
skip_tool = {
    "type": "function",
    "function": {
        "name": "skip_tools",
        "description": (
            "A dummy tool used to indicate that the AI can answer this question directly "
            "without needing to call any external data source or web search."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}

# System prompt instructing the AI about when to use each tool
tool_system_prompt = (
    "You are a helpful assistant with access to three tools:\n\n"
    "1. `get_stock_summary`: Use this tool to get the latest stock quotes, prices, and detailed stock info for any NSE stock symbols. "
    "You must return the `stock_symbols` parameter as a list of strings. Do not return a string, JSON string, or single comma-separated string. "
    "Example: ['TATAMOTORS.NS', 'RELIANCE.NS']\n\n"
    "2. `search_and_scrape`: Use this tool ONLY for fresh web searches on topics unrelated to stocks, such as weather, news, or general information.\n\n"
    "3. `skip_tools`: Use this tool only when the user asks general questions that can be answered without fresh data or stock info.\n\n"
    "RULES:\n"
    "- ALWAYS prefer `get_stock_summary` for stock-related queries.\n"
    "- ALWAYS return `stock_symbols` as a Python-style list of strings. Example: ['RELIANCE.NS'] — never as a single string.\n"
    "- Use `search_and_scrape` ONLY if the query is unrelated to stocks and requires fresh web data.\n"
    "- Use `skip_tools` ONLY if the question can be answered with general knowledge.\n\n"
    "Examples:\n"
    "- 'Show me the latest Tata Motors stock price.' → use `get_stock_summary` with stock_symbols=['TATAMOTORS.NS']\n"
    "- 'What's the weather in New York?' → use `search_and_scrape`.\n"
    "- 'Who won the World Cup in 2018?' → use `skip_tools`.\n"
)



inital_messages = [
    {'role': 'system', 'content': tool_system_prompt},
    {'role': 'user', 'content': query}  # Example user query; change as needed
]

normal_messages= [
    {'role': 'system', 'content': "You're an helpful Ai assistant"},
    {'role': 'user', 'content': query}
]

# Map function names to actual implementations
available_functions = {
    'search_and_scrape': search_and_scrape,
    # For skip_tools, no actual external call, just return the AI's own answer
    'skip_tools': lambda: "Answer provided directly by AI without external tools.",
    'get_stock_summary':get_stock_summary
}

tools = [web_search_tool, skip_tool, stock_fetch_tool]

# Initial call to chat
response: ChatResponse = chat(
    'llama3.2',
    messages=inital_messages,
    tools=tools,
)

if response.message.tool_calls:
    for tool in response.message.tool_calls:
        func_name = tool.function.name
        args = tool.function.arguments if isinstance(tool.function.arguments, dict) else {}

        if func_name == "skip_tools":
            print("Using skip_tools: answering without external search.")
        
            # user_last_message = next(m for m in inital_messages if m['role'] == 'user')
            # inital_messages.append({'role': 'user', 'content': user_last_message['content']})

            final_response = chat('llama3.2', messages= normal_messages)
            print('Final response:', final_response.message.content)
            continue

        # For real tools, check query is not empty
        if func_name == "search_and_scrape" and not args.get('query', '').strip():
            print("Skipping search_and_scrape call due to empty query.")
            continue

        if func_name == "get_stock_summary":
            stock_symbols = args.get('stock_symbols', '')

            # If stock_symbols is a list, convert to comma-separated string
            if isinstance(stock_symbols, list):
                stock_symbols = ','.join(stock_symbols).strip()
            elif isinstance(stock_symbols, str):
                stock_symbols = stock_symbols.strip()
            else:
                stock_symbols = ''

            # Update args with cleaned stock_symbols
            args['stock_symbols'] = stock_symbols

            # Skip calling function if no stock_symbols
            if not stock_symbols:
                print("Skipping get_stock_summary call due to empty stock_symbols.")
                continue

        func = available_functions.get(func_name)
        if func:
            print(f"Calling function: {func_name} with args: {args}")
            output = func(**args)
            print("Function output:", output)
            
                
            if not isinstance(output, str):
                output_str = json.dumps(output, indent=2)
            else:
                output_str = output

            # Append assistant message and tool output for context
            inital_messages.append(response.message)
            inital_messages.append({
                'role': 'tool',
                'name': func_name,
                'content': output_str
            })

            # Get final assistant response after tool call
            final_response = chat('llama3.2', messages=inital_messages)
            print('Final response:', final_response.message.content)
        else:
            print(f"Function {func_name} not found.")
else:
    # If no tool call, just print assistant message
    print('No tool calls returned from model.')
    print('Assistant response:', response.message.content)
