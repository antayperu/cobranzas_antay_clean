import os
import notion_client
from notion_client import Client

client = Client(auth="dummy")
print(f"Type of client.databases: {type(client.databases)}")
print(f"Methods of client.databases: {dir(client.databases)}")
