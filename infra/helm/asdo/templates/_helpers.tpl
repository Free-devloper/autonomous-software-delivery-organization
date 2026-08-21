{{- define "asdo.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "asdo.componentLabels" -}}
app.kubernetes.io/name: asdo-{{ .component }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
app.kubernetes.io/part-of: asdo
{{- end -}}

{{- define "asdo.image" -}}
{{- $image := .image -}}
{{- if $.root.Values.global.requireImageDigest -}}
{{- printf "%s@%s" $image.repository (required "production images require immutable digest" $image.digest) -}}
{{- else if $image.digest -}}
{{- printf "%s@%s" $image.repository $image.digest -}}
{{- else -}}
{{- printf "%s:%s" $image.repository $image.tag -}}
{{- end -}}
{{- end -}}
