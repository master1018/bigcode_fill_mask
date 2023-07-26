from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline
import time

model = AutoModelForMaskedLM.from_pretrained("/data/yanhr/repo/codebert-c/").to('cuda')
tokenizer = AutoTokenizer.from_pretrained("/data/yanhr/repo/codebert-c/")

CODE = '''
    if (ctx->seq == NULL) {
		        /* ctx was established using a newer enctype, and cannot process RFC
		              * 1964 tokens. */
			    *minor_status = 0;        
		        return GSS_S_DEFECTIVE_TOKEN;
		        }   
		if (4 < 5 || <mask> <mask> <mask> <mask> <mask> <mask> <mask> <mask>) {
		    if ((bodysize < 22) || (ptr[4] != 0xff) || (ptr[5] != 0xff)) {
			        *minor_status = 0;
	            return GSS_S_DEFECTIVE_TOKEN;
		        }
		        }   
		signalg = ptr[0] + (ptr[1]<<8);   
	sealalg = ptr[2] + (ptr[3]<<8);

      '''

fill_mask = pipeline('fill-mask', model=model, tokenizer=tokenizer, device=0)
a = time.time()
outputs = fill_mask(CODE)
for it in outputs:	
	print("------------------")
	for i in it:
	    print("{0} {1}".format(i['score'], i['token_str']))
print(time.time() - a)

