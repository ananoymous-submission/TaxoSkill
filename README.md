# TaxoSkill: Taxonomy-Guided Skill Optimization for Self-Evolving Agents

<p align="center">
  <a href="https://2027.coling-iccl.org"><img src="https://img.shields.io/badge/COLING-2027-4B6BFB" alt="COLING 2027"></a>
  <!-- <a href="#"><img src="https://img.shields.io/badge/Paper-PDF-B31B1B?logo=arxiv" alt="Paper PDF"></a> -->
  <!-- <a href="#"><img src="https://img.shields.io/badge/🤗-Models%20%26%20Results-FFD21E" alt="Models and results"></a> -->
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2EA44F" alt="MIT License"></a>
</p>

This repository is the official implementation of **TaxoSkill: Taxonomy-Guided Skill Optimization for Self-Evolving Agents** (COLING 2027 submission). 

<p align="center">
  <a href="#motivation">Motivation</a> ·
  <a href="#results">Results</a> ·
  <a href="#released-artifacts">Released Artifacts</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#repository-structure">Repository</a> ·
</p>

## Motivation

Two limitations are shared by most skill-optimization pipelines. First, rollouts are sampled at random, so rare task types receive too little signal as soon as the task pool is imbalanced. Second, the learned knowledge is delivered as one global skill that every task receives, which makes each task's context long and fills it with guidance written for unrelated tasks.

TaxoSkill addresses both. It discovers an interpretable taxonomy of reusable task types directly from task instructions, distributes the rollout budget uniformly across those types, and then splits the learned global skill into shared and type-specific guidance. Each task receives only the shared guidance plus the guidance for its own type. TaxoSkill is optimizer-agnostic: it coordinates task selection and skill organization without changing how an optimizer updates or validates skills.

## Results

Evaluated on **ALFWorld** and **ScienceWorld** with the reported protocol of four global optimization epochs followed by splitting, and no additional per-cluster training:

- **Clustering ablation.** TaxoSkill agrees more closely with the official task classes than the strongest standard clustering baseline, K-Means, reaching an AMI of **0.78 vs. 0.40** on ALFWorld and **0.96 vs. 0.94** on ScienceWorld, with consistent task assignments across discovery seeds.
- **Sampling ablation.** As class imbalance rises, taxonomy-uniform selection maintains class coverage while random sampling falls to **64.8%** on ALFWorld and **59.0%** on ScienceWorld.
- **Main results.** Under a matched optimization budget, TaxoSkill gains **1.7** percentage points of solve rate on ALFWorld and loses **0.2** on ScienceWorld, while random sampling loses **4.4** and **11.1** points. Splitting the global skill reduces the average injected skill size by **20.2%** and **55.3%**.

## Released Artifacts

Every result needed to reproduce the reported numbers is included under `results/`. Each discovered taxonomy is released as its final type list, and each learned skill as the markdown that was served.

| Path | Contents |
|---|---|
| `results/clustering_ablation/clusters/` | K-Means, Ward, and DBSCAN assignments per benchmark |
| `results/clustering_ablation/embeddings/` | Qwen3-Embedding-8B task vectors, so the clustering can be re-derived |
| `results/clustering_ablation/flows/` | Class-to-group flow diagrams per method and benchmark |
| `results/clustering_ablation/taxonomy_seeds/` | Discovered task types for seeds 0 to 4, one `types.json` per seed |
| `results/sampling_ablation/pools/` | Candidate pools across omission levels for both benchmarks |
| `results/sampling_ablation/per_pool_taxonomy/` | Task types discovered independently at each omission level |
| `results/main_results/skills/` | Learned global and per-cluster skills for every condition and seed |
| `results/main_results/evals/` | Per-run evaluation results for the runs reported in the paper |
| `results/main_results/routing/` | Inference routing decisions for the per-cluster condition |

## Quick Start

Requires **Python 3.11 or 3.12** and **uv**. Run commands from the repository root.

```bash
git clone <repository-url>
cd TaxoSkill
uv sync
```

Set the model API key and the environment endpoints in your shell or a local `.env` file (see `.env.example`). Model profiles live in `configs/models/` and benchmark configurations in `configs/experiments/`. The matching OpenEnv server must be reachable before launching anything; see the [ALFWorld](environments/alfworld/README.md) and [ScienceWorld](environments/scienceworld/README.md) setup guides.

Evaluate the ReAct agent without a learned skill:

```bash
uv run python -m taxoskill.run \
  --config configs/experiments/alfworld/base.yaml \
  agent.name=react
```

Train a global skill with taxonomy-uniform selection, then split it into shared and type-specific guidance:

```bash
uv run python -m taxoskill.optimization.skillopt.induction \
  --config configs/experiments/alfworld/cluster_cluster.yaml \
  optimization.train_count=50 optimization.validation_count=50 \
  skillopt.num_epochs=4 skillopt.batch_size=25

uv run python -m taxoskill.optimization.skillopt.skill_split \
  --config configs/experiments/alfworld/cluster_cluster.yaml \
  --skill outputs/skillopt/alfworld/seed_0/global_taxoskill_seed_0/best_skill.md
```

Taxonomy discovery, partition construction, and inference routing live under `src/taxoskill/optimization/`. Saved partitions and learned skills are prerequisites for these commands and are not downloaded automatically. Dotted configuration overrides must come after all command flags. New runs are written under `outputs/`, which this repository does not ship.

## Repository Structure

```text
TaxoSkill/
├── config.yaml                     # Base run configuration
├── pyproject.toml                  # Dependencies and package configuration
├── configs/
│   └── models/                     # Actor and optimizer model profiles
├── environments/
│   ├── alfworld/                   # OpenEnv server package
│   └── scienceworld/               # OpenEnv server package
├── results/
│   ├── clustering_ablation/        # Clusters, embeddings, flows, discovered types
│   ├── sampling_ablation/          # Candidate pools and per-pool taxonomies
│   └── main_results/               # Learned skills, evaluations, routing
└── src/taxoskill/
    ├── agents/                     # ReAct agent and prompts
    ├── optimization/
    │   ├── partitioning/           # Taxonomy discovery and clustering methods
    │   ├── selection/              # Random and taxonomy-uniform task selection
    │   └── skillopt/               # Skill optimization, splitting, routing
    └── run.py                      # Evaluation entry point
```

## License

This repository is released under the [MIT License](LICENSE).

## Acknowledgments

TaxoSkill builds on [SkillOpt](https://github.com/microsoft/SkillOpt) and [OpenEnv](https://github.com/huggingface/OpenEnv) for skill optimization and environment serving, and evaluates on the [ALFWorld](https://github.com/alfworld/alfworld) and [ScienceWorld](https://github.com/allenai/ScienceWorld) benchmarks. Task embeddings use [Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B).
