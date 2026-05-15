# Secrets Management

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

## Using Secrets in Configuration

Reference secrets in `pipelines.conf` using environment variable syntax:

```ini
[connection:PostgreSQLConnection]
password=${POSTGRES_PASSWORD}

[connection:KafkaConnection]
sasl_plain_password=${KAFKA_PASSWORD}
```

## Notes

- Each env file in the secrets dir represents a secrets group
- Secret values are loaded as environment variables
- Jupyter integration happens automatically with bspump import
- The automation container receives a `BITSWAN_AUTOMATION_STAGE` environment variable indicating its current stage

## Security Best Practices

1. **Never commit secrets**: Add secrets directory to `.gitignore`
2. **Use separate secrets per stage**: Production secrets should differ from dev
3. **Rotate secrets regularly**: Update passwords periodically
4. **Limit access**: Only grant access to necessary secret groups
5. **Audit usage**: Monitor which automations access which secrets
