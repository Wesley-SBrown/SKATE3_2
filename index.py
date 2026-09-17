# index.py

"""
Main entry point for python cloudflare worker
Handles HTTP requests
"""
from js import Response

async def on_fetch(request, env, ctx):
    NEO4J_URI = env.NEO4J_URI
    NEO4J_PASSWORD = env.NEO4J_PASSWORD

    return Response.new("Hello from Worker!")
