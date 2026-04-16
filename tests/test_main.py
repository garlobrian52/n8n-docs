"""
Tests for main.py: templatesWidget and workflowDemo macros,
and the custom_slugify helper (tested indirectly via workflowDemo).
"""
import json
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as main_module


class MockEnv:
    """Minimal stand-in for the mkdocs-macros Environment object."""

    def __init__(self):
        self._macros = {}

    def macro(self, func):
        self._macros[func.__name__] = func
        return func


def make_env(no_template=False):
    """Instantiate a MockEnv and call define_env() with the desired NO_TEMPLATE setting."""
    env = MockEnv()
    # Use an empty string for the falsy case so the key is always present and
    # patch.dict behaves predictably regardless of the host environment.
    env_override = {"NO_TEMPLATE": "1" if no_template else ""}
    with patch.dict(os.environ, env_override):
        main_module.define_env(env)
    return env


# ---------------------------------------------------------------------------
# templatesWidget – NO_TEMPLATE mode
# ---------------------------------------------------------------------------

class TestTemplatesWidgetNoTemplate:
    def test_returns_placeholder_div(self):
        env = make_env(no_template=True)
        result = env._macros["templatesWidget"]("Test Node", "test-node")
        assert "n8n-templates-widget" in result
        assert "Template widget placeholder" in result

    def test_placeholder_does_not_make_network_request(self):
        env = make_env(no_template=True)
        with patch("requests.get") as mock_get:
            env._macros["templatesWidget"]("Test Node", "test-node")
        mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# templatesWidget – live API path (requests mocked)
# ---------------------------------------------------------------------------

def _make_workflows(count=3):
    return [
        {"name": f"Workflow {i}", "id": i, "user": {"name": f"User {i}"}}
        for i in range(count)
    ]


def _mock_response(workflows):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"workflows": workflows}
    return resp


