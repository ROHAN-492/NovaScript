# NovaScript

**NovaScript** is a lightweight procedural scripting language developed as a Compiler Design Lab project. It implements lexical analysis, syntax analysis, and semantic analysis, and extends the pipeline with a static **Variable Dependency & Impact Analyzer**.

## Project Information

- **Course:** BCSE307P — Compiler Design Lab
- **Faculty:** Dr. Ranjithkumar S
- **Author:** Rohan R
- **Registration Number:** 24BCE0640

## Features

### 1. Lexical Analysis
- Converts source text into tokens such as keywords, identifiers, operators, literals, and symbols.
- Tracks line and column positions for tokens.
- Reports lexical errors such as unexpected characters and unterminated strings.

### 2. Syntax Analysis
- Parses the token stream and builds an Abstract Syntax Tree (AST).
- Represents program constructs including variable declarations, assignments, expressions, conditionals, loops, function definitions/calls, print statements, and return statements.

### 3. Semantic Analysis
- Checks whether identifiers have been declared before use.
- Maintains symbol tables and nested scopes.
- Detects duplicate declarations in a scope, invalid variable/function usage, incorrect function argument counts, and `return` statements outside functions.

### 4. Variable Dependency & Impact Analyzer
- Traverses the AST to identify variable references and dependency relationships.
- Reports direct dependencies, directly affected variables, and potential impact paths.
- Includes scope-aware records and considers selected control-flow relationships.
- Performs **static analysis**: it does not execute NovaScript programs or calculate runtime values.

## Compiler Pipeline

```text
NovaScript Source
       |
       v
Lexical Analysis
       |
       v
Token Stream
       |
       v
Syntax Analysis
       |
       v
Abstract Syntax Tree (AST)
       |
       v
Semantic Analysis
       |
       v
Variable Dependency & Impact Analysis
       |
       v
Dependency / Impact Report
```

## Example Program

```javascript
let price = 100;
let tax = price * 0.1;
let total = price + tax;

print(total);
```

Conceptual dependency flow:

```text
price ──> tax ──> total ──> print(total)
   └────────────> total
```

This illustrates how a change to `price` may affect `tax`, `total`, and the output statement. The analyzer reports potential dependencies based on program structure; it does not execute the program.

## Project Structure

```text
CD project/
├── examples/
│   └── test.nova
├── lexer.py
├── tokens.py
├── parser.py
├── semantic.py
├── symbol_table.py
├── impact_analyzer.py
├── trial.py
└── README.md
```

The exact files may vary slightly depending on the current working version.

## Requirements

- Python 3
- Visual Studio Code or another terminal/IDE

The core pipeline is intended to run with Python's standard library if no extra dependencies have been added.

## Run the Project

1. Open the project folder in Visual Studio Code.
2. Ensure `impact_analyzer.py` is in the same directory as `trial.py`.
3. Ensure the sample source file is at `examples/test.nova`.
4. Open the integrated terminal in the project root.
5. Run:

```powershell
python trial.py
```

If `python` is not available but the Python launcher is installed, try:

```powershell
py trial.py
```

The program runs lexical analysis, syntax analysis, semantic analysis, and—if earlier phases succeed—the variable dependency and impact analysis.

## Current Scope and Limitations

- The project focuses on lexical, syntax, and semantic analysis, plus static variable dependency and impact reporting.
- It does not implement an interpreter or execute NovaScript programs.
- It does not currently implement later phases such as intermediate-code generation, optimization, or machine-code generation.
- Dependency analysis represents potential influence; complex control flow and cross-function argument/return propagation may not be fully modeled.
- The semantic analyzer does not currently provide full datatype inference and type checking.

## Academic Context

This project was developed for **BCSE307P — Compiler Design Lab**. The dependency analyzer is an extension built on the AST and semantic information produced by the existing compiler phases.

---

**Author:** Rohan R  
**Registration Number:** 24BCE0640
