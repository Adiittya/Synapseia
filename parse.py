# GitHub Code Structure Scanner with Ollama-Powered QA

import requests
import re
import os
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
import ollama
import time

# --- Utility: Check Ollama Running ---
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
            files = get_repo_tree(user, repo)
            print(files)
            code_files = [f["path"] for f in files if os.path.splitext(f["path"])[1] in ext_map]

            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = executor.map(lambda p: process_file(p, user, repo), code_files)
                for r in futures:
                    results.extend(r)

            df_structure = pd.DataFrame(results, columns=["file_path", "language", "type", "signature", "content"])

            df_structure.drop_duplicates(subset=["file_path", "language", "type", "signature"], inplace=True)

            
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


            df_structure['tags'] = df_structure.apply(tag_code_block_multi, axis=1)

            df_structure.drop_duplicates(subset=["file_path", "language", "type", "signature"], inplace=True)

            st.session_state.df_structure = df_structure
            st.session_state.scanned_repo = repo_url
    else:
        df_structure = st.session_state.df_structure

    

    # --- Sidebar Filters ---
    st.sidebar.title("🔍 Search Filter")
    search_query = st.sidebar.text_input("Search keyword", key="search_query")
    selected_type = st.sidebar.selectbox("Structure type", ["", "function", "class", "variable", "import"])
    file_filter = st.sidebar.text_input("File name filter", key="file_filter")

    # --- Filtered Data ---
    filtered_df = search_code(df_structure, search_query, selected_type if selected_type else None, file_filter)
    st.subheader("🔎 Search Results")
    st.write(f"Results: {len(filtered_df)}")
    st.dataframe(filtered_df.drop_duplicates(subset=["file_path"]), use_container_width=True)


    
    st.subheader("📌 Auto-Grouped Tags")


    # Step 4: Show one consolidated table with tags
    st.subheader("📋 Code Structure with Tags")
    st.dataframe(df_structure[["file_path", "language", "type", "signature", "tags"]], use_container_width=True)



    repo_tree = get_repo_tree(user, repo)
    file_paths = [item["path"] for item in repo_tree]  

    # --- File Selector ---
    st.markdown("## 📂 Select Files to Analyze or Ask About")
    selected_files = st.multiselect(
        "Choose specific files (or leave empty to include all):",
        options=df_structure["file_path"].unique().tolist(),
        key="selected_files"
    )
    selected_df = df_structure[df_structure["file_path"].isin(selected_files)] if selected_files else df_structure

    if selected_files:
        print("📂 Selected files:")
        for path in selected_files:
            print(f"➡️ {path}")
        
        print("\n🧠 Parsed entries from df_structure:")
        print(selected_df[["file_path", "type", "signature"]].to_string(index=False))


    # --- Ask Questions ---
    st.markdown("## 💬 Ask Questions About Codebase")
    question = st.text_input("Enter your question (e.g. 'What is the role of utils.py?')", key="code_question")
    
    st.markdown("## 🕵️‍♂️ Choose Functions to Trace")

    func_options = selected_df[selected_df["type"] == "function"]["signature"].tolist()
    selected_func_names = st.multiselect("Select functions to trace", func_options)

    if st.button("🔎 Trace Selected Functions"):
        selected_functions = [s.split("(")[0] for s in selected_func_names]

        if not selected_functions:
            st.info("No functions found in selected files.")
        else:
            # 🛠 Fix missing 'content' column if needed
            if "content" not in df_structure.columns:
                with st.spinner("Fetching missing file contents..."):
                    def load_content(path):
                        try:
                            return get_file_raw(user, repo, path)
                        except:
                            return ""
                    df_structure["content"] = df_structure["file_path"].apply(load_content)

            with st.spinner("Searching for function calls..."):
                usage_data = find_function_usages_in_df(df_structure, selected_functions)

                if not usage_data:
                    st.warning("No usages found across repo.")
                else:
                    usage_df = pd.DataFrame(usage_data, columns=["Function", "Used In File"])
                    st.dataframe(usage_df.drop_duplicates(), use_container_width=True)


    if st.button("🧠 Ask with Ollama") and question.strip():
        if not is_ollama_running():
            st.error("❌ Ollama is not running. Please start with `ollama serve`.")
        else:
            if selected_files:
                code_context = selected_df.to_string(index=False)
                file_overview = f"Selected File Code Structure:\n{code_context}"
            else:
                file_paths = [item["path"] for item in get_repo_tree(user, repo)]
                tree = build_tree(file_paths)
                tree_string = "\n".join(get_tree_string(tree))
                file_overview = f"Full Repository File Tree:\n{tree_string}"

            prompt = f"""You are an expert code analyst.

    {file_overview}

    Now answer this question clearly: {question}
    """
            response, dur = ollama_explain_code(prompt)
            st.markdown("### 💡 Ollama's Answer")
            st.write(response)
            if dur:
                st.caption(f"🕒 Answered in {dur} seconds")


#working code