"""
WorkoutAI — Dash application entry point.

Run with:
    python app.py
"""

import uuid

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, clientside_callback, ctx, dcc, html

import db.database as database
from agents import consistency, diet, onboarding, workout
from db.database import format_profile

# ---------------------------------------------------------------------------
# Initialise DB on startup
# ---------------------------------------------------------------------------
database.init_db()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="WorkoutAI",
)
server = app.server  # expose for WSGI deployment

# ---------------------------------------------------------------------------
# Helper: map tab value → agent instance
# ---------------------------------------------------------------------------
AGENTS = {
    "profile": onboarding.agent,
    "workout": workout.agent,
    "consistency": consistency.agent,
    "diet": diet.agent,
}

TABS = [
    {"value": "profile",     "label": "Profile",     "icon": "🧑"},
    {"value": "workout",     "label": "Workout",     "icon": "🏋️"},
    {"value": "consistency", "label": "Consistency", "icon": "📅"},
    {"value": "diet",        "label": "Diet",        "icon": "🥗"},
]

# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def _message_bubble(role: str, text: str) -> html.Div:
    """Render a single chat message bubble."""
    is_user = role == "user"
    bubble = html.Div(
        dcc.Markdown(
            text,
            style={"margin": 0},
        ) if not is_user else text,
        className="p-2 px-3",
        style={
            "maxWidth": "78%",
            "borderRadius": "18px",
            "backgroundColor": "#0d6efd" if is_user else "#ffffff",
            "color": "#ffffff" if is_user else "#212529",
            "boxShadow": "0 1px 2px rgba(0,0,0,0.1)",
            "fontSize": "0.93rem",
            "lineHeight": "1.5",
        },
    )
    return html.Div(
        bubble,
        className="d-flex mb-2 " + ("justify-content-end" if is_user else "justify-content-start"),
    )


def _render_messages(messages: list[dict]) -> list:
    """Convert a list of {role, text} dicts to Dash components."""
    if not messages:
        return [
            html.Div(
                html.P("Send a message to get started.", className="text-muted"),
                className="d-flex justify-content-center align-items-center h-100",
            )
        ]
    return [_message_bubble(m["role"], m["text"]) for m in messages]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
app.layout = dbc.Container(
    [
        # Header
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Span("💪", style={"fontSize": "1.6rem", "marginRight": "8px"}),
                        html.Span("WorkoutAI", className="fw-bold"),
                    ],
                    className="d-flex align-items-center justify-content-center py-3",
                    style={"fontSize": "1.5rem", "color": "#0d6efd"},
                ),
                width=12,
            )
        ),
        # Tabs
        dbc.Row(
            dbc.Col(
                dbc.Tabs(
                    [
                        dbc.Tab(label=f"{t['icon']} {t['label']}", tab_id=t["value"])
                        for t in TABS
                    ],
                    id="active-tab",
                    active_tab="profile",
                ),
                width=12,
            ),
            className="mb-2",
        ),
        # Chat display
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="chat-display",
                    style={
                        "height": "460px",
                        "overflowY": "auto",
                        "padding": "16px",
                        "border": "1px solid #dee2e6",
                        "borderRadius": "8px",
                        "backgroundColor": "#f4f6f9",
                    },
                ),
                width=12,
            )
        ),
        # Input row
        dbc.Row(
            [
                dbc.Col(
                    dbc.Textarea(
                        id="user-input",
                        placeholder="Type your message… (Shift+Enter for new line, Enter to send)",
                        style={
                            "width": "100%",
                            "height": "72px",
                            "resize": "none",
                            "borderRadius": "8px",
                            "border": "1px solid #ced4da",
                            "padding": "10px 14px",
                            "fontSize": "0.93rem",
                        },
                    ),
                    width=10,
                ),
                dbc.Col(
                    dbc.Button(
                        "Send",
                        id="send-btn",
                        color="primary",
                        n_clicks=0,
                        className="w-100",
                        style={"height": "72px", "borderRadius": "8px", "fontSize": "1rem"},
                    ),
                    width=2,
                ),
            ],
            className="mt-2 g-2",
        ),
        # Loading indicator
        dbc.Row(
            dbc.Col(
                dbc.Spinner(
                    html.Div(id="loading-output"),
                    color="primary",
                    size="sm",
                ),
                width=12,
                className="text-center mt-1",
            )
        ),
        # Hidden stores
        dcc.Store(id="session-id", storage_type="memory"),
        dcc.Store(id="chat-histories", data={}, storage_type="memory"),
        dcc.Store(id="profile-store", storage_type="memory"),
        dcc.Interval(id="init-interval", interval=200, max_intervals=1),
    ],
    fluid=True,
    style={"maxWidth": "800px", "padding": "0 16px"},
)

