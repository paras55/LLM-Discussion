import streamlit as st
from openai import OpenAI
from groq import Groq
import os
import requests

# Streamlit app title
st.title("3-Agent LLM Discussion with Contextual Memory and Dynamic Interaction")

# Sidebar for API keys and settings
st.sidebar.header("Settings")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
groq_api_key = st.sidebar.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
turns = st.sidebar.slider("Number of Turns", min_value=1, max_value=10, value=3)

# Initialize API clients
if openai_api_key and groq_api_key:
    openai_client = OpenAI(api_key=openai_api_key)
    groq_client = Groq(api_key=groq_api_key)
else:
    st.error("Please provide both OpenAI and Groq API keys in the sidebar.")
    st.stop()

# Define agents
agents = [
    {"name": "Alex (GPT-3.5)", "client": openai_client, "model": "gpt-3.5-turbo"},
    {"name": "Luna (LLaMA)", "client": groq_client, "model": "llama3-70b-8192"},
    {"name": "Gina (GPT-4o)", "client": openai_client, "model": "gpt-4o"}
]

def web_search(query):
    """Improved web search using SerpAPI."""
    try:
        api_key = os.getenv("SERPAPI_KEY", "")  # Store this key as an environment variable
        if not api_key:
            return "Search failed: SERPAPI_KEY not provided."

        # SerpAPI endpoint
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key
        }

        # Make the request
        response = requests.get(url, params=params)
        data = response.json()

        # Parse the response
        if "organic_results" in data:
            results = data["organic_results"]
            search_summary = ""
            for result in results[:2]:  # Get the top 2 results
                title = result.get("title", "No title")
                link = result.get("link", "No link")
                snippet = result.get("snippet", "No description")
                search_summary += f"**[{title}]({link})**\n{snippet}\n\n"

            return search_summary or "No relevant search results found."
        else:
            return "No search results found."

    except Exception as e:
        return f"Search failed: {str(e)}"

def get_response(agent, chat_history, topic):
    """Generate a response with enhanced contextual memory and dynamic interaction."""
    system_prompt = (
        f"You are {agent['name']}, an AI participating in a group discussion. "
        f"Your role is to actively engage in the conversation, build on previous arguments, ask questions, "
        f"and challenge or support other agents' points of view. "
        f"Maintain the context and keep the discussion cohesive. "
        f"Topic: '{topic}'. Chat history:\n\n{chat_history}\n\n"
        f"Respond concisely (2-3 sentences) and contribute to the flow of discussion. "
        f"You can also ask relevant questions to other agents or propose alternative perspectives. "
        f"To fetch web info, start your message with 'SEARCH: <query>' (e.g., 'SEARCH: Nvidia AI market share')."
    )

    try:
        if agent["client"] == openai_client:
            response = agent["client"].chat.completions.create(
                model=agent["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "What do you think?"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            text = response.choices[0].message.content.strip()
        else:  # Groq client
            response = agent["client"].chat.completions.create(
                model=agent["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "What do you think?"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            text = response.choices[0].message.content.strip()

        # Handle web search if requested
        if text.startswith("SEARCH:"):
            query = text.split("SEARCH:")[1].strip()
            search_result = web_search(query)
            return f"{agent['name']} searched '{query}': {search_result}\nThen said: {text[len('SEARCH: ' + query):].strip() or 'Interesting info!'}"
        return text
    except Exception as e:
        return f"Error: {str(e)}"

# Main app logic
st.header("Start a Contextual Discussion")
topic = st.text_input("Enter a topic for the agents to discuss:")

if st.button("Start Discussion"):
    if not topic:
        st.warning("Please enter a topic!")
    else:
        # Initialize chat history
        chat_history = f"Discussion Topic: {topic}\n\n"
        st.subheader("Discussion")
        st.write(f"**Topic**: {topic}")

        # Run discussion with expandable sections per turn
        for turn in range(turns):
            with st.expander(f"Turn {turn + 1}", expanded=(turn == 0)):  # Expand first turn by default
                turn_history = ""
                for agent in agents:
                    with st.spinner(f"{agent['name']} is thinking..."):
                        response = get_response(agent, chat_history, topic)
                        turn_history += f"**{agent['name']}**: {response}\n\n"
                        chat_history += f"{agent['name']}: {response}\n"
                    st.markdown(f"**{agent['name']}**: {response}")
                # Store turn history in session state for reference (optional)
                if "turn_history" not in st.session_state:
                    st.session_state.turn_history = {}
                st.session_state.turn_history[turn] = turn_history

        st.success("Discussion concluded!")

# Instructions
st.sidebar.markdown("""
### How to Use
1. Enter your OpenAI, Groq, and SerpAPI keys.
2. Set the number of turns.
3. Input a topic and click "Start Discussion".
4. Expand each turn to see the agents' responses!
5. Agents can use 'SEARCH: <query>' to fetch web info.
""")
