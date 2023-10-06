{{- define "gvList" -}}
{{- $groupVersions := . -}}

// Generated documentation. Please do not edit.
= Redpanda Topic CRD Reference
:anchor_prefix: k8s-api
:description: Custom resource definitions for the Topic resource. Use the Topic resource to create and manage topics with the Redpanda Operator.

{description}

.Packages
{{- range $groupVersions }}
- {{ asciidocRenderGVLink . }}
{{- end }}

{{ range $groupVersions }}
{{ template "gvDetails" . }}
{{ end }}

{{- end -}}
