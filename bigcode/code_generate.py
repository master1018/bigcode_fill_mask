import os
import time
import sys
import subprocess
from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline

def progress_bar(finish_tasks_number, tasks_number):
    percentage = round(finish_tasks_number / tasks_number * 100)
    print("progress\r: {}%: ".format(percentage), "=" * (percentage // 2), end="")
    sys.stdout.flush()

class LLM_Code_Generate:
    #openai_api_key = "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"
    #openai_engine = "text-davinci-003"
    
    # save the code file's path
    source_code = {}
    mutattion_code = {}
    model = None
    tokenizer = None
    # import the model data


    def __init__(self) -> None:
        return
    
    def import_model(self, path) -> None:
        print("[+] Wait for import mode...")
        start = time.time()
        self.model = AutoModelForMaskedLM.from_pretrained(path).to('cuda')
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        end = time.time()
        print("[+] Success import mode from {0}, cost {1} s".format(path, end - start))

    def diff_code(self, file_src, file_patch) -> str:
        diff_output = subprocess.run(['diff', file_src, file_patch, '-u'], capture_output=True, text=True)
        return diff_output.stdout

    def import_dataset(self, path_src, path_mut) -> None:
        src_dirs = os.listdir(path_src)
        mut_dirs = os.listdir(path_mut)
        print(len(src_dirs))
        for i in range(0, len(src_dirs)):
            if (src_dirs[i] == ".DS_Store"):
                continue # for mac os
            cur_dir_path = path_src + "/" + src_dirs[i] + "/"
            file_all = os.listdir(cur_dir_path)
            for j in range(0, len(file_all)):
                if ".c" == file_all[j][len(file_all[j]) - 2: len(file_all[j])]:
                    #code = self.read_msg_from_file(cur_dir_path + file_all[j])
                    self.source_code[src_dirs[i]] = cur_dir_path + file_all[j]

        for i in range(0, len(mut_dirs)):
            if mut_dirs[i] == ".DS_Store":
                continue
            cur_dir_path = path_mut + "/" + mut_dirs[i] + "/"
            file_all = os.listdir(cur_dir_path)
            self.mutattion_code[mut_dirs[i]] = []
            for j in range(0, len(file_all)):
                if ".c" == file_all[j][len(file_all[j]) - 2: len(file_all[j])]:
                    #code = self.read_msg_from_file(cur_dir_path + file_all[j])
                    self.mutattion_code[mut_dirs[i]].append(cur_dir_path + file_all[j])
        

    def generate_response(self, request):
        fill_mask = pipeline('fill-mask', model=self.model, tokenizer=self.tokenizer, device=0)
        response = fill_mask(request)
        return response
    
    def read_msg_from_file(self, file_name) -> str:
        input_text = ""
        fp = open(file_name, "r")
        while True:
            line = fp.readline()
            if not line:
                break
            input_text += line
        fp.close()
        assert(input_text != "")
        return input_text

    def generate_code(self, input_text) -> list:
        ret_val = []
        output_text = self.generate_response(input_text)
        output_list = output_text.split("\n")
        cur = 0
        while cur < len(output_list):
            if "Answer" in output_list[cur]:
                tmp = []
                cur += 1
                while cur < len(output_list) and ("Answer" not in output_list[cur]):
                    tmp.append(output_list[cur])
                    cur += 1
                ret_val.append(tmp)
            else:
                cur += 1
        return ret_val
    
    def read_msg_list_from_file(self, file_name):
        ret_list = []
        fp = open(file_name, "r")
        while True:
            line = fp.readline()
            if not line:
                break
            if "/*" in line or "*/" in line or "//" in line:
                continue
            if line.replace(' ', '') == '\n':
                continue
            ret_list.append(line)
        fp.close()
        assert(ret_list != [])
        return ret_list
    def get_statement_type(self, code_line):
        #TODO other type patch
        # test for insert range checker
        if "return" in code_line:
            return "return"
        elif "throw" in code_line:
            return "throw"
        else:
            return "if"

    def generate_input(self, file_mut):
        # TODO change the preprocess of the input data
        input_list = []
        input_list = self.read_msg_list_from_file(file_mut)
        num_of_mask = 0
        statement_of_mask = []

        for i in range(0, len(input_list)):
            if "<mask_ext>" in  input_list[i]:
                input_list[i] =  input_list[i].replace("<mask_ext>", "<mask{0}>".format(num_of_mask))
                num_of_mask += 1
                statement_of_mask.append(self.get_statement_type( input_list[i]))
                
            elif "<mask>" in  input_list[i]:
                input_list[i] =  input_list[i].replace("<mask>", "<mask{0}>".format(num_of_mask))
                num_of_mask += 1
                statement_of_mask.append(self.get_statement_type( input_list[i]))

        return input_list, statement_of_mask
    
    # test 10 mask
    def fill_mask_of_if_statement(self, request):
        ret_val = []
        response = self.generate_response(request)
        head = []
        for it in response[0]:
            head.append(it['token_str'])
        for i in range(0, len(head)):
            ret_val.append(head[i])
            tmp = request.replace("<mask>", head[i], 1)
            count = 0
            while True and ("<mask>" in tmp) and count < 9:
                response_ = self.generate_response(tmp)
                if type(response_[0]) == list:
                    best_token = response_[0][0]['token_str']
                elif type(response_[0]) == dict:
                    best_token = response_[0]['token_str']
                else:
                    print("[-] Error in response:")
                    print(response_)
                    return "ERROR"
                count += 1
                ret_val[i] += best_token
                tmp = tmp.replace("<mask>", best_token, 1)
            
        return ret_val[0: 3]

    def fill_mask_of_return_statement(self, request):
        ret_val = []
        response = self.generate_response(request)
        for it in response:
            ret_val.append(it['token_str'])
        return ret_val[0: 3]
    
    def fill_mask_of_throw_statement(self, request):
        ret_val = []
        response = self.generate_response(request)
        for it in response:
            ret_val.append(it['token_str'])
        return ret_val[0: 3]

    def llm_code_mutate(self) -> None:
        os.system("rm -rf /data/yanhr/result_code/")
        os.system("mkdir /data/yanhr/result_code")
        
        task_number = 0
        finish_task_number = 0
        
        for key in self.source_code:
            try:
                src_file_path = self.source_code[key]
                mut_file_path_list = self.mutattion_code[key]
            except Exception:
                print("[-] Error in key " + key)
            
            task_number += len(mut_file_path_list)
        
        print("begin task number: {0}".format(task_number))
        win_size = 14
        
        assert(self.source_code != {} and self.mutattion_code != {})
        for key in self.source_code:
            try:
                src_file_path = self.source_code[key]
                mut_file_path_list = self.mutattion_code[key]
            except Exception:
                print("[-] Error in key " + key)
            
            os.system("mkdir /data/yanhr/result_code/" + key)
            for mut_file_name in mut_file_path_list:
                print("[+] parse for " + mut_file_name)
                suffix_name = ""
                pare_pos = len(mut_file_name) - 1
                while mut_file_name[pare_pos] != "/":
                    suffix_name = mut_file_name[pare_pos] + suffix_name
                    pare_pos -= 1


                input_list, statement_of_mask = self.generate_input(mut_file_name)

                # TODO use llm to generate patch
                cur_mask = 0
                cur_line = 0
                num_of_mask = len(statement_of_mask)
                result_of_fill = [[]] * num_of_mask

                while (cur_mask < num_of_mask):
                    use_mask = "<mask{0}>".format(cur_mask)
                    try:
                        if use_mask not in input_list[cur_line]:
                            cur_line += 1
                        else:
                            # generate the request for <maski> (i from 0 to n)
                            request = ""
                            head = max(0, cur_line - win_size // 2)
                            tail = min(len(input_list) - 1, cur_line + win_size // 2)
                            for i in range(head, cur_line):
                                request += input_list[i]

                            tmp = input_list[cur_line]
                            if statement_of_mask[cur_mask] == "if":
                                #TODO Auto define the num of <mask> 
                                tmp = tmp.replace(use_mask, "<mask><mask><mask><mask><mask><mask><mask><mask><mask><mask>")
                            else:
                                tmp = tmp.replace(use_mask, "<mask>")

                            request += tmp

                            for i in range(cur_line + 1, tail + 1):
                                request += input_list[i];         
                        

                        # handle the none target mask in the request
                            for i in range(0, cur_mask):
                                check_str = "<mask{0}>".format(i)
                                if check_str in request:
                                    request = request.replace(check_str, result_of_fill[i][0])

                            for i in range(cur_mask + 1, num_of_mask):
                                check_str = "<mask{0}>".format(i)
                                if check_str in request:
                                    request = request.replace(check_str, "<mask>")
                    
                            #TODO move to one api
                            # handle request to generate mask for each <mask>
                            try:
                                if statement_of_mask[cur_mask] == "if":
                                    ret = self.fill_mask_of_if_statement(request)
                                    result_of_fill[cur_mask] = ret
                                elif statement_of_mask[cur_mask] == "return":
                                    ret = self.fill_mask_of_return_statement(request)
                                    result_of_fill[cur_mask] = ret
                                elif statement_of_mask[cur_mask] == "throw":
                                    ret = self.fill_mask_of_throw_statement(request)
                                    result_of_fill[cur_mask] = ret
                            except Exception:
                                print("[-] Error in request about " + statement_of_mask[cur_mask] + " mask")
                                print(request)
                            cur_mask += 1      
                
                            generate_code = ""
                            for i in range(0, len(input_list)):
                                generate_code += input_list[i]
               
                                try:
                                    for t in range(0, 3):
                    
                                        write_msg = generate_code
                    
                                        for i in range(0, num_of_mask):
                                # for if, get the 3 highest score result
                                            if statement_of_mask[i] == "if":
                                                write_msg = write_msg.replace("<mask{0}>".format(i), result_of_fill[i][t])
                                            else:
                                                write_msg = write_msg.replace("<mask{0}>".format(i), result_of_fill[i][0])
                    
                            # write to the C code file
                                        absolute_file_path = "/data/yanhr/result_code/" + key + "/{0}".format(t) + suffix_name
                                        fp = open(absolute_file_path, "w")
                                        fp.write(write_msg)
                                        fp.close()
                                except Exception:
                                    print("[-] Error in build the code for " + mut_file_name)
                    except Exception:
                        print("[-] Failed in mutate code for " + mut_file_name)
        return


if __name__ == "__main__":
    llm_model = LLM_Code_Generate()
    #input_text = llm_model.read_msg_from_file("/Users/haoranyan/work/test/test_sample_en")
    #res = llm_model.generate_code(input_text)
   # print(res)
    llm_model.import_model("/data/yanhr/repo/codebert-c/")
    llm_model.import_dataset("/data/yanhr/mutation_range_source", "/data/yanhr/mutation_insert_range")
    llm_model.llm_code_mutate()
