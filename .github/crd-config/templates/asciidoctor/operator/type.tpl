{{- define "type" -}}
{{- $type := . -}}
{{- /*
Beta CRD marking: types whose names match this pattern document beta features.
They get a plain (beta) suffix on the section heading and a badge::[label=beta]
line at the start of the section body. The explicit [id=...] anchor above each
heading is untouched, so existing xrefs keep working.
Update this pattern when features graduate to GA or new beta CRDs are added.
Pipeline* = Pipeline CRD, Stretch* = StretchCluster CRD, Shadow* = ShadowLink CRD.
*/ -}}
{{- $betaTypePattern := "^(Pipeline|Stretch|Shadow)" -}}
{{- $isBeta := regexMatch $betaTypePattern $type.Name -}}
{{- if asciidocShouldRenderType $type -}}

[id="{{ asciidocTypeID $type | asciidocRenderAnchorID }}"]
== {{ $type.Name  }} {{ if $type.IsAlias }}({{ asciidocRenderTypeLink $type.UnderlyingType  }}) {{ end }}{{ if $isBeta }}(beta){{ end }}

{{ if $isBeta }}badge::[label=beta]

{{ end }}{{ $type.Doc }}

{{ if eq $type.Name "RedpandaClusterSpec" }}
For descriptions and default values, see xref:k-redpanda-helm-spec.adoc[].
{{ end }}

{{ if $type.References -}}
.Appears in:

{{- range $type.SortedReferences }}
- {{ asciidocRenderTypeLink . }}
{{- end }}
{{- end }}

{{ if $type.Members -}}
[cols="25a,75a", options="header"]
|===
| Field | Description
{{ if $type.GVK -}}
| *`apiVersion`* __string__ | `{{ $type.GVK.Group }}/{{ $type.GVK.Version }}`
| *`kind`* __string__ | `{{ $type.GVK.Kind }}`
{{ end -}}

{{ range $type.Members -}}
| *`{{ .Name  }}`* __{{ asciidocRenderType .Type }}__ | {{ template "type_members" . }}
{{ end -}}
|===
{{ end -}}

{{- end -}}
{{- end -}}
