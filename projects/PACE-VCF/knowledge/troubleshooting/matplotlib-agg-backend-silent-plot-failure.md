# Troubleshooting: `plt.show()` runs but no plot appears

## Symptom

A Jupyter cell calls `plt.show()`, runs without any error, and produces no
visible output -- no plot, no exception, nothing.

## Confirmed cause

The matplotlib backend controls where a figure goes when `plt.show()` is
called. Jupyter normally defaults to an inline backend that embeds the
figure as output in the cell. A colleague's imported package (used for model
loading/inference in a downstream notebook) calls `matplotlib.use("Agg")` as
an import-time side effect in two of its modules -- `Agg` renders to an
image buffer only and is never displayed anywhere, by design (it's meant for
headless/batch `savefig()`-only usage). Because that package was imported
*after* `matplotlib.pyplot`, its `matplotlib.use("Agg")` call silently
switched the already-active inline backend to the non-interactive one. From
that point on in the same kernel process, `plt.show()` is a no-op.

This also leaks across notebooks: the backend is a property of the running
kernel *process*, not of the notebook file. A notebook that never imports
the offending package can still show this symptom if it's running in a
kernel session that previously executed a cell that did.

## Resolution

Add `%matplotlib inline` (a Jupyter magic, not a Python function) as the
first line of the affected plotting cell -- it forces the backend back to
the inline one immediately before that cell draws its figure, regardless of
what earlier imports did.

## Diagnostic

```python
import matplotlib
print(matplotlib.get_backend())
```

If this prints `agg` (lowercase), that's the cause. If it prints something
else (e.g. `module://matplotlib_inline.backend_inline`), the backend is
fine and the missing-plot symptom has a different cause (e.g. an empty
results loop that never reaches the plotting code).
