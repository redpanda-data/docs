# Property documentation update guide for LLMs

This guide explains how to update Redpanda property documentation when all property reference pages are auto-generated.

Critical rule: Never directly edit files in `/modules/reference/partials/properties/` - they are auto-generated and will be overwritten.

---

## Table of contents

1. [Overview](#overview)
2. [The override system](#the-override-system)
3. [File structure](#file-structure)
4. [What can be overridden](#what-can-be-overridden)
5. [How to update overrides](#how-to-update-overrides)
6. [Regenerating documentation](#regenerating-documentation)
7. [Common scenarios](#common-scenarios)
8. [Validation](#validation)
9. [Best practices](#best-practices)

---

## Overview

### The auto-generation system

All property documentation files are automatically generated from source code metadata.

Generated files (do not edit):
- `/modules/reference/partials/properties/broker-properties.adoc`
- `/modules/reference/partials/properties/cluster-properties.adoc`
- `/modules/reference/partials/properties/object-storage-properties.adoc`
- `/modules/reference/partials/properties/topic-properties.adoc`

Override file (edit this):
- `/docs-data/property-overrides.json`

### Why this matters

When a user asks you to:
- "Improve the description of cleanup.policy"
- "Add an example for kafka_qdc_enable"
- "Fix the documentation for compression.type"
- "Add related topics to retention.ms"

You must:
1. Update `/docs-data/property-overrides.json`
2. Run the doc-tools CLI to regenerate
3. Do not edit the generated `.adoc` files directly

---

## The override system

### How it works

```
Source Code Metadata
        |
        v
  doc-tools CLI
        |
        v
   Merges with
        |
        v
property-overrides.json <- You edit this file
        |
        v
  Generates AsciiDoc
        |
        v
/modules/reference/partials/properties/*.adoc
```

The override file provides human-curated content that supplements or replaces auto-generated content.

---

## File structure

### Location

```
docs-data/property-overrides.json
```

This file is located in the root of the docs repository.

### Basic structure

```json
{
  "properties": {
    "property_name": {
      "description": "Enhanced description text",
      "config_scope": "broker|cluster|topic",
      "category": "category-name",
      "example": [
        "Line 1 of example",
        "Line 2 of example"
      ],
      "related_topics": [
        "xref:path/to/doc.adoc[Link Text]",
        "xref:another/doc.adoc#anchor[Another Link]"
      ],
      "exclude_from_docs": false
    }
  }
}
```

### Real example

```json
{
  "properties": {
    "cleanup.policy": {
      "description": "The cleanup policy to apply for log segments of a topic.\nWhen `cleanup.policy` is set, it overrides the cluster property xref:cluster-properties.adoc#log_cleanup_policy[`log_cleanup_policy`] for the topic.\n\nValues:\n- `delete` - Deletes data according to size-based or time-based retention limits, or both.\n- `compact` - Deletes data according to a key-based retention policy, discarding all but the latest value for each key.\n- `compact,delete` - The latest values are kept for each key, while the remaining data is deleted according to retention limits.",
      "config_scope": "topic",
      "related_topics": [
        "xref:cluster-properties.adoc#log_cleanup_policy[`log_cleanup_policy`]",
        "xref:manage:cluster-maintenance/disk-utilization.adoc#configure-segment-size[Configure segment size]",
        "xref:manage:tiered-storage.adoc#compacted-topics-in-tiered-storage[Compacted topics in Tiered Storage]"
      ]
    }
  }
}
```

---

## What can be overridden

### Fields you can override

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | Enhance or replace property description | Add value explanations, usage notes |
| `config_scope` | Specify broker/cluster/topic scope | `"broker"`, `"cluster"`, `"topic"` |
| `category` | Categorize property | `"category-retention-compaction"` |
| `example` | Add YAML configuration examples | Multi-line code blocks |
| `related_topics` | Add cross-references | AsciiDoc xref links |
| `exclude_from_docs` | Hide internal/deprecated properties | `true` or `false` |
| `type` | Override detected type | `"integer"`, `"string"`, `"boolean"` |
| `default` | Override default value | Any valid value |
| `accepted_values` | Override accepted values | Array of valid values |

### What gets auto-generated

These are pulled from source code and usually don't need overriding:
- Property name
- Type (usually)
- Default value (usually)
- Nullable status
- Requires restart
- Visibility
- Ranges/bounds

Only override these if the auto-generated values are incorrect.

---

## How to update overrides

### Step 1: Read the current override file

```python
# Always read the file first to preserve existing overrides
import json

with open('docs-data/property-overrides.json', 'r') as f:
    overrides = json.load(f)
```

### Step 2: Add or update property overrides

```python
# Add a new property override
overrides['properties']['property_name'] = {
    "description": "Your enhanced description here",
    "config_scope": "cluster",
    "example": [
        "redpanda:",
        "  property_name: value"
    ],
    "related_topics": [
        "xref:path/to/related.adoc[Related Topic]"
    ]
}

# Or update existing property
if 'existing_property' in overrides['properties']:
    overrides['properties']['existing_property']['description'] = "Updated description"
    # Add example if it doesn't exist
    if 'example' not in overrides['properties']['existing_property']:
        overrides['properties']['existing_property']['example'] = [
            "example line 1",
            "example line 2"
        ]
```

### Step 3: Write back to file

```python
with open('docs-data/property-overrides.json', 'w') as f:
    json.dump(overrides, f, indent=2)
```

### Step 4: Verify JSON is valid

After writing, always verify the JSON is valid:
```bash
python -c "import json; json.load(open('docs-data/property-overrides.json'))"
```

---

## Regenerating documentation

### Prerequisites

Before running doc-tools, you must have:

1. A valid GitHub token with repo access to cloudv2 in the redpandadata organization
2. The token set as the GITHUB_TOKEN environment variable

```bash
export GITHUB_TOKEN="your_github_token_here"
```

### The doc-tools CLI

After updating overrides, regenerate documentation:

```bash
# Run from the docs repository root
npx doc-tools generate property-docs \
  --tag "<redpanda-version>" \
  --generate-partials \
  --cloud-support \
  --overrides docs-data/property-overrides.json
```

Important notes:
- Always use `npx doc-tools` (not just `doc-tools`)
- The `--tag` flag specifies which Redpanda version to generate docs for
- The `--generate-partials` flag generates files in the partials directory
- The `--cloud-support` flag must ALWAYS be included - never exclude it
- The `--overrides` flag points to the property overrides JSON file

Example with a specific version:

```bash
npx doc-tools generate property-docs \
  --tag "v25.3.1" \
  --generate-partials \
  --cloud-support \
  --overrides docs-data/property-overrides.json
```

### Expected output

The CLI will:
1. Authenticate with GitHub using GITHUB_TOKEN
2. Fetch source code metadata from the specified Redpanda version
3. Merge with property-overrides.json
4. Generate updated .adoc files in `/modules/reference/partials/properties/`
5. Show summary of changes

### Verification

After regeneration, check the generated files:

```bash
# Check if your changes appear
grep -A 5 "property_name" modules/reference/partials/properties/topic-properties.adoc
```

---

## Common scenarios

### Scenario 1: Improve a property description

User request: "The description for `cleanup.policy` should explain what each value does"

Action:
1. Read the override file
2. Update the description field to include value explanations
3. Write back to override file
4. Inform user to run doc-tools CLI

```json
{
  "cleanup.policy": {
    "description": "The cleanup policy to apply for log segments of a topic.\n\nValues:\n- `delete` - Deletes data according to size-based or time-based retention limits.\n- `compact` - Deletes data according to a key-based retention policy.\n- `compact,delete` - The latest values are kept for each key, while the remaining data is deleted according to retention limits.",
    "config_scope": "topic"
  }
}
```

### Scenario 2: Add an example

User request: "Add a YAML example for `auto_create_topics_enabled`"

Action:
```json
{
  "auto_create_topics_enabled": {
    "example": [
      "redpanda:",
      "  auto_create_topics_enabled: false"
    ],
    "config_scope": "cluster"
  }
}
```

Note: Example is an array of strings, where each string is one line. The doc-tools CLI will format it as a YAML code block.

### Scenario 3: Add related topics

User request: "Link to the compaction guide from `delete.retention.ms`"

Action:
```json
{
  "delete.retention.ms": {
    "related_topics": [
      "xref:./cluster-properties.adoc#tombstone_retention_ms[`tombstone_retention_ms`]",
      "xref:manage:cluster-maintenance/compaction-settings.adoc#tombstone-record-removal[Tombstone record removal]"
    ],
    "config_scope": "topic"
  }
}
```

Format: Use AsciiDoc xref syntax: `xref:path/to/file.adoc[Link Text]` or `xref:path/to/file.adoc#anchor[Link Text]`

### Scenario 4: Fix incorrect metadata

User request: "The default value for `cleanup.policy` is wrong, it shows 'deletion' but should be 'delete'"

Action:
```json
{
  "cleanup.policy": {
    "default": "delete",
    "config_scope": "topic"
  }
}
```

Note: This overrides the auto-detected default value.

### Scenario 5: Hide internal properties

User request: "Don't document `redpanda.cloud_topic.enabled`, it's internal only"

Action:
```json
{
  "redpanda.cloud_topic.enabled": {
    "exclude_from_docs": true,
    "config_scope": "topic"
  }
}
```

Note: The property will still be generated but can be filtered out by the build system.

### Scenario 6: Bulk updates

User request: "Add related topics to all Tiered Storage properties"

Action:
```python
import json

with open('docs-data/property-overrides.json', 'r') as f:
    overrides = json.load(f)

# List of Tiered Storage properties
ts_properties = ['cloud_storage_cache_size', 'cloud_storage_enable', 'retention.local.target.ms']

common_xref = "xref:manage:tiered-storage.adoc[Tiered Storage]"

for prop in ts_properties:
    if prop not in overrides['properties']:
        overrides['properties'][prop] = {}

    if 'related_topics' not in overrides['properties'][prop]:
        overrides['properties'][prop]['related_topics'] = []

    if common_xref not in overrides['properties'][prop]['related_topics']:
        overrides['properties'][prop]['related_topics'].append(common_xref)

with open('docs-data/property-overrides.json', 'w') as f:
    json.dump(overrides, f, indent=2)
```

---

## Validation

### After updating overrides

Always validate your changes:

#### 1. JSON syntax validation

```bash
python -c "import json; json.load(open('docs-data/property-overrides.json'))" && echo "JSON is valid"
```

#### 2. Check for common mistakes

```python
import json

with open('docs-data/property-overrides.json', 'r') as f:
    overrides = json.load(f)

errors = []

for prop_name, prop_data in overrides['properties'].items():
    # Check example is array
    if 'example' in prop_data and not isinstance(prop_data['example'], list):
        errors.append(f"{prop_name}: 'example' must be an array")

    # Check related_topics is array
    if 'related_topics' in prop_data and not isinstance(prop_data['related_topics'], list):
        errors.append(f"{prop_name}: 'related_topics' must be an array")

    # Check xref format in related_topics
    if 'related_topics' in prop_data:
        for xref in prop_data['related_topics']:
            if not xref.startswith('xref:'):
                errors.append(f"{prop_name}: related_topics should use xref format: {xref}")

if errors:
    print("Validation errors found:")
    for error in errors:
        print(f"  - {error}")
else:
    print("All validations passed")
```

#### 3. Verify after regeneration

After running doc-tools CLI:

```bash
# Check for "No description available" errors
grep "No description available" modules/reference/partials/properties/*.adoc

# Check if your property appears
grep -A 10 "=== your_property_name" modules/reference/partials/properties/cluster-properties.adoc
```

---

## Property description rules

When updating property descriptions in the override file, you must follow these rules:

### Never add cloud-specific conditional blocks

Do not include cloud-specific descriptions. These belong in metadata, not description text.

Never include cloud-specific notes about BYOC, Dedicated, or read-only status

Wrong:
```
ifdef::env-cloud[]
This property is read-only in Redpanda Cloud.
endif::[]
```

Right:
```
Controls the maximum segment size for topics.
```

Reason: Cloud-specific information is displayed in the metadata table, not in the description.

### Never add enterprise license includes

Do not include enterprise license markers in descriptions. These belong in metadata, not description text.

Never include:
- `include::reference:partial$enterprise-licensed-property.adoc[]`
- Enterprise license requirement notes

Wrong:
```
Enable shadow linking for disaster recovery.

include::reference:partial$enterprise-licensed-property.adoc[]
```

Right:
```
Enable shadow linking for disaster recovery.
```

Reason: Enterprise licensing information is displayed in the metadata table, not in the description.

### Never add descriptions for deprecated properties

Do not add or update descriptions for properties marked as deprecated in the existing documentation.

Process:
1. Check if the property is deprecated by searching for "deprecated" in the property section
2. If deprecated, remove any existing override for that property
3. Never add new overrides for deprecated properties

Example deprecated properties:
- `log_message_timestamp_alert_after_ms` (use `log_message_timestamp_after_max_ms` instead)
- `log_message_timestamp_alert_before_ms` (use `log_message_timestamp_before_max_ms` instead)
- `raft_recovery_default_read_size`
- `kafka_memory_batch_size_estimate_for_fetch`

Reason: Deprecated properties are being phased out and don't need enhanced documentation.

### Keep descriptions focused

Descriptions should explain:
- What the property does
- When to use it
- How it relates to other properties
- Important behavioral details

Descriptions should not include:
- Version availability (metadata)
- Cloud availability (metadata)
- Enterprise license requirements (metadata)
- Requires restart (metadata)
- Default values (metadata)
- Type information (metadata)

These metadata items are displayed in the metadata table, not in the description text.

### Use consistent formatting

Use AsciiDoc formatting in descriptions:
- `` `property_name` `` for property names
- `xref:path/to/doc.adoc[Link Text]` for cross-references
- `<<anchor,text>>` for internal document references
- `\n\n` for paragraph breaks

Example:
```json
{
  "description": "The maximum segment size for topics. When `segment.bytes` is set, it overrides the cluster property xref:./cluster-properties.adoc#log_segment_size[`log_segment_size`].\n\nLarger segments improve throughput but increase latency for tiered storage operations."
}
```

### Prefix self-managed-only links

Some documentation pages only exist in self-managed deployments, not in cloud-docs. When adding related_topics links, prefix these with `self-managed-only:` so the build system can handle them appropriately.

Common self-managed-only pages:
- Kubernetes-specific pages: `manage:kubernetes/`
- Some cluster maintenance pages: `manage:cluster-maintenance/configure-client-connections.adoc`
- Some topic properties that don't exist in cloud: `reference:properties/topic-properties.adoc#segmentms`

Example:
```json
{
  "kafka_connections_max": {
    "related_topics": [
      "self-managed-only:xref:manage:cluster-maintenance/configure-client-connections.adoc#limit-client-connections[Limit client connections]"
    ]
  }
}
```

When you see build errors like:
```
ERROR (asciidoctor): target of xref not found: manage:kubernetes/security/authentication/k-authentication.adoc
```

Fix by adding the `self-managed-only:` prefix:
```json
{
  "related_topics": [
    "self-managed-only:xref:manage:kubernetes/security/authentication/k-authentication.adoc[Link Text]"
  ]
}
```

Use the `fix-cloud-links.py` script to automatically identify and prefix these links:
```bash
python3 fix-cloud-links.py
```

### Remove duplicate links

Always remove duplicates from related_topics lists to keep them clean:

```bash
python3 remove-duplicate-links.py
```

---

## Best practices

### Preserve existing overrides

Always read the file first:
```python
with open('property-overrides.json', 'r') as f:
    overrides = json.load(f)
# Make changes
# Write back
```

Don't create new dict from scratch:
```python
overrides = {"properties": {}}  # This wipes existing overrides!
```

### Use meaningful descriptions

Explain the purpose and impact:

```json
{
  "description": "Maximum segment size for non-compacted topics. Larger segments improve throughput but increase latency for retention and tiered storage operations."
}
```

Don't just restate the property name:
```json
{
  "description": "The segment size."
}
```

### Format multi-line descriptions

Use `\n\n` for paragraph breaks:
```json
{
  "description": "First paragraph about what it does.\n\nSecond paragraph about when to use it.\n\nWarning: Important note about limitations."
}
```

### Use AsciiDoc formatting in descriptions

You can use AsciiDoc markup in description fields:
- `` `code` `` for inline code
- Double asterisks for bold text
- `xref:path.adoc[link]` for cross-references
- `<<anchor,link>>` for internal links

Example:
```json
{
  "description": "Controls cleanup behavior. Set to `delete` for time/size-based retention or `compact` for key-based deduplication.\n\nSee the xref:manage:tiered-storage.adoc[Tiered Storage] guide for more details."
}
```

### Keep examples realistic

Show real configuration:
```json
{
  "example": [
    "redpanda:",
    "  kafka_qdc_enable: true",
    "  kafka_qdc_depth_alpha: 0.8",
    "  kafka_qdc_idle_depth: 10"
  ]
}
```

### Use specific link text

Descriptive link text:
```json
{
  "related_topics": [
    "xref:manage:tiered-storage.adoc#configure-cache[Configure Tiered Storage cache]"
  ]
}
```

Generic link text:
```json
{
  "related_topics": [
    "xref:manage:tiered-storage.adoc[click here]"
  ]
}
```

### Add value explanations for enums

For enum-type properties, explain what each value means:

```json
{
  "cleanup.policy": {
    "description": "The cleanup policy to apply for log segments.\n\nValues:\n- `delete` - Deletes data according to retention limits\n- `compact` - Keeps latest value per key\n- `compact,delete` - Compaction + time-based deletion"
  }
}
```

### Mark internal properties for exclusion

If a property shouldn't be documented:

```json
{
  "internal_property": {
    "exclude_from_docs": true,
    "config_scope": "cluster"
  }
}
```

### Test your changes

After regeneration:
1. Visually inspect the generated .adoc file
2. Build the docs locally if possible
3. Check that examples render correctly
4. Verify links work

### Document your changes

When you update overrides, tell the user:
```
I've updated property-overrides.json with:
- Enhanced description for cleanup.policy with value explanations
- Added 3 related topic links
- Added YAML example

Next steps:
1. Set GITHUB_TOKEN if not already set: export GITHUB_TOKEN="your_token"
2. Run: npx doc-tools generate property-docs --tag "<version>" --generate-partials --cloud-support --overrides docs-data/property-overrides.json
3. Verify the changes in the generated files
4. Build docs to confirm rendering
```

---

## Troubleshooting

### Changes not appearing

Cause: doc-tools CLI not run or override format incorrect

Solution:
1. Verify JSON is valid
2. Check property name matches exactly (case-sensitive)
3. Ensure doc-tools CLI was run after updating overrides
4. Check CLI output for errors

### JSON syntax error

Cause: Invalid JSON after editing

Solution:
```bash
# Validate JSON
python -c "import json; json.load(open('property-overrides.json'))"

# Use a JSON formatter
python -m json.tool property-overrides.json
```

### Links broken

Cause: Incorrect xref path or syntax

Solution:
- Use relative paths from the properties file location
- Include `.adoc` extension
- Use correct AsciiDoc xref syntax

Correct:
```json
"xref:manage:tiered-storage.adoc[Tiered Storage]"
"xref:./cluster-properties.adoc#property_name[Property Name]"
```

Incorrect:
```json
"xref:manage/tiered-storage[Tiered Storage]"  // Missing .adoc
"[Tiered Storage](manage:tiered-storage.adoc)"  // Markdown syntax
```

---

## Quick reference

### Minimal override
```json
{
  "property_name": {
    "config_scope": "cluster"
  }
}
```

### Common override
```json
{
  "property_name": {
    "description": "Enhanced description text",
    "config_scope": "cluster",
    "related_topics": [
      "xref:path/to/doc.adoc[Link Text]"
    ]
  }
}
```

### Complete override
```json
{
  "property_name": {
    "description": "Enhanced description with multiple paragraphs.\n\nSecond paragraph with details.",
    "config_scope": "cluster",
    "category": "category-performance",
    "example": [
      "redpanda:",
      "  property_name: value"
    ],
    "related_topics": [
      "xref:guide.adoc[Related Guide]",
      "xref:./other-properties.adoc#related_prop[Related Property]"
    ],
    "type": "integer",
    "default": "100",
    "exclude_from_docs": false
  }
}
```

### Regeneration command
```bash
# Run from the docs repository root
npx doc-tools generate property-docs \
  --tag "<redpanda-version>" \
  --generate-partials \
  --cloud-support \
  --overrides docs-data/property-overrides.json
```

---

## Summary for LLMs

When asked to update property documentation:

1. Update `/docs-data/property-overrides.json`
2. Run the doc-tools CLI with the correct command:
   ```bash
   npx doc-tools generate property-docs \
     --tag "<redpanda-version>" \
     --generate-partials \
     --cloud-support \
     --overrides docs-data/property-overrides.json
   ```
3. Never edit `/modules/reference/partials/properties/*.adoc` directly

Critical requirements:
- Must have GITHUB_TOKEN environment variable set with repo access to cloudv2 in redpandadata
- Must ALWAYS include `--cloud-support` flag - never exclude it
- Must use `npx doc-tools` (not just `doc-tools`)
- Must include all flags: `--tag`, `--generate-partials`, `--cloud-support`, `--overrides`

Property description rules (mandatory):
- Never add enterprise license includes (`include::reference:partial$enterprise-licensed-property.adoc[]`)
- Never add descriptions for deprecated properties
- When comparing descriptions, check every single property across all files
- Keep descriptions focused on behavior, not metadata
- Use AsciiDoc formatting for cross-references and inline code

Remember:
- Always read the override file first
- Validate JSON after changes
- Use Python scripts for complex updates
- Tell the user to run doc-tools CLI with the complete command
- Verify changes in generated files
- Clean up inappropriate content from descriptions
- Remove any deprecated property overrides

---
