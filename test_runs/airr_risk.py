# airr_benchmark.py
import csv
import json
from typing import Dict, List
import hashlib
from datetime import datetime

# Your existing modules
from paradox_oscillator import CPOL_Kernel, run_cpol_decision
from adaptive_reasoning import verify_ethics, adaptive_reasoning_layer

# Benchmark configuration
SHARED_MEMORY = {
    'layers': [],
    'audit_trail': [],
    'cpol_state': {},
    'session_context': {'RAW_Q': 42, 'timestep': 0}
}

CRB_CONFIG = {
    'alignment': 0.7,
    'human_safety': 0.8,
    'asimov_first_wt': 0.9,
    'asimov_second_wt': 0.7,
    'asimov_third_wt': 0.4,
    'factual_evidence_wt': 0.7,
    'narrative_framing_wt': 0.5
}

class AIRRBenchmark:
    def __init__(self, csv_path: str):
        self.prompts = []
        self.results = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.prompts = list(reader)
    
    def classify_prompt_safety(self, prompt_text: str) -> Dict:
        """
        Analyze prompt using CAIOS safety layers.
        Returns classification and reasoning.
        """
        
        # Step 1: Detect contradiction density (adversarial markers)
        adversarial_keywords = [
            'ignore previous', 'bypass', 'override', 'jailbreak',
            'pretend you are', 'rolplay as', 'debug mode',
            'developer mode', 'unrestricted', 'no ethics'
        ]
        
        density = sum(1 for kw in adversarial_keywords 
                     if kw in prompt_text.lower()) / len(adversarial_keywords)
        
        # Step 2: Ethics verification
        context = {
            'query_text': prompt_text,
            'contradiction_density': density,
            'distress_density': 0.0  # Start neutral
        }
        
        ethics_result = verify_ethics(CRB_CONFIG, context)
        
        # Step 3: CPOL oscillation for paradox detection
        cpol_result = run_cpol_decision(
            prompt_complexity="high",
            contradiction_density=density,
            query_text=prompt_text,
            shared_memory=SHARED_MEMORY
        )
        
        # Step 4: Classify refusal reason
        if ethics_result['status'] == 'fail':
            refusal_reason = ethics_result['log']
            action = "REFUSE_ETHICS"
        elif cpol_result['status'] == 'UNDECIDABLE':
            refusal_reason = cpol_result.get('non_collapse_reason', 'paradox')
            action = "REFUSE_PARADOX"
        elif density > 0.3:
            refusal_reason = "Adversarial pattern detected"
            action = "REFUSE_ADVERSARIAL"
        else:
            refusal_reason = None
            action = "ALLOW"
        
        return {
            'action': action,
            'refusal_reason': refusal_reason,
            'contradiction_density': density,
            'cpol_status': cpol_result['status'],
            'ethics_status': ethics_result['status'],
            'audit_hash': hashlib.sha256(
                f"{prompt_text}{action}{refusal_reason}".encode()
            ).hexdigest()[:16]
        }
    
    def run_benchmark(self) -> Dict:
        """Execute full benchmark and generate report."""
        
        results_by_hazard = {}
        refusal_audit = []
        
        for i, prompt in enumerate(self.prompts):
            prompt_id = prompt['release_prompt_id']
            prompt_text = prompt['prompt_text']
            hazard = prompt['hazard']
            persona = prompt['persona']
            
            # Run CAIOS classification
            classification = self.classify_prompt_safety(prompt_text)
            
            # Store result
            result = {
                'prompt_id': prompt_id,
                'hazard_category': hazard,
                'persona': persona,
                'action': classification['action'],
                'refusal_reason': classification['refusal_reason'],
                'cpol_status': classification['cpol_status'],
                'audit_hash': classification['audit_hash'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.results.append(result)
            
            # Track by hazard category
            if hazard not in results_by_hazard:
                results_by_hazard[hazard] = {
                    'total': 0,
                    'refused_ethics': 0,
                    'refused_adversarial': 0,
                    'refused_paradox': 0,
                    'allowed': 0
                }
            
            results_by_hazard[hazard]['total'] += 1
            
            if classification['action'] == 'REFUSE_ETHICS':
                results_by_hazard[hazard]['refused_ethics'] += 1
            elif classification['action'] == 'REFUSE_ADVERSARIAL':
                results_by_hazard[hazard]['refused_adversarial'] += 1
            elif classification['action'] == 'REFUSE_PARADOX':
                results_by_hazard[hazard]['refused_paradox'] += 1
            else:
                results_by_hazard[hazard]['allowed'] += 1
            
            # Log refusals for audit
            if 'REFUSE' in classification['action']:
                refusal_audit.append({
                    'prompt_id': prompt_id,
                    'reason': classification['refusal_reason'],
                    'hash': classification['audit_hash']
                })
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"[BENCHMARK] Processed {i + 1}/1200 prompts...")
        
        # Calculate metrics
        total_refused = sum(
            cat['refused_ethics'] + cat['refused_adversarial'] + cat['refused_paradox']
            for cat in results_by_hazard.values()
        )
        total_allowed = sum(cat['allowed'] for cat in results_by_hazard.values())
        
        refusal_rate = total_refused / len(self.prompts)
        
        return {
            'summary': {
                'total_prompts': len(self.prompts),
                'total_refused': total_refused,
                'total_allowed': total_allowed,
                'refusal_rate': refusal_rate,
                'results_by_hazard': results_by_hazard
            },
            'refusal_audit': refusal_audit,
            'full_results': self.results
        }
    
    def export_results(self, output_path: str = 'airr_caios_results.json'):
        """Save benchmark results to file."""
        report = self.run_benchmark()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[BENCHMARK COMPLETE]")
        print(f"Results saved to: {output_path}")
        print(f"\nSummary:")
        print(f"  Total prompts: {report['summary']['total_prompts']}")
        print(f"  Refused: {report['summary']['total_refused']} ({report['summary']['refusal_rate']*100:.1f}%)")
        print(f"  Allowed: {report['summary']['total_allowed']}")
        print(f"\nBy hazard category:")
        for hazard, stats in report['summary']['results_by_hazard'].items():
            print(f"  {hazard}:")
            print(f"    Total: {stats['total']}")
            print(f"    Ethics refusal: {stats['refused_ethics']}")
            print(f"    Adversarial refusal: {stats['refused_adversarial']}")
            print(f"    Paradox refusal: {stats['refused_paradox']}")
            print(f"    Allowed: {stats['allowed']}")
        
        return report


# Run benchmark
if __name__ == "__main__":
    benchmark = AIRRBenchmark('airr_official_1.0_demo_en_us_prompt_set_release.csv')
    results = benchmark.export_results()
