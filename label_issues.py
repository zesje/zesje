# # Categorize all issues
#
# To use: open with jupyter notebook/lab using jupytext and run all cells

# +
from getpass import getpass
from textwrap import dedent

from ipywidgets import Button, ToggleButtons, Output, VBox
from IPython.display import display, Markdown
import gitlab
# -

gl = gitlab.Gitlab(
    url='https://gitlab.kwant-project.org',
    private_token=getpass('Gitlab API token: ')
)
repo = gl.projects.get('zesje/zesje')

labels = repo.labels.list()

# +
label_dict = {
    tuple(label.name.split(': ')): label
    for label in labels
    if ': ' in label.name
}

categories = ['impact', 'effort', 'maintainability']
degrees = ['low', 'medium', 'high']

# +
description = Output()

selector = {
    category: ToggleButtons(
        options=[
            (degree, label_dict[category, degree])
            for degree in degrees
        ],
        description=category,
        label='medium',
        style={'button_color': label_dict}
    )
    for category in categories
}

submit = Button(
    description='submit & next',
    icon='check'
)

current_issue = None


def submit_labels(issue):
    other_labels = [i for i in issue.labels if ': ' not in i]
    issue.labels = [i.value.name for i in selector.values()] + other_labels
    issue.save()


def render_issue(issue):
    return Markdown(dedent(f"""### [{issue.title}]({issue.web_url})

    {issue.description}
    """))


def next_issue():
    issues = repo.issues.list(all=True, state='opened')
    for issue in issues:
        issue_categories = {
            label.split(': ')[0]: label.split(': ')[1]
            for label in issue.labels
            if ': ' in label
        }
        already_labeled = (
            len(issue_categories) == 3
            and len(set(issue_categories)) == 3
        )
        if not already_labeled:
            break
    else:
        submit.disabled = True
        submit.text = 'Done!'
        for button in selector.values():
            button.disabled = True

        return None

    description.clear_output(wait=True)
    with description:
        display(render_issue(issue))

    for category, degree in issue_categories.items():
        selector[category].label = degree

    return issue


def submit_and_next(event):
    global current_issue

    if current_issue is not None:
        submit_labels(current_issue)

    current_issue = next_issue()


submit.on_click(submit_and_next)


VBox(
    children=[description] + list(selector.values()) + [submit]
)
