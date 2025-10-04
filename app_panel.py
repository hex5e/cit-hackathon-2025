import panel as pn
import pandas as pd
import param

pn.extension('tabulator', notifications=True)

CSS = """
/* Subtle, clean styling to echo the mock */
:root {
  --card-radius: 16px;
}

.card {
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  border-radius: var(--card-radius);
  background: white;
  padding: 20px;
}

.hint {
  color: #475569;
  font-size: 16px;
}

h1.title {
  font-size: 48px;
  line-height: 1.1;
  margin: 0 0 8px 0;
}

.grid-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 900px){
  .grid-two { grid-template-columns: 1fr; }
}
"""

pn.extension(raw_css=[CSS])

INITIAL_PEOPLE = [
    {"first_name": "Ada", "last_name": "Lovelace", "zip": "20500"},
    {"first_name": "Alan", "last_name": "Turing", "zip": "02142"},
    {"first_name": "Grace", "last_name": "Hopper", "zip": "10001"},
    {"first_name": "German", "last_name": "Sheperd", "zip": "43147"},
]


class Directory(param.Parameterized):
    first_name = param.String(default="")
    last_name = param.String(default="")
    zip_code = param.String(default="")

    people = param.List(default=list(INITIAL_PEOPLE))

    def _to_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.people, columns=["first_name", "last_name", "zip"])  # keep order
        df.rename(columns={"first_name": "First name", "last_name": "Last name", "zip": "ZIP"}, inplace=True)
        return df

    @param.depends("people")
    def people_table(self):
        df = self._to_df()
        return pn.widgets.Tabulator(
            df,
            show_index=False,
            layout="fit_columns",
            selectable=False,
            theme="simple",
            configuration={
                "columnHeaderVertAlign": "middle",
            },
            height=360,
        )

    def save(self, *_):
        # Basic validation: required fields and 5-digit zip
        first = self.first_name.strip()
        last = self.last_name.strip()
        zipc = self.zip_code.strip()

        if not first or not last or not zipc:
            pn.state.notifications.warning("Please fill out all fields.")
            return

        if not (zipc.isdigit() and 3 <= len(zipc) <= 10):
            # len range allows leading zeros (string) and international-ish zips
            pn.state.notifications.warning("ZIP should be numeric (3–10 digits).")
            return

        self.people = self.people + [{"first_name": first, "last_name": last, "zip": zipc}]

        # Clear fields
        self.first_name = ""
        self.last_name = ""
        self.zip_code = ""

        pn.state.notifications.success("Saved to directory.")


directory = Directory()

# --- Header ---
header = pn.Column(
    pn.pane.Markdown("# <span class='title'>Community Directory</span>", sizing_mode="stretch_width"),
    pn.pane.Markdown(
        """
        <div class="hint">
        This streamlined demo keeps only the essentials: first name, last name, and ZIP code. 
        Add new entries with the form below and they appear instantly in the directory list.
        </div>
        """,
        sizing_mode="stretch_width",
    ),
    css_classes=["card"],
)

# --- Form Card ---
first_in = pn.widgets.TextInput(name="First name", placeholder="e.g. Ada", value="", sizing_mode="stretch_width")
last_in = pn.widgets.TextInput(name="Last name", placeholder="e.g. Lovelace", value="", sizing_mode="stretch_width")
zip_in = pn.widgets.TextInput(name="ZIP code", placeholder="e.g. 20500", value="", sizing_mode="stretch_width")

# Link widgets to parameters
pn.bind(lambda v: setattr(directory, 'first_name', v), first_in, watch=True)
pn.bind(lambda v: setattr(directory, 'last_name', v), last_in, watch=True)
pn.bind(lambda v: setattr(directory, 'zip_code', v), zip_in, watch=True)

save_btn = pn.widgets.Button(name="Save", button_type="primary", width=120, height=40)
save_btn.on_click(directory.save)

form_card = pn.Column(
    pn.pane.Markdown("## Add a person"),
    first_in,
    last_in,
    zip_in,
    pn.Row(save_btn),
    css_classes=["card"],
)

# --- People Card ---
people_card = pn.Column(
    pn.pane.Markdown("## People"),
    directory.people_table,
    css_classes=["card"],
)

body = pn.Column(
    header,
    pn.Row(
        pn.layout.HSpacer(),
        sizing_mode="stretch_width",
    ),
    pn.Column(
        pn.Row(),
        pn.pane.HTML("<div class='grid-two'></div>", height=0),  # ensures CSS is loaded
        pn.Row(form_card, people_card, sizing_mode="stretch_width"),
        sizing_mode="stretch_width",
    ),
    sizing_mode="stretch_width",
    margin=(10, 16),
)

# Template for a polished feel and responsive layout
TEMPLATE = pn.template.FastListTemplate(
    title="",
    sidebar=[],
    main=[body],
)

# Serveable object
app = TEMPLATE

# For `panel serve panel_community_directory.py` compatibility
if __name__.startswith("bokeh"):  # pragma: no cover
    TEMPLATE.servable()
