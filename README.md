# 📊 DataPilot AI - Autonomous data analysis system. 
Upload any CSV dataset, ask a question, and the agent autonomously performs end-to-end analusis, it plans, executes, reflects, and synthesizes a full analytical report with visualizations.

## 🎯 What is special about DataPilot AI ?

While general LLMs can analyze datasets interactively, they are not designed to execute structured, multi-step analytical workflows with reliability and reproducibility.

**DataPilot AI transforms data analysis into an autonomous system that:**

- Plans analysis strategies before execution  
- Runs real Python code (not simulated answers)  
- Iteratively fixes errors and refines results  
- Maintains state across steps for consistent reasoning  
- Produces structured, reproducible outputs (plots, reports)

## 🧠 Architecture

The system is implemented as a **LangGraph state machine** with the following nodes:
[Planner] → [Executor] → [Evaluator] → [Memory] → (loop or finalize)
↓
[Final Answer]

- **Planner Node** : Decomposes the user query into analysis steps
- **Executor Node** : Generates and executes Python code with self-healing retry loop
- **Evaluator Node** : Reflects on progress and decides whether to continue or finalize
- **Memory Node** : Persists dataframe state and insights across steps
- **Final Answer Node** : Synthesizes all findings into a structured report

## ✨ Features

- 🔄 **ReAct agent loop** : Plan → Act → Observe → Reflect → Repeat
- 🐍 **Dynamic code execution** : LLM writes and runs pandas/matplotlib code
- 🔁 **Self-healing retries** : Agent fixes its own errors automatically
- 📊 **Auto EDA** : Automatic profiling on upload
- 💬 **Follow-up chat** : Continue conversing after report generation
- 📈 **On-demand plots** : Request new visualizations in chat
- 📄 **PDF export** : Download full report with embedded plots
- 🖥️ **Streamlit UI** : Clean web interface

## 🛠️ Tech Stack

- **Orchestration:** LangGraph, LangChain
- **LLM:** OpenRouter API (OpenAI-compatible)
- **Backend:** Python, pandas, numpy, matplotlib, seaborn
- **Frontend:** Streamlit
- **PDF:** ReportLab

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/agentic-data-analyst.git
cd agentic-data-analyst
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment
```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

### 4. Run
```bash
streamlit run app.py
```

## 📁 Project Structure
```bash
data-analyst-agent/
├── app.py                  # Streamlit UI
├── graph.py                # LangGraph state machine
├── state.py                # Shared agent state
├── config.py               # Configuration
├── pdf_generator.py        # PDF report generation
├── nodes/
│   ├── planner.py          # Planning node
│   ├── executor.py         # Code execution node
│   ├── evaluator.py        # Reflection node
│   ├── memory.py           # State management node
│   └── final_answer.py     # Report synthesis node
├── tools/
│   ├── python_runner.py    # Safe code executor
│   ├── eda.py              # Auto EDA
│   └── registry.py        # Tool schemas
├── prompts/                # LLM prompt templates
├── memory/                 # Session memory
└── observability/          # Agent tracing
```

## 📋 Example Queries

- *"Analyze this dataset and find key insights, correlations, and anomalies."*
- *"What factors most influence survival rate?"*
- *"Show age distribution for survivors vs non-survivors."*
- *"Draw a bar chart of average fare by passenger class."*

## 🔑 Environment Variables
NVIDIA_API_KEY=your_key_here

Get a free key at [NVIDIA](https://build.nvidia.com/)

Also create `.env` file, inside it write
`NVIDIA_API_KEY`=your_api_key_here

you can of course use any other LLm api you have, NVIDIA is just an example and what was used during the development and testing of this project.

---
⚠️ Limitations 
- This is still a demo version, so mistakes or bugs are expected
- Performance depends on LLM latency and API limits
- Complex datasets may increase execution time
- Requires careful prompt design for optimal results
