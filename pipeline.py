import os
import json
import requests
import time

# Write necessary parameters below:
api_key = ''  # Write api key for OpenAI or an alternative service
model = "gpt-4o-mini"  # Write LLM model version
url = 'https://api.openai.com/v1/chat/completions'  # Write the URL for the provider service
temperature = 0  # Temperature default setting

def get_tasks(project_description):
    """ Get tasks from a manager agent"""
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
    }
    
    conversation_history = []
    manager = open('agents/manager.txt', 'r').read()
    manager = manager.replace("PROJECT_DESCRIPTION", project_description)
    conversation_history.append({"role": "system", "content": manager})
    payload = {
        'model': model,
        'messages': conversation_history,
        'temperature': temperature
    }
    tasks = \
        requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0]["message"][
            "content"]
    conversation_history.append({"role": "system", "content": tasks})
    reflect = open('agents/manager_reflect.txt', 'r').read()
    conversation_history.append({"role": "system", "content": reflect})
    payload = {
        'model': model,
        'messages': conversation_history,
        'temperature': temperature
    }

    tasks = \
        requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0]["message"][
            "content"]
    conversation_history.append({"role": "system", "content": tasks})

    return tasks


def task_pipeline(code, tasks, project_requirements):
    """Returns updated code based on given tasks and the provided project requirement"""
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
    }
    old_code = code
    new_code = code
    conversation_history = []

    for task in tasks:
        prompt_maker = open('agents/pipeline_prompt_maker.txt', 'r').read().replace("TASK", task)
        prompt_maker = prompt_maker.replace("PROJECT_DESCRIPTION", project_requirements)
        conversation_history.append({"role": "system", "content": prompt_maker})
        payload = {
            'model': model,
            'messages': conversation_history,
            'temperature': temperature
        }
        task_prompt = \
            requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0]["message"][
                "content"]
        conversation_history.clear()
        task_execution = open('agents/pipeline_prompt_executioner.txt', 'r').read().replace('PROMPT', task_prompt)
        task_execution = task_execution.replace('CODEBASE', new_code)
        conversation_history.append({"role": "system", "content": task_execution})
        payload = {
            'model': model,
            'messages': conversation_history,
            'temperature': temperature
        }

        new_code = \
            requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0]["message"][
                "content"]

        conversation_history.clear()
        feedback_code = feedback_loop(old_code, new_code, project_requirements, task)
        new_code = feedback_code

    return new_code


def feedback_loop(old_code_1, new_code_1, project_description, task):
    """Returns updated code based on verifier and finalizer agent"""
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
    }
    old_code = [old_code_1]
    new_code = [new_code_1]
    conversation_history_loop = []
    conversation_history_finalizer = []

    for i in range(0, 2):
        if i == 0:
            task_verifier = open('agents/verifier.txt', 'r').read()
            task_verifier = task_verifier.replace('NEW_CODE', new_code[0])
            task_verifier = task_verifier.replace('OLD_CODE', old_code[0])
            task_verifier = task_verifier.replace('TASK', task)
            task_verifier = task_verifier.replace("PROJECT_DESCRIPTION", project_description)
            conversation_history_loop.append({"role": "system", "content": task_verifier})
            payload = {
                'model': model,
                'messages': conversation_history_loop,
                'temperature': temperature
            }
            remarks = \
                requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0][
                    "message"][
                    "content"]
            conversation_history_loop.append({"role": "system", "content": remarks})

            issue_count = remarks.count("+")
        else:
            task_verifier = open('agents/verifier_continue.txt', 'r').read().replace('CODE', new_code[0])
            conversation_history_loop.append({"role": "system", "content": task_verifier})
            payload = {
                'model': model,
                'messages': conversation_history_loop,
                'temperature': temperature
            }
            remarks = \
                requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0][
                    "message"][
                    "content"]
            conversation_history_loop.append({"role": "system", "content": remarks})

            issue_count = remarks.count("+")

        if issue_count > 0:
            task_finalizer = open('agents/finalizer.txt', 'r').read().replace('REMARKS', remarks)
            task_finalizer = task_finalizer.replace('CODE_CONTENT', new_code[0])
            task_finalizer = task_finalizer.replace('OLD_CODE', old_code[0])
            conversation_history_finalizer.append({"role": "system", "content": task_finalizer})
            payload = {
                'model': model,
                'messages': conversation_history_finalizer,
                'temperature': temperature
            }
            old_code[0] = new_code[0]
            new_code[0] = \
                requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0][
                    "message"][
                    "content"]
            conversation_history_finalizer.clear()
        else:
            break
    return new_code[0]


