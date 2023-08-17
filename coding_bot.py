from text_generation import Client
import re
import io
import sys
import os
import subprocess
import traceback
model = 'llama-aip'
query = "Combine the building mechanics of minecraft, the 2D platforming of mario, and the shooting of call of duty into 1 cohesive game."

def call_api(query, temp, top_p, top_k):
    cl = Client("https://"+model+".lt.mitre.org")
    print("\n" + "\n " + query)
    while True:
        try:
            answer = cl.generate(query, max_new_tokens=150, temperature=temp, top_p=top_p, top_k=top_k).generated_text
            answer = answer.lstrip()
            query += answer 
            if not any(char.isalpha() for char in answer):
                break
        except:
            print("I timed out, let me try again")
    return(query)

def code_writer(query, long):
    if long == True:
        coder_cleaned_query = "QUESTION: " + query + " \n Act as a professional python developer. Write no comments in your code, and format it so there's no spaces. Surround the code with 3 backticks (```) to distinguish between code and instructions. \n ANSWER: \n "
    else:
        coder_cleaned_query = "QUESTION: " + query + " \n The python code must be less than 50 lines long. Act as a professional python developer. Surround the code with 3 backticks (```) to distinguish between code and instructions. \n ANSWER: \n "
    cutoff = len(coder_cleaned_query)
    answer = call_api(coder_cleaned_query, .4, .9, 40)
    answer = answer[(cutoff - 5):]
    pattern = r"```(.*?)```" 
    matches = re.findall(pattern, answer, re.DOTALL)
    code = "\n\n".join(matches)
    return(code)

def code_runner(code):
    filename = "test.py"
    error_occurred = False
    with open(filename, "w") as file:
        file.write(code)
    current_directory = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(current_directory, "test.py")
    completed_process = subprocess.run(['python3', filename], capture_output=True, text=True)
    if completed_process.returncode == 0:
        error_occurred = False
    else:
        error_occurred = True
    return completed_process.stdout, completed_process.stderr, error_occurred

def code_compiler(code):
    filename = "test.py"
    stderr = ""
    with open(filename, "w") as file:
        file.write(code)

    current_directory = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(current_directory, "test.py")

    try:
        compile(code, filename, 'exec')
        error_occurred = False
    except Exception as e:
        error_occurred = True
        stderr = str(e)
    return '', stderr, error_occurred

def coder_agent(query, compressor, long):
    output = ["", "", True]
    code = code_writer(query, long)
    if compressor == True:
        better_code = code_writer("Here's my code: " + query + "\n Will the code work how I want it to? Are there any incorrect imports, syntax errors, logic mistakes, or endless loops? Make any changes to the code so that it solves the problem better. Output the full code (leave the parts that don't need changing the same).", long)
    else:
        better_code = code_writer("Here's the problem to solve: " + query + " \n And here's the code to do it: " + code + "\n Will the code work how I want it to? Are there any incorrect imports, syntax errors, logic mistakes, or endless loops? Will it even complete the task correctly or is it too short? Make any changes and additions to the code so that it solves the problem better. Output the full code (leave the parts that don't need changing the same)", long)
    output = code_compiler(better_code)
    matches = re.findall(r'line (\d+)', output[1])
    if matches:
        line_number_of_error = int(matches[-1])
    else:
        line_number_of_error = 0
    return(output[0], output[1], output[2], better_code, line_number_of_error)

def brain_agent(query):
    cutoff = len(query)
    answer = call_api(query, .6, .95, 60)
    return answer[(cutoff):]

def coding_team(query, compressor, long, query2):
        code = coder_agent(query, compressor, long)
        while code[2] == True:
            code = coder_agent("I tried to solve the problem: " + query2 + " \n but wrote this code: \n" + code[3] + "\n which resulted in the error: " + code[1] + "\n Fix the code. ", False, True)
        
        compressed_code = code_writer("Remove all of the comments and remove the gaps between some of the lines in this code: \n" + code[3], True)
        while compressed_code[2] == True:
            compressed_code = code_writer("Remove all of the comments and remove the gaps between some of the lines in this code: \n" + code[3], True)
        return compressed_code[3]
            
def planning_team(query): 
    plan = brain_agent("QUESTION: " + query + "\n Don't give me a solution; instead, create the outline for a step-by-step plan. Each of the steps will be given to a python coding intern for completion so make them well-defined and simple. The whole plan should be less than 100 words. \n ANSWER: \n")
    refined_plan = brain_agent("QUESTION: Here's my plan: " + plan + "\n Refine the plan into sections that a python coding intern could reasonably complete. (You'll be responsible for joining all of the sections together). Reorganize, add, and remove elements to as you deem necessary, until you think it properly represents a comprehensive plan of action that could be distributed in parts to many interns in order to solve the problem: " + query + " \n It should be less than 150 words, and less than 5 steps long. \n ANSWER: \n")
    sectioned_plan = brain_agent("QUESTION: Here's my plan: " + refined_plan + "\n Compress this plan down into simple well defined commands that you could give to an AI coding intern [CODER] using python to take action right away. You will be responsible for combining the parts into a cohesive end product, but keep in mind that the workers have no idea of the task or overall goal so convey that to them. If you need human assistance (for example, supplying assets that can't be generated with code, supplying an API key, etc.), use the last command to ask for human help. Don't ask the human unless absolutely necessary! Write the step number, followed by who to delegate it to (ie. 5:[CODER] Make an edit feature for a calendar \n 6. [CODER] Make a save feature for a calendar \n 7:[HUMAN] Supply an API for a cloud hosting service). Each prompt should be between 15 and 50 words and you should output less than 5 steps \n ANSWER: \n")
    coder_tasks = []
    human_task = ''
    lines = sectioned_plan.split('\n')
    for line in lines:
        if "[CODER]" in line:
            task = line.replace("[CODER]", "").strip()
            coder_tasks.append(task)
        else:
            task = line.replace("[HUMAN]", "").strip()
            human_task = task
    #refined_plan = brain_agent("QUESTION: Here's my plan: " + str(coder_tasks) has been created to allow AI coding bots writing in python to carry out each step easily. ")
    return coder_tasks, human_task, sectioned_plan

distribute = brain_agent("QUESTION: " + query + " \n Should this command be sent to a coder or a planner first? For example, the commmand to make a calculator should be sent to a coder while the command to make a full platforming game should be sent to a planner first. Output a single word: [CODER] or [PLANNER] based on your decision. \n ANSWER: \n")
if "PLANNER" in distribute:
    coder_tasks, planner_tasks, complete_plan = planning_team(query)
    code_segments = []
    code_segments.append(coding_team("Your task is to: " + coder_tasks[0] + "\n Complete no more and no less than this task", False, False, coder_tasks[0]))
    task1 = coder_tasks[0]
    coder_tasks = coder_tasks[1:]
    i = 0
    for task in coder_tasks:  
        code_segments.append(coding_team("I wrote this code: \n" + code_segments[i] + "\n Modify or add onto this code in ordr to: " + task, False, True, task1 + "\n " + coder_tasks[i]))
        i += 1
else:
    coding_team(query, False, True, query)
