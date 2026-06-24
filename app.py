import streamlit as st
import anthropic
import chromadb
import docx
import io

st.set_page_config(page_title="Onboarding Concierge", page_icon="🏢", layout="wide")

st.title("🏢 Onboarding Concierge")
st.caption("Your AI-powered guide for new hire questions — powered by your company documents")

# ── API Key ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        st.success("API key loaded from secrets ✓")
    except Exception:
        api_key = st.text_input("Anthropic API Key", type="password",
                                help="Get yours at console.anthropic.com")

    st.markdown("---")

    # ── Company name ─────────────────────────────────────────────────────────
    st.subheader("🏢 Company Setup")
    company_name = st.text_input(
        "Company Name",
        value=st.session_state.get("company_name", ""),
        placeholder="e.g. Acme Corp",
    )
    if company_name:
        st.session_state["company_name"] = company_name
    hr_contact = st.text_input(
        "HR Email (for fallback answers)",
        value=st.session_state.get("hr_contact", ""),
        placeholder="hr@yourcompany.com",
    )
    if hr_contact:
        st.session_state["hr_contact"] = hr_contact

    st.markdown("---")

    # ── Document upload ───────────────────────────────────────────────────────
    st.subheader("📂 Upload Onboarding Documents")
    st.caption(
        "Suggested documents:\n"
        "- Employee handbook\n"
        "- IT setup guide\n"
        "- Benefits guide\n"
        "- Leave policy\n"
        "- First week schedule\n"
        "- Who's who directory\n"
        "- New hire FAQ"
    )
    uploaded_docs = st.file_uploader(
        "Select DOCX files", type=["docx"], accept_multiple_files=True
    )

    if uploaded_docs and st.button("🔄 Build Knowledge Base", type="primary"):
        with st.spinner("Processing onboarding documents …"):

            def extract_text_from_docx(file_bytes: bytes) -> str:
                document = docx.Document(io.BytesIO(file_bytes))
                return "\n".join(
                    p.text for p in document.paragraphs if p.text.strip()
                )

            all_chunks, all_metadata = [], []

            for doc_file in uploaded_docs:
                text = extract_text_from_docx(doc_file.read())
                if not text.strip():
                    st.warning(f"No text extracted from {doc_file.name} — skipping.")
                    continue
                words = text.split()
                for i in range(0, len(words), 200):
                    chunk = " ".join(words[i : i + 200])
                    if chunk:
                        all_chunks.append(chunk)
                        all_metadata.append({"source": doc_file.name})

            if all_chunks:
                client = chromadb.Client()
                try:
                    client.delete_collection("onboarding")
                except Exception:
                    pass
                collection = client.create_collection("onboarding")

                for i in range(0, len(all_chunks), 50):
                    batch = all_chunks[i : i + 50]
                    meta = all_metadata[i : i + 50]
                    ids = [str(j) for j in range(i, i + len(batch))]
                    collection.add(documents=batch, metadatas=meta, ids=ids)

                st.session_state["collection"] = collection
                st.session_state["messages"] = []
                st.success(
                    f"✓ {collection.count()} chunks loaded from "
                    f"{len(uploaded_docs)} document(s)"
                )
                st.rerun()
            else:
                st.error("No text could be extracted from the uploaded documents.")

    if st.session_state.get("collection"):
        if st.button("🗑️ Clear Chat History"):
            st.session_state["messages"] = []
            st.rerun()

# ── Initialise session state ─────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Main area ────────────────────────────────────────────────────────────────
if not api_key:
    st.warning("👈 Enter your Anthropic API key in the sidebar to get started.")
    st.stop()

company = st.session_state.get("company_name", "your company")
hr_email = st.session_state.get("hr_contact", "HR")

if "collection" not in st.session_state:
    st.info(
        "👈 Upload your company onboarding documents (DOCX) in the sidebar "
        "and click **Build Knowledge Base** to get started.\n\n"
        "Once loaded, new hires can ask questions like:\n"
        "- *When do I get my laptop?*\n"
        "- *What is my annual leave entitlement?*\n"
        "- *How do I claim medical expenses?*\n"
        "- *Who do I contact for IT support?*"
    )
    st.stop()

st.success(f"💬 Ready to answer questions about joining {company}!")

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
placeholder = f"Ask anything about joining {company} …"
if question := st.chat_input(placeholder):
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Looking through your onboarding documents …"):
            collection = st.session_state["collection"]
            results = collection.query(query_texts=[question], n_results=4)

            context = ""
            sources = []
            for doc_chunk, metadata in zip(
                results["documents"][0], results["metadatas"][0]
            ):
                context += f"\n---\n{doc_chunk}"
                sources.append(metadata["source"])

            claude = anthropic.Anthropic(api_key=api_key)
            response = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=800,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"You are a friendly onboarding assistant for {company}. "
                            "Answer the new hire's question using ONLY the context provided. "
                            "Be warm, welcoming, and concise. "
                            f"If the answer is not in the context, say so and suggest the "
                            f"new hire contact {hr_email} for help.\n\n"
                            f"Context:\n{context}\n\n"
                            f"Question: {question}"
                        ),
                    }
                ],
            )

            answer = response.content[0].text
            st.markdown(answer)

            unique_sources = sorted(set(sources))
            st.caption(f"📄 Sources: {' · '.join(unique_sources)}")

            st.session_state["messages"].append(
                {"role": "assistant", "content": answer}
            )