def single_prompt(code, task_prompt):
    """ Returns modified code based for the given task prompt"""
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
    }
    conversation_history = []
    task_execution = open('agents/pipeline_prompt_executioner.txt', 'r').read().replace('PROMPT', task_prompt)
    task_execution = task_execution.replace('CODE', code)
    conversation_history.append({"role": "system", "content": task_execution})
    payload = {
        'model': model,
        'messages': conversation_history,
        'temperature': temperature
    }

    new_code = \
        requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0]["message"][
            "content"]
    return new_code


def ask_code_file():
    """Ask file path of the code file"""
    while True:
        input_file = input("Please enter the codebase file path: ")
        if os.path.isfile(input_file):
            return input_file
        else:
            print("Error: File does not exist. Please try again.")


def ask_project_file():
    """Ask file path of the project requirements"""

    while True:
        input_file = input(
            "Please enter the project requirements file path (default is project/project_requirements.txt) : ")
        if input_file == "":
            return "project/project_requirements.txt"
        elif os.path.isfile(input_file):
            return input_file
        else:
            print("Error: File does not exist. Please try again.")


def ask_output_file():
    """Ask file path of the written output file"""
    output_file = input("Please enter the output file path: ")
    return output_file


def ask_operation():
    """Ask whether the system is used or a prompt is tested"""
    while True:
        type_input = input(
            "Please enter the type (p for pipeline (default), n for normal prompt): ").lower()
        if type_input == "":
            return 'p'
        elif type_input in ['p', 'n']:
            return type_input
        else:
            print(
                "Error: Invalid input. Please enter the type (p for pipeline, c for custom pipeline, n for normal "
                "prompt)")


def ask_prompt():
    """Ask file path of the tested prompt"""
    input_file = input("Please enter the prompt file name(default is project/prompt.txt): ")
    if input_file == "":
        return "project/prompt.txt"
    elif os.path.isfile(input_file):
        return input_file
    else:
        print("Error: File does not exist. Please try again.")
    return input_file


def main():
    operation = ask_operation()
    code_file = ask_code_file()
    output_file = ask_output_file()
    original_code = open(code_file, 'r').read()
    if operation == 'p':
        project_file = ask_project_file()
        project_description = open(project_file, 'r').read()
        print("Project started at time: ", time.strftime("%H:%M:%S", time.localtime()))
        tasks = get_tasks(project_description)
        modified_code = task_pipeline(original_code, tasks.split("+")[1:], project_description)
        with open(output_file, 'w') as file:
            file.write(modified_code)
        print("Project code finalized and saved to file.")
        print("Project finished at time: ", time.strftime("%H:%M:%S", time.localtime()))

    elif operation == 'n':
        prompt_file = ask_prompt()
        print("Project started at time: ", time.strftime("%H:%M:%S", time.localtime()))
        prompt = open(prompt_file, 'r').read()
        modified_code = single_prompt(original_code, prompt)
        with open(output_file, 'w') as file:
            file.write(modified_code)
        print("Project code finalized and saved to file.")
        print("Project finished at time: ", time.strftime("%H:%M:%S", time.localtime()))


if __name__ == "__main__":
    main()
