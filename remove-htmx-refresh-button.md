# Remove the "Refresh Budgets with HTMX" button

This guide removes the HTMX refresh button from the budget page without breaking the rest of the app.

## 1) Open the frontend page

Go to [budget-manager/frontend/index.html](budget-manager/frontend/index.html).

Find the block that looks like this:

```html
<button
    type="button"
    hx-get="http://127.0.0.1:5004/budgets-html"
    hx-target="#htmxResult"
    hx-swap="innerHTML">
    Refresh Budgets with HTMX
</button>
```

## 2) Delete the button markup

Remove the entire button block from the HTML.

After removal, the section should look like this:

```html
<h2>Budgets</h2>

<div id="htmxResult"></div>
```

If you do not need the HTMX result container either, you can delete:

```html
<div id="htmxResult"></div>
```

## 3) Optional: remove the HTMX script

If this button is the only reason HTMX is being used, remove the script tag from the head of [budget-manager/frontend/index.html](budget-manager/frontend/index.html):

```html
<!-- HTMX -->
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
```

This is optional. Leave it if you may still use HTMX elsewhere in the app later.

## 4) Optional: remove the backend HTMX route

If the button is gone and you no longer want the endpoint at all, remove the HTMX route from [budget-manager/backend/app.py](budget-manager/backend/app.py):

```python
# HTMX route
@app.route("/budgets-html", methods=["GET"])
def get_budgets_html():
    ...
```

This route is only used by the refresh button, so deleting it prevents unused HTMX-specific code from remaining in the backend.

## 5) Reload the app

Restart the frontend if needed, then refresh the page in the browser.

You should no longer see the button labeled "Refresh Budgets with HTMX".

## 6) Final cleanup

Check the page again for any leftover references to:

- `hx-get`
- `hx-target`
- `hx-swap`
- `htmxResult`
- `HTMX`

If none are needed, they can be removed as part of the cleanup.

## Quick summary

The main change is simply deleting the button from [budget-manager/frontend/index.html](budget-manager/frontend/index.html). The HTMX script and backend route can be removed afterward if you want the project to be fully clean.
