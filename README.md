# Multi-agent pipeline
Multi-agent system designed for updating existing code based on the provided code and project requirements.

## Running prerequisites:
Python 3.10 (Can work in other versions, not tested)
API key for a LLM service provider

## Running Instuctions for multi-agent pipeline:
1) Add API key and LLM model and URL in pipeline.py
2) Write project requirements to project/project_requirements.txt or an alternative file
3) Execute pipeline.py
4) Select p for pipeline
5) Enter filepath to orignal code file
6) Enter Output file
7) Enter possible alternative file for project requirements


## Running Instuctions for testing the connection to provider:
1) Add API key and LLM model and URL in pipeline.py
2) Write a prompt in project/prompt.txt or an alternative file
3) Execute pipeline.py
4) Select n for prompt
5) Enter filepath to orignal code file
6) Enter Output file
7) Enter possible alternative file for project requirements
