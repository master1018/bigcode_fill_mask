# pip install -q transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
import time
import torch


MODEL_NAME = "/data/yanhr/repo/santacoder"
MODEL_REVISION = "dedup-alt-comments"
FIM_PREFIX = "<fim-prefix>"
FIM_MIDDLE = "<fim-middle>"
FIM_SUFFIX = "<fim-suffix>"
FIM_PAD = "<fim-pad>"
ENDOFTEXT = "<|endoftext|>"
DEVICE = "cuda"

model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, revision=MODEL_REVISION, trust_remote_code=True).to(DEVICE)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="left")

# Note that the special tokens must be listed in the order below.
tokenizer.add_special_tokens({
"additional_special_tokens": [ ENDOFTEXT, FIM_PREFIX, FIM_MIDDLE, FIM_SUFFIX, FIM_PAD ],
"pad_token": ENDOFTEXT,
})


def extract_fim_part(s: str):
    """
    Find the index of <fim-middle>
    """
    start = s.find(FIM_MIDDLE) + len(FIM_MIDDLE)
    stop = s.find(ENDOFTEXT, start) or len(s)
    return s[start:stop]

def infill(prefix_suffix_tuples, max_tokens: int = 512, temperature: float = 0.2, top_p : float = 0.95):
    output_list = True
    if type(prefix_suffix_tuples) == tuple:
        prefix_suffix_tuples = [prefix_suffix_tuples]
        output_list = False
        
    prompts = [f"{FIM_PREFIX}{prefix}{FIM_SUFFIX}{suffix}{FIM_MIDDLE}" for prefix, suffix in prefix_suffix_tuples]
    # `return_token_type_ids=False` is essential, or we get nonsense output.
    inputs = tokenizer(prompts, return_tensors="pt", padding=True, return_token_type_ids=False).to(DEVICE)
    max_length = inputs.input_ids[0].size(0) + max_tokens
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            do_sample=True,
            top_p=top_p,
            temperature=temperature,
            max_length=max_length,
            pad_token_id=tokenizer.pad_token_id
        )
    # WARNING: cannot use skip_special_tokens, because it blows away the FIM special tokens.
    result = [
        extract_fim_part(tokenizer.decode(tensor, skip_special_tokens=False)) for tensor in outputs
    ]
    return result if output_list else result[0]


prefix = """
    int fun() {
        
        ...

        if (is_undef(r1))
        {
          r1.i = 0;
          push(r1);
          break;
        }

        if (tidx > strlen(r2.s->matches))
            return 
        """

suffix = """ 
            ; 
        match = r2.s->matches[tidx].head;
        r3.i = FALSE;

        while (match != NULL)
        {
          if (r1.i == match->base + match->offset)
          {
            r3.i = TRUE;
            break;
          }

          ...

          }
        """
middle = infill((prefix, suffix))
print(middle)