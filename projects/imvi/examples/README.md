# IMVI contribution examples

These examples describe where information belongs; they do not assert facts about IMVI.

## Add a dataset note

Copy `templates/dataset-entry/README.md` to:

```text
projects/imvi/knowledge/datasets/<dataset-name>.md
```

Document how IMVI uses the dataset, where approved users obtain it, its important fields, and known limitations. Do not commit protected data.

## Add a model entry

Copy `templates/model-entry/` to:

```text
projects/imvi/knowledge/models/<model-name>/
```

Describe how to configure, run, diagnose, and validate the model. If multiple projects use it, promote the entry to `knowledge/models/`.

## Add a troubleshooting note

For a recurring issue, add:

```text
projects/imvi/knowledge/troubleshooting/<short-problem-name>.md
```

Include symptoms, confirmed causes, safe diagnostic commands, resolution steps, and the environment in which the resolution was verified.

## Add a skill

Create a skill only when the procedure is repeatable and an agent should carry it out. Begin with `templates/skill/example-skill/`, rename the directory and skill, and add an evaluation case.
