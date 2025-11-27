import os
import json
import requests
import time
import copy

# Write necessary global parameters below:

API_KEY = ''  # Write API key for OpenAI or an alternative service
URL = 'https://api.openai.com/v1/chat/completions'  # Write the URL for the provider service
FEEDBACK_DEPTH = 2 # The maximum feedback loop between a verifier and a finalizer agent
LOG = True # Prints the phase of the update during the execution

""" Headers; add more parameters if needed ex. effort"""
HEADERS = {
        'Authorization': 'Bearer ' + API_KEY,
        'Content-Type': 'application/json',
    } 

""" Template payload; add more parameters if needed ex. effort"""
PAYLOAD_TEMPLATE = {
        'model': "gpt-4o-mini", # Write LLM model version for the agents
        'messages': [],
        'temperature': 0 # Recommended temperature default setting
    } 


def get_tasks(project_description):
    """ Get tasks from a manager agent"""
    conversation_history = []

    # Step 1: Send Manager Prompt
    if LOG:
        print("Creating tasks...")
    with open('agents/manager.txt') as f:
        manager_prompt = f.read().replace("PROJECT_DESCRIPTION", project_description)

    conversation_history.append({"role": "system", "content": manager_prompt})

    payload = copy.deepcopy(PAYLOAD_TEMPLATE)
    payload["messages"] = conversation_history

    response = requests.post(URL, headers=HEADERS, json=payload, timeout=500)
    tasks = response.json()["choices"][0]["message"]["content"]
    conversation_history.append({"role": "system", "content": tasks})

    # Step 2: Send Reflection Request
    if LOG:
        print("Reflecting tasks...")
    with open('agents/manager_reflect.txt') as f:
        reflect_prompt = f.read()

    conversation_history.append({"role": "system", "content": reflect_prompt})

    payload = copy.deepcopy(PAYLOAD_TEMPLATE)
    payload["messages"] = conversation_history

    response = requests.post(URL, headers=HEADERS, json=payload, timeout=500)
    tasks = response.json()["choices"][0]["message"]["content"]

    conversation_history.append({"role": "system", "content": tasks})

    return tasks


def task_pipeline(code, tasks, project_requirements):
    """Returns updated code based on given tasks and the provided project requirement"""
    old_code = code
    new_code = code
    conversation_history = []  

    for task in tasks:

        if LOG:
            print("Executing task: "+task)

        # Step 1: Make task prompt
        with open('agents/pipeline_prompt_maker.txt') as f:
            prompt_maker = (
                f.read()
                 .replace("TASK", task)
                 .replace("PROJECT_DESCRIPTION", project_requirements)
            )

        conversation_history = [{"role": "system", "content": prompt_maker}]
        payload = copy.deepcopy(PAYLOAD_TEMPLATE)
        payload["messages"] = conversation_history

        response = requests.post(URL, headers=HEADERS, json=payload, timeout=500)
        task_prompt = response.json()["choices"][0]["message"]["content"]

        # Step 2: Execute task on current code
        with open('agents/pipeline_prompt_executioner.txt') as f:
            task_execution = (
                f.read()
                 .replace("PROMPT", task_prompt)
                 .replace("CODEBASE", new_code)
            )

        conversation_history = [{"role": "system", "content": task_execution}]
        payload = copy.deepcopy(PAYLOAD_TEMPLATE)
        payload["messages"] = conversation_history

        response = requests.post(URL, headers=HEADERS, json=payload, timeout=500)
        new_code = response.json()["choices"][0]["message"]["content"]

        # Step 3: Feedback loop
        if LOG:
            print("Verifying the task")
        new_code = feedback_loop(old_code, new_code, project_requirements, task)
    return new_code


