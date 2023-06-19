{{- define "type" -}}
{{- $type := . -}}
{{- if markdownShouldRenderType $type -}}

#### {{ $type.Name }}

{{ if $type.IsAlias }}_Underlying type:_ `{{ markdownRenderTypeLink $type.UnderlyingType  }}`{{ end }}

{{ $type.Doc }}

{{ if eq $type.Name "RedpandaClusterSpec" }}
These fields are used to configure the Redpanda Helm chart. For descriptions and default values, see [Redpanda Helm Chart Specification
](../redpanda-helm-spec).
{{ end }}

{{ if $type.References -}}
_Appears in:_
{{- range $type.SortedReferences }}
- {{ markdownRenderTypeLink . }}
{{- end }}
{{- end }}

{{ if $type.Members -}}
| Field | Description |
| --- | --- |
{{ if $type.GVK -}}
| `apiVersion` _string_ | `{{ $type.GVK.Group }}/{{ $type.GVK.Version }}`
| `kind` _string_ | `{{ $type.GVK.Kind }}`
{{ end -}}

{{ range $type.Members -}}
| `{{ .Name  }}` _{{ markdownRenderType .Type }}_ | {{ template "type_members" . }} |
{{ end -}}

{{ end -}}

{{- end -}}
{{- end -}}
