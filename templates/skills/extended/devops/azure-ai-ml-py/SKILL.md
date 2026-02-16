---
name: azure-ai-ml-py
description: |
  Azure Machine Learning SDK v2 for Python. Use for ML workspaces, jobs, models, datasets, compute, and pipelines.
  Triggers: "azure-ai-ml", "MLClient", "workspace", "model registry", "training jobs", "datasets".
package: azure-ai-ml
---

# Azure Machine Learning SDK v2 for Python

Client library for managing Azure ML resources: workspaces, jobs, models, data, and compute.

## Installation

```bash
pip install azure-ai-ml
```

## Environment Variables

```bash
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_RESOURCE_GROUP=<your-resource-group>
AZURE_ML_WORKSPACE_NAME=<your-workspace-name>
```

## Authentication

```python
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

ml_client = MLClient(
    credential=DefaultAzureCredential(),
    subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
    resource_group_name=os.environ["AZURE_RESOURCE_GROUP"],
    workspace_name=os.environ["AZURE_ML_WORKSPACE_NAME"]
)
```

### From Config File

```python
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

# Uses config.json in current directory or parent
ml_client = MLClient.from_config(
    credential=DefaultAzureCredential()
)
```

## Workspace Management

### Create Workspace

```python
from azure.ai.ml.entities import Workspace

ws = Workspace(
    name="my-workspace",
    location="eastus",
    display_name="My Workspace",
    description="ML workspace for experiments",
    tags={"purpose": "demo"}
)

ml_client.workspaces.begin_create(ws).result()
```

### List Workspaces

```python
for ws in ml_client.workspaces.list():
    print(f"{ws.name}: {ws.location}")
```

## Data Assets

### Register Data

```python
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes

# Register a file
my_data = Data(
    name="my-dataset",
    version="1",
    path="azureml://datastores/workspaceblobstore/paths/data/train.csv",
    type=AssetTypes.URI_FILE,
    description="Training data"
)

ml_client.data.create_or_update(my_data)
```

### Register Folder

```python
my_data = Data(
    name="my-folder-dataset",
    version="1",
    path="azureml://datastores/workspaceblobstore/paths/data/",
    type=AssetTypes.URI_FOLDER
)

ml_client.data.create_or_update(my_data)
```

## Model Registry

### Register Model

```python
from azure.ai.ml.entities import Model
from azure.ai.ml.constants import AssetTypes

model = Model(
    name="my-model",
    version="1",
    path="./model/",
    type=AssetTypes.CUSTOM_MODEL,
    description="My trained model"
)

ml_client.models.create_or_update(model)
```

### List Models

```python
for model in ml_client.models.list(name="my-model"):
    print(f"{model.name} v{model.version}")
```

## Compute

### Create Compute Cluster

```python
from azure.ai.ml.entities import AmlCompute

cluster = AmlCompute(
    name="cpu-cluster",
    type="amlcompute",
    size="Standard_DS3_v2",
    min_instances=0,
    max_instances=4,
    idle_time_before_scale_down=120
)

ml_client.compute.begin_create_or_update(cluster).result()
```

### List Compute

```python
for compute in ml_client.compute.list():
    print(f"{compute.name}: {compute.type}")
```

## Jobs

### Command Job

```python
from azure.ai.ml import command, Input

job = command(
    code="./src",
    command="python train.py --data ${{inputs.data}} --lr ${{inputs.learning_rate}}",
    inputs={
        "data": Input(type="uri_folder", path="azureml:my-dataset:1"),
        "learning_rate": 0.01
    },
    environment="AzureML-sklearn-1.0-ubuntu20.04-py38-cpu@latest",
    compute="cpu-cluster",
    display_name="training-job"
)

returned_job = ml_client.jobs.create_or_update(job)
print(f"Job URL: {returned_job.studio_url}")
```

### Monitor Job

```python
ml_client.jobs.stream(returned_job.name)
```

## Pipelines

```python
from azure.ai.ml import dsl, Input, Output
from azure.ai.ml.entities import Pipeline

@dsl.pipeline(
    compute="cpu-cluster",
    description="Training pipeline"
)
def training_pipeline(data_input):
    prep_step = prep_component(data=data_input)
    train_step = train_component(
        data=prep_step.outputs.output_data,
        learning_rate=0.01
    )
    return {"model": train_step.outputs.model}

pipeline = training_pipeline(
    data_input=Input(type="uri_folder", path="azureml:my-dataset:1")
)

pipeline_job = ml_client.jobs.create_or_update(pipeline)
```

## Environments

### Create Custom Environment

```python
from azure.ai.ml.entities import Environment

env = Environment(
    name="my-env",
    version="1",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04",
    conda_file="./environment.yml"
)

ml_client.environments.create_or_update(env)
```

## Datastores

### List Datastores

```python
for ds in ml_client.datastores.list():
    print(f"{ds.name}: {ds.type}")
```

### Get Default Datastore

```python
default_ds = ml_client.datastores.get_default()
print(f"Default: {default_ds.name}")
```

## MLClient Operations

| Property | Operations |
|----------|------------|
| `workspaces` | create, get, list, delete |
| `jobs` | create_or_update, get, list, stream, cancel |
| `models` | create_or_update, get, list, archive |
| `data` | create_or_update, get, list |
| `compute` | begin_create_or_update, get, list, delete |
| `environments` | create_or_update, get, list |
| `datastores` | create_or_update, get, list, get_default |
| `components` | create_or_update, get, list |

## Best Practices

1. **Use versioning** for data, models, and environments
2. **Configure idle scale-down** to reduce compute costs
3. **Use environments** for reproducible training
4. **Stream job logs** to monitor progress
5. **Register models** after successful training jobs
6. **Use pipelines** for multi-step workflows
7. **Tag resources** for organization and cost tracking


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags azure-ai-ml-py <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
