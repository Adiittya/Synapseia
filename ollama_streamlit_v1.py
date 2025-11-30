import streamlit as st
import json
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
from ollama import chat, ChatResponse
from tools.custom_scrapper import search_and_scrape
from tools.custom_yfinance import get_stock_summary
from tools.custom_memories import store_memory, search_memory
from tools.custom_github import analyze_github_repo, generate_repo_page
from ui_components.memory_manager_modal import memory_manager_dialog
from tool_schema import tools_schema, tools_prompt
import ast
from ui_components.sources_modal import show_sources
import streamlit.components.v1 as components
from ui_components.stock_graph_generation import generate_multiple_charts
from ui_components.suggestion_scroll import suggestion_scroll_ui


# ======================== CONSTANTS ========================

AVAILABLE_FUNCTIONS = { 
    'search_and_scrape': search_and_scrape,
    'get_stock_summary': get_stock_summary,
    'store_memory': store_memory,
    "search_memory": search_memory,
    "analyze_github_repo": analyze_github_repo
}

EMOJI_MAP = {
    "get_stock_summary": "📈",
    "search_and_scrape": "🌐",
    "skip_tools": "💡",
    "store_memory": "💾",
    "search_memory": "📝",
    "analyze_github_repo": "🧑‍💻"
}

AGENT_NAME_MAP = {
    "search_and_scrape": "Scraping Agent 🌐",
    "get_stock_summary": "Stock Agent 📈",
    "store_memory": "Memory Agent 💾",
    "search_memory": "Memory Agent 📝",
    "skip_tools": "Direct Answer 💡",
    "analyze_github_repo": "GitHub Agent 🧑‍💻"
}

SUGGESTION_TOPICS = [
    ("☕", "Explain this week's biggest controversy"),
    ("💸", "Compare Tata Motors & Maruti Suzuki stocks"),
    ("🤓", "summarize today's top tech headlines"),
    ("💻", "HDFC bank stock price"),
    ("😋", "Spill latest tea"),
    ("😷", "Current Aqi of mumbai"),
    ("😢", "How to deal with depression?"),
    ("💅🏻", "Suggestion me skincare routine"),
    ("🐱", "Why my cat bite and hates me"),
    ("➗", "Give all formulas for integrations"),
    ("🎤", "latest concert happening in mumbai?"),
]

# ======================== LOGGING SETUP ========================

