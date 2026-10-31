Team Name: Midnight Commit
Team Members:
1. Lalit Choudhary
2. Chirag Garg
Selected Problem Statement: 05-Automated Documentation Drift Detection
Category: Developer Experience | Documentation Engineering | Static Analysis

Models we use and why:
Model Name: qwen3.5:4b
Purpose: Semantic documentation verification and analysis.
We selected Qwen3.5:4b as our open-weight AI model to analyze the semantic relationship between source-code changes and natural-language documentation.
The model will help identify documentation inconsistencies that cannot be reliably detected through simple keyword matching, such as paraphrased explanations, indirect references, and changes in described software behavior.
It will also help interpret relevant code-change evidence, assess potential documentation drift, explain detected inconsistencies, and generate structured verification results.
We will combine AI-based semantic analysis with deterministic techniques such as Git diff analysis and source-code parsing to improve accuracy and reduce false positives.

Other AI Models Used: None.
