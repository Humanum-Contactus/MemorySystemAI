---
name: baby-organism
description: Relaye vers un nœud Sensors&MemorySystemAI / MemorySystemAI organism (perception, mémoires, ask humain).
user-invocable: true
metadata:
  openclaw:
    requires:
      bins: ["python"]
---

# Bébé organism (memory-node)

Organisme **quasi vide** : mémoire sensorielle-émotionnelle + outils (see/hear/speak/consult_llm/ask_human).
Le LLM est un **outil de consultation**, pas l’identité.

> **Attention concept :** ce skill + `ask_poller.py` sont un **pont** (Telegram),
> pas le cœur MemorySystemAI. Grossir ce canal = risque de retomber en chatbot.
> Les normes (ex. ne pas harceler le tuteur) vivent dans `memory_index` du nœud.

## Config

```bash
set MEMORY_NODE_URL=http://IP_DU_NOEUD:8765
```

## Commandes (`exec`)

```powershell
python PATH/TO/prototypes/memory-node/openclaw-skill/baby_api.py status
python PATH/TO/prototypes/memory-node/openclaw-skill/baby_api.py ask
python PATH/TO/prototypes/memory-node/openclaw-skill/baby_api.py perceive TEXTE
python PATH/TO/prototypes/memory-node/openclaw-skill/baby_api.py answer REPONSE
```

## Flux Telegram

1. Toujours `ask` puis `status` si l’utilisateur parle du bébé.
2. Si `ask.status == pending` → montrer la question, attendre, puis `answer …`.
3. Pour enseigner / interroger → `perceive …`.
4. Répondre avec `result.utterance` + `source` (`memory` / `llm-tool` / `ask-human` / `ask-inhibited`).

Ne pas inventer la personnalité du bébé : tu es le relais.
