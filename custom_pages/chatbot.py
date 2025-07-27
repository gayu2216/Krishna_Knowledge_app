# pages/chatbot.py - Fixed Chatbot page module
import os
import streamlit as st
from dotenv import load_dotenv
import traceback

# LangChain imports
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

# Load environment variables
load_dotenv()

# Initialize components (only once to avoid reloading)
@st.cache_resource
def initialize_rag_components():
    """Initialize RAG components with caching to improve performance"""
    
    try:
        # Initialize Embeddings
        embedding_model = os.getenv("EMBEDDING_MODEL")
        if not embedding_model:
            raise ValueError("EMBEDDING_MODEL not set in environment")
        
        embeddings = OllamaEmbeddings(model=embedding_model)
        
        # Initialize Vector Store
        vector_store = Chroma(
            collection_name=os.getenv("COLLECTION_NAME", "default_collection"),
            embedding_function=embeddings,
            persist_directory=os.getenv("DATABASE_LOCATION", "./chroma_db")
        )
        
        # Test vector store
        test_results = vector_store.similarity_search("test", k=1)
        
        # Initialize Chat Model
        llm = init_chat_model(
            os.getenv("CHAT_MODEL", "llama3"),
            model_provider=os.getenv("MODEL_PROVIDER", "ollama"),
            temperature=0
        )
        
        # Test LLM connection
        try:
            test_response = llm.invoke("Hello")
        except Exception as e:
            raise
        
        # Updated Prompt Template - using ChatPromptTemplate for better compatibility
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant with knowledge about Krishna and Hindu philosophy. 
            You have access to a retrieval tool to search for relevant information.
            
            When a user asks a question:
            1. Use the retrieve tool to find relevant information
            2. Based on the retrieved information, provide a comprehensive answer
            3. Always start your answer with "Hare Krishna...."
            4. If you don't find relevant information, say "I don't know" and don't provide a source
            5. Do not show the raw tool calls or JSON - only provide the final answer
            6. Cite the source
            
            Remember to actually execute the tool and use its results in your response."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Retriever Tool - with error handling
        @tool
        def retrieve(query: str) -> str:
            """Retrieve information related to a query about Krishna and Hindu philosophy."""
            try:
                retrieved_docs = vector_store.similarity_search(query, k=3)
                if not retrieved_docs:
                    return "No relevant information found in the knowledge base."
                
                result = "\n\n".join(
                    f"Source: {doc.metadata.get('source', 'unknown')}\nContent: {doc.page_content}" 
                    for doc in retrieved_docs
                )
                return result
            except Exception as e:
                return f"Error retrieving information: {str(e)}"
        
        tools = [retrieve]
        
        # Create Agent with error handling
        try:
            agent = create_tool_calling_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=tools, 
                verbose=False,  # Disable verbose to prevent raw output
                max_iterations=5,  # Increase iterations to allow proper tool execution
                max_execution_time=60,  # Increase timeout
                return_intermediate_steps=False,  # Don't return intermediate steps
                handle_parsing_errors=True  # Handle parsing errors gracefully
            )
            
            return agent_executor
            
        except Exception as e:
            raise
            
    except Exception as e:
        raise

def apply_chat_styling():
    """Apply styling specific to chat interface"""
    st.markdown("""
    <style>
    [data-testid="chat-message"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 15px !important;
        border-radius: 10px !important;
        margin: 10px 0 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    [data-testid="chat-message"] div {
        color: black !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        line-height: 1.5 !important;
    }
    .stChatInput {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 10px !important;
    }
    .stChatMessage, .stChatMessage * {
        color: black !important;
    }
    .chat-container {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def show_chatbot_page():
    """Main chatbot page function"""
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Apply chat-specific styling
    apply_chat_styling()
    
    # Page header
    st.title("💬 Any Questions?")
    st.markdown("Ask me anything about Lord Krishna, Hindu philosophy, or spiritual guidance!")
    

    
    # Initialize RAG components
    try:
        agent_executor = initialize_rag_components()
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {str(e)}")
        st.error("Please check your environment configuration and Ollama service.")
        st.markdown("**Troubleshooting steps:**")
        st.markdown("1. Ensure Ollama is running: `ollama serve`")
        st.markdown("2. Check if your models are available: `ollama list`")
        st.markdown("3. Verify your .env file has all required variables")
        st.markdown("4. Check if the Chroma database exists and is accessible")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Chat interface container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        # Add welcome message
        welcome_msg = AIMessage("Hare Krishna! 🙏 I'm here to help you learn about Lord Krishna and Hindu philosophy. Ask me anything!")
        st.session_state.chat_messages.append(welcome_msg)
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
            st.markdown(
                f'<div style="color: black; font-weight: 500; background-color: rgba(255,255,255,0.9); padding: 10px; border-radius: 5px;">{message.content}</div>',
                unsafe_allow_html=True
            )
    
    # Chat input
    user_question = st.chat_input("Ask me about Krishna, philosophy, or spiritual guidance...")
    
    if user_question:
        # Add user message to chat
        user_msg = HumanMessage(user_question)
        st.session_state.chat_messages.append(user_msg)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(
                f'<div style="color: black; font-weight: 500; background-color: rgba(255,255,255,0.9); padding: 10px; border-radius: 5px;">{user_question}</div>',
                unsafe_allow_html=True
            )
        
        # Generate AI response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            try:
                # Show progress
                response_placeholder.markdown("🤔 Thinking...")
                
                # Simple chat history formatting
                chat_history_str = ""
                for msg in st.session_state.chat_messages[:-1]:  # Exclude the just-added message
                    role = "Human" if isinstance(msg, HumanMessage) else "Assistant"
                    chat_history_str += f"{role}: {msg.content}\n"
                
                # Get response from agent with timeout
                
                result = agent_executor.invoke({
                    "input": user_question
                })
                
                ai_response = result.get("output", "No response generated")
                
                # Clean up any remaining tool call artifacts
                if "retrieve" in ai_response and "{" in ai_response:
                    ai_response = "Hare Krishna! I apologize, but I'm having trouble processing your question. Please try asking in a different way."
                
                # Ensure response starts with "Hare Krishna" if it doesn't
                if not ai_response.startswith("Hare Krishna"):
                    ai_response = f"Hare Krishna! {ai_response}"
                
                # Display AI response
                response_placeholder.markdown(
                    f'<div style="color: black; font-weight: 500; background-color: rgba(255,255,255,0.9); padding: 10px; border-radius: 5px;">{ai_response}</div>',
                    unsafe_allow_html=True
                )
                
                # Add AI message to chat history
                ai_msg = AIMessage(ai_response)
                st.session_state.chat_messages.append(ai_msg)
                
            except Exception as e:
                error_msg = f"Hare Krishna! I apologize, but I encountered an error: {str(e)}"
                
                response_placeholder.markdown(
                    f'<div style="color: red; font-weight: 500; background-color: rgba(255,255,255,0.9); padding: 10px; border-radius: 5px;">{error_msg}</div>',
                    unsafe_allow_html=True
                )
                
                st.session_state.chat_messages.append(AIMessage(error_msg))
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar with chat info
    with st.sidebar:
        st.header("📊 Chat Statistics")
        
        # Chat statistics
        if len(st.session_state.chat_messages) > 1:  # Exclude welcome message
            human_msgs = [m for m in st.session_state.chat_messages if isinstance(m, HumanMessage)]
            st.metric("Questions Asked", len(human_msgs))
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_messages = [
                AIMessage("Hare Krishna! 🙏 I'm here to help you learn about Lord Krishna and Hindu philosophy. Ask me anything!")
            ]
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)