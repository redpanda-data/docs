@cluster:sasl @variant:vectorized
Feature: Group CRDs
  Background: Cluster available
    Given cluster "sasl" is available

  @skip:gke @skip:aks @skip:eks
  Scenario: Manage group ACLs
    When I apply Kubernetes manifest:
    """
# tag::manage-group-acls[]
    # In this example manifest, ACLs are created for an OIDC group called "engineering"
    # in a cluster called "sasl". The group is granted read access to topics matching "team-"
    # and read access to Schema Registry subjects matching "team-".
    ---
    apiVersion: cluster.redpanda.com/v1alpha2
    kind: Group
    metadata:
      name: engineering
    spec:
      cluster:
        clusterRef:
          name: sasl
      authorization:
        acls:
          - type: allow
            resource:
              type: topic
              name: team-
              patternType: prefixed
            operations: [Read, Describe]
          - type: allow
            resource:
              type: subject
              name: team-
              patternType: prefixed
            operations: [Read, Describe]
# end::manage-group-acls[]
    """
    And group "engineering" is successfully synced
    Then group "engineering" should have 2 ACLs for topic pattern "team-" in cluster "sasl"
