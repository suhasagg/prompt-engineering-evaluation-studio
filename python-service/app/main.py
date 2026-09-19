from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Literal
import json, re, time, uuid, statistics
from difflib import SequenceMatcher

app = FastAPI(title="Prompt Engineering & Evaluation Studio", version="1.0.0")
EXPERIMENTS: dict[str, dict] = {}

class PromptVariant(BaseModel):
    name: str
    template: str

class Example(BaseModel):
    input: str
    expected: Any | None = None

class ExperimentRequest(BaseModel):
    name: str = "experiment"
    models: list[str] = Field(default_factory=lambda:["mock-balanced","mock-strict"])
    prompts: list[PromptVariant]
    dataset: list[Example]
    output_mode: Literal["text","json"] = "text"
    json_required_keys: list[str] = Field(default_factory=list)


def render(template: str, value: str) -> str:
    return template.replace("{{input}}", value)

def mock_model(model: str, prompt: str, output_mode: str):
    # Deterministic offline adapter. Replace/add adapters for Azure OpenAI/OpenAI/local models.
    raw = prompt.split("INPUT:")[-1].strip() if "INPUT:" in prompt else prompt
    if output_mode == "json":
        sentiment = "positive" if any(w in raw.lower() for w in ["great","love","excellent","good"]) else "negative" if any(w in raw.lower() for w in ["bad","hate","terrible","poor"]) else "neutral"
        if model == "mock-strict":
            return json.dumps({"sentiment": sentiment, "answer": raw[:120]}, ensure_ascii=False)
        return json.dumps({"answer": raw[:120], "sentiment": sentiment}, ensure_ascii=False)
    if model == "mock-strict":
        return raw[:180].strip()
    return f"Answer: {raw[:170].strip()}"

def normalize(x: Any) -> str:
    if isinstance(x, (dict,list)):
        return json.dumps(x, sort_keys=True, ensure_ascii=False)
    return str(x or "").strip().lower()

def score(expected: Any, actual: Any) -> float | None:
    if expected is None: return None
    return round(SequenceMatcher(None, normalize(expected), normalize(actual)).ratio(), 4)

def json_metrics(text: str, required: list[str]):
    try:
        obj = json.loads(text)
        valid = True
        keys_ok = all(k in obj for k in required) if isinstance(obj, dict) else not required
        return obj, valid, keys_ok
    except Exception:
        return text, False, False

@app.get("/health")
def health(): return {"status":"ok"}

@app.post("/api/v1/experiments")
def run_experiment(req: ExperimentRequest):
    if not req.prompts or not req.dataset or not req.models:
        raise HTTPException(400, "models, prompts and dataset must be non-empty")
    exp_id = str(uuid.uuid4())
    rows=[]
    for model in req.models:
        for variant in req.prompts:
            for i, ex in enumerate(req.dataset):
                prompt=render(variant.template, ex.input)
                start=time.perf_counter()
                output=mock_model(model,prompt,req.output_mode)
                latency=round((time.perf_counter()-start)*1000,3)
                parsed=output; valid_json=None; schema_ok=None
                if req.output_mode == "json":
                    parsed,valid_json,schema_ok=json_metrics(output,req.json_required_keys)
                rows.append({"model":model,"prompt":variant.name,"example":i,"input":ex.input,"output":parsed,
                             "accuracy":score(ex.expected,parsed),"valid_json":valid_json,"schema_ok":schema_ok,
                             "latency_ms":latency,"chars":len(output)})
    groups={}
    for r in rows:
        key=(r["model"],r["prompt"]); groups.setdefault(key,[]).append(r)
    summary=[]
    for (model,prompt),rs in groups.items():
        acc=[r["accuracy"] for r in rs if r["accuracy"] is not None]
        summary.append({"model":model,"prompt":prompt,"cases":len(rs),
          "avg_accuracy":round(statistics.mean(acc),4) if acc else None,
          "json_valid_rate":round(sum(r["valid_json"] is True for r in rs)/len(rs),4) if req.output_mode=="json" else None,
          "schema_pass_rate":round(sum(r["schema_ok"] is True for r in rs)/len(rs),4) if req.output_mode=="json" else None,
          "avg_latency_ms":round(statistics.mean(r["latency_ms"] for r in rs),3)})
    result={"id":exp_id,"name":req.name,"summary":summary,"results":rows}
    EXPERIMENTS[exp_id]=result
    return result

@app.get("/api/v1/experiments/{exp_id}")
def get_experiment(exp_id: str):
    if exp_id not in EXPERIMENTS: raise HTTPException(404,"experiment not found")
    return EXPERIMENTS[exp_id]

@app.get("/api/v1/analytics")
def analytics():
    return {"experiments":len(EXPERIMENTS),"runs":sum(len(x["results"]) for x in EXPERIMENTS.values())}
