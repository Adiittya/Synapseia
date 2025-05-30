import streamlit as st
import json
import logging
from ollama import chat, ChatResponse
from tools.custom_scrapper import search_and_scrape
from tools.custom_yfinance import get_stock_summary
from tools.custom_memories import store_memory, search_memory
from ui_components.memory_manager import memory_manager_dialog
from tool_schema import tools_schema 
from tool_schema import tools_prompt
import ast

# ------------------------ SETUP ------------------------

available_functions = {
    'search_and_scrape': search_and_scrape,
    'skip_tools': lambda: "Answer provided directly by AI without external tools.",
    'get_stock_summary': get_stock_summary,
    'store_memory': store_memory,
    "search_memory": search_memory
}

logging.basicConfig(level=logging.INFO, filename="tool_logs.txt", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

emoji_map = {
    "get_stock_summary": "📈",
    "search_and_scrape": "🌐",
    "skip_tools": "💡",
    "store_memory": "💾",
    "search_memory": "📝"
}

def stream_ollama_response(model: str, messages: list):
    for chunk in chat(model, messages=messages, stream=True):
        if chunk and getattr(chunk, "message", None):
            yield chunk.message.content

# ------------------------ UI SETUP ------------------------

st.set_page_config(page_title="Ollama Stock & Web Assistant", layout="wide")
st.title("Adi'sss Stock & Web Assistant")

if st.button("🗃️ Manage Memory"):
    memory_manager_dialog() 
    
if "query" not in st.session_state:
    st.session_state.query = ""

st.markdown("#### 💡 Quick Suggestions:")
suggestions = [
    "What's the stock price of RELIANCE?",
    "Show me latest news Tata motors.",
    "What's the weather in Delhi?",
    "Compare and do analysis of kotak and hdfc bank with latest price in table format"
]

cols = st.columns(len(suggestions))
for i, suggestion in enumerate(suggestions):
    if cols[i].button(suggestion):
        st.session_state.query = suggestion
        st.rerun()

query = st.text_input("Ask a question:", value=st.session_state.query, key="query")

# ------------------------ MAIN LOGIC ------------------------

if st.button("Ask") and query:
    with st.spinner("Thinking..."):
        initial_messages = [
            {'role': 'system', 'content': tools_prompt.tool_system_prompt},
            {'role': 'user', 'content': query}
        ]

        normal_messages = [
            {'role': 'system', 'content': "You're a helpful AI assistant."},
            {'role': 'user', 'content': query}
        ]

        memory_messages = [
            {
                'role': 'system',
                'content': (
                    "You are a helpful AI assistant. Your role is to remember and refer to what the user has previously told you. "
                    "The context of the conversation may include entries from memory with the role 'tool', and you should use that information "
                    "to respond appropriately."
                )
            },
            {
                'role': 'user',
                'content': query
            }
        ]

        tools = [tools_schema.web_search_tool, tools_schema.skip_tool, tools_schema.stock_fetch_tool, tools_schema.store_memory_tool, tools_schema.search_memory_tool]
        try:
            response: ChatResponse = chat('llama3.2', messages=initial_messages, tools=tools)
            logging.info("Initial chat call successful")
        except Exception as e:
            st.error(f"Chat model failed: {e}")
            st.stop()

        if response.message.tool_calls:
            
            for tool in response.message.tool_calls:
                func_name = tool.function.name
                args = tool.function.arguments if isinstance(tool.function.arguments, dict) else {}

                emoji = emoji_map.get(func_name, "🔧")
                st.info(f"{emoji} AI selected function: `{func_name}` with args {args}")

                # Validate and process inputs with if-else for each tool
                if func_name == "search_and_scrape":
                    if not args.get('query', '').strip():
                        st.warning("Empty query passed to search_and_scrape tool. Skipping.")
                        continue
                    
                elif func_name == "get_stock_summary":
                    stock_symbols = args.get('stock_symbols', '')
                    if isinstance(stock_symbols, list):
                        stock_symbols = ','.join(stock_symbols).strip()
                    elif isinstance(stock_symbols, str):
                        stock_symbols = stock_symbols.strip()
                    else:
                        stock_symbols = ''
                    args['stock_symbols'] = stock_symbols
                    if not stock_symbols:
                        st.warning("No stock symbols detected. Skipping get_stock_summary.")
                        continue
                    
                elif func_name == "store_memory":
                    tags = args.get("tags")
                    if isinstance(tags, str):
                        try:
                            tags = ast.literal_eval(tags)
                            if not isinstance(tags, list):
                                raise ValueError
                            args["tags"] = tags
                        except Exception:
                            st.warning(f"Invalid tags format: {tags}. Skipping store_memory.")
                            continue
                    elif tags is not None and not isinstance(tags, list):
                        st.warning(f"Invalid tags format: {tags}. Skipping store_memory.")
                        continue
                    
                else:
                    # You can add other tool-specific validations here if needed
                    pass

                # Check if function is available
                func = available_functions.get(func_name)
                if not func:
                    st.error(f"Function `{func_name}` not found.")
                    continue

                # REAL-TIME MULTI-STEP STATUS UPDATES 
                try:
                    with st.status(f"{emoji} Calling `{func_name}` and refining answer with AI...") as status:
                        status.write(f"Step 1: Calling `{func_name}` tool...")
                        output = func(**args)
                        status.write("Step 2: Tool call completed.")

                        output_str = json.dumps(output, indent=2) if not isinstance(output, str) else output

                        # Prepare refinement messages based on tool
                        if func_name == "search_memory":
                            refinement_messages = [
                                {
                                    'role': 'system',
                                    'content': (
                                        "You are a helpful AI assistant. Your role is to remember and refer to what the user has previously told you. "
                                        "The context of the conversation may include entries from memory with the role 'tool', and you should use that information "
                                        "to respond appropriately."
                                    )
                                },
                                {
                                    'role': 'user',
                                    'content': query
                                },
                                {
                                    'role': 'tool',
                                    'name': func_name,
                                    'content': output_str
                                }
                            ]

                        elif func_name == "store_memory":
                            # Usually store_memory is a fire-and-forget, so you might just skip refinement or do a simple confirmation
                            refinement_messages = [
                                {
                                    'role': 'system',
                                    'content': "You are a helpful AI assistant."
                                },
                                {
                                    'role': 'user',
                                    'content': f"The user's memory has been updated with: {output_str}"
                                }
                            ]

                        elif func_name == "get_stock_summary":
                            refinement_messages = initial_messages + [{
                                'role': 'tool',
                                'name': func_name,
                                'content': output_str
                            }]

                        elif func_name == "search_and_scrape":
                            refinement_messages = initial_messages + [{
                                'role': 'tool',
                                'name': func_name,
                                'content': output_str
                            }]

                        elif func_name == "skip_tools":
                            # For skip_tools, just append output as a direct AI answer
                            refinement_messages = initial_messages + [{
                                'role': 'tool',
                                'name': func_name,
                                'content': output_str
                            }]

                        else:
                            # Default fallback
                            refinement_messages = initial_messages + [{
                                'role': 'tool',
                                'name': func_name,
                                'content': output_str
                            }]

        
                    # Display tool usage and output outside the status block
                    st.subheader(f"🔧 Tool Used: `{func_name}`")
                    st.code(output_str, language="json")

                    st.subheader("💬 Final Answer:")
                    st.write_stream(stream_ollama_response("llama3.2", refinement_messages))

                except Exception as e:
                    st.error(f"Error executing `{func_name}`: {e}")
                    continue