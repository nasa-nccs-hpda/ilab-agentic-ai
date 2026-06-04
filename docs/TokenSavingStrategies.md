# AI Usage Optimization Guide for Scientific Software Engineering and HPC Teams

## Overview

As AI tools become increasingly integrated into software development workflows, managing token consumption is essential for controlling costs while maintaining productivity. This guide captures practical strategies for maximizing the value of AI-assisted development, particularly for scientific computing, HPC, Earth science modeling, GPU acceleration, and large-scale software engineering projects.

The recommendations in this document have been distilled from real-world usage involving code translation, model deployment, scientific software modernization, GPU optimization, and AI-assisted software engineering.

---

# Table of Contents

1. Why Token Efficiency Matters
2. Understanding Where Tokens Are Consumed
3. General Best Practices
4. Prompt Engineering for Efficiency
5. Context Management Strategies
6. Code Translation Workflows
7. Scientific Software Development Workflows
8. Multi-Agent Workflows
9. Model Selection Recommendations
10. Team Standards
11. Example Prompt Templates
12. Common Anti-Patterns
13. Expected Savings

---

# Why Token Efficiency Matters

Most AI usage costs originate from:

* Large context windows
* Repeated code pasting
* Excessively verbose responses
* Long-running conversations
* Re-explaining project context

For large scientific software projects, a single inefficient conversation can consume more tokens than an entire day of focused development.

Benefits of efficient workflows include:

* Reduced operational cost
* Faster responses
* Improved model focus
* More predictable outputs
* Increased daily throughput

---

# Understanding Where Tokens Are Consumed

The AI processes:

```
Input Tokens
+
Conversation History
+
System Instructions
+
Output Tokens
```

For example:

```text
500 lines of code pasted
+
10 previous messages
+
2000 token response
```

can easily exceed 20,000 tokens for a single request.

Many users underestimate how much conversation history contributes to token usage.

---

# General Best Practices

## 1. Request Concise Responses

Instead of:

```text
Explain this code.
```

Use:

```text
Explain this code in 5 bullet points.
```

Or:

```text
Limit response to 200 tokens.
```

Examples:

```text
Output only code.
```

```text
Return summary only.
```

```text
Use bullet points.
```

```text
Maximum 10 sentences.
```

---

## 2. Eliminate Unnecessary Explanations

Avoid:

```text
Translate this function.
```

Use:

```text
Translate this function.
Return code only.
No explanations.
```

---

## 3. Request Structured Outputs

Prefer:

```text
Output:
1. Root Cause
2. Fix
3. Validation Steps
```

Over open-ended prompts.

Structured outputs reduce unnecessary verbosity.

---

# Context Management Strategies

## Problem

Most token waste occurs from repeatedly sending context.

Example:

```text
Here is my architecture...
[1000 tokens]

Here is my design...
[1000 tokens]

Here is my code...
[2000 tokens]
```

Repeated across dozens of prompts.

---

## Solution: Project Context Files

Create:

```text
PROJECT_CONTEXT.md
```

Example:

```markdown
# Project Context

Project: GEOS GPU Translation

Target:
- NVIDIA A100
- CUDA 12

Requirements:
- Preserve scientific fidelity
- Match baseline outputs

Coding Standards:
- C++17
- CMake

Known Constraints:
- MPI decomposition
- OpenMP currently used
```

Then prompt:

```text
Assume PROJECT_CONTEXT.md remains unchanged.

Task:
Translate this function to CUDA.
```

---

## Context Compression

Before continuing a long conversation:

Ask AI:

```text
Summarize this conversation in 20 bullet points.
```

Save the summary.

Start a new conversation using:

```text
Project Summary:
[paste summary]
```

This often reduces context size by 90%.

---

# Conversation Management

## Recommended

Create separate conversations for:

* GPU translation
* Bug fixing
* Documentation
* Performance optimization
* Architecture discussions

## Avoid

Single conversations spanning:

* Multiple projects
* Multiple months
* Multiple subsystems

Large conversations create token inflation.

---

# Code Translation Workflows

## Inefficient Workflow

```text
Translate this 3000-line module.
```

Results:

* Expensive
* Hard to review
* Often incorrect

---

## Efficient Workflow

### Step 1

```text
Analyze module.
Identify translation strategy.
```

### Step 2

```text
Identify GPU candidate regions.
```

### Step 3

```text
Translate function #1.
```

### Step 4

```text
Validate outputs.
```

### Step 5

