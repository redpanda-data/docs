{{- define "gvDetails" -}}
{{- $gv := . -}}

{{ $gv.Doc }}

{{- if $gv.Kinds  }}
.Resource Types
{{- range $gv.SortedKinds }}
- {{ $gv.TypeForKind . | asciidocRenderTypeLink }}
{{- end }}
{{ end }}

{{ range $gv.SortedTypes }}
{{ template "type" . }}
{{ end }}

{{- end -}}
