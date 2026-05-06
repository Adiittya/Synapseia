# GitHub Code Structure Scanner with Ollama-Powered QA

import requests
import re
import os
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
import ollama
import time
from collections import defaultdict

# --- Utility: Check Ollama Running ---

from collections import defaultdict
import os

def generate_folder_summary(paths):
    grouped = defaultdict(lambda: {"files": [], "folders": set()})
    
    for path in paths:
        parts = path.split("/")
        for i in range(1, len(parts)):
            parent = "/".join(parts[:i])
            current = parts[i]
            if i == len(parts) - 1:
                if "." in current:  # file
                    grouped[parent]["files"].append(current)
                else:  # folder with no trailing file (unlikely)
                    grouped[parent]["folders"].add(current)
            else:
                grouped[parent]["folders"].add(current)
    
    # Build lines in readable form
    lines = []
    for folder in sorted(grouped):
        items = []
        if grouped[folder]["files"]:
            items.extend(sorted(grouped[folder]["files"]))
        if grouped[folder]["folders"]:
            items.extend(sorted(f + "/" for f in grouped[folder]["folders"]))
        if items:
            lines.append(f"📁 {folder}/: {', '.join(items)}")
    return "\n".join(lines)

def is_ollama_running():
    try:
        ollama.list()
        return True
    except Exception:
        return False
    
def build_tree(paths):
    tree = {}
    for path in paths:
        parts = path.split('/')
        current = tree
        for part in parts:
            current = current.setdefault(part, {})
    return tree

def get_tree_string(tree, indent=0):
    lines = []
    for key, subtree in tree.items():
        prefix = "    " * indent + ("📁 " if subtree else "📄 ") + key
        lines.append(prefix)
        lines.extend(get_tree_string(subtree, indent + 1))
    return lines


def generate_file_contents_summary(files, df):
    lines = []
    for path in files:
        rows = df[df["file_path"] == path]
        if not rows.empty:
            lines.append(f"📄 **{path}**")
            content = rows.iloc[0]["content"]
            lines.append("```js\n" + content.strip()[:3000] + "\n```")  # Truncate large files
    return "\n\n".join(lines)


# --- Utility: Ask Ollama to Explain Code ---
def ollama_explain_code(prompt, model="llama3.2"):
    start = time.time()
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        end = time.time()
        duration = round(end - start, 2)
        return response['message']['content'], duration
    except Exception as e:
        return f"⚠️ Ollama error: {str(e)}", None

# --- GitHub Auth ---
token = "xxxxxxxxxxxxxxxxxxxxxxx"  # 🔒 Replace this with your GitHub PAT
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "SYNAPSEIA"
}

# --- Language Patterns ---
patterns = {
   "python": {
    "function": r"^\s*def\s+(\w+)\s*\((.*?)\)\s*:",
    "class": r"^\s*class\s+(\w+)\s*(\(.*?\))?\s*:",
    "variable": r"^\s*(\w+)\s*=\s*.+",
    "import": r"^\s*(?:from\s+\S+\s+)?import\s+.+"
    },
"javascript": {
    "function": r"(?:function\s+(\w+)\s*\((.*?)\)\s*{|(?:let|const|var)\s+(\w+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>)",
    "class": r"class\s+(\w+)\s*{",
    "variable": r""
}

,
    "typescript": {
        "function": r"function\s+(\w+)\s*\((.*?)\)\s*{",
        "class": r"class\s+(\w+)\s*{",
        "variable": r"(?:let|const|var)\s+(\w+)\s*=\s*.+",
        "import": r"import\s+.*\s+from\s+['\"].+['\"]"
    },
    "cpp": {
        "function": r"\b(?:void|int|float|double|char|bool|string)\s+(\w+)\s*\((.*?)\)\s*{",
        "class": r"class\s+(\w+)\s*{",
        "variable": r"(?:int|float|double|char|bool|string)\s+(\w+)\s*=\s*.+;",
        "import": r"#include\s+<.+>"
    },
    "java": {
        "function": r"(?:public|private|protected)?\s+(?:void|int|float|String|boolean|double)\s+(\w+)\s*\((.*?)\)\s*{",
        "class": r"class\s+(\w+)\s*{",
        "variable": r"(?:int|float|String|boolean|double)\s+(\w+)\s*=\s*.+;",
        "import": r"import\s+.+;"
    },
    "dart": {
        "function": r"(?:[\w<>]+\s+)?(\w+)\s*\((.*?)\)\s*{",
        "class": r"class\s+(\w+)\s*{",
        "variable": r"(?:final|var|late)?\s*(?:[\w<>]+)\s+(\w+)\s*=?\s*.+;",
        "import": r"import\s+['\"].+['\"]\s*;"
    }
}

