# BitSwan Secrets Management

## Overview

BitSwan uses environment files to manage secrets and sensitive configuration values. These secrets are made available as environment variables within automations and Jupyter notebooks.

## Setup

1. You will see a `secrets` directory in your VSCode Server workspace.
2. Create environment files in the secrets directory.
3. Configure secret groups in `automation.toml`.

## Usage Example

### 1. Create Environment File

Create a file in the secrets directory (e.g., `foo`):
```txt
FOO=foo
```

### 2. Configure Secret Groups

In `automation.toml`, add stage-specific secret groups:

```toml
[secrets]
dev = ["foo"]
staging = ["foo"]
production = ["foo"]
```

You can give your automations access to multiple secret groups per stage:

```toml
[secrets]
dev = ["foo", "bar"]
staging = ["foo-staging", "bar-staging"]
production = ["foo-prod", "bar-prod"]
```

The **dev** secrets are also used in the **live-dev** stage, so you only need to configure `dev`:

```toml
[secrets]
dev = ["foo", "bar"]           # also used by live-dev
staging = ["foo-staging"]
production = ["foo-prod"]
```

### 3. Accessing Secrets

- In automations: Environment variables (e.g., `$FOO`) will be automatically available.
- In Jupyter notebooks: Environment variables are set automatically after importing the `bspump` library. Secrets are loaded as if the automation is running in the **dev** stage.

## Notes

- Each env file in the secrets dir represents a secrets group
- Secret values are loaded as environment variables
- Jupyter integration happens automatically with bspump import
- The automation container receives a `BITSWAN_AUTOMATION_STAGE` environment variable indicating its current stage
