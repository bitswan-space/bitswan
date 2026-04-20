[![Docs](https://img.shields.io/badge/docs-latest-brightgreen)](https://docs.bitswan.space)

# BitSwan

This repository contains two things:

1. **bspump** - The core stream processing library used by [BitSwan4Stream](https://bitswan.space)
2. **Example automations** - Sample pipelines that can run in the [BitSwan Automation Server](https://github.com/bitswan-space/bitswan-automation-server)

## Deployment Options

BitSwan4Stream pipelines can be deployed to:

- **BitSwan Automation Server** - Managed deployment with monitoring and scheduling
- **Apache Flink** - Distributed stream processing on Flink clusters

## Installation

```bash
git clone git@github.com:bitswan-space/BitSwan.git
cd BitSwan
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

For Flink support:
```bash
uv pip install -e ".[flink]"
```

## Running Pipelines

### Local Development

Run a pipeline locally:

```bash
bitswan-notebook examples/WebForms/main.ipynb
```

With auto-reload on code changes:

```bash
bitswan-notebook examples/WebForms/main.ipynb --watch
```

### Deploy to Apache Flink

Run on a local Flink mini-cluster:

```bash
bitswan-flink examples/Kafka2Kafka/main.ipynb
```

Submit to a Flink cluster:

```bash
bitswan-flink --flink-cluster jobmanager:8081 examples/Kafka2Kafka/main.ipynb
```

## Example Automations

Example pipelines are in the [examples](./examples/) directory:

- **Kafka2Kafka** - Stream processing between Kafka topics
- **WebForms** - HTTP form handling
- **WebHooks** - Webhook integrations
- **TimeTrigger** - Scheduled automations

## Testing

Test examples are in the [examples/Testing](./examples/Testing) directory.

Run tests with the `--test` flag:

```bash
bitswan-notebook examples/Testing/InspectError/main.ipynb --test

Running tests for pipeline Kafka2KafkaPipeline.

    ┌ Testing event:        b'foo'
    └ Outputs:              [b'FOO'] ✔

All tests passed for Kafka2KafkaPipeline.
```

Combine `--test` with `--watch` to auto-rerun tests on changes.

## License

The bspump library is open-source software, available under the BSD 3-Clause License.

