---
title: Zoom credentials
description: Documentation for Zoom credentials. Use these credentials to authenticate Zoom in n8n, a workflow automation platform.
contentType: [integration, reference]
---

# Zoom credentials

You can use these credentials to authenticate the following nodes:

- [Zoom](/integrations/builtin/app-nodes/n8n-nodes-base.zoom.md)

## Prerequisites

Create a [Zoom](https://zoom.us/) account. Your account must have one of the following permissions:

- Account owner
- Account admin
- Zoom for developers role

## Supported authentication methods

- API JWT token
- OAuth2

/// warning | API JWT token fully deprecated
Zoom removed support for JWT access tokens in June 2023. This authentication method is no longer supported. You must use OAuth2 for all credentials. If you have existing JWT credentials, migrate them to OAuth2 as soon as possible.
///

## Related resources

Refer to [Zoom's API documentation](https://developers.zoom.us/docs/api/) for more information about the service.

## Using API JWT token

/// danger | No longer supported
This authentication method has been fully deprecated by Zoom since June 2023 and is no longer supported. Don't create new credentials with this method. Migrate any existing JWT credentials to OAuth2.
///

To configure this credential, you'll need:

- A **JWT token**: To create a JWT token, create a new JWT app in the [Zoom App Marketplace](https://marketplace.zoom.us/).

## Using OAuth2

To configure this credential, you'll need:

- A **Client ID**: Generated when you create an OAuth app on the Zoom App Marketplace.
- A **Client Secret**: Generated when you create an OAuth app.

To generate your **Client ID** and **Client Secret**, [create an OAuth app](https://developers.zoom.us/docs/integrations/create/).

Use these settings for your OAuth app:

- Select **User-managed app** for **Select how the app is managed**.
- Copy the **OAuth Callback URL** from n8n and enter it as an **OAuth Redirect URL** in Zoom.
- If your n8n credential displays a **Whitelist URL**, also enter that URL as a an **OAuth Redirect URL**.
- Enter **Scopes** for the scopes you plan to use. For all functionality in the [Zoom](/integrations/builtin/app-nodes/n8n-nodes-base.zoom.md) node, select:
    - `meeting:read`
    - `meeting:write`
    - Refer to [OAuth scopes | Meeting scopes](https://developers.zoom.us/docs/integrations/oauth-scopes/#meeting-scopes) for more information on meeting scopes.
- Copy the **Client ID** and **Client Secret** provided in the Zoom app and enter them in your n8n credential.
