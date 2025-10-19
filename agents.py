from langchain.agents import create_agent

from llms import get_gmail_model
from gmail_tools import gmail_tools


mail_agent = create_agent(
    model=get_gmail_model(),
    tools=gmail_tools,
)