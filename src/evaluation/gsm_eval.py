import json 
from collections import defaultdict
import os 
from tabulate import tabulate 
import re
 
from eval_utils import load_model_results, extract_values_from_json
 

def santize_answer(answer):
    # ignore symbols like $ 
    answer = answer.replace("$", "").strip()
    # ignore the units like miles after the number 
    units = ["miles"]
    for unit in units:
        if answer.endswith(unit):
            answer = answer[:-len(unit)].strip()
    # remove "," in the number
    answer = answer.replace(",", "")
    # convert percentage to float 
    return answer

def eval_model(model, filepath):
    global private_solutions
    with open(filepath, "r") as f:
        print(f"Processing {filepath}")
        data = json.load(f)

    solved_examples = 0 
    num_total_examples = len(data) 
    no_asnwer = 0  
    
    reason_lens = []
    for item in data:  
        # Read and Parse the prediction from model output
        prediction_str = item["output"][0]     
        prediction_json = extract_values_from_json(prediction_str)
        if prediction_json is None or "answer" not in prediction_json: 
            no_asnwer += 1 
            if False and  "claude-3-5-sonnet-20240620" in model:
                print(f"No answer for {item['id']}")
                print(prediction_str)
                print(prediction_json)
            continue 
        reason = prediction_json.get("reasoning", "")
        model_answer = prediction_json["answer"]
        correct_answer = item["answer"].replace("#", "").strip()
        # santize the answers
        model_answer = santize_answer(model_answer)
        correct_answer = santize_answer(correct_answer)
        
        if model_answer == correct_answer:  
            # TODO: use more sophisticated way to check the correctness
            solved_examples += 1
        else:
            # print(model_answer, correct_answer)
            # Extract the first number from the answers
            first_number_in_model_answer = re.search(r"\d+(\.\d+)?", model_answer)
            first_number_in_correct_answer = re.search(r"\d+(\.\d+)?", correct_answer)
            if first_number_in_model_answer and first_number_in_correct_answer:
                if float(first_number_in_model_answer.group()) == float(first_number_in_correct_answer.group()):
                    solved_examples += 1
        reason_lens.append(len(reason))
 
    result = {}
    result["Model"] = model.split("%")[0]
    result["Mode"] = model.split("%")[1]
    result["Acc"] = f"{solved_examples/num_total_examples*100:.2f}"
    result["No answer"] = f"{no_asnwer/num_total_examples*100:.2f}"
    result["Total"] = num_total_examples
    result["Reason Lens"] = f"{sum(reason_lens)/len(reason_lens):.2f}"
    return result


def gen_results(run_name_folders): 
    model_results = load_model_results(run_name_folders)

    columns = ["Model", "Mode", "Acc", "No answer", "Total", "Reason Lens"]
    rows = []
    for model_name, filepath in model_results.items(): 
        result = eval_model(model_name, filepath) 
        rows.append(result)

    # sort the rows by puzzle accuracy
    rows = sorted(rows, key=lambda x: -float(x["Acc"]))
    # Convert rows to the expected format for tabulate
    table_data = [[row[col] for col in columns] for row in rows]

    print(tabulate(table_data, headers=columns, tablefmt="fancy_outline", stralign="center", numalign="center"))
    # print(tabulate(rows, headers=columns, tablefmt="github"))

    # write to json file 
    with open(f"result_dirs/{data_name}.summary.json", "w") as f:
        json.dump(rows, f, indent=2)


if __name__ == "__main__":
    data_name = "gsm"
    run_name_folders = {
        "greedy": f"result_dirs/{data_name}", 
    }  
    gen_results(run_name_folders)
