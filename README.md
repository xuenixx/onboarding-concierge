# Onboarding Concierge

An AI-powered Q&A bot that answers new hire questions using company onboarding documents, built with Claude API and ChromaDB.

## What it does
New hires ask questions in plain language and get warm, accurate answers cited from company documents — without needing to search through handbooks manually.

## Sample questions it can answer
- When do I get my laptop?
- What is my annual leave entitlement?
- How do I claim medical expenses?
- Who do I contact for IT support?
- What should I do if I feel sick on a workday?

## Tech stack
- Python
- Anthropic Claude API (claude-haiku-4-5)
- ChromaDB (vector database)
- python-docx (document extraction)
- Google Colab

## Demo corpus
Built on fictional Xuenix Entertainment onboarding documents including Employee Handbook, IT Setup Guide, Benefits Guide, Who's Who, First Week Schedule, and New Hire FAQ — all set in Singapore context.

## Known limitations
- Requires Google Colab session to run
- ChromaDB resets on session restart
- Low chunk count (12) due to document conversion — expandable with richer source docs
