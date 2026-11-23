"""Adaptador local de planejamento com modelo e tokenizer injetados."""


class LocalPlanner:
    """Gera planos por inferência local sem depender de um servidor HTTP."""

    def __init__(self, model, tokenizer, max_new_tokens=160):
        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens

    def complete(self, prompt, *, response_model=None):
        if response_model is not None:
            raise ValueError("O planejador local aceita somente texto")
        text = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False,
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        output = self.model.generate(
            **inputs, max_new_tokens=self.max_new_tokens, do_sample=False,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        answer = self.tokenizer.decode(
            output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True,
        )
        if not answer.strip():
            raise RuntimeError("O planejador local retornou uma resposta vazia")
        return answer
