# CyberRisk DSS

**CyberRisk DSS** is a research-oriented decision support system for assessing cybersecurity risks in an enterprise information infrastructure and selecting risk mitigation measures under budget and acceptable residual-risk constraints.

The application is implemented in Python with Streamlit and SQLite. It supports a structured workflow from documenting information assets, threats, and vulnerabilities to assessing risk, comparing candidate safeguards, and reviewing modeled outcomes.

> **Research scope:** CyberRisk DSS is an experimental decision-support application. It does not automatically scan networks, discover vulnerabilities, deploy security controls, or verify actual risk reduction in a production enterprise.

## Key capabilities

- **Information asset inventory:** record and manage assets, their attributes, and criticality.
- **Threat and vulnerability registers:** document risks and associate relevant information with assets.
- **Risk assessment:** calculate and visualize modeled risk scores, including a risk matrix.
- **Mitigation comparison:** compare specialist-defined candidate security measures using estimated cost and residual risk.
- **Constraint-based recommendations:** filter out candidates that exceed the available budget or do not meet the acceptable residual-risk threshold; among eligible measures, prioritize the lowest residual risk, then the lowest cost, with a deterministic tie-breaker.
- **Analysis and reporting:** review experiment outputs, visualizations, and summaries within the Streamlit interface.

All input values and candidate measures must be supplied or reviewed by a specialist. Recommendations depend on the quality and assumptions of those inputs.

## Technology stack

- Python 3
- Streamlit
- SQLite
- pandas, NumPy, Matplotlib, and Plotly
- HTML/CSS styling for the application interface

## Run locally

### 1. Prepare the environment

From the project directory, create a virtual environment and install dependencies:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Using the virtual environment's Python is recommended. On Windows, you can activate it with `.venv\Scripts\activate` in Command Prompt, or `.venv\Scripts\Activate.ps1` in PowerShell.

### 2. Start the application

```bash
python -m streamlit run navigation.py
```

By default, Streamlit opens at `http://localhost:8501`.

**Note:** The application uses a local SQLite database, which is excluded from version control. Database initialization and locally entered records are not provided as a prepopulated enterprise dataset in this repository.

## Project structure

```text
CyberRisk_DSS/
├── navigation.py                 # Streamlit application entry point
├── pages/                        # User interface pages
├── styles/                       # Page-specific stylesheets
├── database.py                   # Local SQLite data operations
├── risk_model.py                 # Risk evaluation logic
├── risk_constraints.py           # Budget and residual-risk constraints
├── experiment_analysis.py        # Experiment-related analysis
├── experiment_results/           # Exported research results and charts
├── .streamlit/config.toml        # Interface configuration
└── requirements.txt              # Python dependencies
```

## Research and validation

The project includes a mathematical risk-model study across **125 input combinations**, focused program checks, and modeled cybersecurity scenarios. Two network-security scenarios were investigated separately in **Cisco Packet Tracer**, using access control lists (ACLs) and Port Security.

The exported materials in `experiment_results/` document modeled results; they must not be interpreted as measurements from a live enterprise environment. Cisco Packet Tracer was used as an independent network simulation environment rather than as a component of the application.

## Limitations

- Risk values, mitigation effectiveness, and costs are model estimates based on entered parameters.
- The system is intended to support expert decisions, not replace cybersecurity assessment by a qualified specialist.
- Results obtained in test and simulation environments do not constitute evidence of deployment or performance in a production organization.
- Additional integration, security, and acceptance testing would be required before operational use.

## Academic context

Developed as the software component of a master's research project on **decision support for managing cyber risks in enterprise information infrastructure**.