# ---------------------------------------------------------------------------
# Clientside callback: attach Enter-to-send listener on page load
# ---------------------------------------------------------------------------
clientside_callback(
    """
    function(_) {
        setTimeout(function() {
            const textarea = document.getElementById('user-input');
            const btn = document.getElementById('send-btn');
            if (textarea && btn && !textarea._keyListenerAdded) {
                textarea._keyListenerAdded = true;
                textarea.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        btn.click();
                    }
                });
            }
        }, 500);
        return window.dash_clientside.no_update;
    }
    """,
    Output("user-input", "placeholder"),
    Input("init-interval", "n_intervals"),
    prevent_initial_call=False,
)

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@app.callback(
    Output("session-id", "data"),
    Output("profile-store", "data"),
    Input("init-interval", "n_intervals"),
)
def init_app(_n):
    """Generate a session ID and load the user profile from SQLite on page load."""
    session_id = str(uuid.uuid4())
    profile = database.get_profile()
    return session_id, profile


@app.callback(
    Output("chat-histories", "data"),
    Output("user-input", "value"),
    Output("profile-store", "data", allow_duplicate=True),
    Output("loading-output", "children"),
    Input("send-btn", "n_clicks"),
    State("user-input", "value"),
    State("active-tab", "active_tab"),
    State("chat-histories", "data"),
    State("session-id", "data"),
    State("profile-store", "data"),
    prevent_initial_call=True,
)
def send_message(n_clicks, message, active_tab, histories, session_id, profile):
    """Handle a user message: route to the correct agent, update chat history."""
    if not message or not message.strip():
        return histories, "", profile, ""

    message = message.strip()
    histories = histories or {}
    tab_history = histories.get(active_tab, [])

    # Guard: require profile for non-onboarding tabs
    if active_tab != "profile" and (not profile or not profile.get("onboarding_complete")):
        tab_history.append({"role": "user", "text": message})
        tab_history.append({
            "role": "assistant",
            "text": "Please complete your profile in the **Profile** tab first so I can give you personalised advice.",
        })
        histories[active_tab] = tab_history
        return histories, "", profile, ""

    # Build profile string for agent context
    profile_str = format_profile(profile) if profile else ""

    # Build per-tab session ID so each tab has independent conversation history
    tab_session_id = f"{session_id}_{active_tab}"

    # Route to agent
    agent = AGENTS[active_tab]
    try:
        response = agent.chat(message, tab_session_id, profile_str)
    except Exception as exc:
        response = f"Something went wrong: {exc}"

    # Append to history
    tab_history.append({"role": "user", "text": message})
    tab_history.append({"role": "assistant", "text": response})
    histories[active_tab] = tab_history

    # After onboarding, reload profile in case it was just saved
    updated_profile = database.get_profile() if active_tab == "profile" else profile

    return histories, "", updated_profile, ""


@app.callback(
    Output("chat-display", "children"),
    Input("chat-histories", "data"),
    Input("active-tab", "active_tab"),
)
def render_chat(histories, active_tab):
    """Re-render the chat area whenever the active tab or history changes."""
    messages = (histories or {}).get(active_tab, [])
    return _render_messages(messages)


# ---------------------------------------------------------------------------
# Auto-scroll chat to bottom on update
# ---------------------------------------------------------------------------
clientside_callback(
    """
    function(children) {
        const el = document.getElementById('chat-display');
        if (el) el.scrollTop = el.scrollHeight;
        return window.dash_clientside.no_update;
    }
    """,
    Output("chat-display", "data-scroll"),
    Input("chat-display", "children"),
    prevent_initial_call=True,
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8050)
