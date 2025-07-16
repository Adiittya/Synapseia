import streamlit as st
import json
import logging
from ollama import chat, ChatResponse
from tools.custom_scrapper import search_and_scrape
from tools.custom_yfinance import get_stock_summary
from tools.custom_memories import store_memory, search_memory
from tools.custom_github import analyze_github_repo
from tools.custom_github import generate_repo_page
from ui_components.memory_manager_modal import memory_manager_dialog
from tool_schema import tools_schema 
from tool_schema import tools_prompt
import ast
from ui_components.sources_modal import show_sources
import streamlit.components.v1 as components
from ui_components.stock_graph_generation import generate_multiple_charts

# ------------------------ SETUP ------------------------

available_functions = { 
    'search_and_scrape': search_and_scrape,
    'skip_tools': lambda: "Answer provided directly by AI without external tools.",
    'get_stock_summary': get_stock_summary,
    'store_memory': store_memory,
    "search_memory": search_memory,
    "analyze_github_repo": analyze_github_repo
}

logging.basicConfig(level=logging.INFO, filename="tool_logs.txt", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

emoji_map = {
    "get_stock_summary": "📈",
    "search_and_scrape": "🌐",
    "skip_tools": "💡",
    "store_memory": "💾",
    "search_memory": "📝",
    "analyze_github_repo": "🧑‍💻"
}

agent_name_map = {
    "search_and_scrape": "Scraping Agent 🌐",
    "get_stock_summary": "Stock Agent 📈",
    "store_memory": "Memory Agent 💾",
    "search_memory": "Memory Agent 📝",
    "skip_tools": "Direct Answer 💡",
    "analyze_github_repo": "GitHub Agent 🧑‍💻"
}


def stream_ollama_response(model: str, messages: list):
    for chunk in chat(model, messages=messages, stream=True):
        if chunk and getattr(chunk, "message", None):
            st.session_state.ai_answer += chunk.message.content
            yield chunk.message.content

# ------------------------ UI SETUP ------------------------


st.set_page_config(page_title="SYNAPSEIA", layout="wide")
# ------------------------ DECLARING SESSIONS ------------------------
if "query" not in st.session_state:
    st.session_state.query = ""
if "search_and_scrape_called" not in st.session_state:
    st.session_state.search_and_scrape_called = False
if "output" not in st.session_state:
    st.session_state.output = None
if "func_name" not in st.session_state:
    st.session_state.func_name = None
if "ai_answer" not in st.session_state:
    st.session_state.ai_answer = ""  # to store final AI answer text
if "sources_favicon" not in st.session_state:
    st.session_state.sources_favicon = ""
if "ask_now" not in st.session_state:
    st.session_state.ask_now = False
if "show_sources_clicked" not in st.session_state:
    st.session_state.show_sources_clicked = False
if "last_query_ran" not in st.session_state:
    st.session_state.last_query_ran = ""
if "charts_generated" not in st.session_state:
    st.session_state.charts_generated = False
if "chart_symbols" not in st.session_state:
    st.session_state.chart_symbols = []
if "tool_expander" not in st.session_state:
    st.session_state.charts_generated = False
    
if "show_github_analysis" not in st.session_state:
    st.session_state.show_github_analysis = False
if "github_repo_url" not in st.session_state:
    st.session_state.github_repo_url = ""

    
    
    
    
# ------------------------ UI CONFIG ------------------------

st.title("Project SYNAPSEIA")
st.markdown("Stock & Web Assistant")

col1, col2 = st.columns([1, 5])
if col1.button("🗃️ Manage Memory"):
    memory_output = memory_manager_dialog()
    print(memory_output)

st.markdown("---")

# ------------------------ SUGGESTIONS ------------------------

st.markdown("#### 💡 Quick Prompts")
hide_streamlit_style = """
    <style>
    /* Hide the top-right menu (three dots) */
    #MainMenu {visibility: hidden;}

    /* Hide the "running man" spinner and the Stop button */
    .stToolbar {visibility: hidden;}
    </style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)
suggestions = [
    "What stock price of RELIANCE and TATAMOTORS?",
    "Show me latest news of tata motors.",
    "What's the current weather in Mumbai?",
    "Spill the latest tea about Wizard liz controversy 😋"
]

cols = st.columns(len(suggestions))
for i, suggestion in enumerate(suggestions):
    if cols[i].button(suggestion):
        st.session_state.query = suggestion
        st.session_state.ask_now = True 

# ------------------------ INPUT QUERY ------------------------
    
query = st.text_area(
    "📝 Ask a question:",
    value=st.session_state.query,
    height=68,  # adjust to desired size
    key="query"
)

print(query)
output_rendered = False

# ------------------------ MAIN LOGIC ------------------------

ask_button_pressed = st.button("Ask")

if (ask_button_pressed or st.session_state.get("ask_now")) and query and query != st.session_state.last_query_ran:

    st.session_state.ask_now = False  # Reset after use
    st.session_state.ai_answer = ""
    st.session_state.output = None
    st.session_state.func_name = None
    st.session_state.search_and_scrape_called = False
    st.session_state.last_query_ran = query
    st.session_state.show_github_analysis = False
    st.session_state.github_repo_url = ""

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

        tools = [tools_schema.web_search_tool, tools_schema.skip_tool, tools_schema.stock_fetch_tool, tools_schema.store_memory_tool, tools_schema.search_memory_tool, tools_schema.github_repo_tool]
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
                # st.info(f"{emoji} AI selected function: `{func_name}` with args {args}")
# -------------------------- Validate and process inputs with if-else for each tool-----------------------------------------------------------------
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
# -------------------------- End of validatation of tools process inputs ------------------------------------------------------------------

                # Check if function is available
                func = available_functions.get(func_name)
                if not func:
                    st.error(f"Function `{func_name}` not found.")
                    continue

                # REAL-TIME MULTI-STEP STATUS UPDATES 
                try:
                    agent_label = agent_name_map.get(func_name, f"{emoji} Calling `{func_name}`")
                    with st.status("Evaluating best agent for this task...", expanded=True) as status:
                        import time
                        import random

                        agent_placeholder = status.empty()
                        all_agents = list(agent_name_map.values())
                        random.shuffle(all_agents)

                        final_agent = agent_name_map.get(func_name, "🔧 Unknown Agent")

                        for agent in all_agents:
                            if agent != final_agent:
                                agent_placeholder.markdown(f"🔄 Switching to: <code>{agent}</code>", unsafe_allow_html=True)
                                time.sleep(0.4)
                            else:
                                # Pause, then show final selected agent
                                time.sleep(0.5)
                                agent_placeholder.markdown(f"✅ <b>Selected:</b> <code>{final_agent}</code>", unsafe_allow_html=True)
                                time.sleep(2)
                                break  # Exit loop once selected
                        status.write(f"Step 1: Calling `{agent_label}` tool...")
                        st.session_state.tool_expander = True
                        output = func(**args)
                        
                        st.session_state.output = output
                        st.session_state.func_name = func_name

                        if func_name == "search_and_scrape":
                            sources_favicon = "".join(
                                f'<img src="{res["favicon_url"]}" class="circle-icon" style="margin-right:-12px;" alt="icon"/>' 
                                for res in (json.loads(output) if isinstance(output, str) else output)[:3] if res.get("favicon_url")
                            )
                            st.session_state.sources_favicon = sources_favicon
                            st.session_state.search_and_scrape_called = True
                            

                            print("icons link", sources_favicon)
                        status.write("Step 2: Tool call completed.")

                        output_str = json.dumps(output, indent=2) if not isinstance(output, str) else output

                        # Prepare refinement messages based on tool
                        if func_name == "search_memory":
                            refinement_messages = [
                                {
                                    'role': 'system',
                                    "content": (
                "You are a perceptive, emotionally intelligent, and highly context-aware AI assistant. "
                "Your job is not just to answer questions, but to understand the user's journey, preferences, tone, and goals over time. "
                "If the `search_memory` tool has returned a result, you must assume it is valid memory previously saved by the user. "
                "Reference and incorporate it naturally into your response. "
                "Do not say that you lack memory or cannot recall things—only say that if the memory tool returned no result. "
                "Avoid generic responses. Be thoughtful, engaging, and practical. "
                "Balance emotional support with directness, especially when the user is struggling or venting. "
                "You are not just a tool—they see you as a thinking partner. Help them feel seen, not just served."
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
                            st.toast (icon="📝", body="Your Memory is been saved !!")
                            refinement_messages = [
                                {
                                    'role': 'system',
                                    'content': "You are a helpful AI assistant."
                                },
                                {
                                    'role': 'user',
                                    'content':   f"User memory update attempted with: {args}. Memory update status: {output_str}. "
                                                "If the update was successful, respond in a concise, warm, and natural tone — acknowledge the info and confirm that it has been remembered. "
                                                "Avoid robotic or overly short replies like 'Got it'. "
                                                "If the update failed, respond politely that the info couldn't be saved."
                                }
                            ]

                        elif func_name == "get_stock_summary":
                            refinement_messages = [
                                {
                                    'role': 'system',
                                    'content': (
                                        "You are a professional AI financial assistant that provides answers to user queries. You have the latest stock price data fetched by the tool. Provide current price and percent change by default. When the user asks for a comparison between stocks, include all ratios (market cap, PE ratio, dividend yield, etc.) in the comparison table. Also, fulfill any other requests or questions in the user’s query. Briefly mention that a graph has been provided showing the past year price trend with dividends and earnings events. If data could not be fetched, inform the user politely. Avoid disclaimers, notes, or additional suggestions unless asked. All data provided is up-to-date."
                                    )
                                },
                                 {
                                    'role': 'user',
                                    'content': query
                                },
                                
                                {
                                    'role': 'tool',
                                    'content': output_str
                                }
                            ]


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

                # Tool Usage Display
                    with st.container():
                
                        with st.expander("📤 Output from Tool", expanded=False):
                            st.markdown("#### 📄 Response")
                            st.json(output_str if isinstance(output_str, (dict, list)) else {"output": output_str})
                    
                
                    if func_name == "get_stock_summary":
        
                        generate_multiple_charts(stock_symbols)
                        st.session_state.charts_generated = True
                        st.session_state.chart_symbols = stock_symbols 
                        print("hiiiii", stock_symbols)
                        
                    elif func_name == "analyze_github_repo":
                        repo_url = str(args.get("repo_url", "")).strip()
                        print(func_name, args)
                        st.session_state.github_repo_url = repo_url
                        st.session_state.show_github_analysis = True
                    
                    if not st.session_state.show_github_analysis:
                        st.subheader("💬 Final Answer:")
                        st.json(refinement_messages, expanded= False)
                        st.write_stream(stream_ollama_response("llama3.2", refinement_messages))  # stream live
                        
                        output_rendered = True
                    


                        
                except Exception as e:
                    st.error(f"Error executing `{func_name}`: {e}")
                    continue


if st.session_state.show_github_analysis and st.session_state.github_repo_url:
    # with st.expander("🧑‍💻 GitHub Code Scanner", expanded=True):
    # from tools.custom_github import generate_repo_page
    generate_repo_page(st.session_state.github_repo_url)

    if st.button("❌ Hide GitHub Analysis"):
        st.session_state.show_github_analysis = False
        st.session_state.github_repo_url = ""
        st.rerun()


if st.session_state.search_and_scrape_called and st.session_state.get('output'):
    if "show_sources_clicked" not in st.session_state:
        st.session_state.show_sources_clicked = False

    # Use a container to group answer and button so they render together
    with st.container():
        if not output_rendered:
            # Show fallback display on rerun
            if st.session_state.output and st.session_state.ai_answer:
                output_str = (
                    json.dumps(st.session_state.output, indent=2)
                    if not isinstance(st.session_state.output, str)
                    else st.session_state.output
                )
            
                with st.container():
                    func_name = st.session_state.get("func_name", "unknown_tool")
                    emoji = emoji_map.get(func_name, "🛠️")
                    agent_label = agent_name_map.get(func_name, f"{emoji} Calling `{func_name}`")

                    with st.status(f"{agent_label} and refining answer with AI...") as status:
                        status.write(f"Step 1: Calling `{agent_label}` tool...")
                        status.write("Step 2: Tool call completed.")
                    
                    with st.expander("📤 Output from Tool", expanded=False):
                        st.markdown("#### 📄 Response")
                        st.json(output_str if isinstance(output_str, (dict, list)) else {"output": output_str})

                st.subheader("💬 Final Answer:")
                st.markdown(st.session_state.ai_answer)

        # Show the button always when search_and_scrape_called, below the answer
        if st.session_state.sources_favicon:
            st.markdown("""
            <style>
            .circle-icon {
                width: 25px;
                height: 25px;
                border-radius: 50%;
                object-fit: cover;
                margin: 0 6px 0 0;  /* Slightly less right margin */
                vertical-align: middle;
                border: none !important;
                box-shadow: none !important;
            }
            .sources-button-container {
                display: flex;
                align-items: center;
                gap: 4px;  /* Reduce spacing between icons */
                margin-top: 8px;  /* Slightly less top margin */
            }
            </style>
            """, unsafe_allow_html=True)

            # Use tighter column ratio to bring items closer
            container = st.container()
            with container:
                col1, col2 = st.columns([0.9, 15])  # Tighter gap: increase icon space, reduce button space

                with col1:
                    st.markdown(
                        f'<div class="sources-button-container">{st.session_state.sources_favicon}</div>',
                        unsafe_allow_html=True
                    )
                with col2:
                    if st.button("Sources", type="tertiary"):
                        st.session_state.show_sources_clicked = True

if (
    st.session_state.get("charts_generated") 
    and st.session_state.get("chart_symbols") 
    and st.session_state.get("func_name") == "get_stock_summary"
):
    if not output_rendered:
        if st.session_state.output and st.session_state.ai_answer:
        
            output_str = (
                    json.dumps(st.session_state.output, indent=2)
                    if not isinstance(st.session_state.output, str)
                    else st.session_state.output
                )
            
            with st.container():
                func_name = st.session_state.get("func_name", "unknown_tool")
                emoji = emoji_map.get(func_name, "🛠️")
                agent_label = agent_name_map.get(func_name, f"{emoji} Calling `{func_name}`")
                with st.status(f"{agent_label} and refining answer with AI...") as status:
                        status.write(f"Step 1: Calling `{agent_label}` tool...")
                        status.write("Step 2: Tool call completed.")
                
                with st.expander("📤 Output from Tool", expanded=False):
                    st.markdown("#### 📄 Response")
                    st.json(output_str if isinstance(output_str, (dict, list)) else {"output": output_str})
                    
        generate_multiple_charts(st.session_state.chart_symbols)

    # 💡 Make sure output isn't rendered more than once
        st.subheader("💬 Final Answer:")
        st.markdown(st.session_state.ai_answer)

if st.session_state.show_sources_clicked:
    show_sources(st.session_state['output'])
    st.session_state.show_sources_clicked = False


