# ------------------------ TOOLS DEFINITION ------------------------

#tool for storing user preference / memories
store_memory_tool = {
    "type": "function",
    "function": {
        "name": "store_memory",
        "description": (
            "Stores memory text into the database with exactly two tags as a list of strings, "
            "like ['color', 'red']."
        ),
        "parameters": {
            "type": "object",
            "required": ["text", "tags"],
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The memory content text to store."
                },
                "tags": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {
                        "type": "string"
                    },
                    "description": "List of exactly two tag strings, e.g., ['color', 'red']"
                }
            }
        }
    }
}

#tool for retriving user preference / memories
search_memory_tool= {
    "type": "function",
    "function": {
        "name": "search_memory",
        "description": "Searches stored memories semantically.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The natural language search query.",
                }
            },
            "required": ["query"]
        }
    }
}



# Tool to get stock summaries for NSE stocks
stock_fetch_tool = {
    "type": "function",
    "function": {
        "name": "get_stock_summary",
        "description": (
            "Fetch the latest stock quotes and details for NSE stock symbols. "
            "Return stock symbols ONLY as a list of strings ending with '.NS', "
            "without any extra info or names. "
            "Example: ['RELIANCE.NS', 'TATASTEEL.NS', 'INFY.NS']"
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
                        "List of NSE stock symbols ending with '.NS'. "
                        "Example: ['RELIANCE.NS', 'TATASTEEL.NS'] "
                        "Do NOT pass a single comma-separated string."
                    )
                }
            }
        }
    }
}

# Tool to perform web search and scrape content (for non-stock queries)
web_search_tool = {
    "type": "function",
    "function": {
        "name": "search_and_scrape",
        "description": (
            "Search the internet with a query and scrape top results' titles, URLs, and snippets. "
            "Use for general info, news, weather, or topics unrelated to stocks."
        ),
        "parameters": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string for DuckDuckGo search and scraping."
                }
            }
        }
    }
}

# Dummy tool for when no external data is needed to answer
skip_tool = {
    "type": "function",
    "function": {
        "name": "skip_tools",
        "description": (
            "Indicate that the question can be answered using general knowledge without calling any external tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}
