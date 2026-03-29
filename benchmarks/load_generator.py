"""
Synthetic load generation for Milestone 5 benchmarking.
"""

from typing import List


def get_prompts(num_requests: int = 50) -> List[str]:
    """
    Returns repeated prompts so cache hit behavior can be measured.
    """
    base_prompts = [
        "Explain machine learning.",
        "What is artificial intelligence?",
        "Explain neural networks.",
        "What is deep learning?",
        "Explain regression.",
        "Explain classification.",
        "What is NLP?",
        "Explain clustering.",
        "What is overfitting?",
        "Explain reinforcement learning.",
    ]

    prompts = []
    for i in range(num_requests):
        prompts.append(base_prompts[i % len(base_prompts)])

    return prompts