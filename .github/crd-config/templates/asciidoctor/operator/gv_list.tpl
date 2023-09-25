{{- define "gvList" -}}
{{- $groupVersions := . -}}

// Generated documentation. Please do not edit.
= Redpanda CRD Reference
:anchor_prefix: k8s-api
:description: Custom resource definitions for the Redpanda resource. Use the Redpanda resource to create and manage Redpanda clusters with the Redpanda Operator.

{description}

.Packages
{{- range $groupVersions }}
- {{ asciidocRenderGVLink . }}
{{- end }}

{{ range $groupVersions }}
{{ template "gvDetails" . }}
{{ end }}

{{- end -}}
