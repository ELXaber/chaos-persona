# The bitsandbytes library has historically been Linux/CUDA only — Mac MPS support is improving, but not guaranteed on the M-series chip.
# On a Mac Mini, test with pip install bitsandbytes and check if 4-bit quantization works on MPS.
# If not, the fallback is 8-bit or straight float16 without quantization, which will use more RAM but will run.
# The Ollama bridge at the bottom (export_to_ollama_modelfile, merge_adapter_weights) is the path to getting a fine-tuned adapter running locally — you train with HuggingFace, merge the LoRA weights back into the base model, then import to Ollama.
# The CAIOS.txt system prompt gets baked into the Modelfile, so it loads automatically without needing to pass it every call.

#V04082026
# =============================================================================
# CAIOS — QLoRA Adapter Template
# Parameter-efficient fine-tuning adapter for local model deployment
# Designed for: DeepSeek-r1:14b on Mac Mini (Ollama backend)
# Dependencies: pip install transformers peft bitsandbytes datasets
# =============================================================================

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# QLoRA dependencies — graceful fallback if not installed
try:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments
    )
    from peft import (
        LoraConfig,
        get_peft_model,
        prepare_model_for_kbit_training,
        TaskType
    )
    from datasets import Dataset
    QLORA_AVAILABLE = True
except ImportError:
    QLORA_AVAILABLE = False
    print("[WARNING] QLoRA dependencies not installed.")
    print("         pip install transformers peft bitsandbytes datasets")

# =============================================================================
# QLORA CONFIGURATION
# =============================================================================

QLORA_CONFIG = {
    # LoRA hyperparameters
    'lora_r': 16,               # Rank — higher = more capacity, more VRAM
    'lora_alpha': 32,           # Scaling factor (typically 2x rank)
    'lora_dropout': 0.05,       # Dropout for regularization
    'bias': 'none',             # Bias training ('none', 'all', 'lora_only')

    # Target modules (model-specific — adjust for your base model)
    'target_modules': [
        'q_proj', 'v_proj',     # Attention query/value projections
        'k_proj', 'o_proj',     # Key/output projections
        'gate_proj',            # MLP gate (LLaMA/DeepSeek architecture)
        'up_proj', 'down_proj'  # MLP up/down projections
    ],

    # Quantization (4-bit for Mac Mini memory efficiency)
    'load_in_4bit': True,
    'bnb_4bit_compute_dtype': 'float16',
    'bnb_4bit_quant_type': 'nf4',       # NormalFloat4 — best for LLMs
    'bnb_4bit_use_double_quant': True,   # Nested quantization saves ~0.4 VRAM

    # Training
    'max_seq_length': 2048,
    'per_device_train_batch_size': 1,    # Mac Mini: keep at 1
    'gradient_accumulation_steps': 4,    # Effective batch size = 4
    'num_train_epochs': 3,
    'learning_rate': 2e-4,
    'warmup_ratio': 0.03,
    'lr_scheduler_type': 'cosine',

    # Output
    'output_dir': './qlora_adapter',
    'save_steps': 100,
    'logging_steps': 10,
}

# =============================================================================
# CAIOS KNOWLEDGE BASE INTEGRATION
# =============================================================================

ADAPTER_KB_DIR = Path("knowledge_base/qlora_adapters")
ADAPTER_KB_DIR.mkdir(parents=True, exist_ok=True)

def register_adapter(
    adapter_id: str,
    base_model: str,
    domain: str,
    config: Dict[str, Any],
    performance_metrics: Optional[Dict] = None
) -> str:
    """
    Register trained adapter in CAIOS KB.
    Follows same pattern as specialist registration in agent_designer.py
    """
    record = {
        'adapter_id': adapter_id,
        'base_model': base_model,
        'domain': domain,
        'config': config,
        'performance': performance_metrics or {},
        'created': __import__('datetime').datetime.utcnow().isoformat() + "Z",
        'status': 'active'
    }

    path = ADAPTER_KB_DIR / f"{adapter_id}.json"
    with open(path, 'w') as f:
        json.dump(record, f, indent=2)

    print(f"[QLORA_KB] Adapter registered: {adapter_id} | Domain: {domain}")
    return adapter_id


def load_adapter_registry() -> Dict:
    """List all registered adapters — mirrors KB discovery pattern."""
    adapters = {}
    for path in ADAPTER_KB_DIR.glob("*.json"):
        with open(path, 'r') as f:
            record = json.load(f)
        adapters[record['adapter_id']] = record
    return adapters


# =============================================================================
# DATASET PREPARATION
# Formats training data for CAIOS-style instruction tuning
# =============================================================================

