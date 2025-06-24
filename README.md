# Verifying Agent Pipeline Updater (VAPU)
Multi-agent system designed for updating existing code based on the provided code and project requirements.

## Running prerequisites:
1) Python 3.10 (Can work in other versions, not tested)
2) API key for an LLM service provider

## Running instructions for multi-agent pipeline:
1) Add API key, LLM model and URL in pipeline.py
2) Write project requirements to project/project_requirements.txt or an alternative file
3) Execute pipeline.py
4) Select 'p' for pipeline
5) Enter file path to original code file
6) Enter output file
7) Enter a possible alternative file for project requirements
8) Wait for the system to write code to the output file


## Running Instuctions for testing the connection to provider:
1) Add API key, LLM model and URL in pipeline.py
2) Write a prompt in project/prompt.txt or an alternative file
3) Execute pipeline.py
4) Select 'n' for prompt
5) Enter file path to original code file
6) Enter output file
7) Enter a possible alternative file for project requirements
8) Wait until the test code is written to the output file

