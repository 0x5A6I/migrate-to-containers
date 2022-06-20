#!/bin/bash
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

set -euo pipefail

# create service account for GCE source
gcloud iam service-accounts create m2c-ce-src --project=${PROJECT_ID}

# add required permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:m2c-ce-src@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/compute.viewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:m2c-ce-src@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/compute.storageAdmin"

# Download service account key
gcloud iam service-accounts keys create m2c-ce-src.json --iam-account=m2c-ce-src@${PROJECT_ID}.iam.gserviceaccount.com --project=${PROJECT_ID}

# create a source for migration
migctl source create ce my-ce-src --project ${PROJECT_ID} --json-key=m2c-ce-src.json
