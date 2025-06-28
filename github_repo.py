import requests
import streamlit as st
import ollama
import os

client = ollama.Client()

# --- GitHub Auth ---
token = "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"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "SYNAPSEIA"
}

st.set_page_config(layout="wide")
st.title("🧠 SYNAPSEIA GitHub Assistant")

def extract_extensions(paths):
    extensions = set()
    for path in paths:
        ext = os.path.splitext(path)[1]
        if ext:
            extensions.add(ext)
    return sorted(list(extensions))


@st.cache_data
def get_tree(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/git/trees/HEAD?recursive=1"
    res = requests.get(url, headers=headers)
    tree = res.json().get("tree", [])
    return [item for item in tree if item["type"] == "blob"]

@st.cache_data
def get_file_raw(user, repo, path):
    url = f"https://raw.githubusercontent.com/{user}/{repo}/HEAD/{path}"
    return requests.get(url).text

def initialize_data(file_paths, content, query, selected_file, model_name):
    tree_snippet = "\n".join(file_paths[:50])
    system_prompt = f"""You are SYNAPSEIA, a code analysis expert... \n{tree_snippet}"""
    full_prompt = f"""### File path:\n{selected_file}\n\n### File content:\n{content}\n\n### User question:\n{query}"""

    response = client.chat(model=model_name, messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_prompt}
    ])
    st.markdown("### 🤖 Response")
    st.write(response['message']['content'])

# --- Input GitHub URL ---
repo_url = st.text_input("📎 Paste GitHub repo URL", "https://github.com/Adiittya/Finbuddy")

if repo_url:
    try:
        user, repo = repo_url.strip().split("/")[-2:]
        file_list = get_tree(user, repo)
        file_paths = [item["path"] for item in file_list]

        # --- Dynamic extension filter ---
        extensions = extract_extensions(file_paths)
        extensions = [".all"] + extensions
        file_ext = st.sidebar.selectbox("🧾 Filter by extension", extensions)
        if file_ext != ".all":
            file_paths = [f for f in file_paths if f.endswith(file_ext)]    
        # --- Smart search ---
        search = st.sidebar.text_input("🔍 Search filename")
        if search:
            file_paths = [f for f in file_paths if search.lower() in f.lower()]

        # --- File select ---
        selected_file = st.sidebar.selectbox("📄 Select a file", sorted(file_paths))

        # --- Model selector ---
        model_name = st.sidebar.selectbox("🧠 Choose model", ["llama3.2", "llama2", "codellama"])

        if selected_file:
            content = get_file_raw(user, repo, selected_file)
            file_size_kb = len(content.encode("utf-8")) / 1024
            st.subheader(f"📄 `{selected_file}` ({file_size_kb:.2f} KB)")

            if file_size_kb > 200:
                st.warning("⚠️ Large file — only partial content shown")

            with st.expander("📝 File content preview", expanded=True):
                st.code(content[:3000], language="python")  # You can add language detection later

            # --- User Query ---
            query = st.text_area("💬 Ask something about this file")
            if st.button("Ask AI"):
                with st.spinner("⏳ Processing..."):
                    initialize_data(file_paths, content[:8000], query, selected_file, model_name)
    except Exception as e:
        st.error(f"❌ Error: {e}")