```text
Translate next function.
```

---

# Patch-Based Development

Always prefer:

```text
Return only modified code.
```

or

```text
Return unified diff only.
```

Example:

```text
Current Function:
[function]

Change:
- Add GPU acceleration
- Preserve interface

Return patch only.
```

Benefits:

* Smaller responses
* Easier code review
* Lower token consumption

---

# Scientific Software Workflows

## GEOS

Recommended workflow:

```text
1. Summarize module
2. Identify numerical methods
3. Identify dependencies
4. Translate kernels
5. Validate outputs
6. Benchmark performance
```

---

## WRF

Recommended workflow:

```text
1. Analyze computational hotspots
2. Identify stencil operations
3. Design GPU strategy
4. Translate incrementally
```

---

## CRTM

Recommended workflow:

```text
1. Parse file structure
2. Validate dimensions
3. Optimize memory access
4. Introduce GPU acceleration
```

---

# Multi-Agent Workflows

Many modern AI platforms support multiple agents.

Recommended pattern:

## Architect Agent

Produces:

* Design
* Plan
* Requirements

---

## Developer Agent

Produces:

* Code

---

## Reviewer Agent

Produces:

* Validation
* Optimization recommendations

---

## Tester Agent

Produces:

* Unit tests
* Integration tests

---

Benefits:

* Better specialization
* Reduced rework
* Lower token waste

---

# Model Selection Recommendations

## Small Models

Use for:

* Documentation
* README generation
* Unit tests
* Refactoring
* Boilerplate code

Examples:

* Claude Haiku
* GPT Mini models

---

## Mid-Sized Models

Use for:

* Standard coding tasks
* Debugging
* Data pipelines

---

## Large Models

Use for:

* Scientific reasoning
* HPC optimization
* Architecture design
* Multi-file translation
* Research discussions

Examples:

* Claude Sonnet
* GPT-5
* Advanced reasoning models

---

# Example Prompt Templates

## Code Translation

```text
You are a compiler.

Task:
Translate the following code to CUDA.

Requirements:
- Preserve numerical behavior
- Preserve API
- No explanations
- Return compilable code only

Code:
[paste code]
```

---

## Bug Fixing

```text
You are a senior software engineer.

Task:
Identify root cause.

Output:
1. Root Cause
2. Fix
3. Validation Steps

Error:
[paste error]
```

---

## Performance Optimization

```text
Analyze this function.

Output:
1. Bottlenecks
2. GPU Opportunities
3. Memory Issues
4. Recommended Fixes

Limit response to 15 bullet points.
```

---

## Documentation

```text
Generate API documentation.

Requirements:
- Concise
- Markdown format
- Maximum 500 words
```

---

# Common Anti-Patterns

## Anti-Pattern 1

```text
Here's my entire repository.
```

Instead:

Provide only relevant files.

---

## Anti-Pattern 2

```text
Continue from above.
```

After 100+ messages.

Instead:

Use a compressed project summary.

---

## Anti-Pattern 3

```text
Explain every line.
```

Unless educational objectives justify it.

---

## Anti-Pattern 4

Requesting complete rewrites repeatedly.

Prefer:

```text
Generate patch only.
```

---

## Anti-Pattern 5

Using premium reasoning models for simple tasks.

Avoid using advanced models for:

* README generation
* Formatting
* Simple refactors

---

# Expected Savings

Organizations adopting these practices commonly report:

| Technique              | Typical Savings |
| ---------------------- | --------------- |
| Concise Outputs        | 20–50%          |
| Patch-Only Responses   | 50–90%          |
| Context Compression    | 70–95%          |
| Project Context Files  | 60–90%          |
| Separate Conversations | 30–70%          |
| Proper Model Selection | 25–80%          |

Combined savings often exceed:

```text
50–90% total token reduction
```

while maintaining equivalent engineering productivity.

---

# Recommended Team Standard

For scientific software engineering teams, the following standard is recommended:

1. Maintain a `PROJECT_CONTEXT.md` file.
2. Use separate conversations per subsystem.
3. Require patch-only code responses.
4. Compress context every 50–100 messages.
5. Reserve premium models for architecture and scientific reasoning.
6. Use small models for documentation and boilerplate generation.
7. Review AI-generated code exactly as human-generated code.
8. Track token consumption alongside engineering metrics.

Following these practices typically provides the best balance between cost, speed, and engineering effectiveness for AI-assisted development in research, HPC, and operational software environments.