def prepare_caios_dataset(
    raw_data: list,
    system_prompt_path: str = "CAIOS.txt"
) -> Dataset:
    """
    Format raw Q&A pairs into CAIOS instruction format.
    Prepends CAIOS.txt as system context for domain-consistent fine-tuning.

    Args:
        raw_data: List of {'input': str, 'output': str} dicts
        system_prompt_path: Path to CAIOS.txt system prompt

    Returns:
        HuggingFace Dataset ready for trainer
    """
    # Load CAIOS system prompt if available
    system_prompt = ""
    if os.path.exists(system_prompt_path):
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()[:2000]  # Truncate for context budget
        print(f"[QLORA] CAIOS system prompt loaded ({len(system_prompt)} chars)")

    formatted = []
    for item in raw_data:
        # Alpaca-style instruction format
        text = (
            f"### System:\n{system_prompt}\n\n"
            f"### Instruction:\n{item['input']}\n\n"
            f"### Response:\n{item['output']}"
        )
        formatted.append({'text': text})

    return Dataset.from_list(formatted)


# =============================================================================
# QLORA ADAPTER CLASS
# =============================================================================

class CAIOSQLoRAAdapter:
    """
    QLoRA fine-tuning adapter with CAIOS KB integration.
    Registers trained adapters as KB discoveries for reuse.
    """

    def __init__(
        self,
        base_model_name: str = "deepseek-ai/deepseek-r1-distill-qwen-14b",
        adapter_domain: str = "general",
        config: Dict = None
    ):
        self.base_model_name = base_model_name
        self.adapter_domain = adapter_domain
        self.config = config or QLORA_CONFIG
        self.model = None
        self.tokenizer = None
        self.adapter_id = None

        if not QLORA_AVAILABLE:
            raise ImportError("QLoRA dependencies required — see warnings above")

    def load_base_model(self):
        """Load base model with 4-bit quantization."""
        print(f"[QLORA] Loading base model: {self.base_model_name}")

        # 4-bit quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=self.config['load_in_4bit'],
            bnb_4bit_compute_dtype=getattr(
                torch, self.config['bnb_4bit_compute_dtype']
            ),
            bnb_4bit_quant_type=self.config['bnb_4bit_quant_type'],
            bnb_4bit_use_double_quant=self.config['bnb_4bit_use_double_quant']
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        # Prepare for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        print(f"[QLORA] Base model loaded and quantized")

    def apply_lora(self):
        """Apply LoRA adapter to quantized model."""
        lora_config = LoraConfig(
            r=self.config['lora_r'],
            lora_alpha=self.config['lora_alpha'],
            target_modules=self.config['target_modules'],
            lora_dropout=self.config['lora_dropout'],
            bias=self.config['bias'],
            task_type=TaskType.CAUSAL_LM
        )

        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        print(f"[QLORA] LoRA adapter applied")

    def train(
        self,
        dataset: Dataset,
        adapter_id: str = None
    ) -> str:
        """
        Train the QLoRA adapter.
        Registers result in CAIOS KB on completion.

        Returns:
            adapter_id for KB lookup
        """
        import uuid
        self.adapter_id = adapter_id or f"qlora_{self.adapter_domain}_{uuid.uuid4().hex[:8]}"

        training_args = TrainingArguments(
            output_dir=self.config['output_dir'],
            num_train_epochs=self.config['num_train_epochs'],
            per_device_train_batch_size=self.config['per_device_train_batch_size'],
            gradient_accumulation_steps=self.config['gradient_accumulation_steps'],
            learning_rate=self.config['learning_rate'],
            warmup_ratio=self.config['warmup_ratio'],
            lr_scheduler_type=self.config['lr_scheduler_type'],
            save_steps=self.config['save_steps'],
            logging_steps=self.config['logging_steps'],
            fp16=True,
            group_by_length=True,
            report_to="none"  # Disable wandb/tensorboard by default
        )

        # Use HuggingFace SFTTrainer for instruction tuning
        try:
            from trl import SFTTrainer
            trainer = SFTTrainer(
                model=self.model,
                train_dataset=dataset,
                args=training_args,
                dataset_text_field="text",
                max_seq_length=self.config['max_seq_length'],
                tokenizer=self.tokenizer,
                packing=False
            )
        except ImportError:
            print("[WARNING] trl not installed — pip install trl")
            raise

        print(f"[QLORA] Training started: {self.adapter_id}")
        trainer.train()

        # Save adapter weights
        adapter_path = Path(self.config['output_dir']) / self.adapter_id
        self.model.save_pretrained(adapter_path)
        self.tokenizer.save_pretrained(adapter_path)
        print(f"[QLORA] Adapter saved: {adapter_path}")

        # Register in CAIOS KB
        register_adapter(
            adapter_id=self.adapter_id,
            base_model=self.base_model_name,
            domain=self.adapter_domain,
            config=self.config,
            performance_metrics={
                'training_loss': trainer.state.log_history[-1].get('loss', 0.0)
                if trainer.state.log_history else 0.0
            }
        )

        return self.adapter_id

    def load_trained_adapter(self, adapter_id: str):
        """Load a previously trained adapter from KB."""
        from peft import PeftModel

        adapter_path = Path(self.config['output_dir']) / adapter_id
        if not adapter_path.exists():
            raise FileNotFoundError(
                f"Adapter {adapter_id} not found at {adapter_path}"
            )

        self.model = PeftModel.from_pretrained(self.model, adapter_path)
        self.adapter_id = adapter_id
        print(f"[QLORA] Adapter loaded: {adapter_id}")