def feedback_loop(old_code, new_code, project_description, task):
    """Returns updated code based on verifier and finalizer agent"""
    current_old = old_code
    current_new = new_code

    conversation_history_loop = []
    conversation_history_finalizer = []

    for i in range(FEEDBACK_DEPTH):
        if LOG:
            print("Verification round: "+str(i))

        # Step 1: Verification
        if i == 0:
            with open('agents/verifier.txt') as f:
                task_verifier = (
                    f.read()
                     .replace('NEW_CODE', current_new)
                     .replace('OLD_CODE', current_old)
                     .replace('TASK', task)
                     .replace('PROJECT_DESCRIPTION', project_description)
                )
        else:
            with open('agents/verifier_continue.txt') as f:
                task_verifier = f.read().replace('CODE', current_new)

        conversation_history_loop.append({"role": "system", "content": task_verifier})

        payload = copy.deepcopy(PAYLOAD_TEMPLATE)
        payload["messages"] = conversation_history_loop

        response = requests.post(URL, headers=HEADERS, json=payload, timeout=500)
        remarks = response.json()["choices"][0]["message"]["content"]

        conversation_history_loop.append({"role": "system", "content": remarks})

        # Count issues 
        issue_count = remarks.count("+")

        # If no issues: return back to task pipeline
        if issue_count <= 0:
            if LOG:
                print("No issues left")
            break

        # Step 2: Finalizer (Fix Issues)
        if LOG:
            print("Finalization with issue amount: "+str(issue_count))
        with open('agents/finalizer.txt') as f:
            task_finalizer = (
                f.read()
                 .replace('REMARKS', remarks)
                 .replace('CODE_CONTENT', current_new)
                 .replace('OLD_CODE', current_old)
            )

        conversation_history_finalizer.append({"role": "system", "content": task_finalizer})

        payload = copy.deepcopy(PAYLOAD_TEMPLATE)
        payload["messages"] = conversation_history_finalizer

        response = requests.post(URL, headers=HEADERS, json=payload, timeout=500)
        current_old = current_new
        current_new = response.json()["choices"][0]["message"]["content"]

        conversation_history_finalizer = []

    return current_new


def single_prompt(code, task_prompt):
    """ Returns modified code based for the given task prompt"""
    with open('agents/pipeline_prompt_executioner.txt') as f:
        task_execution = (
            f.read()
            .replace('PROMPT', task_prompt)
            .replace('CODE', code)
        )
    payload = copy.deepcopy(PAYLOAD_TEMPLATE)
    payload["messages"] = [
        {"role": "system", "content": task_execution}
    ]
    if LOG:
        print("Executing prompt...")
    updated_code = requests.post(URL,headers=HEADERS,json=payload,timeout=500
    ).json()["choices"][0]["message"][
            "content"]
    return updated_code


def ask_source_code():
    """Ask the fle path of the source code"""
    source_code = input("Enter source code path: ")
    return source_code if os.path.isfile(source_code) else (print("Error: The file does not exist. Please try again.") or ask_source_code())


def ask_project_file():
    """Ask file path of the project requirements"""
    project_file = input("Please enter the project requirements file path (default is project/project_requirements.txt) : ") or "project/project_requirements.txt"
    return project_file if os.path.isfile(project_file) else( print("Error: the project requirements file does not exist. Please try again.") or ask_project_file())


def ask_output_file():
    """Ask file path of the written output file"""
    output_file = input("Please enter the output file path: ") or "output.txt"
    return output_file


def ask_operation():
    """Ask whether the system is used or a prompt is tested"""
    type_input = input(
            "Please enter the type (p for pipeline (default), n for normal prompt): ").lower() or 'p'
    return type_input if type_input in ['p', 'n'] else(print(
                "Error: Invalid input. Please enter the type (p for pipeline, n for normal "
                "prompt)") or ask_operation())


def ask_prompt():
    """Ask file path of the tested prompt"""
    input_file = input("Please enter the prompt file name(default is project/prompt.txt): ") or "project/prompt.txt"
    return input_file if os.path.isfile(input_file) else (print("Error: File does not exist. Please try again.") or ask_prompt())


def main():
    operation = ask_operation()
    original_code = open(ask_source_code(), 'r').read()
    output_file = ask_output_file()

    # VAPU workflow
    if operation == 'p':
        project_description = open(ask_project_file(), 'r').read()
        print("Project started at time: ", time.strftime("%H:%M:%S", time.localtime()))
        tasks = get_tasks(project_description)
        modified_code = task_pipeline(original_code, tasks.split("+")[1:], project_description)

    # Single prompt workflow
    elif operation == 'n':
        prompt = open(ask_prompt(), 'r').read()
        print("Project started at time: ", time.strftime("%H:%M:%S", time.localtime()))
        modified_code = single_prompt(original_code, prompt)

    with open(output_file, 'w', encoding="utf-8") as file:
        file.write(modified_code)
    print("Project code finalized and saved to file.")
    print("Project finished at time: ", time.strftime("%H:%M:%S", time.localtime()))

if __name__ == "__main__":
    main()