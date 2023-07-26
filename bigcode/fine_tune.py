from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
import numpy as np
import evaluate

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

MODEL_NAME = "/data/yanhr/repo/santacoder"
DEVICE = "cuda"
MODEL_REVISION = "dedup-alt-comments"

dataset = load_dataset("/data/yanhr/dataset/the_stack", data_dir="data/c", split="train")

tokenized_datasets = dataset


print("[+] Loading pretrain model...")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, revision=MODEL_REVISION, trust_remote_code=True).to(DEVICE)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="left")
print("[+] Loading success!")


training_args = TrainingArguments(output_dir="/data/yanhr/test_trainer")

metric = evaluate.load("accuracy")


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
    compute_metrics=compute_metrics,
)

trainer.train()