{{- define "gvList" -}}
{{- $groupVersions := . -}}

# Redpanda Operator CRD Reference

## Packages
{{- range $groupVersions }}
- {{ markdownRenderGVLink . }}
{{- end }}

{{ range $groupVersions }}
{{ template "gvDetails" . }}
{{ end }}

{{- end -}}