class TestTemplatesWidgetWithAPI:
    def test_returns_full_widget_with_three_workflows(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response(_make_workflows(3))):
            result = env._macros["templatesWidget"]("GitHub", "github")

        assert "n8n-templates-widget" in result
        assert "Workflow 0" in result
        assert "User 0" in result
        assert "n8n-templates-widget-more" in result
        assert "Browse GitHub integration templates" in result

    def test_returns_fallback_when_fewer_than_three_workflows(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response(_make_workflows(2))):
            result = env._macros["templatesWidget"]("GitHub", "github")

        assert "Browse GitHub integration templates" in result
        assert "n8n-templates-widget-more" in result
        # Should not render individual workflow cards
        assert "n8n-templates-widget-template" not in result

    def test_returns_fallback_when_zero_workflows(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response([])):
            result = env._macros["templatesWidget"]("GitHub", "github")

        assert "Browse GitHub integration templates" in result

    def test_returns_fallback_on_request_exception(self):
        import requests as req_lib

        env = make_env()
        with patch("requests.get", side_effect=req_lib.RequestException("timeout")):
            result = env._macros["templatesWidget"]("GitHub", "github")

        assert "Browse GitHub integration templates" in result
        assert "n8n-templates-widget-more" in result

    def test_email_imap_title_maps_to_correct_search_param(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            env._macros["templatesWidget"]("Email Trigger (IMAP)", "email-trigger-imap")

        url = mock_get.call_args[0][0]
        assert "email+imap" in url

    def test_normal_title_replaces_spaces_with_plus(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            env._macros["templatesWidget"]("Google Sheets", "google-sheets")

        url = mock_get.call_args[0][0]
        assert "Google+Sheets" in url

    def test_toload_parameter_is_passed_to_api(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            env._macros["templatesWidget"]("GitHub", "github", toLoad=5)

        url = mock_get.call_args[0][0]
        assert "rows=5" in url

    def test_returns_fallback_when_workflow_missing_name_key(self):
        env = make_env()
        # Workflows have no 'name' key → get_workflow_details returns None
        bad_workflows = [{"id": i, "user": {"name": "User"}} for i in range(3)]
        with patch("requests.get", return_value=_mock_response(bad_workflows)):
            result = env._macros["templatesWidget"]("GitHub", "github")

        assert "Browse all GitHub integration templates" in result

    def test_uses_community_user_when_user_name_key_absent(self):
        env = make_env()
        workflows = [
            {"name": f"WF {i}", "id": i, "user": {}}  # 'name' missing from user dict
            for i in range(3)
        ]
        with patch("requests.get", return_value=_mock_response(workflows)):
            result = env._macros["templatesWidget"]("GitHub", "github")

        assert "n8n Community" in result

    def test_workflow_links_point_to_n8n_io(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response(_make_workflows(3))):
            result = env._macros["templatesWidget"]("GitHub", "github")

        assert "n8n.io/workflows/" in result

    def test_slug_is_included_in_integration_links(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response(_make_workflows(3))):
            result = env._macros["templatesWidget"]("GitHub", "my-custom-slug")

        assert "n8n.io/integrations/my-custom-slug/" in result

    def test_api_request_includes_page_and_sort_params(self):
        env = make_env()
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            env._macros["templatesWidget"]("GitHub", "github")

        url = mock_get.call_args[0][0]
        assert "page=1" in url
        assert "sort=views" in url


# ---------------------------------------------------------------------------
# workflowDemo – NO_TEMPLATE mode
# ---------------------------------------------------------------------------

class TestWorkflowDemoNoTemplate:
    def test_returns_placeholder_div(self):
        env = make_env(no_template=True)
        result = env._macros["workflowDemo"]("file:///test.json")
        assert "n8n-workflow-preview" in result
        assert "Workflow preview placeholder" in result

    def test_placeholder_does_not_read_files_or_make_requests(self):
        env = make_env(no_template=True)
        with patch("builtins.open") as mock_file, patch("requests.get") as mock_get:
            env._macros["workflowDemo"]("file:///test.json")
        mock_file.assert_not_called()
        mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# workflowDemo – file:// scheme
# ---------------------------------------------------------------------------

def _file_workflow():
    return {"nodes": [{"type": "n8n-nodes-base.start"}], "connections": {}}


class TestWorkflowDemoFileScheme:
    def test_returns_preview_div(self):
        env = make_env()
        data = _file_workflow()
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            result = env._macros["workflowDemo"]("file:///my-workflow.json")

        assert "n8n-workflow-preview" in result

    def test_shows_view_workflow_file_link(self):
        env = make_env()
        data = _file_workflow()
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            result = env._macros["workflowDemo"]("file:///my-workflow.json")

        assert "View workflow file" in result

    def test_template_url_points_to_workflows_path(self):
        env = make_env()
        data = _file_workflow()
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            result = env._macros["workflowDemo"]("file:///my-workflow.json")

        assert "/_workflows/my-workflow.json" in result

    def test_output_contains_encoded_workflow(self):
        env = make_env()
        data = _file_workflow()
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            result = env._macros["workflowDemo"]("file:///test.json")

        assert "workflow=" in result
        assert "n8n-demo" in result

    def test_embeds_nodes_from_local_file(self):
        env = make_env()
        data = {"nodes": [{"type": "special-node"}], "connections": {"a": "b"}}
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            result = env._macros["workflowDemo"]("file:///special.json")

        # The encoded JSON is URL-encoded, so check for the node type in the result.
        assert "special-node" in result


# ---------------------------------------------------------------------------
# workflowDemo – http(s):// scheme
# ---------------------------------------------------------------------------

def _http_workflow():
    return {
        "id": 42,
        "name": "My Test Workflow",
        "workflow": {
            "nodes": [{"type": "n8n-nodes-base.start"}],
            "connections": {},
        },
    }


def _http_mock(data):
    resp = MagicMock()
    resp.json.return_value = data
    return resp


class TestWorkflowDemoHttpScheme:
    def test_https_returns_preview_div(self):
        env = make_env()
        with patch("requests.get", return_value=_http_mock(_http_workflow())):
            result = env._macros["workflowDemo"]("https://example.com/wf.json")

        assert "n8n-workflow-preview" in result

    def test_shows_view_template_details_link(self):
        env = make_env()
        with patch("requests.get", return_value=_http_mock(_http_workflow())):
            result = env._macros["workflowDemo"]("https://example.com/wf.json")

        assert "View template details" in result

    def test_template_url_includes_workflow_id(self):
        env = make_env()
        with patch("requests.get", return_value=_http_mock(_http_workflow())):
            result = env._macros["workflowDemo"]("https://example.com/wf.json")

        assert "n8n.io/workflows/42" in result

    def test_workflow_name_is_slugified_in_url(self):
        """custom_slugify("My Test Workflow") should produce "my-test-workflow"."""
        env = make_env()
        with patch("requests.get", return_value=_http_mock(_http_workflow())):
            result = env._macros["workflowDemo"]("https://example.com/wf.json")

        assert "my-test-workflow" in result

    def test_http_scheme_also_supported(self):
        env = make_env()
        with patch("requests.get", return_value=_http_mock(_http_workflow())):
            result = env._macros["workflowDemo"]("http://example.com/wf.json")

        assert "n8n-workflow-preview" in result

    def test_workflow_json_contains_only_nodes_and_connections(self):
        """Only 'nodes' and 'connections' keys should be forwarded to the widget."""
        env = make_env()
        with patch("requests.get", return_value=_http_mock(_http_workflow())):
            result = env._macros["workflowDemo"]("https://example.com/wf.json")

        # The extra 'id' and 'name' keys from the API response must not appear
        # inside the encoded workflow JSON (they are only in the template URL).
        import urllib.parse

        # Extract workflow= param from HTML attribute
        start = result.index("workflow='") + len("workflow='")
        end = result.index("'", start)
        encoded = result[start:end]
        wf = json.loads(urllib.parse.unquote(encoded))
        assert set(wf.keys()) == {"nodes", "connections"}


# ---------------------------------------------------------------------------
# workflowDemo – invalid / missing scheme
# ---------------------------------------------------------------------------

class TestWorkflowDemoInvalidScheme:
    def test_unknown_scheme_raises_value_error(self):
        env = make_env()
        with pytest.raises(ValueError, match="Workflow JSON must include a URL scheme"):
            env._macros["workflowDemo"]("ftp://example.com/wf.json")

    def test_plain_string_raises_value_error(self):
        env = make_env()
        with pytest.raises(ValueError, match="Workflow JSON must include a URL scheme"):
            env._macros["workflowDemo"]("just-a-string")

    def test_empty_string_raises_value_error(self):
        env = make_env()
        with pytest.raises(ValueError, match="Workflow JSON must include a URL scheme"):
            env._macros["workflowDemo"]("")


# ---------------------------------------------------------------------------
# custom_slugify – tested via the https workflowDemo path
# ---------------------------------------------------------------------------

class TestCustomSlugify:
    """
    custom_slugify is a private closure inside define_env, so it is exercised
    indirectly by workflowDemo (https scheme) which calls it to build the URL.
    """

    def _slug_from_name(self, name):
        data = {
            "id": 1,
            "name": name,
            "workflow": {"nodes": [], "connections": {}},
        }
        env = make_env()
        with patch("requests.get", return_value=_http_mock(data)):
            result = env._macros["workflowDemo"]("https://example.com/wf.json")
        # The slug appears between the workflow id and the trailing slash
        # e.g. https://n8n.io/workflows/1-my-slug/
        start = result.index("n8n.io/workflows/1-") + len("n8n.io/workflows/1-")
        end = result.index("/", start)
        return result[start:end]

    def test_basic_ascii_lowercased(self):
        assert self._slug_from_name("Hello World") == "hello-world"

    def test_spaces_become_hyphens(self):
        assert self._slug_from_name("foo bar baz") == "foo-bar-baz"

    def test_ampersand_mapped_to_and(self):
        # CHAR_MAP maps '&' → 'and'
        slug = self._slug_from_name("Sales & Marketing")
        assert "and" in slug

    def test_non_ascii_characters_transliterated(self):
        # CHAR_MAP maps 'é' → 'e'
        slug = self._slug_from_name("Résumé")
        assert "e" in slug
        assert "é" not in slug

    def test_digits_preserved(self):
        assert self._slug_from_name("Workflow 42") == "workflow-42"

    def test_leading_trailing_spaces_stripped(self):
        slug = self._slug_from_name("  padded  ")
        assert not slug.startswith("-")
        assert not slug.endswith("-")
