# AWX MCP Server — Query Reference Guide

> **Important:** Use **Agent mode** in GitHub Copilot Chat (not `@workspace`). Type your query directly without any prefix.

---

## Table of Contents

1. [Environment Management](#1-environment-management)
2. [System Information](#2-system-information)
3. [Organizations](#3-organizations)
4. [Credentials](#4-credentials)
5. [Job Templates](#5-job-templates)
6. [Projects](#6-projects)
7. [Inventories](#7-inventories)
8. [Inventory Groups](#8-inventory-groups)
9. [Inventory Hosts](#9-inventory-hosts)
10. [Job Execution](#10-job-execution)
11. [Job Monitoring](#11-job-monitoring)
12. [Job Diagnostics](#12-job-diagnostics)

---

## 1. Environment Management

### List Environments (`env_list`)
```
list AWX environments
show configured environments
what environments are available
show all AWX connections
```

### Set Active Environment (`env_set_active`)
```
set active environment to production
switch to staging environment
use the dev environment
change active AWX environment to prod
```

### Get Active Environment (`env_get_active`)
```
what is the active environment
show current environment
which AWX environment am I using
get active environment
```

### Test Connection (`env_test_connection`)
```
test AWX connection
test connection to production
is AWX reachable
check if AWX is running
verify AWX connection
```

---

## 2. System Information

### System Info (`awx_system_info`)
```
show AWX system info
get AWX configuration
show AWX dashboard
show AWX settings
who am I in AWX
show my AWX user info
get AWX config
show AWX dashboard summary
```

| `info_type` | Example Query |
|-------------|---------------|
| `config` | `show AWX configuration` |
| `dashboard` | `show AWX dashboard` |
| `settings` | `show AWX settings` |
| `me` | `who am I in AWX` |

---

## 3. Organizations

### List Organizations (`awx_organizations_list`)
```
list AWX organizations
show all organizations
list orgs in AWX
filter organizations by name "Default"
show organizations page 2
```

### Get Organization (`awx_organization_get`)
```
get organization 1
show details for organization 1
get AWX org with ID 1
```

---

## 4. Credentials

### List Credentials (`awx_credentials_list`)
```
list AWX credentials
show all credentials
list credentials filtered by "SSH"
show credentials page 2
```

### List Credential Types (`awx_credential_types_list`)
```
list credential types
show AWX credential types
what credential types are available
```

### Create Credential (`awx_credential_create`)
```
create a new AWX credential named "My SSH Key" with type 1 for organization 1
create credential "Docker Hub" with credential type 2 and organization 1
```

### Delete Credential (`awx_credential_delete`)
```
delete credential 5
remove AWX credential 3
```

---

## 5. Job Templates

### List Templates (`awx_templates_list`)
```
list job templates
show AWX templates
list available templates
show all job templates
filter templates by "Deploy"
list templates page 2 with 10 per page
what templates can I run
```

### Create Template (`awx_template_create`)
```
create a job template named "Deploy App" with inventory 1, project 1, playbook "deploy.yml"
create template "Backup DB" using project 2, inventory 1, playbook "backup.yml", job type "run"
```

### Delete Template (`awx_template_delete`)
```
delete template 5
remove job template 3
delete AWX template with ID 7
```

---

## 6. Projects

### List Projects (`awx_projects_list`)
```
list AWX projects
show all projects
list projects filtered by "Demo"
show projects page 1 with 10 per page
```

### Create Project (`awx_project_create`)
```
create project "My App" in organization 1 with git SCM and URL "https://github.com/user/repo.git"
create AWX project "Infra" in org 1, SCM type git, URL "https://github.com/org/infra.git", branch "main"
```

### Delete Project (`awx_project_delete`)
```
delete project 3
remove AWX project 5
```

### Update Project from SCM (`awx_project_update`)
```
update project 1 from SCM
sync project 1
refresh project 1 from git
update project 3 and wait for completion
```

---

## 7. Inventories

### List Inventories (`awx_inventories_list`)
```
list inventories
show AWX inventories
list inventories filtered by "Production"
show inventories page 2
```

### Create Inventory (`awx_inventory_create`)
```
create inventory "Staging Servers" in organization 1
create AWX inventory "Production" in org 1 with description "Production hosts"
```

### Delete Inventory (`awx_inventory_delete`)
```
delete inventory 3
remove AWX inventory 5
```

---

## 8. Inventory Groups

### List Groups (`awx_inventory_groups_list`)
```
list groups in inventory 1
show groups for inventory 1
what groups are in inventory 2
```

### Create Group (`awx_inventory_group_create`)
```
create group "webservers" in inventory 1
add group "databases" to inventory 1 with description "DB servers"
```

### Delete Group (`awx_inventory_group_delete`)
```
delete group 3
remove inventory group 5
```

---

## 9. Inventory Hosts

### List Hosts (`awx_inventory_hosts_list`)
```
list hosts in inventory 1
show hosts for inventory 1
what hosts are in inventory 2
```

### Create Host (`awx_inventory_host_create`)
```
create host "web01.example.com" in inventory 1
add host "db01" to inventory 1 with description "Primary database"
add host "10.0.1.5" to inventory 1 with variables {"ansible_user": "admin"}
```

### Delete Host (`awx_inventory_host_delete`)
```
delete host 3
remove host 5 from inventory
```

---

## 10. Job Execution

### Launch Job (`awx_job_launch`)
```
launch job template 1
run template 1
execute job template 5
start job from template 1
launch template 1 with extra vars {"env": "staging"}
run template 3 limited to "webservers"
launch template 1 with tags "deploy,config"
run template 2 and skip tags "test"
```

### Cancel Job (`awx_job_cancel`)
```
cancel job 1
stop job 5
abort job 3
kill running job 7
```

### Delete Job (`awx_job_delete`)
```
delete job 1
remove job 5
clean up job 3
```

---

## 11. Job Monitoring

### List Jobs / Job History (`awx_jobs_list`)
```
show recent jobs
list AWX jobs
display job history
show all jobs
list recent job executions
show job runs
what jobs have run recently
get job execution history

# Filtered queries:
show failed jobs
show running jobs
show successful jobs
show pending jobs
list jobs with status failed
show jobs created after 2026-01-01
show recent jobs page 2 with 5 per page
```

### Get Job Details (`awx_job_get`)
```
get details for job 1
check status of job 1
what is the state of job 5
show job 3 details
is job 1 finished
get job 1 metadata
```

---

## 12. Job Diagnostics

### Job Output / Logs (`awx_job_stdout`)
```
show job 1 output
display console output for job 1
view job 1 logs
show what job 1 printed
see the playbook output for job 1
show execution log for job 1
get job 1 stdout
show job 5 output in json format
show last 50 lines of job 1 output
view terminal output for job 3
```

### Job Events / Task Details (`awx_job_events`)
```
show job 1 events
list execution steps for job 1
what tasks ran in job 1
show detailed activity for job 1
view play-by-play for job 1
show task results for job 3
show only failed events for job 1
list failed tasks in job 5
```

### Job Failure Analysis (`awx_job_failure_summary`)
```
why did job 1 fail
analyze failure for job 1
debug job 1 error
troubleshoot job 1
what went wrong with job 5
diagnose job 3 problem
show failure summary for job 1
explain job 1 failure
help me fix job 7 error
```

---

## Combined / Multi-Step Queries

These queries may trigger multiple tool calls:

```
# Overview workflow
show recent jobs and their status
list all failed jobs and show why they failed

# Deep dive into a specific job
show job 1 details, output, and events
get job 1 status and show the logs

# Template + Launch workflow
list templates and run the Deploy template
show templates, then launch template 1 with extra vars {"target": "prod"}

# Inventory management workflow
list inventories, then show hosts in inventory 1
create a host in inventory 1 and then launch template 3 limited to that host

# Project + Template workflow
update project 1 from SCM, then launch template 1
list projects and show templates for project 1
```

---

## Tips

1. **Use Agent mode** — Click the mode dropdown in Copilot Chat and select "Agent" (not "Ask" or "Edit")
2. **No prefix needed** — Just type your query directly, e.g., `show recent jobs`
3. **Be specific with IDs** — Include job/template/inventory IDs when referring to specific resources
4. **Filter results** — Use words like "failed", "running", "page 2", or "filtered by name" to narrow results
5. **Natural language works** — The MCP tools are designed to understand natural phrasing

---

## Tool Summary Table

| Tool Name | Category | Description |
|-----------|----------|-------------|
| `env_list` | Environment | List configured AWX environments |
| `env_set_active` | Environment | Set the active AWX environment |
| `env_get_active` | Environment | Get current active environment |
| `env_test_connection` | Environment | Test AWX connection |
| `awx_system_info` | System | Get AWX config/dashboard/settings/user info |
| `awx_organizations_list` | Organizations | List organizations |
| `awx_organization_get` | Organizations | Get organization by ID |
| `awx_credentials_list` | Credentials | List credentials |
| `awx_credential_types_list` | Credentials | List credential types |
| `awx_credential_create` | Credentials | Create a credential |
| `awx_credential_delete` | Credentials | Delete a credential |
| `awx_templates_list` | Templates | List job templates |
| `awx_template_create` | Templates | Create a job template |
| `awx_template_delete` | Templates | Delete a job template |
| `awx_projects_list` | Projects | List projects |
| `awx_project_create` | Projects | Create a project |
| `awx_project_delete` | Projects | Delete a project |
| `awx_project_update` | Projects | Update project from SCM |
| `awx_inventories_list` | Inventories | List inventories |
| `awx_inventory_create` | Inventories | Create an inventory |
| `awx_inventory_delete` | Inventories | Delete an inventory |
| `awx_inventory_groups_list` | Inventory Groups | List groups in inventory |
| `awx_inventory_group_create` | Inventory Groups | Create group in inventory |
| `awx_inventory_group_delete` | Inventory Groups | Delete group |
| `awx_inventory_hosts_list` | Inventory Hosts | List hosts in inventory |
| `awx_inventory_host_create` | Inventory Hosts | Create host in inventory |
| `awx_inventory_host_delete` | Inventory Hosts | Delete host |
| `awx_job_launch` | Execution | Launch job from template |
| `awx_job_get` | Monitoring | Get job details/status |
| `awx_jobs_list` | Monitoring | List recent jobs / job history |
| `awx_job_cancel` | Execution | Cancel running job |
| `awx_job_delete` | Execution | Delete job record |
| `awx_job_stdout` | Diagnostics | View job console output/logs |
| `awx_job_events` | Diagnostics | View job events/tasks |
| `awx_job_failure_summary` | Diagnostics | Analyze job failure with fix suggestions |
