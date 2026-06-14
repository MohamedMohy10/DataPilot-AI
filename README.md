# 📊 DataPilot AI - Autonomous data analysis system. 
Upload any CSV dataset, ask a question, and the agent autonomously performs end-to-end analusis, it plans, executes, reflects, and synthesizes a full analytical report with visualizations.

## 🎯 What is special about DataPilot AI ?

While general LLMs can analyze datasets interactively, they are not designed to execute structured, multi-step analytical workflows with reliability and reproducibility.

**DataPilot AI transforms data analysis into an autonomous system that:**

- Plans analysis strategies before execution  
- Runs real Python code (not simulated answers)  
- Iteratively fixes errors and refines results  
- Maintains state across steps for consistent reasoning  
- Produces structured, reproducible outputs (plots, dashboards, reports)

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
git clone https://github.com/MohamedMohy10/DataPilot-AI.git
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
## ⚠️ Limitations 
- This is still a demo version, so mistakes or bugs are expected
- Performance depends on LLM latency and API limits
- Complex datasets may increase execution time
- Requires careful prompt design for optimal results

  Examples of a good prompt:
  ```
  "Analyze this dataset and find key insights, correlations, and anomalies"
  ```
  ```
  "Perform full EDA, detect anomalies, test hypotheses, and generate key insights with visualizations.
   Rules:
  - All insights must include numerical evidence
  - Use statistical validation where applicable
  - Keep conclusions concise and grounded
   "
  ```
  ```
  "Perform a comprehensive exploratory data analysis (EDA) of this dataset. Identify data quality issues (missing values, duplicates, outliers, inconsistent    values), summarize the distributions of all variables, analyze relationships between features, identify the key drivers of employee attrition, generate      appropriate visualizations, and conclude with actionable business recommendations. Explain every major finding and justify your conclusions using            evidence from the data."
  ```
  ```
  Analyze the dataset and provide business insights to improve profitability.
  ```
  ```
  If you were a manager, what actions would you take based on this data?
  ```
  ---
  ## Screenshots

  <img width="1230" height="563" alt="image" src="https://github.com/user-attachments/assets/c0c3699b-c3df-4a11-830d-9d4cbbcdef66" />
  <img width="1400" height="663" alt="Screenshot 2026-06-14 174247" src="https://github.com/user-attachments/assets/4ee80365-aa47-43fe-9cf2-61bb99496b4a" />
  <img width="1418" height="759" alt="Screenshot 2026-06-14 174417" src="https://github.com/user-attachments/assets/6e6be453-0b8e-4bde-8d90-93e967adf220" />
  <img width="1422" height="702" alt="Screenshot 2026-06-14 174440" src="https://github.com/user-attachments/assets/c8c42eb6-83b2-44d9-8200-158ef74429fe" />
  <img width="1437" height="483" alt="Screenshot 2026-06-14 174548" src="https://github.com/user-attachments/assets/1350d2ed-66d3-4261-96f7-24ffd6835b5d" />
  <img width="1092" height="477" alt="Screenshot 2026-06-14 174624" src="https://github.com/user-attachments/assets/d0cc7076-acb6-4e8f-bbde-f127f7f23498" />

  Which regions and product categories are underperforming and why?
  ```