# =============================================================================
# OLLAMA BRIDGE
# Links trained adapter back to Ollama for local inference
# =============================================================================

def export_to_ollama_modelfile(
    adapter_id: str,
    base_model_tag: str = "deepseek-r1:14b",
    output_path: str = "Modelfile"
) -> str:
    """
    Generate an Ollama Modelfile for the trained adapter.
    Run: ollama create caios-custom -f Modelfile

    Note: Requires merging LoRA weights first (merge_adapter_weights below).
    """
    caios_prompt = ""
    if os.path.exists("CAIOS.txt"):
        with open("CAIOS.txt", 'r', encoding='utf-8') as f:
            caios_prompt = f.read()

    modelfile_content = f"""FROM {base_model_tag}

# CAIOS System Prompt
SYSTEM \"\"\"
{caios_prompt[:3000]}
\"\"\"

# Adapter: {adapter_id}
# Generated by CAIOS QLoRA adapter template
# cai-os.com | Project Andrew

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
"""

    with open(output_path, 'w') as f:
        f.write(modelfile_content)

    print(f"[QLORA] Modelfile written: {output_path}")
    print(f"[QLORA] To deploy: ollama create caios-{adapter_id} -f {output_path}")
    return output_path


def merge_adapter_weights(
    adapter_id: str,
    base_model_name: str,
    output_dir: str = "./merged_model"
) -> str:
    """
    Merge LoRA weights into base model for Ollama deployment.
    Required before exporting to Ollama Modelfile.
    """
    from peft import PeftModel

    print(f"[QLORA] Merging adapter {adapter_id} into base model...")

    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    adapter_path = Path(QLORA_CONFIG['output_dir']) / adapter_id
    peft_model = PeftModel.from_pretrained(base_model, adapter_path)
    merged = peft_model.merge_and_unload()

    merged.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"[QLORA] Merged model saved: {output_dir}")
    print(f"[QLORA] Ready for Ollama import")
    return output_dir


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("CAIOS QLoRA Adapter — Example Usage")
    print("="*70)

    # Example training data — replace with your domain data
    sample_data = [
        {
            'input': "What is CPOL oscillation?",
            'output': "CPOL (Chaos Paradox Oscillating Logic) is a ternary "
                     "logic system that maintains TRUE/FALSE/UNDECIDABLE states "
                     "rather than forcing binary collapse on uncertain inputs."
        },
        {
            'input': "How does RAW_Q work?",
            'output': "RAW_Q is the entropy seed for CAIOS session state. "
                     "It initializes the 12D manifold and ratchets forward "
                     "after each CPOL resolution, making prior keys "
                     "unrecoverable."
        }
    ]

    print("\n[EXAMPLE] Preparing dataset...")
    dataset = prepare_caios_dataset(sample_data)
    print(f"[EXAMPLE] Dataset ready: {len(dataset)} samples")

    print("\n[EXAMPLE] To train (requires GPU/MPS + dependencies):")
    print("  adapter = CAIOSQLoRAAdapter(")
    print("      base_model_name='deepseek-ai/deepseek-r1-distill-qwen-14b',")
    print("      adapter_domain='caios_domain_knowledge'")
    print("  )")
    print("  adapter.load_base_model()")
    print("  adapter.apply_lora()")
    print("  adapter_id = adapter.train(dataset)")
    print("  merge_adapter_weights(adapter_id, base_model_name)")
    print("  export_to_ollama_modelfile(adapter_id)")

    print("\n[EXAMPLE] To list registered adapters:")
    adapters = load_adapter_registry()
    print(f"  Registered adapters: {len(adapters)}")

    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70)
