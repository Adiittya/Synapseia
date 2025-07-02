# ------------------------ TOOLS DEFINITION ------------------------

#tool for storing user preference / memories
store_memory_tool = {
    "type": "function",
    "function": {
        "name": "store_memory",
        "description": (
            "Explicitly saves a concise, rephrased memory entry only when the user clearly instructs to remember or store something—"
            "such as preferences, goals, or important facts."
        ),
        "parameters": {
            "type": "object",
            "required": ["text", "tags"],
            "properties": {
                "text": {
                    "type": "string",
                    "description": (
                        "The content to remember, rephrased in clear and grammatically correct English. "
                        "It must be user-initiated, intentional, and directly relevant—NOT auto-summarized from long or general user inputs."
                    )
                },
                "tags": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {
                        "type": "string"
                    },
                    "description": (
                        "A list of exactly two lowercase tags describing the memory topic and category. "
                        "Example: ['goal', 'investing'] or ['preference', 'fmcg']. "
                        "Must be meaningful, short, and validated before storing."
                    )
                }
            }
        }
    }
}


#tool for retriving user preference / memories
search_memory_tool = {
    "type": "function",
    "function": {
        "name": "search_memory",
        "description": (
            "Performs a semantic search over stored memories to retrieve relevant entries "
            "based on the natural language query provided."
        ),
        "parameters": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A natural language search query used to find relevant memories. "
                        "The query should be a clear and concise description of what is being searched."
                    )
                }
            }
        }
    }
}



# Tool to get stock summaries for NSE stocks
stock_fetch_tool = {
    "type": "function",
    "function": {
        "name": "get_stock_summary",
        "description": (
            "Fetch the latest stock quotes and relevant details for NSE stock symbols. "
            "Return ONLY a list of NSE stock symbols ending with '.NS', "
            "without any additional data such as company names or prices. "
            "The symbols can be any valid NSE ticker. "
            "Example output: ['ABC.NS', 'XYZ.NS', 'INFY.NS']"
        ),
        "parameters": {
            "type": "object",
            "required": ["stock_symbols"],
            "properties": {
                "stock_symbols": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^[A-Z0-9]+\\.NS$"
                    },
                    "description": (
                        "A list of valid NSE stock symbols, each ending with '.NS'. "
                        "Symbols may include uppercase letters and digits. "
                        "Example: ['ABC.NS', 'XYZ123.NS']. "
                        "Each symbol must be a separate array element, not a comma-separated string."
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
            "Performs an internet search using the given query and extracts key information "
            "from the top results, including titles, URLs, and summary snippets. "
            "This tool is intended for general information retrieval such as news, weather, "
            "and topics unrelated to stock prices or stock symbol queries.\n\n"
            "IMPORTANT: If the AI does not have sufficient knowledge about a recent event, controversy, "
            "or any topic, it must use this tool to perform a search instead of guessing or providing inaccurate information. "
            "The AI should clearly indicate when it relies on search results."
        ),
        "parameters": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A clear and specific natural language query string for DuckDuckGo search."
                    )
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
            "Use this tool ONLY when the user's request can be fully addressed using internal model knowledge, static context, or summarization — "
            "without the need for any external tools, APIs, scraping, memory access, or stock-related functions. "
            "This includes casual conversations, greetings, small talk, basic factual queries, general knowledge questions, summarization, or providing explanations of user-pasted information. "
            "This tool does not accept any parameters. Use it strictly when the query can be resolved confidently."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
           
        }
    }
}
