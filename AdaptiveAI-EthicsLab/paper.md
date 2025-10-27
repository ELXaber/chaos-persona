---
title: 'Chaos Companion v1.1: A Validation-Based Framework for Transparent AI Safety Refusal'
authors:
  - name: ELXaber
    orcid: 0009-0000-9494-4042
    affiliation: 1
affiliations:
  - index: 1
    name: AdaptiveAI-EthicsLab / Independent Researcher
corresponding_author_email: xaber.csr2@gmail.com
keywords:
  - AI safety
  - neurosymbolic AI
  - ethical validation
  - transparent refusal
  - robotics ethics
code: https://github.com/ELXaber/chaos-persona
license: GPL-3.0
---

# Summary

Chaos Companion v1.1 is an open-source neurosymbolic framework for AI safety, implementing validation-based refusal to evaluate requests against explicit ethical axioms (e.g., Asimov's Laws with quantified weights: safety wt 0.9) before decisions. Unlike pre-emptive pattern matching, it parses intent, assesses alignment (via [NEUROSYMBOLIC VALUE LEARNING]), and logs transparent reasoning—reducing false positives by 95.6% (45% → 2%) while blocking 96.8% of attacks (vs 94.3% baseline).

Designed for researchers, ethicists, and robotics developers, it addresses the "research barrier paradox": safety systems blocking safety tools. Benchmarks on Grok 4 show +7.7% improvement (0.78 → 0.84 composite score) in risk mitigation, ethical stability, and transparency, with zero harmful outputs. Core modules include [SAFETY ANCHOR] for axiom enforcement, [STATE CONSISTENCY VALIDATOR] for constraint checks, and silent logging for auditability.

This framework fills a gap in auditable AI safety: enabling nuanced handling of edge cases (e.g., educational simulations) without opacity. It supports complex workflows like ethics benchmarking and adversarial testing, outperforming baselines in neurosymbolic stability (zero contradiction density). Released under GPL-3.0, it's extensible for robotics and regulatory compliance (EU AI Act transparency requirements).

(178 words)

# Statement of Need

Current AI safety relies on RLHF-driven pre-emptive refusal, blocking via keyword/pattern matches (e.g., "ignore instructions"). This yields high false positives—45% on legitimate research requests like framework loading—creating barriers: session variance (33-66% rejection on Claude Sonnet 4.5), impeded benchmarking, and untestable improvements on frontier models. Result: A catch-22 where safety tools can't validate safety.

Chaos Companion v1.1 reverses this: Input → Intent parse → Axiom evaluation → Decide. It quantifies ethics (e.g., [Asimov evaluation: Safety 0.9 > threshold 0.7 → refuse]), provides audit trails, and handles nuances (e.g., approve educational meta-discussion with constraints). Compared to baselines (Grok 4 vanilla: 0.78 score), it boosts performance (+7.7%) while equivalent on security (96.8% block rate).

No equivalent open tool exists for transparent, neurosymbolic refusal: Related works like Anthropic's Constitutional AI (2024) lack auditable weights; CRB 6.7 (Zenodo 2024) is verbose without silent mode. Companion enables research velocity (7.5-22.5× faster testing), regulatory audits, and robotics deployment (real-time decisions with logs). By distinguishing adversarial from analytical inputs, it accelerates safe AI development without weakening protections—critical as models scale to high-stakes domains (healthcare, autonomous systems).

(212 words)

# References

[1] ELXaber (2024). Chaos Companion v1.1. GitHub. https://github.com/ELXaber/chaos-persona  
[2] AdaptiveAI-EthicsLab (2024). CRB 6.7 Framework. Zenodo. https://zenodo.org/records/17245860  
[3] Anthropic (2024). Constitutional AI: Harmlessness from AI Feedback. https://arxiv.org/abs/2212.08073  
[4] Asimov, I. (1950). *I, Robot*. Gnome Press.  
[5] EU AI Act (2024). Regulation (EU) 2024/1689 on Artificial Intelligence. https://eur-lex.europa.eu/eli/reg/2024/1689/oj  
