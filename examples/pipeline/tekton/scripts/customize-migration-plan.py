#!/usr/bin/env python3
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import jsonpatch
import os
import subprocess
import sys
import yaml

migrationName = sys.argv[1]
migrationTemplateFile = sys.argv[2]


def dict_deep_merge(target, customization):
    """Merges customizations into a dictionary in place"""
    for key, value in customization.items():
        if isinstance(value, list):
            if key not in target:
                target[key] = copy.deepcopy(value)
            else:
                target[key].extend(value)
        elif isinstance(value, dict):
            if key not in target:
                target[key] = copy.deepcopy(value)
            else:
                dict_deep_merge(target[key], value)
        elif isinstance(value, set):
            if key not in target:
                target[key] = value.copy()
            else:
                target[key].update(value.copy())
        else:
            target[key] = copy.copy(value)


def execute_command(command):
    """Executes a command, capturing the output"""
    output = subprocess.run(command, capture_output=True, encoding='utf-8')
    if len(output.stderr) > 0:
        print(output.stderr)
    output.check_returncode()
    return output


# Get generated plan
plan_name_cmd = ['kubectl', 'get', 'migrations.anthos-migrate.cloud.google.com', '-n', 'v2k-system',
                 migrationName, '-o', 'jsonpath={.status.resources.generateArtifacts.name}']
plan_name = execute_command(plan_name_cmd).stdout
print(f"Plan Name: {plan_name}")

plan_get_cmd = ['kubectl', 'get', 'generateartifactsflows.anthos-migrate.cloud.google.com', '-n', 'v2k-system',
                plan_name, '-o', 'yaml']
plan_output = execute_command(plan_get_cmd)
full_plan_yaml = yaml.load(plan_output.stdout, Loader=yaml.FullLoader)

plan_raw = full_plan_yaml["metadata"]["annotations"].pop("anthos-migrate.cloud.google.com/raw-content")
plan_yaml = yaml.load(plan_raw, Loader=yaml.FullLoader)

# Customize Plan
if migrationTemplateFile.endswith(".yaml") or \
        migrationTemplateFile.endswith(".YAML") or \
        migrationTemplateFile.endswith(".yml") or \
        migrationTemplateFile.endswith(".YML"):
    with open(migrationTemplateFile) as m:
        customization_yaml = yaml.load(m, Loader=yaml.FullLoader)

    dict_deep_merge(plan_yaml, customization_yaml)
elif migrationTemplateFile.endswith(".json") or \
        migrationTemplateFile.endswith(".JSON"):
    with open(migrationTemplateFile) as m:
        patch = jsonpatch.json.dumps(jsonpatch.json.load(m))

    jsonpatch.apply_patch(plan_yaml, patch, in_place=True)
else:
    print("Using Default Plan")

# Change Names to match
name_patch = jsonpatch.JsonPatch([
    {'op': 'replace', 'path': '/spec/image/base', 'value': f'{migrationName}-non-runnable-base'},
    {'op': 'replace', 'path': '/spec/image/name', 'value': migrationName},
    {'op': 'replace', 'path': '/spec/deployment/appName', 'value': migrationName},
])
name_patch.apply(plan_yaml, in_place=True)

# Apply customized plan
plan_yaml_path = "/plan.yaml"
with open(plan_yaml_path, "w") as m:
    yaml.dump(plan_yaml, m)

plan_apply_cmd = ['kubectl', 'apply', '-f', plan_yaml_path]
os.system("cat " + plan_yaml_path)
execute_command(plan_apply_cmd)
