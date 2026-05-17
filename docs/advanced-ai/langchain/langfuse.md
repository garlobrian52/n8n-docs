---
contentType: howto
title: Use Langfuse with n8n
description: How to enable Langfuse for your self-hosted n8n instance.
---

# Use Langfuse with n8n

[Langfuse](https://langfuse.com/) is an open-source LLM engineering platform. You can connect your n8n instance to Langfuse to record, monitor, and analyze runs in n8n, just as you can in a LangChain application.

/// info | Feature availability
Self-hosted n8n only.
///

## Connect your n8n instance to Langfuse

1. [Log in to Langfuse](https://cloud.langfuse.com/) and get your public and secret API keys from the project settings.

1. Set the Langfuse environment variables:

   | Variable                        | Value |
   | ------------------------------- | ----- |
   | `LANGFUSE_PUBLIC_KEY`           | Set this to your Langfuse public key |
   | `LANGFUSE_SECRET_KEY`           | Set this to your Langfuse secret key |
   | `LANGFUSE_BASEURL`              | Optional. Set to your Langfuse host URL if self-hosting Langfuse (defaults to `"https://cloud.langfuse.com"`) |

   /// note
   If you just created your Langfuse account, you will see a project named **"default"** only after the first trace is sent from n8n.
   ///

   Set the variables so that they're available globally in the environment where you host your n8n instance. You can do this in the same way as the rest of your general configuration.

1. Restart n8n.

## Langfuse custom dashboards

Langfuse provides [custom dashboards](https://langfuse.com/docs/analytics/custom-dashboards) where you can create widgets to visualize your LLM data. To create a new widget:

1. Navigate to your Langfuse project dashboard.
2. Select the **Widgets** tab.
3. Click **New Widget**.
4. Configure your widget:
   - **Data Source**: Choose from traces, observations, or evaluation scores
   - **Metrics**: Select what to measure (count, latency, cost, scores, etc.)
   - **Dimensions**: Group by user, model, time, trace name, etc.
   - **Filters**: Narrow down to specific data subsets
   - **Chart Type**: Pick the best visualization for your data
5. Click **Save** to store your widget.

For information on using Langfuse, refer to [Langfuse's documentation](https://langfuse.com/docs).
