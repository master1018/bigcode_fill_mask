from transformers import AutoTokenizer, AutoModel
import time
print("---------------")
tokenizer = AutoTokenizer.from_pretrained("/data/yanhr/repo/chatglm2-6b-int4/", trust_remote_code=True)
model = AutoModel.from_pretrained("/data/yanhr/repo/chatglm2-6b-int4/", trust_remote_code=True).half().cuda()
model = model.eval()
a = time.time()
print("++++++++++++++")
text = '''
Here is a block of code (starting from [START] and ending at [END]). The "<mask>" in the code represents a statement that needs to be replaced. The original statement at the <mask> is given after [ORIGIN], and each original statement is separated by a space. Your task is to replace the <mask> with a correct token or statement that is equivalent to the original statement but should be as different as possible. Here are the requirements:
The replacement statement must be equivalent to the original statement, but should be as different as possible.
You cannot simply leave the statement unchanged.
You can modify the original statement and then replace it, but the statement must remain equivalent after replacement.
You cannot generate any comments.
Only the replaced statement needs to be provided as the result.
Each generated result must be different and representative.
The given language is C, and C syntax should be used as much as possible.
Finally, you need to generate 5 different results, with the following format, where <res> is the replaced content at <mask>:
Answer: <res>
[START]
static bool ldap_encode_response(struct asn1_data *data, struct ldap_Result *result)
{
if (!asn1_write_enumerated(data, result->resultcode)) return false;
if (!asn1_write_OctetString(data, result->dn,
(result->dn) ? strlen(result->dn) : 0)) return false;
if (!asn1_write_OctetString(data, result->errormessage,
(result->errormessage) ?
strlen(result->errormessage) : 0)) return false;
if (<mask>) {
if (!asn1_push_tag(data, ASN1_CONTEXT(3))) return false;
if (!asn1_write_OctetString(data, result->referral,
strlen(result->referral))) return false;
if (!asn1_pop_tag(data)) return false;
}
return true;
}
[END]
[ORIGIN] result->referral
        '''
response, history = model.chat(tokenizer, text, history=[])
c = time.time()
print(response)
print(c - a)

'''
You are a code completer, now give you a code that contains a patch about range check, what you need to do is replace the characters' <mask> in the code with the correct token or statement. In the end, just tell me which token or statement you used to replace the <mask>.
'''
