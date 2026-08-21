package asdo.authz

import rego.v1

default allow := false

allowed_roles := {
	"organization.configuration.read": {
		"organization_owner",
		"organization_administrator",
		"auditor",
		"read_only_viewer",
		"service_account",
	},
}

allow if {
	input.organization_id
	input.action
	some role in input.roles
	role in allowed_roles[input.action]
}
