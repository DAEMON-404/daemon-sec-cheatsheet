---
title: "CI/CD - Drone CI"
section: "DevOps"
sectionSlug: "devops"
sourcePath: "docs/devops/cicd-drone-ci.md"
sourceUrl: "https://github.com/swisskyrepo/InternalAllTheThings/blob/e891850d6bc6/docs/devops/cicd-drone-ci.md"
sha: "e891850d6bc6"
isIndex: false
---

# CI/CD - Drone CI

The configuration files for Drone builds are located in `.drone.yml`\
Drone build are often self-hosted, this means that you may gain excessive privileges to the kubernetes cluster that runs the runners, or to the hosting cloud environment.

In order to run an OS command in a workflow that builds pull requests - simply add a `commands` instruction to the step.

```yaml
steps:
  - name: do-something
    image: some-image:3.9
    commands:
      - {Payload}
```