logging.basicConfig(
    level=logging.INFO, 
    filename="tool_logs.txt", 
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ======================== HELPER FUNCTIONS ========================

def initialize_session_state():
    """Initialize all session state variables in one place"""
    defaults = {
        "query": "",
        "search_and_scrape_called": False,
        "output": None,
        "func_name": None,
        "ai_answer": "",
        "sources_favicon": "",
        "ask_now": False,
        "show_sources_clicked": False,
        "last_query_ran": "",
        "charts_generated": False,
        "chart_symbols": [],
        "tool_expander": False,
        "show_github_analysis": False,
        "github_repo_url": ""
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_query_state():
    """Reset state variables for a new query"""
    st.session_state.ai_answer = ""
    st.session_state.output = None
    st.session_state.func_name = None
    st.session_state.search_and_scrape_called = False
    st.session_state.show_github_analysis = False
    st.session_state.github_repo_url = ""
    st.session_state.charts_generated = False


@lru_cache(maxsize=1)
def get_custom_css() -> str:
    """Return custom CSS (cached to avoid recreation)"""
    return """
    <style>
    .stApp { background-color: #0f0f0f; }
    
    /* Remove top white space */
    header[data-testid="stHeader"] { height: 0 !important; padding: 0 !important; margin: 0 !important; }
    div.block-container { padding-top: 0 !important; margin-top: 0 !important; }
    main[data-testid="stAppViewContainer"] { padding-top: 0 !important; margin-top: 0 !important; }
    div[data-testid="stAppViewContainer"] { padding-top: 0 !important; margin-top: 0 !important; }
    h1, h2 { margin-top: 0.1rem !important; padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; padding-top: 0 !important; }
    
    /* Animations */
    @keyframes fadeInSmooth {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .element-container, .stStatus, .st-expander, .stTextArea, .stTextInput {
        animation: fadeInSmooth 0.35s ease;
    }
    
    /* Icon effects */
    .circle-icon {
        width: 26px !important; height: 26px !important;
        border-radius: 50%; transition: transform 0.25s ease;
    }
    .circle-icon:hover { transform: scale(1.15); }
    
    /* Smooth scrolling */
    html, body, * { scroll-behavior: smooth !important; -webkit-overflow-scrolling: touch !important; }
    div[data-testid="stVerticalBlock"], div[data-testid="stSidebar"], div[tabindex] {
        scroll-behavior: smooth !important;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stMarkdown p { color: var(--text-secondary); animation: fadeSlideUp 0.6s ease-out; }
    </style>
    """


def stream_ollama_response(model: str, messages: List[Dict]) -> Any:
    """Stream response from Ollama model"""
    for chunk in chat(model, messages=messages, stream=True):
        if chunk and getattr(chunk, "message", None):
            st.session_state.ai_answer += chunk.message.content
            yield chunk.message.content


def build_refinement_messages(func_name: str, query: str, output_str: str, initial_messages: List[Dict]) -> List[Dict]:
    """Build messages for AI refinement based on tool used"""
    
    system_prompts = {
        "search_memory": (
            "You are a perceptive, emotionally intelligent, and highly context-aware AI assistant. "
            "Your job is not just to answer questions, but to understand the user's journey, preferences, tone, and goals over time. "
            "If the `search_memory` tool has returned a result, you must assume it is valid memory previously saved by the user. "
            "Reference and incorporate it naturally into your response. "
            "Do not say that you lack memory or cannot recall things—only say that if the memory tool returned no result. "
            "Avoid generic responses. Be thoughtful, engaging, and practical. "
            "Balance emotional support with directness, especially when the user is struggling or venting. "
            "You are not just a tool—they see you as a thinking partner. Help them feel seen, not just served."
        ),
        "store_memory": "You are a helpful AI assistant.",
        "get_stock_summary": (
            "You are a professional AI financial assistant that provides answers to user queries. You have the latest stock price data fetched by the tool. "
            "Provide current price and percent change by default. When the user asks for a comparison between stocks, include all ratios "
            "(market cap, PE ratio, dividend yield, etc.) in the comparison table. Also, fulfill any other requests or questions in the user's query. "
            "Briefly mention that a graph has been provided. If data could not be fetched, inform the user politely. Avoid disclaimers."
        ),
        "search_and_scrape": (
            "You are a web intelligence assistant. Use only the information provided by the scraping tool. "
            "Do not invent sources, facts, or URLs. Summarize the extracted content in a clear and concise way, "
            "focusing only on the key insights across all articles. If multiple results are provided, combine them "
            "into a short, readable summary with points and explanations. "
            "If the scraped data is empty or unclear, respond naturally without guessing."
        )
    }
    
    if func_name == "search_memory":
        return [
            {'role': 'system', 'content': system_prompts["search_memory"]},
            {'role': 'user', 'content': query},
            {'role': 'tool', 'name': func_name, 'content': output_str}
        ]
    
    if func_name == "store_memory":
        return [
            {'role': 'system', 'content': system_prompts["store_memory"]},
            {'role': 'tool', 'name': func_name, 'content': output_str},
            {
                'role': 'user',
                'content': (
                    "The above is the result of a memory-store operation. "
                    "If it looks successful, respond in a concise, warm, natural tone, acknowledging that you've remembered it. "
                    "If it looks like an error, say politely that the info couldn't be saved."
                )
            }
        ]
    
    if func_name in system_prompts:
        return [
            {'role': 'system', 'content': system_prompts[func_name]},
            {'role': 'user', 'content': query},
            {'role': 'tool', 'name': func_name, 'content': output_str}
        ]
    
    return initial_messages + [{'role': 'tool', 'name': func_name, 'content': output_str}]


def validate_tool_args(func_name: str, args: Dict) -> Optional[Dict]:
    """Validate and process tool arguments. Returns None if validation fails."""
    
    if func_name == "search_and_scrape":
        if not args.get('query', '').strip():
            st.warning("Empty query passed to search_and_scrape tool. Skipping.")
            return None
    
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
            return None
    
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
                return None
        elif tags is not None and not isinstance(tags, list):
            st.warning(f"Invalid tags format: {tags}. Skipping store_memory.")
            return None
    
    return args


def display_tool_output(func_name: str, output: Any):
    """Display tool output in an expander"""
    output_str = json.dumps(output, indent=2) if not isinstance(output, str) else output
    
    with st.expander("📤 Output from Tool", expanded=False):
        st.markdown("#### 📄 Response")
        st.json(output_str if isinstance(output_str, (dict, list)) else {"output": output_str})


def execute_tool_with_status(func_name: str, args: Dict, emoji: str) -> Optional[Any]:
    """Execute tool with real-time status updates"""
    import time
    import random
    
    func = AVAILABLE_FUNCTIONS.get(func_name)
    if not func:
        st.error(f"Function `{func_name}` not found.")
        return None
    
    agent_label = AGENT_NAME_MAP.get(func_name, f"{emoji} Calling `{func_name}`")
    
    with st.status("Evaluating best agent for this task...", expanded=True) as status:
        agent_placeholder = status.empty()
        all_agents = list(AGENT_NAME_MAP.values())
        random.shuffle(all_agents)
        final_agent = AGENT_NAME_MAP.get(func_name, "🔧 Unknown Agent")
        
        # Show agent selection animation
        for agent in all_agents:
            if agent != final_agent:
                agent_placeholder.markdown(f"🔄 Switching to: <code>{agent}</code>", unsafe_allow_html=True)
                time.sleep(0.4)
            else:
                time.sleep(0.5)
                agent_placeholder.markdown(f"✅ <b>Selected:</b> <code>{final_agent}</code>", unsafe_allow_html=True)
                time.sleep(1)
                break
        
        status.write(f"Step 1: Calling `{agent_label}` tool...")
        st.session_state.tool_expander = True
        
        try:
            output = func(**args)
            status.write("Step 2: Tool call completed.")
            return output
        except Exception as e:
            st.error(f"Error executing `{func_name}`: {e}")
            return None


def handle_search_scrape_output(output: Any):
    """Process search_and_scrape output and store favicons"""
    sources_favicon = "".join(
        f'<img src="{res["favicon_url"]}" class="circle-icon" style="margin-right:-12px;" alt="icon"/>' 
        for res in (json.loads(output) if isinstance(output, str) else output)[:3] 
        if res.get("favicon_url")
    )
    st.session_state.sources_favicon = sources_favicon
    st.session_state.search_and_scrape_called = True


def render_sources_button():
    """Render the sources button with favicons"""
    if not st.session_state.sources_favicon:
        return
    
    st.markdown("""
    <style>
    .circle-icon {
        width: 25px; height: 25px; border-radius: 50%;
        object-fit: cover; margin: 0 6px 0 0;
        vertical-align: middle; border: none !important;
        box-shadow: none !important;
    }
    .sources-button-container {
        display: flex; align-items: center;
        gap: 4px; margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    container = st.container()
    with container:
        col1, col2 = st.columns([0.9, 15])
        with col1:
            st.markdown(
                f'<div class="sources-button-container">{st.session_state.sources_favicon}</div>',
                unsafe_allow_html=True
            )
        with col2:
            if st.button("Sources", type="tertiary"):
                st.session_state.show_sources_clicked = True


def render_fallback_output(output_rendered: bool):
    """Render fallback output on rerun"""
    if output_rendered or not st.session_state.output or not st.session_state.ai_answer:
        return
    
    output_str = (
        json.dumps(st.session_state.output, indent=2)
        if not isinstance(st.session_state.output, str)
        else st.session_state.output
    )
    
    func_name = st.session_state.get("func_name", "unknown_tool")
    emoji = EMOJI_MAP.get(func_name, "🛠️")
    agent_label = AGENT_NAME_MAP.get(func_name, f"{emoji} Calling `{func_name}`")
    
    with st.status(f"{agent_label} and refining answer with AI...") as status:
        status.write(f"Step 1: Calling `{agent_label}` tool...")
        status.write("Step 2: Tool call completed.")
    
    display_tool_output(func_name, output_str)
    st.subheader("💬 Final Answer:")
    st.markdown(st.session_state.ai_answer)


# ======================== MAIN APPLICATION ========================

def main():
    # Page config
    st.set_page_config(page_title="SYNAPSEIA", layout="wide")
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Hide Streamlit default elements
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    .stToolbar {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("Project SYNAPSEIA")
    st.markdown("Stock & Web Assistant")
    
    # Memory management
    col1, col2 = st.columns([1, 5])
    if col1.button("🗃️ Manage Memory"):
        memory_output = memory_manager_dialog()
        print(memory_output)
    
    st.markdown("---")
    
    # Suggestions
    st.markdown("#### 💡 Quick Prompts")
    suggestion_scroll_ui(SUGGESTION_TOPICS, num_rows=2)
    
    # Query input
    query = st.text_area(
        "📝 Ask a question:",
        value=st.session_state.query,
        height=68,
        key="query"
    )
    
    output_rendered = False
    ask_button_pressed = st.button("Ask")
    
    # Main query processing logic
    if (ask_button_pressed or st.session_state.get("ask_now")) and query and query != st.session_state.last_query_ran:
        st.session_state.ask_now = False
        reset_query_state()
        st.session_state.last_query_ran = query
        
        with st.spinner("Thinking..."):
            initial_messages = [
                {'role': 'system', 'content': tools_prompt.tool_system_prompt},
                {'role': 'user', 'content': query}
            ]
            
            tools = [
                tools_schema.web_search_tool,
                tools_schema.skip_tool,
                tools_schema.stock_fetch_tool,
                tools_schema.store_memory_tool,
                tools_schema.search_memory_tool,
                tools_schema.github_repo_tool
            ]
            
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
                    emoji = EMOJI_MAP.get(func_name, "🔧")
                    
                    # Handle skip_tools
                    if func_name == "skip_tools":
                        st.session_state.ai_answer = ""
                        direct_messages = [
                            {'role': 'system', 'content': tools_prompt.skip_tool_prompt},
                            {'role': 'user', 'content': query}
                        ]
                        st.subheader("💬 Final Answer:")
                        st.write_stream(stream_ollama_response("llama3.2", direct_messages))
                        output_rendered = True
                        break
                    
                    # Validate arguments
                    args = validate_tool_args(func_name, args)
                    if args is None:
                        continue
                    
                    # Execute tool
                    output = execute_tool_with_status(func_name, args, emoji)
                    if output is None:
                        continue
                    
                    st.session_state.output = output
                    st.session_state.func_name = func_name
                    
                    # Handle special outputs
                    if func_name == "search_and_scrape":
                        handle_search_scrape_output(output)
                    
                    # Display tool output
                    display_tool_output(func_name, output)
                    
                    # Handle stock charts
                    if func_name == "get_stock_summary":
                        generate_multiple_charts(args['stock_symbols'])
                        st.session_state.charts_generated = True
                        st.session_state.chart_symbols = args['stock_symbols']
                    
                    # Handle GitHub analysis
                    elif func_name == "analyze_github_repo":
                        repo_url = str(args.get("repo_url", "")).strip()
                        st.session_state.github_repo_url = repo_url
                        st.session_state.show_github_analysis = True
                    
                    # Generate AI response
                    if not st.session_state.show_github_analysis:
                        output_str = json.dumps(output, indent=2) if not isinstance(output, str) else output
                        refinement_messages = build_refinement_messages(func_name, query, output_str, initial_messages)
                        
                        st.subheader("💬 Final Answer:")
                        st.write_stream(stream_ollama_response("llama3.2", refinement_messages))
                        output_rendered = True
    
    # GitHub analysis display
    if st.session_state.show_github_analysis and st.session_state.github_repo_url:
        generate_repo_page(st.session_state.github_repo_url)
        if st.button("❌ Hide GitHub Analysis"):
            st.session_state.show_github_analysis = False
            st.session_state.github_repo_url = ""
            st.rerun()
    
    # Sources button display
    if st.session_state.search_and_scrape_called and st.session_state.get('output'):
        render_fallback_output(output_rendered)
        render_sources_button()
    
    # Stock charts fallback display
    if (st.session_state.get("charts_generated") and 
        st.session_state.get("chart_symbols") and 
        st.session_state.get("func_name") == "get_stock_summary"):
        
        render_fallback_output(output_rendered)
        if not output_rendered:
            generate_multiple_charts(st.session_state.chart_symbols)
    
    # Show sources modal
    if st.session_state.show_sources_clicked:
        show_sources(st.session_state['output'])
        st.session_state.show_sources_clicked = False
    
    # Fallback renderer for simple answers
    if (not output_rendered and 
        st.session_state.ai_answer and 
        not st.session_state.search_and_scrape_called and 
        not st.session_state.get("charts_generated", False) and 
        not st.session_state.get("show_github_analysis", False)):
        
        st.subheader("💬 Final Answer:")
        st.markdown(st.session_state.ai_answer)
    
    # JavaScript for suggestion pills
    components.html("""
    <script>
    (function(){
        const doc = window.parent.document;

        function setReactValue(element, value) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.parent.HTMLTextAreaElement.prototype, "value"
            ).set;
            nativeInputValueSetter.call(element, value);
            const inputEvent = new Event('input', { bubbles: true });
            const changeEvent = new Event('change', { bubbles: true });
            element.dispatchEvent(inputEvent);
            element.dispatchEvent(changeEvent);
        }

        function fillAndAsk(text){
            const ta = doc.querySelector('textarea[aria-label="📝 Ask a question:"]') ||
                       doc.querySelector('textarea[data-testid="stTextArea"]') ||
                       doc.querySelector("textarea");
            if (!ta) return;
            
            setReactValue(ta, "");
            setTimeout(() => {
                setReactValue(ta, text);
                ta.focus();
                setTimeout(() => {
                    ta.blur();
                    setTimeout(() => clickAsk(), 150);
                }, 100);
            }, 50);
        }

        function clickAsk() {
            const askBtn = [...doc.querySelectorAll("button")]
                .find(b => {
                    const text = (b.innerText || "").trim().toLowerCase();
                    return text === "ask" && !b.disabled && b.offsetParent !== null;
                });
            if (askBtn) askBtn.click();
            else setTimeout(clickAsk, 100);
        }

        function attachHandlers() {
            const buttons = doc.querySelectorAll("button.topic-btn");
            buttons.forEach(btn => {
                const oldHandler = btn._suggestionHandler;
                if (oldHandler) btn.removeEventListener("click", oldHandler);
                
                const newHandler = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const text = btn.dataset.value || btn.innerText.trim();
                    fillAndAsk(text);
                };
                btn._suggestionHandler = newHandler;
                btn.addEventListener("click", newHandler);
            });
        }

        setTimeout(attachHandlers, 500);
        const observer = new MutationObserver(attachHandlers);
        observer.observe(doc.body, { childList: true, subtree: true });
    })();
    </script>
    """, height=0)


if __name__ == "__main__":
    main()