ext_map = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".cpp": "cpp", ".java": "java", ".dart": "dart"
}

# --- GitHub Utilities ---
@st.cache_data(show_spinner=False)
def get_file_raw(user, repo, path):
    url = f"https://raw.githubusercontent.com/{user}/{repo}/HEAD/{path}"
    res = requests.get(url)
    res.raise_for_status()
    return res.text

def extract_code_structure(code, language, path):
    results = []
    for block_type, pattern in patterns.get(language, {}).items():
        matches = re.finditer(pattern, code, re.MULTILINE)
        for match in matches:
            try:
                if block_type == "function":
                    if match.lastindex == 4:  # JS arrow or normal
                        if match.group(1):  # regular function
                            signature = f"{match.group(1)}({match.group(2)})"
                        elif match.group(3):  # arrow function
                            signature = f"{match.group(3)}({match.group(4)})"
                        else:
                            continue
                    else:  # other languages
                        signature = f"{match.group(1)}({match.group(2)})"
                else:
                    signature = match.group(1)

                results.append((path, language, block_type, signature))

            except IndexError:
                print(f"⚠️ Skipping match in {path} for {block_type}: group not found")
    return results



def process_file(path, user, repo):
    try:
        ext = os.path.splitext(path)[1]
        lang = ext_map.get(ext)
        if not lang:
            return []

        content = get_file_raw(user, repo, path)
        extracted = extract_code_structure(content, lang, path)
        
        print(f"Parsed {path} | Language: {lang} | Structures Found: {len(extracted)}")

        # 🔥 Add file content to each extracted row
        for i in range(len(extracted)):
            extracted[i] = extracted[i] + (content,)

        return extracted
    except Exception as e:
        print(f"❌ Error in {path}: {e}")
        return []


def search_code(df, query="", block_type=None, file_filter=None):
    filtered = df.copy()
    if block_type:
        filtered = filtered[filtered["type"].str.lower() == block_type.lower()]
    if file_filter:
        filtered = filtered[filtered["file_path"].str.contains(file_filter, case=False, na=False)]
    if query:
        query = query.lower()
        mask = (
            filtered["signature"].str.lower().str.contains(query, na=False) |
            filtered["file_path"].str.lower().str.contains(query, na=False) |
            filtered["type"].str.lower().str.contains(query, na=False) |
            filtered["language"].str.lower().str.contains(query, na=False)
        )
        filtered = filtered[mask]
    return filtered

