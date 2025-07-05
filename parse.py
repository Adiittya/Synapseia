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
token = "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"  # 🔒 Replace this with your GitHub PAT
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

st.title("🔍 GitHub Code Structure Scanner")

repo_url = st.text_input("Paste GitHub Repository URL", placeholder="https://github.com/user/repo")

if repo_url:
    parts = repo_url.strip().rstrip("/").split("/")
    if len(parts) >= 2 and parts[-1] and parts[-2]:
        user, repo = parts[-2], parts[-1]
    else:
        st.error("❌ Invalid GitHub URL. Please use format: https://github.com/user/repo")
        st.stop()

    if "scanned_repo" not in st.session_state or st.session_state.scanned_repo != repo_url:
        with st.spinner("🔍 Scanning repository..."):
            repo_tree = get_repo_tree(user, repo)
            st.session_state.repo_tree = repo_tree

            file_paths = [f["path"] for f in repo_tree if os.path.splitext(f["path"])[1] in ext_map]
            st.session_state.file_paths = file_paths


            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = executor.map(lambda path: process_file(path, user, repo), file_paths)
                for r in futures:
                    results.extend(r)

            df_structure = pd.DataFrame(results, columns=["file_path", "language", "type", "signature", "content"])
            df_structure.drop_duplicates(subset=["file_path", "language", "type", "signature"], inplace=True)

            def tag_code_block_multi(row):
                name = row['signature'].lower()
                file = row['file_path'].lower()
                tags = []
                if any(kw in name or kw in file for kw in ['auth', 'token', 'login', 'signup']): tags.append('auth')
                if any(kw in name or kw in file for kw in ['db', 'sql', 'database', 'query']): tags.append('database')
                if any(kw in name or kw in file for kw in ['util', 'helper', 'tool', 'misc']): tags.append('utils')
                if any(kw in name or kw in file for kw in ['api', 'route', 'endpoint']): tags.append('api')
                if any(kw in name or kw in file for kw in ['test', 'mock']): tags.append('test')
                if not tags: tags.append('other')
                return ", ".join(tags)

            df_structure["tags"] = df_structure.apply(tag_code_block_multi, axis=1)

            st.session_state.df_structure = df_structure
            st.session_state.scanned_repo = repo_url
    else:
        df_structure = st.session_state.df_structure
        repo_tree = st.session_state.repo_tree
        file_paths = st.session_state.file_paths

    # === Tabs Layout ===
    tab_labels = ["📋 Code Structure", "🔍 Search & Filter", "💬 Q&A & Tracing"]
    tabs = st.tabs(tab_labels)
    if "active_tab_index" not in st.session_state:
        st.session_state.active_tab_index = 0

    
    for i, tab in enumerate(tabs):
        with tab:
            st.session_state.active_tab_index = i
            if i == 0:
                    st.subheader("Repository Summary")
                    st.markdown(f"**Repository:** `{user}/{repo}`")
                    st.markdown(f"**Files Parsed:** `{len(df_structure['file_path'].unique())}`")
                    st.markdown(f"**Languages Detected:** `{', '.join(df_structure['language'].unique())}`")

                    st.markdown("### Repository Tree")
                    tree = build_tree(file_paths)
                    with st.expander("📂 Repository Tree"):
                        st.code("\n".join(get_tree_string(tree)), language="text")


                    st.markdown("### Code Structure and Tags")

                    inner_tab1 = st.tabs(["Filter by Tags"])


                    available_tags = df_structure["tags"].str.split(", ").explode().unique().tolist()
                    selected_tags = st.multiselect("Select tags to filter", available_tags)

                    if selected_tags:
                        filtered_df = df_structure[df_structure["tags"].apply(lambda x: any(tag in x for tag in selected_tags))]
                    else:
                        filtered_df = df_structure

                    st.dataframe(filtered_df[["file_path", "language", "type", "signature", "tags"]], use_container_width=True)


    # === Tab 2: Tagged Code Blocks 

    # === Tab 3: Search and Filter ===
            elif i == 1:
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


    # === Tab 4: Q&A and Function Tracing ===
            elif i == 2:
                    st.subheader("🔎 Trace Function Usages")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        prev_files = st.session_state.get("selected_files", [])

                        files = st.multiselect(
                            "Select files",
                            df_structure["file_path"].unique().tolist(),
                            default=prev_files
                        )

                        # If file selection changed, clear selected functions
                        if set(files) != set(prev_files):
                            st.session_state.selected_functions = []
                            st.session_state.traced_usages = []


                        # Update file selection in session
                        st.session_state.selected_files = files


                    with col2:
                        s_df = df_structure[df_structure["file_path"].isin(files)] if files else df_structure
                        funcs = s_df[s_df["type"] == "function"]["signature"].tolist()
                        selected_funcs = st.multiselect(
                            "Select functions",
                            funcs,
                            default=st.session_state.selected_functions
                        )
                        st.session_state.selected_functions = selected_funcs


                    if st.button("🔍 Trace Usages"):
                        if not selected_funcs:
                            st.warning("Please select at least one function.")
                        else:
                            st.session_state.selected_functions = selected_funcs
                            traced = find_function_usages_in_df(df_structure, [f.split("(")[0] for f in selected_funcs])

                            if traced:
                                # ✅ Deduplicate traced results
                                unique_traced = sorted(set((func, file) for func, file in traced))
                                st.session_state.traced_usages = unique_traced
                                st.success(f"{len(unique_traced)} unique usage(s) found.")
                            else:
                                st.warning("No usages found in the repository.")
                                st.session_state.traced_usages = []  # Optional: clear old if no new result

                    # ✅ Display only once, always from session
                    if st.session_state.traced_usages:
                        st.markdown("### Traced Usages")
                        st.dataframe(
                            pd.DataFrame(
                                st.session_state.traced_usages,
                                columns=["Function", "Used In File"]
                            ),
                            use_container_width=True
                        )



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
                        if st.session_state.ollama_response:
                            st.markdown("### 💡 Last Ollama Response")
                            with st.expander("📜 Prompt Used"):
                                st.code(st.session_state.ollama_prompt, language="text")
                            st.success(st.session_state.ollama_response)
                            st.caption(f"⏱️ Took {st.session_state.ollama_duration} seconds")

                        if not is_ollama_running():
                            st.error("❌ Ollama is not running. Please start the Ollama server.")
                        else:
                            with st.spinner("💭 Ollama is thinking..."):
                                selected_paths = files if files else file_paths
                                context = generate_file_contents_summary(selected_paths, df_structure)


                                if files:
                # Prompt when specific files are selected
                                    prompt = f"""
                                You are a senior software engineer helping analyze a subset of files from a codebase.

                                Here is the context for the selected file(s):

                                {context}

                                Based on the selected file(s), answer the following question:
                                {user_q.strip()}
                                """.strip()
                                else:
                                    # Prompt when full repo structure (tree) is used
                                    prompt = f"""
                                You are a codebase expert analyzing the entire repository.

                                Below is the full project structure with summaries:

                                {context}

                                Use the complete context to answer the following question intelligently:
                                {user_q.strip()}
                                """.strip()


                                try:
                                    print(prompt)
                                    resp, dur = ollama_explain_code(prompt)
                                    st.session_state.ollama_response = resp
                                    st.session_state.ollama_duration = dur
                                    st.session_state.ollama_prompt = prompt


                                    if not resp.strip():
                                        st.warning("⚠️ Received an empty response from Ollama.")
                                    else:
                                        st.markdown(f"**Response (in {dur} seconds):**")
                                        st.markdown(resp)
                                except Exception as e:
                                    st.error(f"💥 Ollama failed: {e}")