def get_default_branch(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json().get("default_branch", "main")  # fallback to 'main'


@st.cache_data(show_spinner=False)
def get_repo_tree(user, repo):
    default_branch = get_default_branch(user, repo)
    url = f"https://api.github.com/repos/{user}/{repo}/git/trees/{default_branch}?recursive=1"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return [item for item in res.json().get("tree", []) if item["type"] == "blob"]

def find_function_usages_in_df(df, function_names):
    usage = []
    df["content"] = df["content"].fillna("")
    for func in function_names:
        mask = df["content"].str.contains(rf"\b{re.escape(func)}\b", na=False)
        matched = df[mask]
        for _, row in matched.iterrows():
            usage.append((func, row["file_path"]))
    return usage




# === Streamlit App ===
st.set_page_config(page_title="GitHub Code Scanner", layout="wide")
# --- Session State Initialization ---
default_keys = {
    "selected_files": [],
    "selected_functions": [],
    "ollama_response": "",
    "ollama_prompt": "",
    "ollama_duration": 0.0,
    "traced_usages": []
}

for k, v in default_keys.items():
    if k not in st.session_state:
        st.session_state[k] = v


def generate_github_page(repo_url: str):
    if not repo_url:
        st.error("❌ Please enter a valid GitHub URL.")
        return

    parts = repo_url.strip().rstrip("/").split("/")
    if len(parts) < 2 or not parts[-2] or not parts[-1]:
        st.error("❌ Invalid GitHub URL. Use format: https://github.com/user/repo")
        return

    user, repo = parts[-2], parts[-1]

    if "scanned_repo" not in st.session_state or st.session_state.scanned_repo != repo_url:
        with st.spinner("🔍 Scanning repository..."):
            repo_tree = get_repo_tree(user, repo)
            file_paths = [f["path"] for f in repo_tree if os.path.splitext(f["path"])[1] in ext_map]

            progress_placeholder = st.empty()
            progress_bar = st.progress(0)
            progress_log = []
            results = []
            scanned_count = 0  # ✅ Initialize this

            
            with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = executor.map(lambda path: process_file(path, user, repo), file_paths)
                    for path, r in zip(file_paths, futures):
                        scanned_count += 1
                        results.extend(r)

                        log_line = f"""
                        <div style="font-size: 0.85rem; color: #adb5bd; margin-bottom: 4px;">
                            <span style="color: #66b2ff;">📄</span> 
                            <strong style="color:#dee2e6;">{scanned_count}/{len(file_paths)}</strong> 
                            <code style="color:#f8f9fa; background:#343a40; padding: 2px 6px; border-radius: 4px;">{path}</code>
                        </div>
                        """


                        progress_log.append(log_line)
                        progress_placeholder.markdown("".join(progress_log[-1:]), unsafe_allow_html=True)
                        progress_bar.progress(scanned_count / len(file_paths))

            st.toast("Scan Complete! All files processed successfully.", icon="✔️")
            progress_bar.empty()

            df_structure = pd.DataFrame(results, columns=["file_path", "language", "type", "signature", "content"])
            df_structure.drop_duplicates(subset=["file_path", "language", "type", "signature"], inplace=True)

            df_structure["tags"] = df_structure.apply(tag_code_block_multi, axis=1)

            st.session_state.repo_tree = repo_tree
            st.session_state.file_paths = file_paths
            st.session_state.df_structure = df_structure
            st.session_state.scanned_repo = repo_url
    else:
        df_structure = st.session_state.df_structure
        file_paths = st.session_state.file_paths

    tab_names = ["📋 Code Structure", "🔍 Search & Filter", "💬 Q&A & Tracing"]
    selected_tab = tabs(tab_names, default_active_tab=st.session_state.get("active_tab", 0))
    st.session_state.active_tab = tab_names.index(selected_tab)

    if selected_tab == "📋 Code Structure":
        render_repo_summary_tab(user, repo, df_structure, file_paths)
    elif selected_tab == "🔍 Search & Filter":
        render_search_tab(df_structure)
    elif selected_tab == "💬 Q&A & Tracing":
        render_qa_tracing_tab(df_structure, file_paths, user, repo)



def render_repo_summary_tab(user, repo, df_structure, file_paths):
    st.subheader("Repository Summary")
    st.markdown(f"**Repository:** `{user}/{repo}`")
    st.markdown(f"**Files Parsed:** `{len(df_structure['file_path'].unique())}`")
    st.markdown(f"**Languages Detected:** `{', '.join(df_structure['language'].unique())}`")

    tree = build_tree(file_paths)
    with st.expander("📂 Repository Tree"):
        st.code("\n".join(get_tree_string(tree)), language="text")

    st.markdown("### Code Structure and Tags")
    available_tags = df_structure["tags"].str.split(", ").explode().unique().tolist()
    selected_tags = st.multiselect("Select tags to filter", available_tags)

    if selected_tags:
        filtered_df = df_structure[df_structure["tags"].apply(lambda x: any(tag in x for tag in selected_tags))]
    else:
        filtered_df = df_structure

    st.dataframe(filtered_df[["file_path", "language", "type", "signature", "tags"]], use_container_width=True)


def render_search_tab(df_structure):
    st.subheader("Search Codebase")
    st.markdown("Filter functions, classes, or code blocks using keywords or file name.")
    st.caption(f"Files Indexed: {df_structure['file_path'].nunique()}")

    col1, col2, col3 = st.columns(3)
    with col1:
        query = st.text_input("Keyword", key="q")
    with col2:
        btype = st.selectbox("Type", ["", "function", "class", "variable", "import"])
    with col3:
        fname = st.text_input("Filename Filter", key="fn")

    filtered = search_code(df_structure, query, btype or None, fname)
    st.caption(f"Matches Found: {len(filtered)}")
    st.dataframe(filtered, use_container_width=True)


def render_qa_tracing_tab(df_structure, file_paths, user, repo):
    st.subheader("🔎 Trace Function Usages")
    
    col1, col2 = st.columns(2)
    with col1:
        prev_files = st.session_state.get("selected_files", [])
        files = st.multiselect("Select files", df_structure["file_path"].unique().tolist(), default=prev_files)
        if set(files) != set(prev_files):
            st.session_state.selected_functions = []
            st.session_state.traced_usages = []
        st.session_state.selected_files = files

    with col2:
        s_df = df_structure[df_structure["file_path"].isin(files)] if files else df_structure
        funcs = s_df[s_df["type"] == "function"]["signature"].tolist()
        selected_funcs = st.multiselect("Select functions", funcs, default=st.session_state.selected_functions)
        st.session_state.selected_functions = selected_funcs

    if st.button("🔍 Trace Usages"):
        if not selected_funcs:
            st.warning("Please select at least one function.")
        else:
            traced = find_function_usages_in_df(df_structure, [f.split("(")[0] for f in selected_funcs])
            if traced:
                st.session_state.traced_usages = sorted(set(traced))
                st.success(f"{len(st.session_state.traced_usages)} unique usage(s) found.")
            else:
                st.warning("No usages found in the repository.")
                st.session_state.traced_usages = []

    if st.session_state.traced_usages:
        st.markdown("### Traced Usages")
        st.dataframe(pd.DataFrame(st.session_state.traced_usages, columns=["Function", "Used In File"]), use_container_width=True)

    # --- Ollama QA ---
    st.markdown("---")
    st.subheader("💬 Ask Ollama About the Codebase")

    if files:
        st.markdown(f"📂 **Context limited to {len(files)} selected file(s)**")
        with st.expander("🔎 See selected file paths", expanded=False):
            for f in files:
                st.markdown(f"- `{f}`")
    else:
        st.markdown("📁 **Context includes the entire repository structure**")

    user_q = st.text_area("Enter your question here", placeholder="e.g., What does this project do?")

    if st.button("🧠 Ask Ollama") and user_q.strip():
        if not is_ollama_running():
            st.error("❌ Ollama is not running.")
            return

        selected_paths = files if files else file_paths
        context = generate_file_contents_summary(selected_paths, df_structure)

        prompt = f"""
        You are a senior software engineer helping analyze {'selected files' if files else 'the full repository'}.

        Context:
        {context}

        Question:
        {user_q.strip()}
        """.strip()

        resp, dur = ollama_explain_code(prompt)
        st.session_state.ollama_response = resp
        st.session_state.ollama_duration = dur
        st.session_state.ollama_prompt = prompt

        if not resp.strip():
            st.warning("⚠️ Received empty response.")
        else:
            st.markdown(f"**Response (in {dur} seconds):**")
            st.markdown(resp)


def tag_code_block_multi(row):
    name = row['signature'].lower()
    file = row['file_path'].lower()
    tags = []

    if any(kw in name or kw in file for kw in ['auth', 'token', 'login', 'signup']):
        tags.append('auth')
    if any(kw in name or kw in file for kw in ['db', 'sql', 'database', 'query']):
        tags.append('database')
    if any(kw in name or kw in file for kw in ['util', 'helper', 'tool', 'misc']):
        tags.append('utils')
    if any(kw in name or kw in file for kw in ['api', 'route', 'endpoint']):
        tags.append('api')
    if any(kw in name or kw in file for kw in ['test', 'mock']):
        tags.append('test')

    if not tags:
        tags.append('other')

    return ", ".join(tags)


def tabs(default_tabs=[], default_active_tab=0):
    if not default_tabs:
        return None

    # Use a key to persist tab across reruns
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = default_active_tab

    active_tab = st.radio(
    "Navigation",  # 🔒 Non-empty for accessibility
    default_tabs,
    index=st.session_state.active_tab,
    key="tab_radio",
    label_visibility="collapsed"  # 👁️ Hides it from UI, keeps it accessible
)
    # Update active_tab in session state immediately
    st.session_state.active_tab = default_tabs.index(active_tab)
    child = st.session_state.active_tab + 1

    st.markdown(f"""
        <style>
        div[role="radiogroup"] {{
            border-bottom: 2px solid rgba(49, 51, 63, 0.1);
            flex-direction: unset;
        }}
        div[role="radiogroup"] > label > div:first-of-type {{
            display: none;
        }}
        div[role="radiogroup"] label {{
            padding-bottom: 0.5em;
            border-radius: 0;
            position: relative;
            top: 3px;
        }}
        div[role="radiogroup"] label .st-fc {{
            padding-left: 0;
        }}
        div[role="radiogroup"] label:hover p {{
            color: red;
        }}
        div[role="radiogroup"] label:nth-child({child}) {{
            border-bottom: 2px solid rgb(255, 75, 75);
        }}
        div[role="radiogroup"] label:nth-child({child}) p {{
            color: rgb(255, 75, 75);
            padding-right: 0;
        }}
        </style>
    """, unsafe_allow_html=True)

    return active_tab
